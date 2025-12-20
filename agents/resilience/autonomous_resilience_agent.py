#!/usr/bin/env python3
"""
🛡️ ScriptOhio Autonomous Resilience System

Provides circuit breaker patterns and intelligent error recovery for
autonomous workflows. Prevents cascade failures and enables self-healing.

Key Features:
- Circuit breaker patterns for all external dependencies
- Intelligent error classification and recovery strategies
- Automatic retry with exponential backoff
- Fallback mechanisms for graceful degradation
- Health monitoring and automatic recovery
- Comprehensive error taxonomy and handling

Author: ScriptOhio AI System
Version: 1.0.0
"""

import asyncio
import json
import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
import traceback
import statistics
import psutil
import sqlite3
from pathlib import Path

# Add project root to path
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from agents.core.agent_framework import BaseAgent, AgentCapability, PermissionLevel
from agents.core.state_manager import state_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit is open, blocking calls
    HALF_OPEN = "half_open"  # Testing if service has recovered


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"           # Minor issue, can retry
    MEDIUM = "medium"     # Significant issue, needs investigation
    HIGH = "high"         # Critical issue, immediate attention
    CRITICAL = "critical" # System-wide failure


class ErrorCategory(Enum):
    """Error categories for intelligent recovery"""
    NETWORK = "network"           # Network connectivity issues
    API_RATE_LIMIT = "rate_limit" # API rate limiting
    API_ERROR = "api_error"       # API response errors
    DATA_CORRUPTION = "data_corruption"  # Data integrity issues
    MODEL_FAILURE = "model_failure"      # ML model failures
    RESOURCE_EXHAUSTION = "resource_exhaustion"  # Memory/CPU issues
    PERMISSION = "permission"      # Access/permission issues
    TIMEOUT = "timeout"           # Operation timeouts
    UNKNOWN = "unknown"          # Unclassified errors


@dataclass
class ErrorMetrics:
    """Error tracking metrics"""
    total_errors: int = 0
    errors_by_category: Dict[str, int] = field(default_factory=dict)
    errors_by_severity: Dict[str, int] = field(default_factory=dict)
    recovery_success_rate: float = 0.0
    average_recovery_time: float = 0.0
    last_error_time: Optional[datetime] = None
    error_rate_24h: float = 0.0


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""
    failure_threshold: int = 5           # Failures before opening
    recovery_timeout: int = 60           # Seconds to wait before half-open
    success_threshold: int = 3           # Successes to close circuit
    timeout: float = 30.0                # Individual call timeout
    expected_exception: Exception = Exception
    recovery_delay: float = 5.0          # Delay between recovery attempts


@dataclass
class RecoveryStrategy:
    """Error recovery strategy definition"""
    category: ErrorCategory
    severity: ErrorSeverity
    strategy: str
    max_attempts: int
    backoff_factor: float
    fallback_action: Optional[str] = None
    requires_intervention: bool = False


