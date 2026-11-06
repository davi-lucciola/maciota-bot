from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, create_engine

from maciota_bot.models import GuildWelcomeChannel


class _EngineHolder:
    engine: Engine | None = None


def create_db_engine(database_url: str) -> Engine:
    return create_engine(database_url)


def init_db(engine: Engine) -> None:
    SQLModel.metadata.create_all(engine)


def get_welcome_channel_id(engine: Engine, guild_id: int) -> int | None:
    with Session(engine) as session:
        row = session.get(GuildWelcomeChannel, guild_id)
        if row is None:
            return None
        return row.channel_id


def set_welcome_channel(engine: Engine, guild_id: int, channel_id: int) -> None:
    with Session(engine) as session:
        row = session.get(GuildWelcomeChannel, guild_id)
        if row is None:
            session.add(
                GuildWelcomeChannel(guild_id=guild_id, channel_id=channel_id),
            )
        else:
            row.channel_id = channel_id
        session.commit()


def configure_engine(engine: Engine | None) -> None:
    previous = _EngineHolder.engine
    _EngineHolder.engine = engine
    if previous is not None and previous is not engine:
        previous.dispose()


def current_engine() -> Engine | None:
    return _EngineHolder.engine
