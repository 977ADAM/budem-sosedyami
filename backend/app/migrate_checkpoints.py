"""Apply LangGraph's PostgreSQL checkpoint migrations from the CLI."""

import asyncio

from app.database import Database
from app.config import settings


async def main() -> None:
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL must be set before applying checkpoint migrations")

    database = await Database.open(settings.database_url)
    try:
        await database.checkpointer.setup()
    finally:
        await database.close()


if __name__ == "__main__":
    asyncio.run(main())
