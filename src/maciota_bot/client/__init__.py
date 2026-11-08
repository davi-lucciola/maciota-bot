import logging

import discord

from maciota_bot import state as app_state
from maciota_bot.agent import build_agent
from maciota_bot.client.commands import build_command_tree
from maciota_bot.client.events import on_member_join, on_message
from maciota_bot.config import settings
from maciota_bot.db import create_db_engine, ensure_sqlite_parents, init_db
from maciota_bot.state import get_state

logger = logging.getLogger('maciota_bot')


def get_intents() -> discord.Intents:
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    return intents


class MaciotaClient(discord.Client):
    def __init__(self) -> None:
        super().__init__(intents=get_intents())
        self.tree = build_command_tree(self)

        self.event(on_message)
        self.event(on_member_join)

        ensure_sqlite_parents(settings.database_url, settings.checkpoint_path)

    async def on_ready(self) -> None:
        agent = await build_agent()
        engine = create_db_engine(settings.database_url)

        state = app_state.AppState(engine=engine, agent=agent, client=self)
        app_state.configure(state)

        await init_db(state.engine)
        await self.tree.sync()

        logger.info('Maciota está na atividade, conectado.')

    async def close(self) -> None:
        state = get_state()

        await state.agent.aclose()
        await super().close()

        logger.info('Maciota está vazando, servidor ta melado.')
