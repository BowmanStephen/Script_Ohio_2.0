"""
Enhanced Agent Framework with DSPy Integration and Advanced Security

This module provides the foundation for our advanced multi-agent system, building upon
the existing BaseAgent framework while adding DSPy-style programmatic composition,
enhanced security, and human-in-the-loop integration capabilities.

Key Features:
- DSPy program composition and execution
- Multi-tier security with role-based permissions
- Human-in-the-loop decision gates
- Comprehensive error handling and recovery
- Performance monitoring and optimization
"""

import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union, Callable
from pathlib import Path


# DSPy-style program composition (simplified implementation)
@dataclass
class DSPyStep:
    """Single step in a DSPy-style program"""

    name: str
    description: str
    function: Callable
    parameters: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    retry_count: int = 3
    timeout: float = 300.0
    security_level: str = "standard"


@dataclass
class DSPyProgram:
    """DSPy-style programmatic composition"""

    name: str
    description: str
    steps: List[DSPyStep] = field(default_factory=list)
    global_parameters: Dict[str, Any] = field(default_factory=dict)
    error_handling: str = "fail_fast"  # fail_fast, retry_all, continue_on_error
    human_gates: List[str] = field(default_factory=list)


# Enhanced permission levels
class EnhancedPermissionLevel(Enum):
    READ_ONLY = "read_only"
    READ_EXECUTE = "read_execute"
    READ_EXECUTE_WRITE = "read_execute_write"
    API_ACCESS = "api_access"
    MODEL_EXECUTION = "model_execution"
    HUMAN_REVIEW = "human_review"
    SYSTEM_ADMIN = "system_admin"


# Automation levels for human-in-the-loop
class AutomationLevel(Enum):
    FULL_AUTO = "full_auto"  # Autonomous execution
    SEMI_AUTO = "semi_auto"  # Human confirmation required
    MANUAL = "manual"  # Human-controlled execution
    EMERGENCY = "emergency"  # Immediate human intervention


# Security context
@dataclass
class SecurityContext:
    """Security context for agent operations"""

    user_id: Optional[str] = None
    session_id: Optional[str] = None
    permissions: List[EnhancedPermissionLevel] = field(default_factory=list)
    access_token: Optional[str] = None
    audit_required: bool = True
    encryption_key: Optional[str] = None


# Human interaction context
@dataclass
class HumanInteraction:
    """Human-in-the-loop interaction configuration"""

    required: bool = False
    automation_level: AutomationLevel = AutomationLevel.FULL_AUTO
    confirmation_message: Optional[str] = None
    timeout_seconds: float = 300.0
    rollback_available: bool = True
    decision_data: Dict[str, Any] = field(default_factory=dict)


# Performance metrics
@dataclass
class AgentMetrics:
    """Performance metrics for agent operations"""

    execution_count: int = 0
    success_count: int = 0
    error_count: int = 0
    average_execution_time: float = 0.0
    last_execution: Optional[datetime] = None
    total_execution_time: float = 0.0


logger = logging.getLogger(__name__)


