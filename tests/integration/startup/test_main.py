import logging
from pathlib import Path

import discord
import pytest

from maciota_bot.main import main


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
        _restore('maciota_bot', 'discord', 'discord.http')
