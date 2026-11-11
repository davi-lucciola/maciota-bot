import logging
import re
from zoneinfo import ZoneInfo

from langchain.chat_models import BaseChatModel
from langchain.messages import AIMessage, AnyMessage, HumanMessage, SystemMessage
from pydantic import Field

from maciota_bot.agent.prompt import (
    PERSONA_PROMPT,
    author_of,
    clip_excerpt,
    line_excerpt,
    recent_messages,
    reply_prompt,
    server_context,
    trigger_instruction,
)
from maciota_bot.agent.schema import (
    BotInput,
    StyleDecision,
    TriggerAction,
    TriggerDecision,
)
from maciota_bot.agent.state import BotState

logger = logging.getLogger(__name__)
_SAO_PAULO = ZoneInfo('America/Sao_Paulo')
_UNSAFE_NAME = re.compile(r'[^A-Za-z0-9_-]+')
_NAME_LIMIT = 64
_BOT_NAME = 'Maciota'


def message_name(display_name: str) -> str:
    slug = _UNSAFE_NAME.sub('_', display_name).strip('_')[:_NAME_LIMIT]
    return slug or 'usuario'


def model_input(state: BotState, instruction: str) -> list[AnyMessage]:
    system = f'{server_context(state)}\n\n{instruction}'
    return [SystemMessage(content=system), *_numbered(recent_messages(state))]


def _numbered(messages: list[AnyMessage]) -> list[AnyMessage]:
    numbered = []
    for index, message in enumerate(messages):
        content = message.content
        if not isinstance(content, str):
            content = str(content)
        numbered.append(message.model_copy(update={'content': f'[{index}] {content}'}))
    return numbered


def _user_content(turn: BotInput) -> str:
    clock = turn.created_at.astimezone(_SAO_PAULO).strftime('%H:%M')
    author = (turn.referenced_author or '').strip()
    mark = _reply_mark(author or None, turn.referenced_excerpt)
    body = f'{mark}: {turn.content}' if mark else turn.content
    return f'{_speaker(turn.author_name)} ({clock}): {body}'


def _speaker(name: str) -> str:
    return name.strip() or 'usuario'


def _reply_mark(author: str | None, excerpt: str | None) -> str:
    quote = clip_excerpt(excerpt) if excerpt else ''
    if author and quote:
        return f'respondendo a {author} ("{quote}")'
    if author:
        return f'respondendo a {author}'
    if quote:
        return f'respondendo ("{quote}")'
    return ''


def _assistant_content(state: BotState, text: str) -> str:
    target = state['reply_to_message_id']
    if not isinstance(target, int):
        return text
    mark = _reply_mark(author_of(state, target), line_excerpt(state, target))
    if not mark:
        return text
    return f'{mark}: {text}'


def message_id_at(state: BotState, index: int | None) -> int | None:
    if index is None:
        return None
    window = recent_messages(state)
    if index < 0 or index >= len(window):
        return None
    message = window[index]
    if not isinstance(message, HumanMessage) or message.id is None:
        return None
    return int(message.id)


class _TriggerInput(BotInput):
    messages: list[AnyMessage] = Field(default_factory=list)


def turn_state(turn: _TriggerInput) -> BotState:
    incoming = HumanMessage(
        content=_user_content(turn),
        name=message_name(turn.author_name),
        id=str(turn.message_id),
    )
    return {
        'messages': [*turn.messages, incoming],
        'channel_id': turn.channel_id,
        'message_id': turn.message_id,
        'author_name': turn.author_name,
        'trigger_type': turn.trigger_type,
        'guild_name': turn.guild_name,
        'guild_description': turn.guild_description,
        'channel_name': turn.channel_name,
        'channel_topic': turn.channel_topic,
        'acidity': turn.acidity,
        'context_hook': '',
        'persona_style': '',
        'final_response': '',
        'reply_to_message_id': None,
        'approved': False,
    }


def make_nodes(
    light_model: BaseChatModel,
    reply_model: BaseChatModel,
) -> tuple:
    async def evaluate_trigger(turn: _TriggerInput) -> BotState:
        state = turn_state(turn)
        if turn.trigger_type == 'mention':
            logger.debug(
                'Decisão: mention, enviar resposta à mensagem %s',
                turn.message_id,
            )
            state['approved'] = True
            state['context_hook'] = ''
            state['reply_to_message_id'] = turn.message_id
            return state

        structured = light_model.with_structured_output(TriggerDecision)
        decision: TriggerDecision = await structured.ainvoke(
            model_input(state, trigger_instruction(state))
        )

        if decision.action == TriggerAction.SILENCE:
            logger.debug('Decisão: silence, não enviar. %s', decision.reasoning)
            state['approved'] = False
            state['context_hook'] = ''
            state['final_response'] = ''
            state['reply_to_message_id'] = None
            return state

        reply_to = None
        if decision.action == TriggerAction.REPLY:
            reply_to = message_id_at(state, decision.message_index)
        logger.debug(
            'Decisão: %s, enviar. gancho=%s reply_to=%s. %s',
            decision.action,
            decision.hook,
            reply_to,
            decision.reasoning,
        )
        state['approved'] = True
        state['context_hook'] = decision.hook
        state['reply_to_message_id'] = reply_to
        return state

    async def persona_router(state: BotState) -> dict[str, str]:
        structured = light_model.with_structured_output(StyleDecision)
        decision: StyleDecision = await structured.ainvoke(
            model_input(state, PERSONA_PROMPT)
        )

        logger.debug('Estilo escolhido: %s', decision.style.value)
        return {'persona_style': decision.style.value}

    async def generate_response(state: BotState) -> dict[str, object]:
        reply: AIMessage = await reply_model.ainvoke(
            model_input(state, reply_prompt(state))
        )
        text = _text(reply).strip()
        logger.debug('Resposta gerada: %s', text)
        return {
            'final_response': text,
            'messages': [
                AIMessage(content=_assistant_content(state, text), name=_BOT_NAME)
            ],
        }

    return evaluate_trigger, persona_router, generate_response


def _text(message: AIMessage) -> str:
    content = message.content
    if isinstance(content, str):
        return content
    return ''.join(part if isinstance(part, str) else str(part) for part in content)
