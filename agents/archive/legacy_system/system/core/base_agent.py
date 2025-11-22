"""
Base Agent Framework - Foundation for all agents in Script Ohio 2.0
Following Claude's best practices for agent development
"""

import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Any, Optional, Union
import json
import time

class PermissionLevel(Enum):
    """Four-tier permission system following security best practices"""
    READ_ONLY = "READ_ONLY"                    # Level 1: Context monitoring, performance tracking
    READ_EXECUTE = "READ_EXECUTE"              # Level 2: Data analysis, model execution
    READ_EXECUTE_WRITE = "READ_EXECUTE_WRITE"  # Level 3: Data modification, agent management
    ADMIN = "ADMIN"                            # Level 4: System configuration, security management

@dataclass
class AgentCapability:
    """Defines agent capabilities and security requirements"""
    name: str
    description: str
    permission_required: PermissionLevel
    tools_required: List[str]
    estimated_duration: Optional[int] = None  # minutes
    resource_requirements: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AgentTask:
    """Represents a task to be executed by an agent"""
    task_id: str
    agent_id: str
    action: str
    parameters: Dict[str, Any]
    target_files: List[str]
    priority: int  # 1=Critical, 2=High, 3=Medium, 4=Low
    dependencies: List[str] = field(default_factory=list)
    timeout: Optional[int] = None
    retry_attempts: int = 3
    created_at: datetime = field(default_factory=datetime.now)
    status: str = "pending"  # pending, in_progress, completed, failed

@dataclass
class AgentMessage:
    """Secure message protocol for inter-agent communication"""
    message_id: str
    sender_id: str
    receiver_id: str
    message_type: str  # TASK_ASSIGNMENT, STATUS_UPDATE, RESULT, ERROR, HEARTBEAT
    payload: Dict[str, Any]
    priority: int
    timestamp: datetime = field(default_factory=datetime.now)
    signature: Optional[str] = None

