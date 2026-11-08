import logging

from langchain.chat_models import BaseChatModel
from langchain.messages import AIMessage, HumanMessage, SystemMessage
from pydantic import Field

from maciota_bot.agent.prompt import (
    PERSONA_PROMPT,
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


def model_input(state: BotState, instruction: str) -> list:
    system = f'{server_context(state)}\n\n{instruction}'
    return [SystemMessage(content=system), *recent_messages(state)]


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
    messages: list = Field(default_factory=list)


def turn_state(turn: _TriggerInput) -> BotState:
    incoming = HumanMessage(
        content=f'{turn.author_name}: {turn.content}',
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
        decision = await structured.ainvoke(
            model_input(state, trigger_instruction(state))
        )

        if not isinstance(decision, TriggerDecision):
            raise TypeError(
                f'Esperado TriggerDecision da LLM, recebido {type(decision).__name__}'
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
        decision = await structured.ainvoke(model_input(state, PERSONA_PROMPT))

        if not isinstance(decision, StyleDecision):
            raise TypeError(
                f'Esperado StyleDecision da LLM, recebido {type(decision).__name__}'
            )

        logger.debug('Estilo escolhido: %s', decision.style)
        return {'persona_style': decision.style}

    async def generate_response(state: BotState) -> dict[str, object]:
        reply = await reply_model.ainvoke(model_input(state, reply_prompt(state)))
        text = _text(reply).strip()
        logger.debug('Resposta gerada: %s', text)
        return {
            'final_response': text,
            'messages': [AIMessage(content=text)],
        }

    return evaluate_trigger, persona_router, generate_response


def _text(message: AIMessage) -> str:
    content = message.content
    if isinstance(content, str):
        return content
    return ''.join(part if isinstance(part, str) else str(part) for part in content)
