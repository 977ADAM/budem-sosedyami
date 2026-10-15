"""HTTP routes and request/response models for the FastAPI application."""

from __future__ import annotations


from fastapi import APIRouter, HTTPException, Path, Request
from openai import APIConnectionError, APITimeoutError, OpenAIError
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.chat_graph import AgentId, invoke_chat

router = APIRouter()


class HistoryTurn(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    message: str = Field(min_length=1, max_length=500)
    reply: str = Field(min_length=1, max_length=20000)


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    message: str = Field(min_length=1, max_length=500)
    history: list[HistoryTurn] = Field(default_factory=list, max_length=100)

    @field_validator("message")
    @classmethod
    def trim_message(cls, message: str) -> str:
        message = message.strip()
        if not message:
            raise ValueError("Message must not be blank")
        return message


class ChatResponse(BaseModel):
    reply: str


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/api/agents/{agent_id}/chat", response_model=ChatResponse)
async def chat(
    http_request: Request,
    chat_request: ChatRequest,
    agent_id: AgentId = Path(description="ID вымышленного соседа"),
) -> ChatResponse:
    graph = http_request.app.state.graph
    if graph is None:
        raise HTTPException(status_code=503, detail="DeepSeek API key is not configured")
    try:
        reply = await invoke_chat(
            graph,
            agent_id,
            chat_request.message,
            [turn.model_dump() for turn in chat_request.history],
        )
    except APITimeoutError as exc:
        raise HTTPException(status_code=504, detail="DeepSeek request timed out") from exc
    except (APIConnectionError, OpenAIError, ValueError) as exc:
        raise HTTPException(status_code=502, detail="DeepSeek request failed") from exc
    return ChatResponse(reply=reply)
