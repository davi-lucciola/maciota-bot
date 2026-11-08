import logging
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
    client = MaciotaClient()
    client.tree = _Tree([])

    await client.on_ready()

    assert (tmp_path / 'maciota.db').is_file()

    def table_names(sync_connection: object) -> list[str]:
        return list(inspect(sync_connection).get_table_names())

    async with get_state().engine.connect() as connection:
        names = await connection.run_sync(table_names)
    assert GuildWelcomeChannel.__tablename__ in names
