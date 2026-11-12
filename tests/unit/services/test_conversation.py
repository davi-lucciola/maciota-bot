import logging
from datetime import UTC, datetime

import discord
import pytest
from langchain.messages import HumanMessage

from maciota_bot.agent.schema import AgentOutput, BotInput
from maciota_bot.db import init_db
from maciota_bot.services.acidity import set_acidity
from maciota_bot.services.conversation import respond
from maciota_bot.state import configure, get_state
from tests.support import make_state

_SENT_AT = datetime(2026, 11, 8, 15, 23, tzinfo=UTC)


class _Author:
    def __init__(self, *, bot: bool, name: str = 'Ada') -> None:
        self.bot = bot
        self.display_name = name


class _Named:
    def __init__(self, item_id: int, name: str) -> None:
        self.id = item_id
        self.name = name


class _Mention:
    def __init__(self, user_id: int, username: str, display_name: str) -> None:
        self.id = user_id
        self.name = username
        self.display_name = display_name


class _Guild:
    def __init__(self) -> None:
        self.id = 3
        self.name = 'Servidor'
        self.description = 'um lugar'


class _Channel:
    def __init__(self) -> None:
        self.id = 7
        self.name = 'geral'
        self.topic = 'assunto'
        self.sent: list[str] = []
        self.references: list[object | None] = []

    async def send(self, content: str, *, reference: object | None = None) -> None:
        self.sent.append(content)
        self.references.append(reference)


class _Referenced:
    def __init__(
        self,
        content: str,
        author: str = 'Davi Lucciola',
        mentions: list[_Mention] | None = None,
    ) -> None:
        self.content = content
        self.author = _Author(bot=False, name=author)
        self.mentions = mentions or []


class _Reference:
    def __init__(self, message_id: int, resolved: object | None) -> None:
        self.message_id = message_id
        self.resolved = resolved


class _HttpResponse:
    status = 404
    reason = 'Not Found'


class _Message:
    def __init__(
        self,
        content: str,
        *,
        bot: bool = False,
        mentioned: bool = False,
        direct: bool = False,
        reference: _Reference | None = None,
        mentions: list[_Mention] | None = None,
    ) -> None:
        self.content = content
        self.id = 99
        self.mentioned = mentioned
        self.author = _Author(bot=bot)
        self.created_at = _SENT_AT
        self.channel = _Channel()
        self.guild = None if direct else _Guild()
        self.reference = reference
        self.mentions = mentions or []


class _Agent:
    def __init__(
        self,
        response: str = '',
        *,
        fail: bool = False,
        reply_to: int | None = None,
    ) -> None:
        self.output = AgentOutput(text=response, reply_to_message_id=reply_to)
        self.fail = fail
        self.calls: list[BotInput] = []

    async def execute(self, turn: BotInput) -> AgentOutput:
        self.calls.append(turn)
        if self.fail:
            raise RuntimeError('model down')
        return self.output


async def _publish(agent: _Agent) -> None:
    current = get_state()
    await init_db(current.engine)
    configure(make_state(current.engine, agent=agent))


def _turn(*, trigger_type: str, content: str) -> BotInput:
    return {
        'messages': [
            HumanMessage(
                content=f'Ada (12:23): {content}',
                name='Ada',
                id='99',
            )
        ],
        'channel_id': 7,
        'message_id': 99,
        'author_name': 'Ada',
        'created_at': _SENT_AT,
        'trigger_type': trigger_type,
        'guild_name': 'Servidor',
        'guild_description': 'um lugar',
        'channel_name': 'geral',
        'channel_topic': 'assunto',
        'acidity': 'medium',
        'referenced_author': None,
        'referenced_excerpt': None,
    }


async def test_bot_author_receives_no_reply() -> None:
    agent = _Agent('oi')
    await _publish(agent)
    message = _Message('!ping', bot=True)

    await respond(message)

    assert message.channel.sent == []
    assert agent.calls == []


async def test_direct_message_receives_no_reply() -> None:
    agent = _Agent('oi')
    await _publish(agent)
    message = _Message('oi', direct=True)

    await respond(message)

    assert message.channel.sent == []
    assert agent.calls == []


async def test_mention_replies_to_the_message(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG, logger='maciota_bot.services.conversation')
    agent = _Agent('cheguei', reply_to=99)
    await _publish(agent)
    message = _Message('e ai', mentioned=True)

    await respond(message)

    assert message.channel.sent == ['cheguei']
    assert message.channel.references[0].message_id == 99
    assert agent.calls == [_turn(trigger_type='mention', content='e ai')]
    assert 'content' not in agent.calls[0]
    assert agent.calls[0]['acidity'] == 'medium'
    assert 'Mensagem recebida no servidor Servidor de Ada: e ai' in caplog.text
    assert 'Decisão: enviar resposta à mensagem 99' in caplog.text


