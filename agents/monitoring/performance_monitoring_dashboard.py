#!/usr/bin/env python3
"""
📊 ScriptOhio Performance Monitoring Dashboard

Comprehensive performance monitoring and alerting system for the
autonomous orchestration platform.

Key Features:
- Real-time performance metrics collection
- Interactive dashboard with live updates
- Alert system for performance degradation
- Historical performance analysis
- Resource usage tracking and optimization
- Agent health monitoring and SLA tracking
- Predictive performance analytics

Author: ScriptOhio AI System
Version: 1.0.0
"""

import asyncio
import json
import logging
import sqlite3
import statistics
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import time
import threading
from collections import defaultdict, deque
import psutil

# Add project root to path
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from agents.core.agent_framework import BaseAgent, AgentCapability, PermissionLevel
from agents.autonomous_orchestration_agent import autonomous_orchestration_agent
from agents.resilience.autonomous_resilience_agent import autonomous_resilience_agent
from agents.scheduling.autonomous_workflow_scheduler import autonomous_workflow_scheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Performance metric definition"""
    name: str
    value: float
    unit: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentMetrics:
    """Agent-specific performance metrics"""
    agent_id: str
    agent_name: str
    status: str
    uptime_seconds: float
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time: float
    error_rate: float
    memory_usage_mb: float
    cpu_usage_percent: float
    last_activity: Optional[datetime] = None


@dataclass
class AlertDefinition:
    """Alert definition"""
    alert_id: str
    name: str
    description: str
    metric_name: str
    condition: str  # "gt", "lt", "eq", "gte", "lte"
    threshold: float
    severity: str  # "low", "medium", "high", "critical"
    enabled: bool = True
    cooldown_minutes: int = 15
    last_triggered: Optional[datetime] = None


@dataclass
class Alert:
    """Active alert"""
    alert_id: str
    name: str
    severity: str
    message: str
    triggered_at: datetime
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class MetricsCollector:
    """Collects and stores performance metrics"""

    def __init__(self):
        self.metrics_history = defaultdict(lambda: deque(maxlen=1000))  # Keep last 1000 points
        self.collection_interval = 30  # seconds
        self.is_collecting = False

    def start_collection(self):
        """Start metrics collection"""
        if not self.is_collecting:
            self.is_collecting = True
            threading.Thread(target=self._collection_loop, daemon=True).start()
            logger.info("Metrics collection started")

    def stop_collection(self):
        """Stop metrics collection"""
        self.is_collecting = False
        logger.info("Metrics collection stopped")

    def _collection_loop(self):
        """Main collection loop"""
        while self.is_collecting:
            try:
                self._collect_system_metrics()
                self._collect_agent_metrics()
                time.sleep(self.collection_interval)
            except Exception as e:
                logger.error(f"Error in metrics collection: {e}")
                time.sleep(5)

    def _collect_system_metrics(self):
        """Collect system-level metrics"""
        timestamp = datetime.now(timezone.utc)

        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        self._add_metric("system.cpu.percent", cpu_percent, "percent", timestamp)

        # Memory metrics
        memory = psutil.virtual_memory()
        self._add_metric("system.memory.percent", memory.percent, "percent", timestamp)
        self._add_metric("system.memory.available_gb", memory.available / (1024**3), "GB", timestamp)

        # Disk metrics
        disk = psutil.disk_usage('/')
        self._add_metric("system.disk.percent", (disk.used / disk.total) * 100, "percent", timestamp)
        self._add_metric("system.disk.free_gb", disk.free / (1024**3), "GB", timestamp)

        # Network metrics
        network = psutil.net_io_counters()
        self._add_metric("system.network.bytes_sent", network.bytes_sent, "bytes", timestamp)
        self._add_metric("system.network.bytes_recv", network.bytes_recv, "bytes", timestamp)

    def _collect_agent_metrics(self):
        """Collect agent-specific metrics"""
        timestamp = datetime.now(timezone.utc)

        try:
            # Autonomous orchestration agent metrics
            orch_status = autonomous_orchestration_agent.get_system_status()
            self._add_metric("agent.orchestration.active_tasks", orch_status.get("active_tasks", 0), "count", timestamp)
            self._add_metric("agent.orchestration.completed_tasks", orch_status.get("completed_tasks", 0), "count", timestamp)
            self._add_metric("agent.orchestration.failed_tasks", orch_status.get("failed_tasks", 0), "count", timestamp)
            self._add_metric("agent.orchestration.response_time", orch_status.get("average_response_time", 0), "seconds", timestamp)

            # Resilience agent metrics
            resilience_status = autonomous_resilience_agent.get_resilience_status()
            self._add_metric("agent.resilience.total_errors", resilience_status["error_metrics"]["total_errors"], "count", timestamp)
            self._add_metric("agent.resilience.error_rate", resilience_status["error_metrics"]["error_rate_24h"], "percent", timestamp)

            # Scheduler agent metrics
            scheduler_status = autonomous_workflow_scheduler.get_scheduler_status()
            self._add_metric("agent.scheduler.total_tasks", scheduler_status["task_summary"]["total_tasks"], "count", timestamp)
            self._add_metric("agent.scheduler.running_tasks", scheduler_status["task_summary"]["running_tasks"], "count", timestamp)

        except Exception as e:
            logger.error(f"Error collecting agent metrics: {e}")

    def _add_metric(self, name: str, value: float, unit: str, timestamp: datetime, tags: Dict = None):
        """Add a metric to the history"""
        metric = PerformanceMetric(
            name=name,
            value=value,
            unit=unit,
            timestamp=timestamp,
            tags=tags or {}
        )
        self.metrics_history[name].append(metric)

    def get_metric_history(self, metric_name: str, hours: int = 24) -> List[PerformanceMetric]:
        """Get metric history for specified time period"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        return [m for m in self.metrics_history[metric_name] if m.timestamp >= cutoff_time]

    def get_current_metrics(self) -> Dict[str, float]:
        """Get current values of all metrics"""
        current_metrics = {}
        for metric_name, metric_queue in self.metrics_history.items():
            if metric_queue:
                current_metrics[metric_name] = metric_queue[-1].value
        return current_metrics

    def get_metric_summary(self, metric_name: str, hours: int = 24) -> Dict[str, float]:
        """Get statistical summary of a metric"""
        metrics = self.get_metric_history(metric_name, hours)
        if not metrics:
            return {}

        values = [m.value for m in metrics]
        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": statistics.mean(values),
            "median": statistics.median(values),
            "p95": statistics.quantiles(values, n=20)[18] if len(values) >= 20 else max(values),
            "p99": statistics.quantiles(values, n=100)[98] if len(values) >= 100 else max(values)
        }


