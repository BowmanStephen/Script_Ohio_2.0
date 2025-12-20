#!/usr/bin/env python3
"""
Human-in-the-Loop Integration System
Version 1.0

Provides strategic decision gates and human oversight for critical agent operations.
Ensures human approval for high-stakes decisions while enabling efficient automation.
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass, field
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import os
from pathlib import Path

from .inter_agent_communication import (
    AgentMessage, MessageType, Priority, send_inter_agent_message,
    communication_system
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DecisionLevel(Enum):
    """Levels of human oversight required"""
    FULLY_AUTOMATIC = "fully_automatic"      # No human intervention required
    NOTIFICATION_ONLY = "notification_only"  # Notify human after action
    HUMAN_APPROVAL_OPTIONAL = "human_approval_optional"  # Can proceed if no response
    HUMAN_APPROVAL_REQUIRED = "human_approval_required"  # Must wait for human approval
    EMERGENCY_OVERRIDE = "emergency_override"  # Requires immediate human intervention

class DecisionStatus(Enum):
    """Status of human decisions"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    ESCALATED = "escalated"
    AUTOMATIC_APPROVAL = "automatic_approval"

class NotificationChannel(Enum):
    """Available notification channels"""
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    DASHBOARD = "dashboard"
    SMS = "sms"

@dataclass
class DecisionGate:
    """Represents a decision point requiring human oversight"""
    gate_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    decision_level: DecisionLevel = DecisionLevel.FULLY_AUTOMATIC
    timeout_minutes: int = 60
    auto_approve_if_no_response: bool = False
    escalation_threshold: int = 2
    required_approvers: int = 1
    approvers: List[str] = field(default_factory=list)
    notification_channels: List[NotificationChannel] = field(default_factory=list)
    custom_criteria: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class DecisionRequest:
    """Represents a request for human decision"""
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    gate_id: str = ""
    requesting_agent: str = ""
    title: str = ""
    description: str = ""
    context_data: Dict[str, Any] = field(default_factory=dict)
    proposed_action: Dict[str, Any] = field(default_factory=dict)
    risk_level: str = "low"  # low, medium, high, critical
    urgency: str = "normal"  # low, normal, high, emergency
    timestamp: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    status: DecisionStatus = DecisionStatus.PENDING
    responses: List[Dict[str, Any]] = field(default_factory=list)
    final_decision: Optional[str] = None
    decision_reason: Optional[str] = None
    escalated: bool = False

