import discord

from maciota_bot.client import build_discord_client, get_intents


def test_get_intents_enables_message_content() -> None:
    intents = get_intents()

    assert intents.message_content is True


def test_build_discord_client_reads_message_content() -> None:
    client = build_discord_client()

    assert isinstance(client, discord.Client)
    assert client.intents.message_content is True


def test_get_intents_enables_members() -> None:
    intents = get_intents()

    assert intents.members is True


def test_build_discord_client_reads_members() -> None:
    client = build_discord_client()

    assert client.intents.members is True
