#!/usr/bin/env python3
"""
Enterprise Monitoring and Observability System

Provides comprehensive monitoring, observability, and alerting capabilities
for the entire Script Ohio 2.0 agent ecosystem.

@context: Enterprise-grade monitoring and observability
@phase: 4 - Production Deployment
"""

import time
import json
import logging
import threading
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, deque
from enum import Enum
import psutil
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics collected."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class MetricDefinition:
    """Definition of a metric to be collected."""
    name: str
    metric_type: MetricType
    description: str
    labels: List[str] = field(default_factory=list)
    unit: str = ""
    aggregation: Optional[str] = None  # avg, sum, max, min, p95, p99


@dataclass
class MetricValue:
    """Single metric value with timestamp and labels."""
    name: str
    value: float
    timestamp: datetime
    labels: Dict[str, str] = field(default_factory=dict)
    metric_type: MetricType = MetricType.GAUGE


@dataclass
class Alert:
    """Alert definition."""
    name: str
    condition: str
    severity: AlertSeverity
    description: str = ""
    enabled: bool = True
    cooldown_seconds: int = 300
    last_triggered: Optional[datetime] = None


@dataclass
class HealthStatus:
    """Component health status."""
    component: str
    status: str  # healthy, degraded, unhealthy
    message: str = ""
    last_check: datetime = field(default_factory=datetime.utcnow)
    metrics: Dict[str, float] = field(default_factory=dict)


class MetricsCollector:
    """Collects and manages system metrics."""

    def __init__(self):
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.counters: Dict[str, float] = defaultdict(float)
        self.gauges: Dict[str, float] = defaultdict(float)
        self.histograms: Dict[str, List[float]] = defaultdict(list)
        self.timers: Dict[str, List[float]] = defaultdict(list)
        self.lock = threading.Lock()

    def record_counter(self, name: str, value: float = 1.0, labels: Dict[str, str] = None):
        """Record a counter metric."""
        with self.lock:
            key = self._make_key(name, labels)
            self.counters[key] += value
            self._record_metric(name, value, labels, MetricType.COUNTER)

    def set_gauge(self, name: str, value: float, labels: Dict[str, str] = None):
        """Set a gauge metric value."""
        with self.lock:
            key = self._make_key(name, labels)
            self.gauges[key] = value
            self._record_metric(name, value, labels, MetricType.GAUGE)

    def record_histogram(self, name: str, value: float, labels: Dict[str, str] = None):
        """Record a histogram metric value."""
        with self.lock:
            key = self._make_key(name, labels)
            self.histograms[key].append(value)
            if len(self.histograms[key]) > 1000:  # Limit size
                self.histograms[key] = self.histograms[key][-1000:]
            self._record_metric(name, value, labels, MetricType.HISTOGRAM)

    def record_timer(self, name: str, duration_ms: float, labels: Dict[str, str] = None):
        """Record a timer metric value."""
        with self.lock:
            key = self._make_key(name, labels)
            self.timers[key].append(duration_ms)
            if len(self.timers[key]) > 1000:  # Limit size
                self.timers[key] = self.timers[key][-1000:]
            self._record_metric(name, duration_ms, labels, MetricType.TIMER)

    def _make_key(self, name: str, labels: Dict[str, str] = None) -> str:
        """Create a unique key for metric with labels."""
        if not labels:
            return name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}[{label_str}]"

    def _record_metric(self, name: str, value: float, labels: Dict[str, str], metric_type: MetricType):
        """Record metric value with timestamp."""
        metric = MetricValue(
            name=name,
            value=value,
            timestamp=datetime.utcnow(),
            labels=labels or {},
            metric_type=metric_type
        )
        key = self._make_key(name, labels)
        self.metrics[key].append(metric)

    def get_metric(self, name: str, labels: Dict[str, str] = None,
                   since: Optional[datetime] = None) -> List[MetricValue]:
        """Get metric values."""
        key = self._make_key(name, labels)
        metrics = list(self.metrics.get(key, []))

        if since:
            metrics = [m for m in metrics if m.timestamp >= since]

        return metrics

    def get_aggregated_metric(self, name: str, aggregation: str,
                            labels: Dict[str, str] = None) -> Optional[float]:
        """Get aggregated metric value."""
        metrics = self.get_metric(name, labels)

        if not metrics:
            return None

        values = [m.value for m in metrics]

        if aggregation == "avg":
            return statistics.mean(values)
        elif aggregation == "sum":
            return sum(values)
        elif aggregation == "max":
            return max(values)
        elif aggregation == "min":
            return min(values)
        elif aggregation == "p95":
            return np.percentile(values, 95)
        elif aggregation == "p99":
            return np.percentile(values, 99)
        else:
            return statistics.mean(values)


