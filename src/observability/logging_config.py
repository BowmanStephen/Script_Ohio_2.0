"""
Structured logging helpers for the Script Ohio platform.

The utilities here centralize logging configuration so that agents and scripts
emit consistent JSON payloads that are easy to aggregate in log pipelines.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from typing import Any, Dict

_OBSERVABILITY_INITIALIZED = False


@dataclass
class ObservabilityConfig:
    """Runtime logging configuration driven by environment variables."""

    service_name: str = os.getenv("SERVICE_NAME", "script_ohio")
    environment: str = os.getenv("APP_ENV", "development")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    structured: bool = os.getenv("STRUCTURED_LOGGING", "1").lower() not in {"0", "false", "no"}


class StructuredLogFormatter(logging.Formatter):
    """Minimal JSON formatter compatible with log aggregators."""

    _RESERVED_FIELDS = {
        "name",
        "msg",
        "args",
        "levelname",
        "levelno",
        "pathname",
        "filename",
        "module",
        "exc_info",
        "exc_text",
        "stack_info",
        "lineno",
        "funcName",
        "created",
        "msecs",
        "relativeCreated",
        "thread",
        "threadName",
        "processName",
        "process",
    }

    def __init__(self, config: ObservabilityConfig):
        super().__init__()
        self.config = config

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat()
        log_entry: Dict[str, Any] = {
            "timestamp": timestamp,
            "level": record.levelname.lower(),
            "logger": record.name,
            "message": record.getMessage(),
            "service": self.config.service_name,
            "environment": self.config.environment,
        }

        if record.exc_info:
            log_entry["exc_info"] = self.formatException(record.exc_info)
        if record.stack_info:
            log_entry["stack_info"] = self.formatStack(record.stack_info)

        # Capture any custom attributes added via `logger.info(..., extra={})`
        for key, value in record.__dict__.items():
            if key in self._RESERVED_FIELDS or key.startswith("_"):
                continue
            log_entry[key] = value

        return json.dumps(log_entry, default=str, ensure_ascii=False)


def configure_logging(
    config: ObservabilityConfig | None = None,
    *,
    service_name: str | None = None,
    environment: str | None = None,
    log_level: str | None = None,
    structured: bool | None = None,
    force: bool = False,
) -> None:
    """
    Configure global logging with optional structured output.

    The configuration is idempotent; repeated calls are ignored unless `force=True`.
    """

    global _OBSERVABILITY_INITIALIZED

    if _OBSERVABILITY_INITIALIZED and not force:
        return

    config = config or ObservabilityConfig()
    if service_name is not None:
        config = replace(config, service_name=service_name)
    if environment is not None:
        config = replace(config, environment=environment)
    if log_level is not None:
        config = replace(config, log_level=log_level)
    if structured is not None:
        config = replace(config, structured=structured)

    root_logger = logging.getLogger()
    root_logger.handlers = []
    root_logger.setLevel(config.log_level.upper())

    handler = logging.StreamHandler()
    if config.structured:
        handler.setFormatter(StructuredLogFormatter(config))
    else:
        handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )

    root_logger.addHandler(handler)
    logging.captureWarnings(True)
    _OBSERVABILITY_INITIALIZED = True


def get_logger(name: str, **context: Any) -> logging.Logger:
    """Return a configured logger, optionally wrapped with static context."""

    configure_logging()
    base_logger = logging.getLogger(name)
    if not context:
        return base_logger
    return logging.LoggerAdapter(base_logger, extra=context)  # type: ignore[return-value]
