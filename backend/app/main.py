"""Composition root: the only place where concrete implementations are wired together."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.application.agent_service import AgentService
from app.infrastructure.config import load_settings
from app.infrastructure.deepseek import build_chat_model
from app.infrastructure.fernet_codec import FernetConversationCodec
from app.infrastructure.logging import configure_logging, log_startup
from app.infrastructure.neighbor_catalog import StaticNeighborRepository
from app.presentation.errors import register_error_handlers
from app.presentation.request_logging import REQUEST_ID_HEADER, log_requests
from app.presentation.routes import router

logger = logging.getLogger("app")


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    configure_logging(application.state.settings.log_level)
    log_startup(application.state.settings, neighbors.ids())
    try:
        yield
    finally:
        await model.aclose()
        logger.info("Stopped")


settings = load_settings()
model = build_chat_model(settings)
neighbors = StaticNeighborRepository()
codec = FernetConversationCodec(settings.context_secret, settings.context_ttl_seconds)
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Будем соседями? API",
    version="0.4.0",
    description="Один эндпоинт: отправьте сообщение соседу и верните полученный `context` "
    "в следующем запросе, чтобы продолжить разговор.",
    lifespan=lifespan,
)
app.state.settings = settings
app.state.agent_service = AgentService(neighbors=neighbors, model=model, codec=codec)
app.state.limiter = limiter
app.state.check_rate_limit = limiter.limit(settings.rate_limit)(lambda request: None)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", REQUEST_ID_HEADER],
    expose_headers=[REQUEST_ID_HEADER],
)
app.middleware("http")(log_requests)
register_error_handlers(app)
app.include_router(router)
