"""
Plan Generator - Strategic Planning Component

Analyzes high-level objectives and creates structured execution plans.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class Task:
    """Represents a single task in an execution plan"""

    task_id: str
    name: str
    description: str
    assigned_subagent: str
    dependencies: List[str] = field(default_factory=list)
    priority: int = 3  # 1=critical, 2=high, 3=normal, 4=low
    estimated_time: float = 0.0  # in seconds
    parameters: Dict[str, Any] = field(default_factory=dict)
    validation_criteria: List[str] = field(default_factory=list)


@dataclass
class ExecutionPlan:
    """Structured execution plan with tasks and metadata"""

    plan_id: str
    objective: str
    tasks: List[Task] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    estimated_total_time: float = 0.0
    parallel_execution: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> List[str]:
        """
        Validate the execution plan.

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        if not self.objective:
            errors.append("Plan must have an objective")

        if not self.tasks:
            errors.append("Plan must have at least one task")

        # Check for circular dependencies
        task_ids = {task.task_id for task in self.tasks}
        for task in self.tasks:
            for dep in task.dependencies:
                if dep not in task_ids:
                    errors.append(f"Task {task.task_id} has invalid dependency: {dep}")
                if dep == task.task_id:
                    errors.append(f"Task {task.task_id} depends on itself")

        # Check that all subagents are valid
        for task in self.tasks:
            if not task.assigned_subagent:
                errors.append(f"Task {task.task_id} has no assigned subagent")

        return errors


class PlanGenerator:
    """
    Generates structured execution plans from high-level objectives.

    Uses high-reasoning model to analyze objectives and break them down
    into discrete, actionable tasks assigned to specialized subagents.
    """

    def __init__(self, subagent_registry):
        """
        Initialize the plan generator.

        Args:
            subagent_registry: SubagentRegistry instance for subagent lookup
        """
        self.subagent_registry = subagent_registry

    def generate_plan(
        self, objective: str, context: Optional[Dict[str, Any]] = None
    ) -> ExecutionPlan:
        """
        Generate an execution plan from a high-level objective.

        Args:
            objective: High-level objective description
            context: Optional context information

        Returns:
            ExecutionPlan with tasks assigned to subagents
        """
        logger.info(f"Generating plan for objective: {objective}")

        # Simple plan generation logic
        # In production, this would use a high-reasoning model to analyze
        # the objective and create a sophisticated plan

        plan_id = f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        plan = ExecutionPlan(plan_id=plan_id, objective=objective)

        # Analyze objective and break down into tasks
        tasks = self._analyze_objective(objective, context or {})

        # Assign tasks to appropriate subagents
        for task in tasks:
            task.assigned_subagent = self._assign_subagent(task)

        plan.tasks = tasks
        plan.estimated_total_time = sum(task.estimated_time for task in tasks)

        # Determine if parallel execution is possible
        plan.parallel_execution = self._can_execute_parallel(plan.tasks)

        logger.info(f"Generated plan with {len(tasks)} tasks")

        return plan

    def _analyze_objective(self, objective: str, context: Dict[str, Any]) -> List[Task]:
        """
        Analyze objective and break down into tasks.

        This is a simplified implementation. In production, this would use
        a high-reasoning model to perform sophisticated analysis.

        Args:
            objective: High-level objective
            context: Context information

        Returns:
            List of tasks
        """
        tasks = []

        # Simple keyword-based task generation
        # In production, use LLM to analyze objective

        if "implement" in objective.lower() or "add" in objective.lower():
            tasks.append(
                Task(
                    task_id="task_1",
                    name="Implementation",
                    description=objective,
                    assigned_subagent="",
                    priority=2,
                    estimated_time=300.0,
                )
            )

        if "test" in objective.lower() or "validate" in objective.lower():
            tasks.append(
                Task(
                    task_id="task_2",
                    name="Testing",
                    description=f"Test and validate: {objective}",
                    assigned_subagent="",
                    dependencies=["task_1"] if tasks else [],
                    priority=2,
                    estimated_time=120.0,
                )
            )

        if not tasks:
            # Default task if no keywords match
            tasks.append(
                Task(
                    task_id="task_1",
                    name="Execute",
                    description=objective,
                    assigned_subagent="",
                    priority=3,
                    estimated_time=180.0,
                )
            )

        return tasks

    def _assign_subagent(self, task: Task) -> str:
        """
        Assign a task to an appropriate subagent.

        Args:
            task: Task to assign

        Returns:
            Subagent name
        """
        available_subagents = self.subagent_registry.list_subagents()

        # Simple assignment logic based on task name
        # In production, use more sophisticated matching

        task_lower = task.name.lower()

        if "test" in task_lower or "qa" in task_lower or "validate" in task_lower:
            if "QA Engineer" in available_subagents:
                return "QA Engineer"

        if (
            "implement" in task_lower
            or "code" in task_lower
            or "engineer" in task_lower
        ):
            if "Senior Engineer" in available_subagents:
                return "Senior Engineer"
            if "Executor" in available_subagents:
                return "Executor"

        if "plan" in task_lower or "design" in task_lower:
            if "Planner" in available_subagents:
                return "Planner"
            if "Product Manager" in available_subagents:
                return "Product Manager"

        if "data" in task_lower or "model" in task_lower or "analysis" in task_lower:
            if "Data Scientist" in available_subagents:
                return "Data Scientist"

        if "security" in task_lower or "audit" in task_lower:
            if "Security Auditor" in available_subagents:
                return "Security Auditor"

        # Default to Executor if available
        if "Executor" in available_subagents:
            return "Executor"

        # Fallback to first available subagent
        return available_subagents[0] if available_subagents else ""

    def _can_execute_parallel(self, tasks: List[Task]) -> bool:
        """
        Determine if tasks can be executed in parallel.

        Args:
            tasks: List of tasks

        Returns:
            True if parallel execution is possible
        """
        if len(tasks) <= 1:
            return False

        # Check if any tasks have dependencies
        has_dependencies = any(task.dependencies for task in tasks)

        # If no dependencies, can execute in parallel
        return not has_dependencies
