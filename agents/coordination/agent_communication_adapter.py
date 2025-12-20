#!/usr/bin/env python3
"""
Agent Communication Adapter
Version 1.0

Integrates existing agents with the inter-agent communication system.
Provides seamless message handling for all specialized agents.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass
import json

from .inter_agent_communication import (
    AgentMessage, MessageType, Priority, DeliveryStatus,
    communication_system, initialize_communication_system,
    register_agent_for_communication, send_inter_agent_message,
    broadcast_to_all_agents, get_communication_statistics
)

logger = logging.getLogger(__name__)

@dataclass
class AgentCapability:
    """Agent capability for communication system registration"""
    name: str
    description: str
    input_types: List[str]
    output_types: List[str]
    execution_time_estimate: float
    requires_human_approval: bool = False

class AgentCommunicationAdapter:
    """Adapter class to integrate existing agents with communication system"""

    def __init__(self, agent_id: str, agent_instance: Any, port: int):
        self.agent_id = agent_id
        self.agent_instance = agent_instance
        self.port = port
        self.endpoint = f"localhost:{port}"
        self.capabilities: List[AgentCapability] = []
        self.message_handlers: Dict[str, Callable] = {}
        self.message_history: List[Dict] = []
        self.is_registered = False

        # Register default message handlers
        self._register_default_handlers()

        logger.info(f"🔌 AgentCommunicationAdapter initialized for {agent_id}")

    def _register_default_handlers(self):
        """Register default message handlers"""
        self.message_handlers.update({
            MessageType.REQUEST: self._handle_request,
            MessageType.RESPONSE: self._handle_response,
            MessageType.NOTIFICATION: self._handle_notification,
            MessageType.BROADCAST: self._handle_broadcast,
            MessageType.COORDINATION: self._handle_coordination,
            MessageType.STATUS_UPDATE: self._handle_status_update,
            MessageType.ERROR_REPORT: self._handle_error_report,
            MessageType.DATA_TRANSFER: self._handle_data_transfer
        })

    def add_capability(self, capability: AgentCapability):
        """Add agent capability"""
        self.capabilities.append(capability)
        logger.info(f"➕ Added capability: {capability.name}")

    def register_message_handler(self, message_type: MessageType, handler: Callable):
        """Register custom message handler"""
        self.message_handlers[message_type] = handler
        logger.info(f"📝 Registered handler for {message_type.value}")

    async def register_with_communication_system(self):
        """Register agent with global communication system"""
        try:
            # Register the agent endpoint and handler
            register_agent_for_communication(
                self.agent_id,
                self.endpoint,
                self._message_handler
            )

            self.is_registered = True
            logger.info(f"✅ Agent {self.agent_id} registered with communication system")

        except Exception as e:
            logger.error(f"❌ Registration failed for {self.agent_id}: {e}")
            raise

    async def _message_handler(self, message: AgentMessage) -> bool:
        """Main message handler for incoming messages"""
        try:
            # Log incoming message
            self._log_message("received", message)

            # Get appropriate handler
            handler = self.message_handlers.get(message.message_type, self._handle_unknown)

            # Handle message
            if asyncio.iscoroutinefunction(handler):
                result = await handler(message)
            else:
                result = handler(message)

            # Log handling result
            self._log_message("handled", message, {"result": result})

            return result

        except Exception as e:
            logger.error(f"❌ Message handling failed: {e}")
            self._log_message("error", message, {"error": str(e)})
            return False

    def _handle_request(self, message: AgentMessage) -> bool:
        """Handle request messages"""
        try:
            # Extract request details
            action = message.payload.get("action", "")
            parameters = message.payload.get("parameters", {})

            # Execute action if agent supports it
            if hasattr(self.agent_instance, '_execute_action'):
                result = self.agent_instance._execute_action(
                    action, parameters, message.metadata.get("user_context", {})
                )

                # Send response if required
                if message.requires_ack:
                    asyncio.create_task(self._send_response(
                        message.sender_id,
                        f"Response: {message.subject}",
                        result,
                        correlation_id=message.message_id
                    ))

                return True
            else:
                logger.warning(f"⚠️ Agent {self.agent_id} does not support _execute_action")
                return False

        except Exception as e:
            logger.error(f"❌ Request handling failed: {e}")
            return False

    def _handle_response(self, message: AgentMessage) -> bool:
        """Handle response messages"""
        try:
            # Process response
            response_data = message.payload
            logger.info(f"📬 Response received from {message.sender_id}: {response_data}")

            # Store response for correlation if needed
            if message.correlation_id:
                self._store_correlated_response(message.correlation_id, response_data)

            return True

        except Exception as e:
            logger.error(f"❌ Response handling failed: {e}")
            return False

    def _handle_notification(self, message: AgentMessage) -> bool:
        """Handle notification messages"""
        try:
            notification_data = message.payload
            logger.info(f"🔔 Notification from {message.sender_id}: {notification_data}")

            # Process notification based on agent capabilities
            if hasattr(self.agent_instance, 'handle_notification'):
                self.agent_instance.handle_notification(notification_data)

            return True

        except Exception as e:
            logger.error(f"❌ Notification handling failed: {e}")
            return False

    def _handle_broadcast(self, message: AgentMessage) -> bool:
        """Handle broadcast messages"""
        try:
            broadcast_data = message.payload
            logger.info(f"📢 Broadcast from {message.sender_id}: {broadcast_data}")

            # Process broadcast
            if hasattr(self.agent_instance, 'handle_broadcast'):
                self.agent_instance.handle_broadcast(broadcast_data)

            return True

        except Exception as e:
            logger.error(f"❌ Broadcast handling failed: {e}")
            return False

    def _handle_coordination(self, message: AgentMessage) -> bool:
        """Handle coordination messages"""
        try:
            coordination_data = message.payload
            logger.info(f"🤝 Coordination request from {message.sender_id}: {coordination_data}")

            # Handle workflow coordination
            workflow_id = coordination_data.get("workflow_id")
            step_data = coordination_data.get("data", {})

            # Execute coordination step
            if hasattr(self.agent_instance, 'execute_coordination_step'):
                result = self.agent_instance.execute_coordination_step(
                    workflow_id, step_data
                )

                # Send response
                asyncio.create_task(self._send_response(
                    message.sender_id,
                    f"Coordination Response: {workflow_id}",
                    result,
                    correlation_id=message.message_id
                ))

            return True

        except Exception as e:
            logger.error(f"❌ Coordination handling failed: {e}")
            return False

    def _handle_status_update(self, message: AgentMessage) -> bool:
        """Handle status update messages"""
        try:
            status_data = message.payload
            logger.info(f"📊 Status update from {message.sender_id}: {status_data}")

            # Update internal status
            if hasattr(self.agent_instance, 'update_peer_status'):
                self.agent_instance.update_peer_status(message.sender_id, status_data)

            return True

        except Exception as e:
            logger.error(f"❌ Status update handling failed: {e}")
            return False

    def _handle_error_report(self, message: AgentMessage) -> bool:
        """Handle error report messages"""
        try:
            error_data = message.payload
            logger.warning(f"⚠️ Error report from {message.sender_id}: {error_data}")

            # Process error report
            if hasattr(self.agent_instance, 'handle_peer_error'):
                self.agent_instance.handle_peer_error(message.sender_id, error_data)

            return True

        except Exception as e:
            logger.error(f"❌ Error report handling failed: {e}")
            return False

    def _handle_data_transfer(self, message: AgentMessage) -> bool:
        """Handle data transfer messages"""
        try:
            transfer_data = message.payload
            logger.info(f"💾 Data transfer from {message.sender_id}: {transfer_data}")

            # Process data transfer
            if hasattr(self.agent_instance, 'receive_data'):
                self.agent_instance.receive_data(message.sender_id, transfer_data)

            return True

        except Exception as e:
            logger.error(f"❌ Data transfer handling failed: {e}")
            return False

    def _handle_unknown(self, message: AgentMessage) -> bool:
        """Handle unknown message types"""
        logger.warning(f"❓ Unknown message type: {message.message_type}")
        return False

    async def _send_response(self, recipient_id: str, subject: str, response_data: Any,
                           correlation_id: str = None):
        """Send response message"""
        try:
            success = await send_inter_agent_message(
                self.agent_id,
                recipient_id,
                subject,
                {
                    "response_data": response_data,
                    "timestamp": datetime.utcnow().isoformat()
                },
                correlation_id=correlation_id
            )

            if success:
                logger.info(f"✅ Response sent to {recipient_id}")
            else:
                logger.error(f"❌ Failed to send response to {recipient_id}")

        except Exception as e:
            logger.error(f"❌ Response sending failed: {e}")

    def _store_correlated_response(self, correlation_id: str, response_data: Any):
        """Store response for correlation with pending request"""
        # Implementation would depend on agent's needs
        pass

    def _log_message(self, action: str, message: AgentMessage, extra_data: Dict = None):
        """Log message activity"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "message_id": message.message_id,
            "sender": message.sender_id,
            "recipient": message.recipient_id,
            "type": message.message_type.value,
            "subject": message.subject
        }

        if extra_data:
            log_entry.update(extra_data)

        self.message_history.append(log_entry)

        # Keep history size manageable
        if len(self.message_history) > 1000:
            self.message_history = self.message_history[-500:]

    async def send_message(self, recipient_id: str, subject: str, payload: Dict[str, Any],
                          priority: Priority = Priority.NORMAL,
                          message_type: MessageType = MessageType.REQUEST,
                          requires_ack: bool = True) -> bool:
        """Send message to another agent"""
        try:
            success = await send_inter_agent_message(
                self.agent_id,
                recipient_id,
                subject,
                payload,
                priority,
                message_type
            )

            if success:
                self._log_message("sent", AgentMessage(
                    sender_id=self.agent_id,
                    recipient_id=recipient_id,
                    message_type=message_type,
                    subject=subject,
                    payload=payload
                ))

            return success

        except Exception as e:
            logger.error(f"❌ Message sending failed: {e}")
            return False

    async def broadcast_message(self, subject: str, payload: Dict[str, Any],
                               priority: Priority = Priority.NORMAL) -> List[bool]:
        """Broadcast message to all agents"""
        try:
            results = await broadcast_to_all_agents(
                self.agent_id,
                subject,
                payload,
                priority
            )

            self._log_message("broadcast", AgentMessage(
                sender_id=self.agent_id,
                recipient_id="ALL",
                message_type=MessageType.BROADCAST,
                subject=subject,
                payload=payload
            ), {"results": results})

            return results

        except Exception as e:
            logger.error(f"❌ Broadcast failed: {e}")
            return []

    async def coordinate_workflow(self, workflow_id: str, agents: List[str],
                                workflow_type: str = "pipeline",
                                workflow_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Coordinate workflow with other agents"""
        try:
            if workflow_type == "pipeline":
                result = await communication_system.execute_pipeline_workflow(
                    workflow_id, agents, workflow_data or {}
                )
            elif workflow_type == "parallel":
                tasks = [workflow_data or {} for _ in agents]
                result = await communication_system.execute_parallel_workflow(
                    workflow_id, agents, tasks
                )
            else:
                raise ValueError(f"Unknown workflow type: {workflow_type}")

            logger.info(f"✅ Workflow {workflow_id} completed: {result['status']}")
            return result

        except Exception as e:
            logger.error(f"❌ Workflow coordination failed: {e}")
            return {"workflow_id": workflow_id, "status": "failed", "error": str(e)}

    async def request_consensus(self, decision_id: str, agents: List[str],
                              proposal: Dict[str, Any], min_consensus: int = None) -> Dict[str, Any]:
        """Request consensus decision from other agents"""
        try:
            result = await communication_system.consensus_decision(
                decision_id, agents, proposal, min_consensus
            )

            logger.info(f"✅ Consensus {decision_id}: {result['consensus_reached']}")
            return result

        except Exception as e:
            logger.error(f"❌ Consensus request failed: {e}")
            return {"decision_id": decision_id, "consensus_reached": False, "error": str(e)}

    def get_message_history(self, limit: int = 100) -> List[Dict]:
        """Get recent message history"""
        return self.message_history[-limit:]

    def get_communication_stats(self) -> Dict[str, Any]:
        """Get agent's communication statistics"""
        stats = get_communication_statistics()

        # Add agent-specific stats
        agent_stats = {
            "agent_id": self.agent_id,
            "is_registered": self.is_registered,
            "capabilities": len(self.capabilities),
            "message_history_size": len(self.message_history),
            "endpoint": self.endpoint
        }

        # Count message types in history
        message_type_counts = {}
        for entry in self.message_history:
            msg_type = entry.get("type", "unknown")
            message_type_counts[msg_type] = message_type_counts.get(msg_type, 0) + 1

        agent_stats["message_type_counts"] = message_type_counts

        return {
            **stats,
            "agent_specific": agent_stats
        }

class AgentCommunicationManager:
    """Manager for all agent communication adapters"""

    def __init__(self):
        self.adapters: Dict[str, AgentCommunicationAdapter] = {}
        self.is_initialized = False

    async def initialize(self, redis_url: str = "redis://localhost:6379/1"):
        """Initialize communication manager"""
        try:
            await initialize_communication_system(redis_url)
            self.is_initialized = True
            logger.info("✅ AgentCommunicationManager initialized")
        except Exception as e:
            logger.error(f"❌ CommunicationManager initialization failed: {e}")
            raise

    def register_agent(self, agent_id: str, agent_instance: Any, port: int,
                      capabilities: List[AgentCapability] = None) -> AgentCommunicationAdapter:
        """Register agent with communication system"""
        adapter = AgentCommunicationAdapter(agent_id, agent_instance, port)

        # Add capabilities if provided
        if capabilities:
            for capability in capabilities:
                adapter.add_capability(capability)

        # Store adapter
        self.adapters[agent_id] = adapter

        logger.info(f"🔌 Agent {agent_id} registered with communication manager")
        return adapter

    async def start_all_communication(self):
        """Start communication for all registered agents"""
        if not self.is_initialized:
            raise RuntimeError("Communication manager not initialized")

        for adapter in self.adapters.values():
            await adapter.register_with_communication_system()

        logger.info(f"🚀 Communication started for {len(self.adapters)} agents")

    async def send_message_from(self, sender_id: str, recipient_id: str, subject: str,
                              payload: Dict[str, Any], priority: Priority = Priority.NORMAL) -> bool:
        """Send message from specific agent"""
        if sender_id not in self.adapters:
            logger.error(f"❌ Sender {sender_id} not registered")
            return False

        return await self.adapters[sender_id].send_message(
            recipient_id, subject, payload, priority
        )

    async def broadcast_from(self, sender_id: str, subject: str, payload: Dict[str, Any],
                           priority: Priority = Priority.NORMAL) -> List[bool]:
        """Broadcast message from specific agent"""
        if sender_id not in self.adapters:
            logger.error(f"❌ Sender {sender_id} not registered")
            return []

        return await self.adapters[sender_id].broadcast_message(
            subject, payload, priority
        )

    def get_all_stats(self) -> Dict[str, Any]:
        """Get statistics for all registered agents"""
        all_stats = {
            "registered_agents": len(self.adapters),
            "is_initialized": self.is_initialized,
            "agent_stats": {}
        }

        for agent_id, adapter in self.adapters.items():
            all_stats["agent_stats"][agent_id] = adapter.get_communication_stats()

        return all_stats

    def get_adapter(self, agent_id: str) -> Optional[AgentCommunicationAdapter]:
        """Get communication adapter for specific agent"""
        return self.adapters.get(agent_id)

# Global communication manager
communication_manager = AgentCommunicationManager()

# Convenience functions
async def initialize_agent_communication(redis_url: str = "redis://localhost:6379/1"):
    """Initialize agent communication system"""
    await communication_manager.initialize(redis_url)

def register_agent_for_communication(agent_id: str, agent_instance: Any, port: int,
                                   capabilities: List[AgentCapability] = None) -> AgentCommunicationAdapter:
    """Register agent for communication"""
    return communication_manager.register_agent(agent_id, agent_instance, port, capabilities)

async def start_agent_communication():
    """Start communication for all registered agents"""
    await communication_manager.start_all_communication()

async def send_from_agent(sender_id: str, recipient_id: str, subject: str,
                         payload: Dict[str, Any]) -> bool:
    """Send message from specific agent"""
    return await communication_manager.send_message_from(
        sender_id, recipient_id, subject, payload
    )

async def broadcast_from_agent(sender_id: str, subject: str, payload: Dict[str, Any]) -> List[bool]:
    """Broadcast from specific agent"""
    return await communication_manager.broadcast_from(sender_id, subject, payload)

def get_all_communication_stats() -> Dict[str, Any]:
    """Get all communication statistics"""
    return communication_manager.get_all_stats()

if __name__ == "__main__":
    async def main():
        """Demo the agent communication adapter"""
        print("🔌 Agent Communication Adapter Demo")
        print("=" * 60)

        # Initialize communication system
        await initialize_agent_communication()

        # Demo agent instance
        class DemoAgent:
            def __init__(self, agent_id: str):
                self.agent_id = agent_id

            def _execute_action(self, action: str, parameters: Dict, user_context: Dict) -> Dict:
                return {
                    "status": "success",
                    "agent": self.agent_id,
                    "action": action,
                    "parameters": parameters
                }

        # Register demo agents
        agent1_instance = DemoAgent("demo_agent_1")
        agent2_instance = DemoAgent("demo_agent_2")

        capabilities = [
            AgentCapability(
                name="demo_action",
                description="Demo action for testing",
                input_types=["string", "dict"],
                output_types=["dict"],
                execution_time_estimate=1.0
            )
        ]

        adapter1 = register_agent_for_communication("demo_agent_1", agent1_instance, 8001, capabilities)
        adapter2 = register_agent_for_communication("demo_agent_2", agent2_instance, 8002, capabilities)

        # Start communication
        await start_agent_communication()

        # Send test message
        success = await send_from_agent(
            "demo_agent_1",
            "demo_agent_2",
            "Test Message",
            {"action": "demo_action", "parameters": {"test": "data"}}
        )

        print(f"Message sent: {success}")

        # Get statistics
        stats = get_all_communication_stats()
        print(f"Communication stats: {json.dumps(stats, indent=2)}")

    asyncio.run(main())