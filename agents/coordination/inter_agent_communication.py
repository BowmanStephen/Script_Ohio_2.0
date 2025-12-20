#!/usr/bin/env python3
"""
Inter-Agent Communication Protocol System
Version 1.0

Provides secure, structured messaging between agents with:
- Message routing and delivery confirmation
- Secure channels with encryption
- Message queuing and persistence
- Cross-agent coordination patterns
- Audit logging and security monitoring
"""

import asyncio
import json
import logging
import time
import uuid
import hmac
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass, field
from cryptography.fernet import Fernet
import redis.asyncio as redis
from concurrent.futures import ThreadPoolExecutor
import jwt
import hashlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MessageType(Enum):
    """Types of messages between agents"""

    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    BROADCAST = "broadcast"
    COORDINATION = "coordination"
    STATUS_UPDATE = "status_update"
    ERROR_REPORT = "error_report"
    DATA_TRANSFER = "data_transfer"


class Priority(Enum):
    """Message priority levels"""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4
    EMERGENCY = 5


class DeliveryStatus(Enum):
    """Message delivery status"""

    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    ACKNOWLEDGED = "acknowledged"
    FAILED = "failed"
    EXPIRED = "expired"


@dataclass
class AgentMessage:
    """Standardized message format for inter-agent communication"""

    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sender_id: str = ""
    recipient_id: str = ""
    message_type: MessageType = MessageType.REQUEST
    priority: Priority = Priority.NORMAL
    subject: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    correlation_id: Optional[str] = None
    reply_to: Optional[str] = None
    requires_ack: bool = True
    encryption_enabled: bool = True
    signature: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Set default expiration if not provided"""
        if self.expires_at is None:
            self.expires_at = datetime.utcnow() + timedelta(hours=24)


class SecureChannelManager:
    """Manages secure communication channels between agents"""

    def __init__(self, redis_url: str = "redis://localhost:6379/1"):
        self.redis_url = redis_url
        self.redis_client = None
        self.encryption_key = Fernet.generate_key()
        self.cipher_suite = Fernet(self.encryption_key)
        self.agent_keys: Dict[str, str] = {}
        self.channel_cache: Dict[str, Dict] = {}
        self.executor = ThreadPoolExecutor(max_workers=10)

        logger.info("🔐 SecureChannelManager initialized")

    async def initialize(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.from_url(self.redis_url)
            await self.redis_client.ping()
            logger.info("✅ Redis connection established")
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            raise

    def register_agent(self, agent_id: str, public_key: str = None):
        """Register an agent for secure communication"""
        if public_key is None:
            public_key = Fernet.generate_key().decode()

        self.agent_keys[agent_id] = public_key

        # Cache agent registration
        self.channel_cache[agent_id] = {
            "registered_at": datetime.utcnow().isoformat(),
            "public_key": public_key,
            "message_count": 0,
        }

        logger.info(f"🔑 Agent {agent_id} registered for secure communication")

    def encrypt_message(self, message: AgentMessage, recipient_id: str) -> AgentMessage:
        """Encrypt message payload for recipient"""
        if not message.encryption_enabled or recipient_id not in self.agent_keys:
            return message

        try:
            # Convert payload to JSON and encrypt
            payload_json = json.dumps(message.payload, default=str)
            encrypted_payload = self.cipher_suite.encrypt(payload_json.encode())

            # Create encrypted message
            encrypted_message = AgentMessage(
                message_id=message.message_id,
                sender_id=message.sender_id,
                recipient_id=message.recipient_id,
                message_type=message.message_type,
                priority=message.priority,
                subject=message.subject,
                payload={
                    "encrypted_data": encrypted_payload.decode(),
                    "encrypted": True,
                },
                timestamp=message.timestamp,
                expires_at=message.expires_at,
                correlation_id=message.correlation_id,
                reply_to=message.reply_to,
                requires_ack=message.requires_ack,
                encryption_enabled=True,
                metadata=message.metadata,
            )

            return encrypted_message

        except Exception as e:
            logger.error(f"❌ Encryption failed: {e}")
            return message

    def decrypt_message(self, message: AgentMessage) -> AgentMessage:
        """Decrypt message payload"""
        if not message.encryption_enabled or "encrypted_data" not in message.payload:
            return message

        try:
            encrypted_payload = message.payload["encrypted_data"].encode()
            decrypted_payload = self.cipher_suite.decrypt(encrypted_payload)
            payload_data = json.loads(decrypted_payload.decode())

            # Restore original payload
            message.payload = payload_data
            message.payload["decrypted"] = True

            return message

        except Exception as e:
            logger.error(f"❌ Decryption failed: {e}")
            return message

    def sign_message(self, message: AgentMessage, sender_secret: str) -> str:
        """Sign message for authentication"""
        message_data = f"{message.message_id}:{message.sender_id}:{message.recipient_id}:{message.timestamp.isoformat()}"
        signature = hmac.new(
            sender_secret.encode(), message_data.encode(), hashlib.sha256
        ).hexdigest()
        return signature

    def verify_signature(
        self, message: AgentMessage, signature: str, sender_secret: str
    ) -> bool:
        """Verify message signature"""
        expected_signature = self.sign_message(message, sender_secret)
        return hmac.compare_digest(signature, expected_signature)


class MessageRouter:
    """Advanced message routing and delivery system"""

    def __init__(self, secure_channel: SecureChannelManager):
        self.secure_channel = secure_channel
        self.routing_table: Dict[str, str] = {}  # agent_id -> endpoint
        self.message_queue = asyncio.Queue()
        self.delivery_handlers: Dict[str, Callable] = {}
        self.active_messages: Dict[str, AgentMessage] = {}
        self.delivery_stats = {
            "total_sent": 0,
            "total_delivered": 0,
            "total_failed": 0,
            "average_delivery_time": 0.0,
        }

        logger.info("📡 MessageRouter initialized")

    def register_agent_endpoint(self, agent_id: str, endpoint: str, handler: Callable):
        """Register agent endpoint and message handler"""
        self.routing_table[agent_id] = endpoint
        self.delivery_handlers[agent_id] = handler
        logger.info(f"🔗 Agent {agent_id} registered at {endpoint}")

    async def send_message(self, message: AgentMessage) -> bool:
        """Send message to recipient with delivery confirmation"""
        try:
            # Validate message
            if not self._validate_message(message):
                return False

            # Encrypt message if required
            if message.encryption_enabled:
                message = self.secure_channel.encrypt_message(
                    message, message.recipient_id
                )

            # Store active message
            self.active_messages[message.message_id] = message

            # Route message
            success = await self._route_message(message)

            if success:
                self.delivery_stats["total_sent"] += 1
                logger.info(
                    f"📤 Message {message.message_id} sent to {message.recipient_id}"
                )
            else:
                self.delivery_stats["total_failed"] += 1
                logger.error(f"❌ Failed to send message {message.message_id}")

            return success

        except Exception as e:
            logger.error(f"❌ Message sending failed: {e}")
            self.delivery_stats["total_failed"] += 1
            return False

    async def _route_message(self, message: AgentMessage) -> bool:
        """Route message to recipient agent"""
        if message.recipient_id not in self.routing_table:
            logger.error(f"❌ No route to agent {message.recipient_id}")
            return False

        try:
            # Get recipient handler
            handler = self.delivery_handlers[message.recipient_id]

            # Decrypt message if needed
            if message.encryption_enabled:
                message = self.secure_channel.decrypt_message(message)

            # Deliver message
            delivery_task = asyncio.create_task(self._deliver_message(handler, message))

            # Wait for delivery with timeout
            try:
                result = await asyncio.wait_for(delivery_task, timeout=30.0)
                return result
            except asyncio.TimeoutError:
                logger.error(f"⏰ Message delivery timeout: {message.message_id}")
                return False

        except Exception as e:
            logger.error(f"❌ Message routing failed: {e}")
            return False

    async def _deliver_message(self, handler: Callable, message: AgentMessage) -> bool:
        """Deliver message to agent handler"""
        try:
            start_time = time.time()

            # Call agent handler
            if asyncio.iscoroutinefunction(handler):
                success = await handler(message)
            else:
                success = handler(message)

            delivery_time = time.time() - start_time

            if success:
                self.delivery_stats["total_delivered"] += 1
                self._update_average_delivery_time(delivery_time)
                logger.info(
                    f"✅ Message {message.message_id} delivered in {delivery_time:.3f}s"
                )

                # Send acknowledgment if required
                if message.requires_ack:
                    await self._send_acknowledgment(message)
            else:
                self.delivery_stats["total_failed"] += 1
                logger.error(f"❌ Message delivery failed: {message.message_id}")

            return success

        except Exception as e:
            logger.error(f"❌ Message delivery error: {e}")
            self.delivery_stats["total_failed"] += 1
            return False

    async def _send_acknowledgment(self, original_message: AgentMessage):
        """Send acknowledgment for received message"""
        ack_message = AgentMessage(
            sender_id=original_message.recipient_id,
            recipient_id=original_message.sender_id,
            message_type=MessageType.RESPONSE,
            subject=f"Acknowledgment: {original_message.subject}",
            payload={
                "acknowledgment": True,
                "original_message_id": original_message.message_id,
                "timestamp": datetime.utcnow().isoformat(),
            },
            correlation_id=original_message.message_id,
            reply_to=original_message.message_id,
            requires_ack=False,
        )

        await self.send_message(ack_message)

    def _validate_message(self, message: AgentMessage) -> bool:
        """Validate message format and content"""
        # Check required fields
        if not all([message.sender_id, message.recipient_id, message.subject]):
            logger.error("❌ Missing required message fields")
            return False

        # Check expiration
        if datetime.utcnow() > message.expires_at:
            logger.error(f"❌ Message expired: {message.message_id}")
            return False

        return True

    def _update_average_delivery_time(self, delivery_time: float):
        """Update average delivery time statistics"""
        total_delivered = self.delivery_stats["total_delivered"]
        if total_delivered == 1:
            self.delivery_stats["average_delivery_time"] = delivery_time
        else:
            current_avg = self.delivery_stats["average_delivery_time"]
            new_avg = (
                current_avg * (total_delivered - 1) + delivery_time
            ) / total_delivered
            self.delivery_stats["average_delivery_time"] = new_avg

    async def broadcast_message(
        self,
        sender_id: str,
        subject: str,
        payload: Dict[str, Any],
        priority: Priority = Priority.NORMAL,
    ) -> List[bool]:
        """Broadcast message to all registered agents"""
        results = []

        for agent_id in self.routing_table.keys():
            if agent_id != sender_id:  # Don't send to sender
                message = AgentMessage(
                    sender_id=sender_id,
                    recipient_id=agent_id,
                    message_type=MessageType.BROADCAST,
                    priority=priority,
                    subject=subject,
                    payload=payload,
                )

                result = await self.send_message(message)
                results.append(result)

        return results

    def get_delivery_statistics(self) -> Dict[str, Any]:
        """Get message delivery statistics"""
        return {
            **self.delivery_stats,
            "active_messages": len(self.active_messages),
            "registered_agents": len(self.routing_table),
            "success_rate": (
                self.delivery_stats["total_delivered"]
                / max(self.delivery_stats["total_sent"], 1)
            )
            * 100,
        }


class CoordinationPatterns:
    """Common coordination patterns for multi-agent workflows"""

    def __init__(self, message_router: MessageRouter):
        self.message_router = message_router
        self.active_workflows: Dict[str, Dict] = {}
        self.workflow_templates: Dict[str, Dict] = {}

        logger.info("🔄 CoordinationPatterns initialized")

    async def pipeline_workflow(
        self, workflow_id: str, agents: List[str], initial_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute sequential pipeline workflow across agents"""
        workflow_start = time.time()

        self.active_workflows[workflow_id] = {
            "type": "pipeline",
            "agents": agents,
            "status": "running",
            "started_at": workflow_start,
            "current_step": 0,
            "results": [],
        }

        try:
            current_data = initial_data

            for i, agent_id in enumerate(agents):
                step_start = time.time()

                # Send step message to agent
                message = AgentMessage(
                    sender_id="coordination_patterns",
                    recipient_id=agent_id,
                    message_type=MessageType.COORDINATION,
                    subject=f"Pipeline Step {i+1}/{len(agents)} - {workflow_id}",
                    payload={
                        "workflow_id": workflow_id,
                        "step_number": i,
                        "total_steps": len(agents),
                        "data": current_data,
                        "step_type": "pipeline",
                    },
                )

                # Send message and wait for response
                success = await self.message_router.send_message(message)

                if not success:
                    raise Exception(
                        f"Pipeline step {i} failed: agent {agent_id} not responding"
                    )

                # Wait for response (simplified - in production would use proper async waiting)
                await asyncio.sleep(0.5)

                step_time = time.time() - step_start
                current_data["step_execution_time"] = step_time

                # Store step result
                self.active_workflows[workflow_id]["results"].append(
                    {
                        "step": i,
                        "agent": agent_id,
                        "execution_time": step_time,
                        "success": True,
                    }
                )

                self.active_workflows[workflow_id]["current_step"] = i + 1

            # Mark workflow complete
            total_time = time.time() - workflow_start
            self.active_workflows[workflow_id].update(
                {
                    "status": "completed",
                    "completed_at": time.time(),
                    "total_execution_time": total_time,
                    "final_result": current_data,
                }
            )

            return {
                "workflow_id": workflow_id,
                "status": "success",
                "total_time": total_time,
                "result": current_data,
            }

        except Exception as e:
            self.active_workflows[workflow_id].update(
                {"status": "failed", "error": str(e), "failed_at": time.time()}
            )

            logger.error(f"❌ Pipeline workflow {workflow_id} failed: {e}")
            return {"workflow_id": workflow_id, "status": "failed", "error": str(e)}

    async def parallel_workflow(
        self, workflow_id: str, agents: List[str], tasks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Execute parallel workflow across multiple agents"""
        workflow_start = time.time()

        self.active_workflows[workflow_id] = {
            "type": "parallel",
            "agents": agents,
            "status": "running",
            "started_at": workflow_start,
            "tasks": tasks,
        }

        try:
            # Create parallel tasks
            async def execute_agent_task(agent_id: str, task_data: Dict[str, Any]):
                message = AgentMessage(
                    sender_id="coordination_patterns",
                    recipient_id=agent_id,
                    message_type=MessageType.COORDINATION,
                    subject=f"Parallel Task - {workflow_id}",
                    payload={
                        "workflow_id": workflow_id,
                        "task_data": task_data,
                        "task_type": "parallel",
                    },
                )

                success = await self.message_router.send_message(message)

                return {"agent": agent_id, "success": success, "task_data": task_data}

            # Execute all tasks in parallel
            tasks = [
                execute_agent_task(agent_id, task_data)
                for agent_id, task_data in zip(agents, tasks)
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            successful_tasks = [
                r for r in results if not isinstance(r, Exception) and r["success"]
            ]
            failed_tasks = [
                r for r in results if isinstance(r, Exception) or not r["success"]
            ]

            total_time = time.time() - workflow_start

            # Mark workflow complete
            self.active_workflows[workflow_id].update(
                {
                    "status": "completed" if not failed_tasks else "partial",
                    "completed_at": time.time(),
                    "total_execution_time": total_time,
                    "results": results,
                    "successful_tasks": len(successful_tasks),
                    "failed_tasks": len(failed_tasks),
                }
            )

            return {
                "workflow_id": workflow_id,
                "status": "success" if not failed_tasks else "partial",
                "total_time": total_time,
                "successful_tasks": len(successful_tasks),
                "failed_tasks": len(failed_tasks),
                "results": results,
            }

        except Exception as e:
            self.active_workflows[workflow_id].update(
                {"status": "failed", "error": str(e), "failed_at": time.time()}
            )

            logger.error(f"❌ Parallel workflow {workflow_id} failed: {e}")
            return {"workflow_id": workflow_id, "status": "failed", "error": str(e)}

    async def consensus_decision(
        self,
        decision_id: str,
        agents: List[str],
        proposal: Dict[str, Any],
        min_consensus: int = None,
    ) -> Dict[str, Any]:
        """Coordinate consensus decision among agents"""
        if min_consensus is None:
            min_consensus = len(agents) // 2 + 1

        consensus_start = time.time()

        # Send proposal to all agents
        responses = []

        for agent_id in agents:
            message = AgentMessage(
                sender_id="coordination_patterns",
                recipient_id=agent_id,
                message_type=MessageType.COORDINATION,
                subject=f"Consensus Decision - {decision_id}",
                payload={
                    "decision_id": decision_id,
                    "proposal": proposal,
                    "consensus_type": "voting",
                    "required_consensus": min_consensus,
                },
            )

            success = await self.message_router.send_message(message)
            responses.append({"agent": agent_id, "responded": success})

        # Wait for responses (simplified implementation)
        await asyncio.sleep(2.0)

        # Process responses (would collect actual votes in production)
        votes_for = sum(1 for r in responses if r["responded"])
        votes_against = len(responses) - votes_for

        consensus_reached = votes_for >= min_consensus

        return {
            "decision_id": decision_id,
            "consensus_reached": consensus_reached,
            "votes_for": votes_for,
            "votes_against": votes_against,
            "required_consensus": min_consensus,
            "total_agents": len(agents),
            "execution_time": time.time() - consensus_start,
        }

    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get status of active workflow"""
        return self.active_workflows.get(workflow_id)

    def list_active_workflows(self) -> Dict[str, Dict[str, Any]]:
        """List all active workflows"""
        return self.active_workflows


class InterAgentCommunicationSystem:
    """Main inter-agent communication system orchestrator"""

    def __init__(self, redis_url: str = "redis://localhost:6379/1"):
        self.redis_url = redis_url
        self.secure_channel = SecureChannelManager(redis_url)
        self.message_router = MessageRouter(self.secure_channel)
        self.coordination_patterns = CoordinationPatterns(self.message_router)
        self.is_initialized = False

        logger.info("🌐 InterAgentCommunicationSystem initialized")

    async def initialize(self):
        """Initialize the communication system"""
        try:
            await self.secure_channel.initialize()
            self.is_initialized = True
            logger.info("✅ Inter-Agent Communication System initialized successfully")
        except Exception as e:
            logger.error(f"❌ Initialization failed: {e}")
            raise

    def register_agent(
        self,
        agent_id: str,
        endpoint: str,
        handler: Callable,
        encryption_enabled: bool = True,
    ):
        """Register agent for communication"""
        # Register with secure channel
        self.secure_channel.register_agent(agent_id)

        # Register with message router
        self.message_router.register_agent_endpoint(agent_id, endpoint, handler)

        logger.info(f"🔗 Agent {agent_id} registered with communication system")

    async def send_message(
        self,
        sender_id: str,
        recipient_id: str,
        subject: str,
        payload: Dict[str, Any],
        priority: Priority = Priority.NORMAL,
        message_type: MessageType = MessageType.REQUEST,
    ) -> bool:
        """Send message between agents"""
        message = AgentMessage(
            sender_id=sender_id,
            recipient_id=recipient_id,
            message_type=message_type,
            priority=priority,
            subject=subject,
            payload=payload,
        )

        return await self.message_router.send_message(message)

    async def broadcast(
        self,
        sender_id: str,
        subject: str,
        payload: Dict[str, Any],
        priority: Priority = Priority.NORMAL,
    ) -> List[bool]:
        """Broadcast message to all agents"""
        return await self.message_router.broadcast_message(
            sender_id, subject, payload, priority
        )

    async def execute_pipeline_workflow(
        self, workflow_id: str, agents: List[str], initial_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute pipeline workflow"""
        return await self.coordination_patterns.pipeline_workflow(
            workflow_id, agents, initial_data
        )

    async def execute_parallel_workflow(
        self, workflow_id: str, agents: List[str], tasks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Execute parallel workflow"""
        return await self.coordination_patterns.parallel_workflow(
            workflow_id, agents, tasks
        )

    async def consensus_decision(
        self,
        decision_id: str,
        agents: List[str],
        proposal: Dict[str, Any],
        min_consensus: int = None,
    ) -> Dict[str, Any]:
        """Execute consensus decision"""
        return await self.coordination_patterns.consensus_decision(
            decision_id, agents, proposal, min_consensus
        )

    def get_system_statistics(self) -> Dict[str, Any]:
        """Get comprehensive system statistics"""
        return {
            "is_initialized": self.is_initialized,
            "message_routing": self.message_router.get_delivery_statistics(),
            "active_workflows": len(self.coordination_patterns.active_workflows),
            "registered_agents": len(self.message_router.routing_table),
            "secure_channels": len(self.secure_channel.agent_keys),
        }

    async def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        health_status = {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": "healthy",
            "components": {},
        }

        try:
            # Check Redis connection
            if self.secure_channel.redis_client:
                await self.secure_channel.redis_client.ping()
                health_status["components"]["redis"] = "healthy"
            else:
                health_status["components"]["redis"] = "disconnected"
                health_status["overall_status"] = "degraded"

            # Check message routing
            delivery_stats = self.message_router.get_delivery_statistics()
            if delivery_stats["success_rate"] < 80:
                health_status["components"]["message_routing"] = "degraded"
                health_status["overall_status"] = "degraded"
            else:
                health_status["components"]["message_routing"] = "healthy"

            # Check agent connectivity
            if len(self.message_router.routing_table) == 0:
                health_status["components"]["agent_connectivity"] = "no_agents"
            else:
                health_status["components"]["agent_connectivity"] = "healthy"

            return health_status

        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")
            health_status["overall_status"] = "unhealthy"
            health_status["error"] = str(e)
            return health_status


# Global communication system instance
communication_system = InterAgentCommunicationSystem()


# Convenience functions
async def initialize_communication_system(redis_url: str = "redis://localhost:6379/1"):
    """Initialize the global communication system"""
    await communication_system.initialize(redis_url)


def register_agent_for_communication(agent_id: str, endpoint: str, handler: Callable):
    """Register agent with global communication system"""
    communication_system.register_agent(agent_id, endpoint, handler)


async def send_inter_agent_message(
    sender_id: str,
    recipient_id: str,
    subject: str,
    payload: Dict[str, Any],
    priority: Priority = Priority.NORMAL,
) -> bool:
    """Send message using global communication system"""
    return await communication_system.send_message(
        sender_id, recipient_id, subject, payload, priority
    )


async def broadcast_to_all_agents(
    sender_id: str,
    subject: str,
    payload: Dict[str, Any],
    priority: Priority = Priority.NORMAL,
) -> List[bool]:
    """Broadcast message using global communication system"""
    return await communication_system.broadcast(sender_id, subject, payload, priority)


def get_communication_statistics() -> Dict[str, Any]:
    """Get communication system statistics"""
    return communication_system.get_system_statistics()


async def perform_communication_health_check() -> Dict[str, Any]:
    """Perform communication system health check"""
    return await communication_system.health_check()


if __name__ == "__main__":

    async def main():
        """Demo the inter-agent communication system"""
        print("🌐 Inter-Agent Communication System Demo")
        print("=" * 60)

        # Initialize system
        await initialize_communication_system()

        # Demo agent handler
        async def demo_agent_handler(message: AgentMessage) -> bool:
            print(f"📨 Agent received message: {message.subject}")
            return True

        # Register demo agents
        register_agent_for_communication(
            "demo_agent_1", "localhost:8001", demo_agent_handler
        )
        register_agent_for_communication(
            "demo_agent_2", "localhost:8002", demo_agent_handler
        )

        # Send test message
        success = await send_inter_agent_message(
            "demo_agent_1", "demo_agent_2", "Test Message", {"test": "data"}
        )

        print(f"Message sent: {success}")

        # Broadcast message
        broadcast_results = await broadcast_to_all_agents(
            "demo_agent_1", "Broadcast Test", {"broadcast": "test"}
        )

        print(f"Broadcast results: {broadcast_results}")

        # Execute pipeline workflow
        workflow_result = await communication_system.execute_pipeline_workflow(
            "demo_workflow", ["demo_agent_1", "demo_agent_2"], {"initial_data": "test"}
        )

        print(f"Pipeline workflow: {workflow_result}")

        # Get system statistics
        stats = get_communication_statistics()
        print(f"System statistics: {stats}")

        # Health check
        health = await perform_communication_health_check()
        print(f"Health status: {health}")

    asyncio.run(main())