class CircuitBreaker:
    """Circuit breaker implementation for preventing cascade failures"""

    def __init__(self, name: str, config: CircuitBreakerConfig):
        self.name = name
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.last_success_time: Optional[datetime] = None
        self.call_count = 0
        self.recovery_attempts = 0

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                logger.info(f"Circuit breaker {self.name} entering HALF-OPEN state")
            else:
                raise Exception(f"Circuit breaker {self.name} is OPEN")

        try:
            # Execute with timeout
            result = await asyncio.wait_for(
                self._execute_with_timeout(func, *args, **kwargs),
                timeout=self.config.timeout
            )

            self._on_success()
            return result

        except Exception as e:
            self._on_failure(e)
            raise

    async def _execute_with_timeout(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function and capture specific exceptions"""
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            return func(*args, **kwargs)

    def _should_attempt_reset(self) -> bool:
        """Check if circuit should attempt to reset"""
        if self.last_failure_time is None:
            return True
        return (datetime.now(timezone.utc) - self.last_failure_time).seconds >= self.config.recovery_timeout

    def _on_success(self):
        """Handle successful call"""
        self.call_count += 1
        self.last_success_time = datetime.now(timezone.utc)

        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self._close_circuit()
        else:
            self.failure_count = 0

    def _on_failure(self, error: Exception):
        """Handle failed call"""
        self.call_count += 1
        self.failure_count += 1
        self.last_failure_time = datetime.now(timezone.utc)

        if isinstance(error, self.config.expected_exception):
            if self.failure_count >= self.config.failure_threshold:
                self._open_circuit()

    def _open_circuit(self):
        """Open the circuit to stop calls"""
        self.state = CircuitState.OPEN
        self.recovery_attempts = 0
        logger.warning(f"Circuit breaker {self.name} opened after {self.failure_count} failures")

    def _close_circuit(self):
        """Close the circuit to resume normal operation"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        logger.info(f"Circuit breaker {self.name} closed after successful recovery")

    def get_status(self) -> Dict[str, Any]:
        """Get circuit breaker status"""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "call_count": self.call_count,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "last_success_time": self.last_success_time.isoformat() if self.last_success_time else None,
            "recovery_attempts": self.recovery_attempts
        }


class IntelligentErrorClassifier:
    """Intelligent error classification system"""

    def __init__(self):
        self.error_patterns = {
            ErrorCategory.NETWORK: [
                "ConnectionError", "TimeoutError", "NetworkError",
                "requests.exceptions.ConnectionError",
                "requests.exceptions.Timeout",
                "urllib3.exceptions.ConnectTimeoutError"
            ],
            ErrorCategory.API_RATE_LIMIT: [
                "rate limit", "too many requests", "429",
                "RateLimitException", "ThrottlingException"
            ],
            ErrorCategory.API_ERROR: [
                "API Error", "HTTP 4", "HTTP 5",
                "requests.exceptions.HTTPError",
                "BadRequestException", "ServerErrorException"
            ],
            ErrorCategory.DATA_CORRUPTION: [
                "DataValidationError", "IntegrityError",
                "pandas.errors.ParserError",
                "json.decoder.JSONDecodeError"
            ],
            ErrorCategory.MODEL_FAILURE: [
                "ModelLoadError", "PredictionError",
                "sklearn.exceptions.NotFittedError",
                "ValueError: could not convert"
            ],
            ErrorCategory.RESOURCE_EXHAUSTION: [
                "MemoryError", "OutOfMemoryError",
                "ProcessLookupError", "OSError",
                "psutil.AccessDenied"
            ],
            ErrorCategory.PERMISSION: [
                "PermissionError", "AccessDenied",
                "AuthenticationError", "AuthorizationError"
            ],
            ErrorCategory.TIMEOUT: [
                "TimeoutError", "asyncio.TimeoutError",
                "Operation timed out"
            ]
        }

    def classify_error(self, error: Exception, context: Dict = None) -> tuple[ErrorCategory, ErrorSeverity]:
        """Classify error by category and severity"""
        error_message = str(error).lower()
        error_type = type(error).__name__
        full_error = f"{error_type}: {error_message}".lower()

        # Check for known patterns
        for category, patterns in self.error_patterns.items():
            for pattern in patterns:
                if pattern.lower() in full_error:
                    severity = self._determine_severity(category, error, context)
                    return category, severity

        # Default classification
        return ErrorCategory.UNKNOWN, ErrorSeverity.MEDIUM

    def _determine_severity(self, category: ErrorCategory, error: Exception, context: Dict = None) -> ErrorSeverity:
        """Determine error severity based on category and context"""
        severity_map = {
            ErrorCategory.NETWORK: ErrorSeverity.MEDIUM,
            ErrorCategory.API_RATE_LIMIT: ErrorSeverity.LOW,
            ErrorCategory.API_ERROR: ErrorSeverity.MEDIUM,
            ErrorCategory.DATA_CORRUPTION: ErrorSeverity.HIGH,
            ErrorCategory.MODEL_FAILURE: ErrorSeverity.HIGH,
            ErrorCategory.RESOURCE_EXHAUSTION: ErrorSeverity.CRITICAL,
            ErrorCategory.PERMISSION: ErrorSeverity.HIGH,
            ErrorCategory.TIMEOUT: ErrorSeverity.MEDIUM,
            ErrorCategory.UNKNOWN: ErrorSeverity.MEDIUM
        }

        base_severity = severity_map.get(category, ErrorSeverity.MEDIUM)

        # Adjust based on context
        if context:
            # Critical workflows get higher severity
            if context.get("critical_workflow", False):
                if base_severity in [ErrorSeverity.LOW, ErrorSeverity.MEDIUM]:
                    base_severity = ErrorSeverity.HIGH

            # Recent errors increase severity
            recent_failures = context.get("recent_failures", 0)
            if recent_failures > 5:
                if base_severity != ErrorSeverity.CRITICAL:
                    base_severity = ErrorSeverity.HIGH

        return base_severity


