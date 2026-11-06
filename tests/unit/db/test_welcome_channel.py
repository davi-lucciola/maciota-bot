from pathlib import Path

from maciota_bot.db import (
    create_db_engine,
    get_welcome_channel_id,
    init_db,
    set_welcome_channel,
)


def _engine(database: Path):
    engine = create_db_engine(f'sqlite:///{database}')
    init_db(engine)
    return engine


def test_missing_row_returns_none(tmp_path: Path) -> None:
    engine = _engine(tmp_path / 'welcome.db')

    assert get_welcome_channel_id(engine, 1) is None

    engine.dispose()


def test_set_writes_and_replaces_the_channel_for_the_same_guild(
    tmp_path: Path,
) -> None:
    engine = _engine(tmp_path / 'welcome.db')

    set_welcome_channel(engine, 7, 100)
    set_welcome_channel(engine, 8, 300)
    assert get_welcome_channel_id(engine, 7) == 100

    set_welcome_channel(engine, 7, 200)

    assert get_welcome_channel_id(engine, 7) == 200
    assert get_welcome_channel_id(engine, 8) == 300
    engine.dispose()


def test_saved_channel_survives_closing_and_opening_the_file(
    tmp_path: Path,
) -> None:
    database = tmp_path / 'welcome.db'
    engine = _engine(database)
    set_welcome_channel(engine, 4, 55)
    engine.dispose()

    reopened = create_db_engine(f'sqlite:///{database}')
    try:
        assert get_welcome_channel_id(reopened, 4) == 55
    finally:
        reopened.dispose()
