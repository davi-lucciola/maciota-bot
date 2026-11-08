import discord
from discord import app_commands

from maciota_bot.services.acidity import define_acidity
from maciota_bot.services.welcome import define_welcome_channel

_ACIDITY_CHOICES = [
    app_commands.Choice(name='mild', value='mild'),
    app_commands.Choice(name='medium', value='medium'),
    app_commands.Choice(name='sharp', value='sharp'),
]


def build_command_tree(client: discord.Client) -> app_commands.CommandTree:
    tree = app_commands.CommandTree(client)
    client.tree = tree

    @tree.command(
        name='welcome',
        description='Set the welcome channel for this server.',
    )
    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    async def welcome(
        interaction: discord.Interaction,
        channel: discord.TextChannel,
    ) -> None:
        await define_welcome_channel(interaction, channel)

    @tree.command(
        name='acidity',
        description='Set how acidic Maciota is in this server.',
    )
    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    @app_commands.choices(level=_ACIDITY_CHOICES)
    async def acidity(
        interaction: discord.Interaction,
        level: str,
    ) -> None:
        await define_acidity(interaction, level)

    return tree
