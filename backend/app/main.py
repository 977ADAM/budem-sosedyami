"""Локальный FastAPI API для демо-соседей."""

import os
from pathlib import Path
from typing import Literal

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from app.agents import AGENTS, build_system_prompt

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

app = FastAPI(title="Локальные ИИ-соседи", version="0.1.0")
DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"


class HistoryMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    agent_id: str
    question_id: str
    history: list[HistoryMessage] = Field(default_factory=list, max_length=40)


class ChatResponse(BaseModel):
    reply: str


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    agent = AGENTS.get(request.agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="Unknown agent")

    question = agent["questions"].get(request.question_id)
    if question is None:
        raise HTTPException(status_code=422, detail="Unknown question for this agent")

    allowed_history_questions = {item["text"] for item in agent["questions"].values()}
    if any(
        message.role == "user" and message.content not in allowed_history_questions
        for message in request.history
    ):
        raise HTTPException(status_code=422, detail="History contains a non-demo question")

    api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
    if not api_key:
        raise HTTPException(status_code=503, detail="DeepSeek API key is not configured")

    messages = [{"role": "system", "content": build_system_prompt(request.agent_id)}]
    messages.extend(message.model_dump() for message in request.history)
    messages.append({"role": "user", "content": question["text"]})
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
    return ChatResponse(reply=reply.strip())