class AlertManager:
    """Manages alert conditions and notifications."""

    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
        self.alerts: Dict[str, Alert] = {}
        self.alert_history: deque = deque(maxlen=1000)
        self.notification_handlers = []

    def add_alert(self, alert: Alert):
        """Add an alert definition."""
        self.alerts[alert.name] = alert

    def check_alerts(self):
        """Check all alert conditions."""
        triggered_alerts = []

        for name, alert in self.alerts.items():
            if not alert.enabled:
                continue

            # Check cooldown
            if (alert.last_triggered and
                datetime.utcnow() - alert.last_triggered < timedelta(seconds=alert.cooldown_seconds)):
                continue

            if self._evaluate_condition(alert.condition):
                alert.last_triggered = datetime.utcnow()
                triggered_alerts.append(alert)

                # Record alert triggered
                self.alert_history.append({
                    'alert_name': name,
                    'timestamp': alert.last_triggered,
                    'severity': alert.severity.value
                })

                self.metrics_collector.record_counter(
                    'alerts_triggered_total',
                    labels={'severity': alert.severity.value, 'alert': name}
                )

        # Send notifications
        for alert in triggered_alerts:
            self._send_notification(alert)

        return triggered_alerts

    def _evaluate_condition(self, condition: str) -> bool:
        """Evaluate alert condition."""
        try:
            # Simple evaluation for common conditions
            # In production, this would use a safer evaluation method
            if "cpu_usage >" in condition:
                threshold = float(condition.split(">")[-1].strip())
                cpu_percent = psutil.cpu_percent()
                return cpu_percent > threshold

            elif "memory_usage >" in condition:
                threshold = float(condition.split(">")[-1].strip())
                memory_percent = psutil.virtual_memory().percent
                return memory_percent > threshold

            elif "error_rate >" in condition:
                # Check error rate from metrics
                threshold = float(condition.split(">")[-1].strip().rstrip("%"))
                error_metrics = self.metrics_collector.get_metric("errors_total")
                total_metrics = self.metrics_collector.get_metric("requests_total")

                if total_metrics and error_metrics:
                    error_rate = (sum(m.value for m in error_metrics[-100:]) /
                                sum(m.value for m in total_metrics[-100:])) * 100
                    return error_rate > threshold

            # Add more condition types as needed
            return False

        except Exception as e:
            logger.error(f"Error evaluating alert condition '{condition}': {e}")
            return False

    def _send_notification(self, alert: Alert):
        """Send alert notification."""
        message = f"🚨 ALERT: {alert.name} ({alert.severity.value.upper()})\n"
        message += f"Description: {alert.description}\n"
        message += f"Triggered at: {alert.last_triggered}"

        logger.warning(message)

        # Call notification handlers
        for handler in self.notification_handlers:
            try:
                handler(alert, message)
            except Exception as e:
                logger.error(f"Error in notification handler: {e}")

    def get_alert_metrics(self) -> Dict[str, Any]:
        """Get alert metrics."""
        recent_alerts = [a for a in self.alert_history
                        if a['timestamp'] > datetime.utcnow() - timedelta(hours=24)]

        alerts_by_severity = defaultdict(int)
        for alert in recent_alerts:
            alerts_by_severity[alert['severity']] += 1

        return {
            'total_alerts_24h': len(recent_alerts),
            'alerts_by_severity': dict(alerts_by_severity),
            'active_alerts': sum(1 for a in self.alerts.values() if a.enabled)
        }


