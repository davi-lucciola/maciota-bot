import discord


def get_intents() -> discord.Intents:
    intents = discord.Intents.default()
    intents.message_content = True
    return intents


def build_discord_client() -> discord.Client:
    return discord.Client(intents=get_intents())
