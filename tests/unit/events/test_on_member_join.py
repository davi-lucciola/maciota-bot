import logging

import pytest

from maciota_bot.events import on_member_join


class _Channel:
    def __init__(self) -> None:
        self.sent: list[str] = []

    async def send(self, content: str) -> None:
        self.sent.append(content)


class _Guild:
    def __init__(self, channel: _Channel | None) -> None:
        self.system_channel = channel


class _Member:
    def __init__(self, mention: str, *, bot: bool, channel: _Channel | None) -> None:
        self.mention = mention
        self.name = 'ada'
        self.bot = bot
        self.guild = _Guild(channel)


async def test_bot_member_sends_nothing(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail(user_name: str) -> str:
        raise AssertionError(user_name)

    monkeypatch.setattr('maciota_bot.events.build_welcome_message', fail)
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
