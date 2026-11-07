import logging
from collections.abc import AsyncIterator, Callable
from pathlib import Path

import pytest

from maciota_bot.db import create_db_engine
from maciota_bot.events import on_ready
from maciota_bot.services.welcome import get_welcome_channel_id
from maciota_bot.state import AppState, configure, get_state


class _Tree:
    def __init__(self, order: list[str]) -> None:
        self.order = order

    async def sync(self) -> list[object]:
        self.order.append('sync')
        return []


@pytest.fixture(autouse=True)
async def _reset_state() -> AsyncIterator[None]:
    configure(AppState())
    yield
    engine = get_state().engine
    configure(AppState())
    if engine is not None:
        await engine.dispose()


async def test_on_ready_logs_then_syncs(
    record_bot_connected: Callable[[list[str]], logging.Handler],
) -> None:
    order: list[str] = []
    configure(AppState(tree=_Tree(order)))
    handler = record_bot_connected(order)
    events_logger = logging.getLogger('maciota_bot.events')
    events_logger.setLevel(logging.INFO)
    events_logger.addHandler(handler)
    try:
        await on_ready()
    finally:
        events_logger.removeHandler(handler)
        events_logger.setLevel(logging.NOTSET)

    assert order == ['log', 'sync']


async def test_on_ready_creates_the_welcome_table(tmp_path: Path) -> None:
    database = tmp_path / 'ready.db'
    engine = create_db_engine(f'sqlite:///{database}')
    configure(AppState(engine=engine, tree=_Tree([])))

    await on_ready()

    assert database.is_file()
    assert await get_welcome_channel_id(1) is None
