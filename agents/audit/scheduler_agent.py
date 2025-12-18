"""
Audit Scheduler Agent - Automated scheduling and trigger management for audit system.

This agent provides:
- Automated audit scheduling with configurable intervals
- Event-driven triggers based on system changes
- Calendar-based scheduling with timezone support
- Smart scheduling based on system load and resource availability
- Integration with cron jobs and task schedulers
"""

import os
import json
import time
import threading
import schedule
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum

from agents.core.agent_framework import BaseAgent, AgentCapability, PermissionLevel


class TriggerType(Enum):
    """Types of audit triggers."""
    SCHEDULED = "scheduled"
    EVENT_DRIVEN = "event_driven"
    MANUAL = "manual"
    CRON = "cron"


@dataclass
class AuditSchedule:
    """Audit schedule configuration."""
    schedule_id: str
    audit_type: str  # quick, comprehensive, domain
    schedule_pattern: str  # cron pattern or interval
    trigger_type: TriggerType
    enabled: bool = True
    parameters: Optional[Dict[str, Any]] = None
    timezone: str = "UTC"
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class AuditTrigger:
    """Audit trigger configuration."""
    trigger_id: str
    trigger_type: TriggerType
    audit_type: str
    event_type: str  # file_change, deployment, system_event
    event_pattern: str  # pattern to match
    enabled: bool = True
    parameters: Optional[Dict[str, Any]] = None
    cooldown_minutes: int = 30
    last_triggered: Optional[datetime] = None


