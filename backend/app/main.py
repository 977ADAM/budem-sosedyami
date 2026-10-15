"""FastAPI API for anonymous, persistent agent conversations."""

from __future__ import annotations

import asyncio
import logging
import os
from contextlib import AsyncExitStack, asynccontextmanager
from pathlib import Path as FilePath
from typing import AsyncIterator

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Path, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from openai import APIConnectionError, APITimeoutError, OpenAIError
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.chat_graph import (
    AgentId,
    build_chat_graph,
    clear_session_threads,
    invoke_chat,
    load_history,
)
from app.database import Database
from app.session_store import SESSION_TTL_DAYS, SessionStore

load_dotenv(FilePath(__file__).resolve().parents[1] / ".env")

logger = logging.getLogger(__name__)
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
SESSION_COOKIE = "neighbor_session"


def _cors_origins() -> list[str]:
    configured = os.getenv("CORS_ORIGINS")
    origins = configured.split(",") if configured else [
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]
    return [origin.strip().rstrip("/") for origin in origins if origin.strip()]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        raise RuntimeError("DATABASE_URL must be configured")

    stack = AsyncExitStack()
    try:
        database = await Database.open(database_url)
        stack.push_async_callback(database.close)
        sessions = SessionStore(database.engine)
        saver = database.checkpointer
        api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
        model = (
            ChatOpenAI(
                model=os.getenv("DEEPSEEK_MODEL", "deepseek-flash"),
                api_key=api_key,
                base_url=DEEPSEEK_BASE_URL,
                timeout=30.0,
                max_retries=0,
            )
            if api_key
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
    allow_origins=_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type"],
)


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    message: str = Field(min_length=1, max_length=500)
    question_id: str | None = Field(default=None, max_length=80)

    @field_validator("message")
    @classmethod
    def trim_message(cls, message: str) -> str:
        message = message.strip()
        if not message:
            raise ValueError("Message must not be blank")
        return message


class ChatResponse(BaseModel):
    reply: str


class HistoryTurn(BaseModel):
    message: str
    reply: str
    question_id: str | None = None


class HistoryResponse(BaseModel):
    turns: list[HistoryTurn]


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/session", status_code=204)
async def create_or_refresh_session(request: Request, response: Response) -> None:
    _, token, _ = await request.app.state.sessions.resolve(
        request.cookies.get(SESSION_COOKIE)
    )
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=SESSION_TTL_DAYS * 24 * 60 * 60,
        httponly=True,
        secure=_cookie_secure(),
        samesite=os.getenv("SESSION_COOKIE_SAMESITE", "lax").lower(),
        path="/api",
    )


@app.delete("/api/session", status_code=204)
async def delete_session(request: Request, response: Response) -> None:
    session_id = await request.app.state.sessions.resolve_existing(
        request.cookies.get(SESSION_COOKIE)
    )
    if session_id:
        await request.app.state.sessions.mark_for_cleanup(session_id)
        try:
            await clear_session_threads(request.app.state.checkpointer, session_id)
            await request.app.state.sessions.revoke(session_id)
        except Exception:
            logger.exception("Session reset queued for background cleanup")
    response.delete_cookie(SESSION_COOKIE, path="/api", httponly=True, secure=_cookie_secure(), samesite="lax")


@app.post("/api/agents/{agent_id}/chat", response_model=ChatResponse)
async def chat(
    http_request: Request,
    chat_request: ChatRequest,
    agent_id: AgentId = Path(description="ID вымышленного соседа"),
) -> ChatResponse:
    session_id = await _require_session(http_request)
    graph = http_request.app.state.graph
    if graph is None:
        raise HTTPException(status_code=503, detail="DeepSeek API key is not configured")
    try:
        reply = await invoke_chat(
            graph,
            session_id,
            agent_id,
            chat_request.message,
            chat_request.question_id,
        )
    except APITimeoutError as exc:
        raise HTTPException(status_code=504, detail="DeepSeek request timed out") from exc
    except (APIConnectionError, OpenAIError, ValueError) as exc:
        raise HTTPException(status_code=502, detail="DeepSeek request failed") from exc
    return ChatResponse(reply=reply)


@app.get("/api/agents/{agent_id}/history", response_model=HistoryResponse)
async def history(
    request: Request,
    agent_id: AgentId = Path(description="ID вымышленного соседа"),
) -> HistoryResponse:
    session_id = await _require_session(request)
    graph = request.app.state.graph
    if graph is None:
        return HistoryResponse(turns=[])
    turns = await load_history(graph, session_id, agent_id)
    return HistoryResponse(turns=turns)


async def _require_session(request: Request):
    session_id = await request.app.state.sessions.resolve_existing(
        request.cookies.get(SESSION_COOKIE)
    )
    if session_id is None:
        raise HTTPException(status_code=401, detail="Session expired; start a new session")
    return session_id


def _cookie_secure() -> bool:
    configured = os.getenv("SESSION_COOKIE_SECURE")
    return configured.lower() == "true" if configured else True


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
