"""
Alerting Agent - Multi-channel alerting system for audit results and system monitoring.

This agent provides:
- Multi-channel alerting (console, file, email, Slack, webhook)
- Intelligent alert deduplication and rate limiting
- Customizable alert thresholds and escalation rules
- Alert templates and formatting
- Historical alert tracking and analytics
"""

import os
import json
import time
import smtplib
import requests
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart

from agents.core.agent_framework import BaseAgent, AgentCapability, PermissionLevel


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertChannel(Enum):
    """Available alert channels."""
    CONSOLE = "console"
    FILE = "file"
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"


@dataclass
class AlertRule:
    """Alert rule configuration."""
    rule_id: str
    name: str
    description: str
    severity: AlertSeverity
    channels: List[AlertChannel]
    threshold_conditions: Dict[str, Any]
    enabled: bool = True
    cooldown_minutes: int = 15
    template: Optional[str] = None
    escalation_rules: Optional[Dict[str, Any]] = None
    created_at: datetime = None
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class AlertMessage:
    """Alert message structure."""
    alert_id: str
    rule_id: str
    severity: AlertSeverity
    title: str
    message: str
    context: Dict[str, Any]
    timestamp: datetime
    channels: List[AlertChannel]
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None

    def __post_init__(self):
        if isinstance(self.timestamp, str):
            self.timestamp = datetime.fromisoformat(self.timestamp)