class HealthChecker:
    """Performs health checks on system components."""

    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
        self.health_checks: Dict[str, callable] = {}
        self.health_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))

    def register_health_check(self, component: str, check_func: callable):
        """Register a health check function."""
        self.health_checks[component] = check_func

    def check_all_components(self) -> Dict[str, HealthStatus]:
        """Perform health checks on all components."""
        results = {}

        for component, check_func in self.health_checks.items():
            try:
                status = check_func()
                results[component] = status

                # Record health status metrics
                self.metrics_collector.set_gauge(
                    'component_health',
                    1.0 if status.status == 'healthy' else 0.0,
                    labels={'component': component}
                )

                # Store in history
                self.health_history[component].append({
                    'timestamp': datetime.utcnow(),
                    'status': status.status,
                    'message': status.message
                })

            except Exception as e:
                error_status = HealthStatus(
                    component=component,
                    status='unhealthy',
                    message=f"Health check failed: {e}"
                )
                results[component] = error_status
                logger.error(f"Health check failed for {component}: {e}")

        return results

    def get_component_uptime(self, component: str, hours: int = 24) -> float:
        """Calculate component uptime percentage."""
        if component not in self.health_history:
            return 0.0

        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        recent_checks = [c for c in self.health_history[component]
                        if c['timestamp'] > cutoff_time]

        if not recent_checks:
            return 0.0

        healthy_count = sum(1 for c in recent_checks if c['status'] == 'healthy')
        return (healthy_count / len(recent_checks)) * 100


