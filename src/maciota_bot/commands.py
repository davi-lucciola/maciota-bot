import discord
from discord import app_commands
from sqlalchemy.engine import Engine

from maciota_bot.db import set_welcome_channel as save_welcome_channel


async def set_welcome_channel(
    interaction: discord.Interaction,
    canal: discord.TextChannel,
    *,
    engine: Engine,
) -> None:
    guild = interaction.guild
    if not interaction.user.guild_permissions.administrator:
        await _reply(
            interaction,
            'Só administradores podem definir o canal de boas-vindas.',
        )
        return

    if not _channel_in_guild(canal, guild):
        await _reply(interaction, 'Esse canal não existe neste servidor.')
        return

    save_welcome_channel(engine, guild.id, canal.id)
    await _reply(
        interaction,
        f'Canal de boas-vindas definido para {canal.mention}.',
    )


def build_command_tree(
    client: discord.Client,
    *,
    engine: Engine,
) -> app_commands.CommandTree:
    tree = app_commands.CommandTree(client)
    client.tree = tree

    @tree.command(
        name='boas-vindas',
        description='Define o canal de boas-vindas do servidor.',
    )
    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    async def boas_vindas(
        interaction: discord.Interaction,
        canal: discord.TextChannel,
    ) -> None:
        await set_welcome_channel(interaction, canal, engine=engine)

    return tree


async def _reply(interaction: discord.Interaction, content: str) -> None:
    await interaction.response.send_message(content, ephemeral=True)


def _channel_in_guild(canal: discord.TextChannel, guild: discord.Guild) -> bool:
    canal_guild = getattr(canal, 'guild', None)
    if canal_guild is None or canal_guild.id != guild.id:
        return False
    resolved = guild.get_channel(canal.id)
    return resolved is not None and resolved.id == canal.id
