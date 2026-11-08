import logging

import pytest

from maciota_bot.services.welcome import greet


class _Channel:
    def __init__(self) -> None:
        self.sent: list[str] = []

    async def send(self, content: str) -> None:
        self.sent.append(content)


class _Guild:
    def __init__(
        self,
        channel: _Channel | None,
        *,
        guild_id: int | None = None,
        channels: dict[int, _Channel] | None = None,
    ) -> None:
        self.system_channel = channel
        self.id = 0 if guild_id is None else guild_id
        self._channels = {} if channels is None else channels

    def get_channel(self, channel_id: int) -> _Channel | None:
        return self._channels.get(channel_id)


class _Member:
    def __init__(
        self,
        mention: str,
        *,
        bot: bool,
        channel: _Channel | None,
        guild_id: int | None = None,
        channels: dict[int, _Channel] | None = None,
    ) -> None:
        self.mention = mention
        self.name = 'ada'
        self.bot = bot
        self.guild = _Guild(channel, guild_id=guild_id, channels=channels)


def _saved_channel(
    monkeypatch: pytest.MonkeyPatch,
    channel_id: int | None,
) -> None:
    async def read(guild_id: int) -> int | None:
        return channel_id

    monkeypatch.setattr('maciota_bot.services.welcome.get_welcome_channel_id', read)


async def test_bot_member_sends_nothing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_message(user_name: str) -> str:
        raise AssertionError(user_name)

    async def fail_read(guild_id: int) -> int | None:
        raise AssertionError(guild_id)

    monkeypatch.setattr(
        'maciota_bot.services.welcome.build_welcome_message',
        fail_message,
    )
    monkeypatch.setattr(
        'maciota_bot.services.welcome.get_welcome_channel_id',
        fail_read,
    )
    channel = _Channel()
    member = _Member('<@42>', bot=True, channel=channel)

    await greet(member)

    assert channel.sent == []


async def test_member_join_sends_the_service_message(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: dict[str, str] = {}

    def build(user_name: str) -> str:
        seen['user_name'] = user_name
        return 'oi ada'

    monkeypatch.setattr('maciota_bot.services.welcome.build_welcome_message', build)
    _saved_channel(monkeypatch, None)
    channel = _Channel()
    member = _Member('<@42>', bot=False, channel=channel)

    await greet(member)

    assert seen['user_name'] == '<@42>'
    assert channel.sent == ['oi ada']


async def test_no_saved_channel_uses_system_channel(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def build(user_name: str) -> str:
        return 'oi ada'

    monkeypatch.setattr('maciota_bot.services.welcome.build_welcome_message', build)
    _saved_channel(monkeypatch, None)
    channel = _Channel()
    member = _Member('<@42>', bot=False, channel=channel, guild_id=5)

    await greet(member)

    assert channel.sent == ['oi ada']


async def test_saved_channel_receives_the_welcome(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def build(user_name: str) -> str:
        return 'oi ada'

    monkeypatch.setattr('maciota_bot.services.welcome.build_welcome_message', build)
    _saved_channel(monkeypatch, 99)
    system = _Channel()
    welcome = _Channel()
    member = _Member(
        '<@42>',
        bot=False,
        channel=system,
        guild_id=5,
        channels={99: welcome},
    )

    await greet(member)

    assert welcome.sent == ['oi ada']
    assert system.sent == []


async def test_missing_saved_channel_falls_back_to_system_channel(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    def build(user_name: str) -> str:
        return 'oi ada'

    monkeypatch.setattr('maciota_bot.services.welcome.build_welcome_message', build)
    _saved_channel(monkeypatch, 99)
    caplog.set_level(logging.WARNING, logger='maciota_bot.services.welcome')
    system = _Channel()
    member = _Member('<@42>', bot=False, channel=system, guild_id=5, channels={})

    await greet(member)

    assert caplog.messages == ['Canal de boas-vindas ausente']
    assert system.sent == ['oi ada']


async def test_missing_saved_and_system_channels_log_and_send_nothing(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    def fail(user_name: str) -> str:
        raise AssertionError(user_name)

    monkeypatch.setattr('maciota_bot.services.welcome.build_welcome_message', fail)
    _saved_channel(monkeypatch, 99)
    caplog.set_level(logging.WARNING, logger='maciota_bot.services.welcome')
    member = _Member('<@42>', bot=False, channel=None, guild_id=5, channels={})

    await greet(member)

    assert caplog.messages == [
        'Canal de boas-vindas ausente',
        'Canal de sistema ausente',
    ]


async def test_missing_system_channel_logs_and_sends_nothing(
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail(user_name: str) -> str:
        raise AssertionError(user_name)

    monkeypatch.setattr('maciota_bot.services.welcome.build_welcome_message', fail)
    _saved_channel(monkeypatch, None)
    caplog.set_level(logging.WARNING, logger='maciota_bot.services.welcome')
    member = _Member('<@42>', bot=False, channel=None)

    await greet(member)

    assert caplog.messages == ['Canal de sistema ausente']
