#!/usr/bin/env python3
"""
Enhanced Error Handling Framework for Script Ohio 2.0

Provides comprehensive error handling, logging, and recovery mechanisms
for the Script Ohio 2.0 ecosystem.
"""

import functools
import json
import logging
import os
import sys
import time
import traceback
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union


class ErrorSeverity(Enum):
    """Error severity levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for better classification"""

    SYNTAX = "syntax"
    RUNTIME = "runtime"
    NETWORK = "network"
    FILE_IO = "file_io"
    API = "api"
    DATA = "data"
    MODEL = "model"
    CONFIGURATION = "configuration"
    VALIDATION = "validation"
    UNKNOWN = "unknown"


class EnhancedError:
    """Enhanced error object with comprehensive context"""

    def __init__(
        self,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        exception: Optional[Exception] = None,
        context: Optional[Dict[str, Any]] = None,
        suggestions: Optional[List[str]] = None,
        recoverable: bool = False,
        recovery_action: Optional[str] = None,
    ):
        self.message = message
        self.severity = severity
        self.category = category
        self.exception = exception
        self.context = context or {}
        self.suggestions = suggestions or []
        self.recoverable = recoverable
        self.recovery_action = recovery_action
        self.timestamp = datetime.now()
        self.traceback_str = traceback.format_exc() if exception else None

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for serialization"""
        return {
            "message": self.message,
            "severity": self.severity.value,
            "category": self.category.value,
            "context": self.context,
            "suggestions": self.suggestions,
            "recoverable": self.recoverable,
            "recovery_action": self.recovery_action,
            "timestamp": self.timestamp.isoformat(),
            "traceback": self.traceback_str,
            "exception_type": type(self.exception).__name__ if self.exception else None,
        }


class ErrorHandler:
    """Enhanced error handler with logging, recovery, and analytics"""

    def __init__(self, log_file: str = None, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.log_file = (
            Path(log_file) if log_file else self.project_root / "error_log.json"
        )
        self.error_history: List[EnhancedError] = []
        self.error_patterns: Dict[str, int] = {}

        # Set up logging
        self._setup_logging()

        # Load existing error history
        self._load_error_history()

    def _setup_logging(self):
        """Set up comprehensive logging"""
        # Create logs directory if it doesn't exist
        log_dir = self.project_root / "logs"
        log_dir.mkdir(exist_ok=True)

        # Configure Python logging
        self.logger = logging.getLogger("script_ohio_error_handler")
        self.logger.setLevel(logging.DEBUG)

        # File handler
        file_handler = logging.FileHandler(log_dir / "errors.log")
        file_handler.setLevel(logging.DEBUG)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # Add handlers
        if not self.logger.handlers:
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)

    def _load_error_history(self):
        """Load existing error history from file"""
        if self.log_file.exists():
            try:
                with open(self.log_file, "r") as f:
                    data = json.load(f)
                    for error_data in data.get("errors", []):
                        # Recreate EnhancedError objects
                        error = EnhancedError(
                            message=error_data["message"],
                            severity=ErrorSeverity(error_data["severity"]),
                            category=ErrorCategory(error_data["category"]),
                            context=error_data["context"],
                            suggestions=error_data["suggestions"],
                            recoverable=error_data["recoverable"],
                            recovery_action=error_data["recovery_action"],
                        )
                        error.timestamp = datetime.fromisoformat(
                            error_data["timestamp"]
                        )
                        error.traceback_str = error_data["traceback"]
                        self.error_history.append(error)

                        # Track patterns
                        pattern_key = f"{error.category.value}:{error.message[:50]}"
                        self.error_patterns[pattern_key] = (
                            self.error_patterns.get(pattern_key, 0) + 1
                        )

            except Exception as e:
                self.logger.warning(f"Failed to load error history: {e}")

    def save_error_history(self):
        """Save error history to file"""
        try:
            data = {
                "last_updated": datetime.now().isoformat(),
                "total_errors": len(self.error_history),
                "error_patterns": self.error_patterns,
                "errors": [
                    error.to_dict() for error in self.error_history[-1000:]
                ],  # Keep last 1000 errors
            }

            with open(self.log_file, "w") as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            self.logger.error(f"Failed to save error history: {e}")

    def handle_error(
        self,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        exception: Optional[Exception] = None,
        context: Optional[Dict[str, Any]] = None,
        suggestions: Optional[List[str]] = None,
        recoverable: bool = False,
        recovery_action: Optional[str] = None,
        reraise: bool = False,
    ) -> Optional[EnhancedError]:
        """
        Handle an error with comprehensive logging and optional recovery

        Args:
            message: Error message
            severity: Error severity level
            category: Error category
            exception: Original exception if any
            context: Additional context information
            suggestions: List of suggestions for fixing the error
            recoverable: Whether the error is recoverable
            recovery_action: Action to take for recovery
            reraise: Whether to reraise the exception

        Returns:
            EnhancedError object
        """
        # Create enhanced error
        error = EnhancedError(
            message=message,
            severity=severity,
            category=category,
            exception=exception,
            context=context,
            suggestions=suggestions,
            recoverable=recoverable,
            recovery_action=recovery_action,
        )

        # Add to history
        self.error_history.append(error)

        # Track patterns
        pattern_key = f"{error.category.value}:{error.message[:50]}"
        self.error_patterns[pattern_key] = self.error_patterns.get(pattern_key, 0) + 1

        # Log based on severity
        log_message = f"[{error.category.value.upper()}] {error.message}"
        if error.context:
            log_message += f" | Context: {error.context}"
        if error.suggestions:
            log_message += f" | Suggestions: {', '.join(error.suggestions[:2])}"

        if severity == ErrorSeverity.CRITICAL:
            self.logger.critical(log_message)
        elif severity == ErrorSeverity.HIGH:
            self.logger.error(log_message)
        elif severity == ErrorSeverity.MEDIUM:
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)

        # Auto-recovery if possible
        if recoverable and recovery_action:
            try:
                self.logger.info(f"Attempting recovery: {recovery_action}")
                # Execute recovery action (this could be more sophisticated)
                if callable(recovery_action):
                    recovery_action()
                self.logger.info("Recovery successful")
            except Exception as recovery_error:
                self.logger.error(f"Recovery failed: {recovery_error}")

        # Save history periodically
        if len(self.error_history) % 10 == 0:
            self.save_error_history()

        # Reraise if requested
        if reraise and exception:
            raise exception

        return error

    def get_error_summary(self, days: int = 7) -> Dict[str, Any]:
        """Get error summary for the last N days"""
        cutoff_date = datetime.now().timestamp() - (days * 24 * 3600)
        recent_errors = [
            error
            for error in self.error_history
            if error.timestamp.timestamp() > cutoff_date
        ]

        category_counts = {}
        severity_counts = {}

        for error in recent_errors:
            category_counts[error.category.value] = (
                category_counts.get(error.category.value, 0) + 1
            )
            severity_counts[error.severity.value] = (
                severity_counts.get(error.severity.value, 0) + 1
            )

        return {
            "period_days": days,
            "total_errors": len(recent_errors),
            "errors_by_category": category_counts,
            "errors_by_severity": severity_counts,
            "most_common_patterns": sorted(
                self.error_patterns.items(), key=lambda x: x[1], reverse=True
            )[:10],
            "recoverable_errors": len([e for e in recent_errors if e.recoverable]),
        }

    def suggest_fixes(self, error: EnhancedError) -> List[str]:
        """Suggest fixes based on error type and patterns"""
        suggestions = error.suggestions.copy()

        # Add suggestions based on category
        if error.category == ErrorCategory.FILE_IO:
            suggestions.extend(
                [
                    "Check if the file exists and is readable",
                    "Verify file permissions",
                    "Check if the disk is full",
                ]
            )
        elif error.category == ErrorCategory.NETWORK:
            suggestions.extend(
                [
                    "Check internet connection",
                    "Verify API endpoints are accessible",
                    "Check rate limiting status",
                ]
            )
        elif error.category == ErrorCategory.API:
            suggestions.extend(
                [
                    "Verify API key is valid",
                    "Check API rate limits",
                    "Review API documentation",
                ]
            )
        elif error.category == ErrorCategory.DATA:
            suggestions.extend(
                [
                    "Check data format and structure",
                    "Verify data completeness",
                    "Check for data corruption",
                ]
            )
        elif error.category == ErrorCategory.MODEL:
            suggestions.extend(
                [
                    "Check if model file exists",
                    "Verify model format compatibility",
                    "Check model dependencies",
                ]
            )
        elif error.category == ErrorCategory.CONFIGURATION:
            suggestions.extend(
                [
                    "Check configuration files",
                    "Verify environment variables",
                    "Review system requirements",
                ]
            )

        # Add pattern-based suggestions
        pattern_key = f"{error.category.value}:{error.message[:50]}"
        if self.error_patterns.get(pattern_key, 0) > 3:
            suggestions.append(
                f"⚠️  This error has occurred {self.error_patterns[pattern_key]} times - consider investigating the root cause"
            )

        return suggestions

    def auto_classify_error(
        self, exception: Exception, message: str = None
    ) -> tuple[ErrorCategory, ErrorSeverity]:
        """Automatically classify error based on exception type and message"""
        message = message or str(exception).lower()

        # File I/O errors
        if isinstance(exception, (FileNotFoundError, PermissionError, OSError)):
            return ErrorCategory.FILE_IO, ErrorSeverity.HIGH

        # Network errors
        if isinstance(exception, (ConnectionError, TimeoutError)):
            return ErrorCategory.NETWORK, ErrorSeverity.MEDIUM

        # API errors
        if (
            "api" in message
            or "401" in message
            or "403" in message
            or "rate limit" in message
        ):
            return ErrorCategory.API, ErrorSeverity.HIGH

        # Data errors
        if (
            "data" in message
            or "csv" in message
            or "json" in message
            or "parse" in message
        ):
            return ErrorCategory.DATA, ErrorSeverity.MEDIUM

        # Model errors
        if "model" in message or "pickle" in message or "joblib" in message:
            return ErrorCategory.MODEL, ErrorSeverity.HIGH

        # Syntax errors
        if isinstance(exception, SyntaxError):
            return ErrorCategory.SYNTAX, ErrorSeverity.CRITICAL

        # Validation errors
        if isinstance(exception, (ValueError, TypeError)):
            return ErrorCategory.VALIDATION, ErrorSeverity.MEDIUM

        return ErrorCategory.UNKNOWN, ErrorSeverity.MEDIUM


def safe_execute(
    error_handler: ErrorHandler,
    func: Callable,
    *args,
    context: Optional[Dict[str, Any]] = None,
    recoverable: bool = False,
    recovery_action: Optional[str] = None,
    **kwargs,
):
    """
    Safely execute a function with comprehensive error handling

    Args:
        error_handler: ErrorHandler instance
        func: Function to execute
        *args: Function arguments
        context: Additional context for error handling
        recoverable: Whether errors are recoverable
        recovery_action: Recovery action description
        **kwargs: Function keyword arguments

    Returns:
        Function result or None if error occurred
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        # Auto-classify error
        category, severity = error_handler.auto_classify_error(e)

        # Handle error
        error_handler.handle_error(
            message=f"Error executing {func.__name__}: {str(e)}",
            severity=severity,
            category=category,
            exception=e,
            context=context
            or {"function": func.__name__, "args": args, "kwargs": kwargs},
            recoverable=recoverable,
            recovery_action=recovery_action,
        )
        return None


