"""Every error leaves the API as `{"detail": "..."}` with text a user can read."""

from __future__ import annotations

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


async def _application_error(_: Request, exc: ApplicationError) -> JSONResponse:
    return _error(*APPLICATION_ERRORS[type(exc)])


async def _validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
    fields = {str(part) for error in exc.errors() for part in error["loc"]}
    detail = next(
        (text for field, text in VALIDATION_MESSAGES.items() if field in fields),
        "Некорректный запрос",
    )
    return _error(422, detail)


async def _rate_limited(_: Request, __: RateLimitExceeded) -> JSONResponse:
    return _error(429, "Слишком много сообщений, подождите минуту")


def register_error_handlers(app: FastAPI) -> None:
    for error in APPLICATION_ERRORS:
        app.add_exception_handler(error, _application_error)
    app.add_exception_handler(RequestValidationError, _validation_error)
    app.add_exception_handler(RateLimitExceeded, _rate_limited)