class AlertingAgent(BaseAgent):
    """Multi-channel alerting agent for audit system."""

    def __init__(self, agent_id: str = "alerting_agent"):
        super().__init__(
            agent_id,
            "Alerting Agent",
            PermissionLevel.READ_EXECUTE_WRITE
        )

        # Alert management
        self.alert_rules: Dict[str, AlertRule] = {}
        self.alert_history: List[AlertMessage] = []
        self.alert_queue: List[AlertMessage] = []
        self.alert_senders: Dict[AlertChannel, Callable] = {}

        # Rate limiting and deduplication
        self.recent_alerts: Dict[str, datetime] = {}  # rule_id -> last_sent_time
        self.alert_deduplication_window = 300  # 5 minutes

        # Configuration
        self.config = {
            "alert_file": "logs/audit_production/alerts.log",
            "alert_history_file": "production_audit_reports/alert_history.json",
            "max_history_size": 1000,
            "default_channels": [AlertChannel.CONSOLE, AlertChannel.FILE],
            "rate_limit_enabled": True,
            "deduplication_enabled": True,
            "batch_send_interval": 60,  # seconds
            "email_config": {
                "enabled": False,
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "username": "",
                "password": "",
                "from_address": "",
                "to_addresses": []
            },
            "slack_config": {
                "enabled": False,
                "webhook_url": "",
                "channel": "#alerts",
                "username": "Audit Bot"
            },
            "webhook_config": {
                "enabled": False,
                "url": "",
                "headers": {},
                "timeout": 30
            }
        }

        # Initialize alert senders
        self._initialize_senders()

        # Load configuration and rules
        self._load_configuration()

        # Start background sender thread
        self.sender_thread = threading.Thread(target=self._background_sender, daemon=True)
        self.sender_running = True
        self.sender_thread.start()

    def _define_capabilities(self) -> List[AgentCapability]:
        """Define alerting capabilities."""
        return [
            AgentCapability(
                name="create_alert_rule",
                description="Create a new alert rule",
                permission_required=PermissionLevel.READ_EXECUTE_WRITE,
                tools_required=["python3"],
                data_access=["alert_configuration"],
                execution_time_estimate=5.0
            ),
            AgentCapability(
                name="send_alert",
                description="Send an immediate alert",
                permission_required=PermissionLevel.READ_EXECUTE_WRITE,
                tools_required=["python3", "notification_services"],
                data_access=["alert_services"],
                execution_time_estimate=10.0
            ),
            AgentCapability(
                name="evaluate_audit_alerts",
                description="Evaluate audit results against alert rules",
                permission_required=PermissionLevel.READ_EXECUTE,
                tools_required=["python3"],
                data_access=["audit_results", "alert_rules"],
                execution_time_estimate=15.0
            ),
            AgentCapability(
                name="list_alert_rules",
                description="List all configured alert rules",
                permission_required=PermissionLevel.READ_EXECUTE,
                tools_required=["python3"],
                data_access=["alert_configuration"],
                execution_time_estimate=2.0
            ),
            AgentCapability(
                name="get_alert_history",
                description="Get alert history and statistics",
                permission_required=PermissionLevel.READ_EXECUTE,
                tools_required=["python3"],
                data_access=["alert_history"],
                execution_time_estimate=5.0
            ),
            AgentCapability(
                name="acknowledge_alert",
                description="Acknowledge an alert",
                permission_required=PermissionLevel.READ_EXECUTE_WRITE,
                tools_required=["python3"],
                data_access=["alert_history"],
                execution_time_estimate=2.0
            ),
            AgentCapability(
                name="test_alert_channels",
                description="Test alert channel connectivity",
                permission_required=PermissionLevel.READ_EXECUTE,
                tools_required=["python3", "notification_services"],
                data_access=["alert_channels"],
                execution_time_estimate=20.0
            )
        ]

    def _execute_action(self, action: str, parameters: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute alerting action."""
        try:
            if action == "create_alert_rule":
                return self._create_alert_rule(parameters, user_context)
            elif action == "send_alert":
                return self._send_alert(parameters, user_context)
            elif action == "evaluate_audit_alerts":
                return self._evaluate_audit_alerts(parameters, user_context)
            elif action == "list_alert_rules":
                return self._list_alert_rules(parameters, user_context)
            elif action == "get_alert_history":
                return self._get_alert_history(parameters, user_context)
            elif action == "acknowledge_alert":
                return self._acknowledge_alert(parameters, user_context)
            elif action == "test_alert_channels":
                return self._test_alert_channels(parameters, user_context)
            else:
                return {"error": f"Unknown action: {action}"}

        except Exception as e:
            return {
                "agent_id": self.agent_id,
                "action": action,
                "error": f"Alerting action failed: {str(e)}"
            }

    def _initialize_senders(self):
        """Initialize alert channel senders."""
        self.alert_senders = {
            AlertChannel.CONSOLE: self._send_console_alert,
            AlertChannel.FILE: self._send_file_alert,
            AlertChannel.EMAIL: self._send_email_alert,
            AlertChannel.SLACK: self._send_slack_alert,
            AlertChannel.WEBHOOK: self._send_webhook_alert
        }

    def _load_configuration(self):
        """Load alerting configuration from file."""
        try:
            config_file = Path("config/alerting_config.json")
            if config_file.exists():
                with open(config_file, 'r') as f:
                    file_config = json.load(f)
                    self.config.update(file_config)

            # Load alert rules
            rules_file = Path("production_audit_reports/alert_rules.json")
            if rules_file.exists():
                with open(rules_file, 'r') as f:
                    rules_data = json.load(f)
                    for rule_data in rules_data.get("rules", []):
                        rule = AlertRule(
                            rule_id=rule_data["rule_id"],
                            name=rule_data["name"],
                            description=rule_data["description"],
                            severity=AlertSeverity(rule_data["severity"]),
                            channels=[AlertChannel(ch) for ch in rule_data["channels"]],
                            threshold_conditions=rule_data["threshold_conditions"],
                            enabled=rule_data["enabled"],
                            cooldown_minutes=rule_data["cooldown_minutes"],
                            template=rule_data.get("template"),
                            escalation_rules=rule_data.get("escalation_rules"),
                            created_at=datetime.fromisoformat(rule_data["created_at"]) if rule_data.get("created_at") else datetime.now()
                        )
                        if rule_data.get("last_triggered"):
                            rule.last_triggered = datetime.fromisoformat(rule_data["last_triggered"])
                        rule.trigger_count = rule_data.get("trigger_count", 0)
                        self.alert_rules[rule.rule_id] = rule

            # Load alert history
            history_file = Path(self.config["alert_history_file"])
            if history_file.exists():
                with open(history_file, 'r') as f:
                    history_data = json.load(f)
                    for alert_data in history_data.get("alerts", []):
                        alert = AlertMessage(
                            alert_id=alert_data["alert_id"],
                            rule_id=alert_data["rule_id"],
                            severity=AlertSeverity(alert_data["severity"]),
                            title=alert_data["title"],
                            message=alert_data["message"],
                            context=alert_data["context"],
                            timestamp=datetime.fromisoformat(alert_data["timestamp"]),
                            channels=[AlertChannel(ch) for ch in alert_data["channels"]],
                            acknowledged=alert_data["acknowledged"],
                            acknowledged_by=alert_data.get("acknowledged_by"),
                            acknowledged_at=datetime.fromisoformat(alert_data["acknowledged_at"]) if alert_data.get("acknowledged_at") else None
                        )
                        self.alert_history.append(alert)

            print(f"✅ Loaded {len(self.alert_rules)} alert rules and {len(self.alert_history)} historical alerts")

        except Exception as e:
            print(f"⚠️ Warning: Could not load alerting configuration: {e}")

    def _save_configuration(self):
        """Save alerting configuration to files."""
        try:
            # Save rules
            rules_file = Path("production_audit_reports/alert_rules.json")
            rules_file.parent.mkdir(parents=True, exist_ok=True)

            rules_data = {
                "rules": [],
                "version": "1.0",
                "last_updated": datetime.now().isoformat()
            }

            for rule in self.alert_rules.values():
                rule_dict = asdict(rule)
                rule_dict["severity"] = rule.severity.value
                rule_dict["channels"] = [ch.value for ch in rule.channels]
                if rule.last_triggered:
                    rule_dict["last_triggered"] = rule.last_triggered.isoformat()
                rule_dict["created_at"] = rule.created_at.isoformat()
                rules_data["rules"].append(rule_dict)

            with open(rules_file, 'w') as f:
                json.dump(rules_data, f, indent=2)

            # Save alert history
            history_file = Path(self.config["alert_history_file"])
            history_file.parent.mkdir(parents=True, exist_ok=True)

            history_data = {
                "alerts": [],
                "version": "1.0",
                "last_updated": datetime.now().isoformat()
            }

            # Keep only recent history
            recent_history = self.alert_history[-self.config["max_history_size"]:]
            for alert in recent_history:
                alert_dict = asdict(alert)
                alert_dict["severity"] = alert.severity.value
                alert_dict["channels"] = [ch.value for ch in alert.channels]
                alert_dict["timestamp"] = alert.timestamp.isoformat()
                if alert.acknowledged_at:
                    alert_dict["acknowledged_at"] = alert.acknowledged_at.isoformat()
                history_data["alerts"].append(alert_dict)

            with open(history_file, 'w') as f:
                json.dump(history_data, f, indent=2)

        except Exception as e:
            print(f"❌ Failed to save alerting configuration: {e}")

    def _create_alert_rule(self, parameters: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new alert rule."""
        try:
            rule_id = parameters.get("rule_id") or f"rule_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            if rule_id in self.alert_rules:
                return {"error": f"Alert rule with ID '{rule_id}' already exists"}

            rule = AlertRule(
                rule_id=rule_id,
                name=parameters.get("name", rule_id),
                description=parameters.get("description", ""),
                severity=AlertSeverity(parameters.get("severity", "warning")),
                channels=[AlertChannel(ch) for ch in parameters.get("channels", ["console", "file"])],
                threshold_conditions=parameters.get("threshold_conditions", {}),
                enabled=parameters.get("enabled", True),
                cooldown_minutes=parameters.get("cooldown_minutes", 15),
                template=parameters.get("template"),
                escalation_rules=parameters.get("escalation_rules")
            )

            self.alert_rules[rule_id] = rule
            self._save_configuration()

            print(f"✅ Created alert rule '{rule_id}': {rule.name}")

            return {
                "rule_id": rule_id,
                "name": rule.name,
                "severity": rule.severity.value,
                "channels": [ch.value for ch in rule.channels],
                "created_at": rule.created_at.isoformat()
            }

        except Exception as e:
            return {"error": f"Failed to create alert rule: {str(e)}"}

    def _send_alert(self, parameters: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Send an immediate alert."""
        try:
            alert_id = parameters.get("alert_id") or f"alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            severity = AlertSeverity(parameters.get("severity", "warning"))
            channels = [AlertChannel(ch) for ch in parameters.get("channels", ["console", "file"])]

            alert = AlertMessage(
                alert_id=alert_id,
                rule_id="manual",
                severity=severity,
                title=parameters.get("title", "Manual Alert"),
                message=parameters.get("message", ""),
                context=parameters.get("context", {}),
                timestamp=datetime.now(),
                channels=channels
            )

            # Send alert immediately
            success_count = self._send_alert_message(alert)

            # Add to history
            self.alert_history.append(alert)
            self._save_configuration()

            print(f"✅ Sent manual alert '{alert_id}' to {success_count}/{len(channels)} channels")

            return {
                "alert_id": alert_id,
                "severity": severity.value,
                "channels_sent": success_count,
                "total_channels": len(channels),
                "timestamp": alert.timestamp.isoformat()
            }

        except Exception as e:
            return {"error": f"Failed to send alert: {str(e)}"}

    def _evaluate_audit_alerts(self, parameters: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate audit results against alert rules."""
        try:
            audit_result = parameters.get("audit_result")
            if not audit_result:
                return {"error": "No audit_result provided"}

            alerts_generated = []
            rules_evaluated = 0
            rules_triggered = 0

            for rule in self.alert_rules.values():
                if not rule.enabled:
                    continue

                rules_evaluated += 1

                # Check cooldown period
                if (rule.last_triggered and
                    datetime.now() - rule.last_triggered < timedelta(minutes=rule.cooldown_minutes)):
                    continue

                # Evaluate rule conditions
                if self._evaluate_rule_conditions(rule, audit_result):
                    rule.last_triggered = datetime.now()
                    rule.trigger_count += 1

                    # Generate alert
                    alert = self._generate_alert_from_rule(rule, audit_result)
                    alerts_generated.append(alert)

                    rules_triggered += 1

            # Queue alerts for sending
            self.alert_queue.extend(alerts_generated)

            return {
                "rules_evaluated": rules_evaluated,
                "rules_triggered": rules_triggered,
                "alerts_generated": len(alerts_generated),
                "queued_for_sending": len(self.alert_queue),
                "alert_ids": [alert.alert_id for alert in alerts_generated]
            }

        except Exception as e:
            return {"error": f"Failed to evaluate audit alerts: {str(e)}"}

    def _list_alert_rules(self, parameters: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """List all configured alert rules."""
        rules_data = []
        for rule in self.alert_rules.values():
            rules_data.append({
                "rule_id": rule.rule_id,
                "name": rule.name,
                "description": rule.description,
                "severity": rule.severity.value,
                "channels": [ch.value for ch in rule.channels],
                "enabled": rule.enabled,
                "cooldown_minutes": rule.cooldown_minutes,
                "threshold_conditions": rule.threshold_conditions,
                "trigger_count": rule.trigger_count,
                "last_triggered": rule.last_triggered.isoformat() if rule.last_triggered else None,
                "created_at": rule.created_at.isoformat()
            })

        return {
            "rules": rules_data,
            "total_rules": len(rules_data),
            "enabled_rules": len([r for r in rules_data if r["enabled"]])
        }

    def _get_alert_history(self, parameters: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Get alert history and statistics."""
        limit = parameters.get("limit", 100)
        severity_filter = parameters.get("severity")
        acknowledged_filter = parameters.get("acknowledged")

        # Filter alerts
        filtered_alerts = self.alert_history

        if severity_filter:
            filtered_alerts = [a for a in filtered_alerts if a.severity.value == severity_filter]

        if acknowledged_filter is not None:
            filtered_alerts = [a for a in filtered_alerts if a.acknowledged == acknowledged_filter]

        # Get recent alerts
        recent_alerts = filtered_alerts[-limit:]

        # Convert to dict format
        alerts_data = []
        for alert in recent_alerts:
            alerts_data.append({
                "alert_id": alert.alert_id,
                "rule_id": alert.rule_id,
                "severity": alert.severity.value,
                "title": alert.title,
                "message": alert.message,
                "channels": [ch.value for ch in alert.channels],
                "timestamp": alert.timestamp.isoformat(),
                "acknowledged": alert.acknowledged,
                "acknowledged_by": alert.acknowledged_by,
                "acknowledged_at": alert.acknowledged_at.isoformat() if alert.acknowledged_at else None
            })

        # Calculate statistics
        total_alerts = len(self.alert_history)
        alerts_by_severity = {}
        for severity in AlertSeverity:
            alerts_by_severity[severity.value] = len([a for a in self.alert_history if a.severity == severity])

        acknowledged_count = len([a for a in self.alert_history if a.acknowledged])

        return {
            "alerts": alerts_data,
            "total_alerts": total_alerts,
            "alerts_by_severity": alerts_by_severity,
            "acknowledged_alerts": acknowledged_count,
            "unacknowledged_alerts": total_alerts - acknowledged_count,
            "acknowledgment_rate": (acknowledged_count / total_alerts * 100) if total_alerts > 0 else 0
        }

    def _acknowledge_alert(self, parameters: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Acknowledge an alert."""
        try:
            alert_id = parameters.get("alert_id")
            acknowledged_by = parameters.get("acknowledged_by", user_context.get("user_id", "unknown"))

            if not alert_id:
                return {"error": "alert_id is required"}

            # Find alert
            alert = None
            for a in self.alert_history:
                if a.alert_id == alert_id:
                    alert = a
                    break

            if not alert:
                return {"error": f"Alert '{alert_id}' not found"}

            if alert.acknowledged:
                return {"error": f"Alert '{alert_id}' is already acknowledged"}

            # Acknowledge alert
            alert.acknowledged = True
            alert.acknowledged_by = acknowledged_by
            alert.acknowledged_at = datetime.now()

            self._save_configuration()

            print(f"✅ Alert '{alert_id}' acknowledged by {acknowledged_by}")

            return {
                "alert_id": alert_id,
                "acknowledged_by": acknowledged_by,
                "acknowledged_at": alert.acknowledged_at.isoformat()
            }

        except Exception as e:
            return {"error": f"Failed to acknowledge alert: {str(e)}"}

    def _test_alert_channels(self, parameters: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Test alert channel connectivity."""
        channels_to_test = parameters.get("channels", ["console", "file"])
        if isinstance(channels_to_test, str):
            channels_to_test = [channels_to_test]

        test_results = {}

        for channel_str in channels_to_test:
            try:
                channel = AlertChannel(channel_str)
                test_alert = AlertMessage(
                    alert_id=f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    rule_id="test",
                    severity=AlertSeverity.INFO,
                    title="Alert Channel Test",
                    message=f"This is a test message to verify {channel_str} connectivity",
                    context={"test": True},
                    timestamp=datetime.now(),
                    channels=[channel]
                )

                success = self._send_alert_message(test_alert)
                test_results[channel_str] = {
                    "success": success > 0,
                    "message": f"Sent to {success} out of 1 channel(s)"
                }

            except Exception as e:
                test_results[channel_str] = {
                    "success": False,
                    "message": f"Error: {str(e)}"
                }

        successful_tests = len([r for r in test_results.values() if r["success"]])

        return {
            "test_results": test_results,
            "successful_tests": successful_tests,
            "total_tests": len(test_results),
            "success_rate": (successful_tests / len(test_results) * 100) if test_results else 0
        }

    def _evaluate_rule_conditions(self, rule: AlertRule, audit_result: Dict[str, Any]) -> bool:
        """Evaluate if rule conditions are met."""
        conditions = rule.threshold_conditions
        summary = audit_result.get("audit_summary", {})

        # Score-based conditions
        if "min_score" in conditions:
            if summary.get("overall_score", 100) < conditions["min_score"]:
                return True

        # Failure-based conditions
        if "max_failures" in conditions:
            if summary.get("failed_checks", 0) > conditions["max_failures"]:
                return True

        # Critical failure conditions
        if "critical_failures" in conditions:
            if summary.get("critical_failures", 0) > 0:
                return True

        # Execution time conditions
        if "max_execution_time" in conditions:
            if audit_result.get("execution_time", 0) > conditions["max_execution_time"]:
                return True

        # Custom conditions
        if "custom_conditions" in conditions:
            for custom_condition in conditions["custom_conditions"]:
                if self._evaluate_custom_condition(custom_condition, audit_result):
                    return True

        return False

    def _evaluate_custom_condition(self, condition: Dict[str, Any], audit_result: Dict[str, Any]) -> bool:
        """Evaluate a custom condition."""
        try:
            field = condition["field"]
            operator = condition["operator"]
            value = condition["value"]

            # Get field value (supports dot notation)
            field_parts = field.split(".")
            current_value = audit_result
            for part in field_parts:
                if isinstance(current_value, dict) and part in current_value:
                    current_value = current_value[part]
                else:
                    current_value = None
                    break

            if current_value is None:
                return False

            # Evaluate condition
            if operator == "equals":
                return current_value == value
            elif operator == "not_equals":
                return current_value != value
            elif operator == "greater_than":
                return current_value > value
            elif operator == "less_than":
                return current_value < value
            elif operator == "contains":
                return value in str(current_value)
            elif operator == "not_contains":
                return value not in str(current_value)

            return False

        except Exception as e:
            print(f"⚠️ Error evaluating custom condition: {e}")
            return False

    def _generate_alert_from_rule(self, rule: AlertRule, audit_result: Dict[str, Any]) -> AlertMessage:
        """Generate an alert message from a rule."""
        alert_id = f"alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{rule.rule_id}"

        title = rule.name
        message = rule.description

        if rule.template:
            # Use template for message
            try:
                context = audit_result.copy()
                context.update({
                    "rule_name": rule.name,
                    "rule_severity": rule.severity.value,
                    "current_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
                message = rule.template.format(**context)
            except Exception as e:
                print(f"⚠️ Error formatting alert template: {e}")
                # Fall back to description

        alert = AlertMessage(
            alert_id=alert_id,
            rule_id=rule.rule_id,
            severity=rule.severity,
            title=title,
            message=message,
            context=audit_result,
            timestamp=datetime.now(),
            channels=rule.channels
        )

        return alert

    def _send_alert_message(self, alert: AlertMessage) -> int:
        """Send alert message to all configured channels."""
        success_count = 0

        for channel in alert.channels:
            try:
                sender = self.alert_senders.get(channel)
                if sender:
                    success = sender(alert)
                    if success:
                        success_count += 1
                else:
                    print(f"⚠️ No sender configured for channel: {channel}")

            except Exception as e:
                print(f"❌ Error sending alert to {channel}: {e}")

        return success_count

    def _background_sender(self):
        """Background thread for sending queued alerts."""
        while self.sender_running:
            try:
                if self.alert_queue:
                    # Process queued alerts
                    alerts_to_send = self.alert_queue.copy()
                    self.alert_queue.clear()

                    for alert in alerts_to_send:
                        self._send_alert_message(alert)
                        self.alert_history.append(alert)

                    # Save updated history
                    self._save_configuration()

                time.sleep(self.config["batch_send_interval"])

            except Exception as e:
                print(f"❌ Error in background sender: {e}")
                time.sleep(10)  # Short sleep on error

    def _send_console_alert(self, alert: AlertMessage) -> bool:
        """Send alert to console."""
        try:
            timestamp = alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            severity_emoji = {
                AlertSeverity.INFO: "ℹ️",
                AlertSeverity.WARNING: "⚠️",
                AlertSeverity.ERROR: "❌",
                AlertSeverity.CRITICAL: "🚨"
            }

            emoji = severity_emoji.get(alert.severity, "📢")

            print(f"\n{emoji} ALERT: {alert.title}")
            print(f"   Time: {timestamp}")
            print(f"   Severity: {alert.severity.value.upper()}")
            print(f"   Message: {alert.message}")
            if alert.context:
                print(f"   Context: {json.dumps(alert.context, indent=2)}")
            print()

            return True

        except Exception as e:
            print(f"❌ Error sending console alert: {e}")
            return False

    def _send_file_alert(self, alert: AlertMessage) -> bool:
        """Send alert to file."""
        try:
            alert_file = Path(self.config["alert_file"])
            alert_file.parent.mkdir(parents=True, exist_ok=True)

            timestamp = alert.timestamp.isoformat()
            alert_entry = {
                "timestamp": timestamp,
                "alert_id": alert.alert_id,
                "rule_id": alert.rule_id,
                "severity": alert.severity.value,
                "title": alert.title,
                "message": alert.message,
                "context": alert.context,
                "channels": [ch.value for ch in alert.channels]
            }

            with open(alert_file, 'a') as f:
                f.write(f"{json.dumps(alert_entry)}\n")

            return True

        except Exception as e:
            print(f"❌ Error sending file alert: {e}")
            return False

    def _send_email_alert(self, alert: AlertMessage) -> bool:
        """Send alert via email."""
        try:
            email_config = self.config["email_config"]
            if not email_config["enabled"]:
                print("⚠️ Email alerts not enabled")
                return False

            # Create message
            msg = MimeMultipart()
            msg['From'] = email_config["from_address"]
            msg['To'] = ', '.join(email_config["to_addresses"])
            msg['Subject'] = f"[{alert.severity.value.upper()}] {alert.title}"

            # Create body
            body = f"""
Alert: {alert.title}
Severity: {alert.severity.value.upper()}
Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
Rule ID: {alert.rule_id}

Message:
{alert.message}

Context:
{json.dumps(alert.context, indent=2)}
            """.strip()

            msg.attach(MimeText(body, 'plain'))

            # Send email
            with smtplib.SMTP(email_config["smtp_server"], email_config["smtp_port"]) as server:
                server.starttls()
                server.login(email_config["username"], email_config["password"])
                server.send_message(msg)

            print(f"✅ Email alert sent to {len(email_config['to_addresses'])} recipients")
            return True

        except Exception as e:
            print(f"❌ Error sending email alert: {e}")
            return False

    def _send_slack_alert(self, alert: AlertMessage) -> bool:
        """Send alert to Slack."""
        try:
            slack_config = self.config["slack_config"]
            if not slack_config["enabled"] or not slack_config["webhook_url"]:
                print("⚠️ Slack alerts not enabled or webhook URL not configured")
                return False

            # Create Slack message
            color = {
                AlertSeverity.INFO: "#36a64f",      # green
                AlertSeverity.WARNING: "#ff9500",   # orange
                AlertSeverity.ERROR: "#ff0000",     # red
                AlertSeverity.CRITICAL: "#8b0000"   # dark red
            }.get(alert.severity, "#36a64f")

            payload = {
                "channel": slack_config["channel"],
                "username": slack_config["username"],
                "attachments": [
                    {
                        "color": color,
                        "title": alert.title,
                        "text": alert.message,
                        "fields": [
                            {
                                "title": "Severity",
                                "value": alert.severity.value.upper(),
                                "short": True
                            },
                            {
                                "title": "Time",
                                "value": alert.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                                "short": True
                            },
                            {
                                "title": "Rule ID",
                                "value": alert.rule_id,
                                "short": True
                            },
                            {
                                "title": "Alert ID",
                                "value": alert.alert_id,
                                "short": True
                            }
                        ],
                        "footer": "Audit Alert System",
                        "ts": int(alert.timestamp.timestamp())
                    }
                ]
            }

            response = requests.post(slack_config["webhook_url"], json=payload, timeout=30)
            response.raise_for_status()

            print("✅ Slack alert sent successfully")
            return True

        except Exception as e:
            print(f"❌ Error sending Slack alert: {e}")
            return False

    def _send_webhook_alert(self, alert: AlertMessage) -> bool:
        """Send alert via webhook."""
        try:
            webhook_config = self.config["webhook_config"]
            if not webhook_config["enabled"] or not webhook_config["url"]:
                print("⚠️ Webhook alerts not enabled or URL not configured")
                return False

            # Create webhook payload
            payload = {
                "alert_id": alert.alert_id,
                "rule_id": alert.rule_id,
                "severity": alert.severity.value,
                "title": alert.title,
                "message": alert.message,
                "context": alert.context,
                "timestamp": alert.timestamp.isoformat(),
                "channels": [ch.value for ch in alert.channels]
            }

            headers = webhook_config.get("headers", {
                "Content-Type": "application/json"
            })

            response = requests.post(
                webhook_config["url"],
                json=payload,
                headers=headers,
                timeout=webhook_config.get("timeout", 30)
            )
            response.raise_for_status()

            print("✅ Webhook alert sent successfully")
            return True

        except Exception as e:
            print(f"❌ Error sending webhook alert: {e}")
            return False

    def cleanup(self):
        """Clean up resources."""
        self.sender_running = False
        if self.sender_thread.is_alive():
            self.sender_thread.join(timeout=5)