class EnterpriseMonitoringSystem:
    """Main enterprise monitoring system."""

    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.alert_manager = AlertManager(self.metrics_collector)
        self.health_checker = HealthChecker(self.metrics_collector)

        self.system_metrics = {
            'cpu': psutil.cpu_percent,
            'memory': lambda: psutil.virtual_memory().percent,
            'disk': lambda: psutil.disk_usage('/').percent,
            'network_io': lambda: psutil.net_io_counters()._asdict()
        }

        self._setup_default_alerts()
        self._setup_health_checks()

        # Start monitoring thread
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()

    def _setup_default_alerts(self):
        """Setup default alert conditions."""
        self.alert_manager.add_alert(Alert(
            name="high_cpu_usage",
            condition="cpu_usage > 80",
            severity=AlertSeverity.WARNING,
            description="CPU usage is above 80%"
        ))

        self.alert_manager.add_alert(Alert(
            name="critical_cpu_usage",
            condition="cpu_usage > 95",
            severity=AlertSeverity.CRITICAL,
            description="CPU usage is critically high"
        ))

        self.alert_manager.add_alert(Alert(
            name="high_memory_usage",
            condition="memory_usage > 85",
            severity=AlertSeverity.WARNING,
            description="Memory usage is above 85%"
        ))

        self.alert_manager.add_alert(Alert(
            name="critical_memory_usage",
            condition="memory_usage > 95",
            severity=AlertSeverity.CRITICAL,
            description="Memory usage is critically high"
        ))

        self.alert_manager.add_alert(Alert(
            name="disk_space_low",
            condition="disk_usage > 90",
            severity=AlertSeverity.WARNING,
            description="Disk space is running low"
        ))

    def _setup_health_checks(self):
        """Setup default health checks."""
        self.health_checker.register_health_check("system_resources", self._check_system_resources)
        self.health_checker.register_health_check("metrics_collection", self._check_metrics_collection)
        self.health_checker.register_health_check("alert_system", self._check_alert_system)
        self.health_checker.register_health_check("python_processes", self._check_python_processes)

    def _check_system_resources(self) -> HealthStatus:
        """Check system resource health."""
        cpu_percent = psutil.cpu_percent()
        memory_percent = psutil.virtual_memory().percent
        disk_percent = psutil.disk_usage('/').percent

        if cpu_percent > 90 or memory_percent > 90 or disk_percent > 95:
            return HealthStatus(
                component="system_resources",
                status="unhealthy",
                message=f"High resource usage: CPU={cpu_percent}%, MEM={memory_percent}%, DISK={disk_percent}%",
                metrics={'cpu': cpu_percent, 'memory': memory_percent, 'disk': disk_percent}
            )
        elif cpu_percent > 70 or memory_percent > 70 or disk_percent > 80:
            return HealthStatus(
                component="system_resources",
                status="degraded",
                message=f"Elevated resource usage: CPU={cpu_percent}%, MEM={memory_percent}%, DISK={disk_percent}%",
                metrics={'cpu': cpu_percent, 'memory': memory_percent, 'disk': disk_percent}
            )
        else:
            return HealthStatus(
                component="system_resources",
                status="healthy",
                message="System resources are normal",
                metrics={'cpu': cpu_percent, 'memory': memory_percent, 'disk': disk_percent}
            )

    def _check_metrics_collection(self) -> HealthStatus:
        """Check metrics collection health."""
        try:
            # Record a test metric
            test_key = f"health_check_{datetime.utcnow().strftime('%Y%m%d%H%M')}"
            self.metrics_collector.set_gauge(test_key, 1.0)

            # Retrieve it
            retrieved = self.metrics_collector.get_metric(test_key)

            if retrieved:
                return HealthStatus(
                    component="metrics_collection",
                    status="healthy",
                    message="Metrics collection working normally"
                )
            else:
                return HealthStatus(
                    component="metrics_collection",
                    status="unhealthy",
                    message="Metrics collection failing"
                )

        except Exception as e:
            return HealthStatus(
                component="metrics_collection",
                status="unhealthy",
                message=f"Metrics collection error: {e}"
            )

    def _check_alert_system(self) -> HealthStatus:
        """Check alert system health."""
        try:
            # Test alert evaluation
            alerts = self.alert_manager.check_alerts()

            return HealthStatus(
                component="alert_system",
                status="healthy",
                message=f"Alert system working, {len(self.alert_manager.alerts)} alerts configured"
            )

        except Exception as e:
            return HealthStatus(
                component="alert_system",
                status="unhealthy",
                message=f"Alert system error: {e}"
            )

    def _check_python_processes(self) -> HealthStatus:
        """Check Python process health."""
        try:
            python_count = len([p for p in psutil.process_iter(['name'])
                              if p.info['name'] == 'Python'])

            # Check current process
            current_process = psutil.Process()
            memory_mb = current_process.memory_info().rss / 1024 / 1024
            cpu_percent = current_process.cpu_percent()

            if memory_mb > 2000:  # More than 2GB
                status = "degraded"
                message = f"High memory usage: {memory_mb:.1f}MB"
            else:
                status = "healthy"
                message = f"Normal resource usage: {memory_mb:.1f}MB, {cpu_percent}% CPU"

            return HealthStatus(
                component="python_processes",
                status=status,
                message=message,
                metrics={'process_count': python_count, 'memory_mb': memory_mb, 'cpu_percent': cpu_percent}
            )

        except Exception as e:
            return HealthStatus(
                component="python_processes",
                status="unhealthy",
                message=f"Process check error: {e}"
            )

    def _monitoring_loop(self):
        """Main monitoring loop."""
        while self.monitoring_active:
            try:
                # Collect system metrics
                cpu_percent = psutil.cpu_percent()
                memory_percent = psutil.virtual_memory().percent
                disk_percent = psutil.disk_usage('/').percent

                self.metrics_collector.set_gauge('system_cpu_usage', cpu_percent)
                self.metrics_collector.set_gauge('system_memory_usage', memory_percent)
                self.metrics_collector.set_gauge('system_disk_usage', disk_percent)

                # Check health
                health_results = self.health_checker.check_all_components()

                # Check alerts
                triggered_alerts = self.alert_manager.check_alerts()

                # Record monitoring system health
                healthy_components = sum(1 for h in health_results.values() if h.status == 'healthy')
                total_components = len(health_results)

                self.metrics_collector.set_gauge(
                    'healthy_components_ratio',
                    healthy_components / total_components if total_components > 0 else 0
                )

                time.sleep(30)  # Check every 30 seconds

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(60)  # Wait longer on error

    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics."""
        return {
            'cpu_usage': psutil.cpu_percent(),
            'memory_usage': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent,
            'network_io': psutil.net_io_counters()._asdict(),
            'process_count': len(psutil.pids()),
            'python_processes': len([p for p in psutil.process_iter(['name'])
                                   if p.info['name'] == 'Python'])
        }

    def get_monitoring_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive monitoring dashboard."""
        health_results = self.health_checker.check_all_components()
        alert_metrics = self.alert_manager.get_alert_metrics()

        # Calculate uptime percentages
        uptime = {}
        for component in health_results.keys():
            uptime[component] = self.health_checker.get_component_uptime(component)

        # Get recent metric trends
        metric_trends = {}
        for metric_name in ['system_cpu_usage', 'system_memory_usage', 'system_disk_usage']:
            recent_metrics = self.metrics_collector.get_metric(
                metric_name,
                since=datetime.utcnow() - timedelta(hours=1)
            )

            if recent_metrics:
                values = [m.value for m in recent_metrics]
                metric_trends[metric_name] = {
                    'current': values[-1] if values else 0,
                    'avg_1h': statistics.mean(values),
                    'max_1h': max(values),
                    'min_1h': min(values)
                }

        return {
            'timestamp': datetime.utcnow().isoformat(),
            'system_health': {
                'overall_status': 'healthy' if all(h.status == 'healthy' for h in health_results.values())
                                 else 'degraded' if any(h.status == 'degraded' for h in health_results.values())
                                 else 'unhealthy',
                'components': {
                    name: {
                        'status': status.status,
                        'message': status.message,
                        'metrics': status.metrics,
                        'uptime_24h': uptime.get(name, 0)
                    }
                    for name, status in health_results.items()
                }
            },
            'alerts': alert_metrics,
            'metrics_trends': metric_trends,
            'system_resources': self.get_system_metrics()
        }

    def add_custom_metric(self, name: str, value: float, metric_type: MetricType = MetricType.GAUGE,
                         labels: Dict[str, str] = None):
        """Add a custom metric."""
        if metric_type == MetricType.COUNTER:
            self.metrics_collector.record_counter(name, value, labels)
        elif metric_type == MetricType.GAUGE:
            self.metrics_collector.set_gauge(name, value, labels)
        elif metric_type == MetricType.HISTOGRAM:
            self.metrics_collector.record_histogram(name, value, labels)
        elif metric_type == MetricType.TIMER:
            self.metrics_collector.record_timer(name, value, labels)

    def shutdown(self):
        """Shutdown monitoring system."""
        self.monitoring_active = False
        if self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=5)


