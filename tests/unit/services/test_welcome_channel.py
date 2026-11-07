from pathlib import Path

from maciota_bot.db import create_db_engine, init_db
from maciota_bot.services.welcome import (
    define_welcome_channel,
    get_welcome_channel_id,
    set_welcome_channel,
)
from maciota_bot.state import AppState, configure, get_state
from tests.support import IdleTree, release_engine


async def _publish(database: Path) -> None:
    engine = create_db_engine(f'sqlite:///{database}')
    await init_db(engine)
    configure(AppState(engine=engine, tree=IdleTree()))


async def test_missing_row_returns_none(tmp_path: Path) -> None:
    await _publish(tmp_path / 'welcome.db')

    assert await get_welcome_channel_id(1) is None


async def test_set_writes_and_replaces_the_channel_for_the_same_guild(
    tmp_path: Path,
) -> None:
    await _publish(tmp_path / 'welcome.db')

    await set_welcome_channel(7, 100)
    await set_welcome_channel(8, 300)
    assert await get_welcome_channel_id(7) == 100

    await set_welcome_channel(7, 200)

    assert await get_welcome_channel_id(7) == 200
    assert await get_welcome_channel_id(8) == 300


async def test_saved_channel_survives_closing_and_opening_the_file(
    tmp_path: Path,
) -> None:
    database = tmp_path / 'welcome.db'
    await _publish(database)
    await set_welcome_channel(4, 55)
    opened = get_state().engine
    assert opened is not None
    await release_engine()

    reopened = create_db_engine(f'sqlite:///{database}')
    configure(AppState(engine=reopened, tree=IdleTree()))

    assert await get_welcome_channel_id(4) == 55


class _Permissions:
    def __init__(self, *, administrator: bool) -> None:
        self.administrator = administrator


class _User:
    def __init__(self, *, administrator: bool) -> None:
        self.guild_permissions = _Permissions(administrator=administrator)


class _Response:
    def __init__(self) -> None:
        self.messages: list[tuple[str, bool]] = []

    async def send_message(self, content: str, *, ephemeral: bool = False) -> None:
        self.messages.append((content, ephemeral))


class _Guild:
    def __init__(self, guild_id: int) -> None:
        self.id = guild_id
        self.channels: dict[int, object] = {}

    def get_channel(self, channel_id: int) -> object | None:
        return self.channels.get(channel_id)


class _Channel:
    def __init__(self, channel_id: int, guild: _Guild) -> None:
        self.id = channel_id
        self.guild = guild
        self.mention = f'<#{channel_id}>'


class _Interaction:
    def __init__(self, guild: _Guild | None, *, administrator: bool) -> None:
        self.guild = guild
        self.user = _User(administrator=administrator)
        self.response = _Response()


async def test_administrator_writes_the_channel(tmp_path: Path) -> None:
    await _publish(tmp_path / 'welcome.db')
    guild = _Guild(7)
    canal = _Channel(99, guild)
    guild.channels[canal.id] = canal
    interaction = _Interaction(guild, administrator=True)

    await define_welcome_channel(interaction, canal)

    assert await get_welcome_channel_id(7) == 99
    assert interaction.response.messages == [
        ('Canal de boas-vindas definido para <#99>.', True),
    ]


async def test_non_administrator_does_not_write(tmp_path: Path) -> None:
    await _publish(tmp_path / 'welcome.db')
    guild = _Guild(7)
    canal = _Channel(99, guild)
    guild.channels[canal.id] = canal
    interaction = _Interaction(guild, administrator=False)

    await define_welcome_channel(interaction, canal)

    assert await get_welcome_channel_id(7) is None
    assert interaction.response.messages == [
        ('Só administradores podem definir o canal de boas-vindas.', True),
    ]


async def test_channel_absent_from_the_guild_does_not_write(tmp_path: Path) -> None:
    await _publish(tmp_path / 'welcome.db')
    guild = _Guild(7)
    canal = _Channel(99, guild)
    interaction = _Interaction(guild, administrator=True)

    await define_welcome_channel(interaction, canal)

    assert await get_welcome_channel_id(7) is None
    assert interaction.response.messages == [
        ('Esse canal não existe neste servidor.', True),
    ]
