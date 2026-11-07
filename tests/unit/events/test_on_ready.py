import logging
from collections.abc import Iterator

import pytest

from maciota_bot.events import on_ready
from maciota_bot.state import AppState, configure


class _Tree:
    def __init__(self, order: list[str]) -> None:
        self.order = order

    async def sync(self) -> list[object]:
        self.order.append('sync')
        return []


class _Handler(logging.Handler):
    def __init__(self, order: list[str]) -> None:
        super().__init__()
        self.order = order

    def emit(self, record: logging.LogRecord) -> None:
        if record.getMessage() == 'Bot conectado':
            self.order.append('log')


@pytest.fixture(autouse=True)
def _reset_state() -> Iterator[None]:
    configure(AppState())
    yield
    configure(AppState())


async def test_on_ready_logs_then_syncs() -> None:
    order: list[str] = []
    configure(AppState(tree=_Tree(order)))
    handler = _Handler(order)
    events_logger = logging.getLogger('maciota_bot.events')
    events_logger.setLevel(logging.INFO)
    events_logger.addHandler(handler)
    try:
        await on_ready()
    finally:
        events_logger.removeHandler(handler)
        events_logger.setLevel(logging.NOTSET)

    assert order == ['log', 'sync']