class NotificationManager:
    """Manages notifications to human approvers"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.email_config = self.config.get("email", {})
        self.slack_config = self.config.get("slack", {})
        self.webhook_config = self.config.get("webhooks", {})

        logger.info("📢 NotificationManager initialized")

    async def send_notification(self, decision_request: DecisionRequest,
                              notification_channels: List[NotificationChannel]) -> Dict[str, bool]:
        """Send notifications through specified channels"""
        results = {}

        for channel in notification_channels:
            try:
                if channel == NotificationChannel.EMAIL:
                    results["email"] = await self._send_email_notification(decision_request)
                elif channel == NotificationChannel.SLACK:
                    results["slack"] = await self._send_slack_notification(decision_request)
                elif channel == NotificationChannel.WEBHOOK:
                    results["webhook"] = await self._send_webhook_notification(decision_request)
                elif channel == NotificationChannel.DASHBOARD:
                    results["dashboard"] = await self._update_dashboard(decision_request)
                else:
                    results[channel.value] = False

            except Exception as e:
                logger.error(f"❌ Notification failed for {channel.value}: {e}")
                results[channel.value] = False

        return results

    async def _send_email_notification(self, decision_request: DecisionRequest) -> bool:
        """Send email notification"""
        try:
            if not self.email_config:
                logger.warning("⚠️ Email configuration not provided")
                return False

            # Create email message
            msg = MimeMultipart()
            msg['From'] = self.email_config.get("from_address", "agent-system@example.com")
            msg['To'] = ", ".join(self.email_config.get("approvers", []))
            msg['Subject'] = f"🤖 Decision Required: {decision_request.title}"

            # Create email body
            body = self._create_email_body(decision_request)
            msg.attach(MimeText(body, 'html'))

            # Send email
            with smtplib.SMTP(
                self.email_config.get("smtp_server", "localhost"),
                self.email_config.get("smtp_port", 587)
            ) as server:
                server.starttls()
                if self.email_config.get("username"):
                    server.login(
                        self.email_config["username"],
                        self.email_config["password"]
                    )
                server.send_message(msg)

            logger.info(f"✅ Email notification sent for request {decision_request.request_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Email notification failed: {e}")
            return False

    async def _send_slack_notification(self, decision_request: DecisionRequest) -> bool:
        """Send Slack notification"""
        try:
            if not self.slack_config:
                logger.warning("⚠️ Slack configuration not provided")
                return False

            # Create Slack message
            slack_message = {
                "text": f"🤖 Decision Required: {decision_request.title}",
                "attachments": [{
                    "color": self._get_slack_color(decision_request.risk_level),
                    "fields": [
                        {"title": "Request ID", "value": decision_request.request_id, "short": True},
                        {"title": "Risk Level", "value": decision_request.risk_level.upper(), "short": True},
                        {"title": "Urgency", "value": decision_request.urgency.upper(), "short": True},
                        {"title": "Requesting Agent", "value": decision_request.requesting_agent, "short": True},
                        {"title": "Description", "value": decision_request.description, "short": False},
                        {"title": "Proposed Action", "value": json.dumps(decision_request.proposed_action, indent=2), "short": False}
                    ],
                    "actions": [
                        {"type": "button", "text": "Approve", "url": f"{self.slack_config.get('base_url', '')}/approve/{decision_request.request_id}"},
                        {"type": "button", "text": "Reject", "url": f"{self.slack_config.get('base_url', '')}/reject/{decision_request.request_id}"}
                    ]
                }]
            }

            # Send to Slack webhook
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.slack_config["webhook_url"],
                    json=slack_message
                ) as response:
                    success = response.status == 200

            if success:
                logger.info(f"✅ Slack notification sent for request {decision_request.request_id}")
            else:
                logger.error(f"❌ Slack notification failed: {response.status}")

            return success

        except Exception as e:
            logger.error(f"❌ Slack notification failed: {e}")
            return False

    async def _send_webhook_notification(self, decision_request: DecisionRequest) -> bool:
        """Send webhook notification"""
        try:
            if not self.webhook_config:
                logger.warning("⚠️ Webhook configuration not provided")
                return False

            webhook_url = self.webhook_config.get("url")
            if not webhook_url:
                logger.warning("⚠️ Webhook URL not configured")
                return False

            payload = {
                "event_type": "decision_request",
                "request_id": decision_request.request_id,
                "title": decision_request.title,
                "description": decision_request.description,
                "risk_level": decision_request.risk_level,
                "urgency": decision_request.urgency,
                "requesting_agent": decision_request.requesting_agent,
                "proposed_action": decision_request.proposed_action,
                "timestamp": decision_request.timestamp.isoformat(),
                "expires_at": decision_request.expires_at.isoformat() if decision_request.expires_at else None
            }

            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook_url,
                    json=payload,
                    headers=self.webhook_config.get("headers", {})
                ) as response:
                    success = response.status == 200

            if success:
                logger.info(f"✅ Webhook notification sent for request {decision_request.request_id}")
            else:
                logger.error(f"❌ Webhook notification failed: {response.status}")

            return success

        except Exception as e:
            logger.error(f"❌ Webhook notification failed: {e}")
            return False

    async def _update_dashboard(self, decision_request: DecisionRequest) -> bool:
        """Update human oversight dashboard"""
        try:
            # Store request for dashboard access
            dashboard_dir = Path("project_management/human_oversight")
            dashboard_dir.mkdir(parents=True, exist_ok=True)

            request_file = dashboard_dir / f"request_{decision_request.request_id}.json"

            with open(request_file, 'w') as f:
                json.dump({
                    "request_id": decision_request.request_id,
                    "gate_id": decision_request.gate_id,
                    "title": decision_request.title,
                    "description": decision_request.description,
                    "risk_level": decision_request.risk_level,
                    "urgency": decision_request.urgency,
                    "requesting_agent": decision_request.requesting_agent,
                    "proposed_action": decision_request.proposed_action,
                    "context_data": decision_request.context_data,
                    "status": decision_request.status.value,
                    "timestamp": decision_request.timestamp.isoformat(),
                    "expires_at": decision_request.expires_at.isoformat() if decision_request.expires_at else None,
                    "responses": decision_request.responses,
                    "escalated": decision_request.escalated
                }, f, indent=2, default=str)

            logger.info(f"✅ Dashboard updated for request {decision_request.request_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Dashboard update failed: {e}")
            return False

    def _create_email_body(self, decision_request: DecisionRequest) -> str:
        """Create HTML email body"""
        risk_color = {
            "low": "#28a745",
            "medium": "#ffc107",
            "high": "#fd7e14",
            "critical": "#dc3545"
        }.get(decision_request.risk_level, "#6c757d")

        urgency_icon = {
            "low": "🟢",
            "normal": "🟡",
            "high": "🟠",
            "emergency": "🔴"
        }.get(decision_request.urgency, "⚪")

        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; margin: 20px;">
            <div style="max-width: 600px; margin: 0 auto;">
                <h2 style="color: #333;">🤖 Human Decision Required</h2>

                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 10px 0;">
                    <h3>{urgency_icon} {decision_request.title}</h3>
                    <p><strong>Request ID:</strong> {decision_request.request_id}</p>
                    <p><strong>Requesting Agent:</strong> {decision_request.requesting_agent}</p>
                    <p><strong>Risk Level:</strong> <span style="color: {risk_color}; font-weight: bold;">{decision_request.risk_level.upper()}</span></p>
                    <p><strong>Urgency:</strong> {decision_request.urgency.upper()}</p>
                </div>

                <div style="margin: 15px 0;">
                    <h4>Description:</h4>
                    <p>{decision_request.description}</p>
                </div>

                <div style="margin: 15px 0;">
                    <h4>Proposed Action:</h4>
                    <pre style="background-color: #f1f1f1; padding: 10px; border-radius: 3px; overflow-x: auto;">
{json.dumps(decision_request.proposed_action, indent=2)}
                    </pre>
                </div>

                <div style="margin: 15px 0;">
                    <h4>Additional Context:</h4>
                    <pre style="background-color: #f1f1f1; padding: 10px; border-radius: 3px; overflow-x: auto;">
{json.dumps(decision_request.context_data, indent=2, default=str)}
                    </pre>
                </div>

                <div style="margin: 20px 0; text-align: center;">
                    <a href="#" style="background-color: #28a745; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin: 5px;">✅ Approve</a>
                    <a href="#" style="background-color: #dc3545; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin: 5px;">❌ Reject</a>
                </div>

                <p style="color: #6c757d; font-size: 12px;">
                    This request will expire at: {decision_request.expires_at or 'No expiration set'}
                </p>
            </div>
        </body>
        </html>
        """

    def _get_slack_color(self, risk_level: str) -> str:
        """Get Slack message color based on risk level"""
        return {
            "low": "good",
            "medium": "warning",
            "high": "danger",
            "critical": "#ff0000"
        }.get(risk_level, "good")

