import logging
from collections.abc import Callable
from pathlib import Path

import discord
import pytest

from maciota_bot.agent import BotAgent
from maciota_bot.client import MaciotaClient
from maciota_bot.client.events import on_member_join, on_message
from maciota_bot.main import main
from maciota_bot.services.welcome import WELCOME_TEMPLATES
from maciota_bot.state import get_state
from tests.support import release_engine


class _Author:
    def __init__(self, *, bot: bool) -> None:
        self.bot = bot


class _Channel:
    def __init__(self) -> None:
        self.sent: list[str] = []

    async def send(self, content: str) -> None:
        self.sent.append(content)


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


def _restore(*names: str) -> None:
    for name in names:
        logger = logging.getLogger(name)
        for handler in list(logger.handlers):
            handler.close()
            logger.removeHandler(handler)
        logger.propagate = True
        logger.setLevel(logging.NOTSET)


async def test_main_logs_in_with_the_token_and_publishes_the_agent(
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
        assert isinstance(client, MaciotaClient)
        assert client.on_message is on_message
        assert client.on_member_join is on_member_join
    finally:
        await release_engine()
        _restore('maciota_bot', 'discord', 'discord.http')


async def test_main_sends_a_welcome_when_a_member_joins(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / 'data').mkdir()
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
        assert isinstance(client, MaciotaClient)
        await client.on_ready()
        assert isinstance(get_state().agent, BotAgent)
        assert (tmp_path / 'data' / 'maciota.db').is_file()
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
        await release_engine()
        _restore('maciota_bot', 'discord', 'discord.http')


async def test_main_syncs_the_welcome_command_when_ready(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    record_bot_connected: Callable[[list[str]], logging.Handler],
) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / 'data').mkdir()
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
    client_logger = logging.getLogger('maciota_bot')
    try:
        main()

        client = captured['client']
        assert isinstance(client, MaciotaClient)
        client_logger.addHandler(handler)
        await client.on_ready()
        assert isinstance(get_state().agent, BotAgent)
        assert order == ['sync', 'log']
        welcome = client.tree.get_command('welcome')
        assert welcome is not None
        assert welcome.name == 'welcome'
        assert welcome.guild_only is True
        assert welcome.default_permissions is not None
        assert welcome.default_permissions.administrator is True
        assert welcome.get_parameter('channel') is not None
        acidity = client.tree.get_command('acidity')
        assert acidity is not None
        assert acidity.name == 'acidity'
        assert acidity.guild_only is True
        assert acidity.default_permissions is not None
        assert acidity.default_permissions.administrator is True
        level = acidity.get_parameter('level')
        assert level is not None
        assert {choice.value for choice in level.choices} == {
            'mild',
            'medium',
            'sharp',
        }
        assert client.tree.get_command('boas-vindas') is None
    finally:
        client_logger.removeHandler(handler)
        await release_engine()
        _restore('maciota_bot', 'discord', 'discord.http')
