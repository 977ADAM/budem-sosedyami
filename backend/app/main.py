"""Локальный FastAPI API для демо-соседей."""

import os
from contextlib import asynccontextmanager
from pathlib import Path as FilePath
from typing import AsyncIterator, Literal

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Path, Request
from fastapi.middleware.cors import CORSMiddleware
from langchain_openai import ChatOpenAI
from openai import APIConnectionError, APITimeoutError, OpenAIError
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.agents import build_system_prompt

load_dotenv(FilePath(__file__).resolve().parents[1] / ".env")

DEEPSEEK_BASE_URL = "https://api.deepseek.com"

AgentId = Literal["anton", "marina", "pavel", "vera"]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
    app.state.model = (
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
    try:
        yield
    finally:
        model = app.state.model
        async_client = getattr(model, "root_async_client", None)
        if async_client is not None:
            await async_client.close()
        app.state.model = None


app = FastAPI(title="Локальные ИИ-соседи", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:3000", "http://127.0.0.1:5173"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


class HistoryTurn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    message: str = Field(min_length=1, max_length=500)
    reply: str = Field(min_length=1, max_length=800)

    @field_validator("message")
    @classmethod
    def trim_message(cls, message: str) -> str:
        message = message.strip()
        if not message:
            raise ValueError("Message must not be blank")
        return message

    @field_validator("reply")
    @classmethod
    def trim_reply(cls, reply: str) -> str:
        reply = reply.strip()
        if not reply:
            raise ValueError("Reply must not be blank")
        return reply


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    message: str = Field(min_length=1, max_length=500)
    history: list[HistoryTurn] = Field(max_length=10)

    @field_validator("message")
    @classmethod
    def trim_message(cls, message: str) -> str:
        message = message.strip()
        if not message:
            raise ValueError("Message must not be blank")
        return message


class ChatResponse(BaseModel):
    reply: str


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


async def chat_for_agent(
    agent_id: AgentId, request: ChatRequest, model: ChatOpenAI | None
) -> ChatResponse:
    messages = [("system", build_system_prompt(agent_id))]
    for turn in request.history:
        messages.append(("user", turn.message))
        messages.append(("assistant", turn.reply))
    messages.append(("user", request.message))

    if model is None:
        raise HTTPException(status_code=503, detail="DeepSeek API key is not configured")

    try:
        result = await model.ainvoke(messages)
    except APITimeoutError as exc:
        raise HTTPException(status_code=504, detail="DeepSeek request timed out") from exc
    except (APIConnectionError, OpenAIError, ValueError) as exc:
        raise HTTPException(status_code=502, detail="DeepSeek request failed") from exc

    reply = result.content
    if not isinstance(reply, str) or not reply.strip():
        raise HTTPException(status_code=502, detail="Empty DeepSeek response")
    reply = reply.strip()
    return ChatResponse(reply=reply)


@app.post("/api/agents/{agent_id}/chat", response_model=ChatResponse)
async def chat(
    http_request: Request,
    chat_request: ChatRequest,
    agent_id: AgentId = Path(description="ID вымышленного соседа"),
) -> ChatResponse:
    return await chat_for_agent(agent_id, chat_request, http_request.app.state.model)
