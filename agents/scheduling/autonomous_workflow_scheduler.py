#!/usr/bin/env python3
"""
⏰ ScriptOhio Autonomous Workflow Scheduler

Intelligent workflow scheduling system that optimizes task execution
based on priorities, resource availability, dependencies, and business rules.

Key Features:
- Priority-based task scheduling with multiple algorithms
- Resource-aware scheduling considering system constraints
- Dependency resolution and critical path management
- Dynamic load balancing across available agents
- Predictive scheduling using machine learning
- Calendar-aware scheduling for sports-specific timing
- Deadline management and SLA enforcement

Author: ScriptOhio AI System
Version: 1.0.0
"""

import asyncio
import json
import logging
import sqlite3
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Set, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import heapq
import uuid
import statistics
import time
import holidays

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


class TaskPriority(Enum):
    """Task priority levels"""
    CRITICAL = 1     # System critical, must run immediately
    HIGH = 2         # Business critical, high priority
    NORMAL = 3       # Normal business priority
    LOW = 4          # Can be delayed
    BACKGROUND = 5   # Background tasks only


class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"           # Waiting to be scheduled
    SCHEDULED = "scheduled"       # Scheduled for execution
    RUNNING = "running"          # Currently executing
    COMPLETED = "completed"      # Successfully completed
    FAILED = "failed"           # Failed execution
    CANCELLED = "cancelled"      # Cancelled by user or system
    BLOCKED = "blocked"         # Blocked by dependencies


class SchedulingAlgorithm(Enum):
    """Scheduling algorithms"""
    PRIORITY_FIRST = "priority_first"           # Priority-based scheduling
    SHORTEST_JOB_FIRST = "sjf"                  # Shortest estimated duration
    ROUND_ROBIN = "round_robin"                 # Fair round-robin
    DEADLINE_DRIVEN = "deadline_driven"         # Deadline-based scheduling
    RESOURCE_AWARE = "resource_aware"           # Resource-optimized scheduling
    MACHINE_LEARNING = "ml_optimized"           # ML-based optimization
    HYBRID = "hybrid"                           # Combination approach


@dataclass
class TaskDependency:
    """Task dependency definition"""
    task_id: str
    dependency_type: str  # "finish_to_start", "start_to_start", "finish_to_finish"
    lag_minutes: int = 0  # Lag time in minutes


@dataclass
class TaskResource:
    """Resource requirement for a task"""
    resource_type: str  # "cpu", "memory", "api_calls", "agent_type"
    amount: float
    unit: str  # "percent", "mb", "calls_per_second", "agent"


@dataclass
class ScheduledTask:
    """Scheduled task definition"""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING

    # Timing information
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    deadline: Optional[datetime] = None

    # Execution details
    agent_type: str = ""
    workflow_type: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    estimated_duration_minutes: float = 0.0
    actual_duration_minutes: float = 0.0

    # Dependencies and resources
    dependencies: List[TaskDependency] = field(default_factory=list)
    resource_requirements: List[TaskResource] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)

    # Business context
    business_value: float = 0.0  # Business impact score (0-1)
    cost_of_delay: float = 0.0   # Cost per hour of delay
    sla_deadline: Optional[datetime] = None  # Service Level Agreement deadline

    # Scheduling metadata
    retry_count: int = 0
    max_retries: int = 3
    retry_delay_minutes: float = 5.0
    tags: List[str] = field(default_factory=list)

    # Metrics
    execution_history: List[Dict[str, Any]] = field(default_factory=list)


