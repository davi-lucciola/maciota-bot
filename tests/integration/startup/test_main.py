import logging
from collections.abc import Callable
from pathlib import Path

import discord
import pytest

from maciota_bot.events import on_member_join, on_message, on_ready
from maciota_bot.main import main
from maciota_bot.services.welcome import WELCOME_TEMPLATES
from maciota_bot.state import AppState, configure, get_state


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


class _Guild:
    def __init__(self, channel: _Channel | None) -> None:
        self.id = 1
        self.system_channel = channel


class _Member:
    def __init__(
        self,
        mention: str,
        *,
        bot: bool = False,
        channel: _Channel | None,
    ) -> None:
        self.mention = mention
        self.name = 'ada'
        self.bot = bot
        self.guild = _Guild(channel)


async def _close_database() -> None:
    engine = get_state().engine
    configure(AppState())
    if engine is not None:
        await engine.dispose()


def _restore(*names: str) -> None:
    for name in names:
        logger = logging.getLogger(name)
        for handler in list(logger.handlers):
            handler.close()
            logger.removeHandler(handler)
        logger.propagate = True
        logger.setLevel(logging.NOTSET)


async def test_main_logs_in_with_the_token_and_answers_ping(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    captured: dict[str, object] = {}

    def run(
        self: discord.Client,
        token: str,
        *,
        log_handler: object = None,
    ) -> None:
        captured['client'] = self
        captured['token'] = token
        captured['log_handler'] = log_handler

    monkeypatch.setattr(discord.Client, 'run', run)
    try:
        main()

        assert captured['token'] == 'test-token'
        assert captured['log_handler'] is None
        client = captured['client']
        assert isinstance(client, discord.Client)
        assert get_state().engine is not None
        assert get_state().tree is client.tree
        assert client.on_ready is on_ready
        assert client.on_message is on_message
        assert client.on_member_join is on_member_join
        message = _Message('!ping')
        await client.on_message(message)
        assert message.channel.sent == ['pong']
    finally:
        await _close_database()
        _restore('maciota_bot', 'discord', 'discord.http')


async def test_main_sends_a_welcome_when_a_member_joins(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    captured: dict[str, object] = {}

    def run(
        self: discord.Client,
        token: str,
        *,
        log_handler: object = None,
    ) -> None:
        captured['client'] = self

    async def sync(
        self: discord.app_commands.CommandTree,
        *,
        guild: object = None,
    ) -> list[object]:
        return []

    monkeypatch.setattr(discord.Client, 'run', run)
    monkeypatch.setattr(discord.app_commands.CommandTree, 'sync', sync)
    try:
        main()

        client = captured['client']
        assert isinstance(client, discord.Client)
        await client.on_ready()
        assert (tmp_path / 'maciota.db').is_file()
        channel = _Channel()
        member = _Member('<@42>', channel=channel)
        await client.on_member_join(member)
        expected = [
            template.replace('{user_name}', '<@42>') for template in WELCOME_TEMPLATES
        ]
        assert len(channel.sent) == 1
        assert channel.sent[0] in expected
        assert 'ada' not in channel.sent[0]
    finally:
        await _close_database()
        _restore('maciota_bot', 'discord', 'discord.http')


async def test_main_syncs_the_welcome_command_when_ready(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    record_bot_connected: Callable[[list[str]], logging.Handler],
) -> None:
    monkeypatch.chdir(tmp_path)
    captured: dict[str, object] = {}
    order: list[str] = []

    def run(
        self: discord.Client,
        token: str,
        *,
        log_handler: object = None,
    ) -> None:
        captured['client'] = self

    async def sync(
        self: discord.app_commands.CommandTree,
        *,
        guild: object = None,
    ) -> list[object]:
        order.append('sync')
        return []

    monkeypatch.setattr(discord.Client, 'run', run)
    monkeypatch.setattr(discord.app_commands.CommandTree, 'sync', sync)
    handler = record_bot_connected(order)
    events_logger = logging.getLogger('maciota_bot.events')
    try:
        main()

        client = captured['client']
        assert isinstance(client, discord.Client)
        events_logger.addHandler(handler)
        await client.on_ready()
        assert order == ['log', 'sync']
        command = client.tree.get_command('boas-vindas')
        assert command is not None
        assert command.name == 'boas-vindas'
        assert command.guild_only is True
        assert command.default_permissions is not None
        assert command.default_permissions.administrator is True
        assert command.get_parameter('canal') is not None
    finally:
        events_logger.removeHandler(handler)
        await _close_database()
        _restore('maciota_bot', 'discord', 'discord.http')
