"""Simple observability hub for structured events and health metrics."""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .error_taxonomy import ErrorReport, ErrorSeverity
from .logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class ObservabilityEvent:
    """Generic event wrapper used for in-memory fan-out."""

    event_type: str
    payload: Dict[str, Any]
    severity: str = "info"


class ObservabilityHub:
    """In-process event bus for logging + health snapshots."""

    _instance: Optional["ObservabilityHub"] = None
    _lock = threading.Lock()

    def __init__(self) -> None:
        self._events: List[ObservabilityEvent] = []
        self._metrics: Dict[str, Any] = {}

    @classmethod
    def instance(cls) -> "ObservabilityHub":
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def emit_event(self, event_type: str, payload: Dict[str, Any], severity: str = "info") -> None:
        event = ObservabilityEvent(event_type=event_type, payload=payload, severity=severity)
        self._events.append(event)
        logger.log(
            level=self._severity_to_level(severity),
            msg=f"[event:{event_type}]",
            extra={"event": payload},
        )

    def emit_error(self, error_report: ErrorReport) -> None:
        self.emit_event(
            event_type="error",
            payload=error_report.to_event_payload(),
            severity=error_report.severity.value,
        )

    def set_metric(self, key: str, value: Any) -> None:
        self._metrics[key] = value

    def export_metrics(self) -> Dict[str, Any]:
        return dict(self._metrics)

    @staticmethod
    def _severity_to_level(severity: str) -> int:
        mapping = {
            ErrorSeverity.LOW.value: logging.INFO,
            ErrorSeverity.MEDIUM.value: logging.WARNING,
            ErrorSeverity.HIGH.value: logging.ERROR,
            ErrorSeverity.CRITICAL.value: logging.CRITICAL,
            ErrorSeverity.INFO.value: logging.INFO,
            ErrorSeverity.WARNING.value: logging.WARNING,
            ErrorSeverity.ERROR.value: logging.ERROR,
        }
        return mapping.get(severity, logging.INFO)

