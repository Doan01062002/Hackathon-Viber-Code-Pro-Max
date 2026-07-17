"""Logging configuration owned by the AI module."""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime
from threading import Lock
from typing import Literal

from ai.config import AISettings, get_ai_settings

LOGGER_NAME = "srrm.ai"
_HANDLER_MARKER = "_srrm_ai_handler"
_configuration_lock = Lock()


class JsonFormatter(logging.Formatter):
    """Render stable, machine-readable agent logs."""

    _extra_fields = (
        "event",
        "run_id",
        "duration_ms",
        "query_length",
        "error_type",
    )

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for field in self._extra_fields:
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False)


def _build_formatter(log_format: Literal["json", "text"]) -> logging.Formatter:
    if log_format == "json":
        return JsonFormatter()
    return logging.Formatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )


def configure_ai_logging(settings: AISettings | None = None) -> logging.Logger:
    """Configure the AI logger without changing the process root logger."""
    resolved_settings = settings or get_ai_settings()
    logger = logging.getLogger(LOGGER_NAME)

    with _configuration_lock:
        logger.setLevel(resolved_settings.ai_log_level)
        logger.propagate = False

        handler = next(
            (current for current in logger.handlers if getattr(current, _HANDLER_MARKER, False)),
            None,
        )
        if handler is None:
            handler = logging.StreamHandler(sys.stdout)
            setattr(handler, _HANDLER_MARKER, True)
            logger.addHandler(handler)

        handler.setLevel(resolved_settings.ai_log_level)
        handler.setFormatter(_build_formatter(resolved_settings.ai_log_format))

    return logger


def get_ai_logger() -> logging.Logger:
    """Return the configured logger used across the AI module."""
    return configure_ai_logging()
