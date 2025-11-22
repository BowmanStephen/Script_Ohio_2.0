#!/usr/bin/env python3
"""
KPI Tracker for CFBD Integration Enhancement
📊 Tracks and visualizes project KPIs across all phases
📈 Real-time monitoring of progress and milestones
🎯 Automated alerting for KPI threshold breaches

Author: Script Ohio 2.0 Agent System
Version: 1.0.0
Created: 2025-01-14
"""

import json
import time
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import statistics

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class KPIDataPoint:
    """Individual KPI data point"""
    timestamp: datetime
    value: float
    metadata: Dict[str, Any]
    source: str

@dataclass
class KPIThreshold:
    """KPI threshold for alerting"""
    kpi_name: str
    threshold_type: str  # "min", "max", "target"
    value: float
    severity: str  # "low", "medium", "high", "critical"
    description: str

@dataclass
class KPIAlert:
    """KPI alert"""
    alert_id: str
    kpi_name: str
    threshold_type: str
    current_value: float
    threshold_value: float
    severity: str
    message: str
    timestamp: datetime
    resolved: bool
    resolved_at: Optional[datetime]

class KPITracker:
    """
    KPI Tracker for CFBD Integration Enhancement Project

    Tracks progress across all phases with real-time monitoring and alerting
    """

    def __init__(self):
        # KPI data storage
        self.kpi_data = defaultdict(lambda: deque(maxlen=10000))
        self.current_values = {}
        self.kpi_definitions = self._load_kpi_definitions()
        self.thresholds = self._load_thresholds()

        # Alert management
        self.alerts = deque(maxlen=1000)
        self.alert_callbacks = []

        # Monitoring
        self.monitoring_active = False
        self.monitoring_thread = None

        # Progress tracking
        self.phase_progress = {}
        self.milestone_tracking = {}

        logger.info("📊 KPI Tracker initialized")

    def _load_kpi_definitions(self) -> Dict[str, Any]:
        """Load KPI definitions from configuration"""
        try:
            kpi_file = Path("project_management/CFBD_INTEGRATION/KPI_DASHBOARD/kpi_definitions.json")
            if kpi_file.exists():
                with open(kpi_file, 'r') as f:
                    data = json.load(f)
                    return data.get("project_kpis", {})
        except Exception as e:
            logger.warning(f"Could not load KPI definitions: {e}")

        # Default KPI definitions
        return {
            "ingestion_latency": {
                "name": "Ingestion Latency",
                "unit": "minutes",
                "target": 10,
                "description": "Time from CFBD data availability to ingestion completion"
            },
            "api_error_rate": {
                "name": "API Error Rate",
                "unit": "percent",
                "target": 0.5,
                "description": "Percentage of CFBD calls returning non-2xx after retries"
            },
            "rate_limit_breaches": {
                "name": "Rate Limit Breaches",
                "unit": "count",
                "target": 0,
                "description": "Count of 429 responses per day"
            },
            "dataset_coverage": {
                "name": "Dataset Coverage",
                "unit": "datasets",
                "target": 12,
                "description": "Number of CFBD datasets actively ingested"
            },
            "agent_compliance": {
                "name": "Agent Compliance",
                "unit": "percent",
                "target": 100,
                "description": "Percentage of agents using unified CFBD client"
            },
            "data_freshness": {
                "name": "Data Freshness",
                "unit": "days",
                "target": 1,
                "description": "Age of latest record per dataset during season"
            },
            "incident_mttr": {
                "name": "Incident MTTR",
                "unit": "minutes",
                "target": 60,
                "description": "Mean time to resolve CFBD-related incidents"
            },
            "documentation_freshness": {
                "name": "Documentation Freshness",
                "unit": "days",
                "target": 30,
                "description": "Days since last update to run-book/governance docs"
            }
        }

    def _load_thresholds(self) -> Dict[str, List[KPIThreshold]]:
        """Load KPI thresholds for alerting"""
        thresholds = defaultdict(list)

        # Define default thresholds based on KPI definitions
        for kpi_name, kpi_def in self.kpi_definitions.items():
            target = kpi_def.get("target", 0)

            # Different threshold types based on KPI nature
            if kpi_name in ["ingestion_latency", "api_error_rate", "rate_limit_breaches",
                           "data_freshness", "incident_mttr", "documentation_freshness"]:
                # Lower is better
                thresholds[kpi_name].extend([
                    KPIThreshold(
                        kpi_name=kpi_name,
                        threshold_type="max",
                        value=target * 1.2,
                        severity="medium",
                        description=f"{kpi_def['name']} approaching warning level"
                    ),
                    KPIThreshold(
                        kpi_name=kpi_name,
                        threshold_type="max",
                        value=target * 1.5,
                        severity="high",
                        description=f"{kpi_def['name']} critical level"
                    ),
                    KPIThreshold(
                        kpi_name=kpi_name,
                        threshold_type="target",
                        value=target,
                        severity="low",
                        description=f"{kpi_def['name']} target achieved"
                    )
                ])
            elif kpi_name in ["dataset_coverage", "agent_compliance"]:
                # Higher is better
                thresholds[kpi_name].extend([
                    KPIThreshold(
                        kpi_name=kpi_name,
                        threshold_type="min",
                        value=target * 0.9,
                        severity="medium",
                        description=f"{kpi_def['name']} below target"
                    ),
                    KPIThreshold(
                        kpi_name=kpi_name,
                        threshold_type="min",
                        value=target * 0.7,
                        severity="high",
                        description=f"{kpi_def['name']} critically low"
                    ),
                    KPIThreshold(
                        kpi_name=kpi_name,
                        threshold_type="target",
                        value=target,
                        severity="low",
                        description=f"{kpi_def['name']} target achieved"
                    )
                ])

        return thresholds

    def record_kpi(self, kpi_name: str, value: float, metadata: Dict[str, Any] = None,
                   source: str = "manual") -> Dict[str, Any]:
        """Record a KPI value"""
        if metadata is None:
            metadata = {}

        # Create data point
        data_point = KPIDataPoint(
            timestamp=datetime.now(),
            value=value,
            metadata=metadata,
            source=source
        )

        # Store data point
        self.kpi_data[kpi_name].append(data_point)
        self.current_values[kpi_name] = value

        # Check thresholds and create alerts
        self._check_thresholds(kpi_name, value)

        logger.info(f"📊 Recorded KPI {kpi_name}: {value} ({self.kpi_definitions.get(kpi_name, {}).get('unit', '')})")

        return {
            "status": "success",
            "kpi_name": kpi_name,
            "value": value,
            "timestamp": data_point.timestamp.isoformat()
        }

    def get_kpi_history(self, kpi_name: str, hours: int = 24) -> List[Dict[str, Any]]:
        """Get KPI history for specified time range"""
        if kpi_name not in self.kpi_data:
            return []

        cutoff_time = datetime.now() - timedelta(hours=hours)
        history = [
            {
                "timestamp": dp.timestamp.isoformat(),
                "value": dp.value,
                "metadata": dp.metadata,
                "source": dp.source
            }
            for dp in self.kpi_data[kpi_name]
            if dp.timestamp >= cutoff_time
        ]

        return history

    def get_kpi_summary(self, kpi_name: str, hours: int = 24) -> Dict[str, Any]:
        """Get KPI summary statistics"""
        history = self.get_kpi_history(kpi_name, hours)

        if not history:
            return {
                "kpi_name": kpi_name,
                "data_points": 0,
                "current_value": None,
                "average": None,
                "trend": "no_data"
            }

        values = [h["value"] for h in history]
        current_value = values[-1] if values else None
        average = statistics.mean(values) if values else None

        # Calculate trend
        if len(values) >= 2:
            recent_avg = statistics.mean(values[-5:])  # Last 5 data points
            older_avg = statistics.mean(values[:5])   # First 5 data points

            if recent_avg > older_avg * 1.1:
                trend = "increasing"
            elif recent_avg < older_avg * 0.9:
                trend = "decreasing"
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"

        # Get KPI definition
        kpi_def = self.kpi_definitions.get(kpi_name, {})
        target = kpi_def.get("target")

        return {
            "kpi_name": kpi_name,
            "definition": kpi_def,
            "data_points": len(history),
            "current_value": current_value,
            "average": average,
            "min": min(values) if values else None,
            "max": max(values) if values else None,
            "target": target,
            "target_met": target is not None and current_value is not None and self._is_target_met(kpi_name, current_value, target),
            "trend": trend
        }

    def get_project_overview(self) -> Dict[str, Any]:
        """Get overall project KPI overview"""
        overview = {
            "timestamp": datetime.now().isoformat(),
            "kpi_summaries": {},
            "overall_health": "healthy",
            "critical_alerts": 0,
            "active_alerts": 0,
            "phase_progress": self.phase_progress
        }

        # Get summary for all KPIs
        for kpi_name in self.kpi_definitions.keys():
            summary = self.get_kpi_summary(kpi_name)
            overview["kpi_summaries"][kpi_name] = summary

        # Count alerts
        active_alerts = [a for a in self.alerts if not a.resolved]
        critical_alerts = [a for a in active_alerts if a.severity == "critical"]

        overview["active_alerts"] = len(active_alerts)
        overview["critical_alerts"] = len(critical_alerts)

        # Determine overall health
        if critical_alerts:
            overview["overall_health"] = "critical"
        elif len(active_alerts) > 0:
            overview["overall_health"] = "degraded"
        elif len([s for s in overview["kpi_summaries"].values() if s.get("target_met", False)]) == len(overview["kpi_summaries"]):
            overview["overall_health"] = "excellent"

        return overview

    def update_phase_progress(self, phase_name: str, progress_percentage: float,
                            metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Update phase progress"""
        if metadata is None:
            metadata = {}

        self.phase_progress[phase_name] = {
            "progress_percentage": progress_percentage,
            "last_updated": datetime.now().isoformat(),
            "metadata": metadata
        }

        # Record as KPI
        self.record_kpi(
            f"phase_{phase_name}_progress",
            progress_percentage,
            {"phase": phase_name, **metadata},
            "phase_tracker"
        )

        logger.info(f"📈 Updated {phase_name} progress: {progress_percentage}%")

        return {
            "status": "success",
            "phase": phase_name,
            "progress": progress_percentage,
            "timestamp": self.phase_progress[phase_name]["last_updated"]
        }

    def mark_milestone(self, milestone_name: str, completed: bool = True,
                       metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Mark milestone completion"""
        if metadata is None:
            metadata = {}

        self.milestone_tracking[milestone_name] = {
            "completed": completed,
            "completion_date": datetime.now().isoformat() if completed else None,
            "metadata": metadata
        }

        # Record as KPI (binary: 1 for completed, 0 for not completed)
        self.record_kpi(
            f"milestone_{milestone_name}",
            1.0 if completed else 0.0,
            {"milestone": milestone_name, **metadata},
            "milestone_tracker"
        )

        status = "completed" if completed else "reverted"
        logger.info(f"🎯 Milestone {milestone_name} {status}")

        return {
            "status": "success",
            "milestone": milestone_name,
            "completed": completed,
            "timestamp": self.milestone_tracking[milestone_name]["completion_date"]
        }

    def generate_dashboard_data(self) -> Dict[str, Any]:
        """Generate data for KPI dashboard"""
        overview = self.get_project_overview()

        dashboard_data = {
            "overview": overview,
            "kpi_details": {},
            "phase_details": {},
            "milestone_details": {},
            "alerts": self._get_active_alerts(),
            "trends": {}
        }

        # Detailed KPI information
        for kpi_name, kpi_def in self.kpi_definitions.items():
            summary = overview["kpi_summaries"].get(kpi_name, {})
            history = self.get_kpi_history(kpi_name, hours=24)

            dashboard_data["kpi_details"][kpi_name] = {
                "definition": kpi_def,
                "summary": summary,
                "history": history[-10:],  # Last 10 data points
                "trend_7d": self._calculate_trend(kpi_name, hours=168),
                "trend_24h": self._calculate_trend(kpi_name, hours=24)
            }

        # Phase details
        for phase_name, phase_data in self.phase_progress.items():
            dashboard_data["phase_details"][phase_name] = {
                "progress": phase_data["progress_percentage"],
                "last_updated": phase_data["last_updated"],
                "metadata": phase_data.get("metadata", {})
            }

        # Milestone details
        for milestone_name, milestone_data in self.milestone_tracking.items():
            dashboard_data["milestone_details"][milestone_name] = {
                "completed": milestone_data["completed"],
                "completion_date": milestone_data["completion_date"],
                "metadata": milestone_data.get("metadata", {})
            }

        # Calculate trends
        dashboard_data["trends"] = self._calculate_project_trends()

        return dashboard_data

    def export_data(self, format_type: str = "json", hours: int = 24) -> Dict[str, Any]:
        """Export KPI data in specified format"""
        if format_type.lower() == "json":
            return self._export_json(hours)
        elif format_type.lower() == "csv":
            return self._export_csv(hours)
        else:
            raise ValueError(f"Unsupported export format: {format_type}")

    def _check_thresholds(self, kpi_name: str, value: float):
        """Check KPI against thresholds and create alerts"""
        if kpi_name not in self.thresholds:
            return

        for threshold in self.thresholds[kpi_name]:
            alert_triggered = False

            if threshold.threshold_type == "max" and value > threshold.value:
                alert_triggered = True
                message = f"{kpi_name} exceeded maximum threshold: {value} > {threshold.value}"
            elif threshold.threshold_type == "min" and value < threshold.value:
                alert_triggered = True
                message = f"{kpi_name} below minimum threshold: {value} < {threshold.value}"
            elif threshold.threshold_type == "target" and self._is_target_met(kpi_name, value, threshold.value):
                alert_triggered = True
                message = f"{kpi_name} achieved target: {value} (target: {threshold.value})"

            if alert_triggered:
                alert = KPIAlert(
                    alert_id=f"{kpi_name}_{threshold.threshold_type}_{int(datetime.now().timestamp())}",
                    kpi_name=kpi_name,
                    threshold_type=threshold.threshold_type,
                    current_value=value,
                    threshold_value=threshold.value,
                    severity=threshold.severity,
                    message=message,
                    timestamp=datetime.now(),
                    resolved=False,
                    resolved_at=None
                )

                self.alerts.append(alert)
                logger.warning(f"🚨 KPI Alert [{threshold.severity}]: {message}")

                # Call alert callbacks
                for callback in self.alert_callbacks:
                    try:
                        callback(alert)
                    except Exception as e:
                        logger.error(f"Alert callback failed: {e}")

    def _is_target_met(self, kpi_name: str, value: float, target: float) -> bool:
        """Determine if KPI target is met"""
        # For some KPIs, lower is better
        lower_is_better = kpi_name in [
            "ingestion_latency", "api_error_rate", "rate_limit_breaches",
            "data_freshness", "incident_mttr", "documentation_freshness"
        ]

        if lower_is_better:
            return value <= target
        else:
            return value >= target

    def _get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get list of active alerts"""
        return [
            asdict(alert) for alert in self.alerts
            if not alert.resolved
        ]

    def _calculate_trend(self, kpi_name: str, hours: int) -> Dict[str, Any]:
        """Calculate trend for a KPI over specified period"""
        history = self.get_kpi_history(kpi_name, hours)

        if len(history) < 2:
            return {"trend": "insufficient_data", "change_percent": 0}

        values = [h["value"] for h in history]
        first_value = values[0]
        last_value = values[-1]

        if first_value == 0:
            change_percent = float('inf') if last_value > 0 else 0
        else:
            change_percent = ((last_value - first_value) / first_value) * 100

        # Determine trend direction
        if abs(change_percent) < 5:
            trend = "stable"
        elif change_percent > 0:
            trend = "improving" if kpi_name not in [
                "ingestion_latency", "api_error_rate", "rate_limit_breaches",
                "data_freshness", "incident_mttr", "documentation_freshness"
            ] else "degrading"
        else:
            trend = "degrading" if kpi_name not in [
                "ingestion_latency", "api_error_rate", "rate_limit_breaches",
                "data_freshness", "incident_mttr", "documentation_freshness"
            ] else "improving"

        return {
            "trend": trend,
            "change_percent": change_percent,
            "first_value": first_value,
            "last_value": last_value,
            "data_points": len(values)
        }

    def _calculate_project_trends(self) -> Dict[str, Any]:
        """Calculate overall project trends"""
        trends = {
            "overall_health": "stable",
            "improving_kpis": [],
            "degrading_kpis": [],
            "stable_kpis": []
        }

        for kpi_name in self.kpi_definitions.keys():
            trend_24h = self._calculate_trend(kpi_name, 24)
            trend_7d = self._calculate_trend(kpi_name, 168)

            trends[f"{kpi_name}_24h"] = trend_24h
            trends[f"{kpi_name}_7d"] = trend_7d

            # Classify by trend
            if trend_24h["trend"] == "improving":
                trends["improving_kpis"].append(kpi_name)
            elif trend_24h["trend"] == "degrading":
                trends["degrading_kpis"].append(kpi_name)
            else:
                trends["stable_kpis"].append(kpi_name)

        # Overall trend assessment
        if trends["degrading_kpis"]:
            trends["overall_health"] = "degrading"
        elif trends["improving_kpis"] and not trends["degrading_kpis"]:
            trends["overall_health"] = "improving"

        return trends

    def _export_json(self, hours: int) -> Dict[str, Any]:
        """Export KPI data as JSON"""
        return {
            "export_timestamp": datetime.now().isoformat(),
            "time_range_hours": hours,
            "kpi_data": {
                kpi_name: self.get_kpi_history(kpi_name, hours)
                for kpi_name in self.kpi_definitions.keys()
            },
            "phase_progress": self.phase_progress,
            "milestone_tracking": self.milestone_tracking,
            "alerts": [asdict(alert) for alert in self.alerts]
        }

    def _export_csv(self, hours: int) -> Dict[str, Any]:
        """Export KPI data as CSV (conceptual)"""
        # In a real implementation, this would generate actual CSV files
        return {
            "format": "csv",
            "files_generated": len(self.kpi_definitions),
            "time_range_hours": hours,
            "note": "CSV export would generate separate files for each KPI"
        }

    def add_alert_callback(self, callback: Callable[[KPIAlert], None]):
        """Add callback function for alerts"""
        self.alert_callbacks.append(callback)

    def start_monitoring(self, check_interval: int = 60):
        """Start background monitoring"""
        if self.monitoring_active:
            return

        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(check_interval,),
            daemon=True
        )
        self.monitoring_thread.start()
        logger.info("📊 KPI monitoring started")

    def stop_monitoring(self):
        """Stop background monitoring"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        logger.info("📊 KPI monitoring stopped")

    def _monitoring_loop(self, check_interval: int):
        """Background monitoring loop"""
        while self.monitoring_active:
            try:
                # Auto-generate some derived KPIs
                self._update_derived_kpis()
                time.sleep(check_interval)
            except Exception as e:
                logger.error(f"KPI monitoring loop error: {e}")
                time.sleep(check_interval)

    def _update_derived_kpis(self):
        """Update automatically calculated KPIs"""
        # Example: Calculate overall compliance rate
        if "agent_compliance" in self.current_values and "dataset_coverage" in self.current_values:
            agent_comp = self.current_values["agent_compliance"]
            data_cov = self.current_values["dataset_coverage"]

            # Weighted average of compliance metrics
            overall_health = (agent_comp * 0.6 + (data_cov / 12 * 100) * 0.4)

            self.record_kpi(
                "overall_system_health",
                overall_health,
                {"derived_from": ["agent_compliance", "dataset_coverage"]},
                "auto_calculated"
            )

# Global KPI tracker instance
kpi_tracker = KPITracker()

# Convenience functions
def record_kpi(kpi_name: str, value: float, metadata: Dict[str, Any] = None, source: str = "manual"):
    """Record a KPI value"""
    return kpi_tracker.record_kpi(kpi_name, value, metadata, source)

def get_project_overview() -> Dict[str, Any]:
    """Get overall project KPI overview"""
    return kpi_tracker.get_project_overview()

def update_phase_progress(phase_name: str, progress: float, metadata: Dict[str, Any] = None):
    """Update phase progress"""
    return kpi_tracker.update_phase_progress(phase_name, progress, metadata)

def mark_milestone(milestone_name: str, completed: bool = True, metadata: Dict[str, Any] = None):
    """Mark milestone completion"""
    return kpi_tracker.mark_milestone(milestone_name, completed, metadata)

def generate_dashboard() -> Dict[str, Any]:
    """Generate dashboard data"""
    return kpi_tracker.generate_dashboard_data()

if __name__ == "__main__":
    # Test the KPI tracker
    print("📊 Testing KPI Tracker")

    # Record some test KPIs
    record_kpi("agent_compliance", 75.0, {"phase": "phase_0"})
    record_kpi("dataset_coverage", 8.0, {"source": "data_agent"})

    # Update phase progress
    update_phase_progress("phase_0_foundation", 60.0)

    # Mark milestone
    mark_milestone("dependency_unification", True)

    # Get overview
    overview = get_project_overview()
    print(f"✅ Overview: {overview['overall_health']} health")
    print(f"📈 Active alerts: {overview['active_alerts']}")