def with_error_handling(
    error_handler: ErrorHandler,
    category: ErrorCategory = ErrorCategory.UNKNOWN,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    recoverable: bool = False,
    recovery_action: Optional[str] = None,
    suggestions: Optional[List[str]] = None,
):
    """
    Decorator for adding comprehensive error handling to functions
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                auto_category, auto_severity = error_handler.auto_classify_error(e)

                # Use decorator category/severity if specified, otherwise use auto-classified
                final_category = (
                    category if category != ErrorCategory.UNKNOWN else auto_category
                )
                final_severity = (
                    severity if severity != ErrorSeverity.MEDIUM else auto_severity
                )

                error_handler.handle_error(
                    message=f"Error in {func.__name__}: {str(e)}",
                    severity=final_severity,
                    category=final_category,
                    exception=e,
                    context={"function": func.__name__, "module": func.__module__},
                    suggestions=suggestions,
                    recoverable=recoverable,
                    recovery_action=recovery_action,
                    reraise=True,  # Reraise for decorator usage
                )

        return wrapper

    return decorator


# Global error handler instance
_global_error_handler = None


def get_error_handler() -> ErrorHandler:
    """Get or create global error handler instance"""
    global _global_error_handler
    if _global_error_handler is None:
        _global_error_handler = ErrorHandler()
    return _global_error_handler


def handle_error(
    message: str,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    category: ErrorCategory = ErrorCategory.UNKNOWN,
    exception: Optional[Exception] = None,
    context: Optional[Dict[str, Any]] = None,
    suggestions: Optional[List[str]] = None,
    recoverable: bool = False,
    recovery_action: Optional[str] = None,
    reraise: bool = False,
) -> Optional[EnhancedError]:
    """Convenience function for handling errors with global handler"""
    return get_error_handler().handle_error(
        message=message,
        severity=severity,
        category=category,
        exception=exception,
        context=context,
        suggestions=suggestions,
        recoverable=recoverable,
        recovery_action=recovery_action,
        reraise=reraise,
    )
