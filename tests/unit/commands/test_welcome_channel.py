from pathlib import Path

from maciota_bot.commands import set_welcome_channel
from maciota_bot.db import create_db_engine, get_welcome_channel_id, init_db


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


def _engine(tmp_path: Path):
    engine = create_db_engine(f'sqlite:///{tmp_path / "welcome.db"}')
    init_db(engine)
    return engine


async def test_administrator_writes_the_channel(tmp_path: Path) -> None:
    engine = _engine(tmp_path)
    guild = _Guild(7)
    canal = _Channel(99, guild)
    guild.channels[canal.id] = canal
    interaction = _Interaction(guild, administrator=True)

    await set_welcome_channel(interaction, canal, engine=engine)

    assert get_welcome_channel_id(engine, 7) == 99
    assert interaction.response.messages == [
        ('Canal de boas-vindas definido para <#99>.', True),
    ]
    engine.dispose()


async def test_non_administrator_does_not_write(tmp_path: Path) -> None:
    engine = _engine(tmp_path)
    guild = _Guild(7)
    canal = _Channel(99, guild)
    guild.channels[canal.id] = canal
    interaction = _Interaction(guild, administrator=False)

    await set_welcome_channel(interaction, canal, engine=engine)

    assert get_welcome_channel_id(engine, 7) is None
    assert interaction.response.messages == [
        ('Só administradores podem definir o canal de boas-vindas.', True),
    ]
    engine.dispose()


async def test_channel_absent_from_the_guild_does_not_write(tmp_path: Path) -> None:
    engine = _engine(tmp_path)
    guild = _Guild(7)
    canal = _Channel(99, guild)
    interaction = _Interaction(guild, administrator=True)

    await set_welcome_channel(interaction, canal, engine=engine)

    assert get_welcome_channel_id(engine, 7) is None
    assert interaction.response.messages == [
        ('Esse canal não existe neste servidor.', True),
    ]
    engine.dispose()
