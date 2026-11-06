import logging
from pathlib import Path

import discord
import pytest

from maciota_bot.db import configure_engine
from maciota_bot.main import main
from maciota_bot.services.welcome import WELCOME_TEMPLATES


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


def _close_database() -> None:
    configure_engine(None)


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
        message = _Message('!ping')
        await client.on_message(message)
        assert message.channel.sent == ['pong']
    finally:
        _close_database()
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

    monkeypatch.setattr(discord.Client, 'run', run)
    try:
        main()

        client = captured['client']
        assert isinstance(client, discord.Client)
        channel = _Channel()
        member = _Member('<@42>', channel=channel)
        await client.on_member_join(member)
        expected = [
            template.replace('{user_name}', '<@42>') for template in WELCOME_TEMPLATES
        ]
        assert len(channel.sent) == 1
        assert channel.sent[0] in expected
        assert 'ada' not in channel.sent[0]
        assert (tmp_path / 'maciota.db').is_file()
    finally:
        _close_database()
        _restore('maciota_bot', 'discord', 'discord.http')


async def test_main_syncs_the_welcome_command_when_ready(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
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

    class _Handler(logging.Handler):
        def __init__(self, events: list[str]) -> None:
            super().__init__()
            self.events = events

        def emit(self, record: logging.LogRecord) -> None:
            if record.getMessage() == 'Bot conectado':
                self.events.append('log')

    monkeypatch.setattr(discord.Client, 'run', run)
    monkeypatch.setattr(discord.app_commands.CommandTree, 'sync', sync)
    handler = _Handler(order)
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
        _close_database()
        _restore('maciota_bot', 'discord', 'discord.http')
