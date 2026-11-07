import discord
from discord import app_commands

from maciota_bot.services.welcome_channel import define_welcome_channel


def build_command_tree(client: discord.Client) -> app_commands.CommandTree:
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
        await define_welcome_channel(interaction, canal)

    return tree
