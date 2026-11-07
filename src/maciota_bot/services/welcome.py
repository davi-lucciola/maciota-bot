import random

import discord
from sqlmodel.ext.asyncio.session import AsyncSession

from maciota_bot.models import GuildWelcomeChannel
from maciota_bot.state import get_state

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
    session: AsyncSession,
    guild_id: int,
) -> GuildWelcomeChannel | None:
    return await session.get(GuildWelcomeChannel, guild_id)


async def get_welcome_channel_id(guild_id: int) -> int | None:
    engine = get_state().engine
    if engine is None:
        return None
    async with AsyncSession(engine) as session:
        row = await _find_welcome_row(session, guild_id)
        if row is None:
            return None
        return row.channel_id


async def set_welcome_channel(guild_id: int, channel_id: int) -> None:
    engine = get_state().engine
    if engine is None:
        raise RuntimeError('Database engine is not configured')
    async with AsyncSession(engine) as session:
        row = await _find_welcome_row(session, guild_id)
        if row is None:
            session.add(
                GuildWelcomeChannel(guild_id=guild_id, channel_id=channel_id),
            )
        else:
            row.channel_id = channel_id
        await session.commit()


async def define_welcome_channel(
    interaction: discord.Interaction,
    canal: discord.TextChannel,
) -> None:
    guild = interaction.guild
    assert guild is not None

    if not interaction.user.guild_permissions.administrator:
        await _reply(
            interaction,
            'Só administradores podem definir o canal de boas-vindas.',
        )
        return

    if not _channel_in_guild(canal, guild):
        await _reply(interaction, 'Esse canal não existe neste servidor.')
        return

    await set_welcome_channel(guild.id, canal.id)
    await _reply(
        interaction,
        f'Canal de boas-vindas definido para {canal.mention}.',
    )


async def _reply(interaction: discord.Interaction, content: str) -> None:
    await interaction.response.send_message(content, ephemeral=True)


def _channel_in_guild(canal: discord.TextChannel, guild: discord.Guild) -> bool:
    canal_guild = getattr(canal, 'guild', None)
    if canal_guild is None or canal_guild.id != guild.id:
        return False
    resolved = guild.get_channel(canal.id)
    return resolved is not None and resolved.id == canal.id
