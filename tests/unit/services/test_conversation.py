import logging

import pytest

from maciota_bot.agent.schema import AgentOutput, BotInput
from maciota_bot.services.conversation import respond
from maciota_bot.state import configure, get_state
from tests.support import make_state


class _Author:
    def __init__(self, *, bot: bool, name: str = 'Ada') -> None:
        self.bot = bot
        self.display_name = name


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


class _Message:
    def __init__(
        self,
        content: str,
        *,
        bot: bool = False,
        mentioned: bool = False,
        direct: bool = False,
    ) -> None:
        self.content = content
        self.id = 99
        self.mentioned = mentioned
        self.author = _Author(bot=bot)
        self.channel = _Channel()
        self.guild = None if direct else _Guild()


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


def _publish(agent: _Agent) -> None:
    current = get_state()
    configure(make_state(current.engine, agent=agent))


def _turn(*, trigger_type: str, content: str) -> BotInput:
    return BotInput(
        channel_id=7,
        message_id=99,
        author_name='Ada',
        content=content,
        trigger_type=trigger_type,
        guild_name='Servidor',
        guild_description='um lugar',
        channel_name='geral',
        channel_topic='assunto',
    )


async def test_bot_author_receives_no_reply() -> None:
    agent = _Agent('oi')
    _publish(agent)
    message = _Message('!ping', bot=True)

    await respond(message)

    assert message.channel.sent == []
    assert agent.calls == []


async def test_direct_message_receives_no_reply() -> None:
    agent = _Agent('oi')
    _publish(agent)
    message = _Message('oi', direct=True)

    await respond(message)

    assert message.channel.sent == []
    assert agent.calls == []


async def test_mention_replies_to_the_message(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG, logger='maciota_bot.services.conversation')
    agent = _Agent('cheguei', reply_to=99)
    _publish(agent)
    message = _Message('e ai', mentioned=True)

    await respond(message)

    assert message.channel.sent == ['cheguei']
    assert message.channel.references[0].message_id == 99
    assert agent.calls == [_turn(trigger_type='mention', content='e ai')]
    assert 'Mensagem recebida no servidor Servidor de Ada: e ai' in caplog.text
    assert 'Decisão: enviar resposta à mensagem 99' in caplog.text


async def test_ordinary_text_is_a_channel_message(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG, logger='maciota_bot.services.conversation')
    agent = _Agent('kkk')
    _publish(agent)
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
    _publish(agent)
    message = _Message('hello')

    await respond(message)

    assert message.channel.sent == []
    assert 'Decisão: não enviar, resposta vazia' in caplog.text


async def test_agent_failure_sends_nothing() -> None:
    agent = _Agent(fail=True)
    _publish(agent)
    message = _Message('hello')

    await respond(message)

    assert message.channel.sent == []
