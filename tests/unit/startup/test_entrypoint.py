from pathlib import Path

from maciota_bot.entrypoint import sqlite_parent_directories


def test_default_sqlite_parents_are_data() -> None:
    assert sqlite_parent_directories() == [Path('data'), Path('data')]
