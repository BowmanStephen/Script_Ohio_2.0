"""
Task Delegator - Task Assignment Component

Assigns tasks from execution plans to appropriate subagents.
"""

import logging
from typing import Any, Dict, List, Optional

from agents.claude_code_subagent_registry import SubagentDefinition, SubagentRegistry

logger = logging.getLogger(__name__)


class TaskDelegator:
    """
    Delegates tasks to appropriate subagents based on execution plans.

    Manages task assignment, monitors execution, and handles results.
    """

    def __init__(self, subagent_registry: SubagentRegistry):
        """
        Initialize the task delegator.

        Args:
            subagent_registry: SubagentRegistry instance
        """
        self.subagent_registry = subagent_registry
        self.active_tasks: Dict[str, Dict[str, Any]] = {}

    def delegate_task(
        self,
        task,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Delegate a task to its assigned subagent.

        Args:
            task: Task from ExecutionPlan
            context: Optional context information

        Returns:
            Task execution result
        """
        logger.info(f"Delegating task {task.task_id} to {task.assigned_subagent}")

        # Get subagent definition
        subagent = self.subagent_registry.get_subagent(task.assigned_subagent)
        if not subagent:
            return {
                "success": False,
                "error": f"Subagent not found: {task.assigned_subagent}",
                "task_id": task.task_id,
            }

        # Track active task
        self.active_tasks[task.task_id] = {
            "task": task,
            "subagent": subagent,
            "status": "running",
            "started_at": None,
        }

        # In production, this would invoke the actual subagent
        # For now, return a mock result
        result = {
            "success": True,
            "task_id": task.task_id,
            "subagent": task.assigned_subagent,
            "result": f"Task {task.name} executed by {task.assigned_subagent}",
            "execution_time": task.estimated_time,
        }

        # Update task status
        self.active_tasks[task.task_id]["status"] = "completed"
        self.active_tasks[task.task_id]["result"] = result

        return result

    def delegate_tasks_parallel(
        self, tasks: List, context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Delegate multiple tasks in parallel.

        Args:
            tasks: List of tasks to delegate
            context: Optional context information

        Returns:
            List of task execution results
        """
        logger.info(f"Delegating {len(tasks)} tasks in parallel")

        results = []
        for task in tasks:
            result = self.delegate_task(task, context)
            results.append(result)

        return results

    def delegate_tasks_sequential(
        self, tasks: List, context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Delegate multiple tasks sequentially, respecting dependencies.

        Args:
            tasks: List of tasks to delegate
            context: Optional context information

        Returns:
            List of task execution results
        """
        logger.info(f"Delegating {len(tasks)} tasks sequentially")

        # Build dependency graph
        task_map = {task.task_id: task for task in tasks}
        completed = set()
        results = []

        # Execute tasks in dependency order
        while len(completed) < len(tasks):
            progress = False

            for task in tasks:
                if task.task_id in completed:
                    continue

                # Check if all dependencies are completed
                if all(dep in completed for dep in task.dependencies):
                    result = self.delegate_task(task, context)
                    results.append(result)
                    completed.add(task.task_id)
                    progress = True

            if not progress:
                # Circular dependency or missing dependency
                remaining = [t.task_id for t in tasks if t.task_id not in completed]
                logger.error(f"Circular dependency or missing dependency: {remaining}")
                break

        return results

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status of an active task.

        Args:
            task_id: Task ID

        Returns:
            Task status or None if not found
        """
        return self.active_tasks.get(task_id)
