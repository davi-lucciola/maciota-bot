import logging

import discord


logger = logging.getLogger(__name__)

async def on_ready() -> None:
    logger.info("Bot conectado")


async def on_message(message: discord.Message) -> None:
    if message.author.bot:
        return
    
    if message.content.strip().lower() != "!ping":
        return
    
    await message.channel.send("pong")
