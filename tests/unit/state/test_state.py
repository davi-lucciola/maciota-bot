from collections.abc import AsyncIterator
from pathlib import Path

import pytest

from maciota_bot.db import create_db_engine
from maciota_bot.state import AppState, configure, get_state


@pytest.fixture(autouse=True)
async def _reset_state() -> AsyncIterator[None]:
    configure(AppState())
    yield
    engine = get_state().engine
    configure(AppState())
    if engine is not None:
        await engine.dispose()


async def test_configure_publishes_the_engine_get_state_returns(tmp_path: Path) -> None:
    engine = create_db_engine(f'sqlite:///{tmp_path / "state.db"}')
    configure(AppState(engine=engine))

    assert get_state().engine is engine
    assert engine.url.drivername == 'sqlite+aiosqlite'


async def test_sqlite_aiosqlite_url_keeps_the_driver(tmp_path: Path) -> None:
    engine = create_db_engine(f'sqlite+aiosqlite:///{tmp_path / "already.db"}')
    configure(AppState(engine=engine))

    assert get_state().engine is engine
    assert engine.url.drivername == 'sqlite+aiosqlite'
