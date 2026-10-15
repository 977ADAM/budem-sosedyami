"""HTTP routes and request/response models for the FastAPI application."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Path, Request, Response
from openai import APIConnectionError, APITimeoutError, OpenAIError
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.chat_graph import (
    AgentId,
    clear_session_threads,
    invoke_chat,
    load_history,
)
from app.config import settings
from app.session_store import SESSION_TTL_DAYS

logger = logging.getLogger(__name__)
router = APIRouter()


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


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/api/session", status_code=204)
async def create_or_refresh_session(request: Request, response: Response) -> None:
    _, token, _ = await request.app.state.sessions.resolve(
        request.cookies.get(settings.session_cookie_name)
    )
    response.set_cookie(
        settings.session_cookie_name,
        token,
        max_age=SESSION_TTL_DAYS * 24 * 60 * 60,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite=settings.session_cookie_samesite,
        path="/api",
    )


@router.delete("/api/session", status_code=204)
async def delete_session(request: Request, response: Response) -> None:
    session_id = await request.app.state.sessions.resolve_existing(
        request.cookies.get(settings.session_cookie_name)
    )
    if session_id:
        await request.app.state.sessions.mark_for_cleanup(session_id)
        try:
            await clear_session_threads(request.app.state.checkpointer, session_id)
            await request.app.state.sessions.revoke(session_id)
        except Exception:
            logger.exception("Session reset queued for background cleanup")
    response.delete_cookie(
        settings.session_cookie_name,
        path="/api",
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite=settings.session_cookie_samesite,
    )


@router.post("/api/agents/{agent_id}/chat", response_model=ChatResponse)
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


@router.get("/api/agents/{agent_id}/history", response_model=HistoryResponse)
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
        request.cookies.get(settings.session_cookie_name)
    )
    if session_id is None:
        raise HTTPException(status_code=401, detail="Session expired; start a new session")
    return session_id
