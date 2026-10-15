"""Long-lived PostgreSQL connection pools used by the application."""

from __future__ import annotations

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine


class Database:
    """Own the SQLAlchemy and LangGraph PostgreSQL pools for one app process."""

    def __init__(self, database_url: str) -> None:
        self.engine: AsyncEngine = create_async_engine(
            _sqlalchemy_url(database_url),
            pool_size=10,
            max_overflow=0,
            pool_pre_ping=True,
        )
        self.checkpoint_pool = AsyncConnectionPool(
            conninfo=_psycopg_url(database_url),
            kwargs={
                "autocommit": True,
                "prepare_threshold": 0,
                "row_factory": dict_row,
            },
            min_size=1,
            max_size=10,
            open=False,
        )
        self.checkpointer = AsyncPostgresSaver(
            self.checkpoint_pool,
            serde=JsonPlusSerializer(
                pickle_fallback=False,
                allowed_msgpack_modules=None,
            ),
        )

    @classmethod
    async def open(cls, database_url: str) -> Database:
        database = cls(database_url)
        try:
            async with database.engine.connect():
                pass
            await database.checkpoint_pool.open(wait=True)
        except Exception:
            await database.close()
            raise
        return database

    async def close(self) -> None:
        try:
            await self.checkpoint_pool.close()
        finally:
            await self.engine.dispose()


def _sqlalchemy_url(database_url: str) -> str:
    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql+psycopg://", 1)
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    return database_url


def _psycopg_url(database_url: str) -> str:
    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql://", 1)
    if database_url.startswith("postgresql+psycopg://"):
        return database_url.replace("postgresql+psycopg://", "postgresql://", 1)
    return database_url
