"""Observability utilities shared by agents and scripts."""

from .logging_config import configure_logging, get_logger, ObservabilityConfig
from .error_taxonomy import (
    ErrorCategory,
    ErrorEvent,
    ErrorReport,
    ErrorSeverity,
    build_error_event,
    summarize_exception,
)
from .hub import ObservabilityHub

__all__ = [
    "configure_logging",
    "get_logger",
    "ObservabilityConfig",
    "ErrorCategory",
    "ErrorSeverity",
    "ErrorReport",
    "ErrorEvent",
    "build_error_event",
    "summarize_exception",
    "ObservabilityHub",
]
