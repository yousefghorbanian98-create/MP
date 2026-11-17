"""لاگ ساختاریافته با structlog — JSON برای Grafana/Loki (لایهٔ ۱۳)."""

from __future__ import annotations

import logging
import sys

import structlog
from asgi_correlation_id import correlation_id


def add_request_id(_logger, _method_name: str, event_dict: dict) -> dict:
    """Attach the OSS ASGI correlation middleware's ID to structured logs."""
    request_id = correlation_id.get()
    if request_id:
        event_dict["request_id"] = request_id
    return event_dict


def configure_logging(json_logs: bool = True) -> None:
    """پیکربندی structlog — در dev خوانا، در production JSON."""
    processors: list = [
        structlog.contextvars.merge_contextvars,
        add_request_id,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]
    if json_logs:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        logger_factory=structlog.PrintLoggerFactory(sys.stdout),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)
