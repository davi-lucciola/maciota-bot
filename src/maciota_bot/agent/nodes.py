from typing import Any

from langchain.messages import AIMessage, SystemMessage

from maciota_bot.agent.prompt import (
    HOOK_PROMPT,
    PERSONA_PROMPT,
    STYLES,
    channel_line,
    recent_messages,
    reply_prompt,
)
from maciota_bot.agent.state import BotState


def model_input(state: BotState, instruction: str) -> list:
    system = f'{channel_line(state)}\n\n{instruction}'
    return [SystemMessage(content=system), *recent_messages(state)]


def decide_hook(text: str) -> tuple[bool, str]:
    lines = [line.strip() for line in text.strip().splitlines() if line.strip()]
    if not lines:
        return False, ''
    head = lines[0].casefold()
    if head.startswith('não') or head.startswith('nao'):
        return False, ''
    if head.startswith('sim'):
        if len(lines) > 1:
            return True, lines[1]
        return True, lines[0][3:].strip(' :-')
    return False, ''


def select_style(text: str) -> str:
    cleaned = text.strip().casefold()
    for style in STYLES:
        if style.casefold() in cleaned:
            return style
    return STYLES[0]


async def read_model(model: Any, messages: list) -> str:
    reply = await model.ainvoke(messages)
    content = reply.content
    if isinstance(content, str):
        return content
    return ''.join(part if isinstance(part, str) else str(part) for part in content)


def make_nodes(light_model: object, reply_model: object) -> tuple:
    async def evaluate_trigger(state: BotState) -> dict[str, object]:
        if state['trigger_type'] == 'mention':
            return {'approved': True, 'context_hook': ''}

        text = await read_model(light_model, model_input(state, HOOK_PROMPT))
        approved, hook = decide_hook(text)
        if not approved:
            return {
                'approved': False,
                'context_hook': '',
                'final_response': '',
            }
        return {'approved': True, 'context_hook': hook}

    async def persona_router(state: BotState) -> dict[str, str]:
        text = await read_model(light_model, model_input(state, PERSONA_PROMPT))
        return {'persona_style': select_style(text)}

    async def generate_response(state: BotState) -> dict[str, object]:
        instruction = reply_prompt(state['persona_style'], state['context_hook'])
        text = (await read_model(reply_model, model_input(state, instruction))).strip()
        return {
            'final_response': text,
            'messages': [AIMessage(content=text)],
        }

    return evaluate_trigger, persona_router, generate_response
