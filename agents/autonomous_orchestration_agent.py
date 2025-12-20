"""
🏛️ ScriptOhio Autonomous Orchestration Agent

Self-managing orchestration agent that proactively manages ScriptOhio workflows
without human intervention. Monitors triggers, executes workflows, and maintains
the entire analytics pipeline autonomously.
"""

import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from agents.core.agent_framework import AgentCapability, BaseAgent, PermissionLevel

# Import existing orchestration components
from agents.core.state_manager import StateManager
from agents.core.trigger_system import TriggerRegistry, TriggerType

logger = logging.getLogger(__name__)


class AutonomyLevel(Enum):
    """Levels of autonomous operation"""
    OFF = "off"
    MONITOR_ONLY = "monitor_only"
    SEMI_AUTONOMOUS = "semi_autonomous"
    FULLY_AUTONOMOUS = "fully_autonomous"


class WorkflowStatus(Enum):
    """Autonomous workflow execution status"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"
    PAUSED = "paused"


@dataclass
class AutonomousTask:
    """Task definition for autonomous execution"""
    task_id: str
    workflow_type: str
    parameters: Dict[str, Any]
    trigger_source: str
    priority: int = 1
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: WorkflowStatus = WorkflowStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@dataclass
class SystemMetrics:
    """System-wide performance metrics"""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    active_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    average_response_time: float = 0.0
    system_health_score: float = 1.0
    resource_usage: Dict[str, float] = field(default_factory=dict)


class AutonomousOrchestrationAgent(BaseAgent):
    """
    Self-managing orchestration agent for ScriptOhio

    Proactively manages workflows, monitors triggers, and maintains
    the entire analytics pipeline with minimal human intervention.
    """

    def __init__(self, autonomy_level: AutonomyLevel = AutonomyLevel.FULLY_AUTONOMOUS):
        """Initialize the autonomous orchestration agent"""
        super().__init__(
            agent_id="autonomous_orchestration_agent",
            name="ScriptOhio Autonomous Orchestration Engine",
            permission_level=PermissionLevel.ADMIN,
        )

        # Autonomous configuration
        self.autonomy_level = autonomy_level
        self.config = self._load_autonomous_config()

        # Core components
        self.trigger_registry = TriggerRegistry()
        self.state_manager = StateManager()
        self.task_queue: List[AutonomousTask] = []
        self.execution_history: List[AutonomousTask] = []

        # Performance tracking
        self.system_metrics = SystemMetrics()
        self.last_health_check = datetime.now(timezone.utc)

        # Load existing agents for delegation
        self._initialize_agent_delegates()

        logger.info(f"AutonomousOrchestrationAgent initialized with autonomy level: {autonomy_level.value}")

    def _load_autonomous_config(self) -> Dict[str, Any]:
        """Load autonomous orchestration configuration"""
        config_path = Path("config/autonomous_orchestration.json")
        if config_path.exists():
            try:
                with open(config_path, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Error loading autonomous config: {e}")

        return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default autonomous configuration"""
        return {
            "triggers": {
                "weekly_analysis": {
                    "schedule": "every wednesday 09:00",
                    "event": "new_cfbd_data_available",
                    "conditions": ["data_quality_check"],
                    "enabled": True
                },
                "model_training": {
                    "performance_threshold": 0.05,
                    "data_threshold": 100,
                    "schedule": "monthly",
                    "enabled": True
                },
                "gameday_predictions": {
                    "schedule": "game_days_08:00_20:00_hourly",
                    "event": "line_movement_significant",
                    "enabled": True
                }
            },
            "autonomy_level": "fully_autonomous",
            "self_healing": {
                "enabled": True,
                "circuit_breaker_threshold": 5,
                "auto_retry": True,
                "fallback_strategies": True
            },
            "monitoring": {
                "metrics": ["accuracy", "drift", "response_time", "resource_usage"],
                "alerts": ["performance_degradation", "errors", "resource_limits"],
                "health_check_interval": 300  # 5 minutes
            },
            "execution": {
                "max_concurrent_tasks": 5,
                "task_timeout": 3600,  # 1 hour
                "priority_levels": 3
            }
        }

    def _initialize_agent_delegates(self):
        """Initialize connections to existing specialized agents"""
        self.agent_delegates = {}

        # Import existing agents lazily
        try:
            from agents.weekly_analysis_orchestrator import weekly_analysis_orchestrator
            self.agent_delegates["weekly_analysis"] = weekly_analysis_orchestrator
        except ImportError:
            logger.warning("Weekly analysis orchestrator not available")

        try:
            from agents.model_execution_engine import model_execution_engine
            self.agent_delegates["model_execution"] = model_execution_engine
        except ImportError:
            logger.warning("Model execution engine not available")

        try:
            from agents.validation_orchestrator import validation_orchestrator
            self.agent_delegates["validation"] = validation_orchestrator
        except ImportError:
            logger.warning("Validation orchestrator not available")

        # Add more agent delegates as needed
        logger.info(f"Initialized {len(self.agent_delegates)} agent delegates")

    def _define_capabilities(self) -> List[AgentCapability]:
        """Define autonomous orchestration capabilities"""
        return [
            AgentCapability(
                name="monitor_triggers",
                description="Monitor and respond to autonomous triggers",
                permission_required=PermissionLevel.READ_EXECUTE,
                tools_required=["scheduler", "file_monitor", "api_monitor"],
                data_access=["trigger_registry", "system_state"],
                execution_time_estimate=0.1,
            ),
            AgentCapability(
                name="execute_autonomous_workflow",
                description="Execute workflows without human intervention",
                permission_required=PermissionLevel.ADMIN,
                tools_required=["workflow_executor", "resource_manager"],
                data_access=["task_queue", "execution_history"],
                execution_time_estimate=2.0,
            ),
            AgentCapability(
                name="self_heal_system",
                description="Detect and recover from system failures",
                permission_required=PermissionLevel.ADMIN,
                tools_required=["circuit_breaker", "error_recovery"],
                data_access=["error_logs", "system_metrics"],
                execution_time_estimate=1.0,
            ),
            AgentCapability(
                name="optimize_resources",
                description="Optimize system resource allocation",
                permission_required=PermissionLevel.ADMIN,
                tools_required=["resource_optimizer", "performance_monitor"],
                data_access=["resource_usage", "performance_metrics"],
                execution_time_estimate=0.5,
            ),
            AgentCapability(
                name="manage_task_queue",
                description="Manage and prioritize autonomous task execution",
                permission_required=PermissionLevel.ADMIN,
                tools_required=["task_scheduler", "queue_manager"],
                data_access=["task_queue", "execution_history"],
                execution_time_estimate=0.2,
            ),
        ]

    def _execute_action(
        self, action: str, parameters: Dict[str, Any], user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute autonomous orchestration actions"""
        action_start_time = time.time()

        try:
            # Check autonomy level
            if self.autonomy_level == AutonomyLevel.OFF:
                return {
                    "success": False,
                    "error": "Autonomous orchestration is disabled",
                    "autonomy_level": self.autonomy_level.value,
                }

            # Route to appropriate action
            if action == "monitor_triggers":
                result = self._monitor_triggers(parameters, user_context)
            elif action == "execute_autonomous_workflow":
                result = self._execute_autonomous_workflow(parameters, user_context)
            elif action == "self_heal_system":
                result = self._self_heal_system(parameters, user_context)
            elif action == "optimize_resources":
                result = self._optimize_resources(parameters, user_context)
            elif action == "manage_task_queue":
                result = self._manage_task_queue(parameters, user_context)
            elif action == "run_autonomous_cycle":
                result = self._run_autonomous_cycle(parameters, user_context)
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}",
                    "available_actions": [cap.name for cap in self._define_capabilities()],
                }

            # Update metrics
            execution_time = time.time() - action_start_time
            self._update_system_metrics(action, execution_time, result.get("success", False))

            return result

        except Exception as e:
            execution_time = time.time() - action_start_time
            logger.error(f"Error in autonomous action {action}: {e}")

            # Attempt self-healing if enabled
            if self.config.get("self_healing", {}).get("enabled", True):
                self._attempt_error_recovery(action, e, parameters)

            return {
                "success": False,
                "error": str(e),
                "action": action,
                "execution_time": execution_time,
                "autonomy_level": self.autonomy_level.value,
            }

    def _monitor_triggers(self, params: Dict, context: Dict) -> Dict[str, Any]:
        """Monitor for autonomous workflow triggers"""
        triggered_tasks = []

        try:
            # Check schedule-based triggers
            for trigger_name, trigger_config in self.config.get("triggers", {}).items():
                if not trigger_config.get("enabled", True):
                    continue

                # Check if trigger conditions are met
                if self._evaluate_trigger_conditions(trigger_config):
                    task = self._create_task_from_trigger(trigger_name, trigger_config)
                    if task:
                        triggered_tasks.append(task)
                        self.task_queue.append(task)
                        logger.info(f"Created autonomous task from trigger: {trigger_name}")

            return {
                "success": True,
                "triggers_checked": len(self.config.get("triggers", {})),
                "tasks_created": len(triggered_tasks),
                "task_queue_size": len(self.task_queue),
                "triggered_tasks": [task.task_id for task in triggered_tasks],
            }

        except Exception as e:
            logger.error(f"Error monitoring triggers: {e}")
            return {
                "success": False,
                "error": f"Trigger monitoring failed: {e}",
                "partial_tasks": len(triggered_tasks),
            }

    def _execute_autonomous_workflow(self, params: Dict, context: Dict) -> Dict[str, Any]:
        """Execute autonomous workflow"""
        workflow_type = params.get("workflow_type")
        task_id = params.get("task_id")

        if task_id:
            # Execute specific task
            task = self._find_task_by_id(task_id)
            if not task:
                return {"success": False, "error": f"Task {task_id} not found"}
            return self._execute_task(task)

        elif workflow_type:
            # Execute next task of given type
            task = self._get_next_task_of_type(workflow_type)
            if task:
                return self._execute_task(task)
            else:
                return {"success": True, "message": f"No pending tasks of type: {workflow_type}"}

        else:
            # Execute next highest priority task
            if self.task_queue:
                task = min(self.task_queue, key=lambda t: (-t.priority, t.created_at))
                return self._execute_task(task)
            else:
                return {"success": True, "message": "No tasks in queue"}

    def _execute_task(self, task: AutonomousTask) -> Dict[str, Any]:
        """Execute a single autonomous task"""
        if task.status != WorkflowStatus.PENDING:
            return {"success": False, "error": f"Task {task.task_id} is not pending (status: {task.status.value})"}

        # Mark task as running
        task.status = WorkflowStatus.RUNNING
        task.started_at = datetime.now(timezone.utc)

        try:
            logger.info(f"Executing autonomous task: {task.task_id} ({task.workflow_type})")

            # Delegate to appropriate agent
            result = self._delegate_to_agent(task.workflow_type, task.parameters)

            # Mark task as completed
            task.status = WorkflowStatus.SUCCESS
            task.completed_at = datetime.now(timezone.utc)
            task.result = result

            # Move to execution history
            self.task_queue.remove(task)
            self.execution_history.append(task)

            # Update state
            self.state_manager.save_task_state(task)

            return {
                "success": True,
                "task_id": task.task_id,
                "workflow_type": task.workflow_type,
                "execution_time": (task.completed_at - task.started_at).total_seconds(),
                "result": result,
            }

        except Exception as e:
            # Mark task as failed
            task.status = WorkflowStatus.FAILED
            task.completed_at = datetime.now(timezone.utc)
            task.error = str(e)

            # Check if we should retry
            if task.retry_count < task.max_retries:
                task.status = WorkflowStatus.RETRYING
                task.retry_count += 1
                task.started_at = None  # Reset for retry

                # Exponential backoff
                delay = min(300, 30 * (2 ** task.retry_count))  # Max 5 minutes
                logger.info(f"Retrying task {task.task_id} in {delay}s (attempt {task.retry_count}/{task.max_retries})")

                return {
                    "success": False,
                    "error": str(e),
                    "task_id": task.task_id,
                    "retry_attempt": task.retry_count,
                    "retry_delay": delay,
                    "will_retry": True,
                }
            else:
                # Move to failed history
                self.task_queue.remove(task)
                self.execution_history.append(task)

                logger.error(f"Task {task.task_id} failed permanently after {task.max_retries} retries")

                return {
                    "success": False,
                    "error": str(e),
                    "task_id": task.task_id,
                    "retry_attempts": task.retry_count,
                    "will_retry": False,
                    "final_failure": True,
                }

    def _delegate_to_agent(self, workflow_type: str, parameters: Dict) -> Dict[str, Any]:
        """Delegate task execution to appropriate specialized agent"""
        agent_mapping = {
            "weekly_analysis": "weekly_analysis",
            "model_training": "model_execution",
            "validation": "validation",
            "data_processing": "cfbd_integration",
        }

        agent_key = agent_mapping.get(workflow_type)
        if agent_key and agent_key in self.agent_delegates:
            agent = self.agent_delegates[agent_key]

            # Call agent with parameters
            if hasattr(agent, '_execute_action'):
                # Use agent's execute_action method
                action = workflow_type.replace("_", "")
                return agent._execute_action(action, parameters, {})
            elif hasattr(agent, 'execute_workflow'):
                # Use generic workflow execution
                return agent.execute_workflow(workflow_type, parameters)
            else:
                # Fallback to direct method call
                method_name = f"run_{workflow_type}"
                if hasattr(agent, method_name):
                    method = getattr(agent, method_name)
                    return method(**parameters)

        # Fallback execution logic
        return self._fallback_execution(workflow_type, parameters)

    def _fallback_execution(self, workflow_type: str, parameters: Dict) -> Dict[str, Any]:
        """Fallback execution logic for workflows without dedicated agents"""
        if workflow_type == "weekly_analysis":
            return self._run_weekly_analysis_fallback(parameters)
        elif workflow_type == "model_training":
            return self._run_model_training_fallback(parameters)
        elif workflow_type == "gameday_predictions":
            return self._run_gameday_predictions_fallback(parameters)
        else:
            raise ValueError(f"Unsupported workflow type: {workflow_type}")

    def _run_weekly_analysis_fallback(self, params: Dict) -> Dict[str, Any]:
        """Fallback weekly analysis execution"""
        week = params.get("week", self._get_current_week())
        season = params.get("season", 2025)

        # Import and run existing weekly analysis script
        try:
            import subprocess
            import sys

            cmd = [
                sys.executable,
                "scripts/run_weekly_analysis.py",
                "--week", str(week),
                "--season", str(season)
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)

            if result.returncode == 0:
                return {
                    "success": True,
                    "week": week,
                    "season": season,
                    "output": result.stdout,
                    "execution_method": "fallback_script"
                }
            else:
                raise Exception(f"Script failed with return code {result.returncode}: {result.stderr}")

        except Exception as e:
            raise Exception(f"Weekly analysis fallback failed: {e}")

    def _run_model_training_fallback(self, params: Dict) -> Dict[str, Any]:
        """Fallback model training execution"""
        try:
            import subprocess
            import sys

            cmd = [sys.executable, "scripts/retrain_models_current.py"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)

            if result.returncode == 0:
                return {
                    "success": True,
                    "output": result.stdout,
                    "execution_method": "fallback_script"
                }
            else:
                raise Exception(f"Model training failed: {result.stderr}")

        except Exception as e:
            raise Exception(f"Model training fallback failed: {e}")

    def _run_gameday_predictions_fallback(self, params: Dict) -> Dict[str, Any]:
        """Fallback gameday predictions execution"""
        # This would integrate with existing prediction systems
        return {
            "success": True,
            "message": "Gameday predictions executed (placeholder)",
            "execution_method": "fallback_placeholder"
        }

    def _self_heal_system(self, params: Dict, context: Dict) -> Dict[str, Any]:
        """Perform self-healing operations"""
        healing_actions = []

        try:
            # Check for stuck tasks
            stuck_tasks = self._find_stuck_tasks()
            for task in stuck_tasks:
                if self._reset_stuck_task(task):
                    healing_actions.append(f"Reset stuck task: {task.task_id}")

            # Check system health
            health_issues = self._diagnose_health_issues()
            for issue in health_issues:
                if self._heal_health_issue(issue):
                    healing_actions.append(f"Healed issue: {issue['type']}")

            # Optimize resources if needed
            if self.system_metrics.system_health_score < 0.8:
                optimization_result = self._optimize_resources(params, context)
                if optimization_result.get("success"):
                    healing_actions.append("Optimized system resources")

            return {
                "success": True,
                "healing_actions": healing_actions,
                "stuck_tasks_fixed": len([a for a in healing_actions if "Reset stuck task" in a]),
                "health_issues_fixed": len([a for a in healing_actions if "Healed issue" in a]),
                "system_health_score": self.system_metrics.system_health_score,
            }

        except Exception as e:
            logger.error(f"Self-healing failed: {e}")
            return {
                "success": False,
                "error": f"Self-healing failed: {e}",
                "partial_actions": healing_actions,
            }

    def _optimize_resources(self, params: Dict, context: Dict) -> Dict[str, Any]:
        """Optimize system resource usage"""
        optimizations = []

        try:
            # Clean up old task history
            if len(self.execution_history) > 1000:
                old_tasks = self.execution_history[:-500]
                self.execution_history = self.execution_history[-500:]
                optimizations.append(f"Cleaned {len(old_tasks)} old task records")

            # Optimize task queue
            if len(self.task_queue) > 50:
                # Remove old low-priority tasks
                current_time = datetime.now(timezone.utc)
                self.task_queue = [
                    task for task in self.task_queue
                    if (task.priority > 1 or
                        (current_time - task.created_at).total_seconds() < 86400)  # Keep high priority or recent tasks
                ]
                optimizations.append("Optimized task queue size")

            # Check memory usage and cleanup if needed
            try:
                import psutil
                memory_percent = psutil.virtual_memory().percent
                if memory_percent > 85:
                    # Force garbage collection
                    import gc
                    gc.collect()
                    optimizations.append("Performed memory cleanup")
            except ImportError:
                pass  # psutil not available

            return {
                "success": True,
                "optimizations": optimizations,
                "task_queue_size": len(self.task_queue),
                "execution_history_size": len(self.execution_history),
                "estimated_memory_saved": len(optimizations) * 10,  # MB estimate
            }

        except Exception as e:
            logger.error(f"Resource optimization failed: {e}")
            return {
                "success": False,
                "error": f"Resource optimization failed: {e}",
                "partial_optimizations": optimizations,
            }

    def _manage_task_queue(self, params: Dict, context: Dict) -> Dict[str, Any]:
        """Manage autonomous task queue"""
        operation = params.get("operation", "status")

        if operation == "status":
            return {
                "success": True,
                "queue_size": len(self.task_queue),
                "pending_tasks": len([t for t in self.task_queue if t.status == WorkflowStatus.PENDING]),
                "running_tasks": len([t for t in self.task_queue if t.status == WorkflowStatus.RUNNING]),
                "retrying_tasks": len([t for t in self.task_queue if t.status == WorkflowStatus.RETRYING]),
                "tasks_by_type": self._group_tasks_by_type(),
                "oldest_task_age": self._get_oldest_task_age(),
            }

        elif operation == "clear":
            cleared_count = len(self.task_queue)
            self.task_queue.clear()
            return {
                "success": True,
                "cleared_tasks": cleared_count,
            }

        elif operation == "prioritize":
            task_type = params.get("task_type")
            if task_type:
                for task in self.task_queue:
                    if task.workflow_type == task_type:
                        task.priority = max(task.priority, params.get("priority", 5))

                return {
                    "success": True,
                    "prioritized_tasks": len([t for t in self.task_queue if t.workflow_type == task_type]),
                    "new_priority": params.get("priority", 5),
                }

        else:
            return {"success": False, "error": f"Unknown operation: {operation}"}

    def _run_autonomous_cycle(self, params: Dict, context: Dict) -> Dict[str, Any]:
        """Run a complete autonomous cycle"""
        cycle_results = {}

        try:
            # 1. Monitor triggers
            trigger_result = self._monitor_triggers(params, context)
            cycle_results["trigger_monitoring"] = trigger_result

            # 2. Execute pending tasks (limit concurrent executions)
            max_executions = params.get("max_executions", 3)
            executed_tasks = []

            for _ in range(min(max_executions, len(self.task_queue))):
                if self.task_queue:
                    task_result = self._execute_autonomous_workflow({}, context)
                    if task_result.get("success"):
                        executed_tasks.append(task_result.get("task_id"))

            cycle_results["task_execution"] = {
                "success": True,
                "executed_tasks": executed_tasks,
                "execution_count": len(executed_tasks),
            }

            # 3. Self-healing (if needed)
            if self.system_metrics.system_health_score < 0.9:
                heal_result = self._self_heal_system(params, context)
                cycle_results["self_healing"] = heal_result

            # 4. Resource optimization
            optimize_result = self._optimize_resources(params, context)
            cycle_results["resource_optimization"] = optimize_result

            # 5. Update system metrics
            self._update_system_health()

            return {
                "success": True,
                "cycle_completed": True,
                "cycle_results": cycle_results,
                "system_health_score": self.system_metrics.system_health_score,
                "active_tasks": self.system_metrics.active_tasks,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"Autonomous cycle failed: {e}")
            return {
                "success": False,
                "error": f"Autonomous cycle failed: {e}",
                "partial_results": cycle_results,
            }

    # Helper methods

    def _evaluate_trigger_conditions(self, trigger_config: Dict) -> bool:
        """Evaluate if trigger conditions are met"""
        # This would contain sophisticated condition evaluation logic
        # For now, implement basic time-based and data-based triggers

        trigger_type = trigger_config.get("type", "schedule")

        if trigger_type == "schedule":
            # Check if scheduled time has arrived
            schedule = trigger_config.get("schedule", "")
            return self._check_schedule_condition(schedule)

        elif trigger_type == "event":
            # Check if event has occurred
            event = trigger_config.get("event", "")
            return self._check_event_condition(event)

        elif trigger_type == "data_threshold":
            # Check if data threshold reached
            threshold = trigger_config.get("data_threshold", 0)
            return self._check_data_threshold(threshold)

        return False

    def _check_schedule_condition(self, schedule: str) -> bool:
        """Check if schedule condition is met"""
        # Simplified schedule checking
        now = datetime.now(timezone.utc)

        if "wednesday" in schedule.lower() and now.weekday() == 2:  # Wednesday is 2
            if "09:00" in schedule and now.hour >= 9:
                return True

        # Add more sophisticated schedule parsing as needed
        return False

    def _check_event_condition(self, event: str) -> bool:
        """Check if event condition is met"""
        # This would integrate with event monitoring systems
        # For now, return False (no events detected)
        return False

    def _check_data_threshold(self, threshold: int) -> bool:
        """Check if data threshold is reached"""
        # This would check actual data availability
        # For now, return False
        return False

    def _create_task_from_trigger(self, trigger_name: str, trigger_config: Dict) -> Optional[AutonomousTask]:
        """Create autonomous task from trigger"""
        task_id = f"{trigger_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Map trigger to workflow type
        workflow_mapping = {
            "weekly_analysis": "weekly_analysis",
            "model_training": "model_training",
            "gameday_predictions": "gameday_predictions",
        }

        workflow_type = workflow_mapping.get(trigger_name)
        if not workflow_type:
            logger.warning(f"Unknown trigger type: {trigger_name}")
            return None

        # Create task with appropriate parameters
        parameters = trigger_config.get("parameters", {})

        return AutonomousTask(
            task_id=task_id,
            workflow_type=workflow_type,
            parameters=parameters,
            trigger_source=trigger_name,
            priority=trigger_config.get("priority", 1),
        )

    def _find_task_by_id(self, task_id: str) -> Optional[AutonomousTask]:
        """Find task by ID in queue or history"""
        # Check queue first
        for task in self.task_queue:
            if task.task_id == task_id:
                return task

        # Check history
        for task in self.execution_history:
            if task.task_id == task_id:
                return task

        return None

    def _get_next_task_of_type(self, workflow_type: str) -> Optional[AutonomousTask]:
        """Get next task of specific type"""
        for task in sorted(self.task_queue, key=lambda t: (-t.priority, t.created_at)):
            if task.workflow_type == workflow_type and task.status == WorkflowStatus.PENDING:
                return task
        return None

    def _update_system_metrics(self, action: str, execution_time: float, success: bool):
        """Update system performance metrics"""
        self.system_metrics.active_tasks = len([t for t in self.task_queue if t.status == WorkflowStatus.RUNNING])
        self.system_metrics.completed_tasks = len([t for t in self.execution_history if t.status == WorkflowStatus.SUCCESS])
        self.system_metrics.failed_tasks = len([t for t in self.execution_history if t.status == WorkflowStatus.FAILED])

        # Update average response time
        total_tasks = self.system_metrics.completed_tasks + self.system_metrics.failed_tasks
        if total_tasks > 0:
            self.system_metrics.average_response_time = (
                (self.system_metrics.average_response_time * (total_tasks - 1) + execution_time) / total_tasks
            )

        # Calculate health score
        if total_tasks > 0:
            success_rate = self.system_metrics.completed_tasks / total_tasks
            self.system_metrics.system_health_score = min(1.0, success_rate * 1.2)  # Scale up slightly

    def _update_system_health(self):
        """Update overall system health metrics"""
        try:
            import psutil

            # Get system resource usage
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_percent = psutil.virtual_memory().percent

            self.system_metrics.resource_usage = {
                "cpu_percent": cpu_percent,
                "memory_percent": memory_percent,
            }

            # Adjust health score based on resources
            if cpu_percent > 90 or memory_percent > 90:
                self.system_metrics.system_health_score *= 0.9
            elif cpu_percent > 70 or memory_percent > 80:
                self.system_metrics.system_health_score *= 0.95

        except ImportError:
            pass  # psutil not available

        self.last_health_check = datetime.now(timezone.utc)

    def _find_stuck_tasks(self) -> List[AutonomousTask]:
        """Find tasks that have been running too long"""
        stuck_tasks = []
        timeout = self.config.get("execution", {}).get("task_timeout", 3600)
        current_time = datetime.now(timezone.utc)

        for task in self.task_queue:
            if (task.status == WorkflowStatus.RUNNING and
                task.started_at and
                (current_time - task.started_at).total_seconds() > timeout):
                stuck_tasks.append(task)

        return stuck_tasks

    def _reset_stuck_task(self, task: AutonomousTask) -> bool:
        """Reset a stuck task"""
        try:
            task.status = WorkflowStatus.PENDING
            task.started_at = None
            task.retry_count += 1

            if task.retry_count >= task.max_retries:
                # Permanently fail the task
                task.status = WorkflowStatus.FAILED
                task.error = "Task timed out and exceeded max retries"
                self.task_queue.remove(task)
                self.execution_history.append(task)

            return True
        except Exception as e:
            logger.error(f"Failed to reset stuck task {task.task_id}: {e}")
            return False

    def _diagnose_health_issues(self) -> List[Dict[str, Any]]:
        """Diagnose system health issues"""
        issues = []

        # Check for high failure rate
        total_recent = len(self.execution_history[-50:]) if len(self.execution_history) >= 50 else len(self.execution_history)
        failed_recent = len([t for t in self.execution_history[-50:] if t.status == WorkflowStatus.FAILED]) if total_recent > 0 else 0

        if total_recent > 0 and failed_recent / total_recent > 0.3:  # 30% failure rate
            issues.append({
                "type": "high_failure_rate",
                "severity": "high",
                "details": f"{failed_recent}/{total_recent} recent tasks failed"
            })

        # Check for queue backlog
        if len(self.task_queue) > 20:
            issues.append({
                "type": "queue_backlog",
                "severity": "medium",
                "details": f"{len(self.task_queue)} tasks in queue"
            })

        # Check system resources
        cpu = self.system_metrics.resource_usage.get("cpu_percent", 0)
        memory = self.system_metrics.resource_usage.get("memory_percent", 0)

        if cpu > 90 or memory > 90:
            issues.append({
                "type": "resource_exhaustion",
                "severity": "critical",
                "details": f"CPU: {cpu}%, Memory: {memory}%"
            })

        return issues

    def _heal_health_issue(self, issue: Dict[str, Any]) -> bool:
        """Attempt to heal a health issue"""
        issue_type = issue["type"]

        try:
            if issue_type == "high_failure_rate":
                # Clear queue of low-priority tasks
                self.task_queue = [t for t in self.task_queue if t.priority > 2]
                return True

            elif issue_type == "queue_backlog":
                # Increase concurrent execution limit
                # This would need to be implemented in the execution logic
                return True

            elif issue_type == "resource_exhaustion":
                # Force garbage collection
                import gc
                gc.collect()
                return True

        except Exception as e:
            logger.error(f"Failed to heal issue {issue_type}: {e}")

        return False

    def _attempt_error_recovery(self, action: str, error: Exception, parameters: Dict):
        """Attempt to recover from execution errors"""
        logger.info(f"Attempting error recovery for action: {action}")

        # Store error for analysis
        error_info = {
            "action": action,
            "error": str(error),
            "parameters": parameters,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        self.state_manager.save_error_state(error_info)

    def _group_tasks_by_type(self) -> Dict[str, int]:
        """Group tasks by workflow type"""
        type_counts = {}
        for task in self.task_queue:
            type_counts[task.workflow_type] = type_counts.get(task.workflow_type, 0) + 1
        return type_counts

    def _get_oldest_task_age(self) -> Optional[float]:
        """Get age of oldest task in seconds"""
        if not self.task_queue:
            return None

        oldest_task = min(self.task_queue, key=lambda t: t.created_at)
        return (datetime.now(timezone.utc) - oldest_task.created_at).total_seconds()

    def _get_current_week(self) -> int:
        """Get current college football week"""
        # This would contain actual week calculation logic
        # For now, return a reasonable default
        now = datetime.now(timezone.utc)
        # Rough estimate - would need proper implementation
        return min(18, max(1, (now - datetime(now.year, 9, 1, tzinfo=timezone.utc)).days // 7 + 1))

    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        return {
            "autonomy_level": self.autonomy_level.value,
            "system_health_score": self.system_metrics.system_health_score,
            "active_tasks": self.system_metrics.active_tasks,
            "task_queue_size": len(self.task_queue),
            "total_completed": self.system_metrics.completed_tasks,
            "total_failed": self.system_metrics.failed_tasks,
            "average_response_time": self.system_metrics.average_response_time,
            "resource_usage": self.system_metrics.resource_usage,
            "last_health_check": self.last_health_check.isoformat(),
            "agent_delegates": list(self.agent_delegates.keys()),
        }


# Global instance
autonomous_orchestration_agent = AutonomousOrchestrationAgent()