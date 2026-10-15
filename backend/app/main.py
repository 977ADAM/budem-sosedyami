"""Локальный FastAPI API для демо-соседей."""

import os
from pathlib import Path
import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict

from app.agents import AGENTS, build_system_prompt
from app.dialogues import DIALOGUES, append_turn, generation, reset_dialogues

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

app = FastAPI(title="Локальные ИИ-соседи", version="0.1.0")
DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    agent_id: str
    question_id: str


class ChatResponse(BaseModel):
    reply: str


class DialogueResponse(BaseModel):
    answers: dict[str, str]


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/dialogue/{agent_id}", response_model=DialogueResponse)
async def get_dialogue(agent_id: str) -> DialogueResponse:
    if agent_id not in AGENTS:
        raise HTTPException(status_code=404, detail="Unknown agent")
    return DialogueResponse(
        answers={turn["question_id"]: turn["reply"] for turn in DIALOGUES.get(agent_id, [])}
    )


@app.post("/api/dialogue/reset")
async def clear_dialogues() -> dict[str, str]:
    reset_dialogues()
    return {"status": "ok"}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    agent = AGENTS.get(request.agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="Unknown agent")

    question = agent["questions"].get(request.question_id)
    if question is None:
        raise HTTPException(status_code=422, detail="Unknown question for this agent")

    api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
    if not api_key:
        raise HTTPException(status_code=503, detail="DeepSeek API key is not configured")

    messages = [{"role": "system", "content": build_system_prompt(request.agent_id)}]
    request_generation = generation(request.agent_id)
    for turn in DIALOGUES.get(request.agent_id, []):
        messages.append({"role": "user", "content": turn["question"]})
        messages.append({"role": "assistant", "content": turn["reply"]})
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
    reply = reply.strip()
    if not append_turn(
        request.agent_id,
        {"question_id": request.question_id, "question": question["text"], "reply": reply},
        request_generation,
    ):
        raise HTTPException(status_code=409, detail="Dialogue was reset while the reply was pending")
    return ChatResponse(reply=reply)
