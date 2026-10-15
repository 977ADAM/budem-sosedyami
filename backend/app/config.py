"""Application settings loaded from environment variables and backend/.env."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")


@dataclass(frozen=True, slots=True)
class Settings:
    database_url: str
    deepseek_api_key: str
    deepseek_model: str
    deepseek_base_url: str
    cors_origins: tuple[str, ...]
    session_cookie_name: str
    session_cookie_secure: bool
    session_cookie_samesite: str


def _configured_origins() -> tuple[str, ...]:
    configured = os.getenv("CORS_ORIGINS")
    origins = configured.split(",") if configured else [
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]
    return tuple(origin.strip().rstrip("/") for origin in origins if origin.strip())


def _configured_cookie_secure() -> bool:
    configured = os.getenv("SESSION_COOKIE_SECURE")
    return configured.lower() == "true" if configured else True


def _load_settings() -> Settings:
    return Settings(
        database_url=os.getenv("DATABASE_URL", "").strip(),
        deepseek_api_key=os.getenv("DEEPSEEK_API_KEY", "").strip(),
        deepseek_model=os.getenv("DEEPSEEK_MODEL", "deepseek-flash"),
        deepseek_base_url="https://api.deepseek.com",
        cors_origins=_configured_origins(),
        session_cookie_name="neighbor_session",
        session_cookie_secure=_configured_cookie_secure(),
        session_cookie_samesite=os.getenv("SESSION_COOKIE_SAMESITE", "lax").lower(),
    )


settings = _load_settings()
