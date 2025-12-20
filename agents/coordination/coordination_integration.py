#!/usr/bin/env python3
"""
Coordination Integration System
Version 1.0

Integrates inter-agent communication and human-in-the-loop systems.
Provides unified coordination for the entire multi-agent architecture.
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable
from pathlib import Path

from .inter_agent_communication import (
    initialize_communication_system, communication_system,
    AgentMessage, MessageType, Priority
)
from .agent_communication_adapter import (
    initialize_agent_communication, register_agent_for_communication,
    AgentCapability, communication_manager, AgentCommunicationAdapter
)
from .human_in_the_loop import (
    initialize_human_in_the_loop, register_decision_gate,
    request_human_decision, submit_human_decision,
    DecisionLevel, NotificationChannel, human_in_the_loop_system
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CoordinationIntegrator:
    """Main coordination integrator for all agents and systems"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.registered_agents: Dict[str, AgentCommunicationAdapter] = {}
        self.coordination_workflows: Dict[str, Dict] = {}
        self.system_metrics = {
            "start_time": datetime.utcnow().isoformat(),
            "agents_registered": 0,
            "decisions_requested": 0,
            "messages_exchanged": 0,
            "workflows_executed": 0
        }

        logger.info("🔗 CoordinationIntegrator initialized")

    async def initialize(self):
        """Initialize all coordination systems"""
        try:
            logger.info("🚀 Initializing coordination systems...")

            # Initialize communication system
            redis_url = self.config.get("redis_url", "redis://localhost:6379/1")
            await initialize_communication_system(redis_url)
            await initialize_agent_communication(redis_url)

            # Initialize human-in-the-loop system
            hitl_config = self.config.get("human_in_the_loop", {})
            await initialize_human_in_the_loop(hitl_config)

            # Register default decision gates for our specialized agents
            await self._register_default_decision_gates()

            logger.info("✅ All coordination systems initialized successfully")

        except Exception as e:
            logger.error(f"❌ Coordination initialization failed: {e}")
            raise

    async def _register_default_decision_gates(self):
        """Register default decision gates for our agent ecosystem"""
        default_gates = [
            {
                "gate_id": "critical_data_operations",
                "name": "Critical CFBD Data Operations",
                "description": "Human approval for critical CFBD API operations and large data processing",
                "decision_level": DecisionLevel.HUMAN_APPROVAL_REQUIRED,
                "timeout_minutes": 120,
                "notification_channels": [NotificationChannel.EMAIL, NotificationChannel.DASHBOARD],
                "custom_criteria": {
                    "data_size_threshold_mb": 1000,
                    "api_call_limit_threshold": 1000,
                    "critical_data_types": ["play_by_play", "player_stats", "advanced_metrics"]
                }
            },
            {
                "gate_id": "model_deployment_production",
                "name": "Model Deployment to Production",
                "description": "Human approval required for deploying ML models to production environment",
                "decision_level": DecisionLevel.HUMAN_APPROVAL_REQUIRED,
                "timeout_minutes": 60,
                "notification_channels": [NotificationChannel.EMAIL, NotificationChannel.SLACK],
                "custom_criteria": {
                    "min_accuracy_threshold": 0.75,
                    "min_training_games": 1000,
                    "max_model_size_mb": 500
                }
            },
            {
                "gate_id": "bowl_prediction_publication",
                "name": "Bowl Game Predictions Publication",
                "description": "Human review before publishing bowl game predictions to public",
                "decision_level": DecisionLevel.HUMAN_APPROVAL_OPTIONAL,
                "timeout_minutes": 180,
                "notification_channels": [NotificationChannel.EMAIL, NotificationChannel.DASHBOARD],
                "custom_criteria": {
                    "high_stakes_games": ["playoffs", "championship", "ny6"],
                    "confidence_threshold": 0.6
                }
            },
            {
                "gate_id": "security_sensitive_operations",
                "name": "Security-Sensitive Operations",
                "description": "Emergency approval for security-critical operations",
                "decision_level": DecisionLevel.EMERGENCY_OVERRIDE,
                "timeout_minutes": 15,
                "notification_channels": [NotificationChannel.EMAIL, NotificationChannel.SMS, NotificationChannel.SLACK],
                "custom_criteria": {
                    "critical_operations": ["database_backup", "system_shutdown", "emergency_recovery"]
                }
            },
            {
                "gate_id": "automated_weekly_analysis",
                "name": "Automated Weekly Analysis Execution",
                "description": "Notification for automated weekly analysis workflows",
                "decision_level": DecisionLevel.NOTIFICATION_ONLY,
                "timeout_minutes": 30,
                "notification_channels": [NotificationChannel.DASHBOARD],
                "custom_criteria": {
                    "report_types": ["weekly_summary", "performance_metrics", "trend_analysis"]
                }
            }
        ]

        for gate_config in default_gates:
            register_decision_gate(**gate_config)

        logger.info(f"🚪 Registered {len(default_gates)} default decision gates")

    async def register_specialized_agent(self, agent_id: str, agent_instance: Any, port: int,
                                       capabilities: List[AgentCapability] = None) -> bool:
        """Register a specialized agent with the coordination system"""
        try:
            # Create communication adapter for the agent
            adapter = register_agent_for_communication(
                agent_id, agent_instance, port, capabilities
            )

            # Store adapter
            self.registered_agents[agent_id] = adapter

            # Add custom message handlers for coordination
            await self._setup_agent_coordination_handlers(agent_id, adapter)

            # Update metrics
            self.system_metrics["agents_registered"] += 1

            logger.info(f"🤖 Specialized agent {agent_id} registered with coordination system")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to register agent {agent_id}: {e}")
            return False

    async def _setup_agent_coordination_handlers(self, agent_id: str, adapter: AgentCommunicationAdapter):
        """Setup coordination-specific message handlers for agent"""

        # Human decision response handler
        async def handle_human_decision_response(message: AgentMessage) -> bool:
            """Handle response from human-in-the-loop system"""
            try:
                decision_data = message.payload
                request_id = decision_data.get("decision_request_id")
                final_decision = decision_data.get("final_decision")
                reason = decision_data.get("reason")

                if request_id and final_decision:
                    logger.info(f"📋 Agent {agent_id} received decision: {final_decision} for request {request_id}")
                    # Agent can now proceed with the decision
                    return True
                else:
                    logger.warning(f"⚠️ Invalid decision response format for agent {agent_id}")
                    return False

            except Exception as e:
                logger.error(f"❌ Error handling human decision for agent {agent_id}: {e}")
                return False

        # Coordination workflow handler
        async def handle_coordination_workflow(message: AgentMessage) -> bool:
            """Handle coordination workflow messages"""
            try:
                workflow_data = message.payload
                workflow_id = workflow_data.get("workflow_id")
                step_number = workflow_data.get("step_number")
                step_data = workflow_data.get("data", {})

                if workflow_id and step_number is not None:
                    logger.info(f"🔄 Agent {agent_id} executing workflow {workflow_id}, step {step_number}")

                    # Execute the agent's part of the workflow
                    # This would call the agent's execute_coordination_step method
                    if hasattr(agent_instance := self.registered_agents[agent_id].agent_instance, 'execute_coordination_step'):
                        result = agent_instance.execute_coordination_step(workflow_id, step_data)
                        # Result would be automatically sent back by the adapter
                        return True

                return False

            except Exception as e:
                logger.error(f"❌ Error handling coordination workflow for agent {agent_id}: {e}")
                return False

        # Register custom handlers
        adapter.register_message_handler(MessageType.RESPONSE, handle_human_decision_response)
        adapter.register_message_handler(MessageType.COORDINATION, handle_coordination_workflow)

    async def execute_coordinated_workflow(self, workflow_name: str, agents: List[str],
                                         workflow_data: Dict[str, Any],
                                         workflow_type: str = "pipeline") -> Dict[str, Any]:
        """Execute a coordinated workflow across multiple agents"""
        try:
            workflow_id = f"{workflow_name}_{int(time.time())}"

            # Get communication adapter for the first agent (coordinator)
            if not agents:
                raise ValueError("No agents specified for workflow")

            coordinator = agents[0]
            if coordinator not in self.registered_agents:
                raise ValueError(f"Coordinator agent {coordinator} not registered")

            # Check if this workflow requires human approval
            await self._check_workflow_human_approval(workflow_name, workflow_data)

            # Execute workflow through communication system
            if workflow_type == "pipeline":
                result = await communication_system.execute_pipeline_workflow(
                    workflow_id, agents, workflow_data
                )
            elif workflow_type == "parallel":
                tasks = [workflow_data for _ in agents]
                result = await communication_system.execute_parallel_workflow(
                    workflow_id, agents, tasks
                )
            else:
                raise ValueError(f"Unknown workflow type: {workflow_type}")

            # Store workflow information
            self.coordination_workflows[workflow_id] = {
                "name": workflow_name,
                "type": workflow_type,
                "agents": agents,
                "data": workflow_data,
                "result": result,
                "timestamp": datetime.utcnow().isoformat()
            }

            # Update metrics
            self.system_metrics["workflows_executed"] += 1

            logger.info(f"✅ Coordinated workflow {workflow_name} completed: {result.get('status', 'unknown')}")
            return result

        except Exception as e:
            logger.error(f"❌ Coordinated workflow {workflow_name} failed: {e}")
            return {
                "workflow_id": workflow_id,
                "status": "failed",
                "error": str(e)
            }

    async def _check_workflow_human_approval(self, workflow_name: str, workflow_data: Dict[str, Any]):
        """Check if workflow requires human approval"""
        # Define workflows that require human approval
        approval_required_workflows = [
            "critical_data_processing",
            "model_production_deployment",
            "public_prediction_publication",
            "system_security_operations"
        ]

        if workflow_name in approval_required_workflows:
            await request_human_decision(
                "workflow_execution",
                "coordination_system",
                f"Workflow Execution Approval: {workflow_name}",
                f"Requesting approval to execute critical workflow: {workflow_name}",
                {
                    "workflow_name": workflow_name,
                    "workflow_data": workflow_data,
                    "execution_type": "automated_workflow"
                },
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "system_state": "operational"
                },
                risk_level="medium",
                urgency="normal"
            )

            self.system_metrics["decisions_requested"] += 1

    async def broadcast_system_update(self, sender_id: str, update_type: str,
                                    update_data: Dict[str, Any]) -> List[bool]:
        """Broadcast system update to all agents"""
        try:
            if sender_id not in self.registered_agents:
                logger.error(f"❌ Sender {sender_id} not registered")
                return []

            subject = f"System Update: {update_type}"
            success = await self.registered_agents[sender_id].broadcast_message(
                subject, update_data
            )

            # Update metrics
            self.system_metrics["messages_exchanged"] += len(self.registered_agents) - 1

            logger.info(f"📢 System update {update_type} broadcasted by {sender_id}")
            return success

        except Exception as e:
            logger.error(f"❌ System update broadcast failed: {e}")
            return []

    async def request_peer_consensus(self, requesting_agent: str, decision_topic: str,
                                   proposal: Dict[str, Any],
                                   min_consensus: int = None) -> Dict[str, Any]:
        """Request consensus from peer agents"""
        try:
            if requesting_agent not in self.registered_agents:
                raise ValueError(f"Requesting agent {requesting_agent} not registered")

            # Get all other agents for consensus
            peer_agents = [
                agent_id for agent_id in self.registered_agents.keys()
                if agent_id != requesting_agent
            ]

            if not peer_agents:
                logger.warning("⚠️ No peer agents available for consensus")
                return {"consensus_reached": False, "reason": "No peers available"}

            # Request consensus through communication system
            decision_id = f"consensus_{decision_topic}_{int(time.time())}"
            result = await communication_system.consensus_decision(
                decision_id, peer_agents, proposal, min_consensus
            )

            logger.info(f"🤝 Consensus for {decision_topic}: {result.get('consensus_reached', False)}")
            return result

        except Exception as e:
            logger.error(f"❌ Consensus request failed: {e}")
            return {"consensus_reached": False, "error": str(e)}

    def get_coordination_status(self) -> Dict[str, Any]:
        """Get comprehensive coordination system status"""
        return {
            "system_metrics": self.system_metrics,
            "registered_agents": list(self.registered_agents.keys()),
            "active_workflows": len(self.coordination_workflows),
            "communication_stats": communication_system.get_system_statistics(),
            "human_oversight_stats": human_in_the_loop_system.get_system_status(),
            "system_uptime_minutes": (
                datetime.utcnow() - datetime.fromisoformat(self.system_metrics["start_time"])
            ).total_seconds() / 60
        }

    async def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        health_status = {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": "healthy",
            "components": {}
        }

        try:
            # Check communication system
            comm_health = await communication_system.health_check()
            health_status["components"]["communication_system"] = comm_health["overall_status"]

            # Check human-in-the-loop system
            hitl_status = human_in_the_loop_system.get_system_status()
            health_status["components"]["human_oversight"] = (
                "healthy" if hitl_status["is_initialized"] else "uninitialized"
            )

            # Check agent connectivity
            healthy_agents = 0
            for agent_id, adapter in self.registered_agents.items():
                if adapter.is_registered:
                    healthy_agents += 1

            agent_health = "healthy" if healthy_agents == len(self.registered_agents) else "degraded"
            health_status["components"]["agent_connectivity"] = agent_health

            # Determine overall status
            component_statuses = health_status["components"].values()
            if all(status == "healthy" for status in component_statuses):
                health_status["overall_status"] = "healthy"
            elif any(status == "unhealthy" for status in component_statuses):
                health_status["overall_status"] = "unhealthy"
            else:
                health_status["overall_status"] = "degraded"

            return health_status

        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")
            health_status["overall_status"] = "unhealthy"
            health_status["error"] = str(e)
            return health_status

