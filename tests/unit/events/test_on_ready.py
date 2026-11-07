import logging
from collections.abc import Callable
from pathlib import Path

from sqlalchemy import inspect

from maciota_bot.db import create_db_engine
from maciota_bot.events import on_ready
from maciota_bot.models import GuildWelcomeChannel
from maciota_bot.state import AppState, configure


class _Tree:
    def __init__(self, order: list[str]) -> None:
        self.order = order

    async def sync(self) -> list[object]:
        self.order.append('sync')
        return []


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

    def table_names(sync_connection: object) -> list[str]:
        return list(inspect(sync_connection).get_table_names())

    async with engine.connect() as connection:
        names = await connection.run_sync(table_names)
    assert GuildWelcomeChannel.__tablename__ in names