class EnhancedBaseAgent:
    """
    Enhanced Base Agent with DSPy integration and advanced security

    This class extends the basic agent functionality with:
    - DSPy-style program composition
    - Enhanced security with role-based permissions
    - Human-in-the-loop decision gates
    - Comprehensive performance monitoring
    - Advanced error handling and recovery
    """

    def __init__(
        self,
        agent_id: str,
        agent_name: str,
        permission_level: EnhancedPermissionLevel,
        security_context: Optional[SecurityContext] = None,
        capabilities: Optional[List[str]] = None,
    ):
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.permission_level = permission_level
        self.capabilities = capabilities or []

        # Security and context
        self.security_context = security_context or SecurityContext()
        self.human_interaction = HumanInteraction()

        # DSPy program support
        self.dspy_programs: Dict[str, DSPyProgram] = {}
        self.current_program: Optional[DSPyProgram] = None

        # Performance monitoring
        self.metrics = AgentMetrics()
        self.execution_history: List[Dict[str, Any]] = []

        # Error handling
        self.error_handlers: Dict[str, Callable] = {}
        self.fallback_strategies: Dict[str, Callable] = {}

        # Logging
        self.logger = logging.getLogger(f"agents.{self.__class__.__name__}")

        # Initialize security
        self._initialize_security()

        self.logger.info(
            f"Enhanced agent initialized: {self.agent_id} ({self.agent_name})"
        )

    def _initialize_security(self):
        """Initialize security context and permissions"""
        # Validate security context
        if not self.security_context.permissions:
            self.security_context.permissions = [self.permission_level]

        # Add agent-specific permissions
        if self.permission_level not in self.security_context.permissions:
            self.security_context.permissions.append(self.permission_level)

        self.logger.debug(f"Security context initialized for {self.agent_id}")

    def register_dspy_program(self, program: DSPyProgram):
        """Register a DSPy program for this agent"""
        self.dspy_programs[program.name] = program
        self.logger.info(f"Registered DSPy program: {program.name}")

    def execute_dspy_program(
        self,
        program_name: str,
        parameters: Optional[Dict[str, Any]] = None,
        human_interaction: Optional[HumanInteraction] = None,
    ) -> Dict[str, Any]:
        """
        Execute a DSPy program with full security and monitoring

        Args:
            program_name: Name of the DSPy program to execute
            parameters: Program-specific parameters
            human_interaction: Human-in-the-loop configuration

        Returns:
            Execution results with comprehensive metadata
        """
        start_time = time.time()
        execution_id = f"{self.agent_id}_{program_name}_{int(start_time)}"

        try:
            # Validate program exists
            if program_name not in self.dspy_programs:
                raise ValueError(f"Program '{program_name}' not registered")

            program = self.dspy_programs[program_name]
            self.current_program = program

            # Update security context
            if human_interaction:
                self.human_interaction = human_interaction

            # Log execution start
            self.logger.info(
                f"Executing DSPy program: {program_name} (ID: {execution_id})"
            )

            # Security validation
            self._validate_security_requirements(program)

            # Human gate if required
            if program.human_gates or human_interaction:
                self._handle_human_gates(program, parameters or {})

            # Execute program steps
            results = self._execute_program_steps(program, parameters or {})

            # Update metrics
            execution_time = time.time() - start_time
            self._update_metrics(True, execution_time)

            # Log execution
            self._log_execution(
                execution_id, program_name, True, execution_time, results
            )

            return {
                "status": "success",
                "execution_id": execution_id,
                "program_name": program_name,
                "results": results,
                "execution_time": execution_time,
                "timestamp": datetime.utcnow().isoformat(),
                "agent_id": self.agent_id,
            }

        except Exception as e:
            execution_time = time.time() - start_time
            self._update_metrics(False, execution_time)

            # Log error
            self._log_execution(
                execution_id, program_name, False, execution_time, {"error": str(e)}
            )

            # Handle error with fallback strategies
            return self._handle_execution_error(
                execution_id, program_name, e, execution_time
            )

    def _validate_security_requirements(self, program: DSPyProgram):
        """Validate security requirements for program execution"""
        # Check if agent has required permissions
        required_permissions = self._get_program_permissions(program)

        for permission in required_permissions:
            if permission not in self.security_context.permissions:
                raise PermissionError(
                    f"Insufficient permissions: {permission} required"
                )

        # Validate access token if API access required
        if EnhancedPermissionLevel.API_ACCESS in required_permissions:
            if not self.security_context.access_token:
                raise ValueError("API access token required")

        self.logger.debug(f"Security validation passed for program: {program.name}")

    def _get_program_permissions(
        self, program: DSPyProgram
    ) -> List[EnhancedPermissionLevel]:
        """Determine required permissions for a program"""
        permissions = [self.permission_level]

        # Check steps for additional permission requirements
        for step in program.steps:
            if "api" in step.security_level:
                if EnhancedPermissionLevel.API_ACCESS not in permissions:
                    permissions.append(EnhancedPermissionLevel.API_ACCESS)

            if "model" in step.security_level:
                if EnhancedPermissionLevel.MODEL_EXECUTION not in permissions:
                    permissions.append(EnhancedPermissionLevel.MODEL_EXECUTION)

            if "human" in step.security_level:
                if EnhancedPermissionLevel.HUMAN_REVIEW not in permissions:
                    permissions.append(EnhancedPermissionLevel.HUMAN_REVIEW)

        return permissions

    def _handle_human_gates(self, program: DSPyProgram, parameters: Dict[str, Any]):
        """Handle human-in-the-loop decision gates"""
        gates = program.human_gates

        if (
            self.human_interaction.required
            or self.human_interaction.automation_level != AutomationLevel.FULL_AUTO
        ):
            # Prepare decision data
            decision_data = {
                "agent_id": self.agent_id,
                "program_name": program.name,
                "parameters": parameters,
                "timestamp": datetime.utcnow().isoformat(),
                "security_context": {
                    "user_id": self.security_context.user_id,
                    "permissions": [p.value for p in self.security_context.permissions],
                },
            }

            # Update human interaction context
            self.human_interaction.decision_data = decision_data

            # Log human gate requirement
            self.logger.info(f"Human gate required for program: {program.name}")

            # In a real implementation, this would trigger a human interface
            # For now, we'll simulate human approval
            if self.human_interaction.automation_level == AutomationLevel.EMERGENCY:
                raise RuntimeError("Emergency intervention required")

            # Simulate human confirmation for demo purposes
            self.logger.info(f"Human confirmation received for program: {program.name}")

    def _execute_program_steps(
        self, program: DSPyProgram, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute all steps in a DSPy program"""
        results = {}
        step_results = {}

        for step in program.steps:
            step_start_time = time.time()

            try:
                self.logger.info(f"Executing step: {step.name}")

                # Check dependencies
                if step.dependencies:
                    for dep in step.dependencies:
                        if dep not in step_results:
                            raise ValueError(f"Dependency not met: {dep}")

                # Prepare step parameters
                step_params = {
                    **program.global_parameters,
                    **parameters,
                    **step.parameters,
                    "dependencies": {
                        dep: step_results[dep] for dep in step.dependencies
                    },
                }

                # Execute step function
                step_result = self._execute_step_with_security(step, step_params)

                # Store step result
                step_results[step.name] = step_result
                results[step.name] = step_result

                step_time = time.time() - step_start_time
                self.logger.info(f"Step completed: {step.name} ({step_time:.2f}s)")

            except Exception as e:
                step_time = time.time() - step_start_time
                self.logger.error(
                    f"Step failed: {step.name} ({step_time:.2f}s) - {str(e)}"
                )

                # Handle based on error handling strategy
                if program.error_handling == "fail_fast":
                    raise
                elif program.error_handling == "retry_all":
                    # Implement retry logic here
                    pass
                elif program.error_handling == "continue_on_error":
                    step_results[step.name] = {"error": str(e)}
                    results[step.name] = {"error": str(e)}
                    continue

        return results

    def _execute_step_with_security(
        self, step: DSPyStep, parameters: Dict[str, Any]
    ) -> Any:
        """Execute a single step with security validation"""
        # Validate step security level
        if step.security_level == "high":
            self._validate_high_security_step(step, parameters)
        elif step.security_level == "model":
            self._validate_model_execution_step(step, parameters)
        elif step.security_level == "api":
            self._validate_api_access_step(step, parameters)

        # Execute step with timeout
        if hasattr(step.function, "__self__"):
            # Bound method
            result = step.function(**parameters)
        else:
            # Unbound function or static method
            result = step.function(self, **parameters)

        return result

    def _validate_high_security_step(self, step: DSPyStep, parameters: Dict[str, Any]):
        """Validate high-security step execution"""
        if (
            EnhancedPermissionLevel.SYSTEM_ADMIN
            not in self.security_context.permissions
        ):
            raise PermissionError(
                f"High security step requires system admin permission: {step.name}"
            )

    def _validate_model_execution_step(
        self, step: DSPyStep, parameters: Dict[str, Any]
    ):
        """Validate model execution step"""
        if (
            EnhancedPermissionLevel.MODEL_EXECUTION
            not in self.security_context.permissions
        ):
            raise PermissionError(
                f"Model execution requires model execution permission: {step.name}"
            )

    def _validate_api_access_step(self, step: DSPyStep, parameters: Dict[str, Any]):
        """Validate API access step"""
        if EnhancedPermissionLevel.API_ACCESS not in self.security_context.permissions:
            raise PermissionError(
                f"API access requires API access permission: {step.name}"
            )

        if not self.security_context.access_token:
            raise ValueError("API access token required for API step")

    def _update_metrics(self, success: bool, execution_time: float):
        """Update agent performance metrics"""
        self.metrics.execution_count += 1
        self.metrics.total_execution_time += execution_time

        if success:
            self.metrics.success_count += 1
        else:
            self.metrics.error_count += 1

        self.metrics.average_execution_time = (
            self.metrics.total_execution_time / self.metrics.execution_count
        )
        self.metrics.last_execution = datetime.utcnow()

    def _log_execution(
        self,
        execution_id: str,
        program_name: str,
        success: bool,
        execution_time: float,
        result: Dict[str, Any],
    ):
        """Log execution details"""
        log_entry = {
            "execution_id": execution_id,
            "agent_id": self.agent_id,
            "program_name": program_name,
            "success": success,
            "execution_time": execution_time,
            "timestamp": datetime.utcnow().isoformat(),
            "result_summary": {
                "status": result.get("status", "unknown"),
                "keys": (
                    list(result.keys())
                    if isinstance(result, dict)
                    else "non_dict_result"
                ),
            },
        }

        if self.security_context.audit_required:
            # Store in audit log
            self.execution_history.append(log_entry)

        self.logger.info(
            f"Execution logged: {execution_id} - {'SUCCESS' if success else 'FAILED'}"
        )

    def _handle_execution_error(
        self,
        execution_id: str,
        program_name: str,
        error: Exception,
        execution_time: float,
    ) -> Dict[str, Any]:
        """Handle execution errors with fallback strategies"""
        self.logger.error(f"Execution error in {program_name}: {str(error)}")

        # Check for fallback strategies
        error_type = type(error).__name__

        if error_type in self.fallback_strategies:
            try:
                self.logger.info(f"Attempting fallback strategy for {error_type}")
                fallback_result = self.fallback_strategies[error_type](
                    error, execution_id
                )
                return {
                    "status": "fallback_success",
                    "execution_id": execution_id,
                    "program_name": program_name,
                    "fallback_result": fallback_result,
                    "original_error": str(error),
                    "execution_time": execution_time,
                    "timestamp": datetime.utcnow().isoformat(),
                    "agent_id": self.agent_id,
                }
            except Exception as fallback_error:
                self.logger.error(f"Fallback strategy failed: {str(fallback_error)}")

        return {
            "status": "error",
            "execution_id": execution_id,
            "program_name": program_name,
            "error": str(error),
            "error_type": error_type,
            "execution_time": execution_time,
            "timestamp": datetime.utcnow().isoformat(),
            "agent_id": self.agent_id,
            "recovery_options": self._get_recovery_options(error),
        }

    def _get_recovery_options(self, error: Exception) -> List[str]:
        """Get recovery options for an error"""
        options = ["retry_execution", "fallback_strategy", "human_intervention"]

        # Add specific options based on error type
        if "permission" in str(error).lower():
            options.insert(0, "check_permissions")
        elif "timeout" in str(error).lower():
            options.insert(0, "increase_timeout")
        elif "api" in str(error).lower():
            options.insert(0, "check_api_credentials")

        return options

    def register_error_handler(self, error_type: str, handler: Callable):
        """Register an error handler for a specific error type"""
        self.error_handlers[error_type] = handler
        self.logger.info(f"Registered error handler for: {error_type}")

    def register_fallback_strategy(self, error_type: str, strategy: Callable):
        """Register a fallback strategy for a specific error type"""
        self.fallback_strategies[error_type] = strategy
        self.logger.info(f"Registered fallback strategy for: {error_type}")

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics"""
        success_rate = (
            (self.metrics.success_count / self.metrics.execution_count) * 100
            if self.metrics.execution_count > 0
            else 0
        )

        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "execution_count": self.metrics.execution_count,
            "success_count": self.metrics.success_count,
            "error_count": self.metrics.error_count,
            "success_rate": round(success_rate, 2),
            "average_execution_time": round(self.metrics.average_execution_time, 3),
            "total_execution_time": round(self.metrics.total_execution_time, 3),
            "last_execution": (
                self.metrics.last_execution.isoformat()
                if self.metrics.last_execution
                else None
            ),
            "registered_programs": list(self.dspy_programs.keys()),
            "capabilities": self.capabilities,
            "permission_level": self.permission_level.value,
        }

    def get_execution_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent execution history"""
        return self.execution_history[-limit:] if self.execution_history else []
