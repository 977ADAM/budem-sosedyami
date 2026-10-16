"""Backend with a fake model, so load tests measure our code and not DeepSeek.

    uv run uvicorn loadtest.stub_server:app --no-access-log --port 8100

STUB_LATENCY (seconds, default 1.0) and STUB_REPLY_CHARS (default 800) shape the
fake replies; STUB_RATE_LIMIT (default effectively unlimited) sets the per-IP limit;
LOG_LEVEL (default WARNING) sets the log level.
"""

from __future__ import annotations

import asyncio
import os
import random
from collections.abc import Sequence

from app.domain.conversation import Turn
from app.infrastructure.config import Settings
from app.main import create_app

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


app = create_app(
    Settings(
        context_secret="loadtest",
        log_level=os.getenv("LOG_LEVEL", "WARNING").upper(),
        rate_limit=os.getenv("STUB_RATE_LIMIT", "1000000/minute"),
    ),
    StubChatModel(
        latency=float(os.getenv("STUB_LATENCY", "1.0")),
        reply_chars=int(os.getenv("STUB_REPLY_CHARS", "800")),
    ),
)
