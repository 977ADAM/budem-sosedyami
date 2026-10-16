"""Access log with a request ID that is attached to every log line of the request."""

from __future__ import annotations

import logging
import re
import time
from collections.abc import Awaitable, Callable
from contextvars import ContextVar
from uuid import uuid4

from fastapi import Request, Response

REQUEST_ID_HEADER = "X-Request-ID"
request_id_var: ContextVar[str] = ContextVar("request_id", default="-")

logger = logging.getLogger("app.http")

# Client-supplied IDs end up in the log, so only harmless characters are accepted.
_VALID_REQUEST_ID = re.compile(r"[A-Za-z0-9._-]{1,64}")
_QUIET_PATHS = {"/health"}


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        return True


def _request_id(request: Request) -> str:
    candidate = request.headers.get(REQUEST_ID_HEADER, "")
    return candidate if _VALID_REQUEST_ID.fullmatch(candidate) else uuid4().hex[:12]


async def log_requests(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    request_id = _request_id(request)
    token = request_id_var.set(request_id)
    started = time.perf_counter()
    client = request.client.host if request.client else "-"
    try:
        response = await call_next(request)
    except Exception:
        logger.exception(
            "%s %s crashed after %.0fms client=%s",
            request.method, request.url.path, (time.perf_counter() - started) * 1000, client,
        )
        raise
    else:
        response.headers[REQUEST_ID_HEADER] = request_id
        level = logging.DEBUG if request.url.path in _QUIET_PATHS else logging.INFO
        logger.log(
            level,
            "%s %s %s %.0fms client=%s",
            request.method, request.url.path, response.status_code,
            (time.perf_counter() - started) * 1000, client,
        )
        return response
    finally:
        request_id_var.reset(token)
