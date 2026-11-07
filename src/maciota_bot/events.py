import logging

import discord

from maciota_bot.db import init_db
from maciota_bot.services.welcome import (
    build_welcome_message,
    get_welcome_channel_id,
)
from maciota_bot.state import get_state

logger = logging.getLogger(__name__)


async def on_ready() -> None:
    state = get_state()

    await init_db(state.engine)
    await state.tree.sync()

    logger.info('Bot conectado')


async def on_message(message: discord.Message) -> None:
    if message.author.bot:
        return

    state = get_state()
    user = state.client.user
    trigger_type = (
        'mention' if user is not None and user.mentioned_in(message) else 'proactive'
    )
    try:
        text = await state.agent.execute(
            channel_id=message.channel.id,
            message_id=message.id,
            author_name=message.author.display_name,
            content=message.content,
            trigger_type=trigger_type,
        )
    except Exception:
        logger.exception('Falha ao responder no canal')
        return

    if text.strip():
        await message.channel.send(text)


async def on_member_join(member: discord.Member) -> None:
    if member.bot:
        return

    channel = await _configured_channel(member)
    if channel is None:
        channel = member.guild.system_channel
    if channel is None:
        logger.warning('Canal de sistema ausente')
        return

    message = build_welcome_message(member.mention)
    await channel.send(message)


async def _configured_channel(
    member: discord.Member,
) -> discord.abc.Messageable | None:
    channel_id = await get_welcome_channel_id(member.guild.id)
    if channel_id is None:
        return None

    channel = member.guild.get_channel(channel_id)
    if channel is None:
        logger.warning('Canal de boas-vindas ausente')
        return None
    return channel
