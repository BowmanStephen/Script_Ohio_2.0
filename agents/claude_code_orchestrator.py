"""
Claude Code Plan-then-Execute Orchestrator

Main orchestrator that separates strategic planning from tactical implementation.
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from agents.claude_code_subagent_registry import SubagentRegistry
from agents.core.agent_framework import AgentCapability, BaseAgent, PermissionLevel
from agents.core.plan_generator import ExecutionPlan, PlanGenerator
from agents.core.task_delegator import TaskDelegator

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """Result of plan execution"""

    execution_id: str
    plan_id: str
    status: str  # "success", "failed", "partial"
    tasks_completed: int
    tasks_failed: int
    total_tasks: int
    results: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    execution_time: float = 0.0
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None


class PlanThenExecuteOrchestrator(BaseAgent):
    """
    Plan-then-Execute Orchestrator for Claude Code integration.

    Separates strategic planning from tactical implementation:
    - Planning Phase: Analyzes objectives and creates execution plans
    - Execution Phase: Delegates tasks to specialized subagents
    """

    def __init__(self, agent_id: str = "claude_code_orchestrator"):
        """Initialize the orchestrator"""
        super().__init__(
            agent_id=agent_id,
            name="Claude Code Plan-then-Execute Orchestrator",
            permission_level=PermissionLevel.ADMIN,
        )

        # Initialize subagent registry
        self.subagent_registry = SubagentRegistry()

        # Initialize planning and delegation components
        self.plan_generator = PlanGenerator(self.subagent_registry)
        self.task_delegator = TaskDelegator(self.subagent_registry)

        # Execution history
        self.execution_history: List[ExecutionResult] = []

        logger.info("PlanThenExecuteOrchestrator initialized")

    def _define_capabilities(self) -> List[AgentCapability]:
        """Define orchestrator capabilities"""
        return [
            AgentCapability(
                name="plan_phase",
                description="Generate strategic execution plan from high-level objective",
                permission_required=PermissionLevel.ADMIN,
                tools_required=["planning", "analysis"],
                data_access=["subagent_registry"],
                execution_time_estimate=5.0,
            ),
            AgentCapability(
                name="execute_phase",
                description="Execute plan by delegating tasks to subagents",
                permission_required=PermissionLevel.ADMIN,
                tools_required=["task_delegation", "subagent_execution"],
                data_access=["subagent_registry", "execution_history"],
                execution_time_estimate=10.0,
            ),
            AgentCapability(
                name="plan_and_execute",
                description="Complete Plan-then-Execute workflow",
                permission_required=PermissionLevel.ADMIN,
                tools_required=["planning", "task_delegation"],
                data_access=["subagent_registry", "execution_history"],
                execution_time_estimate=15.0,
            ),
        ]

    def _execute_action(
        self, action: str, parameters: Dict[str, Any], user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute orchestrator actions"""
        try:
            if action == "plan_phase":
                return self._plan_phase(parameters, user_context)
            elif action == "execute_phase":
                return self._execute_phase(parameters, user_context)
            elif action == "plan_and_execute":
                return self._plan_and_execute(parameters, user_context)
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}",
                    "available_actions": [
                        cap.name for cap in self._define_capabilities()
                    ],
                }
        except Exception as e:
            logger.error(f"Error executing action {action}: {e}")
            return {
                "success": False,
                "error": str(e),
                "action": action,
            }

    def _plan_phase(
        self, parameters: Dict[str, Any], user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Planning phase: Generate execution plan from objective.

        Args:
            parameters: Must contain 'objective' key
            user_context: User context

        Returns:
            Execution plan
        """
        objective = parameters.get("objective")
        if not objective:
            return {"success": False, "error": "Missing 'objective' parameter"}

        context = parameters.get("context", {})

        # Generate plan
        plan = self.plan_generator.generate_plan(objective, context)

        # Validate plan
        validation_errors = plan.validate()
        if validation_errors:
            return {
                "success": False,
                "error": "Plan validation failed",
                "validation_errors": validation_errors,
                "plan": plan,
            }

        return {
            "success": True,
            "plan": plan,
            "plan_id": plan.plan_id,
            "task_count": len(plan.tasks),
            "estimated_time": plan.estimated_total_time,
        }

    def _execute_phase(
        self, parameters: Dict[str, Any], user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execution phase: Execute plan by delegating tasks to subagents.

        Args:
            parameters: Must contain 'plan' or 'plan_id' key
            user_context: User context

        Returns:
            Execution result
        """
        import time

        start_time = time.time()

        # Get plan
        plan = parameters.get("plan")
        if not plan:
            plan_id = parameters.get("plan_id")
            if plan_id:
                # In production, retrieve plan from storage
                return {"success": False, "error": "Plan retrieval not implemented"}
            else:
                return {
                    "success": False,
                    "error": "Missing 'plan' or 'plan_id' parameter",
                }

        if not isinstance(plan, ExecutionPlan):
            return {"success": False, "error": "Invalid plan format"}

        # Create execution result
        execution_id = str(uuid.uuid4())
        result = ExecutionResult(
            execution_id=execution_id,
            plan_id=plan.plan_id,
            status="running",
            tasks_completed=0,
            tasks_failed=0,
            total_tasks=len(plan.tasks),
        )

        context = parameters.get("context", {})

        # Execute tasks
        if plan.parallel_execution:
            task_results = self.task_delegator.delegate_tasks_parallel(
                plan.tasks, context
            )
        else:
            task_results = self.task_delegator.delegate_tasks_sequential(
                plan.tasks, context
            )

        # Process results
        result.results = task_results
        result.tasks_completed = sum(1 for r in task_results if r.get("success"))
        result.tasks_failed = sum(1 for r in task_results if not r.get("success"))

        # Collect errors
        result.errors = [
            r.get("error", "Unknown error")
            for r in task_results
            if not r.get("success")
        ]

        # Determine final status
        if result.tasks_failed == 0:
            result.status = "success"
        elif result.tasks_completed == 0:
            result.status = "failed"
        else:
            result.status = "partial"

        result.execution_time = time.time() - start_time
        result.completed_at = datetime.now()

        # Store in history
        self.execution_history.append(result)

        return {
            "success": result.status != "failed",
            "execution_id": execution_id,
            "result": result,
            "tasks_completed": result.tasks_completed,
            "tasks_failed": result.tasks_failed,
            "execution_time": result.execution_time,
        }

    def _plan_and_execute(
        self, parameters: Dict[str, Any], user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Complete Plan-then-Execute workflow: plan then execute.

        Args:
            parameters: Must contain 'objective' key
            user_context: User context

        Returns:
            Combined planning and execution result
        """
        # Planning phase
        plan_result = self._plan_phase(parameters, user_context)
        if not plan_result.get("success"):
            return plan_result

        plan = plan_result["plan"]

        # Execution phase
        exec_result = self._execute_phase({"plan": plan, **parameters}, user_context)

        return {
            "success": exec_result.get("success", False),
            "plan": plan,
            "execution": exec_result,
            "plan_id": plan.plan_id,
            "execution_id": exec_result.get("execution_id"),
        }

    def plan_phase(
        self, objective: str, context: Optional[Dict[str, Any]] = None
    ) -> ExecutionPlan:
        """
        Public method for planning phase.

        Args:
            objective: High-level objective
            context: Optional context

        Returns:
            ExecutionPlan
        """
        result = self._plan_phase(
            {"objective": objective, "context": context or {}}, {}
        )
        if not result.get("success"):
            raise ValueError(f"Planning failed: {result.get('error')}")
        return result["plan"]

    def execute_phase(
        self, plan: ExecutionPlan, context: Optional[Dict[str, Any]] = None
    ) -> ExecutionResult:
        """
        Public method for execution phase.

        Args:
            plan: ExecutionPlan to execute
            context: Optional context

        Returns:
            ExecutionResult
        """
        result = self._execute_phase({"plan": plan, "context": context or {}}, {})
        if not result.get("success"):
            raise ValueError(f"Execution failed: {result.get('error')}")
        return result["result"]
