"""
Task Manager - Manages task distribution, execution, and monitoring
Following Claude's best practices for task orchestration
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
import logging

from base_agent import AgentTask, AgentMessage, PermissionLevel

class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"

class TaskPriority(Enum):
    """Task priority levels"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4

@dataclass
class TaskExecution:
    """Task execution record with detailed tracking"""
    task_id: str
    agent_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None
    retry_count: int = 0
    logs: List[str] = field(default_factory=list)

class TaskManager:
    """
    Advanced task management system following Claude's best practices:
    - Efficient task distribution
    - Comprehensive monitoring
    - Robust error handling
    - Priority-based scheduling
    """

    def __init__(self, max_concurrent_tasks: int = 10):
        self.max_concurrent_tasks = max_concurrent_tasks
        self.logger = logging.getLogger("task_manager")

        # Task storage and queues
        self.task_queue = asyncio.PriorityQueue()
        self.active_tasks: Dict[str, TaskExecution] = {}
        self.completed_tasks: Dict[str, TaskExecution] = {}
        self.failed_tasks: Dict[str, TaskExecution] = {}

        # Task scheduling
        self.task_schedulers = {}
        self.task_dependencies = {}  # task_id -> [dependent_task_ids]

        # Performance tracking
        self.metrics = {
            "total_tasks_created": 0,
            "total_tasks_completed": 0,
            "total_tasks_failed": 0,
            "average_execution_time": 0.0,
            "queue_size": 0,
            "active_count": 0
        }

        # Event handlers
        self.task_created_handlers = []
        self.task_completed_handlers = []
        self.task_failed_handlers = []

        self.logger.info(f"TaskManager initialized with max_concurrent_tasks={max_concurrent_tasks}")

    async def submit_task(self, task: AgentTask,
                         priority: TaskPriority = TaskPriority.MEDIUM) -> str:
        """
        Submit a task for execution with priority scheduling

        Args:
            task: The task to execute
            priority: Task priority level

        Returns:
            Task ID for tracking
        """
        try:
            # Generate unique task ID if not provided
            if not task.task_id:
                task.task_id = str(uuid.uuid4())

            # Validate task
            if not self._validate_task(task):
                raise ValueError(f"Invalid task: {task}")

            # Add to priority queue (lower number = higher priority)
            queue_item = (priority.value, task.task_id, task)
            await self.task_queue.put(queue_item)

            # Update metrics
            self.metrics["total_tasks_created"] += 1
            self.metrics["queue_size"] = self.task_queue.qsize()

            # Log task creation
            self.logger.info(f"Task {task.task_id} submitted with priority {priority.name}")

            # Notify handlers
            await self._notify_task_created(task)

            return task.task_id

        except Exception as e:
            self.logger.error(f"Error submitting task: {e}")
            raise

    async def get_next_task(self, agent_id: str) -> Optional[AgentTask]:
        """
        Get the next available task for execution

        Args:
            agent_id: ID of the requesting agent

        Returns:
            Next task or None if no tasks available
        """
        try:
            # Check if agent can take more tasks
            if len(self.active_tasks) >= self.max_concurrent_tasks:
                self.logger.debug("Max concurrent tasks reached")
                return None

            # Get next task from queue
            try:
                priority, task_id, task = await asyncio.wait_for(
                    self.task_queue.get(), timeout=1.0
                )
            except asyncio.TimeoutError:
                return None

            # Check task dependencies
            if not self._check_task_dependencies(task):
                # Re-queue task for later
                await self.task_queue.put((priority, task_id, task))
                return None

            # Create task execution record
            execution = TaskExecution(
                task_id=task.task_id,
                agent_id=agent_id,
                start_time=datetime.now(),
                status=TaskStatus.IN_PROGRESS
            )

            self.active_tasks[task.task_id] = execution
            self.metrics["active_count"] = len(self.active_tasks)

            # Update task status
            task.status = "in_progress"

            self.logger.info(f"Task {task.task_id} assigned to agent {agent_id}")
            return task

        except Exception as e:
            self.logger.error(f"Error getting next task: {e}")
            return None

    def complete_task(self, task_id: str, result: Dict[str, Any]) -> bool:
        """
        Mark a task as completed with results

        Args:
            task_id: ID of the task
            result: Task execution result

        Returns:
            True if successful, False otherwise
        """
        try:
            if task_id not in self.active_tasks:
                self.logger.warning(f"Task {task_id} not found in active tasks")
                return False

            # Update execution record
            execution = self.active_tasks.pop(task_id)
            execution.end_time = datetime.now()
            execution.status = TaskStatus.COMPLETED
            execution.result = result
            execution.execution_time = (execution.end_time - execution.start_time).total_seconds()

            # Move to completed tasks
            self.completed_tasks[task_id] = execution

            # Update metrics
            self.metrics["total_tasks_completed"] += 1
            self.metrics["active_count"] = len(self.active_tasks)
            self._update_average_execution_time(execution.execution_time)

            # Clean up old completed tasks (keep last 1000)
            if len(self.completed_tasks) > 1000:
                oldest_tasks = sorted(
                    self.completed_tasks.items(),
                    key=lambda x: x[1].end_time or datetime.min
                )[:100]
                for old_task_id, _ in oldest_tasks:
                    del self.completed_tasks[old_task_id]

            # Log completion
            self.logger.info(f"Task {task_id} completed successfully in {execution.execution_time:.2f}s")

            # Notify handlers
            asyncio.create_task(self._notify_task_completed(task_id, result))

            return True

        except Exception as e:
            self.logger.error(f"Error completing task {task_id}: {e}")
            return False

    def fail_task(self, task_id: str, error: str,
                  retry: bool = True) -> bool:
        """
        Mark a task as failed with optional retry

        Args:
            task_id: ID of the task
            error: Error description
            retry: Whether to retry the task

        Returns:
            True if successful, False otherwise
        """
        try:
            if task_id not in self.active_tasks:
                self.logger.warning(f"Task {task_id} not found in active tasks")
                return False

            execution = self.active_tasks.pop(task_id)
            execution.end_time = datetime.now()
            execution.error = error

            if retry and execution.retry_count < 3:
                # Retry the task
                execution.retry_count += 1
                execution.status = TaskStatus.PENDING
                execution.logs.append(f"Retry {execution.retry_count}: {error}")

                # Re-queue with higher priority
                priority = TaskPriority.HIGH if execution.retry_count == 1 else TaskPriority.CRITICAL
                retry_task = AgentTask(
                    task_id=task_id,
                    agent_id=execution.agent_id,
                    action=execution.result.get('action', 'retry') if execution.result else 'retry',
                    parameters=execution.result.get('parameters', {}) if execution.result else {},
                    target_files=[],
                    priority=priority.value,
                    retry_attempts=3 - execution.retry_count
                )

                asyncio.create_task(self.submit_task(retry_task, priority))

                self.logger.info(f"Task {task_id} queued for retry {execution.retry_count}")
                return True
            else:
                # Mark as failed
                execution.status = TaskStatus.FAILED
                execution.execution_time = (execution.end_time - execution.start_time).total_seconds()

                self.failed_tasks[task_id] = execution

                # Update metrics
                self.metrics["total_tasks_failed"] += 1
                self.metrics["active_count"] = len(self.active_tasks)

                # Clean up old failed tasks (keep last 500)
                if len(self.failed_tasks) > 500:
                    oldest_tasks = sorted(
                        self.failed_tasks.items(),
                        key=lambda x: x[1].end_time or datetime.min
                    )[:100]
                    for old_task_id, _ in oldest_tasks:
                        del self.failed_tasks[old_task_id]

                # Log failure
                self.logger.error(f"Task {task_id} failed permanently: {error}")

                # Notify handlers
                asyncio.create_task(self._notify_task_failed(task_id, error))

                return True

        except Exception as e:
            self.logger.error(f"Error failing task {task_id}: {e}")
            return False

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get the current status of a task"""
        if task_id in self.active_tasks:
            execution = self.active_tasks[task_id]
            return {
                "task_id": task_id,
                "status": execution.status.value,
                "agent_id": execution.agent_id,
                "start_time": execution.start_time.isoformat(),
                "execution_time": (datetime.now() - execution.start_time).total_seconds(),
                "retry_count": execution.retry_count
            }
        elif task_id in self.completed_tasks:
            execution = self.completed_tasks[task_id]
            return {
                "task_id": task_id,
                "status": execution.status.value,
                "agent_id": execution.agent_id,
                "start_time": execution.start_time.isoformat(),
                "end_time": execution.end_time.isoformat() if execution.end_time else None,
                "execution_time": execution.execution_time,
                "retry_count": execution.retry_count,
                "result": execution.result
            }
        elif task_id in self.failed_tasks:
            execution = self.failed_tasks[task_id]
            return {
                "task_id": task_id,
                "status": execution.status.value,
                "agent_id": execution.agent_id,
                "start_time": execution.start_time.isoformat(),
                "end_time": execution.end_time.isoformat() if execution.end_time else None,
                "execution_time": execution.execution_time,
                "retry_count": execution.retry_count,
                "error": execution.error,
                "logs": execution.logs
            }
        else:
            return None

    def get_metrics(self) -> Dict[str, Any]:
        """Get comprehensive task management metrics"""
        # Calculate success rate
        total_completed = self.metrics["total_tasks_completed"] + self.metrics["total_tasks_failed"]
        success_rate = (self.metrics["total_tasks_completed"] / max(total_completed, 1)) * 100

        # Calculate queue health
        queue_health = "good"
        if self.task_queue.qsize() > self.max_concurrent_tasks * 2:
            queue_health = "overloaded"
        elif self.task_queue.qsize() > self.max_concurrent_tasks:
            queue_health = "busy"

        return {
            **self.metrics,
            "queue_size": self.task_queue.qsize(),
            "queue_health": queue_health,
            "success_rate": success_rate,
            "active_tasks": len(self.active_tasks),
            "completed_tasks": len(self.completed_tasks),
            "failed_tasks": len(self.failed_tasks),
            "timestamp": datetime.now().isoformat()
        }

    def _validate_task(self, task: AgentTask) -> bool:
        """Validate task structure and content"""
        if not task.task_id:
            return False

        if not task.agent_id:
            return False

        if not task.action:
            return False

        return True

    def _check_task_dependencies(self, task: AgentTask) -> bool:
        """Check if task dependencies are satisfied"""
        if not task.dependencies:
            return True

        for dep_task_id in task.dependencies:
            dep_status = self.get_task_status(dep_task_id)
            if not dep_status or dep_status["status"] != "completed":
                return False

        return True

    def _update_average_execution_time(self, execution_time: float) -> None:
        """Update average execution time metric"""
        total_completed = self.metrics["total_tasks_completed"]
        if total_completed == 1:
            self.metrics["average_execution_time"] = execution_time
        else:
            current_avg = self.metrics["average_execution_time"]
            self.metrics["average_execution_time"] = (
                (current_avg * (total_completed - 1) + execution_time) / total_completed
            )

    async def _notify_task_created(self, task: AgentTask) -> None:
        """Notify task created event handlers"""
        for handler in self.task_created_handlers:
            try:
                await handler(task)
            except Exception as e:
                self.logger.error(f"Error in task created handler: {e}")

    async def _notify_task_completed(self, task_id: str, result: Dict[str, Any]) -> None:
        """Notify task completed event handlers"""
        for handler in self.task_completed_handlers:
            try:
                await handler(task_id, result)
            except Exception as e:
                self.logger.error(f"Error in task completed handler: {e}")

    async def _notify_task_failed(self, task_id: str, error: str) -> None:
        """Notify task failed event handlers"""
        for handler in self.task_failed_handlers:
            try:
                await handler(task_id, error)
            except Exception as e:
                self.logger.error(f"Error in task failed handler: {e}")

    def add_task_created_handler(self, handler: Callable) -> None:
        """Add handler for task created events"""
        self.task_created_handlers.append(handler)

    def add_task_completed_handler(self, handler: Callable) -> None:
        """Add handler for task completed events"""
        self.task_completed_handlers.append(handler)

    def add_task_failed_handler(self, handler: Callable) -> None:
        """Add handler for task failed events"""
        self.task_failed_handlers.append(handler)

    async def shutdown(self) -> Dict[str, Any]:
        """Graceful shutdown of task manager"""
        try:
            self.logger.info("TaskManager shutting down gracefully")

            # Cancel all active tasks
            active_task_ids = list(self.active_tasks.keys())
            for task_id in active_task_ids:
                self.fail_task(task_id, "Task manager shutdown", retry=False)

            # Save final metrics
            shutdown_info = {
                "final_metrics": self.get_metrics(),
                "active_tasks_cancelled": len(active_task_ids),
                "shutdown_time": datetime.now().isoformat()
            }

            # Save to log
            with open("logs/task_manager_shutdown.json", 'w') as f:
                json.dump(shutdown_info, f, indent=2)

            self.logger.info("TaskManager shutdown complete")
            return shutdown_info

        except Exception as e:
            self.logger.error(f"Error during TaskManager shutdown: {e}")
            return {
                "error": str(e),
                "shutdown_time": datetime.now().isoformat()
            }