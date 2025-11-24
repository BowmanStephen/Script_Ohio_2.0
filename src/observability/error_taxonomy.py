"""
Centralized error taxonomy and reporting helpers.

This module consolidates the canonical error severity levels, categories,
and reporting structures so every agent/script uses the same metadata.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4


class ErrorCategory(str, Enum):
    """Unified error categories for routing and dashboards."""

    NETWORK = "network"
    DATA = "data"
    MODEL = "model"
    AGENT = "agent"
    SYSTEM = "system"
    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit"
    RESOURCE = "resource"
    CONFIGURATION = "configuration"
    SECURITY = "security"
    EXTERNAL_API = "external_api"
    IO = "io"
    VALIDATION = "validation"
    PERMISSION = "permission"
    EXECUTION = "execution"
    UNKNOWN = "unknown"


class ErrorSeverity(str, Enum):
    """Normalized error impact tiers used across the platform."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class ErrorReport:
    """Structured error payload emitted to logs/telemetry."""

    error_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    error_type: str = ""
    error_message: str = ""
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
    category: ErrorCategory = ErrorCategory.UNKNOWN
    context: Dict[str, Any] = field(default_factory=dict)
    stack_trace: str = ""
    recovery_attempted: bool = False
    recovery_successful: bool = False
    user_facing_message: str = ""
    technical_details: Dict[str, Any] = field(default_factory=dict)
    affected_components: List[str] = field(default_factory=list)

    def to_event_payload(self) -> Dict[str, Any]:
        """Convert the report to a serializable dict for logs or exporters."""
        payload = asdict(self)
        payload["severity"] = self.severity.value
        payload["category"] = self.category.value
        payload["timestamp"] = self.timestamp.isoformat()
        return payload


@dataclass
class ErrorEvent:
    """
    Structured representation of an error for logging and telemetry.

    Attributes:
        message: Human-readable summary of the error.
        category: Taxonomy bucket for the error.
        severity: Severity level.
        context: Optional contextual fields (request IDs, agent names, etc).
        remediation: Optional hint for mitigation.
    """

    message: str
    category: ErrorCategory = ErrorCategory.UNKNOWN
    severity: ErrorSeverity = ErrorSeverity.ERROR
    context: Dict[str, Any] = field(default_factory=dict)
    remediation: Optional[str] = None

    def to_log_extra(self) -> Dict[str, Any]:
        """Return logging extra payload for structured logging."""
        payload = {
            "error.category": self.category.value,
            "error.severity": self.severity.value,
        }
        if self.context:
            payload["error.context"] = self.context
        if self.remediation:
            payload["error.remediation"] = self.remediation
        return payload


def build_error_event(
    message: str,
    category: ErrorCategory = ErrorCategory.UNKNOWN,
    severity: ErrorSeverity = ErrorSeverity.ERROR,
    context: Optional[Dict[str, Any]] = None,
    remediation: Optional[str] = None,
) -> ErrorEvent:
    """Helper to quickly construct an ErrorEvent."""
    return ErrorEvent(
        message=message,
        category=category,
        severity=severity,
        context=context or {},
        remediation=remediation,
    )


def summarize_exception(exc: BaseException) -> Dict[str, Optional[str]]:
    """Extract lightweight metadata about an exception."""
    return {
        "exception_type": type(exc).__name__,
        "exception_message": str(exc)[:2048],
    }
