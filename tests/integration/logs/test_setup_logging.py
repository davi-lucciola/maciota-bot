import logging
import logging.handlers
from pathlib import Path

import pytest

from maciota_bot.config import settings
from maciota_bot.logs import ColourFormatter, setup_logging


def _restore(*names: str) -> None:
    for name in names:
        logger = logging.getLogger(name)
        for handler in list(logger.handlers):
            handler.close()
            logger.removeHandler(handler)
        logger.propagate = True
        logger.setLevel(logging.NOTSET)


def test_setup_logging_splits_console_and_discord_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    setup_logging()
    try:
        bot_logger = logging.getLogger('maciota_bot')
        discord_logger = logging.getLogger('discord')

        assert bot_logger.propagate is False
        assert bot_logger.level == logging.getLevelNamesMapping()[settings.log_level]
        [console] = bot_logger.handlers
        assert type(console) is logging.StreamHandler
        assert isinstance(console.formatter, ColourFormatter)

        assert discord_logger.propagate is False
        [file_handler] = discord_logger.handlers
        assert isinstance(file_handler, logging.handlers.RotatingFileHandler)
        assert Path(file_handler.baseFilename) == tmp_path / 'discord.log'
    finally:
        _restore('maciota_bot', 'discord', 'discord.http')


def test_setup_logging_uses_the_configured_console_level(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(settings, 'log_level', 'DEBUG')
    setup_logging()
    try:
        bot_logger = logging.getLogger('maciota_bot')
        assert bot_logger.level == logging.DEBUG
    finally:
        _restore('maciota_bot', 'discord', 'discord.http')
