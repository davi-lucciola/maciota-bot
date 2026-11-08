import discord

from maciota_bot.services.conversation import respond
from maciota_bot.services.welcome import greet


async def on_message(message: discord.Message) -> None:
    await respond(message)


async def on_member_join(member: discord.Member) -> None:
    await greet(member)
