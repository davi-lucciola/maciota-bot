import logging

import discord

from maciota_bot.agent import build_agent
from maciota_bot.client.commands import build_command_tree
from maciota_bot.client.events import on_member_join, on_message
from maciota_bot.db import init_db
from maciota_bot.state import get_state

logger = logging.getLogger(__name__)


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

    async def on_ready(self) -> None:
        state = get_state()

        if state.agent is None:
            state.agent = await build_agent()

        await init_db(state.engine)
        await self.tree.sync()

        logger.info('Bot conectado')

    async def close(self) -> None:
        agent = get_state().agent
        if agent is not None:
            await agent.aclose()
        await super().close()
