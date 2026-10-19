"""Application settings loaded from environment variables and backend/.env."""

from __future__ import annotations

import math
import os
import re
import secrets
from dataclasses import dataclass
from pathlib import Path
from typing import TypeVar

from dotenv import load_dotenv
from limits import parse_many


@dataclass(frozen=True, slots=True)
class Settings:
    deepseek_api_key: str = ""
    deepseek_model: str = "deepseek-flash"
    deepseek_max_tokens: int = 1000
    deepseek_timeout_seconds: float = 30.0
    context_secret: str = ""
    context_secret_is_ephemeral: bool = False
    context_ttl_seconds: int = 24 * 60 * 60
    rate_limit: str = "20/minute"
    max_retries: int = 0
    cors_origins: tuple[str, ...] = ("http://127.0.0.1:3000", "http://localhost:3000")
    log_level: str = "INFO"

    def __post_init__(self) -> None:
        for name, value in (
            ("DEEPSEEK_MAX_TOKENS", self.deepseek_max_tokens),
            ("CONTEXT_TTL_SECONDS", self.context_ttl_seconds),
        ):
            if value <= 0:
                raise ValueError(f"{name}: ожидается целое число больше нуля")
        if not math.isfinite(self.deepseek_timeout_seconds) or self.deepseek_timeout_seconds <= 0:
            raise ValueError("DEEPSEEK_TIMEOUT_SECONDS: ожидается конечное число больше нуля")
        if self.max_retries != 0:
            raise ValueError("MAX_RETRIES: повторные попытки запрещены, допустимо только 0")
        try:
            rate_limits = parse_many(self.rate_limit)
            zero_window = re.search(r"(?:/|\bper)\s*0+\s*[a-z]", self.rate_limit, re.IGNORECASE)
            if not rate_limits or any(limit.amount <= 0 for limit in rate_limits) or zero_window:
                raise ValueError("Rate limit amounts and windows must be positive")
        except ValueError as exc:
            raise ValueError("RATE_LIMIT: ожидается положительный лимит, например 20/minute") from exc



def _origins(configured: str | None) -> tuple[str, ...]:
    if not configured:
        return Settings().cors_origins
    return tuple(origin.strip().rstrip("/") for origin in configured.split(",") if origin.strip())


Number = TypeVar("Number", int, float)


def _env_number(name: str, default: Number, number_type: type[Number]) -> Number:
    try:
        return number_type(os.getenv(name, str(default)))
    except ValueError as exc:
        raise ValueError(f"{name}: некорректное числовое значение") from exc


def load_settings() -> Settings:
    load_dotenv(Path(__file__).resolve().parents[2] / ".env")
    defaults = Settings()
    context_secret = os.getenv("CONTEXT_SECRET", "").strip()
    return Settings(
        deepseek_api_key=os.getenv("DEEPSEEK_API_KEY", "").strip(),
        deepseek_model=os.getenv("DEEPSEEK_MODEL", defaults.deepseek_model),
        deepseek_max_tokens=_env_number("DEEPSEEK_MAX_TOKENS", defaults.deepseek_max_tokens, int),
        deepseek_timeout_seconds=_env_number(
            "DEEPSEEK_TIMEOUT_SECONDS", defaults.deepseek_timeout_seconds, float
        ),
        context_secret=context_secret or secrets.token_urlsafe(32),
        context_secret_is_ephemeral=not context_secret,
        context_ttl_seconds=_env_number("CONTEXT_TTL_SECONDS", defaults.context_ttl_seconds, int),
        rate_limit=os.getenv("RATE_LIMIT", defaults.rate_limit),
        cors_origins=_origins(os.getenv("CORS_ORIGINS")),
        log_level=os.getenv("LOG_LEVEL", defaults.log_level).upper(),
        max_retries=_env_number("MAX_RETRIES", defaults.max_retries, int),
    )
