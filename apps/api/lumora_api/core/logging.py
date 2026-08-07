"""Structured logging configuration, applied once at process startup."""

import logging
import sys
from typing import Any

from lumora_api.core.config import Settings


class _JsonFormatter(logging.Formatter):
    """Minimal JSON log formatter — no external dependency required."""

    def format(self, record: logging.LogRecord) -> str:
        import json

        payload: dict[str, Any] = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload)


def configure_logging(settings: Settings) -> None:
    """Configure the root logger once, at application startup."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(_JsonFormatter())

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(settings.log_level)

    # Quiet down noisy third-party loggers below the app's own threshold.
    logging.getLogger("uvicorn.access").setLevel(
        "WARNING" if settings.is_production else settings.log_level
    )
