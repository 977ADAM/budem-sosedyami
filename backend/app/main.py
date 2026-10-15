"""FastAPI API for anonymous, persistent agent conversations."""

from __future__ import annotations

import asyncio
import logging
from contextlib import AsyncExitStack, asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from app.api import router
from app.chat_graph import build_chat_graph, clear_session_threads
from app.config import settings
from app.database import Database
from app.session_store import SessionStore

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL must be configured")

    stack = AsyncExitStack()
    try:
        database = await Database.open(settings.database_url)
        stack.push_async_callback(database.close)
        sessions = SessionStore(database.engine)
        saver = database.checkpointer
        model = (
            ChatOpenAI(
                model=settings.deepseek_model,
                api_key=settings.deepseek_api_key,
                base_url=settings.deepseek_base_url,
                timeout=30.0,
                max_retries=0,
            )
            if settings.deepseek_api_key
            else None
        )
        app.state.sessions = sessions
        app.state.checkpointer = saver
        app.state.model = model
        app.state.graph = build_chat_graph(model, saver) if model else None
        cleanup_task = asyncio.create_task(_cleanup_expired_sessions(sessions, saver))
        app.state.cleanup_task = cleanup_task
        yield
    finally:
        task = getattr(app.state, "cleanup_task", None)
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        model = getattr(app.state, "model", None)
        async_client = getattr(model, "root_async_client", None)
        if async_client is not None:
            await async_client.close()
        await stack.aclose()


app = FastAPI(title="Локальные ИИ-соседи", version="0.2.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type"],
)
app.include_router(router)


async def _cleanup_expired_sessions(sessions: SessionStore, saver: AsyncPostgresSaver) -> None:
    while True:
        try:
            for session_id in await sessions.claim_expired():
                try:
                    await clear_session_threads(saver, session_id)
                    await sessions.revoke(session_id)
                except Exception:
                    logger.exception("Failed to clean up expired anonymous session")
            await asyncio.sleep(300)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Anonymous-session cleanup failed")
            await asyncio.sleep(30)
