"""
Agent Marketplace and Task Distribution System
Provides intelligent task routing, load balancing, and agent discovery
"""

import asyncio
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Set
from dataclasses import dataclass, field, asdict
from enum import Enum
import json
import logging
import heapq
from collections import defaultdict, deque

from .secure_messaging import (
    AgentMessage, MessageType, MessagePriority,
    secure_messaging, message_router, create_message, send_message
)

class AgentStatus(Enum):
    IDLE = "idle"
    BUSY = "busy"
    OVERLOADED = "overloaded"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"

class TaskStatus(Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskPriority(Enum):
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4

@dataclass
class AgentCapability:
    """Defines an agent's capability for task matching"""
    name: str
    category: str
    version: str = "1.0"
    parameters: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    requires_specialization: bool = False

@dataclass
class AgentProfile:
    """Complete profile of an agent in the marketplace"""
    agent_id: str
    name: str
    agent_type: str
    status: AgentStatus = AgentStatus.IDLE
    capabilities: List[AgentCapability] = field(default_factory=list)
    max_concurrent_tasks: int = 5
    current_tasks: int = 0
    performance_rating: float = 5.0
    reliability_score: float = 5.0
    specialization_areas: List[str] = field(default_factory=list)
    resource_requirements: Dict[str, Any] = field(default_factory=dict)
    cost_per_task: float = 0.0
    availability_schedule: Dict[str, Any] = field(default_factory=dict)
    last_heartbeat: datetime = field(default_factory=datetime.now)
    metrics: Dict[str, Any] = field(default_factory=dict)

    def is_available(self) -> bool:
        """Check if agent is available for new tasks"""
        return (self.status == AgentStatus.IDLE and
                self.current_tasks < self.max_concurrent_tasks)

    def can_handle_capability(self, required_capability: str) -> bool:
        """Check if agent can handle a specific capability"""
        return any(cap.name == required_capability for cap in self.capabilities)

@dataclass
class Task:
    """Represents a task to be executed by an agent"""
    task_id: str
    task_type: str
    required_capability: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.MEDIUM
    estimated_duration: int = 60  # seconds
    max_cost: float = float('inf')
    deadline: Optional[datetime] = None
    requester_id: str = ""
    status: TaskStatus = TaskStatus.PENDING
    assigned_agent: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    tags: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)  # task_ids

    def is_expired(self) -> bool:
        """Check if task has passed its deadline"""
        if self.deadline is None:
            return False
        return datetime.now() > self.deadline

    def can_retry(self) -> bool:
        """Check if task can be retried"""
        return self.retry_count < self.max_retries

