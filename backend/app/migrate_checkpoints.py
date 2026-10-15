"""Apply LangGraph's PostgreSQL checkpoint migrations from the CLI."""

import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

from app.database import Database

load_dotenv(Path(__file__).resolve().parents[1] / ".env")


async def main() -> None:
    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        raise RuntimeError("DATABASE_URL must be set before applying checkpoint migrations")

    database = await Database.open(database_url)
    try:
        await database.checkpointer.setup()
    finally:
        await database.close()


if __name__ == "__main__":
    asyncio.run(main())
