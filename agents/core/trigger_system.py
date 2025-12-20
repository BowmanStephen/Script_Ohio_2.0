"""
🔄 Trigger System for Autonomous Orchestration

Manages various types of triggers that can initiate autonomous workflows:
- Schedule-based triggers (time-based)
- Event-driven triggers (API changes, file updates)
- Performance-based triggers (accuracy drops, resource limits)
- Data-based triggers (new data availability, thresholds)
"""

import json
import logging
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class TriggerType(Enum):
    """Types of triggers"""
    SCHEDULE = "schedule"
    EVENT = "event"
    PERFORMANCE = "performance"
    DATA_THRESHOLD = "data_threshold"
    EXTERNAL_WEBHOOK = "external_webhook"
    CUSTOM = "custom"


class TriggerStatus(Enum):
    """Trigger status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    TRIGGERED = "triggered"
    ERROR = "error"


@dataclass
class TriggerDefinition:
    """Definition of a trigger"""
    id: str
    name: str
    trigger_type: TriggerType
    config: Dict[str, Any]
    workflow_mapping: str  # Which workflow to trigger
    enabled: bool = True
    conditions: List[Dict[str, Any]] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    cooldown_seconds: int = 300  # Minimum time between triggers
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0
    status: TriggerStatus = TriggerStatus.ACTIVE
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TriggerEvent:
    """Event that occurred"""
    event_id: str
    trigger_id: str
    timestamp: datetime
    data: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)


class TriggerRegistry:
    """
    Registry for managing autonomous workflow triggers
    """

    def __init__(self, registry_path: Optional[Path] = None):
        """Initialize the trigger registry"""
        self.triggers: Dict[str, TriggerDefinition] = {}
        self.active_events: List[TriggerEvent] = []
        self.event_handlers: Dict[TriggerType, List[Callable]] = {
            trigger_type: [] for trigger_type in TriggerType
        }

        # File persistence
        self.registry_path = registry_path or Path("project_management/triggers/registry.json")
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)

        # Load existing triggers
        self._load_triggers()

        logger.info(f"TriggerRegistry initialized with {len(self.triggers)} triggers")

    def register_trigger(self, trigger_def: TriggerDefinition) -> bool:
        """Register a new trigger"""
        try:
            # Validate trigger definition
            self._validate_trigger(trigger_def)

            # Store trigger
            self.triggers[trigger_def.id] = trigger_def

            # Save to file
            self._save_triggers()

            logger.info(f"Registered trigger: {trigger_def.id} ({trigger_def.name})")
            return True

        except Exception as e:
            logger.error(f"Failed to register trigger {trigger_def.id}: {e}")
            return False

    def unregister_trigger(self, trigger_id: str) -> bool:
        """Unregister a trigger"""
        if trigger_id in self.triggers:
            del self.triggers[trigger_id]
            self._save_triggers()
            logger.info(f"Unregistered trigger: {trigger_id}")
            return True
        return False

    def check_triggers(self) -> List[TriggerEvent]:
        """Check all triggers and return triggered events"""
        triggered_events = []
        current_time = datetime.now(timezone.utc)

        for trigger in self.triggers.values():
            if not trigger.enabled or trigger.status != TriggerStatus.ACTIVE:
                continue

            # Check cooldown
            if (trigger.last_triggered and
                (current_time - trigger.last_triggered).total_seconds() < trigger.cooldown_seconds):
                continue

            try:
                if self._evaluate_trigger(trigger):
                    # Create trigger event
                    event = TriggerEvent(
                        event_id=f"{trigger.id}_{current_time.strftime('%Y%m%d_%H%M%S')}",
                        trigger_id=trigger.id,
                        timestamp=current_time,
                        data={
                            "workflow": trigger.workflow_mapping,
                            "parameters": trigger.parameters,
                            "trigger_type": trigger.trigger_type.value,
                        },
                        metadata={
                            "trigger_name": trigger.name,
                            "conditions_met": True,
                        }
                    )

                    # Update trigger state
                    trigger.last_triggered = current_time
                    trigger.trigger_count += 1
                    trigger.status = TriggerStatus.TRIGGERED

                    # Store event
                    triggered_events.append(event)
                    self.active_events.append(event)

                    logger.info(f"Trigger activated: {trigger.id} -> {trigger.workflow_mapping}")

            except Exception as e:
                logger.error(f"Error evaluating trigger {trigger.id}: {e}")
                trigger.status = TriggerStatus.ERROR

        # Clean up old events (keep last 100)
        self.active_events = self.active_events[-100:]

        # Save state
        self._save_triggers()

        return triggered_events

    def register_event_handler(self, trigger_type: TriggerType, handler: Callable):
        """Register a custom event handler for a trigger type"""
        self.event_handlers[trigger_type].append(handler)
        logger.info(f"Registered event handler for {trigger_type.value}")

    def get_trigger_stats(self) -> Dict[str, Any]:
        """Get trigger statistics"""
        stats = {
            "total_triggers": len(self.triggers),
            "active_triggers": len([t for t in self.triggers.values() if t.enabled]),
            "triggered_today": len([
                t for t in self.triggers.values()
                if t.last_triggered and t.last_triggered.date() == datetime.now(timezone.utc).date()
            ]),
            "by_type": {},
            "recent_events": len(self.active_events),
        }

        # Group by type
        for trigger_type in TriggerType:
            stats["by_type"][trigger_type.value] = len([
                t for t in self.triggers.values() if t.trigger_type == trigger_type
            ])

        return stats

    def create_script_ohio_triggers(self) -> bool:
        """Create default ScriptOhio autonomous triggers"""
        default_triggers = [
            # Weekly analysis trigger
            TriggerDefinition(
                id="weekly_analysis_wednesday",
                name="Weekly Analysis - Wednesday Morning",
                trigger_type=TriggerType.SCHEDULE,
                config={
                    "schedule": "0 9 * * 3",  # Wednesday 9 AM
                    "timezone": "UTC",
                },
                workflow_mapping="weekly_analysis",
                parameters={
                    "auto_discover_week": True,
                    "enhanced_features": True,
                },
                cooldown_seconds=86400,  # Once per day
            ),

            # Model training trigger
            TriggerDefinition(
                id="model_training_monthly",
                name="Model Training - Monthly Review",
                trigger_type=TriggerType.SCHEDULE,
                config={
                    "schedule": "0 2 1 * *",  # First of month at 2 AM
                    "timezone": "UTC",
                },
                workflow_mapping="model_training",
                parameters={
                    "auto_optimize": True,
                    "validate_performance": True,
                },
                cooldown_seconds=2592000,  # Once per month
            ),

            # Performance degradation trigger
            TriggerDefinition(
                id="performance_degradation",
                name="Performance Degradation Alert",
                trigger_type=TriggerType.PERFORMANCE,
                config={
                    "metric": "prediction_accuracy",
                    "threshold": 0.05,  # 5% drop
                    "evaluation_window": 7,  # Last 7 days
                },
                workflow_mapping="model_training",
                parameters={
                    "reason": "performance_degradation",
                    "urgent": True,
                },
                cooldown_seconds=604800,  # Once per week
            ),

            # New data availability trigger
            TriggerDefinition(
                id="new_cfbd_data",
                name="New CFBD Data Available",
                trigger_type=TriggerType.DATA_THRESHOLD,
                config={
                    "data_source": "cfbd_api",
                    "check_endpoint": "/games",
                    "min_new_records": 10,
                },
                workflow_mapping="weekly_analysis",
                parameters={
                    "data_source": "cfbd",
                    "auto_process": True,
                },
                cooldown_seconds=3600,  # Once per hour
            ),

            # Game day predictions trigger
            TriggerDefinition(
                id="gameday_predictions",
                name="Game Day Predictions",
                trigger_type=TriggerType.SCHEDULE,
                config={
                    "schedule": "0 8,12,16,20 * * 0,1,6",  # Game days (Sat, Sun, Fri)
                    "timezone": "UTC",
                },
                workflow_mapping="gameday_predictions",
                parameters={
                    "update_existing": True,
                    "check_line_movements": True,
                },
                cooldown_seconds=10800,  # Every 3 hours on game days
            ),

            # Resource usage alert trigger
            TriggerDefinition(
                id="high_resource_usage",
                name="High Resource Usage Alert",
                trigger_type=TriggerType.PERFORMANCE,
                config={
                    "metric": "resource_usage",
                    "cpu_threshold": 90,
                    "memory_threshold": 90,
                    "duration_minutes": 10,
                },
                workflow_mapping="resource_optimization",
                parameters={
                    "cleanup_cache": True,
                    "optimize_tasks": True,
                },
                cooldown_seconds=1800,  # Every 30 minutes
            ),

            # Weekly system health check
            TriggerDefinition(
                id="weekly_health_check",
                name="Weekly System Health Check",
                trigger_type=TriggerType.SCHEDULE,
                config={
                    "schedule": "0 6 * * 1",  # Monday 6 AM
                    "timezone": "UTC",
                },
                workflow_mapping="system_maintenance",
                parameters={
                    "full_check": True,
                    "generate_report": True,
                },
                cooldown_seconds=604800,  # Once per week
            ),
        ]

        success_count = 0
        for trigger in default_triggers:
            if self.register_trigger(trigger):
                success_count += 1

        logger.info(f"Created {success_count}/{len(default_triggers)} default ScriptOhio triggers")
        return success_count == len(default_triggers)

    def _validate_trigger(self, trigger: TriggerDefinition):
        """Validate trigger definition"""
        if not trigger.id or not trigger.name:
            raise ValueError("Trigger must have ID and name")

        if not trigger.workflow_mapping:
            raise ValueError("Trigger must specify workflow mapping")

        # Validate trigger type specific config
        if trigger.trigger_type == TriggerType.SCHEDULE:
            if "schedule" not in trigger.config:
                raise ValueError("Schedule trigger must have schedule config")

        elif trigger.trigger_type == TriggerType.PERFORMANCE:
            if "metric" not in trigger.config:
                raise ValueError("Performance trigger must specify metric")

        elif trigger.trigger_type == TriggerType.DATA_THRESHOLD:
            if "data_source" not in trigger.config:
                raise ValueError("Data threshold trigger must specify data source")

    def _evaluate_trigger(self, trigger: TriggerDefinition) -> bool:
        """Evaluate if trigger conditions are met"""
        # Check trigger type specific conditions
        if trigger.trigger_type == TriggerType.SCHEDULE:
            return self._evaluate_schedule_trigger(trigger)
        elif trigger.trigger_type == TriggerType.EVENT:
            return self._evaluate_event_trigger(trigger)
        elif trigger.trigger_type == TriggerType.PERFORMANCE:
            return self._evaluate_performance_trigger(trigger)
        elif trigger.trigger_type == TriggerType.DATA_THRESHOLD:
            return self._evaluate_data_threshold_trigger(trigger)
        elif trigger.trigger_type == TriggerType.EXTERNAL_WEBHOOK:
            return self._evaluate_webhook_trigger(trigger)
        elif trigger.trigger_type == TriggerType.CUSTOM:
            return self._evaluate_custom_trigger(trigger)

        return False

    def _evaluate_schedule_trigger(self, trigger: TriggerDefinition) -> bool:
        """Evaluate schedule-based trigger"""
        schedule = trigger.config.get("schedule", "")
        if not schedule:
            return False

        try:
            from croniter import croniter
            current_time = datetime.now(timezone.utc)

            # Parse cron schedule
            base_time = trigger.last_triggered or trigger.created_at
            cron = croniter(schedule, base_time)

            # Check if next execution time has passed
            next_time = cron.get_next(datetime)
            return current_time >= next_time

        except ImportError:
            # Fallback to simple schedule parsing
            logger.warning("croniter not available, using simple schedule evaluation")
            return self._simple_schedule_evaluation(trigger)
        except Exception as e:
            logger.error(f"Error evaluating schedule trigger {trigger.id}: {e}")
            return False

    def _simple_schedule_evaluation(self, trigger: TriggerDefinition) -> bool:
        """Simple schedule evaluation without croniter"""
        schedule = trigger.config.get("schedule", "")
        current_time = datetime.now(timezone.utc)

        # Basic daily/weekly patterns
        if "daily" in schedule.lower():
            last_trigger = trigger.last_triggered or trigger.created_at
            return (current_time - last_trigger).days >= 1

        elif "weekly" in schedule.lower():
            last_trigger = trigger.last_triggered or trigger.created_at
            return (current_time - last_trigger).days >= 7

        elif "monthly" in schedule.lower():
            last_trigger = trigger.last_triggered or trigger.created_at
            return (current_time - last_trigger).days >= 30

        return False

    def _evaluate_event_trigger(self, trigger: TriggerDefinition) -> bool:
        """Evaluate event-based trigger"""
        event_type = trigger.config.get("event_type", "")

        # This would integrate with event monitoring systems
        # For now, check recent events
        for event in self.active_events[-10:]:  # Check last 10 events
            if event.data.get("event_type") == event_type:
                return True

        return False

    def _evaluate_performance_trigger(self, trigger: TriggerDefinition) -> bool:
        """Evaluate performance-based trigger"""
        metric = trigger.config.get("metric", "")
        threshold = trigger.config.get("threshold", 0)
        window = trigger.config.get("evaluation_window", 7)  # days

        # This would integrate with performance monitoring
        # For now, simulate with basic checks
        if metric == "prediction_accuracy":
            # Check if accuracy has dropped by threshold
            return False  # Placeholder

        elif metric == "resource_usage":
            try:
                import psutil
                cpu_threshold = trigger.config.get("cpu_threshold", 90)
                memory_threshold = trigger.config.get("memory_threshold", 90)

                cpu_usage = psutil.cpu_percent(interval=1)
                memory_usage = psutil.virtual_memory().percent

                return cpu_usage > cpu_threshold or memory_usage > memory_threshold

            except ImportError:
                return False

        return False

    def _evaluate_data_threshold_trigger(self, trigger: TriggerDefinition) -> bool:
        """Evaluate data threshold trigger"""
        data_source = trigger.config.get("data_source", "")
        min_records = trigger.config.get("min_new_records", 10)

        if data_source == "cfbd_api":
            # Check CFBD API for new data
            return self._check_cfbd_data_availability(min_records)

        elif data_source == "file_system":
            # Check file system for new files
            return self._check_file_system_changes(trigger)

        return False

    def _check_cfbd_data_availability(self, min_records: int) -> bool:
        """Check CFBD API for new data availability"""
        try:
            from src.cfbd_client.unified_client import UnifiedCFBDClient
            client = UnifiedCFBDClient()

            # Get recent games to check for new data
            current_time = datetime.now(timezone.utc)
            week_ago = current_time - timedelta(days=7)

            # This is a simplified check - would need proper implementation
            # For now, return False (no new data detected)
            return False

        except Exception as e:
            logger.error(f"Error checking CFBD data availability: {e}")
            return False

    def _check_file_system_changes(self, trigger: TriggerDefinition) -> bool:
        """Check file system for new files"""
        watch_path = trigger.config.get("watch_path", "")
        if not watch_path or not Path(watch_path).exists():
            return False

        try:
            path = Path(watch_path)
            last_check = trigger.last_triggered or trigger.created_at

            # Check for files modified since last check
            new_files = []
            for file_path in path.rglob("*"):
                if file_path.is_file():
                    mod_time = datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc)
                    if mod_time > last_check:
                        new_files.append(file_path)

            min_files = trigger.config.get("min_new_files", 1)
            return len(new_files) >= min_files

        except Exception as e:
            logger.error(f"Error checking file system changes: {e}")
            return False

    def _evaluate_webhook_trigger(self, trigger: TriggerDefinition) -> bool:
        """Evaluate external webhook trigger"""
        # This would check for webhook calls
        # For now, return False
        return False

    def _evaluate_custom_trigger(self, trigger: TriggerDefinition) -> bool:
        """Evaluate custom trigger using registered handlers"""
        handlers = self.event_handlers[TriggerType.CUSTOM]
        for handler in handlers:
            try:
                if handler(trigger):
                    return True
            except Exception as e:
                logger.error(f"Error in custom trigger handler: {e}")

        return False

    def _load_triggers(self):
        """Load triggers from file"""
        try:
            if self.registry_path.exists():
                with open(self.registry_path, "r") as f:
                    data = json.load(f)

                for trigger_data in data.get("triggers", []):
                    # Reconstruct trigger objects
                    trigger = TriggerDefinition(**trigger_data)
                    self.triggers[trigger.id] = trigger

                logger.info(f"Loaded {len(self.triggers)} triggers from file")

        except Exception as e:
            logger.error(f"Error loading triggers from file: {e}")

    def _save_triggers(self):
        """Save triggers to file"""
        try:
            data = {
                "triggers": [
                    {
                        "id": t.id,
                        "name": t.name,
                        "trigger_type": t.trigger_type.value,
                        "config": t.config,
                        "workflow_mapping": t.workflow_mapping,
                        "enabled": t.enabled,
                        "conditions": t.conditions,
                        "parameters": t.parameters,
                        "cooldown_seconds": t.cooldown_seconds,
                        "last_triggered": t.last_triggered.isoformat() if t.last_triggered else None,
                        "trigger_count": t.trigger_count,
                        "status": t.status.value,
                        "created_at": t.created_at.isoformat(),
                        "metadata": t.metadata,
                    }
                    for t in self.triggers.values()
                ],
                "last_updated": datetime.now(timezone.utc).isoformat(),
            }

            with open(self.registry_path, "w") as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            logger.error(f"Error saving triggers to file: {e}")


# Global trigger registry instance
trigger_registry = TriggerRegistry()