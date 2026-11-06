import logging
from collections.abc import Iterator
from pathlib import Path

import pytest

from maciota_bot.db import (
    configure_engine,
    create_db_engine,
    init_db,
    set_welcome_channel,
)
from maciota_bot.events import on_member_join


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
        if guild_id is not None:
            self.id = guild_id
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


@pytest.fixture(autouse=True)
def _reset_engine() -> Iterator[None]:
    configure_engine(None)
    yield
    configure_engine(None)


def _use_database(tmp_path: Path):
    engine = create_db_engine(f'sqlite:///{tmp_path / "welcome.db"}')
    init_db(engine)
    configure_engine(engine)
    return engine


async def test_bot_member_sends_nothing(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    def fail_message(user_name: str) -> str:
        raise AssertionError(user_name)

    def fail_read(engine: object, guild_id: int) -> int | None:
        raise AssertionError((engine, guild_id))

    monkeypatch.setattr('maciota_bot.events.build_welcome_message', fail_message)
    monkeypatch.setattr('maciota_bot.events.get_welcome_channel_id', fail_read)
    _use_database(tmp_path)
    channel = _Channel()
    member = _Member('<@42>', bot=True, channel=channel)

    await on_member_join(member)

    assert channel.sent == []


async def test_member_join_sends_the_service_message(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: dict[str, str] = {}

    def build(user_name: str) -> str:
        seen['user_name'] = user_name
        return 'oi ada'

    monkeypatch.setattr('maciota_bot.events.build_welcome_message', build)
    channel = _Channel()
    member = _Member('<@42>', bot=False, channel=channel)

    await on_member_join(member)

    assert seen['user_name'] == '<@42>'
    assert channel.sent == ['oi ada']


async def test_no_saved_channel_uses_system_channel(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    def build(user_name: str) -> str:
        return 'oi ada'

    monkeypatch.setattr('maciota_bot.events.build_welcome_message', build)
    _use_database(tmp_path)
    channel = _Channel()
    member = _Member('<@42>', bot=False, channel=channel, guild_id=5)

    await on_member_join(member)

    assert channel.sent == ['oi ada']


async def test_saved_channel_receives_the_welcome(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    def build(user_name: str) -> str:
        return 'oi ada'

    monkeypatch.setattr('maciota_bot.events.build_welcome_message', build)
    engine = _use_database(tmp_path)
    system = _Channel()
    welcome = _Channel()
    set_welcome_channel(engine, 5, 99)
    member = _Member(
        '<@42>',
        bot=False,
        channel=system,
        guild_id=5,
        channels={99: welcome},
    )

    await on_member_join(member)

    assert welcome.sent == ['oi ada']
    assert system.sent == []


async def test_missing_saved_channel_falls_back_to_system_channel(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    def build(user_name: str) -> str:
        return 'oi ada'

    monkeypatch.setattr('maciota_bot.events.build_welcome_message', build)
    engine = _use_database(tmp_path)
    set_welcome_channel(engine, 5, 99)
    caplog.set_level(logging.WARNING, logger='maciota_bot.events')
    system = _Channel()
    member = _Member('<@42>', bot=False, channel=system, guild_id=5, channels={})

    await on_member_join(member)

    assert caplog.messages == ['Canal de boas-vindas ausente']
    assert system.sent == ['oi ada']


async def test_missing_saved_and_system_channels_log_and_send_nothing(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    def fail(user_name: str) -> str:
        raise AssertionError(user_name)

    monkeypatch.setattr('maciota_bot.events.build_welcome_message', fail)
    engine = _use_database(tmp_path)
    set_welcome_channel(engine, 5, 99)
    caplog.set_level(logging.WARNING, logger='maciota_bot.events')
    member = _Member('<@42>', bot=False, channel=None, guild_id=5, channels={})

    await on_member_join(member)

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

    monkeypatch.setattr('maciota_bot.events.build_welcome_message', fail)
    caplog.set_level(logging.WARNING, logger='maciota_bot.events')
    member = _Member('<@42>', bot=False, channel=None)

    await on_member_join(member)

    assert caplog.messages == ['Canal de sistema ausente']
