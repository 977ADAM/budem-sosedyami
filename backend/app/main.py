"""Локальный FastAPI API для демо-соседей."""

import os
from pathlib import Path
import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.agents import AGENTS, build_system_prompt

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

app = FastAPI(title="Локальные ИИ-соседи", version="0.1.0")
DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"


class HistoryTurn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question_id: str = Field(min_length=1)
    reply: str = Field(min_length=1, max_length=800)

    @field_validator("reply")
    @classmethod
    def trim_reply(cls, reply: str) -> str:
        reply = reply.strip()
        if not reply:
            raise ValueError("Reply must not be blank")
        return reply


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question_id: str = Field(min_length=1)
    history: list[HistoryTurn] = Field(max_length=3)


class ChatResponse(BaseModel):
    reply: str


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


async def chat_for_agent(agent_id: str, request: ChatRequest) -> ChatResponse:
    agent = AGENTS[agent_id]
    question = agent["questions"].get(request.question_id)
    if question is None:
        raise HTTPException(status_code=422, detail="Unknown question for this agent")

    messages = [{"role": "system", "content": build_system_prompt(agent_id)}]
    seen_question_ids: set[str] = set()
    for turn in request.history:
        history_question = agent["questions"].get(turn.question_id)
        if (
            history_question is None
            or turn.question_id == request.question_id
            or turn.question_id in seen_question_ids
        ):
            raise HTTPException(status_code=422, detail="Invalid dialogue history")
        seen_question_ids.add(turn.question_id)
        messages.append({"role": "user", "content": history_question["text"]})
        messages.append({"role": "assistant", "content": turn.reply})
    messages.append({"role": "user", "content": question["text"]})

    api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
    if not api_key:
        raise HTTPException(status_code=503, detail="DeepSeek API key is not configured")

    payload = {
        "model": os.getenv("DEEPSEEK_MODEL", "deepseek-flash"),
        "messages": messages,
        "stream": False,
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                DEEPSEEK_URL,
                headers={"Authorization": f"Bearer {api_key}"},
                json=payload,
            )
            response.raise_for_status()
            result = response.json()
    except httpx.TimeoutException as exc:
        raise HTTPException(status_code=504, detail="DeepSeek request timed out") from exc
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(status_code=502, detail="DeepSeek request failed") from exc

    try:
        reply = result["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise HTTPException(status_code=502, detail="Invalid DeepSeek response") from exc
    if not isinstance(reply, str) or not reply.strip():
        raise HTTPException(status_code=502, detail="Empty DeepSeek response")
    reply = reply.strip()
    return ChatResponse(reply=reply)


@app.post("/api/agents/anton/chat", response_model=ChatResponse)
async def chat_anton(request: ChatRequest) -> ChatResponse:
    return await chat_for_agent("anton", request)


@app.post("/api/agents/marina/chat", response_model=ChatResponse)
async def chat_marina(request: ChatRequest) -> ChatResponse:
    return await chat_for_agent("marina", request)


@app.post("/api/agents/pavel/chat", response_model=ChatResponse)
async def chat_pavel(request: ChatRequest) -> ChatResponse:
    return await chat_for_agent("pavel", request)


@app.post("/api/agents/vera/chat", response_model=ChatResponse)
async def chat_vera(request: ChatRequest) -> ChatResponse:
    return await chat_for_agent("vera", request)
