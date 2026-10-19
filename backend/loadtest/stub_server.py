"""Backend with a fake model, so load tests measure our code and not DeepSeek.

    uv run uvicorn loadtest.stub_server:app --no-access-log --port 8100

STUB_LATENCY (seconds, default 1.0) and STUB_REPLY_CHARS (default 800) shape the
fake replies; STUB_RATE_LIMIT (default effectively unlimited) sets the per-IP limit;
LOG_LEVEL (default WARNING) sets the log level.
"""

from __future__ import annotations

import asyncio
import logging
import os
import random
from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager

from fastapi import FastAPI
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.application.agent_service import AgentService
from app.domain.conversation import Turn
from app.infrastructure.config import Settings
from app.infrastructure.fernet_codec import FernetConversationCodec
from app.infrastructure.neighbor_catalog import StaticNeighborRepository
from app.presentation.errors import register_error_handlers
from app.presentation.request_logging import log_requests
from app.presentation.routes import router

WORDS = (
    "дом двор парк метро кофе школа прогулка сквер улица район магазин аптека утро вечер "
    "выходные дочка работа окно встреча автобус пекарня бульвар галерея пруд самокат "
    "остановка секция кружок маршрут тишина деревья скамейка соседи библиотека"
).split()


class StubChatModel:
    def __init__(self, latency: float, reply_chars: int) -> None:
        self._latency = latency
        self._reply_chars = reply_chars

    async def reply(self, system_prompt: str, history: Sequence[Turn], message: str) -> str:
        await asyncio.sleep(self._latency * random.uniform(0.5, 1.5))
        text = " ".join(random.choice(WORDS) for _ in range(self._reply_chars // 6))
        return text[: self._reply_chars].capitalize() + "."

    async def aclose(self) -> None:
        pass


settings = Settings(
    context_secret="loadtest",
    log_level=os.getenv("LOG_LEVEL", "WARNING").upper(),
    rate_limit=os.getenv("STUB_RATE_LIMIT", "1000000/minute"),
)
model = StubChatModel(
    latency=float(os.getenv("STUB_LATENCY", "1.0")),
    reply_chars=int(os.getenv("STUB_REPLY_CHARS", "800")),
)
neighbors = StaticNeighborRepository()
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    logging.basicConfig(level=settings.log_level)
    try:
        yield
    finally:
        await model.aclose()


app = FastAPI(lifespan=lifespan)
app.state.settings = settings
app.state.limiter = limiter
app.state.check_rate_limit = limiter.limit(settings.rate_limit)(lambda request: None)
app.state.agent_service = AgentService(
    neighbors=neighbors,
    model=model,
    codec=FernetConversationCodec(settings.context_secret, settings.context_ttl_seconds),
)
app.middleware("http")(log_requests)
register_error_handlers(app)
app.include_router(router)
