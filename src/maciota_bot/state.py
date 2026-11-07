from dataclasses import dataclass

from discord import app_commands
from sqlalchemy.engine import Engine


@dataclass
class AppState:
    engine: Engine | None = None
    tree: app_commands.CommandTree | None = None


class _StateHolder:
    current = AppState()


def current() -> AppState:
    return _StateHolder.current


def configure(state: AppState) -> None:
    previous = _StateHolder.current.engine
    _StateHolder.current = state
    if previous is not None and previous is not state.engine:
        previous.dispose()
