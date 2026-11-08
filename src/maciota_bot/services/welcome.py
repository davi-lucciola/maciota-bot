import logging
import random

import discord
from sqlmodel.ext.asyncio.session import AsyncSession

from maciota_bot.db import get_session
from maciota_bot.models import GuildWelcomeChannel

logger = logging.getLogger(__name__)

WELCOME_TEMPLATES: tuple[str, ...] = (
    '{user_name} entrou. Esconde o controle antes que peça.',
    'Chegou {user_name}. A zueira subiu e ninguém avisou.',
    '{user_name} passou na portaria. A ficha ainda não caiu.',
    'Silêncio na sala: {user_name} chegou pedindo palco.',
    '{user_name} entrou. Podem aplaudir. Ou fingir que não viram.',
    'Olha só: {user_name}. Trouxe desculpa ou só a cara de pau?',
    '{user_name} logou. O grupo tremeu e o lanche sumiu.',
    '{user_name} chegou. Aqui o tapete de boas-vindas é uma casca de banana.',
)


def build_welcome_message(user_name: str) -> str:
    template = random.choice(WELCOME_TEMPLATES)
    return template.replace('{user_name}', user_name)


async def _find_welcome_row(
    session: AsyncSession, guild_id: int
) -> GuildWelcomeChannel | None:
    return await session.get(GuildWelcomeChannel, guild_id)


async def _save_welcome_channel(
    session: AsyncSession, guild_channel: GuildWelcomeChannel
) -> None:
    session.add(guild_channel)
    await session.commit()


async def get_welcome_channel_id(guild_id: int) -> int | None:
    async with get_session() as session:
        row = await _find_welcome_row(session, guild_id)

        if row is None:
            return None

        return row.channel_id


async def set_welcome_channel(guild_id: int, channel_id: int) -> None:
    async with get_session() as session:
        row = await _find_welcome_row(session, guild_id)

        if row is not None:
            row.channel_id = channel_id
            await session.commit()
            return

        guild_channel = GuildWelcomeChannel(guild_id=guild_id, channel_id=channel_id)
        await _save_welcome_channel(session, guild_channel)


async def define_welcome_channel(
    interaction: discord.Interaction,
    canal: discord.TextChannel,
) -> None:
    guild = interaction.guild
    assert guild is not None

    if not interaction.user.guild_permissions.administrator:
        await _reply(
            interaction,
            'Only administrators can set the welcome channel.',
        )
        return

    if not _channel_in_guild(canal, guild):
        await _reply(interaction, 'That channel is not in this server.')
        return

    await set_welcome_channel(guild.id, canal.id)
    await _reply(
        interaction,
        f'Welcome channel set to {canal.mention}.',
    )


async def greet(member: discord.Member) -> None:
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


async def _reply(interaction: discord.Interaction, content: str) -> None:
    await interaction.response.send_message(content, ephemeral=True)


def _channel_in_guild(canal: discord.TextChannel, guild: discord.Guild) -> bool:
    canal_guild = getattr(canal, 'guild', None)
    if canal_guild is None or canal_guild.id != guild.id:
        return False
    resolved = guild.get_channel(canal.id)
    return resolved is not None and resolved.id == canal.id
