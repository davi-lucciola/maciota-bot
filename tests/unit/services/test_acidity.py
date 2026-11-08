from pathlib import Path

from maciota_bot.db import create_db_engine, init_db
from maciota_bot.services.acidity import define_acidity, get_acidity, set_acidity
from maciota_bot.state import configure, get_state
from tests.support import make_state, release_engine


async def _publish(database: Path) -> None:
    engine = create_db_engine(f'sqlite:///{database}')
    await init_db(engine)
    configure(make_state(engine))


async def test_missing_row_returns_medium(tmp_path: Path) -> None:
    await _publish(tmp_path / 'acidity.db')

    assert await get_acidity(1) == 'medium'


async def test_set_writes_and_replaces_the_level_for_the_same_guild(
    tmp_path: Path,
) -> None:
    await _publish(tmp_path / 'acidity.db')

    await set_acidity(7, 'mild')
    await set_acidity(8, 'sharp')
    assert await get_acidity(7) == 'mild'

    await set_acidity(7, 'medium')

    assert await get_acidity(7) == 'medium'
    assert await get_acidity(8) == 'sharp'


async def test_saved_level_survives_closing_and_opening_the_file(
    tmp_path: Path,
) -> None:
    database = tmp_path / 'acidity.db'
    await _publish(database)
    await set_acidity(4, 'sharp')
    opened = get_state().engine
    assert opened is not None
    await release_engine()

    reopened = create_db_engine(f'sqlite:///{database}')
    configure(make_state(reopened))

    assert await get_acidity(4) == 'sharp'


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


class _Interaction:
    def __init__(self, guild: _Guild | None, *, administrator: bool) -> None:
        self.guild = guild
        self.user = _User(administrator=administrator)
        self.response = _Response()


async def test_administrator_writes_the_level(tmp_path: Path) -> None:
    await _publish(tmp_path / 'acidity.db')
    interaction = _Interaction(_Guild(7), administrator=True)

    await define_acidity(interaction, 'sharp')

    assert await get_acidity(7) == 'sharp'
    assert interaction.response.messages == [('Acidity set to sharp.', True)]


async def test_non_administrator_does_not_write(tmp_path: Path) -> None:
    await _publish(tmp_path / 'acidity.db')
    interaction = _Interaction(_Guild(7), administrator=False)

    await define_acidity(interaction, 'mild')

    assert await get_acidity(7) == 'medium'
    assert interaction.response.messages == [
        ('Only administrators can set the acidity.', True),
    ]
