import discord
from sqlmodel.ext.asyncio.session import AsyncSession

from maciota_bot.agent.schema import Acidity
from maciota_bot.db import get_session
from maciota_bot.models import GuildAcidity


async def _find_acidity_row(
    session: AsyncSession, guild_id: int
) -> GuildAcidity | None:
    return await session.get(GuildAcidity, guild_id)


def _known_level(level: str) -> Acidity | None:
    if level == 'mild':
        return 'mild'
    if level == 'medium':
        return 'medium'
    if level == 'sharp':
        return 'sharp'
    return None


async def get_acidity(guild_id: int) -> Acidity:
    async with get_session() as session:
        row = await _find_acidity_row(session, guild_id)

    if row is None:
        return 'medium'

    known = _known_level(row.level)
    if known is None:
        return 'medium'

    return known


async def set_acidity(guild_id: int, level: Acidity) -> None:
    async with get_session() as session:
        row = await _find_acidity_row(session, guild_id)

        if row is not None:
            row.level = level
            await session.commit()
            return

        session.add(GuildAcidity(guild_id=guild_id, level=level))
        await session.commit()


async def define_acidity(interaction: discord.Interaction, level: str) -> None:
    guild = interaction.guild
    assert guild is not None

    if not interaction.user.guild_permissions.administrator:
        await _reply(interaction, 'Only administrators can set the acidity.')
        return

    known = _known_level(level)
    assert known is not None

    await set_acidity(guild.id, known)
    await _reply(interaction, f'Acidity set to {known}.')


async def _reply(interaction: discord.Interaction, content: str) -> None:
    await interaction.response.send_message(content, ephemeral=True)
