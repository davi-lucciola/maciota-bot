from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlmodel import SQLModel

from maciota_bot.state import get_state


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
async def get_session() -> AsyncIterator[AsyncSession]:
    state = get_state()

    async with AsyncSession(state.engine) as session:
        yield session
