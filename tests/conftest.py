import logging
import os
from collections.abc import AsyncIterator, Callable
from pathlib import Path

import pytest

from maciota_bot.state import AppState, configure
from tests.support import release_engine

# Importing maciota_bot.config builds Settings immediately.
os.environ['DISCORD_TOKEN'] = 'test-token'

_KINDS = frozenset({'unit', 'integration'})


def _record_bot_connected(order: list[str]) -> logging.Handler:
    class _ConnectedHandler(logging.Handler):
        def __init__(self) -> None:
            super().__init__()
            self.order = order

        def emit(self, record: logging.LogRecord) -> None:
            if record.getMessage() == 'Bot conectado':
                self.order.append('log')

    return _ConnectedHandler()


@pytest.fixture
def record_bot_connected() -> Callable[[list[str]], logging.Handler]:
    return _record_bot_connected


@pytest.fixture(autouse=True)
async def _reset_state() -> AsyncIterator[None]:
    configure(AppState())
    yield
    await release_engine()


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    tests_root = Path(__file__).parent
    for item in items:
        parts = item.path.resolve().relative_to(tests_root).parts
        if not parts or parts[0] not in _KINDS:
            continue
        item.add_marker(getattr(pytest.mark, parts[0]))
        if len(parts) >= 3:
            item.add_marker(getattr(pytest.mark, parts[1]))
