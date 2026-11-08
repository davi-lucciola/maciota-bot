import logging

from langchain.chat_models import BaseChatModel
from langchain.messages import AIMessage, HumanMessage, SystemMessage

from maciota_bot.agent.prompt import (
    PERSONA_PROMPT,
    STYLES,
    recent_messages,
    reply_prompt,
    server_context,
    trigger_instruction,
)
from maciota_bot.agent.schema import TriggerAction, TriggerDecision
from maciota_bot.agent.state import BotState

logger = logging.getLogger(__name__)


def model_input(state: BotState, instruction: str) -> list:
    system = f'{server_context(state)}\n\n{instruction}'
    return [SystemMessage(content=system), *recent_messages(state)]


def select_style(text: str) -> str:
    cleaned = text.strip().casefold()
    for style in STYLES:
        if style.casefold() in cleaned:
            return style
    return STYLES[0]


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


def make_nodes(
    light_model: BaseChatModel,
    reply_model: BaseChatModel,
) -> tuple:
    async def evaluate_trigger(state: BotState) -> dict[str, object]:
        if state['trigger_type'] == 'mention':
            logger.debug(
                'Decisão: mention, enviar resposta à mensagem %s',
                state['message_id'],
            )
            return {
                'approved': True,
                'context_hook': '',
                'reply_to_message_id': state['message_id'],
            }

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
            return {
                'approved': False,
                'context_hook': '',
                'final_response': '',
                'reply_to_message_id': None,
            }

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
        return {
            'approved': True,
            'context_hook': decision.hook,
            'reply_to_message_id': reply_to,
        }

    async def persona_router(state: BotState) -> dict[str, str]:
        reply = await light_model.ainvoke(model_input(state, PERSONA_PROMPT))
        style = select_style(_text(reply))
        logger.debug('Estilo escolhido: %s', style)
        return {'persona_style': style}

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
