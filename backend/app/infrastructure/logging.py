"""Application logging configuration."""

import logging

from app.infrastructure.config import Settings
from app.presentation.request_logging import RequestIdFilter

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
    logging.getLogger("app").setLevel(level)


def log_startup(settings: Settings, neighbors: tuple[str, ...]) -> None:
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
