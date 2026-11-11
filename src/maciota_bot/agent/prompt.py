import re
from functools import cache
from importlib.resources import files

from langchain.messages import AnyMessage, HumanMessage

from maciota_bot.agent.schema import Acidity
from maciota_bot.agent.state import MESSAGE_WINDOW, BotState

_SLOT = re.compile(r'\{\{([a-z0-9_]+)\}\}')
_CLOCK = re.compile(r' \(\d{2}:\d{2}\)$')
_PROMPTS = files('maciota_bot.agent').joinpath('prompts')
_EXCERPT_LIMIT = 80


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
    return render('audience_reply', autor=author_of(state, target))


def recent_messages(state: BotState) -> list[AnyMessage]:
    return list(state['messages'])[-MESSAGE_WINDOW:]


def clip_excerpt(text: str) -> str:
    return ' '.join(text.split())[:_EXCERPT_LIMIT]


_SPEAKER = re.compile(r'^(?P<name>.+?) \(\d{2}:\d{2}\): ')


def author_of(state: BotState, message_id: int) -> str:
    message = _human(state, message_id)
    if message is None:
        return 'essa pessoa'
    spoken = _speaker_name(str(message.content))
    if spoken:
        return spoken
    if message.name:
        return message.name
    head = str(message.content).split(': ', 1)[0]
    return _CLOCK.sub('', head)


def line_excerpt(state: BotState, message_id: int) -> str | None:
    message = _human(state, message_id)
    if message is None:
        return None
    content = str(message.content)
    match = _SPEAKER.match(content)
    text = content[match.end() :] if match else content
    excerpt = clip_excerpt(text)
    return excerpt or None


def _speaker_name(content: str) -> str:
    match = _SPEAKER.match(content)
    if match is None:
        return ''
    return match.group('name').strip()


def _human(state: BotState, message_id: int) -> HumanMessage | None:
    for message in recent_messages(state):
        if not isinstance(message, HumanMessage) or message.id is None:
            continue
        if int(message.id) != message_id:
            continue
        return message
    return None
