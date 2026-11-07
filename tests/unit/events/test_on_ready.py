import logging
from collections.abc import Callable
from pathlib import Path

from sqlalchemy import inspect

from maciota_bot.db import create_db_engine
from maciota_bot.events import on_ready
from maciota_bot.models import GuildWelcomeChannel
from maciota_bot.state import configure
from tests.support import make_state


class _Tree:
    def __init__(self, order: list[str]) -> None:
        self.order = order

    async def sync(self) -> list[object]:
        self.order.append('sync')
        return []


async def test_on_ready_syncs_then_logs(
    record_bot_connected: Callable[[list[str]], logging.Handler],
    tmp_path: Path,
) -> None:
    order: list[str] = []
    engine = create_db_engine(f'sqlite:///{tmp_path / "ready-log.db"}')
    configure(make_state(engine, tree=_Tree(order)))
    handler = record_bot_connected(order)
    events_logger = logging.getLogger('maciota_bot.events')
    events_logger.setLevel(logging.INFO)
    events_logger.addHandler(handler)
    try:
        await on_ready()
    finally:
        events_logger.removeHandler(handler)
        events_logger.setLevel(logging.NOTSET)

    assert order == ['sync', 'log']


async def test_on_ready_creates_the_welcome_table(tmp_path: Path) -> None:
    database = tmp_path / 'ready.db'
    engine = create_db_engine(f'sqlite:///{database}')
    configure(make_state(engine, tree=_Tree([])))

    await on_ready()

    assert database.is_file()

    def table_names(sync_connection: object) -> list[str]:
        return list(inspect(sync_connection).get_table_names())

    async with engine.connect() as connection:
        names = await connection.run_sync(table_names)
    assert GuildWelcomeChannel.__tablename__ in names
