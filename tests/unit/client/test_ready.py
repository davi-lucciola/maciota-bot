import logging
from collections.abc import Callable
from pathlib import Path

from sqlalchemy import inspect

from maciota_bot.client import MaciotaClient
from maciota_bot.db import create_db_engine
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
    client = MaciotaClient()
    tree = _Tree(order)
    client.tree = tree
    configure(make_state(engine, tree=tree, client=client))
    handler = record_bot_connected(order)
    client_logger = logging.getLogger('maciota_bot.client.bot')
    client_logger.setLevel(logging.INFO)
    client_logger.addHandler(handler)
    try:
        await client.on_ready()
    finally:
        client_logger.removeHandler(handler)
        client_logger.setLevel(logging.NOTSET)

    assert order == ['sync', 'log']


async def test_on_ready_creates_the_welcome_table(tmp_path: Path) -> None:
    database = tmp_path / 'ready.db'
    engine = create_db_engine(f'sqlite:///{database}')
    client = MaciotaClient()
    tree = _Tree([])
    client.tree = tree
    configure(make_state(engine, tree=tree, client=client))

    await client.on_ready()

    assert database.is_file()

    def table_names(sync_connection: object) -> list[str]:
        return list(inspect(sync_connection).get_table_names())

    async with engine.connect() as connection:
        names = await connection.run_sync(table_names)
    assert GuildWelcomeChannel.__tablename__ in names