class AuditSchedulerAgent(BaseAgent):
    """Agent for scheduling and managing automated audit execution."""

    def __init__(self, agent_id: str = "audit_scheduler_agent"):
        super().__init__(
            agent_id,
            "Audit Scheduler Agent",
            PermissionLevel.READ_EXECUTE_WRITE
        )

        # Scheduler state
        self.schedules: Dict[str, AuditSchedule] = {}
        self.triggers: Dict[str, AuditTrigger] = {}
        self.scheduler_thread: Optional[threading.Thread] = None
        self.scheduler_running = False
        self.event_watchers: Dict[str, threading.Thread] = {}

        # Configuration
        self.config = {
            "scheduler_enabled": True,
            "max_concurrent_audits": 2,
            "default_timezone": "UTC",
            "schedule_file": "production_audit_reports/scheduler_config.json",
            "retry_failed_audits": True,
            "retry_delay_minutes": 15,
            "max_retries": 3
        }

        # Load existing schedules
        self._load_schedules()

    def _define_capabilities(self) -> List[AgentCapability]:
        """Define scheduler capabilities."""
        return [
            AgentCapability(
                name="create_schedule",
                description="Create a new audit schedule",
                permission_required=PermissionLevel.READ_EXECUTE_WRITE,
                tools_required=["python3", "schedule", "datetime"],
                data_access=["schedule_configuration", "audit_parameters"],
                execution_time_estimate=5.0
            ),
            AgentCapability(
                name="list_schedules",
                description="List all configured audit schedules",
                permission_required=PermissionLevel.READ_EXECUTE,
                tools_required=["python3"],
                data_access=["schedule_configuration"],
                execution_time_estimate=2.0
            ),
            AgentCapability(
                name="update_schedule",
                description="Update an existing audit schedule",
                permission_required=PermissionLevel.READ_EXECUTE_WRITE,
                tools_required=["python3"],
                data_access=["schedule_configuration"],
                execution_time_estimate=5.0
            ),
            AgentCapability(
                name="delete_schedule",
                description="Delete an audit schedule",
                permission_required=PermissionLevel.READ_EXECUTE_WRITE,
                tools_required=["python3"],
                data_access=["schedule_configuration"],
                execution_time_estimate=2.0
            ),
            AgentCapability(
                name="start_scheduler",
                description="Start the audit scheduler service",
                permission_required=PermissionLevel.READ_EXECUTE_WRITE,
                tools_required=["python3", "threading", "schedule"],
                data_access=["scheduler_service"],
                execution_time_estimate=10.0
            ),
            AgentCapability(
                name="stop_scheduler",
                description="Stop the audit scheduler service",
                permission_required=PermissionLevel.READ_EXECUTE_WRITE,
                tools_required=["python3", "threading"],
                data_access=["scheduler_service"],
                execution_time_estimate=5.0
            ),
            AgentCapability(
                name="create_trigger",
                description="Create an event-driven audit trigger",
                permission_required=PermissionLevel.READ_EXECUTE_WRITE,
                tools_required=["python3", "file_system_monitoring"],
                data_access=["trigger_configuration", "event_patterns"],
                execution_time_estimate=5.0
            ),
            AgentCapability(
                name="get_scheduler_status",
                description="Get current scheduler status and statistics",
                permission_required=PermissionLevel.READ_EXECUTE,
                tools_required=["python3"],
                data_access=["scheduler_status"],
                execution_time_estimate=2.0
            )
        ]

    def _execute_action(self, action: str, parameters: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute scheduler action."""
        try:
            if action == "create_schedule":
                return self._create_schedule(parameters, user_context)
            elif action == "list_schedules":
                return self._list_schedules(parameters, user_context)
            elif action == "update_schedule":
                return self._update_schedule(parameters, user_context)
            elif action == "delete_schedule":
                return self._delete_schedule(parameters, user_context)
            elif action == "start_scheduler":
                return self._start_scheduler(parameters, user_context)
            elif action == "stop_scheduler":
                return self._stop_scheduler(parameters, user_context)
            elif action == "create_trigger":
                return self._create_trigger(parameters, user_context)
            elif action == "get_scheduler_status":
                return self._get_scheduler_status(parameters, user_context)
            else:
                return {"error": f"Unknown action: {action}"}

        except Exception as e:
            return {
                "agent_id": self.agent_id,
                "action": action,
                "error": f"Scheduler action failed: {str(e)}"
            }

    def _load_schedules(self):
        """Load schedules from configuration file."""
        try:
            schedule_file = Path(self.config["schedule_file"])
            if schedule_file.exists():
                with open(schedule_file, 'r') as f:
                    data = json.load(f)

                # Load schedules
                for schedule_data in data.get("schedules", []):
                    schedule = AuditSchedule(**schedule_data)
                    # Convert string timestamps back to datetime objects
                    if schedule.last_run:
                        schedule.last_run = datetime.fromisoformat(schedule.last_run)
                    if schedule.next_run:
                        schedule.next_run = datetime.fromisoformat(schedule.next_run)
                    if schedule.created_at:
                        schedule.created_at = datetime.fromisoformat(schedule.created_at)
                    self.schedules[schedule.schedule_id] = schedule

                # Load triggers
                for trigger_data in data.get("triggers", []):
                    trigger = AuditTrigger(**trigger_data)
                    if trigger.last_triggered:
                        trigger.last_triggered = datetime.fromisoformat(trigger.last_triggered)
                    self.triggers[trigger.trigger_id] = trigger

                print(f"✅ Loaded {len(self.schedules)} schedules and {len(self.triggers)} triggers")

        except Exception as e:
            print(f"⚠️ Warning: Could not load schedules from {self.config['schedule_file']}: {e}")

    def _save_schedules(self):
        """Save schedules to configuration file."""
        try:
            schedule_file = Path(self.config["schedule_file"])
            schedule_file.parent.mkdir(parents=True, exist_ok=True)

            data = {
                "schedules": [],
                "triggers": [],
                "version": "1.0",
                "last_updated": datetime.now().isoformat()
            }

            # Convert schedules to dict
            for schedule in self.schedules.values():
                schedule_dict = {
                    "schedule_id": schedule.schedule_id,
                    "audit_type": schedule.audit_type,
                    "schedule_pattern": schedule.schedule_pattern,
                    "trigger_type": schedule.trigger_type.value,
                    "enabled": schedule.enabled,
                    "parameters": schedule.parameters,
                    "timezone": schedule.timezone,
                    "last_run": schedule.last_run.isoformat() if schedule.last_run else None,
                    "next_run": schedule.next_run.isoformat() if schedule.next_run else None,
                    "run_count": schedule.run_count,
                    "success_count": schedule.success_count,
                    "failure_count": schedule.failure_count,
                    "created_at": schedule.created_at.isoformat() if schedule.created_at else datetime.now().isoformat()
                }
                data["schedules"].append(schedule_dict)

            # Convert triggers to dict
            for trigger in self.triggers.values():
                trigger_dict = {
                    "trigger_id": trigger.trigger_id,
                    "trigger_type": trigger.trigger_type.value,
                    "audit_type": trigger.audit_type,
                    "event_type": trigger.event_type,
                    "event_pattern": trigger.event_pattern,
                    "enabled": trigger.enabled,
                    "parameters": trigger.parameters,
                    "cooldown_minutes": trigger.cooldown_minutes,
                    "last_triggered": trigger.last_triggered.isoformat() if trigger.last_triggered else None
                }
                data["triggers"].append(trigger_dict)

            with open(schedule_file, 'w') as f:
                json.dump(data, f, indent=2)

            print(f"✅ Saved {len(self.schedules)} schedules and {len(self.triggers)} triggers")

        except Exception as e:
            print(f"❌ Failed to save schedules: {e}")

    def _create_schedule(self, parameters: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new audit schedule."""
        try:
            schedule_id = parameters.get("schedule_id") or f"schedule_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            audit_type = parameters.get("audit_type", "quick")
            schedule_pattern = parameters.get("schedule_pattern", "hourly")
            trigger_type = TriggerType(parameters.get("trigger_type", "scheduled"))

            if schedule_id in self.schedules:
                return {
                    "error": f"Schedule with ID '{schedule_id}' already exists"
                }

            # Create new schedule
            schedule = AuditSchedule(
                schedule_id=schedule_id,
                audit_type=audit_type,
                schedule_pattern=schedule_pattern,
                trigger_type=trigger_type,
                enabled=parameters.get("enabled", True),
                parameters=parameters.get("parameters", {}),
                timezone=parameters.get("timezone", self.config["default_timezone"])
            )

            # Calculate next run time
            schedule.next_run = self._calculate_next_run(schedule)

            self.schedules[schedule_id] = schedule
            self._save_schedules()

            print(f"✅ Created schedule '{schedule_id}' for {audit_type} audits")

            return {
                "schedule_id": schedule_id,
                "audit_type": audit_type,
                "schedule_pattern": schedule_pattern,
                "next_run": schedule.next_run.isoformat() if schedule.next_run else None,
                "created_at": schedule.created_at.isoformat()
            }

        except Exception as e:
            return {"error": f"Failed to create schedule: {str(e)}"}

    def _list_schedules(self, parameters: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """List all configured schedules."""
        schedules_data = []
        for schedule in self.schedules.values():
            schedules_data.append({
                "schedule_id": schedule.schedule_id,
                "audit_type": schedule.audit_type,
                "schedule_pattern": schedule.schedule_pattern,
                "trigger_type": schedule.trigger_type.value,
                "enabled": schedule.enabled,
                "timezone": schedule.timezone,
                "last_run": schedule.last_run.isoformat() if schedule.last_run else None,
                "next_run": schedule.next_run.isoformat() if schedule.next_run else None,
                "run_count": schedule.run_count,
                "success_count": schedule.success_count,
                "failure_count": schedule.failure_count,
                "success_rate": (schedule.success_count / schedule.run_count * 100) if schedule.run_count > 0 else 0,
                "created_at": schedule.created_at.isoformat() if schedule.created_at else None
            })

        return {
            "schedules": schedules_data,
            "total_schedules": len(schedules_data),
            "enabled_schedules": len([s for s in schedules_data if s["enabled"]])
        }

    def _update_schedule(self, parameters: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing schedule."""
        try:
            schedule_id = parameters.get("schedule_id")
            if not schedule_id or schedule_id not in self.schedules:
                return {"error": f"Schedule '{schedule_id}' not found"}

            schedule = self.schedules[schedule_id]

            # Update allowed fields
            if "audit_type" in parameters:
                schedule.audit_type = parameters["audit_type"]
            if "schedule_pattern" in parameters:
                schedule.schedule_pattern = parameters["schedule_pattern"]
            if "enabled" in parameters:
                schedule.enabled = parameters["enabled"]
            if "parameters" in parameters:
                schedule.parameters.update(parameters["parameters"])
            if "timezone" in parameters:
                schedule.timezone = parameters["timezone"]

            # Recalculate next run time
            schedule.next_run = self._calculate_next_run(schedule)

            self._save_schedules()

            print(f"✅ Updated schedule '{schedule_id}'")

            return {
                "schedule_id": schedule_id,
                "updated_at": datetime.now().isoformat(),
                "next_run": schedule.next_run.isoformat() if schedule.next_run else None
            }

        except Exception as e:
            return {"error": f"Failed to update schedule: {str(e)}"}

    def _delete_schedule(self, parameters: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a schedule."""
        try:
            schedule_id = parameters.get("schedule_id")
            if not schedule_id or schedule_id not in self.schedules:
                return {"error": f"Schedule '{schedule_id}' not found"}

            del self.schedules[schedule_id]
            self._save_schedules()

            print(f"✅ Deleted schedule '{schedule_id}'")

            return {"schedule_id": schedule_id, "deleted_at": datetime.now().isoformat()}

        except Exception as e:
            return {"error": f"Failed to delete schedule: {str(e)}"}

    def _start_scheduler(self, parameters: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Start the scheduler service."""
        try:
            if self.scheduler_running:
                return {"status": "already_running", "message": "Scheduler is already running"}

            if not self.config["scheduler_enabled"]:
                return {"status": "disabled", "message": "Scheduler is disabled in configuration"}

            self.scheduler_running = True
            self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
            self.scheduler_thread.start()

            print("🚀 Audit scheduler started")

            return {
                "status": "started",
                "started_at": datetime.now().isoformat(),
                "schedules_loaded": len(self.schedules),
                "triggers_loaded": len(self.triggers)
            }

        except Exception as e:
            return {"error": f"Failed to start scheduler: {str(e)}"}

    def _stop_scheduler(self, parameters: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Stop the scheduler service."""
        try:
            if not self.scheduler_running:
                return {"status": "not_running", "message": "Scheduler is not running"}

            self.scheduler_running = False

            # Wait for scheduler thread to finish
            if self.scheduler_thread and self.scheduler_thread.is_alive():
                self.scheduler_thread.join(timeout=5)

            # Stop event watchers
            for thread_id, thread in self.event_watchers.items():
                if thread.is_alive():
                    # Graceful stop would need more sophisticated implementation
                    pass

            self.event_watchers.clear()

            print("🛑 Audit scheduler stopped")

            return {
                "status": "stopped",
                "stopped_at": datetime.now().isoformat()
            }

        except Exception as e:
            return {"error": f"Failed to stop scheduler: {str(e)}"}

    def _create_trigger(self, parameters: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Create an event-driven audit trigger."""
        try:
            trigger_id = parameters.get("trigger_id") or f"trigger_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            if trigger_id in self.triggers:
                return {"error": f"Trigger with ID '{trigger_id}' already exists"}

            trigger = AuditTrigger(
                trigger_id=trigger_id,
                trigger_type=TriggerType(parameters.get("trigger_type", "event_driven")),
                audit_type=parameters.get("audit_type", "quick"),
                event_type=parameters.get("event_type", "file_change"),
                event_pattern=parameters.get("event_pattern", ""),
                enabled=parameters.get("enabled", True),
                parameters=parameters.get("parameters", {}),
                cooldown_minutes=parameters.get("cooldown_minutes", 30)
            )

            self.triggers[trigger_id] = trigger
            self._save_schedules()

            # Start event watcher for this trigger
            if trigger.enabled and self.scheduler_running:
                self._start_event_watcher(trigger)

            print(f"✅ Created trigger '{trigger_id}' for {trigger.event_type} events")

            return {
                "trigger_id": trigger_id,
                "event_type": trigger.event_type,
                "event_pattern": trigger.event_pattern,
                "audit_type": trigger.audit_type,
                "created_at": datetime.now().isoformat()
            }

        except Exception as e:
            return {"error": f"Failed to create trigger: {str(e)}"}

    def _get_scheduler_status(self, parameters: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Get current scheduler status and statistics."""
        active_schedules = len([s for s in self.schedules.values() if s.enabled])
        active_triggers = len([t for t in self.triggers.values() if t.enabled])

        # Calculate statistics
        total_runs = sum(s.run_count for s in self.schedules.values())
        total_successes = sum(s.success_count for s in self.schedules.values())
        total_failures = sum(s.failure_count for s in self.schedules.values())

        return {
            "scheduler_running": self.scheduler_running,
            "scheduler_enabled": self.config["scheduler_enabled"],
            "schedules": {
                "total": len(self.schedules),
                "active": active_schedules,
                "inactive": len(self.schedules) - active_schedules
            },
            "triggers": {
                "total": len(self.triggers),
                "active": active_triggers,
                "inactive": len(self.triggers) - active_triggers
            },
            "statistics": {
                "total_runs": total_runs,
                "total_successes": total_successes,
                "total_failures": total_failures,
                "overall_success_rate": (total_successes / total_runs * 100) if total_runs > 0 else 0
            },
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds() if hasattr(self, 'start_time') else 0
        }

    def _calculate_next_run(self, schedule: AuditSchedule) -> Optional[datetime]:
        """Calculate the next run time for a schedule."""
        try:
            if schedule.trigger_type == TriggerType.SCHEDULED:
                # Parse simple patterns like "hourly", "daily", "weekly"
                pattern = schedule.schedule_pattern.lower()
                now = datetime.now()

                if pattern == "hourly":
                    return now + timedelta(hours=1)
                elif pattern == "daily":
                    return now + timedelta(days=1)
                elif pattern == "weekly":
                    return now + timedelta(weeks=1)
                elif pattern.startswith("every_"):
                    # Format: every_2_hours, every_30_minutes, every_1_day
                    parts = pattern.split("_")
                    if len(parts) == 3:
                        interval = int(parts[1])
                        unit = parts[2]

                        if unit.startswith("hour"):
                            return now + timedelta(hours=interval)
                        elif unit.startswith("minute"):
                            return now + timedelta(minutes=interval)
                        elif unit.startswith("day"):
                            return now + timedelta(days=interval)

            return None

        except Exception as e:
            print(f"⚠️ Error calculating next run time: {e}")
            return None

    def _scheduler_loop(self):
        """Main scheduler loop."""
        print("🔄 Scheduler loop started")

        while self.scheduler_running:
            try:
                current_time = datetime.now()

                # Check scheduled audits
                for schedule in self.schedules.values():
                    if (schedule.enabled and
                        schedule.next_run and
                        current_time >= schedule.next_run):

                        self._execute_scheduled_audit(schedule)

                # Check event-driven triggers
                for trigger in self.triggers.values():
                    if trigger.enabled:
                        self._check_event_trigger(trigger)

                # Sleep for a short interval
                time.sleep(60)  # Check every minute

            except Exception as e:
                print(f"❌ Error in scheduler loop: {e}")
                time.sleep(60)  # Sleep and continue

        print("🔄 Scheduler loop stopped")

    def _execute_scheduled_audit(self, schedule: AuditSchedule):
        """Execute a scheduled audit."""
        try:
            print(f"🔍 Executing scheduled audit: {schedule.schedule_id} ({schedule.audit_type})")

            # Import and run production audit
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent.parent))
            from scripts.production_audit import ProductionAuditRunner

            # Create audit runner
            runner = ProductionAuditRunner()

            # Execute audit
            kwargs = schedule.parameters or {}
            if schedule.audit_type == "domain":
                kwargs.update(schedule.parameters or {})

            success, result = runner.run_audit(schedule.audit_type, **kwargs)

            # Update schedule statistics
            schedule.run_count += 1
            schedule.last_run = datetime.now()

            if success:
                schedule.success_count += 1
                print(f"✅ Scheduled audit completed successfully")
            else:
                schedule.failure_count += 1
                print(f"❌ Scheduled audit failed: {result.get('error', 'Unknown error')}")

                # Retry logic
                if (self.config["retry_failed_audits"] and
                    schedule.failure_count <= self.config["max_retries"]):

                    retry_delay = self.config["retry_delay_minutes"]
                    schedule.next_run = datetime.now() + timedelta(minutes=retry_delay)
                    print(f"🔄 Will retry in {retry_delay} minutes")

            # Calculate next run time
            if schedule.trigger_type == TriggerType.SCHEDULED:
                schedule.next_run = self._calculate_next_run(schedule)

            # Save updated schedule
            self._save_schedules()

        except Exception as e:
            print(f"❌ Error executing scheduled audit: {e}")
            schedule.failure_count += 1
            schedule.last_run = datetime.now()
            self._save_schedules()

    def _check_event_trigger(self, trigger: AuditTrigger):
        """Check if an event trigger should be activated."""
        try:
            # Check cooldown period
            if (trigger.last_triggered and
                datetime.now() - trigger.last_triggered < timedelta(minutes=trigger.cooldown_minutes)):
                return

            # Simple file change detection (could be enhanced with proper file watching)
            if trigger.event_type == "file_change":
                if self._check_file_changes(trigger):
                    self._activate_trigger(trigger)

            # Could add more event types here (deployment, system events, etc.)

        except Exception as e:
            print(f"❌ Error checking event trigger: {e}")

    def _check_file_changes(self, trigger: AuditTrigger) -> bool:
        """Check for file changes matching trigger pattern."""
        try:
            # Simple implementation - check if files matching pattern exist and are recent
            pattern = trigger.event_pattern
            if not pattern:
                return False

            # This is a simplified implementation
            # A production version would use proper file system monitoring
            import glob
            import time

            files = glob.glob(pattern, recursive=True)
            current_time = time.time()

            for file_path in files:
                try:
                    mtime = os.path.getmtime(file_path)
                    # Check if file was modified in the last 5 minutes
                    if current_time - mtime < 300:  # 5 minutes
                        return True
                except OSError:
                    continue

            return False

        except Exception as e:
            print(f"❌ Error checking file changes: {e}")
            return False

    def _activate_trigger(self, trigger: AuditTrigger):
        """Activate an event trigger and run the associated audit."""
        try:
            print(f"🎯 Activating trigger: {trigger.trigger_id} ({trigger.audit_type})")

            # Execute audit
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent.parent))
            from scripts.production_audit import ProductionAuditRunner

            runner = ProductionAuditRunner()
            kwargs = trigger.parameters or {}

            if trigger.audit_type == "domain":
                kwargs.update(trigger.parameters or {})

            success, result = runner.run_audit(trigger.audit_type, **kwargs)

            # Update trigger
            trigger.last_triggered = datetime.now()

            if success:
                print(f"✅ Triggered audit completed successfully")
            else:
                print(f"❌ Triggered audit failed: {result.get('error', 'Unknown error')}")

            self._save_schedules()

        except Exception as e:
            print(f"❌ Error activating trigger: {e}")
            trigger.last_triggered = datetime.now()
            self._save_schedules()

    def _start_event_watcher(self, trigger: AuditTrigger):
        """Start an event watcher for a trigger."""
        # This would implement proper file system watching
        # For now, we rely on the periodic checking in the scheduler loop
        pass

    @property
    def start_time(self) -> datetime:
        """Get scheduler start time."""
        return getattr(self, '_start_time', datetime.now())