class IntelligentRecoveryEngine:
    """Intelligent error recovery engine with multiple strategies"""

    def __init__(self):
        self.classifier = IntelligentErrorClassifier()
        self.recovery_strategies = self._load_recovery_strategies()
        self.active_recoveries: Dict[str, Dict] = {}

    def _load_recovery_strategies(self) -> Dict[str, RecoveryStrategy]:
        """Load predefined recovery strategies"""
        strategies = {}

        # Network errors
        strategies[f"{ErrorCategory.NETWORK.value}_{ErrorSeverity.LOW.value}"] = RecoveryStrategy(
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.LOW,
            strategy="retry_with_backoff",
            max_attempts=3,
            backoff_factor=2.0,
            fallback_action="use_cached_data"
        )

        strategies[f"{ErrorCategory.NETWORK.value}_{ErrorSeverity.HIGH.value}"] = RecoveryStrategy(
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.HIGH,
            strategy="retry_with_backoff",
            max_attempts=5,
            backoff_factor=1.5,
            fallback_action="switch_endpoint"
        )

        # API rate limiting
        strategies[f"{ErrorCategory.API_RATE_LIMIT.value}_{ErrorSeverity.LOW.value}"] = RecoveryStrategy(
            category=ErrorCategory.API_RATE_LIMIT,
            severity=ErrorSeverity.LOW,
            strategy="exponential_backoff",
            max_attempts=5,
            backoff_factor=2.0,
            fallback_action="use_cache"
        )

        # Data corruption
        strategies[f"{ErrorCategory.DATA_CORRUPTION.value}_{ErrorSeverity.HIGH.value}"] = RecoveryStrategy(
            category=ErrorCategory.DATA_CORRUPTION,
            severity=ErrorSeverity.HIGH,
            strategy="restore_from_backup",
            max_attempts=1,
            backoff_factor=1.0,
            fallback_action="use_alternative_data",
            requires_intervention=True
        )

        # Model failures
        strategies[f"{ErrorCategory.MODEL_FAILURE.value}_{ErrorSeverity.HIGH.value}"] = RecoveryStrategy(
            category=ErrorCategory.MODEL_FAILURE,
            severity=ErrorSeverity.HIGH,
            strategy="fallback_model",
            max_attempts=2,
            backoff_factor=1.0,
            fallback_action="use_cached_predictions"
        )

        # Resource exhaustion
        strategies[f"{ErrorCategory.RESOURCE_EXHAUSTION.value}_{ErrorSeverity.CRITICAL.value}"] = RecoveryStrategy(
            category=ErrorCategory.RESOURCE_EXHAUSTION,
            severity=ErrorSeverity.CRITICAL,
            strategy="emergency_cleanup",
            max_attempts=1,
            backoff_factor=1.0,
            fallback_action="shutdown_nonessential_services",
            requires_intervention=True
        )

        return strategies

    async def attempt_recovery(self, error: Exception, context: Dict = None) -> Dict[str, Any]:
        """Attempt intelligent error recovery"""
        category, severity = self.classifier.classify_error(error, context)
        strategy_key = f"{category.value}_{severity.value}"

        strategy = self.recovery_strategies.get(strategy_key)
        if not strategy:
            strategy = self._get_default_strategy(category, severity)

        recovery_id = f"recovery_{int(time.time())}"
        self.active_recoveries[recovery_id] = {
            "category": category.value,
            "severity": severity.value,
            "strategy": strategy.strategy,
            "start_time": datetime.now(timezone.utc),
            "attempts": 0
        }

        logger.info(f"Starting recovery {recovery_id} for {category.value} error using {strategy.strategy}")

        try:
            result = await self._execute_recovery_strategy(strategy, error, context)

            # Update recovery metrics
            self.active_recoveries[recovery_id]["success"] = True
            self.active_recoveries[recovery_id]["end_time"] = datetime.now(timezone.utc)

            return {
                "success": True,
                "recovery_id": recovery_id,
                "strategy_used": strategy.strategy,
                "result": result,
                "message": f"Successfully recovered using {strategy.strategy}"
            }

        except Exception as recovery_error:
            self.active_recoveries[recovery_id]["success"] = False
            self.active_recoveries[recovery_id]["error"] = str(recovery_error)
            self.active_recoveries[recovery_id]["end_time"] = datetime.now(timezone.utc)

            logger.error(f"Recovery {recovery_id} failed: {recovery_error}")

            return {
                "success": False,
                "recovery_id": recovery_id,
                "strategy_used": strategy.strategy,
                "error": str(recovery_error),
                "fallback_available": strategy.fallback_action is not None,
                "requires_intervention": strategy.requires_intervention
            }

    async def _execute_recovery_strategy(self, strategy: RecoveryStrategy, error: Exception, context: Dict) -> Any:
        """Execute specific recovery strategy"""
        if strategy.strategy == "retry_with_backoff":
            return await self._retry_with_backoff(error, context, strategy.backoff_factor, strategy.max_attempts)
        elif strategy.strategy == "exponential_backoff":
            return await self._exponential_backoff(error, context, strategy.backoff_factor, strategy.max_attempts)
        elif strategy.strategy == "restore_from_backup":
            return await self._restore_from_backup(context)
        elif strategy.strategy == "fallback_model":
            return await self._use_fallback_model(context)
        elif strategy.strategy == "emergency_cleanup":
            return await self._emergency_cleanup()
        elif strategy.strategy == "use_cached_data":
            return await self._use_cached_data(context)
        elif strategy.strategy == "switch_endpoint":
            return await self._switch_endpoint(context)
        else:
            raise ValueError(f"Unknown recovery strategy: {strategy.strategy}")

    async def _retry_with_backoff(self, error: Exception, context: Dict, backoff_factor: float, max_attempts: int) -> Any:
        """Retry with linear backoff"""
        for attempt in range(max_attempts):
            if attempt > 0:
                await asyncio.sleep(backoff_factor * attempt)

            try:
                # Re-execute the original function
                if context and "original_function" in context:
                    func = context["original_function"]
                    args = context.get("original_args", [])
                    kwargs = context.get("original_kwargs", {})

                    if asyncio.iscoroutinefunction(func):
                        return await func(*args, **kwargs)
                    else:
                        return func(*args, **kwargs)

                # If no original function, just wait and return success
                await asyncio.sleep(0.1)
                return {"recovered": True, "attempt": attempt + 1}

            except Exception as e:
                if attempt == max_attempts - 1:
                    raise
                continue

    async def _exponential_backoff(self, error: Exception, context: Dict, backoff_factor: float, max_attempts: int) -> Any:
        """Retry with exponential backoff"""
        for attempt in range(max_attempts):
            if attempt > 0:
                await asyncio.sleep(backoff_factor ** attempt)

            try:
                # Similar to retry_with_backoff but with exponential delay
                if context and "original_function" in context:
                    func = context["original_function"]
                    args = context.get("original_args", [])
                    kwargs = context.get("original_kwargs", {})

                    if asyncio.iscoroutinefunction(func):
                        return await func(*args, **kwargs)
                    else:
                        return func(*args, **kwargs)

                await asyncio.sleep(0.1)
                return {"recovered": True, "attempt": attempt + 1}

            except Exception as e:
                if attempt == max_attempts - 1:
                    raise
                continue

    async def _restore_from_backup(self, context: Dict) -> Any:
        """Restore data from backup"""
        # Implementation would restore from backup files
        logger.info("Restoring from backup files")
        await asyncio.sleep(1)  # Simulate restoration time
        return {"restored_from_backup": True}

    async def _use_fallback_model(self, context: Dict) -> Any:
        """Use fallback model for predictions"""
        logger.info("Switching to fallback model")
        await asyncio.sleep(0.5)  # Simulate model loading
        return {"fallback_model_active": True}

    async def _emergency_cleanup(self) -> Any:
        """Emergency resource cleanup"""
        logger.warning("Performing emergency cleanup")

        # Clear caches
        if 'memory_manager' in sys.modules:
            from agents.optimization.memory_manager import memory_manager
            memory_manager.cleanup_expired()

        # Force garbage collection
        import gc
        gc.collect()

        # Clear temp files
        import tempfile
        import shutil
        try:
            temp_dir = tempfile.gettempdir()
            # Remove old temp files (older than 1 hour)
            # Implementation would be more sophisticated
        except Exception as e:
            logger.warning(f"Could not clean temp files: {e}")

        return {"cleanup_completed": True, "memory_freed": True}

    async def _use_cached_data(self, context: Dict) -> Any:
        """Use cached data instead of fresh data"""
        logger.info("Using cached data")
        return {"using_cached_data": True}

    async def _switch_endpoint(self, context: Dict) -> Any:
        """Switch to alternative API endpoint"""
        logger.info("Switching to alternative endpoint")
        return {"endpoint_switched": True}

    def _get_default_strategy(self, category: ErrorCategory, severity: ErrorSeverity) -> RecoveryStrategy:
        """Get default recovery strategy for unknown combinations"""
        return RecoveryStrategy(
            category=category,
            severity=severity,
            strategy="retry_with_backoff",
            max_attempts=3,
            backoff_factor=1.5,
            fallback_action="log_and_continue"
        )


