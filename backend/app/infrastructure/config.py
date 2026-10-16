"""Application settings loaded from environment variables and backend/.env."""

from __future__ import annotations

import os
import secrets
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True, slots=True)
class Settings:
    deepseek_api_key: str = ""
    deepseek_model: str = "deepseek-flash"
    deepseek_base_url: str = ""
    deepseek_max_tokens: int = 1000
    deepseek_timeout_seconds: float = 30.0
    context_secret: str = ""
    context_secret_is_ephemeral: bool = False
    context_ttl_seconds: int = 24 * 60 * 60
    rate_limit: str = "20/minute"
    max_retries: int = 0
    cors_origins: tuple[str, ...] = ("http://127.0.0.1:3000", "http://127.0.0.1:5173")
    log_level: str = "INFO"


def _origins(configured: str | None) -> tuple[str, ...]:
    if not configured:
        return Settings().cors_origins
    return tuple(origin.strip().rstrip("/") for origin in configured.split(",") if origin.strip())


def _base_url(configured: str | None) -> str:
    """Пустая строка означает стандартный адрес DeepSeek из langchain-deepseek."""
    return (configured or "").strip().rstrip("/")


def load_settings() -> Settings:
    load_dotenv(Path(__file__).resolve().parents[2] / ".env")
    defaults = Settings()
    context_secret = os.getenv("CONTEXT_SECRET", "").strip()
    return Settings(
        deepseek_api_key=os.getenv("DEEPSEEK_API_KEY", "").strip(),
        deepseek_model=os.getenv("DEEPSEEK_MODEL", defaults.deepseek_model),
        deepseek_base_url=_base_url(os.getenv("DEEPSEEK_BASE_URL")),
        deepseek_max_tokens=int(os.getenv("DEEPSEEK_MAX_TOKENS", defaults.deepseek_max_tokens)),
        deepseek_timeout_seconds=float(
            os.getenv("DEEPSEEK_TIMEOUT_SECONDS", defaults.deepseek_timeout_seconds)
        ),
        context_secret=context_secret or secrets.token_urlsafe(32),
        context_secret_is_ephemeral=not context_secret,
        context_ttl_seconds=int(os.getenv("CONTEXT_TTL_SECONDS", defaults.context_ttl_seconds)),
        rate_limit=os.getenv("RATE_LIMIT", defaults.rate_limit),
        cors_origins=_origins(os.getenv("CORS_ORIGINS")),
        log_level=os.getenv("LOG_LEVEL", defaults.log_level).upper(),
    )
