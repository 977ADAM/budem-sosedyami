"""FastAPI API for stateless agent conversations."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langchain_openai import ChatOpenAI

from app.api import router
from app.chat_graph import build_chat_graph
from app.config import settings



@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    try:
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
        app.state.model = model
        app.state.graph = build_chat_graph(model) if model else None
        yield
    finally:
        model = getattr(app.state, "model", None)
        async_client = getattr(model, "root_async_client", None)
        if async_client is not None:
            await async_client.close()


app = FastAPI(title="Локальные ИИ-соседи", version="0.2.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
app.include_router(router)
