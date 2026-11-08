from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from sqlalchemy.engine.url import make_url
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from maciota_bot.state import get_state


def ensure_sqlite_parents(database_url: str, checkpoint_path: str) -> None:
    url = make_url(database_url)
    if url.drivername.startswith('sqlite') and url.database not in {None, ':memory:'}:
        Path(url.database).parent.mkdir(parents=True, exist_ok=True)
    Path(checkpoint_path).parent.mkdir(parents=True, exist_ok=True)


def create_db_engine(database_url: str) -> AsyncEngine:
    return create_async_engine(_async_sqlite_url(database_url))


def _async_sqlite_url(database_url: str) -> str:
    if database_url.startswith('sqlite+aiosqlite://'):
        return database_url
    if database_url.startswith('sqlite://'):
        return 'sqlite+aiosqlite://' + database_url.removeprefix('sqlite://')
    return database_url


async def init_db(engine: AsyncEngine) -> None:
    async with engine.begin() as connection:
        await connection.run_sync(SQLModel.metadata.create_all)


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession]:
    state = get_state()

    async with AsyncSession(state.engine) as session:
        yield session
