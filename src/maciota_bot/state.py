from dataclasses import dataclass

from discord import app_commands
from sqlalchemy.ext.asyncio import AsyncEngine


@dataclass
class AppState:
    engine: AsyncEngine | None = None
    tree: app_commands.CommandTree | None = None


class _StateHolder:
    current: AppState | None = None


def get_state() -> AppState:
    if _StateHolder.current is None:
        raise RuntimeError('Application state is not configured')
    return _StateHolder.current


def configure(state: AppState) -> None:
    _StateHolder.current = state
