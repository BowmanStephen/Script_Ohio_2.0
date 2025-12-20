"""
Memory-Aware Agent Load Balancing System

Intelligently distributes workload among agents based on their memory usage,
performance metrics, and current capacity. Optimizes system performance
through smart resource allocation.

Features:
- Real-time agent capacity monitoring
- Memory-based load balancing algorithms
- Dynamic agent scaling and allocation
- Performance-aware task distribution
- Resource optimization and bottleneck detection
"""

import heapq
import json
import logging
import statistics
import threading
import time
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class AgentCapacity:
    """Represents an agent's current capacity and performance"""

    agent_id: str
    max_concurrent_tasks: int
    current_tasks: int
    memory_usage_mb: float
    memory_limit_mb: float
    cpu_usage_percent: float
    avg_response_time_ms: float
    success_rate: float
    last_activity: datetime
    specialization_tags: List[str]
    health_status: str  # healthy, warning, critical, offline


@dataclass
class TaskRequirement:
    """Represents resource requirements for a task"""

    task_id: str
    task_type: str
    estimated_memory_mb: float
    estimated_duration_min: float
    required_capabilities: List[str]
    priority: int  # 1-10, 10 being highest
    deadline: Optional[datetime]
    coordination_requirements: List[str]


@dataclass
class LoadBalancingDecision:
    """Represents a load balancing decision"""

    task_id: str
    assigned_agent: str
    confidence_score: float
    reasoning: List[str]
    estimated_completion_time: datetime
    resource_allocation: Dict[str, Any]


