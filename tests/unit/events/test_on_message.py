from maciota_bot.events import on_message


class _Author:
    def __init__(self, *, bot: bool) -> None:
        self.bot = bot


class _Channel:
    def __init__(self) -> None:
        self.sent: list[str] = []

    async def send(self, content: str) -> None:
        self.sent.append(content)


class _Message:
    def __init__(self, content: str, *, bot: bool = False) -> None:
        self.content = content
        self.author = _Author(bot=bot)
        self.channel = _Channel()


async def test_bot_author_receives_no_reply() -> None:
    message = _Message('!ping', bot=True)

    await on_message(message)

    assert message.channel.sent == []


async def test_ping_receives_pong() -> None:
    message = _Message('!ping')

    await on_message(message)

    assert message.channel.sent == ['pong']


async def test_ping_ignores_surrounding_space_and_case() -> None:
    message = _Message('  !PING\n')

    await on_message(message)

    assert message.channel.sent == ['pong']


async def test_other_text_receives_no_reply() -> None:
    message = _Message('hello')

    await on_message(message)

    assert message.channel.sent == []
