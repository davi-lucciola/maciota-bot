from collections.abc import Iterator
from pathlib import Path

import pytest

from maciota_bot.db import create_db_engine
from maciota_bot.state import AppState, configure


@pytest.fixture(autouse=True)
def _reset_state() -> Iterator[None]:
    configure(AppState())
    yield
    configure(AppState())


def test_replacing_the_state_disposes_the_previous_engine(tmp_path: Path) -> None:
    engine = create_db_engine(f'sqlite:///{tmp_path / "state.db"}')
    pool = engine.pool
    configure(AppState(engine=engine))

    configure(AppState())

    assert engine.pool is not pool
