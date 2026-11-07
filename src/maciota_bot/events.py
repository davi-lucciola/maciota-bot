import logging

import discord

from maciota_bot.services.welcome import build_welcome_message
from maciota_bot.services.welcome_channel import get_welcome_channel_id
from maciota_bot.state import current

logger = logging.getLogger(__name__)


async def on_ready() -> None:
    logger.info('Bot conectado')
    tree = current().tree
    assert tree is not None
    await tree.sync()


async def on_message(message: discord.Message) -> None:
    if message.author.bot:
        return

    if message.content.strip().lower() != '!ping':
        return

    await message.channel.send('pong')


async def on_member_join(member: discord.Member) -> None:
    if member.bot:
        return

    channel = _configured_channel(member)
    if channel is None:
        channel = member.guild.system_channel
    if channel is None:
        logger.warning('Canal de sistema ausente')
        return

    message = build_welcome_message(member.mention)
    await channel.send(message)


def _configured_channel(member: discord.Member) -> discord.abc.Messageable | None:
    channel_id = get_welcome_channel_id(member.guild.id)
    if channel_id is None:
        return None

    channel = member.guild.get_channel(channel_id)
    if channel is None:
        logger.warning('Canal de boas-vindas ausente')
        return None
    return channel
