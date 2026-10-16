"""Composition root: the only place where concrete implementations are wired together."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.application.chat_with_neighbor import ChatWithNeighbor
from app.application.ports import ChatModel
from app.infrastructure.config import Settings, load_settings
from app.infrastructure.deepseek import build_chat_model
from app.infrastructure.fernet_codec import FernetConversationCodec
from app.infrastructure.neighbor_catalog import StaticNeighborRepository
from app.presentation.errors import register_error_handlers
from app.presentation.routes import build_router


def create_app(settings: Settings, chat_model: ChatModel | None = None) -> FastAPI:
    model = chat_model or build_chat_model(settings)
    neighbors = StaticNeighborRepository()

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        try:
            yield
        finally:
            await model.aclose()

    app = FastAPI(
        title="Будем соседями? API",
        version="0.4.0",
        description="Один эндпоинт: отправьте сообщение соседу и верните полученный `context` "
        "в следующем запросе, чтобы продолжить разговор.",
        lifespan=lifespan,
    )
    app.state.chat_with_neighbor = ChatWithNeighbor(
        neighbors=neighbors,
        model=model,
        codec=FernetConversationCodec(settings.context_secret, settings.context_ttl_seconds),
    )
    app.state.limiter = limiter = Limiter(key_func=get_remote_address)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )
    app.include_router(build_router(limiter, settings.rate_limit, neighbors.ids()))
    register_error_handlers(app)
    return app


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
app = create_app(load_settings())