class AlertManager:
    """Manages alerts and notifications"""

    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
        self.alerts: Dict[str, Alert] = {}
        self.alert_definitions = self._load_default_alerts()
        self.is_monitoring = False
        self.monitoring_interval = 60  # seconds

    def _load_default_alerts(self) -> Dict[str, AlertDefinition]:
        """Load default alert definitions"""
        return {
            "high_cpu_usage": AlertDefinition(
                alert_id="high_cpu_usage",
                name="High CPU Usage",
                description="CPU usage is above threshold",
                metric_name="system.cpu.percent",
                condition="gt",
                threshold=80.0,
                severity="high"
            ),
            "high_memory_usage": AlertDefinition(
                alert_id="high_memory_usage",
                name="High Memory Usage",
                description="Memory usage is above threshold",
                metric_name="system.memory.percent",
                condition="gt",
                threshold=85.0,
                severity="high"
            ),
            "low_disk_space": AlertDefinition(
                alert_id="low_disk_space",
                name="Low Disk Space",
                description="Available disk space is below threshold",
                metric_name="system.disk.percent",
                condition="gt",
                threshold=90.0,
                severity="critical"
            ),
            "high_error_rate": AlertDefinition(
                alert_id="high_error_rate",
                name="High Error Rate",
                description="System error rate is above threshold",
                metric_name="agent.resilience.error_rate",
                condition="gt",
                threshold=10.0,
                severity="medium"
            ),
            "slow_response_time": AlertDefinition(
                alert_id="slow_response_time",
                name="Slow Response Time",
                description="Agent response time is above threshold",
                metric_name="agent.orchestration.response_time",
                condition="gt",
                threshold=5.0,
                severity="medium"
            )
        }

    def start_monitoring(self):
        """Start alert monitoring"""
        if not self.is_monitoring:
            self.is_monitoring = True
            threading.Thread(target=self._monitoring_loop, daemon=True).start()
            logger.info("Alert monitoring started")

    def stop_monitoring(self):
        """Stop alert monitoring"""
        self.is_monitoring = False
        logger.info("Alert monitoring stopped")

    def _monitoring_loop(self):
        """Main alert monitoring loop"""
        while self.is_monitoring:
            try:
                self._check_alerts()
                time.sleep(self.monitoring_interval)
            except Exception as e:
                logger.error(f"Error in alert monitoring: {e}")
                time.sleep(10)

    def _check_alerts(self):
        """Check all alert conditions"""
        current_metrics = self.metrics_collector.get_current_metrics()

        for alert_def in self.alert_definitions.values():
            if not alert_def.enabled:
                continue

            # Check cooldown period
            if (alert_def.last_triggered and
                datetime.now(timezone.utc) - alert_def.last_triggered < timedelta(minutes=alert_def.cooldown_minutes)):
                continue

            # Get current metric value
            metric_value = current_metrics.get(alert_def.metric_name)
            if metric_value is None:
                continue

            # Check alert condition
            triggered = False
            if alert_def.condition == "gt" and metric_value > alert_def.threshold:
                triggered = True
            elif alert_def.condition == "lt" and metric_value < alert_def.threshold:
                triggered = True
            elif alert_def.condition == "gte" and metric_value >= alert_def.threshold:
                triggered = True
            elif alert_def.condition == "lte" and metric_value <= alert_def.threshold:
                triggered = True
            elif alert_def.condition == "eq" and abs(metric_value - alert_def.threshold) < 0.001:
                triggered = True

            if triggered:
                self._trigger_alert(alert_def, metric_value)
            else:
                self._resolve_alert(alert_def.alert_id)

    def _trigger_alert(self, alert_def: AlertDefinition, current_value: float):
        """Trigger an alert"""
        alert_id = alert_def.alert_id

        if alert_id not in self.alerts or self.alerts[alert_id].resolved_at:
            # New alert or resolved alert being triggered again
            message = f"{alert_def.name}: {alert_def.description}. Current value: {current_value}{alert_def.threshold}"

            alert = Alert(
                alert_id=alert_id,
                name=alert_def.name,
                severity=alert_def.severity,
                message=message,
                triggered_at=datetime.now(timezone.utc),
                metadata={"threshold": alert_def.threshold, "current_value": current_value}
            )

            self.alerts[alert_id] = alert
            alert_def.last_triggered = datetime.now(timezone.utc)

            logger.warning(f"Alert triggered: {message}")

    def _resolve_alert(self, alert_id: str):
        """Resolve an alert"""
        if alert_id in self.alerts and not self.alerts[alert_id].resolved_at:
            self.alerts[alert_id].resolved_at = datetime.now(timezone.utc)
            logger.info(f"Alert resolved: {self.alerts[alert_id].name}")

    def get_active_alerts(self) -> List[Alert]:
        """Get all active (unresolved) alerts"""
        return [alert for alert in self.alerts.values() if alert.resolved_at is None]

    def get_alert_history(self, hours: int = 24) -> List[Alert]:
        """Get alert history for specified time period"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        return [alert for alert in self.alerts.values() if alert.triggered_at >= cutoff_time]


class PerformanceMonitoringDashboard(BaseAgent):
    """Performance monitoring dashboard for autonomous orchestration"""

    def __init__(self):
        super().__init__(
            agent_id="performance_monitoring_dashboard",
            name="ScriptOhio Performance Monitoring Dashboard",
            permission_level=PermissionLevel.READ_ONLY
        )

        # Database setup
        self.db_path = Path("project_management/monitoring/performance_dashboard.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

        # Monitoring components
        self.metrics_collector = MetricsCollector()
        self.alert_manager = AlertManager(self.metrics_collector)

        # Dashboard state
        self.dashboard_active = False
        self.last_update = None

    def _init_database(self):
        """Initialize SQLite database for performance data"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS performance_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    metrics TEXT NOT NULL,
                    alerts TEXT
                )
            ''')

            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_timestamp ON performance_snapshots(timestamp)
            ''')

            conn.execute('''
                CREATE TABLE IF NOT EXISTS agent_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    agent_id TEXT NOT NULL,
                    metrics TEXT NOT NULL
                )
            ''')

            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_agent_timestamp ON agent_performance(timestamp, agent_id)
            ''')

    def _define_capabilities(self) -> List[AgentCapability]:
        """Define agent capabilities"""
        return [
            AgentCapability(
                name="get_dashboard_overview",
                description="Get comprehensive dashboard overview",
                execution_time_estimate=5.0,
                required_permissions=[PermissionLevel.READ_ONLY],
                parameters=[],
                returns={"overview": "object", "metrics": "object", "alerts": "object"}
            ),
            AgentCapability(
                name="get_performance_metrics",
                description="Get detailed performance metrics",
                execution_time_estimate=3.0,
                required_permissions=[PermissionLevel.READ_ONLY],
                parameters=["metric_names", "time_range_hours"],
                returns={"metrics": "object", "summaries": "object"}
            ),
            AgentCapability(
                name="get_system_health",
                description="Get overall system health assessment",
                execution_time_estimate=3.0,
                required_permissions=[PermissionLevel.READ_ONLY],
                parameters=["detailed"],
                returns={"health_score": "float", "components": "object", "issues": "list"}
            ),
            AgentCapability(
                name="start_monitoring",
                description="Start performance monitoring",
                execution_time_estimate=2.0,
                required_permissions=[PermissionLevel.READ_EXECUTE],
                parameters=["collection_interval"],
                returns={"status": "string", "monitoring_active": "boolean"}
            ),
            AgentCapability(
                name="get_alerts",
                description="Get current alerts and alert history",
                execution_time_estimate=2.0,
                required_permissions=[PermissionLevel.READ_ONLY],
                parameters=["include_resolved", "hours"],
                returns={"active_alerts": "list", "alert_history": "list"}
            )
        ]

    def _execute_action(self, action: str, parameters: Dict, user_context: Dict) -> Dict:
        """Execute agent actions"""
        try:
            if action == "get_dashboard_overview":
                return self._get_dashboard_overview()

            elif action == "get_performance_metrics":
                return self._get_performance_metrics(
                    parameters.get("metric_names", []),
                    parameters.get("time_range_hours", 24)
                )

            elif action == "get_system_health":
                return self._get_system_health(parameters.get("detailed", False))

            elif action == "start_monitoring":
                return self._start_monitoring(parameters.get("collection_interval", 30))

            elif action == "get_alerts":
                return self._get_alerts(
                    parameters.get("include_resolved", False),
                    parameters.get("hours", 24)
                )

            else:
                raise ValueError(f"Unknown action: {action}")

        except Exception as e:
            logger.error(f"Error in dashboard agent {action}: {e}")
            return {
                "status": "error",
                "error": str(e),
                "agent_id": self.agent_id
            }

    def _get_dashboard_overview(self) -> Dict:
        """Get comprehensive dashboard overview"""
        current_metrics = self.metrics_collector.get_current_metrics()
        active_alerts = self.alert_manager.get_active_alerts()

        # System health assessment
        health_score = self._calculate_health_score(current_metrics, active_alerts)

        # Agent status summary
        agent_summary = {
            "orchestration_agent": {
                "status": "active",
                "active_tasks": current_metrics.get("agent.orchestration.active_tasks", 0),
                "completed_today": current_metrics.get("agent.orchestration.completed_tasks", 0)
            },
            "resilience_agent": {
                "status": "active",
                "total_errors": current_metrics.get("agent.resilience.total_errors", 0),
                "error_rate": current_metrics.get("agent.resilience.error_rate", 0)
            },
            "scheduler_agent": {
                "status": "active" if autonomous_workflow_scheduler.is_running else "inactive",
                "total_tasks": current_metrics.get("agent.scheduler.total_tasks", 0),
                "running_tasks": current_metrics.get("agent.scheduler.running_tasks", 0)
            }
        }

        # Recent performance trends
        performance_trends = self._calculate_performance_trends()

        return {
            "status": "success",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "health_score": health_score,
            "active_alerts_count": len(active_alerts),
            "system_metrics": {
                "cpu_usage": current_metrics.get("system.cpu.percent", 0),
                "memory_usage": current_metrics.get("system.memory.percent", 0),
                "disk_usage": current_metrics.get("system.disk.percent", 0),
                "available_memory_gb": current_metrics.get("system.memory.available_gb", 0)
            },
            "agent_summary": agent_summary,
            "performance_trends": performance_trends,
            "active_alerts": [
                {
                    "id": alert.alert_id,
                    "name": alert.name,
                    "severity": alert.severity,
                    "message": alert.message,
                    "triggered_at": alert.triggered_at.isoformat()
                }
                for alert in active_alerts
            ]
        }

    def _get_performance_metrics(self, metric_names: List[str], time_range_hours: int) -> Dict:
        """Get detailed performance metrics"""
        if not metric_names:
            # Return all available metrics
            metric_names = list(self.metrics_collector.metrics_history.keys())

        metrics_data = {}
        summaries = {}

        for metric_name in metric_names:
            history = self.metrics_collector.get_metric_history(metric_name, time_range_hours)
            summary = self.metrics_collector.get_metric_summary(metric_name, time_range_hours)

            # Convert to serializable format
            metrics_data[metric_name] = [
                {
                    "timestamp": metric.timestamp.isoformat(),
                    "value": metric.value,
                    "unit": metric.unit,
                    "tags": metric.tags
                }
                for metric in history
            ]

            if summary:
                summaries[metric_name] = {
                    "count": summary["count"],
                    "min": round(summary["min"], 2),
                    "max": round(summary["max"], 2),
                    "average": round(summary["avg"], 2),
                    "median": round(summary["median"], 2),
                    "p95": round(summary["p95"], 2) if "p95" in summary else None,
                    "p99": round(summary["p99"], 2) if "p99" in summary else None
                }

        return {
            "status": "success",
            "time_range_hours": time_range_hours,
            "metrics": metrics_data,
            "summaries": summaries,
            "total_metrics": len(metric_names)
        }

    def _get_system_health(self, detailed: bool = False) -> Dict:
        """Get overall system health assessment"""
        current_metrics = self.metrics_collector.get_current_metrics()
        active_alerts = self.alert_manager.get_active_alerts()

        # Calculate health score (0-100)
        health_score = self._calculate_health_score(current_metrics, active_alerts)

        # Component health assessment
        components = {
            "system_resources": {
                "status": self._get_resource_health(current_metrics),
                "score": self._get_resource_score(current_metrics),
                "issues": self._get_resource_issues(current_metrics)
            },
            "agent_performance": {
                "status": self._get_agent_health(current_metrics),
                "score": self._get_agent_score(current_metrics),
                "issues": self._get_agent_issues(current_metrics)
            },
            "error_rates": {
                "status": self._get_error_health(current_metrics),
                "score": self._get_error_score(current_metrics),
                "issues": self._get_error_issues(current_metrics)
            }
        }

        # Overall issues
        all_issues = []
        for component in components.values():
            all_issues.extend(component["issues"])

        if active_alerts:
            all_issues.extend([f"Active alert: {alert.name}" for alert in active_alerts])

        result = {
            "status": "success",
            "health_score": health_score,
            "overall_status": "healthy" if health_score >= 80 else "degraded" if health_score >= 60 else "critical",
            "components": components,
            "active_alerts_count": len(active_alerts),
            "issues": all_issues,
            "last_assessment": datetime.now(timezone.utc).isoformat()
        }

        if detailed:
            result["detailed_metrics"] = current_metrics
            result["recommendations"] = self._generate_health_recommendations(current_metrics, active_alerts)

        return result

    def _start_monitoring(self, collection_interval: int = 30) -> Dict:
        """Start performance monitoring"""
        try:
            # Start metrics collection
            self.metrics_collector.collection_interval = collection_interval
            self.metrics_collector.start_collection()

            # Start alert monitoring
            self.alert_manager.start_monitoring()

            self.dashboard_active = True
            self.last_update = datetime.now(timezone.utc)

            logger.info(f"Performance monitoring started with {collection_interval}s interval")

            return {
                "status": "success",
                "monitoring_active": True,
                "collection_interval": collection_interval,
                "alerts_active": len(self.alert_manager.get_active_alerts()),
                "message": "Performance monitoring started successfully"
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "monitoring_active": False
            }

    def _get_alerts(self, include_resolved: bool = False, hours: int = 24) -> Dict:
        """Get current alerts and alert history"""
        active_alerts = self.alert_manager.get_active_alerts()
        alert_history = self.alert_manager.get_alert_history(hours) if include_resolved else []

        return {
            "status": "success",
            "active_alerts": [
                {
                    "id": alert.alert_id,
                    "name": alert.name,
                    "severity": alert.severity,
                    "message": alert.message,
                    "triggered_at": alert.triggered_at.isoformat(),
                    "metadata": alert.metadata
                }
                for alert in active_alerts
            ],
            "alert_history": [
                {
                    "id": alert.alert_id,
                    "name": alert.name,
                    "severity": alert.severity,
                    "message": alert.message,
                    "triggered_at": alert.triggered_at.isoformat(),
                    "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None,
                    "duration_minutes": ((alert.resolved_at or datetime.now(timezone.utc)) - alert.triggered_at).total_seconds() / 60
                }
                for alert in alert_history
            ],
            "summary": {
                "active_count": len(active_alerts),
                "resolved_count": len([a for a in alert_history if a.resolved_at]),
                "total_count": len(alert_history) + len(active_alerts)
            }
        }

    def _calculate_health_score(self, current_metrics: Dict, active_alerts: List) -> float:
        """Calculate overall system health score (0-100)"""
        score = 100.0

        # Deduct points for high resource usage
        cpu_usage = current_metrics.get("system.cpu.percent", 0)
        if cpu_usage > 90:
            score -= 20
        elif cpu_usage > 80:
            score -= 10
        elif cpu_usage > 70:
            score -= 5

        memory_usage = current_metrics.get("system.memory.percent", 0)
        if memory_usage > 90:
            score -= 20
        elif memory_usage > 80:
            score -= 10
        elif memory_usage > 70:
            score -= 5

        disk_usage = current_metrics.get("system.disk.percent", 0)
        if disk_usage > 95:
            score -= 25
        elif disk_usage > 90:
            score -= 15
        elif disk_usage > 85:
            score -= 5

        # Deduct points for active alerts
        for alert in active_alerts:
            if alert.severity == "critical":
                score -= 30
            elif alert.severity == "high":
                score -= 20
            elif alert.severity == "medium":
                score -= 10
            elif alert.severity == "low":
                score -= 5

        # Deduct points for high error rates
        error_rate = current_metrics.get("agent.resilience.error_rate", 0)
        if error_rate > 10:
            score -= 20
        elif error_rate > 5:
            score -= 10
        elif error_rate > 2:
            score -= 5

        return max(0, score)

    def _get_resource_health(self, current_metrics: Dict) -> str:
        """Get resource health status"""
        cpu = current_metrics.get("system.cpu.percent", 0)
        memory = current_metrics.get("system.memory.percent", 0)
        disk = current_metrics.get("system.disk.percent", 0)

        if cpu > 90 or memory > 90 or disk > 95:
            return "critical"
        elif cpu > 80 or memory > 80 or disk > 90:
            return "warning"
        else:
            return "healthy"

    def _get_resource_score(self, current_metrics: Dict) -> float:
        """Get resource health score"""
        cpu = current_metrics.get("system.cpu.percent", 0)
        memory = current_metrics.get("system.memory.percent", 0)
        disk = current_metrics.get("system.disk.percent", 0)

        # Average resource score
        resource_score = (100 - cpu + 100 - memory + 100 - disk) / 3
        return max(0, resource_score)

    def _get_resource_issues(self, current_metrics: Dict) -> List[str]:
        """Get resource-related issues"""
        issues = []

        cpu = current_metrics.get("system.cpu.percent", 0)
        if cpu > 90:
            issues.append(f"Critical CPU usage: {cpu:.1f}%")
        elif cpu > 80:
            issues.append(f"High CPU usage: {cpu:.1f}%")

        memory = current_metrics.get("system.memory.percent", 0)
        if memory > 90:
            issues.append(f"Critical memory usage: {memory:.1f}%")
        elif memory > 80:
            issues.append(f"High memory usage: {memory:.1f}%")

        disk = current_metrics.get("system.disk.percent", 0)
        if disk > 95:
            issues.append(f"Critical disk usage: {disk:.1f}%")
        elif disk > 90:
            issues.append(f"High disk usage: {disk:.1f}%")

        return issues

    def _get_agent_health(self, current_metrics: Dict) -> str:
        """Get agent performance health"""
        response_time = current_metrics.get("agent.orchestration.response_time", 0)
        active_tasks = current_metrics.get("agent.orchestration.active_tasks", 0)

        if response_time > 10 or active_tasks > 20:
            return "warning"
        else:
            return "healthy"

    def _get_agent_score(self, current_metrics: Dict) -> float:
        """Get agent performance score"""
        response_time = current_metrics.get("agent.orchestration.response_time", 0)
        active_tasks = current_metrics.get("agent.orchestration.active_tasks", 0)

        # Score based on response time and task load
        response_score = max(0, 100 - response_time * 10)  # 10 points per second
        task_score = max(0, 100 - active_tasks * 5)  # 5 points per active task

        return (response_score + task_score) / 2

    def _get_agent_issues(self, current_metrics: Dict) -> List[str]:
        """Get agent performance issues"""
        issues = []

        response_time = current_metrics.get("agent.orchestration.response_time", 0)
        if response_time > 5:
            issues.append(f"Slow response time: {response_time:.2f}s")

        active_tasks = current_metrics.get("agent.orchestration.active_tasks", 0)
        if active_tasks > 15:
            issues.append(f"High task load: {active_tasks} active tasks")

        return issues

    def _get_error_health(self, current_metrics: Dict) -> str:
        """Get error rate health status"""
        error_rate = current_metrics.get("agent.resilience.error_rate", 0)

        if error_rate > 10:
            return "critical"
        elif error_rate > 5:
            return "warning"
        else:
            return "healthy"

    def _get_error_score(self, current_metrics: Dict) -> float:
        """Get error rate score"""
        error_rate = current_metrics.get("agent.resilience.error_rate", 0)
        return max(0, 100 - error_rate * 10)  # 10 points per percent error rate

    def _get_error_issues(self, current_metrics: Dict) -> List[str]:
        """Get error-related issues"""
        issues = []

        error_rate = current_metrics.get("agent.resilience.error_rate", 0)
        if error_rate > 10:
            issues.append(f"Critical error rate: {error_rate:.1f}%")
        elif error_rate > 5:
            issues.append(f"High error rate: {error_rate:.1f}%")

        total_errors = current_metrics.get("agent.resilience.total_errors", 0)
        if total_errors > 100:
            issues.append(f"High total error count: {total_errors}")

        return issues

    def _calculate_performance_trends(self) -> Dict:
        """Calculate recent performance trends"""
        trends = {}

        # Calculate trends for key metrics
        key_metrics = [
            "system.cpu.percent",
            "system.memory.percent",
            "agent.orchestration.response_time",
            "agent.resilience.error_rate"
        ]

        for metric_name in key_metrics:
            history = self.metrics_collector.get_metric_history(metric_name, 2)  # Last 2 hours

            if len(history) >= 2:
                # Simple trend calculation (current vs average of earlier values)
                recent_values = [m.value for m in history[-10:]]  # Last 10 points
                earlier_values = [m.value for m in history[:-10]] if len(history) > 10 else [m.value for m in history[:len(history)//2]]

                if earlier_values and recent_values:
                    recent_avg = statistics.mean(recent_values)
                    earlier_avg = statistics.mean(earlier_values)

                    trend_percent = ((recent_avg - earlier_avg) / earlier_avg * 100) if earlier_avg > 0 else 0
                    trends[metric_name] = {
                        "trend_percent": round(trend_percent, 2),
                        "direction": "up" if trend_percent > 5 else "down" if trend_percent < -5 else "stable",
                        "recent_avg": round(recent_avg, 2),
                        "earlier_avg": round(earlier_avg, 2)
                    }

        return trends

    def _generate_health_recommendations(self, current_metrics: Dict, active_alerts: List) -> List[str]:
        """Generate health improvement recommendations"""
        recommendations = []

        # Resource recommendations
        cpu_usage = current_metrics.get("system.cpu.percent", 0)
        if cpu_usage > 80:
            recommendations.append("Consider scaling CPU resources or optimizing computational load")

        memory_usage = current_metrics.get("system.memory.percent", 0)
        if memory_usage > 80:
            recommendations.append("Consider increasing memory or implementing memory optimization")

        disk_usage = current_metrics.get("system.disk.percent", 0)
        if disk_usage > 85:
            recommendations.append("Cleanup disk space or implement data archival policies")

        # Performance recommendations
        response_time = current_metrics.get("agent.orchestration.response_time", 0)
        if response_time > 5:
            recommendations.append("Investigate slow response times and optimize agent performance")

        # Error recommendations
        error_rate = current_metrics.get("agent.resilience.error_rate", 0)
        if error_rate > 5:
            recommendations.append("Investigate root causes of increased error rate and improve error handling")

        # Alert-specific recommendations
        for alert in active_alerts:
            if "error" in alert.name.lower():
                recommendations.append("Address active error conditions immediately")
            elif "resource" in alert.name.lower():
                recommendations.append("Monitor and optimize resource utilization")

        if not recommendations:
            recommendations.append("System is performing well - continue monitoring")

        return recommendations

    def get_dashboard_status(self) -> Dict:
        """Get dashboard monitoring status"""
        return {
            "dashboard_active": self.dashboard_active,
            "monitoring_active": self.metrics_collector.is_collecting,
            "alerts_active": self.alert_manager.is_monitoring,
            "collection_interval": self.metrics_collector.collection_interval,
            "last_update": self.last_update.isoformat() if self.last_update else None,
            "metrics_count": len(self.metrics_collector.metrics_history),
            "active_alerts_count": len(self.alert_manager.get_active_alerts()),
            "alert_definitions_count": len(self.alert_manager.alert_definitions)
        }


# Global dashboard instance
performance_monitoring_dashboard = PerformanceMonitoringDashboard()