class AgentMarketplace:
    """Central marketplace for agent discovery and task distribution"""

    def __init__(self):
        self.registered_agents: Dict[str, AgentProfile] = {}
        self.active_tasks: Dict[str, Task] = {}
        self.task_queue: List[Task] = []
        self.completed_tasks: Dict[str, Task] = {}

        # Performance tracking
        self.agent_performance: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        self.task_history: deque = deque(maxlen=1000)  # Last 1000 tasks

        # Load balancing
        self.load_balancing_strategy = "performance_weighted"  # "round_robin", "least_loaded", "performance_weighted"

        # Event handlers
        self.task_handlers: Dict[str, List[Callable]] = defaultdict(list)
        self.agent_handlers: Dict[str, List[Callable]] = defaultdict(list)

        # Background tasks
        self.background_thread = None
        self.running = False

        self.logger = logging.getLogger("agent_marketplace")

        # Start background processing
        self.start_background_processing()

    def register_agent(self, agent_profile: AgentProfile) -> bool:
        """Register an agent in the marketplace"""
        try:
            # Validate agent profile
            if not self._validate_agent_profile(agent_profile):
                return False

            # Register with message router
            message_router.register_agent(agent_profile.agent_id, {
                "endpoint": f"marketplace://{agent_profile.agent_id}",
                "protocol": "marketplace",
                "capabilities": [cap.name for cap in agent_profile.capabilities]
            })

            # Store agent profile
            self.registered_agents[agent_profile.agent_id] = agent_profile

            # Register message handlers
            secure_messaging.register_handler(MessageType.STATUS_UPDATE, self._handle_agent_status_update)
            secure_messaging.register_handler(MessageType.HEARTBEAT, self._handle_agent_heartbeat)

            self.logger.info(f"Agent registered in marketplace: {agent_profile.agent_id}")
            self._trigger_agent_event("agent_registered", agent_profile)

            return True

        except Exception as e:
            self.logger.error(f"Error registering agent {agent_profile.agent_id}: {e}")
            return False

    def unregister_agent(self, agent_id: str) -> bool:
        """Unregister an agent from the marketplace"""
        try:
            if agent_id not in self.registered_agents:
                return False

            # Reassign current tasks
            agent = self.registered_agents[agent_id]
            self._reassign_agent_tasks(agent_id)

            # Remove from marketplace
            del self.registered_agents[agent_id]
            message_router.unregister_agent(agent_id)

            self.logger.info(f"Agent unregistered from marketplace: {agent_id}")
            self._trigger_agent_event("agent_unregistered", {"agent_id": agent_id})

            return True

        except Exception as e:
            self.logger.error(f"Error unregistering agent {agent_id}: {e}")
            return False

    def submit_task(self, task: Task) -> str:
        """Submit a task to the marketplace"""
        try:
            # Validate task
            if not self._validate_task(task):
                raise ValueError("Invalid task")

            # Add to active tasks
            self.active_tasks[task.task_id] = task

            # Add to queue for processing
            heapq.heappush(self.task_queue, (task.priority.value, task.created_at.timestamp(), task))

            self.logger.info(f"Task submitted: {task.task_id} ({task.task_type})")
            self._trigger_task_event("task_submitted", task)

            # Try to assign immediately
            self._process_task_queue()

            return task.task_id

        except Exception as e:
            self.logger.error(f"Error submitting task: {e}")
            raise

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a task"""
        task = self.active_tasks.get(task_id) or self.completed_tasks.get(task_id)
        if task is None:
            return None

        return {
            "task_id": task.task_id,
            "task_type": task.task_type,
            "status": task.status.value,
            "assigned_agent": task.assigned_agent,
            "created_at": task.created_at.isoformat(),
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "priority": task.priority.value,
            "retry_count": task.retry_count,
            "error_message": task.error_message
        }

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a task"""
        task = self.active_tasks.get(task_id)
        if task is None:
            return False

        if task.status in [TaskStatus.COMPLETED, TaskStatus.CANCELLED]:
            return False

        # Update task status
        task.status = TaskStatus.CANCELLED
        task.completed_at = datetime.now()

        # Notify assigned agent
        if task.assigned_agent:
            self._notify_agent_of_cancellation(task)

        # Move to completed
        self.completed_tasks[task_id] = task
        del self.active_tasks[task_id]

        self.logger.info(f"Task cancelled: {task_id}")
        self._trigger_task_event("task_cancelled", task)

        return True

    def find_agents_for_capability(self, capability: str, filter_available: bool = True) -> List[AgentProfile]:
        """Find agents that can handle a specific capability"""
        agents = []

        for agent in self.registered_agents.values():
            if agent.can_handle_capability(capability):
                if not filter_available or agent.is_available():
                    agents.append(agent)

        # Sort by performance rating
        agents.sort(key=lambda a: a.performance_rating, reverse=True)
        return agents

    def get_marketplace_status(self) -> Dict[str, Any]:
        """Get overall marketplace status"""
        total_agents = len(self.registered_agents)
        available_agents = sum(1 for a in self.registered_agents.values() if a.is_available())

        pending_tasks = sum(1 for t in self.active_tasks.values() if t.status == TaskStatus.PENDING)
        in_progress_tasks = sum(1 for t in self.active_tasks.values() if t.status == TaskStatus.IN_PROGRESS)

        return {
            "total_agents": total_agents,
            "available_agents": available_agents,
            "busy_agents": total_agents - available_agents,
            "active_tasks": len(self.active_tasks),
            "pending_tasks": pending_tasks,
            "in_progress_tasks": in_progress_tasks,
            "completed_tasks": len(self.completed_tasks),
            "queue_length": len(self.task_queue),
            "average_task_duration": self._calculate_average_task_duration(),
            "success_rate": self._calculate_success_rate(),
            "system_load": self._calculate_system_load(),
            "capabilities": self._get_capability_summary()
        }

    def _validate_agent_profile(self, agent: AgentProfile) -> bool:
        """Validate agent profile"""
        if not agent.agent_id or not agent.name:
            return False
        if not agent.capabilities:
            return False
        if agent.max_concurrent_tasks <= 0:
            return False
        return True

    def _validate_task(self, task: Task) -> bool:
        """Validate task"""
        if not task.task_id or not task.task_type:
            return False
        if not task.required_capability:
            return False
        if task.estimated_duration <= 0:
            return False
        return True

    def _process_task_queue(self):
        """Process the task queue and assign tasks to agents"""
        while self.task_queue and not self._is_system_overloaded():
            _, _, task = heapq.heappop(self.task_queue)

            if task.status != TaskStatus.PENDING:
                continue  # Skip if task is no longer pending

            if task.is_expired():
                self._mark_task_failed(task, "Task expired before assignment")
                continue

            # Find suitable agent
            agent = self._find_best_agent_for_task(task)
            if agent:
                self._assign_task_to_agent(task, agent)
            else:
                # No suitable agent, put back in queue
                heapq.heappush(self.task_queue, (task.priority.value, time.time(), task))
                break

    def _find_best_agent_for_task(self, task: Task) -> Optional[AgentProfile]:
        """Find the best agent for a task based on current strategy"""
        suitable_agents = self.find_agents_for_capability(task.required_capability, filter_available=True)

        if not suitable_agents:
            return None

        if self.load_balancing_strategy == "round_robin":
            return suitable_agents[0]  # Simple round-robin

        elif self.load_balancing_strategy == "least_loaded":
            return min(suitable_agents, key=lambda a: a.current_tasks / a.max_concurrent_tasks)

        elif self.load_balancing_strategy == "performance_weighted":
            # Performance-weighted selection
            scores = []
            for agent in suitable_agents:
                load_factor = 1 - (agent.current_tasks / agent.max_concurrent_tasks)
                performance_factor = agent.performance_rating / 5.0
                reliability_factor = agent.reliability_score / 5.0
                score = load_factor * 0.4 + performance_factor * 0.4 + reliability_factor * 0.2
                scores.append((score, agent))

            scores.sort(reverse=True)
            return scores[0][1]

        return suitable_agents[0]

    def _assign_task_to_agent(self, task: Task, agent: AgentProfile):
        """Assign a task to an agent"""
        try:
            # Update task and agent status
            task.status = TaskStatus.ASSIGNED
            task.assigned_agent = agent.agent_id
            agent.current_tasks += 1

            if agent.current_tasks >= agent.max_concurrent_tasks:
                agent.status = AgentStatus.BUSY

            # Send task assignment message
            assignment_message = create_message(
                sender_id="marketplace",
                receiver_id=agent.agent_id,
                message_type=MessageType.TASK_ASSIGNMENT,
                payload={
                    "task": asdict(task),
                    "assignment_time": datetime.now().isoformat()
                },
                priority=MessagePriority(task.priority.value)
            )

            send_message(assignment_message)

            self.logger.info(f"Task {task.task_id} assigned to agent {agent.agent_id}")
            self._trigger_task_event("task_assigned", task)

        except Exception as e:
            self.logger.error(f"Error assigning task {task.task_id} to agent {agent.agent_id}: {e}")
            # Revert assignment
            task.status = TaskStatus.PENDING
            task.assigned_agent = None
            agent.current_tasks -= 1

    def _reassign_agent_tasks(self, agent_id: str):
        """Reassign tasks from an agent that's going offline"""
        tasks_to_reassign = [
            task for task in self.active_tasks.values()
            if task.assigned_agent == agent_id and task.status == TaskStatus.ASSIGNED
        ]

        for task in tasks_to_reassign:
            task.status = TaskStatus.PENDING
            task.assigned_agent = None
            task.retry_count += 1

            # Put back in queue
            heapq.heappush(self.task_queue, (task.priority.value, time.time(), task))

        self.logger.info(f"Reassigned {len(tasks_to_reassign)} tasks from agent {agent_id}")

    def _handle_agent_status_update(self, message: AgentMessage):
        """Handle agent status update messages"""
        try:
            agent_id = message.sender_id
            status_data = message.payload

            if agent_id in self.registered_agents:
                agent = self.registered_agents[agent_id]

                # Update agent status
                if "status" in status_data:
                    agent.status = AgentStatus(status_data["status"])

                if "current_tasks" in status_data:
                    agent.current_tasks = status_data["current_tasks"]

                if "metrics" in status_data:
                    agent.metrics.update(status_data["metrics"])

                # Update performance tracking
                self._update_agent_performance(agent_id, status_data)

                # Trigger event
                self._trigger_agent_event("agent_status_updated", agent)

        except Exception as e:
            self.logger.error(f"Error handling status update from {message.sender_id}: {e}")

    def _handle_agent_heartbeat(self, message: AgentMessage):
        """Handle agent heartbeat messages"""
        try:
            agent_id = message.sender_id

            if agent_id in self.registered_agents:
                agent = self.registered_agents[agent_id]
                agent.last_heartbeat = datetime.now()

                # Update heartbeat data
                if "metrics" in message.payload:
                    agent.metrics.update(message.payload["metrics"])
                    self._update_agent_performance(agent_id, message.payload)

        except Exception as e:
            self.logger.error(f"Error handling heartbeat from {message.sender_id}: {e}")

    def _notify_agent_of_cancellation(self, task: Task):
        """Notify an agent about task cancellation"""
        try:
            cancellation_message = create_message(
                sender_id="marketplace",
                receiver_id=task.assigned_agent,
                message_type=MessageType.COORDINATION,
                payload={
                    "action": "task_cancelled",
                    "task_id": task.task_id,
                    "reason": "Task cancelled by user"
                },
                priority=MessagePriority.HIGH
            )

            send_message(cancellation_message)

        except Exception as e:
            self.logger.error(f"Error notifying agent of task cancellation: {e}")

    def _update_agent_performance(self, agent_id: str, performance_data: Dict[str, Any]):
        """Update agent performance metrics"""
        try:
            current_time = time.time()

            for metric, value in performance_data.items():
                if isinstance(value, (int, float)):
                    # Update weighted average
                    old_value = self.agent_performance[agent_id][metric]
                    new_value = (old_value * 0.9 + value * 0.1)  # 0.9 weight to old value
                    self.agent_performance[agent_id][metric] = new_value

            # Update agent profile performance rating
            if agent_id in self.registered_agents:
                agent = self.registered_agents[agent_id]
                performance_metrics = self.agent_performance[agent_id]

                # Calculate performance rating based on key metrics
                if performance_metrics:
                    rating = sum(performance_metrics.values()) / len(performance_metrics)
                    agent.performance_rating = min(5.0, max(1.0, rating))

        except Exception as e:
            self.logger.error(f"Error updating agent performance for {agent_id}: {e}")

    def _trigger_task_event(self, event_type: str, task: Task):
        """Trigger task-related events"""
        for handler in self.task_handlers[event_type]:
            try:
                handler(task)
            except Exception as e:
                self.logger.error(f"Error in task event handler for {event_type}: {e}")

    def _trigger_agent_event(self, event_type: str, agent_data: Any):
        """Trigger agent-related events"""
        for handler in self.agent_handlers[event_type]:
            try:
                handler(agent_data)
            except Exception as e:
                self.logger.error(f"Error in agent event handler for {event_type}: {e}")

    def _is_system_overloaded(self) -> bool:
        """Check if the system is overloaded"""
        if not self.registered_agents:
            return False

        total_capacity = sum(agent.max_concurrent_tasks for agent in self.registered_agents.values())
        current_load = sum(agent.current_tasks for agent in self.registered_agents.values())

        return (current_load / total_capacity) > 0.9  # 90% capacity threshold

    def _mark_task_failed(self, task: Task, error_message: str):
        """Mark a task as failed"""
        task.status = TaskStatus.FAILED
        task.error_message = error_message
        task.completed_at = datetime.now()

        # Move to completed tasks
        self.completed_tasks[task.task_id] = task
        if task.task_id in self.active_tasks:
            del self.active_tasks[task.task_id]

        self.logger.error(f"Task failed: {task.task_id} - {error_message}")
        self._trigger_task_event("task_failed", task)

    def _calculate_average_task_duration(self) -> float:
        """Calculate average task duration"""
        if not self.completed_tasks:
            return 0.0

        durations = []
        for task in self.completed_tasks.values():
            if task.started_at and task.completed_at:
                duration = (task.completed_at - task.started_at).total_seconds()
                durations.append(duration)

        return sum(durations) / len(durations) if durations else 0.0

    def _calculate_success_rate(self) -> float:
        """Calculate task success rate"""
        if not self.completed_tasks:
            return 1.0

        successful_tasks = sum(1 for task in self.completed_tasks.values() if task.status == TaskStatus.COMPLETED)
        return successful_tasks / len(self.completed_tasks)

    def _calculate_system_load(self) -> float:
        """Calculate current system load"""
        if not self.registered_agents:
            return 0.0

        total_capacity = sum(agent.max_concurrent_tasks for agent in self.registered_agents.values())
        current_load = sum(agent.current_tasks for agent in self.registered_agents.values())

        return current_load / total_capacity if total_capacity > 0 else 0.0

    def _get_capability_summary(self) -> Dict[str, int]:
        """Get summary of available capabilities"""
        capability_counts = defaultdict(int)

        for agent in self.registered_agents.values():
            for cap in agent.capabilities:
                capability_counts[cap.name] += 1

        return dict(capability_counts)

    def start_background_processing(self):
        """Start background processing thread"""
        if self.background_thread is None or not self.background_thread.is_alive():
            self.running = True
            self.background_thread = threading.Thread(target=self._background_worker, daemon=True)
            self.background_thread.start()

    def stop_background_processing(self):
        """Stop background processing thread"""
        self.running = False
        if self.background_thread:
            self.background_thread.join(timeout=5)

    def _background_worker(self):
        """Background worker for processing tasks and monitoring agents"""
        while self.running:
            try:
                # Process task queue
                self._process_task_queue()

                # Check for inactive agents
                self._check_agent_health()

                # Clean up old completed tasks
                self._cleanup_old_tasks()

                # Sleep for a short interval
                time.sleep(1)

            except Exception as e:
                self.logger.error(f"Error in background worker: {e}")
                time.sleep(5)

    def _check_agent_health(self):
        """Check health of registered agents"""
        current_time = datetime.now()
        timeout_threshold = timedelta(minutes=5)  # 5 minutes timeout

        for agent_id, agent in list(self.registered_agents.items()):
            if current_time - agent.last_heartbeat > timeout_threshold:
                if agent.status != AgentStatus.OFFLINE:
                    agent.status = AgentStatus.OFFLINE
                    self._reassign_agent_tasks(agent_id)
                    self.logger.warning(f"Agent marked as offline due to missed heartbeats: {agent_id}")

    def _cleanup_old_tasks(self):
        """Clean up old completed tasks"""
        cutoff_time = datetime.now() - timedelta(hours=24)  # Keep tasks for 24 hours

        old_task_ids = [
            task_id for task_id, task in self.completed_tasks.items()
            if task.completed_at and task.completed_at < cutoff_time
        ]

        for task_id in old_task_ids:
            del self.completed_tasks[task_id]

# Global marketplace instance
marketplace = AgentMarketplace()

# Convenience functions
def register_agent(agent_profile: AgentProfile) -> bool:
    """Register an agent with the global marketplace"""
    return marketplace.register_agent(agent_profile)

def submit_task(task: Task) -> str:
    """Submit a task to the global marketplace"""
    return marketplace.submit_task(task)

def get_task_status(task_id: str) -> Optional[Dict[str, Any]]:
    """Get task status from global marketplace"""
    return marketplace.get_task_status(task_id)

def find_agents(capability: str) -> List[AgentProfile]:
    """Find agents for a capability using global marketplace"""
    return marketplace.find_agents_for_capability(capability)

def get_marketplace_status() -> Dict[str, Any]:
    """Get marketplace status from global marketplace"""
    return marketplace.get_marketplace_status()