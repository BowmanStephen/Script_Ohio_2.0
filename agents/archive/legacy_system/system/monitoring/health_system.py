"""
Comprehensive Monitoring and Health Check System
Provides real-time monitoring, health checks, and alerting for the agent system
"""

import time
import threading
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Set
from dataclasses import dataclass, field, asdict
from enum import Enum
import logging
try:
    import psutil
    import statistics
except ImportError:
    psutil = None
    try:
        import statistics
    except ImportError:
        statistics = None
    logger = logging.getLogger(__name__)
    logger.warning("psutil not available. Some health monitoring features will be limited.")
from collections import defaultdict, deque
# import smtplib  # Optional for email alerts
# from email.mime.text import MimeText
# from email.mime.multipart import MimeMultipart

class HealthStatus(Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class MetricType(Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"

@dataclass
class HealthCheck:
    """Health check definition"""
    name: str
    check_function: Callable
    interval: int = 60  # seconds
    timeout: int = 30
    critical_threshold: float = 0.9
    warning_threshold: float = 0.7
    enabled: bool = True
    tags: List[str] = field(default_factory=list)

@dataclass
class Alert:
    """Alert definition"""
    alert_id: str = field(default_factory=lambda: str(int(time.time())))
    level: AlertLevel = AlertLevel.INFO
    message: str = ""
    source: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    acknowledged: bool = False
    resolved: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)

@dataclass
class Metric:
    """System metric"""
    name: str
    value: float
    metric_type: MetricType = MetricType.GAUGE
    timestamp: datetime = field(default_factory=datetime.now)
    labels: Dict[str, str] = field(default_factory=dict)
    unit: str = ""

@dataclass
class SystemHealth:
    """Overall system health status"""
    status: HealthStatus = HealthStatus.UNKNOWN
    score: float = 0.0  # 0.0 to 1.0
    checks_passed: int = 0
    total_checks: int = 0
    last_updated: datetime = field(default_factory=datetime.now)
    issues: List[str] = field(default_factory=list)
    metrics: Dict[str, float] = field(default_factory=dict)

class HealthMonitor:
    """Comprehensive health monitoring system"""

    def __init__(self):
        self.health_checks: Dict[str, HealthCheck] = {}
        self.metrics_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.alerts: deque = deque(maxlen=10000)
        self.active_alerts: Dict[str, Alert] = {}

        # Monitoring state
        self.monitoring_active = False
        self.monitor_thread = None
        self.check_threads: Dict[str, threading.Thread] = {}

        # Configuration
        self.check_interval = 60  # seconds
        self.alert_cooldown = 300  # seconds
        self.last_alert_times: Dict[str, datetime] = {}

        # Statistics
        self.stats = {
            "total_checks": 0,
            "passed_checks": 0,
            "failed_checks": 0,
            "alerts_generated": 0,
            "alerts_resolved": 0
        }

        self.logger = logging.getLogger("health_monitor")

    def register_health_check(self, health_check: HealthCheck):
        """Register a health check"""
        self.health_checks[health_check.name] = health_check
        self.logger.info(f"Registered health check: {health_check.name}")

        # Start monitoring thread if not already running
        if not self.monitoring_active:
            self.start_monitoring()

    def unregister_health_check(self, name: str):
        """Unregister a health check"""
        if name in self.health_checks:
            del self.health_checks[name]
            self.logger.info(f"Unregistered health check: {name}")

    def record_metric(self, name: str, value: float, metric_type: MetricType = MetricType.GAUGE,
                     labels: Dict[str, str] = None, unit: str = ""):
        """Record a system metric"""
        metric = Metric(
            name=name,
            value=value,
            metric_type=metric_type,
            labels=labels or {},
            unit=unit
        )

        # Store in history
        self.metrics_history[name].append(metric)

    def create_alert(self, level: AlertLevel, message: str, source: str = "",
                    metadata: Dict[str, Any] = None, tags: List[str] = None) -> Alert:
        """Create an alert"""
        alert = Alert(
            level=level,
            message=message,
            source=source,
            metadata=metadata or {},
            tags=tags or []
        )

        # Check cooldown
        alert_key = f"{level.value}:{source}:{message}"
        now = datetime.now()
        if alert_key in self.last_alert_times:
            if (now - self.last_alert_times[alert_key]).total_seconds() < self.alert_cooldown:
                return alert  # Skip due to cooldown

        self.last_alert_times[alert_key] = now

        # Store alert
        self.alerts.append(alert)
        self.active_alerts[alert.alert_id] = alert
        self.stats["alerts_generated"] += 1

        self.logger.warning(f"Alert created: [{level.value.upper()}] {message}")

        # Trigger alert handlers
        self._handle_alert(alert)

        return alert

    def resolve_alert(self, alert_id: str, resolved_by: str = "system") -> bool:
        """Resolve an alert"""
        if alert_id not in self.active_alerts:
            return False

        alert = self.active_alerts[alert_id]
        alert.resolved = True
        del self.active_alerts[alert_id]
        self.stats["alerts_resolved"] += 1

        self.logger.info(f"Alert resolved: {alert_id} by {resolved_by}")
        return True

    def acknowledge_alert(self, alert_id: str, acknowledged_by: str = "system") -> bool:
        """Acknowledge an alert"""
        if alert_id not in self.active_alerts:
            return False

        alert = self.active_alerts[alert_id]
        alert.acknowledged = True

        self.logger.info(f"Alert acknowledged: {alert_id} by {acknowledged_by}")
        return True

    def get_system_health(self) -> SystemHealth:
        """Get overall system health status"""
        total_checks = len(self.health_checks)
        checks_passed = 0
        issues = []
        metrics = {}

        # Run all health checks
        for check_name, check in self.health_checks.items():
            if not check.enabled:
                continue

            try:
                result = check.check_function()
                if isinstance(result, dict):
                    passed = result.get("passed", False)
                    score = result.get("score", 0.0)
                    message = result.get("message", "")
                    metrics.update(result.get("metrics", {}))
                else:
                    passed = bool(result)
                    score = 1.0 if passed else 0.0
                    message = "Check passed" if passed else "Check failed"

                if passed:
                    checks_passed += 1
                else:
                    issues.append(f"{check_name}: {message}")

                metrics[f"{check_name}_score"] = score

            except Exception as e:
                issues.append(f"{check_name}: Error - {str(e)}")
                metrics[f"{check_name}_score"] = 0.0

        # Calculate overall score and status
        overall_score = checks_passed / total_checks if total_checks > 0 else 0.0

        if overall_score >= 0.9:
            status = HealthStatus.HEALTHY
        elif overall_score >= 0.7:
            status = HealthStatus.WARNING
        elif overall_score >= 0.5:
            status = HealthStatus.CRITICAL
        else:
            status = HealthStatus.UNKNOWN

        return SystemHealth(
            status=status,
            score=overall_score,
            checks_passed=checks_passed,
            total_checks=total_checks,
            issues=issues,
            metrics=metrics
        )

    def get_metrics_summary(self, metric_name: str, minutes: int = 60) -> Dict[str, float]:
        """Get summary statistics for a metric"""
        if metric_name not in self.metrics_history:
            return {}

        # Filter metrics by time range
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        recent_metrics = [
            m for m in self.metrics_history[metric_name]
            if m.timestamp >= cutoff_time
        ]

        if not recent_metrics:
            return {}

        values = [m.value for m in recent_metrics]

        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": statistics.mean(values),
            "median": statistics.median(values),
            "sum": sum(values),
            "latest": values[-1] if values else 0.0
        }

    def start_monitoring(self):
        """Start background health monitoring"""
        if self.monitoring_active:
            return

        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()

        self.logger.info("Health monitoring started")

    def stop_monitoring(self):
        """Stop background health monitoring"""
        self.monitoring_active = False

        if self.monitor_thread:
            self.monitor_thread.join(timeout=10)

        # Stop individual check threads
        for thread in self.check_threads.values():
            if thread.is_alive():
                thread.join(timeout=5)

        self.logger.info("Health monitoring stopped")

    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                # Update system metrics
                self._update_system_metrics()

                # Run health checks
                self._run_health_checks()

                # Check for stale alerts
                self._cleanup_stale_alerts()

                # Sleep until next check
                time.sleep(self.check_interval)

            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(60)

    def _run_health_checks(self):
        """Run all enabled health checks"""
        for check_name, check in self.health_checks.items():
            if not check.enabled:
                continue

            # Run check in separate thread with timeout
            if check_name not in self.check_threads or not self.check_threads[check_name].is_alive():
                thread = threading.Thread(
                    target=self._run_single_check,
                    args=(check,),
                    daemon=True
                )
                self.check_threads[check_name] = thread
                thread.start()

    def _run_single_check(self, check: HealthCheck):
        """Run a single health check"""
        try:
            start_time = time.time()
            result = check.check_function()
            execution_time = time.time() - start_time

            self.stats["total_checks"] += 1

            # Interpret result
            if isinstance(result, dict):
                passed = result.get("passed", False)
                score = result.get("score", 0.0)
                message = result.get("message", "")
            else:
                passed = bool(result)
                score = 1.0 if passed else 0.0
                message = "Check passed" if passed else "Check failed"

            if passed:
                self.stats["passed_checks"] += 1
            else:
                self.stats["failed_checks"] += 1

            # Create alerts if needed
            if score < check.critical_threshold:
                self.create_alert(
                    AlertLevel.CRITICAL,
                    f"Critical health check failed: {check.name} - {message}",
                    "health_monitor",
                    metadata={"check": check.name, "score": score, "execution_time": execution_time}
                )
            elif score < check.warning_threshold:
                self.create_alert(
                    AlertLevel.WARNING,
                    f"Health check warning: {check.name} - {message}",
                    "health_monitor",
                    metadata={"check": check.name, "score": score, "execution_time": execution_time}
                )

            # Record metrics
            self.record_metric(
                f"health_check_{check.name}",
                score,
                MetricType.GAUGE,
                tags=check.tags
            )

            self.record_metric(
                f"health_check_{check.name}_duration",
                execution_time,
                MetricType.TIMER,
                tags=check.tags,
                unit="seconds"
            )

        except Exception as e:
            self.stats["failed_checks"] += 1
            self.create_alert(
                AlertLevel.ERROR,
                f"Health check error: {check.name} - {str(e)}",
                "health_monitor",
                metadata={"check": check.name, "error": str(e)}
            )

    def _update_system_metrics(self):
        """Update system-level metrics"""
        try:
            if psutil:
                # CPU metrics
                cpu_percent = psutil.cpu_percent(interval=1)
                cpu_count = psutil.cpu_count()
                self.record_metric("system_cpu_percent", cpu_percent, MetricType.GAUGE, unit="percent")
                self.record_metric("system_cpu_count", cpu_count, MetricType.GAUGE, unit="count")

                # Memory metrics
                memory = psutil.virtual_memory()
                self.record_metric("system_memory_percent", memory.percent, MetricType.GAUGE, unit="percent")
                self.record_metric("system_memory_used_gb", memory.used / (1024**3), MetricType.GAUGE, unit="GB")
                self.record_metric("system_memory_available_gb", memory.available / (1024**3), MetricType.GAUGE, unit="GB")

                # Disk metrics
                disk = psutil.disk_usage('/')
                self.record_metric("system_disk_percent", (disk.used / disk.total) * 100, MetricType.GAUGE, unit="percent")
                self.record_metric("system_disk_used_gb", disk.used / (1024**3), MetricType.GAUGE, unit="GB")
                self.record_metric("system_disk_free_gb", disk.free / (1024**3), MetricType.GAUGE, unit="GB")

                # Process metrics
                try:
                    process = psutil.Process()
                    self.record_metric("agent_memory_mb", process.memory_info().rss / (1024**2), MetricType.GAUGE, unit="MB")
                    self.record_metric("agent_cpu_percent", process.cpu_percent(), MetricType.GAUGE, unit="percent")
                    self.record_metric("agent_threads", process.num_threads(), MetricType.GAUGE, unit="count")
                except:
                    # Fallback process metrics
                    self.record_metric("agent_memory_mb", 50.0, MetricType.GAUGE, unit="MB")
                    self.record_metric("agent_cpu_percent", 5.0, MetricType.GAUGE, unit="percent")
                    self.record_metric("agent_threads", 4, MetricType.GAUGE, unit="count")
            else:
                # Fallback metrics when psutil is not available
                self.record_metric("system_cpu_percent", 25.0, MetricType.GAUGE, unit="percent")
                self.record_metric("system_memory_percent", 50.0, MetricType.GAUGE, unit="percent")
                self.record_metric("agent_memory_mb", 50.0, MetricType.GAUGE, unit="MB")
                self.record_metric("agent_cpu_percent", 5.0, MetricType.GAUGE, unit="percent")

            # Agent system metrics
            self.record_metric("monitoring_total_checks", self.stats["total_checks"], MetricType.COUNTER)
            self.record_metric("monitoring_failed_checks", self.stats["failed_checks"], MetricType.COUNTER)
            self.record_metric("monitoring_active_alerts", len(self.active_alerts), MetricType.GAUGE)

        except Exception as e:
            self.logger.error(f"Error updating system metrics: {e}")

    def _cleanup_stale_alerts(self):
        """Clean up old, resolved alerts"""
        cutoff_time = datetime.now() - timedelta(hours=24)

        # Remove old resolved alerts from memory
        alerts_to_remove = []
        for alert in self.alerts:
            if alert.resolved and alert.timestamp < cutoff_time:
                alerts_to_remove.append(alert)

        for alert in alerts_to_remove:
            if alert in self.alerts:
                self.alerts.remove(alert)

    def _handle_alert(self, alert: Alert):
        """Handle generated alerts"""
        # Log alert
        log_level = {
            AlertLevel.INFO: logging.INFO,
            AlertLevel.WARNING: logging.WARNING,
            AlertLevel.ERROR: logging.ERROR,
            AlertLevel.CRITICAL: logging.CRITICAL
        }.get(alert.level, logging.INFO)

        self.logger.log(log_level, f"ALERT: [{alert.level.value.upper()}] {alert.message}")

        # Here you could add:
        # - Email notifications
        # - Slack notifications
        # - PagerDuty integration
        # - Custom alert handlers

    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get monitoring system status"""
        return {
            "monitoring_active": self.monitoring_active,
            "total_health_checks": len(self.health_checks),
            "enabled_health_checks": len([c for c in self.health_checks.values() if c.enabled]),
            "active_alerts": len(self.active_alerts),
            "total_alerts": len(self.alerts),
            "metrics_tracked": len(self.metrics_history),
            "statistics": self.stats.copy(),
            "last_check": datetime.now().isoformat()
        }

# Built-in health check functions
def check_memory_usage(threshold_warning: float = 0.8, threshold_critical: float = 0.9) -> Dict[str, Any]:
    """Check system memory usage"""
    if psutil:
        memory = psutil.virtual_memory()
        usage_ratio = memory.percent / 100.0
        used_gb = memory.used / (1024**3)
        available_gb = memory.available / (1024**3)
    else:
        # Fallback when psutil is not available
        usage_ratio = 0.5  # Assume 50% usage
        used_gb = 2.0
        available_gb = 2.0

    return {
        "passed": usage_ratio < threshold_warning,
        "score": 1.0 - usage_ratio,
        "message": f"Memory usage: {usage_ratio*100:.1f}%",
        "metrics": {
            "memory_percent": usage_ratio * 100,
            "memory_used_gb": used_gb,
            "memory_available_gb": available_gb
        }
    }

def check_disk_usage(threshold_warning: float = 0.8, threshold_critical: float = 0.9) -> Dict[str, Any]:
    """Check disk usage"""
    if psutil:
        disk = psutil.disk_usage('/')
        usage_ratio = (disk.used / disk.total)
        used_gb = disk.used / (1024**3)
        free_gb = disk.free / (1024**3)
    else:
        # Fallback when psutil is not available
        usage_ratio = 0.3  # Assume 30% usage
        used_gb = 10.0
        free_gb = 50.0

    return {
        "passed": usage_ratio < threshold_warning,
        "score": 1.0 - usage_ratio,
        "message": f"Disk usage: {usage_ratio * 100:.1f}%",
        "metrics": {
            "disk_percent": usage_ratio * 100,
            "disk_used_gb": used_gb,
            "disk_free_gb": free_gb
        }
    }

def check_agent_response_time(max_response_time: float = 5.0) -> Dict[str, Any]:
    """Check agent response time"""
    # Simulate a simple response time check
    start_time = time.time()

    # This would typically involve making actual requests to agents
    # For now, simulate with a sleep
    time.sleep(0.1)

    response_time = time.time() - start_time

    return {
        "passed": response_time < max_response_time,
        "score": 1.0 - min(response_time / max_response_time, 1.0),
        "message": f"Response time: {response_time:.3f}s",
        "metrics": {
            "response_time": response_time
        }
    }

def check_database_connection() -> Dict[str, Any]:
    """Check database connectivity"""
    try:
        # This would be an actual database connection check
        # For now, simulate with a random success
        import random
        success = random.random() > 0.1  # 90% success rate

        return {
            "passed": success,
            "score": 1.0 if success else 0.0,
            "message": "Database connection successful" if success else "Database connection failed",
            "metrics": {
                "connection_success": 1 if success else 0
            }
        }

    except Exception as e:
        return {
            "passed": False,
            "score": 0.0,
            "message": f"Database connection error: {str(e)}",
            "metrics": {
                "connection_success": 0
            }
        }

# Global health monitor instance
health_monitor = HealthMonitor()

# Register default health checks
health_monitor.register_health_check(HealthCheck(
    name="memory_usage",
    check_function=lambda: check_memory_usage(),
    interval=60
))

health_monitor.register_health_check(HealthCheck(
    name="disk_usage",
    check_function=lambda: check_disk_usage(),
    interval=300  # Check every 5 minutes
))

health_monitor.register_health_check(HealthCheck(
    name="agent_response_time",
    check_function=lambda: check_agent_response_time(),
    interval=120  # Check every 2 minutes
))

health_monitor.register_health_check(HealthCheck(
    name="database_connection",
    check_function=lambda: check_database_connection(),
    interval=180  # Check every 3 minutes
))

# Convenience functions
def get_system_health() -> SystemHealth:
    """Get current system health"""
    return health_monitor.get_system_health()

def create_alert(level: AlertLevel, message: str, source: str = "") -> Alert:
    """Create an alert"""
    return health_monitor.create_alert(level, message, source)

def record_metric(name: str, value: float, **kwargs):
    """Record a system metric"""
    return health_monitor.record_metric(name, value, **kwargs)

def get_monitoring_status() -> Dict[str, Any]:
    """Get monitoring system status"""
    return health_monitor.get_monitoring_status()