# Global monitoring system instance
monitoring_system = EnterpriseMonitoringSystem()


def get_monitoring_system() -> EnterpriseMonitoringSystem:
    """Get the global monitoring system instance."""
    return monitoring_system


def add_agent_metric(agent_name: str, action: str, duration_ms: float, success: bool = True):
    """Add agent execution metric."""
    monitoring_system.add_custom_metric(
        'agent_execution_duration_ms',
        duration_ms,
        MetricType.TIMER,
        labels={'agent': agent_name, 'action': action}
    )

    monitoring_system.add_custom_metric(
        'agent_executions_total',
        1,
        MetricType.COUNTER,
        labels={'agent': agent_name, 'action': action, 'status': 'success' if success else 'failure'}
    )


def add_api_metric(endpoint: str, duration_ms: float, status_code: int):
    """Add API call metric."""
    monitoring_system.add_custom_metric(
        'api_request_duration_ms',
        duration_ms,
        MetricType.TIMER,
        labels={'endpoint': endpoint, 'status_code': str(status_code)}
    )

    monitoring_system.add_custom_metric(
        'api_requests_total',
        1,
        MetricType.COUNTER,
        labels={'endpoint': endpoint, 'status_code': str(status_code)}
    )


def add_business_metric(metric_name: str, value: float, labels: Dict[str, str] = None):
    """Add business-specific metric."""
    monitoring_system.add_custom_metric(metric_name, value, MetricType.GAUGE, labels)


if __name__ == "__main__":
    # Demo monitoring system
    print("🔍 Enterprise Monitoring System Demo")

    # Get monitoring dashboard
    dashboard = monitoring_system.get_monitoring_dashboard()

    print(f"System Status: {dashboard['system_health']['overall_status']}")
    print(f"Components: {len(dashboard['system_health']['components'])}")
    print(f"Active Alerts: {dashboard['alerts']['active_alerts']}")
    print(f"CPU Usage: {dashboard['system_resources']['cpu_usage']:.1f}%")
    print(f"Memory Usage: {dashboard['system_resources']['memory_usage']:.1f}%")

    # Add some demo metrics
    add_agent_metric("cfbd_integration_agent", "fetch_games", 1250.5, True)
    add_api_metric("/games/2025", 150.2, 200)
    add_business_metric("predictions_generated", 42, {"week": "14", "season": "2025"})

    print("\nDemo metrics added successfully!")

    # Keep running for a bit to show monitoring in action
    try:
        time.sleep(10)
    except KeyboardInterrupt:
        print("\nShutting down monitoring system...")
        monitoring_system.shutdown()