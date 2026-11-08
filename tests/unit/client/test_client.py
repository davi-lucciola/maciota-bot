import discord
import pytest

from maciota_bot.client import MaciotaClient, get_intents
from maciota_bot.state import configure, get_state
from tests.support import make_state


def test_get_intents_enables_message_content() -> None:
    intents = get_intents()

    assert intents.message_content is True


def test_client_reads_message_content() -> None:
    client = MaciotaClient()

    assert isinstance(client, discord.Client)
    assert client.intents.message_content is True


def test_get_intents_enables_members() -> None:
    intents = get_intents()

    assert intents.members is True


def test_client_reads_members() -> None:
    client = MaciotaClient()

    assert client.intents.members is True


async def test_close_shuts_down_the_agent_then_the_gateway(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    order: list[str] = []

    class _Agent:
        def __init__(self) -> None:
            self.closed = False

        async def aclose(self) -> None:
            self.closed = True
            order.append('agent')

    async def gateway_close(self: discord.Client) -> None:
        order.append('gateway')

    monkeypatch.setattr(discord.Client, 'close', gateway_close)
    client = MaciotaClient()
    current = get_state()
    configure(
        make_state(current.engine, tree=client.tree, agent=_Agent(), client=client)
    )

    await client.close()

    assert order == ['agent', 'gateway']