# Global coordination integrator instance
coordination_integrator = CoordinationIntegrator()

# Convenience functions
async def initialize_coordination_system(config: Dict[str, Any] = None):
    """Initialize the global coordination system"""
    await coordination_integrator.initialize(config)

async def register_specialized_agent(agent_id: str, agent_instance: Any, port: int,
                                   capabilities: List[AgentCapability] = None) -> bool:
    """Register specialized agent with global coordination system"""
    return await coordination_integrator.register_specialized_agent(
        agent_id, agent_instance, port, capabilities
    )

async def execute_agent_workflow(workflow_name: str, agents: List[str],
                               workflow_data: Dict[str, Any],
                               workflow_type: str = "pipeline") -> Dict[str, Any]:
    """Execute coordinated workflow using global system"""
    return await coordination_integrator.execute_coordinated_workflow(
        workflow_name, agents, workflow_data, workflow_type
    )

async def broadcast_system_update(sender_id: str, update_type: str,
                               update_data: Dict[str, Any]) -> List[bool]:
    """Broadcast system update using global system"""
    return await coordination_integrator.broadcast_system_update(
        sender_id, update_type, update_data
    )

def get_coordination_system_status() -> Dict[str, Any]:
    """Get coordination system status"""
    return coordination_integrator.get_coordination_status()