async def test_ordinary_text_is_a_channel_message(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG, logger='maciota_bot.services.conversation')
    agent = _Agent('kkk')
    await _publish(agent)
    message = _Message('!ping')

    await respond(message)

    assert agent.calls == [_turn(trigger_type='proactive', content='!ping')]
    assert message.channel.sent == ['kkk']
    assert message.channel.references == [None]
    assert 'Decisão: enviar mensagem no canal' in caplog.text


async def test_empty_response_sends_nothing(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG, logger='maciota_bot.services.conversation')
    agent = _Agent('   ')
    await _publish(agent)
    message = _Message('hello')

    await respond(message)

    assert message.channel.sent == []
    assert 'Decisão: não enviar, resposta vazia' in caplog.text


async def test_agent_failure_sends_nothing() -> None:
    agent = _Agent(fail=True)
    await _publish(agent)
    message = _Message('hello')

    await respond(message)

    assert message.channel.sent == []


async def test_saved_acidity_reaches_the_turn() -> None:
    agent = _Agent('ok')
    await _publish(agent)
    await set_acidity(3, 'sharp')
    message = _Message('e ai', mentioned=True)

    await respond(message)

    assert agent.calls[0]['acidity'] == 'sharp'


async def test_resolved_reply_reaches_the_turn() -> None:
    agent = _Agent('ok')
    await _publish(agent)
    message = _Message(
        'responde ele',
        reference=_Reference(50, _Referenced('Eu posso te desligar ein')),
    )

    await respond(message)

    assert agent.calls[0]['referenced_author'] == 'Davi Lucciola'
    assert agent.calls[0]['referenced_excerpt'] == 'Eu posso te desligar ein'
    spoken = agent.calls[0]['messages'][0].content
    assert spoken == (
        'Ada (12:23): respondendo a Davi Lucciola '
        '("Eu posso te desligar ein"): responde ele'
    )


async def test_unresolved_reply_is_fetched() -> None:
    agent = _Agent('ok')
    await _publish(agent)
    message = _Message('responde ele', reference=_Reference(50, None))

    async def fetch_message(message_id: int) -> _Referenced:
        assert message_id == 50
        return _Referenced('Eu posso te desligar ein')

    message.channel.fetch_message = fetch_message

    await respond(message)

    assert agent.calls[0]['referenced_author'] == 'Davi Lucciola'
    assert agent.calls[0]['referenced_excerpt'] == 'Eu posso te desligar ein'


async def test_failed_reply_fetch_leaves_the_turn_unmarked() -> None:
    agent = _Agent('ok')
    await _publish(agent)
    message = _Message('responde ele', reference=_Reference(50, None))

    async def fetch_message(message_id: int) -> None:
        raise discord.HTTPException(_HttpResponse(), 'missing')

    message.channel.fetch_message = fetch_message

    await respond(message)

    assert agent.calls[0]['referenced_author'] is None
    assert agent.calls[0]['referenced_excerpt'] is None


async def test_user_mention_becomes_the_username() -> None:
    agent = _Agent('ok')
    await _publish(agent)
    message = _Message(
        'Qual é meu nome <@1568031015299981423>',
        mentions=[_Mention(1568031015299981423, 'maciota', 'Maciota Bot')],
    )

    await respond(message)

    content = agent.calls[0]['messages'][0].content
    assert content == 'Ada (12:23): Qual é meu nome @maciota'
    assert '<@1568031015299981423>' not in content
    assert 'Maciota Bot' not in content


async def test_unresolved_mention_stays() -> None:
    agent = _Agent('ok')
    await _publish(agent)
    message = _Message('oi <@999>')

    await respond(message)

    assert agent.calls[0]['messages'][0].content == 'Ada (12:23): oi <@999>'


async def test_quoted_user_mention_becomes_the_username() -> None:
    agent = _Agent('ok')
    await _publish(agent)
    quoted = _Referenced(
        'fala com <@7> e <@!7>',
        mentions=[_Mention(7, 'ada', 'Ada Lovelace')],
    )
    message = _Message('responde ele', reference=_Reference(50, quoted))

    await respond(message)

    assert agent.calls[0]['referenced_excerpt'] == 'fala com @ada e @ada'


async def test_role_and_channel_mentions_become_names() -> None:
    agent = _Agent('ok')
    await _publish(agent)
    message = _Message('vem <@&3> no <#8>')
    message.role_mentions = [_Named(3, 'mods')]
    message.channel_mentions = [_Named(8, 'geral')]

    await respond(message)

    assert agent.calls[0]['messages'][0].content == 'Ada (12:23): vem @mods no #geral'