class DecisionEngine:
    """Core decision engine for human-in-the-loop processing"""

    def __init__(self, notification_manager: NotificationManager):
        self.notification_manager = notification_manager
        self.decision_gates: Dict[str, DecisionGate] = {}
        self.active_requests: Dict[str, DecisionRequest] = {}
        self.decision_history: List[Dict[str, Any]] = []
        self.escalation_rules: Dict[str, Dict] = {}

        # Load default decision gates
        self._load_default_gates()

        logger.info("🧠 DecisionEngine initialized")

    def _load_default_gates(self):
        """Load default decision gates for common scenarios"""
        default_gates = [
            DecisionGate(
                gate_id="data_pipeline_critical",
                name="Critical Data Pipeline Operations",
                description="Human approval required for critical data pipeline changes",
                decision_level=DecisionLevel.HUMAN_APPROVAL_REQUIRED,
                timeout_minutes=120,
                notification_channels=[NotificationChannel.EMAIL, NotificationChannel.SLACK],
                custom_criteria={"max_data_risk_score": 0.8}
            ),
            DecisionGate(
                gate_id="model_deployment",
                name="Model Deployment to Production",
                description="Human approval required for deploying models to production",
                decision_level=DecisionLevel.HUMAN_APPROVAL_REQUIRED,
                timeout_minutes=60,
                notification_channels=[NotificationChannel.EMAIL],
                custom_criteria={"min_accuracy_threshold": 0.75}
            ),
            DecisionGate(
                gate_id="high_value_predictions",
                name="High-Value Prediction Operations",
                description="Notification for high-value prediction operations",
                decision_level=DecisionLevel.NOTIFICATION_ONLY,
                timeout_minutes=30,
                notification_channels=[NotificationChannel.DASHBOARD],
                custom_criteria={"value_threshold": 10000}
            ),
            DecisionGate(
                gate_id="security_operations",
                name="Security-Sensitive Operations",
                description="Human approval for security-sensitive operations",
                decision_level=DecisionLevel.EMERGENCY_OVERRIDE,
                timeout_minutes=15,
                notification_channels=[NotificationChannel.EMAIL, NotificationChannel.SMS, NotificationChannel.SLACK],
                custom_criteria={}
            )
        ]

        for gate in default_gates:
            self.decision_gates[gate.gate_id] = gate

        logger.info(f"📋 Loaded {len(default_gates)} default decision gates")

    def register_decision_gate(self, gate: DecisionGate):
        """Register a new decision gate"""
        self.decision_gates[gate.gate_id] = gate
        logger.info(f"🚪 Registered decision gate: {gate.name}")

    async def request_decision(self, gate_id: str, requesting_agent: str, title: str,
                             description: str, proposed_action: Dict[str, Any],
                             context_data: Dict[str, Any] = None,
                             risk_level: str = "low", urgency: str = "normal") -> Dict[str, Any]:
        """Request human decision for an operation"""
        try:
            # Get decision gate
            if gate_id not in self.decision_gates:
                logger.error(f"❌ Decision gate {gate_id} not found")
                return {"status": "error", "message": "Decision gate not found"}

            gate = self.decision_gates[gate_id]

            # Create decision request
            expires_at = datetime.utcnow() + timedelta(minutes=gate.timeout_minutes)

            request = DecisionRequest(
                gate_id=gate_id,
                requesting_agent=requesting_agent,
                title=title,
                description=description,
                context_data=context_data or {},
                proposed_action=proposed_action,
                risk_level=risk_level,
                urgency=urgency,
                expires_at=expires_at
            )

            # Store request
            self.active_requests[request.request_id] = request

            # Handle based on decision level
            if gate.decision_level == DecisionLevel.FULLY_AUTOMATIC:
                return await self._handle_automatic_approval(request, gate)

            # Send notifications
            notification_results = await self.notification_manager.send_notification(
                request, gate.notification_channels
            )

            # Set up timeout handling
            if gate.auto_approve_if_no_response:
                asyncio.create_task(self._handle_request_timeout(request, gate))

            logger.info(f"🤝 Decision request {request.request_id} created for gate {gate_id}")

            return {
                "status": "pending",
                "request_id": request.request_id,
                "decision_level": gate.decision_level.value,
                "timeout_minutes": gate.timeout_minutes,
                "notifications_sent": notification_results,
                "expires_at": expires_at.isoformat()
            }

        except Exception as e:
            logger.error(f"❌ Decision request failed: {e}")
            return {"status": "error", "message": str(e)}

    async def submit_decision(self, request_id: str, approver: str, decision: str,
                            reason: str = None) -> Dict[str, Any]:
        """Submit human decision for a request"""
        try:
            if request_id not in self.active_requests:
                logger.error(f"❌ Decision request {request_id} not found")
                return {"status": "error", "message": "Request not found"}

            request = self.active_requests[request_id]

            # Check if request is still pending
            if request.status != DecisionStatus.PENDING:
                logger.warning(f"⚠️ Request {request_id} is not pending (status: {request.status.value})")
                return {"status": "error", "message": "Request not pending"}

            # Check expiration
            if request.expires_at and datetime.utcnow() > request.expires_at:
                logger.warning(f"⚠️ Request {request_id} has expired")
                return {"status": "error", "message": "Request expired"}

            # Record response
            response = {
                "approver": approver,
                "decision": decision,
                "reason": reason,
                "timestamp": datetime.utcnow().isoformat()
            }

            request.responses.append(response)

            # Update request status
            if decision.lower() in ["approve", "approved", "yes"]:
                request.status = DecisionStatus.APPROVED
                request.final_decision = "approved"
                request.decision_reason = reason
            elif decision.lower() in ["reject", "rejected", "no"]:
                request.status = DecisionStatus.REJECTED
                request.final_decision = "rejected"
                request.decision_reason = reason
            else:
                logger.warning(f"⚠️ Invalid decision: {decision}")
                return {"status": "error", "message": "Invalid decision"}

            # Record in history
            self._record_decision_history(request)

            # Notify requesting agent
            await self._notify_agent_of_decision(request)

            # Remove from active requests
            del self.active_requests[request_id]

            logger.info(f"✅ Decision submitted for request {request_id}: {decision}")

            return {
                "status": "success",
                "request_id": request_id,
                "decision": decision,
                "final_decision": request.final_decision,
                "reason": reason
            }

        except Exception as e:
            logger.error(f"❌ Decision submission failed: {e}")
            return {"status": "error", "message": str(e)}

    async def _handle_automatic_approval(self, request: DecisionRequest, gate: DecisionGate) -> Dict[str, Any]:
        """Handle automatic approval for fully automatic gates"""
        request.status = DecisionStatus.AUTOMATIC_APPROVAL
        request.final_decision = "approved"
        request.decision_reason = f"Automatic approval for gate: {gate.name}"

        # Record in history
        self._record_decision_history(request)

        logger.info(f"🤖 Automatic approval for request {request.request_id}")

        return {
            "status": "approved",
            "request_id": request.request_id,
            "decision_level": "fully_automatic",
            "reason": "Automatic approval"
        }

    async def _handle_request_timeout(self, request: DecisionRequest, gate: DecisionGate):
        """Handle request timeout"""
        await asyncio.sleep(gate.timeout_minutes * 60)

        if request.request_id in self.active_requests and request.status == DecisionStatus.PENDING:
            if gate.auto_approve_if_no_response:
                request.status = DecisionStatus.AUTOMATIC_APPROVAL
                request.final_decision = "approved"
                request.decision_reason = "Auto-approved due to timeout"

                # Record in history
                self._record_decision_history(request)

                # Notify agent
                await self._notify_agent_of_decision(request)

                # Remove from active requests
                del self.active_requests[request.request_id]

                logger.info(f"⏰ Request {request.request_id} auto-approved due to timeout")
            else:
                request.status = DecisionStatus.EXPIRED
                request.final_decision = "expired"
                request.decision_reason = "Request expired"

                # Record in history
                self._record_decision_history(request)

                # Notify agent
                await self._notify_agent_of_decision(request)

                # Remove from active requests
                del self.active_requests[request.request_id]

                logger.info(f"⏰ Request {request.request_id} expired")

    def _record_decision_history(self, request: DecisionRequest):
        """Record decision in history"""
        history_entry = {
            "request_id": request.request_id,
            "gate_id": request.gate_id,
            "requesting_agent": request.requesting_agent,
            "title": request.title,
            "description": request.description,
            "proposed_action": request.proposed_action,
            "risk_level": request.risk_level,
            "urgency": request.urgency,
            "status": request.status.value,
            "final_decision": request.final_decision,
            "decision_reason": request.decision_reason,
            "responses": request.responses,
            "timestamp": request.timestamp.isoformat(),
            "completed_at": datetime.utcnow().isoformat()
        }

        self.decision_history.append(history_entry)

        # Keep history size manageable
        if len(self.decision_history) > 10000:
            self.decision_history = self.decision_history[-5000]

    async def _notify_agent_of_decision(self, request: DecisionRequest):
        """Notify requesting agent of decision"""
        try:
            # Send message to requesting agent
            message_content = {
                "decision_request_id": request.request_id,
                "final_decision": request.final_decision,
                "reason": request.decision_reason,
                "timestamp": datetime.utcnow().isoformat()
            }

            await send_inter_agent_message(
                "human_in_the_loop_system",
                request.requesting_agent,
                f"Decision Made: {request.title}",
                message_content
            )

        except Exception as e:
            logger.error(f"❌ Failed to notify agent of decision: {e}")

    def get_active_requests(self) -> Dict[str, Dict[str, Any]]:
        """Get all active decision requests"""
        return {
            request_id: {
                "request_id": request.request_id,
                "gate_id": request.gate_id,
                "title": request.title,
                "requesting_agent": request.requesting_agent,
                "risk_level": request.risk_level,
                "urgency": request.urgency,
                "status": request.status.value,
                "timestamp": request.timestamp.isoformat(),
                "expires_at": request.expires_at.isoformat() if request.expires_at else None,
                "responses_count": len(request.responses)
            }
            for request_id, request in self.active_requests.items()
        }

    def get_decision_statistics(self) -> Dict[str, Any]:
        """Get decision statistics"""
        total_requests = len(self.decision_history)
        if total_requests == 0:
            return {
                "total_requests": 0,
                "approval_rate": 0,
                "rejection_rate": 0,
                "automatic_approvals": 0,
                "average_response_time_minutes": 0
            }

        approvals = sum(1 for entry in self.decision_history if entry.get("final_decision") == "approved")
        rejections = sum(1 for entry in self.decision_history if entry.get("final_decision") == "rejected")
        automatic_approvals = sum(1 for entry in self.decision_history if entry.get("status") == "automatic_approval")

        # Calculate average response time (simplified)
        response_times = []
        for entry in self.decision_history:
            try:
                created = datetime.fromisoformat(entry["timestamp"])
                completed = datetime.fromisoformat(entry["completed_at"])
                response_time = (completed - created).total_seconds() / 60  # Convert to minutes
                response_times.append(response_time)
            except (KeyError, ValueError):
                continue

        avg_response_time = sum(response_times) / len(response_times) if response_times else 0

        return {
            "total_requests": total_requests,
            "active_requests": len(self.active_requests),
            "approvals": approvals,
            "rejections": rejections,
            "automatic_approvals": automatic_approvals,
            "approval_rate": (approvals / total_requests) * 100 if total_requests > 0 else 0,
            "rejection_rate": (rejections / total_requests) * 100 if total_requests > 0 else 0,
            "automatic_approval_rate": (automatic_approvals / total_requests) * 100 if total_requests > 0 else 0,
            "average_response_time_minutes": avg_response_time,
            "registered_gates": len(self.decision_gates)
        }

