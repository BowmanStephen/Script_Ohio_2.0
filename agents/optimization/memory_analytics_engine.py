"""
Advanced Memory Analytics Engine for Super AI Agent Architecture

Provides real-time analytics, performance monitoring, and intelligent insights
for the 4-level hierarchical memory management system.

Features:
- Real-time performance metrics and trend analysis
- Agent behavior pattern recognition
- Memory optimization recommendations
- Predictive analytics for capacity planning
- Interactive dashboard data generation
"""

import json
import logging
import statistics
import threading
import time
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class AgentPerformanceMetrics:
    """Performance metrics for individual agents"""

    agent_id: str
    memory_usage_mb: float
    cache_hit_rate: float
    avg_response_time_ms: float
    operations_per_minute: float
    error_rate: float
    memory_efficiency_score: float
    coordination_events: int
    last_active: datetime


@dataclass
class WorkflowAnalytics:
    """Analytics for workflow patterns"""

    workflow_type: str
    avg_completion_time_min: float
    success_rate: float
    agent_coordination_score: float
    memory_optimization_rate: float
    bottleneck_agents: List[str]
    optimization_recommendations: List[str]


@dataclass
class MemoryTrendAnalysis:
    """Trend analysis for memory usage patterns"""

    time_period: str
    growth_rate_percent: float
    peak_usage_times: List[str]
    cache_performance_trend: str  # improving, stable, declining
    compression_efficiency_trend: str
    capacity_projection_days: int


