from typing import cast

import discord
from sqlmodel.ext.asyncio.session import AsyncSession

from maciota_bot.agent.schema import Acidity
from maciota_bot.db import get_session
from maciota_bot.models import GuildAcidity


async def _find_acidity_row(
    session: AsyncSession, guild_id: int
) -> GuildAcidity | None:
    return await session.get(GuildAcidity, guild_id)


async def get_acidity(guild_id: int) -> Acidity:
    async with get_session() as session:
        row = await _find_acidity_row(session, guild_id)

        if row is None:
            return 'medium'

        return cast(Acidity, row.level)


async def set_acidity(guild_id: int, level: Acidity) -> None:
    async with get_session() as session:
        row = await _find_acidity_row(session, guild_id)

        if row is not None:
            row.level = level
            await session.commit()
            return

        session.add(GuildAcidity(guild_id=guild_id, level=level))
        await session.commit()


async def define_acidity(interaction: discord.Interaction, level: Acidity) -> None:
    guild = interaction.guild
    assert guild is not None

    if not interaction.user.guild_permissions.administrator:
        await _reply(interaction, 'Only administrators can set the acidity.')
        return

    await set_acidity(guild.id, level)
    await _reply(interaction, f'Acidity set to {level}.')


async def _reply(interaction: discord.Interaction, content: str) -> None:
    await interaction.response.send_message(content, ephemeral=True)
