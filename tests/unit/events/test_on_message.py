from maciota_bot.events import on_message
from maciota_bot.state import configure, get_state
from tests.support import make_state


class _Author:
    def __init__(self, *, bot: bool, name: str = 'Ada') -> None:
        self.bot = bot
        self.display_name = name


class _Channel:
    def __init__(self) -> None:
        self.id = 7
        self.sent: list[str] = []

    async def send(self, content: str) -> None:
        self.sent.append(content)


class _Message:
    def __init__(
        self,
        content: str,
        *,
        bot: bool = False,
        mentioned: bool = False,
    ) -> None:
        self.content = content
        self.id = 99
        self.mentioned = mentioned
        self.author = _Author(bot=bot)
        self.channel = _Channel()


class _Agent:
    def __init__(self, response: str = '', *, fail: bool = False) -> None:
        self.response = response
        self.fail = fail
        self.calls: list[dict[str, object]] = []

    async def execute(self, **kwargs: object) -> str:
        self.calls.append(kwargs)
        if self.fail:
            raise RuntimeError('model down')
        return self.response


def _publish(agent: _Agent) -> None:
    current = get_state()
    configure(make_state(current.engine, tree=current.tree, agent=agent))


async def test_bot_author_receives_no_reply() -> None:
    agent = _Agent('oi')
    _publish(agent)
    message = _Message('!ping', bot=True)

    await on_message(message)

    assert message.channel.sent == []
    assert agent.calls == []


async def test_mention_sends_the_agent_text() -> None:
    agent = _Agent('cheguei')
    _publish(agent)
    message = _Message('e ai', mentioned=True)

    await on_message(message)

    assert message.channel.sent == ['cheguei']
    assert agent.calls == [
        {
            'channel_id': 7,
            'message_id': 99,
            'author_name': 'Ada',
            'content': 'e ai',
            'trigger_type': 'mention',
        }
    ]


async def test_ordinary_text_is_proactive() -> None:
    agent = _Agent('kkk')
    _publish(agent)
    message = _Message('!ping')

    await on_message(message)

    assert agent.calls[0]['trigger_type'] == 'proactive'
    assert agent.calls[0]['content'] == '!ping'
    assert message.channel.sent == ['kkk']


async def test_empty_response_sends_nothing() -> None:
    agent = _Agent('   ')
    _publish(agent)
    message = _Message('hello')

    await on_message(message)

    assert message.channel.sent == []


async def test_agent_failure_sends_nothing() -> None:
    agent = _Agent(fail=True)
    _publish(agent)
    message = _Message('hello')

    await on_message(message)

    assert message.channel.sent == []