class HumanInTheLoopSystem:
    """Main Human-in-the-Loop system orchestrator"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.notification_manager = NotificationManager(self.config.get("notifications", {}))
        self.decision_engine = DecisionEngine(self.notification_manager)
        self.is_initialized = False

        logger.info("👥 HumanInTheLoopSystem initialized")

    async def initialize(self):
        """Initialize the human-in-the-loop system"""
        try:
            # Create directories for dashboard and history
            dashboard_dir = Path("project_management/human_oversight")
            dashboard_dir.mkdir(parents=True, exist_ok=True)

            self.is_initialized = True
            logger.info("✅ Human-in-the-Loop System initialized successfully")

        except Exception as e:
            logger.error(f"❌ Initialization failed: {e}")
            raise

    def register_decision_gate(self, gate_id: str, name: str, description: str,
                             decision_level: DecisionLevel, timeout_minutes: int = 60,
                             notification_channels: List[NotificationChannel] = None,
                             **kwargs) -> bool:
        """Register a new decision gate"""
        try:
            gate = DecisionGate(
                gate_id=gate_id,
                name=name,
                description=description,
                decision_level=decision_level,
                timeout_minutes=timeout_minutes,
                notification_channels=notification_channels or [NotificationChannel.DASHBOARD],
                **kwargs
            )

            self.decision_engine.register_decision_gate(gate)
            logger.info(f"🚪 Registered decision gate: {name}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to register decision gate: {e}")
            return False

    async def request_human_decision(self, gate_id: str, requesting_agent: str, title: str,
                                   description: str, proposed_action: Dict[str, Any],
                                   context_data: Dict[str, Any] = None,
                                   risk_level: str = "low", urgency: str = "normal") -> Dict[str, Any]:
        """Request human decision for an operation"""
        return await self.decision_engine.request_decision(
            gate_id, requesting_agent, title, description,
            proposed_action, context_data, risk_level, urgency
        )

    async def submit_human_decision(self, request_id: str, approver: str, decision: str,
                                  reason: str = None) -> Dict[str, Any]:
        """Submit human decision"""
        return await self.decision_engine.submit_decision(request_id, approver, decision, reason)

    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        return {
            "is_initialized": self.is_initialized,
            "active_requests": self.decision_engine.get_active_requests(),
            "decision_statistics": self.decision_engine.get_decision_statistics(),
            "registered_gates": {
                gate_id: {
                    "name": gate.name,
                    "decision_level": gate.decision_level.value,
                    "timeout_minutes": gate.timeout_minutes,
                    "notification_channels": [ch.value for ch in gate.notification_channels]
                }
                for gate_id, gate in self.decision_engine.decision_gates.items()
            }
        }

# Global human-in-the-loop system instance
human_in_the_loop_system = HumanInTheLoopSystem()

# Convenience functions
async def initialize_human_in_the_loop(config: Dict[str, Any] = None):
    """Initialize the global human-in-the-loop system"""
    await human_in_the_loop_system.initialize()

def register_decision_gate(gate_id: str, name: str, description: str,
                         decision_level: DecisionLevel, timeout_minutes: int = 60,
                         notification_channels: List[NotificationChannel] = None) -> bool:
    """Register a decision gate with the global system"""
    return human_in_the_loop_system.register_decision_gate(
        gate_id, name, description, decision_level, timeout_minutes, notification_channels
    )

async def request_human_decision(gate_id: str, requesting_agent: str, title: str,
                               description: str, proposed_action: Dict[str, Any],
                               context_data: Dict[str, Any] = None,
                               risk_level: str = "low", urgency: str = "normal") -> Dict[str, Any]:
    """Request human decision using the global system"""
    return await human_in_the_loop_system.request_human_decision(
        gate_id, requesting_agent, title, description,
        proposed_action, context_data, risk_level, urgency
    )

async def submit_human_decision(request_id: str, approver: str, decision: str,
                              reason: str = None) -> Dict[str, Any]:
    """Submit human decision using the global system"""
    return await human_in_the_loop_system.submit_human_decision(request_id, approver, decision, reason)

def get_human_oversight_status() -> Dict[str, Any]:
    """Get human oversight system status"""
    return human_in_the_loop_system.get_system_status()

if __name__ == "__main__":
    async def main():
        """Demo the human-in-the-loop system"""
        print("👥 Human-in-the-Loop System Demo")
        print("=" * 60)

        # Initialize system
        await initialize_human_in_the_loop()

        # Register a custom decision gate
        register_decision_gate(
            "demo_gate",
            "Demo Decision Gate",
            "Demo gate for testing human-in-the-loop functionality",
            DecisionLevel.HUMAN_APPROVAL_REQUIRED,
            timeout_minutes=5,
            notification_channels=[NotificationChannel.DASHBOARD]
        )

        # Request a human decision
        decision_request = await request_human_decision(
            "demo_gate",
            "demo_agent",
            "Test Decision Request",
            "This is a test decision request for demo purposes",
            {"action": "deploy_model", "model_name": "test_model"},
            {"test_context": "demo_data"},
            risk_level="medium",
            urgency="normal"
        )

        print(f"Decision request: {json.dumps(decision_request, indent=2, default=str)}")

        # Get system status
        status = get_human_oversight_status()
        print(f"System status: {json.dumps(status, indent=2, default=str)}")

        print("\n✅ Demo completed! Check the dashboard for the pending decision request.")

    asyncio.run(main())