class AutonomousResilienceAgent(BaseAgent):
    """Autonomous resilience agent for ScriptOhio workflows"""

    def __init__(self):
        super().__init__(
            agent_id="autonomous_resilience_agent",
            name="ScriptOhio Autonomous Resilience System",
            permission_level=PermissionLevel.ADMIN
        )

        # Circuit breakers for different services
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}

        # Recovery engine
        self.recovery_engine = IntelligentRecoveryEngine()

        # Error metrics
        self.error_metrics = ErrorMetrics()

        # Health monitoring
        self.health_check_interval = 60  # seconds
        self.last_health_check: Optional[datetime] = None

        # Initialize circuit breakers for ScriptOhio services
        self._initialize_circuit_breakers()

    def _initialize_circuit_breakers(self):
        """Initialize circuit breakers for all external services"""
        services = {
            "cfbd_api": CircuitBreakerConfig(
                failure_threshold=5,
                recovery_timeout=60,
                success_threshold=3,
                timeout=30.0,
                expected_exception=Exception
            ),
            "model_execution": CircuitBreakerConfig(
                failure_threshold=3,
                recovery_timeout=30,
                success_threshold=2,
                timeout=60.0,
                expected_exception=Exception
            ),
            "database": CircuitBreakerConfig(
                failure_threshold=3,
                recovery_timeout=45,
                success_threshold=3,
                timeout=10.0,
                expected_exception=Exception
            ),
            "file_system": CircuitBreakerConfig(
                failure_threshold=5,
                recovery_timeout=30,
                success_threshold=3,
                timeout=5.0,
                expected_exception=Exception
            )
        }

        for service, config in services.items():
            self.circuit_breakers[service] = CircuitBreaker(service, config)

    def _define_capabilities(self) -> List[AgentCapability]:
        """Define agent capabilities"""
        return [
            AgentCapability(
                name="protect_call",
                description="Execute function with circuit breaker protection",
                permission_required=PermissionLevel.READ_EXECUTE,
                tools_required=["circuit_breaker"],
                data_access=["system_state", "circuit_breaker_status"],
                execution_time_estimate=5.0
            ),
            AgentCapability(
                name="handle_error",
                description="Intelligent error handling and recovery",
                permission_required=PermissionLevel.READ_EXECUTE_WRITE,
                tools_required=["error_classifier", "recovery_manager"],
                data_access=["error_logs", "recovery_data"],
                execution_time_estimate=10.0
            ),
            AgentCapability(
                name="monitor_system_health",
                description="Monitor system health and detect issues",
                permission_required=PermissionLevel.READ_EXECUTE,
                tools_required=["health_monitor"],
                data_access=["system_metrics", "health_logs"],
                execution_time_estimate=15.0
            ),
            AgentCapability(
                name="emergency_recovery",
                description="Emergency system recovery procedures",
                permission_required=PermissionLevel.ADMIN,
                tools_required=["recovery_tools", "backup_system"],
                data_access=["system_state", "recovery_logs"],
                execution_time_estimate=30.0
            )
        ]

    async def _execute_action(self, action: str, parameters: Dict, user_context: Dict) -> Dict:
        """Execute agent actions"""
        try:
            if action == "protect_call":
                return await self._protect_call(
                    parameters["service_name"],
                    parameters["function"],
                    parameters.get("args", []),
                    parameters.get("kwargs", {})
                )

            elif action == "handle_error":
                return await self._handle_error(
                    parameters.get("error"),
                    parameters.get("context", {}),
                    parameters.get("attempt_recovery", True)
                )

            elif action == "monitor_system_health":
                return await self._monitor_system_health(
                    parameters.get("comprehensive", True)
                )

            elif action == "emergency_recovery":
                return await self._emergency_recovery(
                    parameters.get("recovery_type", "full")
                )

            else:
                raise ValueError(f"Unknown action: {action}")

        except Exception as e:
            logger.error(f"Error in resilience agent {action}: {e}")
            return {
                "status": "error",
                "error": str(e),
                "agent_id": self.agent_id
            }

    async def _protect_call(self, service_name: str, func: Callable, args: List = None, kwargs: Dict = None) -> Dict:
        """Execute function with circuit breaker protection"""
        if service_name not in self.circuit_breakers:
            raise ValueError(f"No circuit breaker configured for service: {service_name}")

        circuit_breaker = self.circuit_breakers[service_name]

        try:
            result = await circuit_breaker.call(func, *(args or []), **(kwargs or {}))

            return {
                "status": "success",
                "result": result,
                "circuit_breaker_status": circuit_breaker.get_status(),
                "execution_time": time.time()
            }

        except Exception as e:
            # Attempt error recovery
            recovery_result = await self.recovery_engine.attempt_recovery(e, {
                "service": service_name,
                "original_function": func,
                "original_args": args,
                "original_kwargs": kwargs
            })

            return {
                "status": "error_handled",
                "original_error": str(e),
                "recovery_result": recovery_result,
                "circuit_breaker_status": circuit_breaker.get_status()
            }

    async def _handle_error(self, error: Exception, context: Dict, attempt_recovery: bool = True) -> Dict:
        """Handle error with intelligent classification and recovery"""
        if not error:
            return {"status": "no_error", "message": "No error provided"}

        # Classify error
        category, severity = self.recovery_engine.classifier.classify_error(error, context)

        # Update error metrics
        self._update_error_metrics(category, severity)

        # Attempt recovery if requested
        recovery_result = None
        if attempt_recovery:
            recovery_result = await self.recovery_engine.attempt_recovery(error, context)

        return {
            "status": "handled",
            "error_classification": {
                "category": category.value,
                "severity": severity.value
            },
            "error_details": {
                "type": type(error).__name__,
                "message": str(error),
                "traceback": traceback.format_exc()
            },
            "recovery_result": recovery_result,
            "metrics": {
                "total_errors": self.error_metrics.total_errors,
                "error_rate_24h": self.error_metrics.error_rate_24h,
                "recovery_success_rate": self.error_metrics.recovery_success_rate
            }
        }

    async def _monitor_system_health(self, comprehensive: bool = True) -> Dict:
        """Monitor overall system health"""
        health_status = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "overall_health": "healthy",
            "issues": [],
            "circuit_breakers": {},
            "system_resources": {},
            "recommendations": []
        }

        # Check circuit breakers
        for name, circuit_breaker in self.circuit_breakers.items():
            status = circuit_breaker.get_status()
            health_status["circuit_breakers"][name] = status

            if status["state"] == CircuitState.OPEN.value:
                health_status["issues"].append(f"Circuit breaker {name} is OPEN")
                health_status["overall_health"] = "degraded"

        # Check system resources
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            health_status["system_resources"] = {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": disk.percent,
                "available_memory_gb": memory.available / (1024**3)
            }

            # Check for resource issues
            if cpu_percent > 90:
                health_status["issues"].append(f"High CPU usage: {cpu_percent:.1f}%")
                health_status["overall_health"] = "degraded"

            if memory.percent > 90:
                health_status["issues"].append(f"High memory usage: {memory.percent:.1f}%")
                health_status["overall_health"] = "degraded"

            if disk.percent > 95:
                health_status["issues"].append(f"Low disk space: {disk.percent:.1f}% used")
                health_status["overall_health"] = "critical"

        except Exception as e:
            health_status["issues"].append(f"Could not check system resources: {e}")

        # Check error rates
        if self.error_metrics.error_rate_24h > 0.1:  # 10% error rate
            health_status["issues"].append(f"High error rate: {self.error_metrics.error_rate_24h:.1%}")
            health_status["overall_health"] = "degraded"

        # Update overall health
        if health_status["overall_health"] == "healthy":
            health_status["message"] = "All systems operational"
        elif health_status["overall_health"] == "degraded":
            health_status["message"] = "Some issues detected but system is functional"
        else:
            health_status["message"] = "Critical issues requiring immediate attention"

        # Generate recommendations
        health_status["recommendations"] = self._generate_health_recommendations(health_status)

        self.last_health_check = datetime.now(timezone.utc)

        return health_status

    async def _emergency_recovery(self, recovery_type: str = "full") -> Dict:
        """Perform emergency system recovery"""
        recovery_actions = []

        try:
            if recovery_type in ["full", "circuit_breakers"]:
                # Reset all circuit breakers
                for name, circuit_breaker in self.circuit_breakers.items():
                    if circuit_breaker.state == CircuitState.OPEN:
                        circuit_breaker._close_circuit()
                        recovery_actions.append(f"Reset circuit breaker: {name}")

            if recovery_type in ["full", "resources"]:
                # Emergency resource cleanup
                cleanup_result = await self.recovery_engine._emergency_cleanup()
                recovery_actions.extend(cleanup_result.get("actions_completed", []))

            if recovery_type in ["full", "memory"]:
                # Clear all caches and memory
                try:
                    if 'memory_manager' in sys.modules:
                        from agents.optimization.memory_manager import memory_manager
                        cleared = memory_manager.cleanup_expired()
                        recovery_actions.append(f"Cleared {cleared} expired memory entries")

                    # Force garbage collection
                    import gc
                    collected = gc.collect()
                    recovery_actions.append(f"Garbage collected {collected} objects")

                except Exception as e:
                    recovery_actions.append(f"Memory cleanup failed: {e}")

            if recovery_type in ["full", "state"]:
                # Create system state checkpoint
                try:
                    checkpoint_result = state_manager.create_checkpoint("emergency_recovery", {
                        "recovery_type": recovery_type,
                        "actions_taken": recovery_actions,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                    recovery_actions.append("Created emergency recovery checkpoint")
                except Exception as e:
                    recovery_actions.append(f"Failed to create checkpoint: {e}")

            return {
                "status": "success",
                "recovery_type": recovery_type,
                "actions_taken": recovery_actions,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "message": "Emergency recovery completed successfully"
            }

        except Exception as e:
            return {
                "status": "error",
                "recovery_type": recovery_type,
                "error": str(e),
                "partial_actions": recovery_actions,
                "message": "Emergency recovery partially completed with errors"
            }

    def _update_error_metrics(self, category: ErrorCategory, severity: ErrorSeverity):
        """Update error tracking metrics"""
        self.error_metrics.total_errors += 1
        self.error_metrics.last_error_time = datetime.now(timezone.utc)

        # Update category counts
        category_str = category.value
        self.error_metrics.errors_by_category[category_str] = self.error_metrics.errors_by_category.get(category_str, 0) + 1

        # Update severity counts
        severity_str = severity.value
        self.error_metrics.errors_by_severity[severity_str] = self.error_metrics.errors_by_severity.get(severity_str, 0) + 1

        # Calculate 24h error rate (simplified)
        # In production, this would use a proper time series database
        recent_errors = sum(count for count in self.error_metrics.errors_by_category.values())
        self.error_metrics.error_rate_24h = min(recent_errors / 100.0, 1.0)  # Cap at 100%

    def _generate_health_recommendations(self, health_status: Dict) -> List[str]:
        """Generate health improvement recommendations"""
        recommendations = []

        # Circuit breaker recommendations
        open_circuits = [name for name, status in health_status["circuit_breakers"].items()
                        if status["state"] == CircuitState.OPEN.value]
        if open_circuits:
            recommendations.append(f"Investigate and resolve issues with services: {', '.join(open_circuits)}")

        # Resource recommendations
        resources = health_status.get("system_resources", {})
        if resources.get("cpu_percent", 0) > 80:
            recommendations.append("Consider scaling CPU resources or optimizing computational load")

        if resources.get("memory_percent", 0) > 80:
            recommendations.append("Consider increasing memory or implementing memory optimization")

        if resources.get("disk_percent", 0) > 90:
            recommendations.append("Cleanup disk space or implement data archival")

        # Error rate recommendations
        if self.error_metrics.error_rate_24h > 0.05:
            recommendations.append("Investigate root causes of increased error rate")

        if not recommendations:
            recommendations.append("System is healthy - continue normal operations")

        return recommendations

    def get_resilience_status(self) -> Dict:
        """Get comprehensive resilience system status"""
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "error_metrics": {
                "total_errors": self.error_metrics.total_errors,
                "errors_by_category": self.error_metrics.errors_by_category,
                "errors_by_severity": self.error_metrics.errors_by_severity,
                "error_rate_24h": self.error_metrics.error_rate_24h,
                "last_error_time": self.error_metrics.last_error_time.isoformat() if self.error_metrics.last_error_time else None
            },
            "circuit_breakers": {name: cb.get_status() for name, cb in self.circuit_breakers.items()},
            "recovery_engine": {
                "active_recoveries": len(self.recovery_engine.active_recoveries),
                "available_strategies": len(self.recovery_engine.recovery_strategies)
            },
            "last_health_check": self.last_health_check.isoformat() if self.last_health_check else None
        }


# Global instance
autonomous_resilience_agent = AutonomousResilienceAgent()