class BaseAgent(ABC):
    """
    Base class for all agents following Claude's best practices:
    - Focused capabilities
    - Clear boundaries
    - Modular design
    - Comprehensive performance monitoring
    """

    def __init__(self, agent_id: str, name: str, permission_level: PermissionLevel, tool_loader=None):
        self.agent_id = agent_id
        self.name = name
        self.permission_level = permission_level
        self.tool_loader = tool_loader
        self.logger = logging.getLogger(f"agent.{agent_id}")

        # Agent state management
        self.status = "initialized"
        self.capabilities = self._define_capabilities()
        self.created_at = datetime.now()
        self.last_activity = None
        self.execution_history = []
        self.performance_metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_response_time": 0.0,
            "peak_memory_usage": 0.0
        }

        # Security and compliance
        self.security_context = {
            "permission_level": permission_level,
            "allowed_operations": self._get_allowed_operations(),
            "access_log": []
        }

        self.logger.info(f"Agent {self.agent_id} initialized with permission level: {permission_level.value}")

    @abstractmethod
    def _define_capabilities(self) -> List[AgentCapability]:
        """
        Define agent capabilities and required permissions.
        Each agent must specify what it can do and what permissions it needs.

        Returns:
            List of AgentCapability objects
        """
        pass

    @abstractmethod
    def _execute_action(self, action: str, parameters: Dict[str, Any],
                      user_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute agent action with proper routing and error handling.
        All agent logic should be implemented here with action-based routing.

        Args:
            action: The specific action to execute
            parameters: Action-specific parameters
            user_context: Context information about the user/request

        Returns:
            Dict containing action results

        Raises:
            ValueError: For unknown actions
            PermissionError: For insufficient permissions
        """
        pass

    def execute_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute agent request with comprehensive error handling and monitoring.
        This is the main entry point for all agent interactions.
        """
        start_time = time.time()
        request_id = str(uuid.uuid4())

        try:
            # Update agent state
            self.status = "executing"
            self.last_activity = datetime.now()

            # Log request for security audit
            self._log_access("execute_request", {
                "request_id": request_id,
                "action": request.get('action', 'unknown'),
                "user_context": request.get('user_context', {})
            })

            # Validate request
            self._validate_request(request)

            # Extract request components
            action = request.get('action', 'unknown')
            parameters = request.get('parameters', {})
            user_context = request.get('user_context', {})

            # Validate permissions for action
            if not self._validate_action_permissions(action, user_context):
                raise PermissionError(f"Insufficient permissions for action: {action}")

            # Execute action
            self.logger.info(f"Executing action: {action} for agent: {self.agent_id}")
            result = self._execute_action(action, parameters, user_context)

            # Update performance metrics
            execution_time = time.time() - start_time
            self._update_performance_metrics(True, execution_time)

            # Log execution in history
            self.execution_history.append({
                "request_id": request_id,
                "action": action,
                "status": "success",
                "execution_time": execution_time,
                "timestamp": datetime.now().isoformat()
            })

            self.status = "completed"

            return {
                "status": "success",
                "result": result,
                "agent_id": self.agent_id,
                "request_id": request_id,
                "execution_time": execution_time,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            execution_time = time.time() - start_time
            self._update_performance_metrics(False, execution_time)

            # Log error in history
            self.execution_history.append({
                "request_id": request_id,
                "action": request.get('action', 'unknown'),
                "status": "failed",
                "error": str(e),
                "execution_time": execution_time,
                "timestamp": datetime.now().isoformat()
            })

            self.status = "error"
            self.logger.error(f"Error executing request: {e}")

            return {
                "status": "error",
                "error": str(e),
                "agent_id": self.agent_id,
                "request_id": request_id,
                "execution_time": execution_time,
                "timestamp": datetime.now().isoformat()
            }

    def _get_allowed_operations(self) -> List[str]:
        """Get allowed operations based on permission level"""
        permission_operations = {
            PermissionLevel.READ_ONLY: ["monitor", "query", "read"],
            PermissionLevel.READ_EXECUTE: ["monitor", "query", "read", "execute"],
            PermissionLevel.READ_EXECUTE_WRITE: ["monitor", "query", "read", "execute", "write", "modify"],
            PermissionLevel.ADMIN: ["monitor", "query", "read", "execute", "write", "modify", "admin"]
        }
        return permission_operations.get(self.permission_level, [])

    def _validate_action_permissions(self, action: str, user_context: Dict[str, Any]) -> bool:
        """Validate if agent has permission for the given action"""
        # ADMIN and READ_EXECUTE_WRITE level agents have all permissions for demo purposes
        if self.permission_level in [PermissionLevel.ADMIN, PermissionLevel.READ_EXECUTE_WRITE]:
            return True

        # Check if action is in allowed operations
        allowed_ops = self._get_allowed_operations()

        # Extract operation type from action (basic implementation)
        action_operation = action.split('_')[0].lower()

        return action_operation in allowed_ops

    def _validate_request(self, request: Dict[str, Any]) -> None:
        """Validate request format and content"""
        if not isinstance(request, dict):
            raise ValueError("Request must be a dictionary")

        if 'action' not in request:
            raise ValueError("Request must contain 'action' field")

        if not isinstance(request['action'], str):
            raise ValueError("Action must be a string")

        # Log security validation
        self._log_access("validate_request", {
            "request_validated": True,
            "action": request['action']
        })

    def _update_performance_metrics(self, success: bool, execution_time: float) -> None:
        """Update performance metrics"""
        self.performance_metrics["total_requests"] += 1

        if success:
            self.performance_metrics["successful_requests"] += 1
        else:
            self.performance_metrics["failed_requests"] += 1

        # Update average response time
        total_requests = self.performance_metrics["total_requests"]
        current_avg = self.performance_metrics["average_response_time"]
        self.performance_metrics["average_response_time"] = (
            (current_avg * (total_requests - 1) + execution_time) / total_requests
        )

        # Update peak memory usage (simplified)
        try:
            import psutil
            current_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            if current_memory > self.performance_metrics["peak_memory_usage"]:
                self.performance_metrics["peak_memory_usage"] = current_memory
        except ImportError:
            # psutil not available, skip memory tracking
            pass

    def _log_access(self, operation: str, details: Dict[str, Any]) -> None:
        """Log access for security audit"""
        access_log_entry = {
            "timestamp": datetime.now().isoformat(),
            "agent_id": self.agent_id,
            "operation": operation,
            "details": details
        }
        self.security_context["access_log"].append(access_log_entry)

        # Keep log size manageable (last 1000 entries)
        if len(self.security_context["access_log"]) > 1000:
            self.security_context["access_log"] = self.security_context["access_log"][-1000:]

    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive agent status"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "status": self.status,
            "permission_level": self.permission_level.value,
            "capabilities_count": len(self.capabilities),
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
            "performance_metrics": self.performance_metrics,
            "security_context": {
                "permission_level": self.security_context["permission_level"].value,
                "access_log_entries": len(self.security_context["access_log"])
            }
        }

    def get_capabilities(self) -> List[AgentCapability]:
        """Get agent capabilities"""
        return self.capabilities

    def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        try:
            # Basic health checks
            status_ok = self.status in ["initialized", "completed", "idle"]

            # Check performance metrics
            error_rate = (self.performance_metrics["failed_requests"] /
                         max(self.performance_metrics["total_requests"], 1)) * 100

            # Memory check (if available)
            memory_ok = True
            try:
                import psutil
                memory_usage = psutil.Process().memory_info().rss / 1024 / 1024  # MB
                memory_ok = memory_usage < 1024  # Less than 1GB
            except ImportError:
                memory_ok = True  # Can't check, assume OK

            health_score = 100
            if not status_ok:
                health_score -= 30
            if error_rate > 10:
                health_score -= 20
            if not memory_ok:
                health_score -= 25

            return {
                "status": "healthy" if health_score >= 80 else "unhealthy",
                "health_score": health_score,
                "checks": {
                    "status_ok": status_ok,
                    "error_rate": f"{error_rate:.1f}%",
                    "memory_ok": memory_ok
                },
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "health_score": 0,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def shutdown(self) -> Dict[str, Any]:
        """Graceful shutdown"""
        try:
            self.status = "shutting_down"
            self.logger.info(f"Agent {self.agent_id} shutting down gracefully")

            # Save final state
            final_state = {
                "agent_id": self.agent_id,
                "status": "shutdown",
                "final_metrics": self.performance_metrics,
                "total_executions": len(self.execution_history),
                "shutdown_time": datetime.now().isoformat()
            }

            # Save to log file if needed
            shutdown_log_path = f"logs/agent_shutdown_{self.agent_id}.json"
            try:
                with open(shutdown_log_path, 'w') as f:
                    json.dump(final_state, f, indent=2)
            except Exception as e:
                self.logger.warning(f"Could not save shutdown log: {e}")

            self.status = "shutdown"
            return final_state

        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")
            return {
                "agent_id": self.agent_id,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }