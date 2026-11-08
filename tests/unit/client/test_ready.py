import io
import logging
import os
from collections.abc import Callable
from pathlib import Path

import pytest
from sqlalchemy import inspect

from maciota_bot.client import MaciotaClient
from maciota_bot.models import GuildWelcomeChannel
from maciota_bot.state import get_state


class _Tree:
    def __init__(self, order: list[str]) -> None:
        self.order = order

    async def sync(self) -> list[object]:
        self.order.append('sync')
        return []


async def test_on_ready_syncs_then_logs(
    record_bot_connected: Callable[[list[str]], logging.Handler],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / 'data').mkdir()
    order: list[str] = []
    client = MaciotaClient()
    client.tree = _Tree(order)
    handler = record_bot_connected(order)
    client_logger = logging.getLogger('maciota_bot')
    client_logger.setLevel(logging.INFO)
    client_logger.addHandler(handler)
    try:
        await client.on_ready()
    finally:
        client_logger.removeHandler(handler)
        client_logger.setLevel(logging.NOTSET)

    assert order == ['sync', 'log']


async def test_on_ready_creates_the_welcome_table(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / 'data').mkdir()
    client = MaciotaClient()
    client.tree = _Tree([])

    await client.on_ready()

    assert (tmp_path / 'data' / 'maciota.db').is_file()

    def table_names(sync_connection: object) -> list[str]:
        return list(inspect(sync_connection).get_table_names())

    async with get_state().engine.connect() as connection:
        names = await connection.run_sync(table_names)
    assert GuildWelcomeChannel.__tablename__ in names


def _record_exit(exited: list[int]) -> Callable[[int], None]:
    def record(code: int) -> None:
        exited.append(code)

    return record


def _capture(name: str) -> tuple[logging.Logger, io.StringIO, logging.Handler]:
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    logger = logging.getLogger(name)
    logger.addHandler(handler)
    logger.setLevel(logging.ERROR)
    return logger, stream, handler


async def test_on_ready_error_logs_to_the_console_and_exits(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    exited: list[int] = []
    monkeypatch.setattr(os, '_exit', _record_exit(exited))
    bot_logger, console, bot_handler = _capture('maciota_bot')
    discord_logger, discord_log, discord_handler = _capture('discord')
    client = MaciotaClient()
    try:
        raise RuntimeError('unable to open database file')
    except RuntimeError:
        await client.on_error('on_ready')
    finally:
        bot_logger.removeHandler(bot_handler)
        discord_logger.removeHandler(discord_handler)
        bot_logger.setLevel(logging.NOTSET)
        discord_logger.setLevel(logging.NOTSET)

    assert exited == [1]
    assert 'unable to open database file' in console.getvalue()
    assert 'unable to open database file' in discord_log.getvalue()


async def test_other_event_errors_do_not_exit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    exited: list[int] = []
    monkeypatch.setattr(os, '_exit', _record_exit(exited))
    client = MaciotaClient()

    try:
        raise RuntimeError('message failed')
    except RuntimeError:
        await client.on_error('on_message')

    assert exited == []
