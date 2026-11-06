import logging

import discord

from maciota_bot.services.welcome import build_welcome_message

logger = logging.getLogger(__name__)


async def on_ready() -> None:
    logger.info('Bot conectado')


async def on_message(message: discord.Message) -> None:
    if message.author.bot:
        return

    if message.content.strip().lower() != '!ping':
        return

    await message.channel.send('pong')


async def on_member_join(member: discord.Member) -> None:
    if member.bot:
        return

    channel = member.guild.system_channel
    if channel is None:
        logger.warning('Canal de sistema ausente')
        return

    await channel.send(build_welcome_message(member.name))
