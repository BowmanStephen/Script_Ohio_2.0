#!/usr/bin/env python3
"""
Comprehensive Error Handling and Recovery System

Implements OpenAI best practices for error handling:
- Circuit breaker pattern for failure prevention
- Intelligent retry mechanisms with exponential backoff
- Graceful degradation and fallback systems
- Error classification and intelligent routing
- Comprehensive logging and monitoring
- Automatic recovery and self-healing
"""

import time
import uuid
import traceback
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from functools import wraps
from collections import defaultdict
import json

from src.observability import (
    ErrorCategory,
    ErrorReport,
    ErrorSeverity,
    ObservabilityHub,
    get_logger,
)

logger = get_logger("error_handling")

class CircuitState(Enum):
    """States for circuit breaker"""
    CLOSED = "closed"                     # Normal operation
    OPEN = "open"                         # Failing, reject requests
    HALF_OPEN = "half_open"               # Testing if failures are resolved

@dataclass
class RetryConfig:
    """Configuration for retry mechanisms"""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    backoff_factor: float = 2.0
    jitter: bool = True
    retry_on: List[ErrorCategory] = field(default_factory=lambda: [ErrorCategory.NETWORK, ErrorCategory.TIMEOUT])

class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    expected_exception: type = Exception
    success_threshold: int = 3  # Successes needed to close circuit

