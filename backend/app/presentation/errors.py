"""Every error leaves the API as `{"detail": "..."}` with text a user can read."""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from app.application.errors import (
    ApplicationError,
    ChatModelFailed,
    ChatModelNotConfigured,
    ChatModelTimeout,
    NeighborNotFound,
)
from app.domain.conversation import MAX_MESSAGE_LENGTH

logger = logging.getLogger(__name__)

APPLICATION_ERRORS: dict[type[ApplicationError], tuple[int, str]] = {
    NeighborNotFound: (422, "Неизвестный сосед"),
    ChatModelNotConfigured: (503, "Сосед сейчас недоступен: модель не настроена"),
    ChatModelTimeout: (504, "Сосед не ответил вовремя, попробуйте ещё раз"),
    ChatModelFailed: (502, "Сосед не смог ответить, попробуйте ещё раз"),
}

VALIDATION_MESSAGES = {
    "message": f"Сообщение должно быть от 1 до {MAX_MESSAGE_LENGTH} символов",
    "context": "Некорректный context",
}


def _error(status: int, detail: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"detail": detail})


async def _application_error(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, ApplicationError)
    status, detail = APPLICATION_ERRORS[type(exc)]
    level = logging.ERROR if status >= 500 else logging.WARNING
    logger.log(level, "%s -> %s", type(exc).__name__, status)
    return _error(status, detail)


async def _validation_error(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)
    fields = {str(part) for error in exc.errors() for part in error["loc"]}
    problems = sorted({f"{'.'.join(map(str, error['loc']))}:{error['type']}" for error in exc.errors()})
    logger.warning("Invalid request: %s", ", ".join(problems))
    detail = next(
        (text for field, text in VALIDATION_MESSAGES.items() if field in fields),
        "Некорректный запрос",
    )
    return _error(422, detail)


async def _rate_limited(_: Request, __: Exception) -> JSONResponse:
    return _error(429, "Слишком много сообщений, подождите минуту")


def register_error_handlers(app: FastAPI) -> None:
    for error in APPLICATION_ERRORS:
        app.add_exception_handler(error, _application_error)
    app.add_exception_handler(RequestValidationError, _validation_error)
    app.add_exception_handler(RateLimitExceeded, _rate_limited)
