"""Composition root: the only place where concrete implementations are wired together."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.application.agent_service import ChatWithNeighbor
from app.application.ports import ChatModel
from app.infrastructure.config import Settings, load_settings
from app.infrastructure.deepseek import build_chat_model
from app.infrastructure.fernet_codec import FernetConversationCodec
from app.infrastructure.neighbor_catalog import StaticNeighborRepository
from app.presentation.errors import register_error_handlers
from app.presentation.request_logging import REQUEST_ID_HEADER, RequestIdFilter, log_requests
from app.presentation.routes import build_router

logger = logging.getLogger("app")


def configure_logging(level: str) -> None:
    """App loggers use LOG_LEVEL; third-party libraries only report warnings.

    Called from the lifespan, not at import: importing the app must not change
    logging for the process that imports it (tests, scripts, tooling).
    """
    handler = logging.StreamHandler()
    handler.addFilter(RequestIdFilter())
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s [%(request_id)s] %(name)s: %(message)s")
    )
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(logging.WARNING)
    logger.setLevel(level)


def _log_startup(settings: Settings, neighbors: tuple[str, ...]) -> None:
    logger.info(
        "Starting: model=%s deepseek_configured=%s max_tokens=%s timeout=%ss rate_limit=%s "
        "context_ttl=%ss cors=%s neighbors=%s",
        settings.deepseek_model,
        bool(settings.deepseek_api_key),
        settings.deepseek_max_tokens,
        settings.deepseek_timeout_seconds,
        settings.rate_limit,
        settings.context_ttl_seconds,
        ",".join(settings.cors_origins),
        ",".join(neighbors),
    )
    if settings.context_secret_is_ephemeral:
        logger.warning("CONTEXT_SECRET is not set: conversations will reset on every restart")


def create_app(settings: Settings, chat_model: ChatModel | None = None) -> FastAPI:
    model = chat_model or build_chat_model(settings)
    neighbors = StaticNeighborRepository()

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        configure_logging(settings.log_level)
        _log_startup(settings, neighbors.ids())
        try:
            yield
        finally:
            await model.aclose()
            logger.info("Stopped")

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
        allow_headers=["Content-Type", REQUEST_ID_HEADER],
        expose_headers=[REQUEST_ID_HEADER],
    )
    app.middleware("http")(log_requests)
    app.include_router(build_router(limiter, settings.rate_limit, neighbors.ids()))
    register_error_handlers(app)
    return app


_settings = load_settings()
app = create_app(_settings)
