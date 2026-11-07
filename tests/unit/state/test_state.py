from pathlib import Path

from maciota_bot.db import create_db_engine
from maciota_bot.state import configure, get_state
from tests.support import make_state


async def test_configure_publishes_the_engine_get_state_returns(tmp_path: Path) -> None:
    engine = create_db_engine(f'sqlite:///{tmp_path / "state.db"}')
    configure(make_state(engine))

    assert get_state().engine is engine
    assert engine.url.drivername == 'sqlite+aiosqlite'


async def test_sqlite_aiosqlite_url_keeps_the_driver(tmp_path: Path) -> None:
    engine = create_db_engine(f'sqlite+aiosqlite:///{tmp_path / "already.db"}')
    configure(make_state(engine))

    assert get_state().engine is engine
    assert engine.url.drivername == 'sqlite+aiosqlite'