class MemoryAwareLoadBalancer:
    """Advanced load balancing system with memory awareness"""

    def __init__(self, memory_manager=None):
        self.memory_manager = memory_manager
        self.agent_capacities = {}
        self.task_queue = []
        self.active_assignments = {}
        self.performance_history = defaultdict(lambda: deque(maxlen=100))
        self.balancing_strategies = {
            "memory_optimized": self._balance_by_memory,
            "performance_optimized": self._balance_by_performance,
            "capacity_optimized": self._balance_by_capacity,
            "hybrid": self._hybrid_balancing,
        }
        self.current_strategy = "hybrid"
        self.balancing_interval_seconds = 30

        # Start background monitoring
        self._start_capacity_monitoring()

        logger.info("Memory-Aware Load Balancer initialized")

    def _start_capacity_monitoring(self):
        """Start background monitoring of agent capacities"""

        def monitor_capacities():
            while True:
                try:
                    self._update_agent_capacities()
                    self._rebalance_tasks()
                    time.sleep(self.balancing_interval_seconds)
                except Exception as e:
                    logger.error(f"Capacity monitoring error: {e}")
                    time.sleep(self.balancing_interval_seconds)

        monitor_thread = threading.Thread(target=monitor_capacities, daemon=True)
        monitor_thread.start()
        logger.info("Background capacity monitoring started")

    def _update_agent_capacities(self):
        """Update capacity information for all agents"""

        # Get agent data from memory system
        if not self.memory_manager:
            return

        try:
            # Get all agent-related entries
            agent_entries = self.memory_manager.search_by_tags(["agent_context"])

            # Group by agent
            agent_data = defaultdict(list)
            for entry in agent_entries:
                if hasattr(entry, "tags"):
                    for tag in entry.tags:
                        if tag.endswith("_agent") and tag != "agent":
                            agent_data[tag].append(entry)

            # Update capacity for each agent
            for agent_id, entries in agent_data.items():
                capacity = self._calculate_agent_capacity(agent_id, entries)
                if capacity:
                    self.agent_capacities[agent_id] = capacity
                    self.performance_history[agent_id].append(
                        {
                            "timestamp": datetime.now(),
                            "memory_usage": capacity.memory_usage_mb,
                            "response_time": capacity.avg_response_time_ms,
                            "success_rate": capacity.success_rate,
                        }
                    )

        except Exception as e:
            logger.warning(f"Capacity update error: {e}")

    def _calculate_agent_capacity(
        self, agent_id: str, entries: List
    ) -> Optional[AgentCapacity]:
        """Calculate current capacity for an agent"""

        if not entries:
            return None

        # Extract agent data from entries
        current_time = datetime.now()
        memory_usage = 0.0
        active_tasks = 0
        response_times = []
        specializations = set()

        for entry in entries:
            if hasattr(entry, "value") and isinstance(entry.value, dict):
                value = entry.value

                # Memory usage
                if hasattr(entry, "size_bytes"):
                    memory_usage += entry.size_bytes / 1024 / 1024

                # Active tasks
                if value.get("agent_status") in ["running", "processing"]:
                    active_tasks += 1

                # Response time
                if "response_time" in value:
                    response_times.append(value["response_time"])

                # Specializations
                if hasattr(entry, "tags"):
                    specializations.update(
                        [
                            tag
                            for tag in entry.tags
                            if tag not in ["agent", "agent_context", agent_id]
                        ]
                    )

        # Calculate metrics
        avg_response_time = statistics.mean(response_times) if response_times else 100.0
        memory_usage_mb = min(memory_usage, 20.0)  # Cap at 20MB

        # Determine specialization tags
        specialization_tags = list(specializations)[:5]  # Limit to 5 tags

        # Determine health status
        health_status = "healthy"
        if memory_usage_mb > 15:
            health_status = "critical"
        elif memory_usage_mb > 10 or avg_response_time > 500:
            health_status = "warning"

        # Set default values based on agent type
        agent_configs = {
            "cfbd_integration_agent": {"max_tasks": 3, "memory_limit": 20},
            "model_execution_engine": {"max_tasks": 2, "memory_limit": 20},
            "analytics_orchestrator": {"max_tasks": 5, "memory_limit": 20},
            "weekly_matchup_analysis_agent": {"max_tasks": 3, "memory_limit": 20},
            "documentation_agent": {"max_tasks": 4, "memory_limit": 20},
        }

        config = agent_configs.get(agent_id, {"max_tasks": 3, "memory_limit": 20})

        return AgentCapacity(
            agent_id=agent_id,
            max_concurrent_tasks=config["max_tasks"],
            current_tasks=active_tasks,
            memory_usage_mb=memory_usage_mb,
            memory_limit_mb=config["memory_limit"],
            cpu_usage_percent=min(100, active_tasks * 25),  # Estimate
            avg_response_time_ms=avg_response_time,
            success_rate=95.0,  # Would calculate from actual data
            last_activity=current_time,
            specialization_tags=specialization_tags,
            health_status=health_status,
        )

    def assign_task(self, task: TaskRequirement) -> LoadBalancingDecision:
        """Assign a task to the most suitable agent"""

        # Use current balancing strategy
        strategy_func = self.balancing_strategies.get(
            self.current_strategy, self._hybrid_balancing
        )
        return strategy_func(task)

    def _balance_by_memory(self, task: TaskRequirement) -> LoadBalancingDecision:
        """Balance tasks based on memory availability"""

        suitable_agents = []

        for agent_id, capacity in self.agent_capacities.items():
            # Check if agent can handle the task
            if (
                capacity.current_tasks < capacity.max_concurrent_tasks
                and capacity.memory_usage_mb + task.estimated_memory_mb
                <= capacity.memory_limit_mb
                and capacity.health_status in ["healthy", "warning"]
            ):

                # Check capability match
                if self._agent_has_capability(capacity, task.required_capabilities):
                    # Calculate memory-based score
                    memory_available = (
                        capacity.memory_limit_mb - capacity.memory_usage_mb
                    )
                    memory_score = memory_available / capacity.memory_limit_mb
                    task_ratio = (
                        task.estimated_memory_mb / memory_available
                        if memory_available > 0
                        else 0
                    )

                    suitable_agents.append(
                        (agent_id, memory_score - task_ratio, capacity)
                    )

        if not suitable_agents:
            return self._create_no_assignment_decision(task)

        # Sort by memory score (best first)
        suitable_agents.sort(key=lambda x: x[1], reverse=True)
        best_agent_id, score, capacity = suitable_agents[0]

        return LoadBalancingDecision(
            task_id=task.task_id,
            assigned_agent=best_agent_id,
            confidence_score=min(1.0, max(0.0, score)),
            reasoning=[
                f"Selected for optimal memory availability",
                f"Memory available: {capacity.memory_limit_mb - capacity.memory_usage_mb:.1f}MB",
                f"Task memory requirement: {task.estimated_memory_mb:.1f}MB",
            ],
            estimated_completion_time=datetime.now()
            + timedelta(minutes=task.estimated_duration_min),
            resource_allocation={
                "memory_mb": task.estimated_memory_mb,
                "estimated_duration": task.estimated_duration_min,
            },
        )

    def _balance_by_performance(self, task: TaskRequirement) -> LoadBalancingDecision:
        """Balance tasks based on agent performance metrics"""

        suitable_agents = []

        for agent_id, capacity in self.agent_capacities.items():
            if (
                capacity.current_tasks < capacity.max_concurrent_tasks
                and capacity.health_status in ["healthy", "warning"]
                and self._agent_has_capability(capacity, task.required_capabilities)
            ):

                # Calculate performance score
                performance_score = (
                    (capacity.success_rate / 100) * 0.4  # 40% weight to success rate
                    + (1 - min(1.0, capacity.avg_response_time_ms / 1000))
                    * 0.4  # 40% to response time
                    + (
                        1
                        - min(
                            1.0, capacity.current_tasks / capacity.max_concurrent_tasks
                        )
                    )
                    * 0.2  # 20% to load
                )

                suitable_agents.append((agent_id, performance_score, capacity))

        if not suitable_agents:
            return self._create_no_assignment_decision(task)

        suitable_agents.sort(key=lambda x: x[1], reverse=True)
        best_agent_id, score, capacity = suitable_agents[0]

        return LoadBalancingDecision(
            task_id=task.task_id,
            assigned_agent=best_agent_id,
            confidence_score=score,
            reasoning=[
                f"Selected for optimal performance metrics",
                f"Success rate: {capacity.success_rate:.1f}%",
                f"Response time: {capacity.avg_response_time_ms:.0f}ms",
                f"Current load: {capacity.current_tasks}/{capacity.max_concurrent_tasks}",
            ],
            estimated_completion_time=datetime.now()
            + timedelta(minutes=task.estimated_duration_min),
            resource_allocation={
                "performance_optimized": True,
                "expected_quality": capacity.success_rate,
            },
        )

    def _balance_by_capacity(self, task: TaskRequirement) -> LoadBalancingDecision:
        """Balance tasks based on agent capacity availability"""

        suitable_agents = []

        for agent_id, capacity in self.agent_capacities.items():
            if capacity.health_status in [
                "healthy",
                "warning",
            ] and self._agent_has_capability(capacity, task.required_capabilities):

                # Calculate capacity score
                capacity_available = (
                    capacity.max_concurrent_tasks - capacity.current_tasks
                )
                capacity_ratio = capacity_available / capacity.max_concurrent_tasks

                # Factor in memory capacity
                memory_ratio = (
                    capacity.memory_limit_mb - capacity.memory_usage_mb
                ) / capacity.memory_limit_mb

                combined_score = (capacity_ratio * 0.6) + (memory_ratio * 0.4)

                suitable_agents.append((agent_id, combined_score, capacity))

        if not suitable_agents:
            return self._create_no_assignment_decision(task)

        suitable_agents.sort(key=lambda x: x[1], reverse=True)
        best_agent_id, score, capacity = suitable_agents[0]

        return LoadBalancingDecision(
            task_id=task.task_id,
            assigned_agent=best_agent_id,
            confidence_score=score,
            reasoning=[
                f"Selected for optimal capacity availability",
                f"Task slots available: {capacity.max_concurrent_tasks - capacity.current_tasks}",
                f"Memory available: {capacity.memory_limit_mb - capacity.memory_usage_mb:.1f}MB",
            ],
            estimated_completion_time=datetime.now()
            + timedelta(minutes=task.estimated_duration_min),
            resource_allocation={
                "capacity_based": True,
                "load_distribution": "balanced",
            },
        )

    def _hybrid_balancing(self, task: TaskRequirement) -> LoadBalancingDecision:
        """Hybrid balancing considering all factors"""

        suitable_agents = []

        for agent_id, capacity in self.agent_capacities.items():
            if (
                capacity.current_tasks < capacity.max_concurrent_tasks
                and capacity.health_status in ["healthy", "warning"]
                and self._agent_has_capability(capacity, task.required_capabilities)
            ):

                # Calculate hybrid score
                memory_score = (
                    capacity.memory_limit_mb - capacity.memory_usage_mb
                ) / capacity.memory_limit_mb
                performance_score = capacity.success_rate / 100
                capacity_score = (
                    capacity.max_concurrent_tasks - capacity.current_tasks
                ) / capacity.max_concurrent_tasks
                response_score = 1 - min(1.0, capacity.avg_response_time_ms / 1000)

                # Weight the factors
                hybrid_score = (
                    memory_score * 0.3  # 30% memory
                    + performance_score * 0.3  # 30% performance
                    + capacity_score * 0.25  # 25% capacity
                    + response_score * 0.15  # 15% response time
                )

                suitable_agents.append((agent_id, hybrid_score, capacity))

        if not suitable_agents:
            return self._create_no_assignment_decision(task)

        suitable_agents.sort(key=lambda x: x[1], reverse=True)
        best_agent_id, score, capacity = suitable_agents[0]

        return LoadBalancingDecision(
            task_id=task.task_id,
            assigned_agent=best_agent_id,
            confidence_score=score,
            reasoning=[
                f"Selected using hybrid optimization algorithm",
                f"Memory score: {(capacity.memory_limit_mb - capacity.memory_usage_mb) / capacity.memory_limit_mb:.2f}",
                f"Performance score: {capacity.success_rate / 100:.2f}",
                f"Capacity score: {(capacity.max_concurrent_tasks - capacity.current_tasks) / capacity.max_concurrent_tasks:.2f}",
            ],
            estimated_completion_time=datetime.now()
            + timedelta(minutes=task.estimated_duration_min),
            resource_allocation={
                "hybrid_optimized": True,
                "multi_factor_balancing": True,
            },
        )

    def _agent_has_capability(
        self, capacity: AgentCapacity, required_capabilities: List[str]
    ) -> bool:
        """Check if agent has required capabilities"""

        if not required_capabilities:
            return True

        agent_capabilities = set(capacity.specialization_tags)
        required_caps = set(required_capabilities)

        # Check if agent has at least one required capability or can handle general tasks
        return (
            bool(agent_capabilities & required_caps)
            or "general" in required_capabilities
        )

    def _create_no_assignment_decision(
        self, task: TaskRequirement
    ) -> LoadBalancingDecision:
        """Create decision when no suitable agent is available"""

        return LoadBalancingDecision(
            task_id=task.task_id,
            assigned_agent="none",
            confidence_score=0.0,
            reasoning=[
                "No suitable agent available",
                "All agents at capacity or incompatible",
                "Consider waiting or scaling resources",
            ],
            estimated_completion_time=datetime.now()
            + timedelta(hours=24),  # Far future
            resource_allocation={"status": "failed", "reason": "no_capacity"},
        )

    def _rebalance_tasks(self):
        """Rebalance tasks if needed"""

        # Check for agents that are overloaded
        overloaded_agents = [
            agent_id
            for agent_id, capacity in self.agent_capacities.items()
            if capacity.current_tasks >= capacity.max_concurrent_tasks
            or capacity.memory_usage_mb > capacity.memory_limit_mb * 0.8
        ]

        if overloaded_agents:
            logger.info(f"Detected overloaded agents: {overloaded_agents}")
            # Implement rebalancing logic here

    def get_load_balancing_status(self) -> Dict[str, Any]:
        """Get comprehensive load balancing status"""

        current_time = datetime.now()
        total_capacity = sum(
            cap.max_concurrent_tasks for cap in self.agent_capacities.values()
        )
        current_load = sum(cap.current_tasks for cap in self.agent_capacities.values())
        total_memory_mb = sum(
            cap.memory_limit_mb for cap in self.agent_capacities.values()
        )
        used_memory_mb = sum(
            cap.memory_usage_mb for cap in self.agent_capacities.values()
        )

        # Agent health breakdown
        health_counts = defaultdict(int)
        for capacity in self.agent_capacities.values():
            health_counts[capacity.health_status] += 1

        # Performance metrics
        avg_response_time = (
            statistics.mean(
                [cap.avg_response_time_ms for cap in self.agent_capacities.values()]
            )
            if self.agent_capacities
            else 0
        )
        avg_success_rate = (
            statistics.mean(
                [cap.success_rate for cap in self.agent_capacities.values()]
            )
            if self.agent_capacities
            else 0
        )

        return {
            "timestamp": current_time.isoformat(),
            "current_strategy": self.current_strategy,
            "overall_status": {
                "total_agents": len(self.agent_capacities),
                "capacity_utilization_percent": (
                    (current_load / total_capacity * 100) if total_capacity > 0 else 0
                ),
                "memory_utilization_percent": (
                    (used_memory_mb / total_memory_mb * 100)
                    if total_memory_mb > 0
                    else 0
                ),
                "active_tasks": current_load,
                "max_concurrent_tasks": total_capacity,
            },
            "agent_health": dict(health_counts),
            "performance_metrics": {
                "avg_response_time_ms": avg_response_time,
                "avg_success_rate_percent": avg_success_rate,
            },
            "agent_details": {
                agent_id: {
                    "load_percent": (
                        (cap.current_tasks / cap.max_concurrent_tasks * 100)
                        if cap.max_concurrent_tasks > 0
                        else 0
                    ),
                    "memory_percent": (
                        (cap.memory_usage_mb / cap.memory_limit_mb * 100)
                        if cap.memory_limit_mb > 0
                        else 0
                    ),
                    "response_time_ms": cap.avg_response_time_ms,
                    "health": cap.health_status,
                    "specializations": cap.specialization_tags,
                }
                for agent_id, cap in self.agent_capacities.items()
            },
            "optimization_recommendations": self._generate_load_balancing_recommendations(),
        }

    def _generate_load_balancing_recommendations(self) -> List[str]:
        """Generate recommendations for load balancing optimization"""

        recommendations = []

        # Check overall utilization
        if len(self.agent_capacities) > 0:
            total_capacity = sum(
                cap.max_concurrent_tasks for cap in self.agent_capacities.values()
            )
            current_load = sum(
                cap.current_tasks for cap in self.agent_capacities.values()
            )
            utilization = (
                current_load / total_capacity * 100 if total_capacity > 0 else 0
            )

            if utilization > 80:
                recommendations.append(
                    "High system utilization - consider scaling agent resources"
                )
            elif utilization < 30:
                recommendations.append(
                    "Low system utilization - consider agent consolidation"
                )

        # Check for struggling agents
        struggling_agents = [
            agent_id
            for agent_id, cap in self.agent_capacities.items()
            if cap.health_status in ["warning", "critical"]
        ]

        if struggling_agents:
            recommendations.append(
                f"Agent health issues detected: {', '.join(struggling_agents[:2])}"
            )

        # Check strategy effectiveness
        if self.current_strategy == "memory_optimized":
            recommendations.append(
                "Consider switching to hybrid strategy for balanced optimization"
            )

        return recommendations[:5]  # Return top 5 recommendations

    def set_balancing_strategy(self, strategy: str) -> Dict[str, Any]:
        """Change the load balancing strategy"""

        if strategy not in self.balancing_strategies:
            return {
                "success": False,
                "error": f"Unknown strategy: {strategy}",
                "available_strategies": list(self.balancing_strategies.keys()),
            }

        old_strategy = self.current_strategy
        self.current_strategy = strategy

        logger.info(
            f"Load balancing strategy changed from {old_strategy} to {strategy}"
        )

        return {
            "success": True,
            "old_strategy": old_strategy,
            "new_strategy": strategy,
            "timestamp": datetime.now().isoformat(),
        }

    def get_agent_utilization_trends(
        self, agent_id: str, hours: int = 24
    ) -> Dict[str, Any]:
        """Get utilization trends for a specific agent"""

        if agent_id not in self.performance_history:
            return {"error": f"No data available for agent: {agent_id}"}

        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_data = [
            entry
            for entry in self.performance_history[agent_id]
            if entry["timestamp"] > cutoff_time
        ]

        if not recent_data:
            return {"error": "No recent data available"}

        memory_usage = [entry["memory_usage"] for entry in recent_data]
        response_times = [entry["response_time"] for entry in recent_data]

        return {
            "agent_id": agent_id,
            "time_period_hours": hours,
            "data_points": len(recent_data),
            "memory_stats": {
                "avg_mb": statistics.mean(memory_usage),
                "min_mb": min(memory_usage),
                "max_mb": max(memory_usage),
                "trend": (
                    "increasing" if memory_usage[-1] > memory_usage[0] else "decreasing"
                ),
            },
            "response_time_stats": {
                "avg_ms": statistics.mean(response_times),
                "min_ms": min(response_times),
                "max_ms": max(response_times),
            },
            "current_capacity": (
                self.agent_capacities.get(agent_id).__dict__
                if agent_id in self.agent_capacities
                else None
            ),
        }


# Initialize global load balancer
memory_load_balancer = MemoryAwareLoadBalancer()