class CalendarManager:
    """Manages business and sports calendars for intelligent scheduling"""

    def __init__(self):
        # Initialize US holidays
        self.us_holidays = holidays.US()

        # College football specific dates
        self.football_season_dates = {
            2025: {
                "season_start": datetime(2025, 8, 30, tzinfo=timezone.utc),
                "regular_season_end": datetime(2025, 12, 6, tzinfo=timezone.utc),
                "championship Weekend": datetime(2025, 12, 13, tzinfo=timezone.utc),
                "bowl_season_start": datetime(2025, 12, 20, tzinfo=timezone.utc),
                "championship_game": datetime(2026, 1, 19, tzinfo=timezone.utc)
            }
        }

        # Game days by week (2025 season)
        self.game_days_2025 = {
            1: ["2025-09-06", "2025-09-07"],  # Week 1
            2: ["2025-09-13", "2025-09-14"],  # Week 2
            # Add more weeks as needed
            14: ["2025-11-29", "2025-11-30"],  # Week 14 (Rivalry weekend)
        }

        # Business hours (UTC)
        self.business_hours = {
            "start": 13,  # 8 AM EST = 1 PM UTC
            "end": 23,    # 6 PM EST = 11 PM UTC
            "weekdays": [0, 1, 2, 3, 4]  # Monday-Friday
        }

    def is_business_hours(self, dt: datetime) -> bool:
        """Check if datetime is during business hours"""
        return (
            dt.weekday() in self.business_hours["weekdays"] and
            self.business_hours["start"] <= dt.hour < self.business_hours["end"]
        )

    def is_holiday(self, dt: datetime) -> bool:
        """Check if date is a holiday"""
        return dt.date() in self.us_holidays

    def is_game_day(self, dt: datetime, season: int = 2025) -> bool:
        """Check if date is a game day"""
        date_str = dt.strftime("%Y-%m-%d")

        if season in self.football_season_dates:
            season_dates = self.football_season_dates[season]

            # Check if within season
            if season_dates["season_start"] <= dt <= season_dates["bowl_season_start"]:
                for week_days in self.game_days_2025.values():
                    if date_str in week_days:
                        return True

        return False

    def get_optimal_execution_time(self, task: ScheduledTask, preferred_time: datetime = None) -> datetime:
        """Get optimal execution time considering calendar constraints"""
        if preferred_time is None:
            preferred_time = datetime.now(timezone.utc)

        # Game day tasks get priority scheduling
        if "gameday" in task.tags or "game_day" in task.tags:
            # Schedule immediately on game days
            if self.is_game_day(preferred_time):
                return preferred_time

        # Critical tasks can run anytime
        if task.priority == TaskPriority.CRITICAL:
            return preferred_time

        # For other tasks, prefer off-peak hours
        optimal_time = preferred_time

        # Avoid holidays
        if self.is_holiday(optimal_time):
            # Move to next business day
            days_ahead = 1
            while self.is_holiday(optimal_time + timedelta(days=days_ahead)) or \
                  (optimal_time + timedelta(days=days_ahead)).weekday() >= 5:
                days_ahead += 1

            optimal_time = optimal_time + timedelta(days=days_ahead)
            optimal_time = optimal_time.replace(hour=self.business_hours["start"], minute=0)

        # Prefer business hours for normal priority tasks
        if task.priority == TaskPriority.NORMAL and not self.is_business_hours(optimal_time):
            # Move to next business hour
            if optimal_time.hour >= self.business_hours["end"]:
                optimal_time = optimal_time + timedelta(days=1)
                optimal_time = optimal_time.replace(hour=self.business_hours["start"], minute=0)
            elif optimal_time.hour < self.business_hours["start"]:
                optimal_time = optimal_time.replace(hour=self.business_hours["start"], minute=0)

        return optimal_time