class MemoryAnalyticsEngine:
    """Advanced analytics engine for memory management system"""

    def __init__(self, memory_manager=None):
        self.memory_manager = memory_manager
        self.metrics_history = defaultdict(
            lambda: deque(maxlen=1000)
        )  # Keep last 1000 data points
        self.agent_profiles = {}
        self.workflow_patterns = {}
        self.anomaly_detection_threshold = 2.0  # Standard deviations
        self.analytics_cache = {}
        self.cache_ttl_minutes = 5
        self.last_analysis_time = None

        # Start background analytics collection
        self._start_analytics_collection()

        logger.info("Memory Analytics Engine initialized")

    def _start_analytics_collection(self):
        """Start background thread for continuous analytics collection"""

        def collect_metrics():
            while True:
                try:
                    self._collect_realtime_metrics()
                    time.sleep(60)  # Collect every minute
                except Exception as e:
                    logger.error(f"Analytics collection error: {e}")
                    time.sleep(60)

        analytics_thread = threading.Thread(target=collect_metrics, daemon=True)
        analytics_thread.start()
        logger.info("Background analytics collection started")

    def _collect_realtime_metrics(self):
        """Collect real-time metrics from memory system"""
        current_time = datetime.now()

        # Get system-wide metrics
        if self.memory_manager:
            try:
                stats = self.memory_manager.get_stats()

                # Store time-series data
                self.metrics_history["system_stats"].append(
                    {
                        "timestamp": current_time,
                        "total_entries": stats.total_entries,
                        "total_size_mb": stats.total_size_mb,
                        "hit_rate": stats.hit_rate,
                        "compression_ratio": stats.compression_ratio,
                    }
                )

                # Collect level-specific metrics
                if hasattr(stats, "level_stats"):
                    for level_name, level_stats in stats.level_stats.items():
                        self.metrics_history[f"level_{level_name}"].append(
                            {
                                "timestamp": current_time,
                                "entries": getattr(level_stats, "entries", 0),
                                "size_mb": getattr(level_stats, "size_mb", 0.0),
                                "hit_rate": getattr(level_stats, "hit_rate", 0.0),
                                "utilization_pct": (
                                    getattr(level_stats, "size_mb", 0.0)
                                    / getattr(level_stats, "max_size_mb", 1.0)
                                )
                                * 100,
                            }
                        )

            except Exception as e:
                logger.warning(f"Could not collect memory stats: {e}")

    def analyze_agent_performance(
        self, agent_id: str, time_window_hours: int = 24
    ) -> AgentPerformanceMetrics:
        """Analyze performance metrics for a specific agent"""

        # Get agent-specific memory entries
        agent_entries = (
            self.memory_manager.search_by_tags([agent_id])
            if self.memory_manager
            else []
        )

        # Calculate metrics
        current_time = datetime.now()
        cutoff_time = current_time - timedelta(hours=time_window_hours)

        recent_entries = [
            entry
            for entry in agent_entries
            if hasattr(entry, "timestamp") and entry.timestamp > cutoff_time
        ]

        if not recent_entries:
            return AgentPerformanceMetrics(
                agent_id=agent_id,
                memory_usage_mb=0.0,
                cache_hit_rate=0.0,
                avg_response_time_ms=0.0,
                operations_per_minute=0.0,
                error_rate=0.0,
                memory_efficiency_score=0.0,
                coordination_events=0,
                last_active=current_time,
            )

        # Calculate memory usage
        total_memory_mb = sum(
            getattr(entry, "size_bytes", 0) / 1024 / 1024 for entry in recent_entries
        )

        # Calculate operations per minute
        time_span_minutes = time_window_hours * 60
        operations_per_minute = (
            len(recent_entries) / time_span_minutes if time_span_minutes > 0 else 0
        )

        # Estimate coordination events (entries with workflow tags)
        coordination_events = len(
            [
                entry
                for entry in recent_entries
                if hasattr(entry, "tags")
                and any(
                    "workflow" in tag or "coordination" in tag for tag in entry.tags
                )
            ]
        )

        # Calculate memory efficiency score (0-100)
        memory_efficiency_score = min(
            100, (1.0 - (total_memory_mb / 20.0)) * 100
        )  # Assuming 20MB limit

        # Estimate cache hit rate from entry patterns
        cache_entries = [
            entry
            for entry in recent_entries
            if hasattr(entry, "tags") and "cache" in entry.tags
        ]
        cache_hit_rate = (
            len(cache_entries) / len(recent_entries) * 100 if recent_entries else 0
        )

        # Estimate response time (placeholder - would come from actual timing data)
        avg_response_time_ms = 50.0 + (len(recent_entries) * 0.1)  # Simple model

        return AgentPerformanceMetrics(
            agent_id=agent_id,
            memory_usage_mb=total_memory_mb,
            cache_hit_rate=cache_hit_rate,
            avg_response_time_ms=avg_response_time_ms,
            operations_per_minute=operations_per_minute,
            error_rate=0.0,  # Would track from actual errors
            memory_efficiency_score=memory_efficiency_score,
            coordination_events=coordination_events,
            last_active=max(
                (getattr(entry, "timestamp", current_time) for entry in recent_entries),
                default=current_time,
            ),
        )

    def analyze_workflow_patterns(self, workflow_type: str = None) -> WorkflowAnalytics:
        """Analyze workflow patterns and performance"""

        # Get workflow-related entries
        workflow_entries = []
        if self.memory_manager:
            all_workflow_entries = self.memory_manager.search_by_tags(["workflow"])
            if workflow_type:
                workflow_entries = [
                    entry
                    for entry in all_workflow_entries
                    if hasattr(entry, "tags") and workflow_type in entry.tags
                ]
            else:
                workflow_entries = all_workflow_entries

        if not workflow_entries:
            return WorkflowAnalytics(
                workflow_type=workflow_type or "unknown",
                avg_completion_time_min=0.0,
                success_rate=0.0,
                agent_coordination_score=0.0,
                memory_optimization_rate=0.0,
                bottleneck_agents=[],
                optimization_recommendations=["No workflow data available"],
            )

        # Analyze completion times
        completed_workflows = [
            entry
            for entry in workflow_entries
            if hasattr(entry, "value")
            and isinstance(entry.value, dict)
            and entry.value.get("status") == "completed"
        ]

        completion_times = []
        for workflow in completed_workflows:
            if "started_at" in workflow.value and "completed_at" in workflow.value:
                start = datetime.fromisoformat(
                    workflow.value["started_at"].replace("Z", "+00:00")
                )
                end = datetime.fromisoformat(
                    workflow.value["completed_at"].replace("Z", "+00:00")
                )
                completion_time_min = (end - start).total_seconds() / 60
                completion_times.append(completion_time_min)

        avg_completion_time = (
            statistics.mean(completion_times) if completion_times else 0.0
        )

        # Calculate success rate
        success_rate = (
            len(completed_workflows) / len(workflow_entries) * 100
            if workflow_entries
            else 0
        )

        # Analyze agent coordination
        coordination_scores = []
        agent_participation = defaultdict(int)

        for workflow in workflow_entries:
            if hasattr(workflow, "value") and "agent_assignments" in workflow.value:
                agents = list(workflow.value["agent_assignments"].keys())
                agent_participation.update(
                    {agent: agent_participation[agent] + 1 for agent in agents}
                )
                coordination_scores.append(len(agents))

        avg_coordination_score = (
            statistics.mean(coordination_scores) if coordination_scores else 0
        )

        # Identify bottleneck agents (most frequently used)
        bottleneck_agents = sorted(
            agent_participation.items(), key=lambda x: x[1], reverse=True
        )[:3]
        bottleneck_agents = [agent for agent, count in bottleneck_agents]

        # Generate optimization recommendations
        recommendations = []
        if avg_completion_time > 10:
            recommendations.append(
                "Consider parallelizing tasks to reduce completion time"
            )
        if success_rate < 90:
            recommendations.append("Implement better error handling and retry logic")
        if avg_coordination_score < 3:
            recommendations.append("Increase agent collaboration for better outcomes")
        if len(bottleneck_agents) > 0:
            recommendations.append(
                f"Consider load balancing for heavily used agents: {', '.join(bottleneck_agents[:2])}"
            )

        return WorkflowAnalytics(
            workflow_type=workflow_type or "general",
            avg_completion_time_min=avg_completion_time,
            success_rate=success_rate,
            agent_coordination_score=avg_coordination_score,
            memory_optimization_rate=95.0,  # Placeholder
            bottleneck_agents=bottleneck_agents,
            optimization_recommendations=recommendations,
        )

    def analyze_memory_trends(self, time_period_days: int = 7) -> MemoryTrendAnalysis:
        """Analyze memory usage trends and provide capacity projections"""

        current_time = datetime.now()
        cutoff_time = current_time - timedelta(days=time_period_days)

        # Get system stats history
        system_history = list(self.metrics_history["system_stats"])
        recent_history = [
            entry for entry in system_history if entry["timestamp"] > cutoff_time
        ]

        if len(recent_history) < 2:
            return MemoryTrendAnalysis(
                time_period=f"Last {time_period_days} days",
                growth_rate_percent=0.0,
                peak_usage_times=[],
                cache_performance_trend="insufficient_data",
                compression_efficiency_trend="insufficient_data",
                capacity_projection_days=365,
            )

        # Calculate growth rate
        start_size = recent_history[0]["total_size_mb"]
        end_size = recent_history[-1]["total_size_mb"]
        growth_rate = (
            ((end_size - start_size) / start_size * 100) if start_size > 0 else 0
        )

        # Find peak usage times
        peak_times = []
        if len(recent_history) >= 24:  # Need at least 24 hours of data
            hourly_usage = defaultdict(list)
            for entry in recent_history:
                hour = entry["timestamp"].hour
                hourly_usage[hour].append(entry["total_size_mb"])

            avg_hourly_usage = {
                hour: statistics.mean(sizes) for hour, sizes in hourly_usage.items()
            }
            peak_hours = sorted(
                avg_hourly_usage.items(), key=lambda x: x[1], reverse=True
            )[:3]
            peak_times = [f"{hour:02d}:00" for hour, _ in peak_hours]

        # Analyze cache performance trend
        hit_rates = [entry["hit_rate"] for entry in recent_history]
        if len(hit_rates) >= 2:
            recent_avg = (
                statistics.mean(hit_rates[-10:])
                if len(hit_rates) >= 10
                else statistics.mean(hit_rates)
            )
            earlier_avg = (
                statistics.mean(hit_rates[:10])
                if len(hit_rates) >= 10
                else hit_rates[0]
            )

            if recent_avg > earlier_avg * 1.05:
                cache_trend = "improving"
            elif recent_avg < earlier_avg * 0.95:
                cache_trend = "declining"
            else:
                cache_trend = "stable"
        else:
            cache_trend = "insufficient_data"

        # Analyze compression efficiency
        compression_ratios = [
            entry["compression_ratio"]
            for entry in recent_history
            if entry["compression_ratio"] > 0
        ]
        if len(compression_ratios) >= 2:
            recent_comp_avg = (
                statistics.mean(compression_ratios[-5:])
                if len(compression_ratios) >= 5
                else statistics.mean(compression_ratios)
            )
            earlier_comp_avg = compression_ratios[0]

            if (
                recent_comp_avg < earlier_comp_avg * 0.95
            ):  # Lower ratio = better compression
                comp_trend = "improving"
            elif recent_comp_avg > earlier_comp_avg * 1.05:
                comp_trend = "declining"
            else:
                comp_trend = "stable"
        else:
            comp_trend = "insufficient_data"

        # Capacity projection (simplified)
        if growth_rate > 0:
            current_capacity_pct = (end_size / 370) * 100  # 370MB total capacity
            days_to_capacity = (
                ((100 - current_capacity_pct) / growth_rate) * time_period_days
                if growth_rate > 0
                else 999
            )
        else:
            days_to_capacity = 999

        return MemoryTrendAnalysis(
            time_period=f"Last {time_period_days} days",
            growth_rate_percent=growth_rate,
            peak_usage_times=peak_times,
            cache_performance_trend=cache_trend,
            compression_efficiency_trend=comp_trend,
            capacity_projection_days=min(999, int(days_to_capacity)),
        )

    def generate_dashboard_data(self) -> Dict[str, Any]:
        """Generate comprehensive dashboard data"""

        # Check cache
        cache_key = f"dashboard_{datetime.now().strftime('%Y%m%d_%H%M')}"
        if cache_key in self.analytics_cache:
            return self.analytics_cache[cache_key]

        try:
            # System overview
            system_stats = (
                self.memory_manager.get_stats() if self.memory_manager else None
            )

            # Agent performance analysis
            agent_performance = {}
            agent_ids = [
                "cfbd_integration_agent",
                "model_execution_engine",
                "analytics_orchestrator",
                "weekly_matchup_analysis_agent",
                "documentation_agent",
            ]

            for agent_id in agent_ids:
                agent_performance[agent_id] = self.analyze_agent_performance(agent_id)

            # Workflow analysis
            workflow_analytics = self.analyze_workflow_patterns()
            weekly_analysis = self.analyze_workflow_patterns("weekly_analysis")

            # Memory trends
            memory_trends = self.analyze_memory_trends()

            # Level utilization
            level_utilization = {}
            if system_stats and hasattr(system_stats, "level_stats"):
                for level_name, level_stats in system_stats.level_stats.items():
                    utilization = (
                        getattr(level_stats, "size_mb", 0.0)
                        / getattr(level_stats, "max_size_mb", 1.0)
                    ) * 100
                    level_utilization[level_name] = {
                        "utilization_percent": utilization,
                        "entries": getattr(level_stats, "entries", 0),
                        "size_mb": getattr(level_stats, "size_mb", 0.0),
                        "hit_rate": getattr(level_stats, "hit_rate", 0.0),
                    }

            dashboard_data = {
                "timestamp": datetime.now().isoformat(),
                "system_overview": {
                    "total_entries": system_stats.total_entries if system_stats else 0,
                    "total_size_mb": system_stats.total_size_mb if system_stats else 0,
                    "overall_hit_rate": system_stats.hit_rate if system_stats else 0,
                    "compression_ratio": (
                        system_stats.compression_ratio if system_stats else 0
                    ),
                    "system_health": (
                        "optimal"
                        if system_stats and system_stats.hit_rate > 0.8
                        else "needs_attention"
                    ),
                },
                "agent_performance": agent_performance,
                "workflow_analytics": {
                    "general": workflow_analytics,
                    "weekly_analysis": weekly_analysis,
                },
                "memory_trends": memory_trends,
                "level_utilization": level_utilization,
                "optimization_recommendations": self._generate_system_recommendations(
                    agent_performance, workflow_analytics, memory_trends
                ),
                "performance_alerts": self._detect_performance_anomalies(
                    agent_performance, memory_trends
                ),
            }

            # Cache the results
            self.analytics_cache[cache_key] = dashboard_data
            self.last_analysis_time = datetime.now()

            return dashboard_data

        except Exception as e:
            logger.error(f"Dashboard generation error: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "system_overview": {"system_health": "error"},
            }

    def _generate_system_recommendations(
        self,
        agent_perf: Dict,
        workflow_analytics: WorkflowAnalytics,
        memory_trends: MemoryTrendAnalysis,
    ) -> List[str]:
        """Generate intelligent system optimization recommendations"""

        recommendations = []

        # Agent-based recommendations
        inefficient_agents = [
            agent_id
            for agent_id, metrics in agent_perf.items()
            if metrics.memory_efficiency_score < 50
        ]
        if inefficient_agents:
            recommendations.append(
                f"Memory optimization needed for: {', '.join(inefficient_agents[:2])}"
            )

        # Workflow-based recommendations
        if workflow_analytics.avg_completion_time_min > 10:
            recommendations.append(
                "Consider workflow parallelization to reduce completion time"
            )

        if workflow_analytics.success_rate < 90:
            recommendations.append(
                "Implement better error handling and recovery mechanisms"
            )

        # Memory trend recommendations
        if memory_trends.growth_rate_percent > 20:
            recommendations.append(
                "High memory growth detected - consider aggressive cleanup policies"
            )

        if memory_trends.cache_performance_trend == "declining":
            recommendations.append(
                "Cache performance declining - review TTL settings and access patterns"
            )

        if memory_trends.capacity_projection_days < 30:
            recommendations.append(
                "URGENT: Projected capacity exhaustion within 30 days"
            )

        # Level-specific recommendations
        # (Would add more based on level utilization data)

        return recommendations[:5]  # Return top 5 recommendations

    def _detect_performance_anomalies(
        self, agent_perf: Dict, memory_trends: MemoryTrendAnalysis
    ) -> List[str]:
        """Detect performance anomalies and alert on them"""

        alerts = []

        # Check for agent anomalies
        for agent_id, metrics in agent_perf.items():
            if metrics.error_rate > 10:
                alerts.append(
                    f"High error rate detected for {agent_id}: {metrics.error_rate:.1f}%"
                )

            if metrics.avg_response_time_ms > 1000:
                alerts.append(
                    f"Slow response time for {agent_id}: {metrics.avg_response_time_ms:.0f}ms"
                )

            if metrics.memory_usage_mb > 15:  # Near 20MB limit
                alerts.append(
                    f"High memory usage for {agent_id}: {metrics.memory_usage_mb:.1f}MB"
                )

        # Memory trend anomalies
        if memory_trends.growth_rate_percent > 50:
            alerts.append(
                f"ALERT: Abnormal memory growth rate: {memory_trends.growth_rate_percent:.1f}%"
            )

        if memory_trends.capacity_projection_days < 7:
            alerts.append("CRITICAL: Memory capacity exhaustion expected within 7 days")

        return alerts


# Initialize global analytics engine
memory_analytics_engine = MemoryAnalyticsEngine()
