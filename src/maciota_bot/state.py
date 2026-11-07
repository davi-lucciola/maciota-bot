from dataclasses import dataclass

import discord
from discord import app_commands
from sqlalchemy.ext.asyncio import AsyncEngine

from maciota_bot.agent import Agent


@dataclass
class AppState:
    engine: AsyncEngine
    tree: app_commands.CommandTree
    agent: Agent
    client: discord.Client


_state: AppState | None = None


def get_state() -> AppState:
    if _state is None:
        raise RuntimeError('Application state is not configured')

    return _state


def configure(state: AppState) -> None:
    global _state  # noqa: PLW0603
    _state = state