async def perform_coordination_health_check() -> Dict[str, Any]:
    """Perform coordination system health check"""
    return await coordination_integrator.health_check()

if __name__ == "__main__":
    async def main():
        """Demo the coordination integration system"""
        print("🔗 Coordination Integration System Demo")
        print("=" * 60)

        # Initialize coordination system
        config = {
            "redis_url": "redis://localhost:6379/1",
            "human_in_the_loop": {
                "notifications": {
                    "email": {
                        "smtp_server": "localhost",
                        "smtp_port": 587,
                        "from_address": "coordination-system@example.com",
                        "approvers": ["admin@example.com"]
                    }
                }
            }
        }

        await initialize_coordination_system(config)

        # Demo agent instance
        class DemoSpecializedAgent:
            def __init__(self, agent_id: str):
                self.agent_id = agent_id

            def _execute_action(self, action: str, parameters: Dict, user_context: Dict) -> Dict:
                return {
                    "status": "success",
                    "agent": self.agent_id,
                    "action": action,
                    "parameters": parameters,
                    "execution_time": 1.23
                }

            def execute_coordination_step(self, workflow_id: str, step_data: Dict) -> Dict:
                return {
                    "agent": self.agent_id,
                    "workflow_id": workflow_id,
                    "step_completed": True,
                    "result": f"Processed by {self.agent_id}",
                    "step_data": step_data
                }

        # Register demo specialized agents
        demo_capabilities = [
            AgentCapability(
                name="coordination_demo",
                description="Demo coordination capability",
                input_types=["dict"],
                output_types=["dict"],
                execution_time_estimate=2.0
            )
        ]

        agent1_instance = DemoSpecializedAgent("cfbd_integration_agent")
        agent2_instance = DemoSpecializedAgent("model_execution_engine")

        await register_specialized_agent("cfbd_integration_agent", agent1_instance, 8200, demo_capabilities)
        await register_specialized_agent("model_execution_engine", agent2_instance, 8300, demo_capabilities)

        # Start agent communication
        await communication_manager.start_all_communication()

        # Execute coordinated workflow
        workflow_result = await execute_agent_workflow(
            "data_processing_pipeline",
            ["cfbd_integration_agent", "model_execution_engine"],
            {"task": "process_week_13_data", "season": 2025},
            "pipeline"
        )

        print(f"Workflow result: {json.dumps(workflow_result, indent=2, default=str)}")

        # Broadcast system update
        broadcast_result = await broadcast_system_update(
            "cfbd_integration_agent",
            "data_processed",
            {"games_processed": 50, "season": 2025, "week": 13}
        )

        print(f"Broadcast result: {broadcast_result}")

        # Get coordination system status
        status = get_coordination_system_status()
        print(f"Coordination status: {json.dumps(status, indent=2, default=str)}")

        # Health check
        health = await perform_coordination_health_check()
        print(f"Health status: {health}")

        print("\n✅ Coordination integration demo completed successfully!")

    asyncio.run(main())