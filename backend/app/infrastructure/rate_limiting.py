"""Bind SlowAPI's request check to an application's limiter."""

from collections.abc import Callable

from fastapi import Request
from slowapi import Limiter


def build_rate_limit_check(limiter: Limiter, rate_limit: str) -> Callable[[Request], None]:
    @limiter.limit(rate_limit)
    def check(request: Request) -> None:
        """SlowAPI checks the limit before entering this function."""

    return check
