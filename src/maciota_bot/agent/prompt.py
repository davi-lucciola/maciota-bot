import re
from functools import cache
from importlib.resources import files

from langchain.messages import HumanMessage

from maciota_bot.agent.schema import Acidity
from maciota_bot.agent.state import MESSAGE_WINDOW, BotState

_SLOT = re.compile(r'\{\{([a-z0-9_]+)\}\}')
_CLOCK = re.compile(r' \(\d{2}:\d{2}\)$')
_PROMPTS = files('maciota_bot.agent').joinpath('prompts')


@cache
def _template(name: str) -> str:
    parts = name.split('/')
    parts[-1] = f'{parts[-1]}.md'
    return _PROMPTS.joinpath(*parts).read_text(encoding='utf-8')


def render(name: str, **values: str) -> str:
    lines = []
    for line in _template(name).splitlines():
        filled = _fill(line, values)
        if filled is not None:
            lines.append(filled)
    return '\n'.join(lines).strip()


def _fill(line: str, values: dict[str, str]) -> str | None:
    keys = _SLOT.findall(line)
    for key in keys:
        if key not in values:
            raise KeyError(key)
    if any(not values[key] for key in keys):
        return None
    return _SLOT.sub(lambda match: values[match.group(1)], line)


PERSONA_PROMPT = render('style')


def persona_for(acidity: Acidity) -> str:
    return render('persona', acidez=render(f'acidity/{acidity}'))


def server_context(state: BotState) -> str:
    return render(
        'server',
        channel_id=str(state['channel_id']),
        guild_name=state['guild_name'] or '',
        guild_description=state['guild_description'] or '',
        channel_name=state['channel_name'] or '',
        channel_topic=state['channel_topic'] or '',
    )


def trigger_instruction(_state: BotState) -> str:
    return render('trigger')


def reply_prompt(state: BotState) -> str:
    hook = state['context_hook'] or (
        'nenhum gancho separado; responda à mensagem atual'
    )
    return render(
        'reply',
        persona=persona_for(state['acidity']),
        estilo=state['persona_style'],
        gancho=hook,
        audiencia=reply_audience(state),
    )


def reply_audience(state: BotState) -> str:
    target = state['reply_to_message_id']
    if target is None:
        return render('audience_channel')
    return render('audience_reply', autor=_author_of(state, target))


def recent_messages(state: BotState) -> list:
    return list(state['messages'])[-MESSAGE_WINDOW:]


def _author_of(state: BotState, message_id: int) -> str:
    for message in recent_messages(state):
        if not isinstance(message, HumanMessage) or message.id is None:
            continue
        if int(message.id) != message_id:
            continue
        head = str(message.content).split(': ', 1)[0]
        return _CLOCK.sub('', head)
    return 'essa pessoa'
