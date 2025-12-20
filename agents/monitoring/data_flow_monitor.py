#!/usr/bin/env python3
"""
Data Flow Monitor - Real-time Monitoring and Alerting for Data Pipeline
Provides comprehensive monitoring, metrics collection, and alerting capabilities
"""

import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
import time
import uuid
from collections import defaultdict, deque
import statistics
import threading
from pathlib import Path

from ..core.event_stream_manager import (
    EventStreamManager, Event, EventPriority, EventSubscription
)
from ..core.enhanced_agent_framework import EnhancedBaseAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MetricType(Enum):
    """Types of metrics collected"""
    COUNTER = "counter"           # Counting occurrences
    GAUGE = "gauge"              # Current value
    HISTOGRAM = "histogram"      # Distribution of values
    TIMER = "timer"              # Duration measurements
    RATE = "rate"                # Rate per time unit

class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class HealthStatus(Enum):
    """System health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"

@dataclass
class MetricDefinition:
    """Definition for a monitored metric"""
    name: str
    metric_type: MetricType
    description: str
    unit: str
    tags: Dict[str, str] = field(default_factory=dict)
    thresholds: Dict[str, float] = field(default_factory=dict)  # warning, critical thresholds

@dataclass
class MetricValue:
    """Individual metric value with timestamp"""
    metric_name: str
    value: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    tags: Dict[str, str] = field(default_factory=dict)

@dataclass
class AlertRule:
    """Alert rule definition"""
    rule_id: str
    name: str
    description: str
    metric_name: str
    condition: str  # gt, lt, eq, gte, lte, rate_increase
    threshold: float
    severity: AlertSeverity
    duration_minutes: int = 5  # How long condition must persist
    tags: Dict[str, str] = field(default_factory=dict)
    enabled: bool = True

@dataclass
class Alert:
    """Alert instance"""
    alert_id: str
    rule_id: str
    severity: AlertSeverity
    message: str
    metric_value: float
    triggered_at: datetime
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    tags: Dict[str, str] = field(default_factory=dict)

@dataclass
class SystemHealth:
    """Overall system health assessment"""
    status: HealthStatus
    score: float  # 0.0 to 1.0
    issues: List[str]
    last_assessment: datetime
    component_health: Dict[str, Dict[str, Any]]

class DataFlowMonitor(EnhancedBaseAgent):
    """
    Comprehensive data flow monitoring system
    Tracks performance, quality, and health across the entire data pipeline
    """

    def __init__(self, agent_id: str = "data_flow_monitor"):
        super().__init__(
            agent_id=agent_id,
            agent_name="Data Flow Monitor",
            permission_level=self.PermissionLevel.READ_ONLY
        )

        # Metrics storage and processing
        self.metrics_definitions: Dict[str, MetricDefinition] = {}
        self.metrics_data: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.aggregated_metrics: Dict[str, Dict[str, float]] = {}

        # Alert management
        self.alert_rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: deque = deque(maxlen=1000)

        # Health monitoring
        self.system_health = SystemHealth(
            status=HealthStatus.HEALTHY,
            score=1.0,
            issues=[],
            last_assessment=datetime.now(timezone.utc),
            component_health={}
        )

        # Performance tracking
        self.performance_windows = {
            "1m": timedelta(minutes=1),
            "5m": timedelta(minutes=5),
            "15m": timedelta(minutes=15),
            "1h": timedelta(hours=1),
            "24h": timedelta(hours=24)
        }

        # Monitoring state
        self.monitoring_active = False
        self.last_metrics_update = datetime.now(timezone.utc)
        self.metrics_collection_interval = 30  # seconds

        # Event stream integration
        self.event_manager: Optional[EventStreamManager] = None

        # Dashboards and reporting
        self.dashboard_data = {}
        self.report_cache = {}

    def _define_capabilities(self) -> List['AgentCapability']:
        """Define data flow monitor capabilities"""
        return [
            self.AgentCapability(
                name="monitor_pipeline_performance",
                description="Monitor real-time pipeline performance metrics and KPIs",
                execution_time_estimate=2.0,
                required_permissions=[self.PermissionLevel.READ_ONLY],
                parameters=["pipeline_ids", "metric_types", "time_window"],
                returns={"performance_metrics": "dict", "trends": "dict", "anomalies": "list"}
            ),
            self.AgentCapability(
                name="track_data_quality",
                description="Track data quality metrics and generate quality reports",
                execution_time_estimate=3.0,
                required_permissions=[self.PermissionLevel.READ_ONLY],
                parameters=["quality_dimensions", "thresholds", "time_range"],
                returns={"quality_scores": "dict", "quality_trends": "dict", "issues": "list"}
            ),
            self.AgentCapability(
                name="manage_alerts",
                description="Manage alert rules, trigger alerts, and handle alert lifecycle",
                execution_time_estimate=1.0,
                required_permissions=[self.PermissionLevel.READ_EXECUTE],
                parameters=["action", "alert_config", "alert_id"],
                returns={"alert_status": "string", "active_alerts": "list"}
            ),
            self.AgentCapability(
                name="generate_health_report",
                description="Generate comprehensive system health reports",
                execution_time_estimate=5.0,
                required_permissions=[self.PermissionLevel.READ_ONLY],
                parameters=["report_type", "components", "time_range"],
                returns={"health_report": "dict", "recommendations": "list"}
            )
        ]

    async def initialize(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Initialize the data flow monitor

        Args:
            config: Configuration dictionary

        Returns:
            Initialization status
        """
        try:
            # Initialize event stream manager
            if "event_stream" in config:
                event_config = config["event_stream"]
                self.event_manager = EventStreamManager(event_config)
                await self.event_manager.initialize()
                await self._setup_monitoring_subscriptions()

            # Initialize metric definitions
            await self._initialize_metric_definitions()

            # Initialize alert rules
            await self._initialize_alert_rules()

            # Start background monitoring tasks
            self.monitoring_active = True
            asyncio.create_task(self._metrics_collection_loop())
            asyncio.create_task(self._alert_evaluation_loop())
            asyncio.create_task(self._health_assessment_loop())

            logger.info("Data Flow Monitor initialized successfully")
            return {
                "status": "success",
                "metrics_defined": len(self.metrics_definitions),
                "alert_rules": len(self.alert_rules),
                "monitoring_active": self.monitoring_active
            }

        except Exception as e:
            logger.error(f"Failed to initialize Data Flow Monitor: {e}")
            return {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__
            }

    async def _setup_monitoring_subscriptions(self) -> None:
        """Setup event subscriptions for monitoring"""
        # Performance metrics events
        performance_subscription = EventSubscription(
            subscriber_id="monitor_performance",
            event_types={
                "stage.completed",
                "batch.processed",
                "agent.performance.report",
                "pipeline.metrics"
            }
        )
        await self.event_manager.subscribe_to_events(performance_subscription)

        # Data quality events
        quality_subscription = EventSubscription(
            subscriber_id="monitor_quality",
            event_types={
                "validation.completed",
                "data.quality.assessed",
                "quality.degradation"
            }
        )
        await self.event_manager.subscribe_to_events(quality_subscription)

        # System health events
        health_subscription = EventSubscription(
            subscriber_id="monitor_health",
            event_types={
                "agent.healthy",
                "agent.unhealthy",
                "pipeline.failed",
                "system.error"
            },
            priority_filter={EventPriority.HIGH, EventPriority.CRITICAL}
        )
        await self.event_manager.subscribe_to_events(health_subscription)

    async def _initialize_metric_definitions(self) -> None:
        """Initialize standard metric definitions"""

        # Pipeline performance metrics
        performance_metrics = [
            MetricDefinition(
                name="pipeline_throughput",
                metric_type=MetricType.RATE,
                description="Number of batches processed per minute",
                unit="batches/min",
                thresholds={"warning": 50, "critical": 20}
            ),
            MetricDefinition(
                name="stage_processing_time",
                metric_type=MetricType.HISTOGRAM,
                description="Time to process individual pipeline stages",
                unit="seconds",
                thresholds={"warning": 30, "critical": 60}
            ),
            MetricDefinition(
                name="end_to_end_latency",
                metric_type=MetricType.TIMER,
                description="Total time from ingestion to distribution",
                unit="seconds",
                thresholds={"warning": 60, "critical": 120}
            ),
            MetricDefinition(
                name="data_quality_score",
                metric_type=MetricType.GAUGE,
                description="Overall data quality score (0-1)",
                unit="score",
                thresholds={"warning": 0.7, "critical": 0.5}
            ),
            MetricDefinition(
                name="error_rate",
                metric_type=MetricType.RATE,
                description="Number of errors per 100 batches",
                unit="errors/100batches",
                thresholds={"warning": 5, "critical": 15}
            ),
            MetricDefinition(
                name="agent_response_time",
                metric_type=MetricType.HISTOGRAM,
                description="Agent response time distribution",
                unit="milliseconds",
                thresholds={"warning": 5000, "critical": 10000}
            ),
            MetricDefinition(
                name="cache_hit_rate",
                metric_type=MetricType.GAUGE,
                description="Cache hit rate percentage",
                unit="percent",
                thresholds={"warning": 70, "critical": 50}
            ),
            MetricDefinition(
                name="api_rate_limit_utilization",
                metric_type=MetricType.GAUGE,
                description="API rate limit utilization percentage",
                unit="percent",
                thresholds={"warning": 80, "critical": 95}
            )
        ]

        for metric in performance_metrics:
            self.metrics_definitions[metric.name] = metric

    async def _initialize_alert_rules(self) -> None:
        """Initialize default alert rules"""
        default_rules = [
            AlertRule(
                rule_id="high_error_rate",
                name="High Error Rate",
                description="Error rate exceeds threshold",
                metric_name="error_rate",
                condition="gt",
                threshold=10,
                severity=AlertSeverity.ERROR,
                duration_minutes=5
            ),
            AlertRule(
                rule_id="low_data_quality",
                name="Low Data Quality",
                description="Data quality score below threshold",
                metric_name="data_quality_score",
                condition="lt",
                threshold=0.6,
                severity=AlertSeverity.WARNING,
                duration_minutes=3
            ),
            AlertRule(
                rule_id="pipeline_latency_high",
                name="High Pipeline Latency",
                description="Pipeline processing latency too high",
                metric_name="end_to_end_latency",
                condition="gt",
                threshold=90,
                severity=AlertSeverity.WARNING,
                duration_minutes=10
            ),
            AlertRule(
                rule_id="agent_unresponsive",
                name="Agent Unresponsive",
                description="Agent response time exceeds threshold",
                metric_name="agent_response_time",
                condition="gt",
                threshold=15000,
                severity=AlertSeverity.CRITICAL,
                duration_minutes=2
            ),
            AlertRule(
                rule_id="api_rate_limit_exceeded",
                name="API Rate Limit Exceeded",
                description="API rate limit utilization too high",
                metric_name="api_rate_limit_utilization",
                condition="gt",
                threshold=90,
                severity=AlertSeverity.ERROR,
                duration_minutes=1
            )
        ]

        for rule in default_rules:
            self.alert_rules[rule.rule_id] = rule

    async def _execute_action(self, action: str, parameters: Dict, user_context: Dict) -> Dict[str, Any]:
        """Execute data flow monitor actions"""
        try:
            if action == "monitor_pipeline_performance":
                return await self._monitor_pipeline_performance(parameters, user_context)
            elif action == "track_data_quality":
                return await self._track_data_quality(parameters, user_context)
            elif action == "manage_alerts":
                return await self._manage_alerts(parameters, user_context)
            elif action == "generate_health_report":
                return await self._generate_health_report(parameters, user_context)
            else:
                raise ValueError(f"Unknown action: {action}")

        except Exception as e:
            logger.error(f"Error executing action '{action}': {e}")
            return {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__,
                "agent_id": self.agent_id
            }

    async def _monitor_pipeline_performance(self, parameters: Dict, user_context: Dict) -> Dict[str, Any]:
        """Monitor pipeline performance metrics"""
        pipeline_ids = parameters.get("pipeline_ids", [])
        metric_types = parameters.get("metric_types", ["throughput", "latency", "error_rate"])
        time_window = parameters.get("time_window", "1h")

        try:
            # Get performance metrics for specified time window
            window_delta = self.performance_windows.get(time_window, timedelta(hours=1))
            cutoff_time = datetime.now(timezone.utc) - window_delta

            performance_metrics = {}
            trends = {}
            anomalies = []

            for metric_type in metric_types:
                metric_data = self._get_metric_data(metric_type, cutoff_time)

                if metric_data:
                    # Calculate statistics
                    values = [m.value for m in metric_data]
                    performance_metrics[metric_type] = {
                        "current": values[-1] if values else 0,
                        "average": statistics.mean(values) if values else 0,
                        "min": min(values) if values else 0,
                        "max": max(values) if values else 0,
                        "p95": statistics.quantiles(values, n=20)[18] if len(values) > 20 else max(values) if values else 0,
                        "count": len(values)
                    }

                    # Calculate trend
                    if len(values) >= 10:
                        recent_avg = statistics.mean(values[-5:])
                        older_avg = statistics.mean(values[:5])
                        trend = ((recent_avg - older_avg) / older_avg) * 100 if older_avg != 0 else 0
                        trends[metric_type] = {
                            "trend_percent": trend,
                            "direction": "increasing" if trend > 0 else "decreasing" if trend < 0 else "stable"
                        }

                    # Detect anomalies
                    if len(values) >= 20:
                        anomalies.extend(self._detect_anomalies(metric_type, values))

            return {
                "status": "success",
                "performance_metrics": performance_metrics,
                "trends": trends,
                "anomalies": anomalies,
                "time_window": time_window,
                "generated_at": datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to monitor pipeline performance: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    def _get_metric_data(self, metric_name: str, since: datetime) -> List[MetricValue]:
        """Get metric data since specified time"""
        if metric_name not in self.metrics_data:
            return []

        return [
            metric for metric in self.metrics_data[metric_name]
            if metric.timestamp >= since
        ]

    def _detect_anomalies(self, metric_name: str, values: List[float]) -> List[Dict[str, Any]]:
        """Detect anomalies in metric values using statistical methods"""
        anomalies = []

        if len(values) < 20:
            return anomalies

        # Calculate baseline using first 80% of values
        baseline_size = int(len(values) * 0.8)
        baseline_values = values[:baseline_size]
        test_values = values[baseline_size:]

        if not baseline_values or not test_values:
            return anomalies

        baseline_mean = statistics.mean(baseline_values)
        baseline_std = statistics.stdev(baseline_values) if len(baseline_values) > 1 else 0

        # Detect outliers in recent values
        for i, value in enumerate(test_values):
            z_score = abs((value - baseline_mean) / baseline_std) if baseline_std > 0 else 0

            if z_score > 3:  # 3 sigma rule
                anomalies.append({
                    "metric_name": metric_name,
                    "value": value,
                    "expected_range": [baseline_mean - 3 * baseline_std, baseline_mean + 3 * baseline_std],
                    "z_score": z_score,
                    "severity": "high" if z_score > 4 else "medium",
                    "timestamp": (datetime.now(timezone.utc) - timedelta(seconds=len(test_values) - i)).isoformat()
                })

        return anomalies

    async def _track_data_quality(self, parameters: Dict, user_context: Dict) -> Dict[str, Any]:
        """Track data quality metrics and generate quality reports"""
        quality_dimensions = parameters.get("quality_dimensions", ["completeness", "accuracy", "consistency"])
        thresholds = parameters.get("thresholds", {"completeness": 0.9, "accuracy": 0.95, "consistency": 0.85})
        time_range = parameters.get("time_range", "24h")

        try:
            # Collect quality metrics
            quality_metrics = {}
            quality_trends = {}
            issues = []

            for dimension in quality_dimensions:
                metric_name = f"quality_{dimension}"
                metric_data = self._get_metric_data(metric_name, datetime.now(timezone.utc) - timedelta(hours=24))

                if metric_data:
                    values = [m.value for m in metric_data]
                    current_quality = values[-1] if values else 0

                    quality_metrics[dimension] = {
                        "current_score": current_quality,
                        "average_score": statistics.mean(values) if values else 0,
                        "min_score": min(values) if values else 0,
                        "threshold": thresholds.get(dimension, 0.8),
                        "compliance": current_quality >= thresholds.get(dimension, 0.8)
                    }

                    # Check for quality issues
                    if current_quality < thresholds.get(dimension, 0.8):
                        issues.append({
                            "dimension": dimension,
                            "severity": "high" if current_quality < 0.5 else "medium",
                            "description": f"{dimension.title()} quality below threshold",
                            "current_value": current_quality,
                            "threshold": thresholds.get(dimension, 0.8)
                        })

                    # Calculate trend
                    if len(values) >= 10:
                        recent_avg = statistics.mean(values[-5:])
                        older_avg = statistics.mean(values[:5])
                        trend = ((recent_avg - older_avg) / older_avg) * 100 if older_avg != 0 else 0
                        quality_trends[dimension] = {
                            "trend_percent": trend,
                            "direction": "improving" if trend > 0 else "declining" if trend < 0 else "stable"
                        }

            # Calculate overall quality score
            overall_score = 0
            total_weight = 0
            for dimension, metrics in quality_metrics.items():
                weight = 1.0  # Equal weighting for now
                overall_score += metrics["current_score"] * weight
                total_weight += weight

            overall_quality_score = overall_score / total_weight if total_weight > 0 else 0

            return {
                "status": "success",
                "quality_scores": quality_metrics,
                "overall_quality_score": overall_quality_score,
                "quality_trends": quality_trends,
                "issues": issues,
                "time_range": time_range,
                "generated_at": datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to track data quality: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def _manage_alerts(self, parameters: Dict, user_context: Dict) -> Dict[str, Any]:
        """Manage alert rules and active alerts"""
        action = parameters.get("action")
        alert_config = parameters.get("alert_config", {})
        alert_id = parameters.get("alert_id")

        try:
            if action == "create_rule":
                return await self._create_alert_rule(alert_config)
            elif action == "update_rule":
                return await self._update_alert_rule(alert_id, alert_config)
            elif action == "delete_rule":
                return await self._delete_alert_rule(alert_id)
            elif action == "acknowledge_alert":
                return await self._acknowledge_alert(alert_id)
            elif action == "resolve_alert":
                return await self._resolve_alert(alert_id)
            elif action == "list_alerts":
                return await self._list_alerts(parameters.get("severity"), parameters.get("status"))
            else:
                raise ValueError(f"Unknown alert action: {action}")

        except Exception as e:
            logger.error(f"Failed to manage alerts: {e}")
            return {
                "status": "error",
                "error": str(e),
                "action": action
            }

    async def _create_alert_rule(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new alert rule"""
        rule_id = config.get("rule_id", f"rule_{uuid.uuid4().hex[:8]}")

        alert_rule = AlertRule(
            rule_id=rule_id,
            name=config["name"],
            description=config.get("description", ""),
            metric_name=config["metric_name"],
            condition=config["condition"],
            threshold=config["threshold"],
            severity=AlertSeverity(config["severity"]),
            duration_minutes=config.get("duration_minutes", 5),
            tags=config.get("tags", {})
        )

        self.alert_rules[rule_id] = alert_rule

        return {
            "status": "success",
            "rule_id": rule_id,
            "message": f"Alert rule '{alert_rule.name}' created successfully"
        }

    async def _update_alert_rule(self, rule_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing alert rule"""
        if rule_id not in self.alert_rules:
            return {
                "status": "error",
                "error": f"Alert rule not found: {rule_id}"
            }

        rule = self.alert_rules[rule_id]

        # Update rule properties
        if "name" in config:
            rule.name = config["name"]
        if "description" in config:
            rule.description = config["description"]
        if "threshold" in config:
            rule.threshold = config["threshold"]
        if "severity" in config:
            rule.severity = AlertSeverity(config["severity"])
        if "enabled" in config:
            rule.enabled = config["enabled"]

        return {
            "status": "success",
            "rule_id": rule_id,
            "message": f"Alert rule '{rule.name}' updated successfully"
        }

    async def _delete_alert_rule(self, rule_id: str) -> Dict[str, Any]:
        """Delete an alert rule"""
        if rule_id not in self.alert_rules:
            return {
                "status": "error",
                "error": f"Alert rule not found: {rule_id}"
            }

        rule_name = self.alert_rules[rule_id].name
        del self.alert_rules[rule_id]

        return {
            "status": "success",
            "rule_id": rule_id,
            "message": f"Alert rule '{rule_name}' deleted successfully"
        }

    async def _acknowledge_alert(self, alert_id: str) -> Dict[str, Any]:
        """Acknowledge an active alert"""
        if alert_id not in self.active_alerts:
            return {
                "status": "error",
                "error": f"Alert not found: {alert_id}"
            }

        alert = self.active_alerts[alert_id]
        alert.acknowledged_at = datetime.now(timezone.utc)

        return {
            "status": "success",
            "alert_id": alert_id,
            "message": "Alert acknowledged successfully"
        }

    async def _resolve_alert(self, alert_id: str) -> Dict[str, Any]:
        """Resolve an active alert"""
        if alert_id not in self.active_alerts:
            return {
                "status": "error",
                "error": f"Alert not found: {alert_id}"
            }

        alert = self.active_alerts[alert_id]
        alert.resolved_at = datetime.now(timezone.utc)

        # Move to history
        self.alert_history.append(alert)
        del self.active_alerts[alert_id]

        return {
            "status": "success",
            "alert_id": alert_id,
            "message": "Alert resolved successfully"
        }

    async def _list_alerts(self, severity: Optional[str] = None, status: Optional[str] = None) -> Dict[str, Any]:
        """List alerts with optional filtering"""
        alerts = list(self.active_alerts.values())

        # Apply filters
        if severity:
            severity_filter = AlertSeverity(severity)
            alerts = [a for a in alerts if a.severity == severity_filter]

        if status:
            if status == "acknowledged":
                alerts = [a for a in alerts if a.acknowledged_at is not None]
            elif status == "unacknowledged":
                alerts = [a for a in alerts if a.acknowledged_at is None]

        return {
            "status": "success",
            "active_alerts": len(alerts),
            "alerts": [
                {
                    "alert_id": a.alert_id,
                    "rule_id": a.rule_id,
                    "severity": a.severity.value,
                    "message": a.message,
                    "triggered_at": a.triggered_at.isoformat(),
                    "acknowledged_at": a.acknowledged_at.isoformat() if a.acknowledged_at else None
                }
                for a in alerts
            ]
        }

    async def _generate_health_report(self, parameters: Dict, user_context: Dict) -> Dict[str, Any]:
        """Generate comprehensive system health report"""
        report_type = parameters.get("report_type", "comprehensive")
        components = parameters.get("components", ["all"])
        time_range = parameters.get("time_range", "24h")

        try:
            health_report = {
                "report_type": report_type,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "time_range": time_range,
                "overall_health": self.system_health.status.value,
                "health_score": self.system_health.score,
                "component_health": {}
            }

            # Component-specific health
            if "all" in components or "pipeline" in components:
                health_report["component_health"]["pipeline"] = self._assess_pipeline_health()

            if "all" in components or "agents" in components:
                health_report["component_health"]["agents"] = self._assess_agent_health()

            if "all" in components or "data_quality" in components:
                health_report["component_health"]["data_quality"] = self._assess_data_quality_health()

            if "all" in components or "performance" in components:
                health_report["component_health"]["performance"] = self._assess_performance_health()

            # Generate recommendations
            recommendations = self._generate_health_recommendations(health_report)
            health_report["recommendations"] = recommendations

            # Include active alerts
            health_report["active_alerts"] = [
                {
                    "severity": alert.severity.value,
                    "message": alert.message,
                    "duration_minutes": (datetime.now(timezone.utc) - alert.triggered_at).total_seconds() / 60
                }
                for alert in self.active_alerts.values()
            ]

            return {
                "status": "success",
                "health_report": health_report
            }

        except Exception as e:
            logger.error(f"Failed to generate health report: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    def _assess_pipeline_health(self) -> Dict[str, Any]:
        """Assess pipeline component health"""
        # Get pipeline metrics
        throughput_data = self._get_metric_data("pipeline_throughput", datetime.now(timezone.utc) - timedelta(hours=1))
        error_rate_data = self._get_metric_data("error_rate", datetime.now(timezone.utc) - timedelta(hours=1))
        latency_data = self._get_metric_data("end_to_end_latency", datetime.now(timezone.utc) - timedelta(hours=1))

        health_score = 1.0
        issues = []

        # Check throughput
        if throughput_data:
            avg_throughput = statistics.mean([m.value for m in throughput_data])
            if avg_throughput < 20:
                health_score -= 0.3
                issues.append("Low pipeline throughput")
            elif avg_throughput < 50:
                health_score -= 0.1
                issues.append("Reduced pipeline throughput")

        # Check error rate
        if error_rate_data:
            avg_error_rate = statistics.mean([m.value for m in error_rate_data])
            if avg_error_rate > 15:
                health_score -= 0.4
                issues.append("High error rate")
            elif avg_error_rate > 5:
                health_score -= 0.2
                issues.append("Elevated error rate")

        # Check latency
        if latency_data:
            avg_latency = statistics.mean([m.value for m in latency_data])
            if avg_latency > 120:
                health_score -= 0.3
                issues.append("High processing latency")
            elif avg_latency > 60:
                health_score -= 0.1
                issues.append("Elevated processing latency")

        status = HealthStatus.HEALTHY
        if health_score < 0.5:
            status = HealthStatus.CRITICAL
        elif health_score < 0.7:
            status = HealthStatus.UNHEALTHY
        elif health_score < 0.9:
            status = HealthStatus.DEGRADED

        return {
            "status": status.value,
            "health_score": max(0.0, health_score),
            "issues": issues,
            "metrics": {
                "throughput": statistics.mean([m.value for m in throughput_data]) if throughput_data else 0,
                "error_rate": statistics.mean([m.value for m in error_rate_data]) if error_rate_data else 0,
                "latency": statistics.mean([m.value for m in latency_data]) if latency_data else 0
            }
        }

    def _assess_agent_health(self) -> Dict[str, Any]:
        """Assess agent component health"""
        response_time_data = self._get_metric_data("agent_response_time", datetime.now(timezone.utc) - timedelta(hours=1))

        health_score = 1.0
        issues = []

        if response_time_data:
            avg_response_time = statistics.mean([m.value for m in response_time_data])
            if avg_response_time > 15000:  # 15 seconds
                health_score -= 0.4
                issues.append("Very slow agent response times")
            elif avg_response_time > 5000:  # 5 seconds
                health_score -= 0.2
                issues.append("Slow agent response times")

        # Check active alerts related to agents
        agent_alerts = [
            alert for alert in self.active_alerts.values()
            if "agent" in alert.message.lower()
        ]

        if agent_alerts:
            critical_agent_alerts = [a for a in agent_alerts if a.severity == AlertSeverity.CRITICAL]
            if critical_agent_alerts:
                health_score -= 0.5
                issues.append(f"{len(critical_agent_alerts)} critical agent alerts")

        status = HealthStatus.HEALTHY
        if health_score < 0.5:
            status = HealthStatus.CRITICAL
        elif health_score < 0.7:
            status = HealthStatus.UNHEALTHY
        elif health_score < 0.9:
            status = HealthStatus.DEGRADED

        return {
            "status": status.value,
            "health_score": max(0.0, health_score),
            "issues": issues,
            "active_agent_alerts": len(agent_alerts),
            "average_response_time": statistics.mean([m.value for m in response_time_data]) if response_time_data else 0
        }

    def _assess_data_quality_health(self) -> Dict[str, Any]:
        """Assess data quality component health"""
        quality_metrics = {}
        overall_score = 0.0
        total_weight = 0.0

        dimensions = ["completeness", "accuracy", "consistency"]
        for dimension in dimensions:
            metric_name = f"quality_{dimension}"
            metric_data = self._get_metric_data(metric_name, datetime.now(timezone.utc) - timedelta(hours=1))

            if metric_data:
                values = [m.value for m in metric_data]
                avg_quality = statistics.mean(values)
                quality_metrics[dimension] = avg_quality

                weight = 1.0
                overall_score += avg_quality * weight
                total_weight += weight

        if total_weight > 0:
            overall_score = overall_score / total_weight

        issues = []
        if overall_score < 0.6:
            issues.append("Poor overall data quality")
        elif overall_score < 0.8:
            issues.append("Data quality needs improvement")

        for dimension, score in quality_metrics.items():
            if score < 0.5:
                issues.append(f"Very poor {dimension} quality")
            elif score < 0.7:
                issues.append(f"Low {dimension} quality")

        status = HealthStatus.HEALTHY
        if overall_score < 0.5:
            status = HealthStatus.CRITICAL
        elif overall_score < 0.7:
            status = HealthStatus.UNHEALTHY
        elif overall_score < 0.85:
            status = HealthStatus.DEGRADED

        return {
            "status": status.value,
            "health_score": overall_score,
            "issues": issues,
            "dimension_scores": quality_metrics
        }

    def _assess_performance_health(self) -> Dict[str, Any]:
        """Assess performance component health"""
        # Get various performance metrics
        cache_hit_rate_data = self._get_metric_data("cache_hit_rate", datetime.now(timezone.utc) - timedelta(hours=1))
        api_utilization_data = self._get_metric_data("api_rate_limit_utilization", datetime.now(timezone.utc) - timedelta(hours=1))

        health_score = 1.0
        issues = []

        # Check cache hit rate
        if cache_hit_rate_data:
            avg_cache_hit_rate = statistics.mean([m.value for m in cache_hit_rate_data])
            if avg_cache_hit_rate < 50:
                health_score -= 0.2
                issues.append("Low cache hit rate")
            elif avg_cache_hit_rate < 70:
                health_score -= 0.1
                issues.append("Suboptimal cache hit rate")

        # Check API utilization
        if api_utilization_data:
            avg_api_utilization = statistics.mean([m.value for m in api_utilization_data])
            if avg_api_utilization > 95:
                health_score -= 0.3
                issues.append("API rate limit near capacity")
            elif avg_api_utilization > 85:
                health_score -= 0.1
                issues.append("High API rate limit utilization")

        status = HealthStatus.HEALTHY
        if health_score < 0.6:
            status = HealthStatus.CRITICAL
        elif health_score < 0.8:
            status = HealthStatus.UNHEALTHY
        elif health_score < 0.9:
            status = HealthStatus.DEGRADED

        return {
            "status": status.value,
            "health_score": max(0.0, health_score),
            "issues": issues,
            "metrics": {
                "cache_hit_rate": statistics.mean([m.value for m in cache_hit_rate_data]) if cache_hit_rate_data else 0,
                "api_utilization": statistics.mean([m.value for m in api_utilization_data]) if api_utilization_data else 0
            }
        }

    def _generate_health_recommendations(self, health_report: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate recommendations based on health assessment"""
        recommendations = []

        component_health = health_report.get("component_health", {})

        # Pipeline recommendations
        pipeline_health = component_health.get("pipeline", {})
        if pipeline_health.get("health_score", 1.0) < 0.8:
            issues = pipeline_health.get("issues", [])
            if "Low pipeline throughput" in issues:
                recommendations.append({
                    "category": "pipeline",
                    "priority": "high",
                    "recommendation": "Increase parallel processing or optimize batch sizes",
                    "expected_impact": "20-40% throughput improvement"
                })
            if "High error rate" in issues:
                recommendations.append({
                    "category": "pipeline",
                    "priority": "critical",
                    "recommendation": "Investigate and fix error sources, improve validation",
                    "expected_impact": "Significant reduction in processing failures"
                })

        # Agent recommendations
        agent_health = component_health.get("agents", {})
        if agent_health.get("health_score", 1.0) < 0.8:
            recommendations.append({
                "category": "agents",
                "priority": "medium",
                "recommendation": "Optimize agent performance or increase resources",
                "expected_impact": "Improved response times and reliability"
            })

        # Data quality recommendations
        quality_health = component_health.get("data_quality", {})
        if quality_health.get("health_score", 1.0) < 0.8:
            recommendations.append({
                "category": "data_quality",
                "priority": "high",
                "recommendation": "Enhance validation rules and data source quality checks",
                "expected_impact": "Improved data reliability and analysis accuracy"
            })

        # Performance recommendations
        performance_health = component_health.get("performance", {})
        if performance_health.get("health_score", 1.0) < 0.8:
            issues = performance_health.get("issues", [])
            if "Low cache hit rate" in issues:
                recommendations.append({
                    "category": "performance",
                    "priority": "medium",
                    "recommendation": "Optimize caching strategy and increase cache size",
                    "expected_impact": "Reduced API calls and improved response times"
                })

        return recommendations

    async def _metrics_collection_loop(self) -> None:
        """Background loop for collecting metrics"""
        while self.monitoring_active:
            try:
                await self._collect_system_metrics()
                await asyncio.sleep(self.metrics_collection_interval)
            except Exception as e:
                logger.error(f"Error in metrics collection loop: {e}")
                await asyncio.sleep(5)

    async def _alert_evaluation_loop(self) -> None:
        """Background loop for evaluating alert rules"""
        while self.monitoring_active:
            try:
                await self._evaluate_alert_rules()
                await asyncio.sleep(60)  # Check alerts every minute
            except Exception as e:
                logger.error(f"Error in alert evaluation loop: {e}")
                await asyncio.sleep(10)

    async def _health_assessment_loop(self) -> None:
        """Background loop for assessing system health"""
        while self.monitoring_active:
            try:
                await self._assess_overall_health()
                await asyncio.sleep(300)  # Assess health every 5 minutes
            except Exception as e:
                logger.error(f"Error in health assessment loop: {e}")
                await asyncio.sleep(30)

    async def _collect_system_metrics(self) -> None:
        """Collect system-level metrics"""
        current_time = datetime.now(timezone.utc)

        # These would be collected from various sources
        # For now, we'll use placeholder values

        # Agent response times (simulated)
        response_time = 1000 + (hash(str(current_time)) % 5000)  # 1-6 seconds
        self._record_metric("agent_response_time", response_time)

        # Cache hit rate (simulated)
        cache_hit_rate = 75 + (hash(str(current_time)[:10]) % 20)  # 75-95%
        self._record_metric("cache_hit_rate", cache_hit_rate)

        # API rate limit utilization (simulated)
        api_utilization = 60 + (hash(str(current_time)[:8]) % 30)  # 60-90%
        self._record_metric("api_rate_limit_utilization", api_utilization)

    async def _evaluate_alert_rules(self) -> None:
        """Evaluate all alert rules and trigger alerts if needed"""
        current_time = datetime.now(timezone.utc)

        for rule in self.alert_rules.values():
            if not rule.enabled:
                continue

            try:
                await self._evaluate_alert_rule(rule, current_time)
            except Exception as e:
                logger.error(f"Error evaluating alert rule {rule.rule_id}: {e}")

    async def _evaluate_alert_rule(self, rule: AlertRule, current_time: datetime) -> None:
        """Evaluate a single alert rule"""
        # Get recent metric data
        metric_data = self._get_metric_data(
            rule.metric_name,
            current_time - timedelta(minutes=rule.duration_minutes * 2)
        )

        if not metric_data:
            return

        # Check if condition is met
        recent_values = [m.value for m in metric_data if m.timestamp >= current_time - timedelta(minutes=rule.duration_minutes)]

        if not recent_values:
            return

        condition_met = self._evaluate_condition(recent_values[-1], rule.condition, rule.threshold)

        if condition_met:
            # Check if alert already exists
            existing_alert = None
            for alert in self.active_alerts.values():
                if alert.rule_id == rule.rule_id:
                    existing_alert = alert
                    break

            if not existing_alert:
                # Create new alert
                alert = Alert(
                    alert_id=f"alert_{uuid.uuid4().hex[:8]}",
                    rule_id=rule.rule_id,
                    severity=rule.severity,
                    message=f"{rule.name}: {rule.metric_name} is {recent_values[-1]} {rule.condition} {rule.threshold}",
                    metric_value=recent_values[-1],
                    triggered_at=current_time,
                    tags=rule.tags
                )

                self.active_alerts[alert.alert_id] = alert

                # Publish alert event
                if self.event_manager:
                    alert_event = Event(
                        type="alert.triggered",
                        source="data_flow_monitor",
                        data={
                            "alert_id": alert.alert_id,
                            "rule_id": rule.rule_id,
                            "severity": alert.severity.value,
                            "message": alert.message,
                            "metric_value": alert.metric_value
                        },
                        priority=EventPriority.HIGH if alert.severity in [AlertSeverity.ERROR, AlertSeverity.CRITICAL] else EventPriority.NORMAL
                    )
                    await self.event_manager.publish_event(alert_event)

    def _evaluate_condition(self, value: float, condition: str, threshold: float) -> bool:
        """Evaluate alert condition"""
        if condition == "gt":
            return value > threshold
        elif condition == "lt":
            return value < threshold
        elif condition == "gte":
            return value >= threshold
        elif condition == "lte":
            return value <= threshold
        elif condition == "eq":
            return value == threshold
        else:
            return False

    async def _assess_overall_health(self) -> None:
        """Assess overall system health"""
        component_health = {
            "pipeline": self._assess_pipeline_health(),
            "agents": self._assess_agent_health(),
            "data_quality": self._assess_data_quality_health(),
            "performance": self._assess_performance_health()
        }

        # Calculate overall health score
        total_score = sum(comp["health_score"] for comp in component_health.values())
        overall_score = total_score / len(component_health)

        # Determine overall status
        if overall_score >= 0.9:
            status = HealthStatus.HEALTHY
        elif overall_score >= 0.7:
            status = HealthStatus.DEGRADED
        elif overall_score >= 0.5:
            status = HealthStatus.UNHEALTHY
        else:
            status = HealthStatus.CRITICAL

        # Collect all issues
        all_issues = []
        for comp_name, comp_health in component_health.items():
            for issue in comp_health.get("issues", []):
                all_issues.append(f"{comp_name}: {issue}")

        self.system_health = SystemHealth(
            status=status,
            score=overall_score,
            issues=all_issues,
            last_assessment=datetime.now(timezone.utc),
            component_health=component_health
        )

    def _record_metric(self, metric_name: str, value: float, tags: Dict[str, str] = None) -> None:
        """Record a metric value"""
        metric = MetricValue(
            metric_name=metric_name,
            value=value,
            tags=tags or {}
        )

        self.metrics_data[metric_name].append(metric)
        self.last_metrics_update = datetime.now(timezone.utc)