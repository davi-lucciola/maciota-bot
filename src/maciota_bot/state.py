from dataclasses import dataclass

from discord import app_commands
from sqlalchemy.ext.asyncio import AsyncEngine


@dataclass
class AppState:
    engine: AsyncEngine | None = None
    tree: app_commands.CommandTree | None = None


_state: AppState | None = None


def get_state() -> AppState:
    if _state is None:
        raise RuntimeError('Application state is not configured')
    return _state


def configure(state: AppState) -> None:
    global _state  # noqa: PLW0603
    _state = state