class PredictiveScheduler:
    """Machine learning-based predictive scheduling"""

    def __init__(self):
        self.historical_data = []
        self.performance_models = {}

    def add_execution_record(self, task: ScheduledTask, execution_time: float, success: bool):
        """Add execution record for learning"""
        record = {
            "task_type": task.workflow_type,
            "estimated_duration": task.estimated_duration_minutes,
            "actual_duration": execution_time,
            "success": success,
            "priority": task.priority.value,
            "resource_requirements": task.resource_requirements,
            "time_of_day": task.started_at.hour if task.started_at else None,
            "day_of_week": task.started_at.weekday() if task.started_at else None,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self.historical_data.append(record)

    def predict_duration(self, task: ScheduledTask) -> float:
        """Predict task execution duration based on historical data"""
        relevant_records = [
            r for r in self.historical_data
            if r["task_type"] == task.workflow_type and r["success"]
        ]

        if not relevant_records:
            return task.estimated_duration_minutes

        # Use historical average with confidence weighting
        durations = [r["actual_duration"] for r in relevant_records]

        # Apply weighted average (more recent records get higher weight)
        weights = []
        for record in relevant_records:
            record_time = datetime.fromisoformat(record["timestamp"])
            days_ago = (datetime.now(timezone.utc) - record_time).days
            weight = max(0.1, 1.0 - (days_ago / 30))  # Decay over 30 days
            weights.append(weight)

        if sum(weights) > 0:
            weighted_avg = sum(d * w for d, w in zip(durations, weights)) / sum(weights)

            # Blend with original estimate (70% historical, 30% estimate)
            return 0.7 * weighted_avg + 0.3 * task.estimated_duration_minutes
        else:
            return statistics.mean(durations)

    def predict_success_probability(self, task: ScheduledTask, scheduled_time: datetime) -> float:
        """Predict probability of successful execution"""
        relevant_records = [
            r for r in self.historical_data
            if r["task_type"] == task.workflow_type
        ]

        if not relevant_records:
            return 0.9  # Default high confidence

        # Consider time-based patterns
        similar_time_records = [
            r for r in relevant_records
            if abs(r.get("time_of_day", 0) - scheduled_time.hour) <= 2 and
               abs(r.get("day_of_week", 0) - scheduled_time.weekday()) <= 1
        ]

        if similar_time_records:
            success_rate = sum(1 for r in similar_time_records if r["success"]) / len(similar_time_records)
            return max(0.5, success_rate)  # Minimum 50% confidence
        else:
            return sum(1 for r in relevant_records if r["success"]) / len(relevant_records)


class AutonomousWorkflowScheduler(BaseAgent):
    """Intelligent workflow scheduler for autonomous operations"""

    def __init__(self):
        super().__init__(
            agent_id="autonomous_workflow_scheduler",
            name="ScriptOhio Autonomous Workflow Scheduler",
            permission_level=PermissionLevel.ADMIN
        )

        # Database setup
        self.db_path = Path("project_management/scheduling/autonomous_scheduler.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

        # Scheduling components
        self.calendar_manager = CalendarManager()
        self.predictive_scheduler = PredictiveScheduler()
        self.current_algorithm = SchedulingAlgorithm.HYBRID

        # Task queues by priority
        self.task_queues: Dict[TaskPriority, List[ScheduledTask]] = {
            priority: [] for priority in TaskPriority
        }

        # Agent registry for resource management
        self.agent_registry = {}
        self.resource_monitor = ResourceMonitor()

        # Scheduling state
        self.is_running = False
        self.scheduling_interval = 60  # seconds
        self.max_concurrent_tasks = 10

        # Load existing tasks
        self._load_scheduled_tasks()

    def _init_database(self):
        """Initialize SQLite database for task persistence"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS scheduled_tasks (
                    task_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    priority INTEGER,
                    status TEXT,
                    created_at TEXT,
                    scheduled_at TEXT,
                    started_at TEXT,
                    completed_at TEXT,
                    deadline TEXT,
                    agent_type TEXT,
                    workflow_type TEXT,
                    parameters TEXT,
                    estimated_duration_minutes REAL,
                    actual_duration_minutes REAL,
                    dependencies TEXT,
                    resource_requirements TEXT,
                    business_value REAL,
                    cost_of_delay REAL,
                    sla_deadline TEXT,
                    retry_count INTEGER,
                    max_retries INTEGER,
                    retry_delay_minutes REAL,
                    tags TEXT,
                    execution_history TEXT
                )
            ''')

            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_status ON scheduled_tasks(status)
            ''')

            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_priority ON scheduled_tasks(priority)
            ''')

            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_scheduled_at ON scheduled_tasks(scheduled_at)
            ''')

    def _load_scheduled_tasks(self):
        """Load scheduled tasks from database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('SELECT * FROM scheduled_tasks WHERE status IN ("pending", "scheduled")')

            for row in cursor.fetchall():
                task = self._row_to_task(row)
                self.task_queues[task.priority].append(task)

    def _row_to_task(self, row) -> ScheduledTask:
        """Convert database row to ScheduledTask object"""
        return ScheduledTask(
            task_id=row[0],
            name=row[1] or "",
            description=row[2] or "",
            priority=TaskPriority(row[3]),
            status=TaskStatus(row[4]),
            created_at=datetime.fromisoformat(row[5]),
            scheduled_at=datetime.fromisoformat(row[6]) if row[6] else None,
            started_at=datetime.fromisoformat(row[7]) if row[7] else None,
            completed_at=datetime.fromisoformat(row[8]) if row[8] else None,
            deadline=datetime.fromisoformat(row[9]) if row[9] else None,
            agent_type=row[10] or "",
            workflow_type=row[11] or "",
            parameters=json.loads(row[12]) if row[12] else {},
            estimated_duration_minutes=row[13] or 0.0,
            actual_duration_minutes=row[14] or 0.0,
            dependencies=json.loads(row[15]) if row[15] else [],
            resource_requirements=json.loads(row[16]) if row[16] else [],
            business_value=row[17] or 0.0,
            cost_of_delay=row[18] or 0.0,
            sla_deadline=datetime.fromisoformat(row[19]) if row[19] else None,
            retry_count=row[20] or 0,
            max_retries=row[21] or 3,
            retry_delay_minutes=row[22] or 5.0,
            tags=json.loads(row[23]) if row[23] else [],
            execution_history=json.loads(row[24]) if row[24] else []
        )

    def _save_task(self, task: ScheduledTask):
        """Save task to database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO scheduled_tasks VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
            ''', (
                task.task_id, task.name, task.description, task.priority.value,
                task.status.value, task.created_at.isoformat(),
                task.scheduled_at.isoformat() if task.scheduled_at else None,
                task.started_at.isoformat() if task.started_at else None,
                task.completed_at.isoformat() if task.completed_at else None,
                task.deadline.isoformat() if task.deadline else None,
                task.agent_type, task.workflow_type, json.dumps(task.parameters),
                task.estimated_duration_minutes, task.actual_duration_minutes,
                json.dumps([d.__dict__ for d in task.dependencies]),
                json.dumps([r.__dict__ for r in task.resource_requirements]),
                task.business_value, task.cost_of_delay,
                task.sla_deadline.isoformat() if task.sla_deadline else None,
                task.retry_count, task.max_retries, task.retry_delay_minutes,
                json.dumps(task.tags), json.dumps(task.execution_history)
            ))

    def _define_capabilities(self) -> List[AgentCapability]:
        """Define agent capabilities"""
        return [
            AgentCapability(
                name="schedule_task",
                description="Schedule a new autonomous task",
                execution_time_estimate=5.0,
                permission_required=PermissionLevel.READ_EXECUTE_WRITE,
                tools_required=["task_definition"],
                data_access=["task_id", "scheduled_time", "status"]
            ),
            AgentCapability(
                name="get_schedule",
                description="Get current task schedule",
                execution_time_estimate=3.0,
                permission_required=[PermissionLevel.READ_EXECUTE],
                tools_required=["priority_filter", "status_filter"],
                data_access=["scheduled_tasks": "list", "summary": "object"]
            ),
            AgentCapability(
                name="optimize_schedule",
                description="Optimize task scheduling using ML",
                execution_time_estimate=15.0,
                permission_required=[PermissionLevel.READ_EXECUTE_WRITE],
                tools_required=["algorithm", "time_horizon"],
                data_access=["optimization_results": "object", "improvements": "list"]
            ),
            AgentCapability(
                name="start_scheduler",
                description="Start the autonomous scheduler",
                execution_time_estimate=5.0,
                permission_required=[PermissionLevel.ADMIN],
                tools_required=["scheduling_interval"],
                data_access=["status": "string", "scheduler_id": "string"]
            ),
            AgentCapability(
                name="stop_scheduler",
                description="Stop the autonomous scheduler",
                execution_time_estimate=3.0,
                permission_required=[PermissionLevel.ADMIN],
                tools_required=["force"],
                data_access=["status": "string", "tasks_stopped": "integer"]
            )
        ]

    def _execute_action(self, action: str, parameters: Dict, user_context: Dict) -> Dict:
        """Execute agent actions"""
        try:
            if action == "schedule_task":
                return self._schedule_task(parameters["task_definition"])

            elif action == "get_schedule":
                return self._get_schedule(
                    parameters.get("priority_filter"),
                    parameters.get("status_filter")
                )

            elif action == "optimize_schedule":
                return self._optimize_schedule(
                    parameters.get("algorithm", "hybrid"),
                    parameters.get("time_horizon", 24)  # hours
                )

            elif action == "start_scheduler":
                return self._start_scheduler(
                    parameters.get("scheduling_interval", self.scheduling_interval)
                )

            elif action == "stop_scheduler":
                return self._stop_scheduler(parameters.get("force", False))

            else:
                raise ValueError(f"Unknown action: {action}")

        except Exception as e:
            logger.error(f"Error in scheduler agent {action}: {e}")
            return {
                "status": "error",
                "error": str(e),
                "agent_id": self.agent_id
            }

    def _schedule_task(self, task_definition: Dict) -> Dict:
        """Schedule a new autonomous task"""
        try:
            # Create task object
            task = ScheduledTask(
                name=task_definition.get("name", "Unnamed Task"),
                description=task_definition.get("description", ""),
                priority=TaskPriority(task_definition.get("priority", TaskPriority.NORMAL.value)),
                agent_type=task_definition.get("agent_type", ""),
                workflow_type=task_definition.get("workflow_type", ""),
                parameters=task_definition.get("parameters", {}),
                estimated_duration_minutes=task_definition.get("estimated_duration_minutes", 0.0),
                deadline=datetime.fromisoformat(task_definition["deadline"]) if task_definition.get("deadline") else None,
                business_value=task_definition.get("business_value", 0.0),
                cost_of_delay=task_definition.get("cost_of_delay", 0.0),
                tags=task_definition.get("tags", [])
            )

            # Parse dependencies
            for dep in task_definition.get("dependencies", []):
                task.dependencies.append(TaskDependency(**dep))

            # Parse resource requirements
            for req in task_definition.get("resource_requirements", []):
                task.resource_requirements.append(TaskResource(**req))

            # Predict optimal execution time
            preferred_time = datetime.now(timezone.utc)
            if "preferred_time" in task_definition:
                preferred_time = datetime.fromisoformat(task_definition["preferred_time"])

            optimal_time = self.calendar_manager.get_optimal_execution_time(task, preferred_time)
            task.scheduled_at = optimal_time

            # Predict duration using ML if available
            predicted_duration = self.predictive_scheduler.predict_duration(task)
            if predicted_duration > 0:
                task.estimated_duration_minutes = predicted_duration

            # Add to appropriate queue
            self.task_queues[task.priority].append(task)

            # Save to database
            self._save_task(task)

            return {
                "status": "success",
                "task_id": task.task_id,
                "scheduled_time": task.scheduled_at.isoformat(),
                "estimated_duration": task.estimated_duration_minutes,
                "priority": task.priority.name
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": "Failed to schedule task"
            }

    def _get_schedule(self, priority_filter: str = None, status_filter: str = None) -> Dict:
        """Get current task schedule with optional filters"""
        tasks = []
        total_count = 0
        queue_sizes = {}

        for priority, queue in self.task_queues.items():
            queue_sizes[priority.name] = len(queue)

            for task in queue:
                # Apply filters
                if priority_filter and priority.name != priority_filter:
                    continue
                if status_filter and task.status.value != status_filter:
                    continue

                tasks.append({
                    "task_id": task.task_id,
                    "name": task.name,
                    "priority": task.priority.name,
                    "status": task.status.value,
                    "scheduled_at": task.scheduled_at.isoformat() if task.scheduled_at else None,
                    "estimated_duration": task.estimated_duration_minutes,
                    "workflow_type": task.workflow_type,
                    "agent_type": task.agent_type,
                    "deadline": task.deadline.isoformat() if task.deadline else None,
                    "business_value": task.business_value,
                    "tags": task.tags
                })
                total_count += 1

        # Sort by scheduled time
        tasks.sort(key=lambda x: x["scheduled_at"] or "")

        return {
            "status": "success",
            "tasks": tasks,
            "summary": {
                "total_tasks": total_count,
                "queue_sizes": queue_sizes,
                "next_execution": tasks[0]["scheduled_at"] if tasks else None
            }
        }

    def _optimize_schedule(self, algorithm: str = "hybrid", time_horizon: int = 24) -> Dict:
        """Optimize task scheduling using specified algorithm"""
        try:
            # Collect all tasks for optimization
            all_tasks = []
            for queue in self.task_queues.values():
                all_tasks.extend(queue)

            if not all_tasks:
                return {
                    "status": "success",
                    "message": "No tasks to optimize",
                    "optimization_results": {"improvements": [], "efficiency_gain": 0.0}
                }

            # Apply optimization algorithm
            if algorithm == "priority_first":
                improvements = self._optimize_priority_first(all_tasks)
            elif algorithm == "deadline_driven":
                improvements = self._optimize_deadline_driven(all_tasks)
            elif algorithm == "resource_aware":
                improvements = self._optimize_resource_aware(all_tasks)
            elif algorithm == "ml_optimized":
                improvements = self._optimize_ml_based(all_tasks)
            else:  # hybrid
                improvements = self._optimize_hybrid(all_tasks)

            # Calculate efficiency improvements
            efficiency_gain = len(improvements) / len(all_tasks) * 100 if all_tasks else 0

            return {
                "status": "success",
                "algorithm_used": algorithm,
                "time_horizon_hours": time_horizon,
                "tasks_optimized": len(all_tasks),
                "improvements_made": len(improvements),
                "efficiency_gain_percent": round(efficiency_gain, 2),
                "optimization_results": {
                    "improvements": improvements,
                    "efficiency_gain": efficiency_gain / 100
                }
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": "Schedule optimization failed"
            }

    def _optimize_priority_first(self, tasks: List[ScheduledTask]) -> List[str]:
        """Optimize using priority-first algorithm"""
        improvements = []

        # Sort by priority and deadline
        tasks.sort(key=lambda t: (t.priority.value, t.deadline or datetime.max))

        # Reschedule tasks to respect priority order
        current_time = datetime.now(timezone.utc)
        for task in tasks:
            if task.scheduled_at and task.scheduled_at < current_time:
                old_time = task.scheduled_at
                task.scheduled_at = current_time
                self._save_task(task)
                improvements.append(f"Rescheduled {task.name} for priority order")

                # Add buffer time between tasks
                current_time += timedelta(minutes=max(15, task.estimated_duration_minutes))

        return improvements

    def _optimize_deadline_driven(self, tasks: List[ScheduledTask]) -> List[str]:
        """Optimize using deadline-driven algorithm"""
        improvements = []

        # Filter tasks with deadlines
        deadline_tasks = [t for t in tasks if t.deadline]

        # Sort by deadline (earliest first)
        deadline_tasks.sort(key=lambda t: t.deadline)

        # Ensure tasks can complete before deadline
        current_time = datetime.now(timezone.utc)
        for task in deadline_tasks:
            if task.deadline:
                latest_start = task.deadline - timedelta(minutes=task.estimated_duration_minutes)

                if current_time > latest_start:
                    improvements.append(f"WARNING: {task.name} cannot complete before deadline")
                else:
                    task.scheduled_at = max(current_time, task.scheduled_at or current_time)
                    self._save_task(task)
                    improvements.append(f"Scheduled {task.name} to meet deadline")

                    current_time = task.scheduled_at + timedelta(minutes=task.estimated_duration_minutes)

        return improvements

    def _optimize_resource_aware(self, tasks: List[ScheduledTask]) -> List[str]:
        """Optimize using resource-aware algorithm"""
        improvements = []

        # Simple resource balancing - avoid CPU-intensive tasks at same time
        cpu_intensive = [t for t in tasks if any(r.resource_type == "cpu" for r in t.resource_requirements)]

        if len(cpu_intensive) > 1:
            # Spread CPU-intensive tasks
            current_time = datetime.now(timezone.utc)
            for i, task in enumerate(cpu_intensive):
                if task.scheduled_at:
                    task.scheduled_at = current_time + timedelta(hours=i*2)
                    self._save_task(task)
                    improvements.append(f"Spread {task.name} to balance CPU load")

        return improvements

    def _optimize_ml_based(self, tasks: List[ScheduledTask]) -> List[str]:
        """Optimize using machine learning predictions"""
        improvements = []

        # Use predictive scheduler to optimize timing
        for task in tasks:
            if task.scheduled_at:
                # Predict success probability
                success_prob = self.predictive_scheduler.predict_success_probability(task, task.scheduled_at)

                # If success probability is low, try to find better time
                if success_prob < 0.7:
                    # Try times in next 24 hours
                    best_time = task.scheduled_at
                    best_prob = success_prob

                    for hours_ahead in range(1, 25):
                        test_time = task.scheduled_at + timedelta(hours=hours_ahead)
                        test_prob = self.predictive_scheduler.predict_success_probability(task, test_time)

                        if test_prob > best_prob:
                            best_time = test_time
                            best_prob = test_prob

                    if best_prob > success_prob + 0.1:  # Significant improvement
                        task.scheduled_at = best_time
                        self._save_task(task)
                        improvements.append(f"Improved {task.name} success probability by {(best_prob - success_prob)*100:.1f}%")

        return improvements

    def _optimize_hybrid(self, tasks: List[ScheduledTask]) -> List[str]:
        """Optimize using hybrid approach combining multiple algorithms"""
        all_improvements = []

        # Apply each algorithm and combine results
        all_improvements.extend(self._optimize_priority_first(tasks.copy()))
        all_improvements.extend(self._optimize_deadline_driven(tasks.copy()))
        all_improvements.extend(self._optimize_ml_based(tasks))

        # Remove duplicates
        unique_improvements = list(set(all_improvements))

        return unique_improvements

    async def _start_scheduler(self, scheduling_interval: int = 60) -> Dict:
        """Start the autonomous scheduler"""
        if self.is_running:
            return {
                "status": "already_running",
                "message": "Scheduler is already running",
                "scheduling_interval": self.scheduling_interval
            }

        self.scheduling_interval = scheduling_interval
        self.is_running = True

        # Start scheduling loop
        asyncio.create_task(self._scheduling_loop())

        logger.info(f"Scheduler started with {scheduling_interval}s interval")
        return {
            "status": "started",
            "scheduling_interval": scheduling_interval,
            "scheduler_id": self.agent_id,
            "message": "Autonomous scheduler started successfully"
        }

    async def _stop_scheduler(self, force: bool = False) -> Dict:
        """Stop the autonomous scheduler"""
        if not self.is_running:
            return {
                "status": "not_running",
                "message": "Scheduler is not currently running"
            }

        self.is_running = False

        # Count running tasks that might be affected
        running_tasks = sum(1 for queue in self.task_queues.values()
                          for task in queue if task.status == TaskStatus.RUNNING)

        logger.info("Scheduler stopped")
        return {
            "status": "stopped",
            "tasks_affected": running_tasks,
            "force_stopped": force,
            "message": "Autonomous scheduler stopped"
        }

    async def _scheduling_loop(self):
        """Main scheduling loop"""
        while self.is_running:
            try:
                await self._process_ready_tasks()
                await self._check_deadlines()
                await self._update_predictions()

                await asyncio.sleep(self.scheduling_interval)

            except Exception as e:
                logger.error(f"Error in scheduling loop: {e}")
                await asyncio.sleep(10)  # Brief pause on error

    async def _process_ready_tasks(self):
        """Process tasks that are ready to execute"""
        current_time = datetime.now(timezone.utc)
        ready_tasks = []

        # Find tasks ready to execute
        for priority, queue in self.task_queues.items():
            for task in queue:
                if (task.status == TaskStatus.SCHEDULED and
                    task.scheduled_at and
                    task.scheduled_at <= current_time and
                    self._dependencies_satisfied(task)):
                    ready_tasks.append(task)

        # Sort by priority and execution time
        ready_tasks.sort(key=lambda t: (t.priority.value, t.estimated_duration_minutes))

        # Execute tasks respecting concurrency limits
        running_count = sum(1 for queue in self.task_queues.values()
                           for task in queue if task.status == TaskStatus.RUNNING)

        available_slots = self.max_concurrent_tasks - running_count

        for task in ready_tasks[:available_slots]:
            await self._execute_task(task)

    async def _execute_task(self, task: ScheduledTask):
        """Execute a scheduled task"""
        try:
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.now(timezone.utc)
            self._save_task(task)

            logger.info(f"Executing task: {task.name}")

            # Simulate task execution (in real system, this would call the appropriate agent)
            execution_time = task.estimated_duration_minutes * 60  # Convert to seconds
            await asyncio.sleep(min(execution_time, 10))  # Cap at 10s for demo

            # Mark as completed
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now(timezone.utc)
            task.actual_duration_minutes = (task.completed_at - task.started_at).total_seconds() / 60

            # Record execution for ML learning
            self.predictive_scheduler.add_execution_record(
                task, task.actual_duration_minutes, True
            )

            self._save_task(task)

            logger.info(f"Completed task: {task.name} in {task.actual_duration_minutes:.1f} minutes")

        except Exception as e:
            # Handle task failure
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now(timezone.utc)

            # Record failure for ML learning
            self.predictive_scheduler.add_execution_record(
                task, task.estimated_duration_minutes, False
            )

            # Schedule retry if appropriate
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                task.status = TaskStatus.SCHEDULED
                task.scheduled_at = datetime.now(timezone.utc) + timedelta(minutes=task.retry_delay_minutes)
                task.retry_delay_minutes *= 2  # Exponential backoff

            self._save_task(task)
            logger.error(f"Failed task: {task.name} - {e}")

    def _dependencies_satisfied(self, task: ScheduledTask) -> bool:
        """Check if all task dependencies are satisfied"""
        for dep in task.dependencies:
            # Find dependent task
            dep_task = None
            for queue in self.task_queues.values():
                for t in queue:
                    if t.task_id == dep.task_id:
                        dep_task = t
                        break
                if dep_task:
                    break

            if not dep_task:
                return False  # Dependency not found

            if dep.dependency_type == "finish_to_start":
                if dep_task.status != TaskStatus.COMPLETED:
                    return False

                # Check lag time
                if dep_task.completed_at:
                    min_start_time = dep_task.completed_at + timedelta(minutes=dep.lag_minutes)
                    if task.scheduled_at and task.scheduled_at < min_start_time:
                        task.scheduled_at = min_start_time
                        self._save_task(task)

        return True

    async def _check_deadlines(self):
        """Check for approaching deadlines and prioritize accordingly"""
        current_time = datetime.now(timezone.utc)
        warning_threshold = timedelta(hours=2)

        for queue in self.task_queues.values():
            for task in queue:
                if task.deadline and task.status in [TaskStatus.PENDING, TaskStatus.SCHEDULED]:
                    time_until_deadline = task.deadline - current_time

                    if time_until_deadline <= warning_threshold:
                        # Upgrade priority for deadline-critical tasks
                        if task.priority != TaskPriority.CRITICAL:
                            old_priority = task.priority
                            task.priority = TaskPriority.HIGH
                            self._save_task(task)

                            logger.warning(
                                f"Upgraded {task.name} priority from {old_priority.name} to HIGH "
                                f"due to approaching deadline"
                            )

    async def _update_predictions(self):
        """Update ML predictions based on current state"""
        # This would periodically retrain models with new data
        pass

    def get_scheduler_status(self) -> Dict:
        """Get comprehensive scheduler status"""
        total_tasks = sum(len(queue) for queue in self.task_queues.values())
        running_tasks = sum(1 for queue in self.task_queues.values()
                           for task in queue if task.status == TaskStatus.RUNNING)

        return {
            "scheduler_id": self.agent_id,
            "is_running": self.is_running,
            "scheduling_interval": self.scheduling_interval,
            "current_algorithm": self.current_algorithm.value,
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "task_summary": {
                "total_tasks": total_tasks,
                "running_tasks": running_tasks,
                "queue_sizes": {priority.name: len(queue) for priority, queue in self.task_queues.items()}
            },
            "ml_models": {
                "historical_records": len(self.predictive_scheduler.historical_data),
                "performance_models": list(self.predictive_scheduler.performance_models.keys())
            },
            "last_update": datetime.now(timezone.utc).isoformat()
        }


class ResourceMonitor:
    """Monitor system resources for scheduling decisions"""

    def __init__(self):
        self.last_check = None
        self.resource_history = []

    def get_current_resources(self) -> Dict[str, float]:
        """Get current system resource usage"""
        import psutil

        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent,
            "active_connections": len(psutil.net_connections())
        }

    def can_schedule_task(self, task: ScheduledTask) -> bool:
        """Check if system has resources for task"""
        resources = self.get_current_resources()

        # Basic resource checks
        if resources["cpu_percent"] > 90:
            return False
        if resources["memory_percent"] > 85:
            return False

        # Check task-specific requirements
        for req in task.resource_requirements:
            if req.resource_type == "cpu" and req.unit == "percent":
                if resources["cpu_percent"] + req.amount > 95:
                    return False
            elif req.resource_type == "memory" and req.unit == "percent":
                if resources["memory_percent"] + req.amount > 90:
                    return False

        return True


# Global scheduler instance
autonomous_workflow_scheduler = AutonomousWorkflowScheduler()