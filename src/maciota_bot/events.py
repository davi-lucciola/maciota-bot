import logging
from typing import Literal

import discord

from maciota_bot.agent import build_agent
from maciota_bot.agent.schema import AgentInput, AgentOutput
from maciota_bot.db import init_db
from maciota_bot.services.welcome import (
    build_welcome_message,
    get_welcome_channel_id,
)
from maciota_bot.state import get_state

logger = logging.getLogger(__name__)


async def on_ready() -> None:
    state = get_state()

    if state.agent is None:
        state.agent = await build_agent()
    await init_db(state.engine)
    await state.tree.sync()

    logger.info('Bot conectado')


async def on_message(message: discord.Message) -> None:
    if message.author.bot or message.guild is None:
        return

    state = get_state()
    agent = state.agent
    if agent is None:
        return

    user = state.client.user
    trigger_type: Literal['mention', 'proactive'] = (
        'mention' if user is not None and user.mentioned_in(message) else 'proactive'
    )
    try:
        output = await agent.execute(_turn(message, trigger_type))
        await _send_output(message, output)
    except Exception:
        logger.exception('Falha ao responder no canal')


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


def _turn(
    message: discord.Message,
    trigger_type: Literal['mention', 'proactive'],
) -> AgentInput:
    channel = message.channel
    guild = message.guild
    assert guild is not None
    return AgentInput(
        channel_id=channel.id,
        message_id=message.id,
        author_name=message.author.display_name,
        content=message.content,
        trigger_type=trigger_type,
        guild_name=guild.name,
        guild_description=guild.description,
        channel_name=getattr(channel, 'name', None),
        channel_topic=getattr(channel, 'topic', None),
    )


async def _send_output(message: discord.Message, output: AgentOutput) -> None:
    if not output.text.strip():
        return

    reference = None
    guild = message.guild
    assert guild is not None
    if output.reply_to_message_id is not None:
        reference = discord.MessageReference(
            message_id=output.reply_to_message_id,
            channel_id=message.channel.id,
            guild_id=guild.id,
        )
    await message.channel.send(output.text, reference=reference)


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