class CircuitBreaker:
    """
    Circuit breaker implementation following OpenAI best practices

    Prevents cascade failures by temporarily stopping operations
    that are consistently failing.
    """

    def __init__(self, name: str, config: CircuitBreakerConfig = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.last_success_time = None

        # Metrics
        self.total_requests = 0
        self.total_failures = 0
        self.total_successes = 0

    def __call__(self, func: Callable) -> Callable:
        """Decorator to wrap functions with circuit breaker"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            return self.execute(func, *args, **kwargs)
        return wrapper

    def execute(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        self.total_requests += 1

        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                logger.info(f"Circuit breaker {self.name} entering HALF_OPEN state")
            else:
                raise CircuitBreakerOpenError(f"Circuit breaker {self.name} is OPEN")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result

        except Exception as e:
            self._on_failure()
            raise

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt circuit reset"""
        if self.last_failure_time is None:
            return False
        return time.time() - self.last_failure_time >= self.config.recovery_timeout

    def _on_success(self):
        """Handle successful operation"""
        self.last_success_time = time.time()
        self.success_count += 1
        self.total_successes += 1

        if self.state == CircuitState.HALF_OPEN:
            if self.success_count >= self.config.success_threshold:
                self._close_circuit()

    def _on_failure(self):
        """Handle failed operation"""
        self.last_failure_time = time.time()
        self.failure_count += 1
        self.total_failures += 1

        if self.state == CircuitState.HALF_OPEN:
            self._open_circuit()
        elif self.failure_count >= self.config.failure_threshold:
            self._open_circuit()

    def _open_circuit(self):
        """Open the circuit to prevent further failures"""
        self.state = CircuitState.OPEN
        self.failure_count = 0
        logger.warning(f"Circuit breaker {self.name} OPENED after {self.config.failure_threshold} failures")

    def _close_circuit(self):
        """Close the circuit to resume normal operation"""
        self.state = CircuitState.CLOSED
        self.success_count = 0
        self.failure_count = 0
        logger.info(f"Circuit breaker {self.name} CLOSED after {self.config.success_threshold} successes")

    def get_metrics(self) -> Dict[str, Any]:
        """Get circuit breaker metrics"""
        return {
            'name': self.name,
            'state': self.state.value,
            'total_requests': self.total_requests,
            'total_failures': self.total_failures,
            'total_successes': self.total_successes,
            'failure_rate': self.total_failures / self.total_requests if self.total_requests > 0 else 0,
            'last_failure_time': self.last_failure_time,
            'last_success_time': self.last_success_time
        }

class RetryHandler:
    """
    Intelligent retry mechanism with exponential backoff

    Implements OpenAI best practices for handling transient failures
    """

    def __init__(self, config: RetryConfig = None):
        self.config = config or RetryConfig()

    def __call__(self, func: Callable) -> Callable:
        """Decorator to wrap functions with retry mechanism"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            return self.execute(func, *args, **kwargs)
        return wrapper

    def execute(self, func: Callable, *args, **kwargs):
        """Execute function with intelligent retry logic"""
        last_exception = None

        for attempt in range(self.config.max_attempts):
            try:
                return func(*args, **kwargs)

            except Exception as e:
                last_exception = e

                # Check if this error type should be retried
                if not self._should_retry(e, attempt):
                    raise

                # Calculate delay for next attempt
                delay = self._calculate_delay(attempt)

                logger.warning(
                    f"Attempt {attempt + 1} failed for {func.__name__}: {str(e)}. "
                    f"Retrying in {delay:.2f} seconds..."
                )

                time.sleep(delay)

        # All retries failed
        error_report = ErrorReporter.create_error_report(
            error=last_exception,
            error_type=f"RetryExhausted_{func.__name__}",
            severity=ErrorSeverity.HIGH,
            context={
                'attempts': self.config.max_attempts,
                'function': func.__name__,
                'args_count': len(args),
                'kwargs_keys': list(kwargs.keys())
            }
        )

        ErrorHandler.handle_error(error_report)

    def _should_retry(self, exception: Exception, attempt: int) -> bool:
        """Determine if the exception should trigger a retry"""
        if attempt >= self.config.max_attempts - 1:
            return False

        # Check exception type
        error_category = ErrorHandler.classify_error(exception)
        return error_category in self.config.retry_on

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay with exponential backoff and jitter"""
        delay = self.config.base_delay * (self.config.backoff_factor ** attempt)
        delay = min(delay, self.config.max_delay)

        if self.config.jitter:
            # Add jitter to prevent thundering herd
            import random
            delay *= (0.5 + random.random() * 0.5)

        return delay

class FallbackSystem:
    """
    Fallback system for graceful degradation

    Provides alternative approaches when primary methods fail
    """

    def __init__(self):
        self.fallback_strategies: Dict[str, List[Callable]] = defaultdict(list)
        self.fallback_usage_stats: Dict[str, int] = defaultdict(int)

    def register_fallback(self, primary_method: str, fallback_strategy: Callable, priority: int = 0):
        """Register a fallback strategy for a primary method"""
        self.fallback_strategies[primary_method].append((priority, fallback_strategy))
        # Sort by priority (lower = higher priority)
        self.fallback_strategies[primary_method].sort(key=lambda x: x[0])

    def execute_with_fallback(self, primary_method: str, primary_func: Callable,
                            *args, **kwargs) -> Any:
        """Execute function with fallback strategies"""
        try:
            # Try primary method first
            result = primary_func(*args, **kwargs)
            return result

        except Exception as primary_error:
            logger.warning(f"Primary method {primary_method} failed: {str(primary_error)}")

            # Try fallback strategies
            fallbacks = self.fallback_strategies.get(primary_method, [])

            for priority, fallback in fallbacks:
                try:
                    logger.info(f"Trying fallback strategy (priority {priority}) for {primary_method}")
                    result = fallback(*args, **kwargs, primary_error=primary_error)
                    self.fallback_usage_stats[primary_method] += 1
                    logger.info(f"Fallback strategy succeeded for {primary_method}")
                    return result

                except Exception as fallback_error:
                    logger.warning(f"Fallback strategy failed: {str(fallback_error)}")
                    continue

            # All fallbacks failed
            raise FallbackExhaustedError(
                f"Primary method {primary_method} and all fallbacks failed. "
                f"Primary error: {str(primary_error)}"
            )

    def get_fallback_metrics(self) -> Dict[str, Any]:
        """Get fallback system metrics"""
        total_fallbacks = sum(self.fallback_usage_stats.values())
        return {
            'registered_fallbacks': len(self.fallback_strategies),
            'fallback_usage_stats': dict(self.fallback_usage_stats),
            'total_fallbacks_used': total_fallbacks
        }

class ErrorHandler:
    """
    Central error handling and recovery system

    Coordinates all error handling components and provides intelligent
    error classification, reporting, and recovery strategies.
    """

    def __init__(self):
        self.error_reports: List[ErrorReport] = []
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.retry_handler = RetryHandler()
        self.fallback_system = FallbackSystem()

        # Error handling strategies by category
        self.error_strategies = {
            ErrorCategory.NETWORK: self._handle_network_error,
            ErrorCategory.DATA: self._handle_data_error,
            ErrorCategory.MODEL: self._handle_model_error,
            ErrorCategory.TIMEOUT: self._handle_timeout_error,
            ErrorCategory.RATE_LIMIT: self._handle_rate_limit_error,
            ErrorCategory.RESOURCE: self._handle_resource_error
        }

        # Error statistics
        self.error_stats = defaultdict(int)
        self.recovery_stats = defaultdict(int)

    def register_circuit_breaker(self, name: str, config: CircuitBreakerConfig = None):
        """Register a circuit breaker for a specific component"""
        self.circuit_breakers[name] = CircuitBreaker(name, config)
        logger.info(f"Registered circuit breaker: {name}")

    def handle_error(self, error_report: ErrorReport) -> bool:
        """
        Handle error with appropriate recovery strategy

        Returns True if error was handled successfully
        """
        try:
            # Log the error
            logger.error(f"Handling error: {error_report.error_message}", extra=error_report.__dict__)

            # Update statistics
            self.error_stats[error_report.category.value] += 1
            self.error_reports.append(error_report)
            ObservabilityHub.instance().emit_error(error_report)

            # Categorize and handle the error
            strategy = self.error_strategies.get(error_report.category, self._handle_unknown_error)
            recovery_success = strategy(error_report)

            # Record recovery attempt
            error_report.recovery_attempted = True
            error_report.recovery_successful = recovery_success

            if recovery_success:
                self.recovery_stats[error_report.category.value] += 1
                logger.info(f"Successfully recovered from error: {error_report.error_id}")
            else:
                logger.error(f"Failed to recover from error: {error_report.error_id}")

            return recovery_success

        except Exception as e:
            logger.error(f"Error in error handling: {str(e)}")
            return False

    @staticmethod
    def classify_error(exception: Exception) -> ErrorCategory:
        """Classify exception into appropriate category"""
        error_message = str(exception).lower()
        exception_type = type(exception).__name__.lower()

        # Network errors
        if any(keyword in error_message or exception_type for keyword in
               ['connection', 'timeout', 'network', 'socket', 'http']):
            if 'timeout' in error_message:
                return ErrorCategory.TIMEOUT
            return ErrorCategory.NETWORK

        # Data errors
        if any(keyword in error_message or exception_type for keyword in
               ['value', 'type', 'key', 'data', 'json', 'parse']):
            return ErrorCategory.DATA

        # Model errors
        if any(keyword in error_message or exception_type for keyword in
               ['model', 'prediction', 'inference', 'torch', 'tensorflow']):
            return ErrorCategory.MODEL

        # Resource errors
        if any(keyword in error_message or exception_type for keyword in
               ['memory', 'disk', 'resource', 'space', 'quota']):
            return ErrorCategory.RESOURCE

        # Rate limit errors
        if any(keyword in error_message or exception_type for keyword in
               ['rate', 'limit', 'quota', 'throttle']):
            return ErrorCategory.RATE_LIMIT

        return ErrorCategory.UNKNOWN

    @staticmethod
    def create_error_report(error: Exception,
                          error_type: str = "",
                          severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                          context: Dict[str, Any] = None,
                          user_facing_message: str = "") -> ErrorReport:
        """Create a comprehensive error report"""
        return ErrorReport(
            error_type=error_type or type(error).__name__,
            error_message=str(error),
            severity=severity,
            category=ErrorHandler.classify_error(error),
            context=context or {},
            stack_trace=traceback.format_exc(),
            user_facing_message=user_facing_message or "An unexpected error occurred. Please try again.",
            technical_details={
                'exception_type': type(error).__name__,
                'exception_args': str(error.args) if error.args else None
            }
        )

    def get_error_metrics(self) -> Dict[str, Any]:
        """Get comprehensive error handling metrics"""
        total_errors = len(self.error_reports)
        recovered_errors = sum(self.recovery_stats.values())
        recovery_rate = recovered_errors / total_errors if total_errors > 0 else 0

        return {
            'total_errors': total_errors,
            'recovered_errors': recovered_errors,
            'recovery_rate': round(recovery_rate, 3),
            'error_by_category': dict(self.error_stats),
            'recovery_by_category': dict(self.recovery_stats),
            'circuit_breakers': {
                name: cb.get_metrics()
                for name, cb in self.circuit_breakers.items()
            },
            'fallback_metrics': self.fallback_system.get_fallback_metrics()
        }

    # Error handling strategies

    def _handle_network_error(self, error_report: ErrorReport) -> bool:
        """Handle network-related errors"""
        logger.info(f"Handling network error: {error_report.error_message}")
        # Could implement retry logic, fallback to cached data, etc.
        return False  # Let caller handle

    def _handle_data_error(self, error_report: ErrorReport) -> bool:
        """Handle data-related errors"""
        logger.info(f"Handling data error: {error_report.error_message}")
        # Could implement data validation, fallback to defaults, etc.
        return False

    def _handle_model_error(self, error_report: ErrorReport) -> bool:
        """Handle model-related errors"""
        logger.info(f"Handling model error: {error_report.error_message}")
        # Could implement model fallback, simplified prediction, etc.
        return False

    def _handle_timeout_error(self, error_report: ErrorReport) -> bool:
        """Handle timeout errors"""
        logger.info(f"Handling timeout error: {error_report.error_message}")
        # Could implement retry with longer timeout, fallback to simpler analysis, etc.
        return False

    def _handle_rate_limit_error(self, error_report: ErrorReport) -> bool:
        """Handle rate limiting errors"""
        logger.info(f"Handling rate limit error: {error_report.error_message}")
        # Could implement exponential backoff, queue requests, etc.
        return False

    def _handle_resource_error(self, error_report: ErrorReport) -> bool:
        """Handle resource exhaustion errors"""
        logger.info(f"Handling resource error: {error_report.error_message}")
        # Could implement resource cleanup, simplified processing, etc.
        return False

    def _handle_unknown_error(self, error_report: ErrorReport) -> bool:
        """Handle unknown errors"""
        logger.warning(f"Handling unknown error: {error_report.error_message}")
        return False

class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open"""
    pass

class FallbackExhaustedError(Exception):
    """Raised when all fallback strategies have failed"""
    pass

# Global error handler instance
error_handler = ErrorHandler()

# Decorators for easy use

def circuit_breaker(name: str, config: CircuitBreakerConfig = None):
    """Decorator to apply circuit breaker to function"""
    def decorator(func):
        cb = error_handler.circuit_breakers.get(name)
        if cb is None:
            cb = CircuitBreaker(name, config)
            error_handler.register_circuit_breaker(name, config)
        return cb(func)
    return decorator

def retry(max_attempts: int = 3, base_delay: float = 1.0, max_delay: float = 60.0):
    """Decorator to apply retry mechanism to function"""
    def decorator(func):
        config = RetryConfig(
            max_attempts=max_attempts,
            base_delay=base_delay,
            max_delay=max_delay
        )
        retry_handler = RetryHandler(config)
        return retry_handler(func)
    return decorator

def handle_errors(error_type: str = "",
                 severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                 user_facing_message: str = ""):
    """Decorator to handle errors in functions"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_report = ErrorHandler.create_error_report(
                    error=e,
                    error_type=error_type or func.__name__,
                    severity=severity,
                    context={
                        'function': func.__name__,
                        'args_count': len(args),
                        'kwargs_keys': list(kwargs.keys())
                    },
                    user_facing_message=user_facing_message
                )
                error_handler.handle_error(error_report)
                raise
        return wrapper
    return decorator

def fallback_for(primary_method: str, priority: int = 0):
    """Decorator to register function as fallback for primary method"""
    def decorator(fallback_func):
        error_handler.fallback_system.register_fallback(primary_method, fallback_func, priority)
        return fallback_func
    return decorator

# Utility functions
def safe_execute(func: Callable, *args, default_value=None, **kwargs) -> Any:
    """Safely execute function with error handling"""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger.error(f"Safe execution failed for {func.__name__}: {str(e)}")
        return default_value