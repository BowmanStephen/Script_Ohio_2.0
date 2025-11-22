"""
Agent Registry - Central repository for agent management and discovery
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

from base_agent import BaseAgent, PermissionLevel

class AgentRegistry:
    """Central repository for managing all agents in the system"""

    def __init__(self, registry_file: str = "logs/agent_registry.json"):
        self.registry_file = Path(registry_file)
        self.logger = logging.getLogger("agent_registry")
        self.registered_agents: Dict[str, Dict[str, Any]] = {}
        self.agent_classes: Dict[str, type] = {}
        self.load_registry()

    def load_registry(self) -> None:
        """Load agent registry from file"""
        try:
            if self.registry_file.exists():
                with open(self.registry_file, 'r') as f:
                    data = json.load(f)
                    self.registered_agents = data.get('registered_agents', {})
                    self.logger.info(f"Loaded registry with {len(self.registered_agents)} agents")
            else:
                self.logger.info("Registry file not found, starting with empty registry")
        except Exception as e:
            self.logger.error(f"Error loading registry: {e}")
            self.registered_agents = {}

    def save_registry(self) -> None:
        """Save agent registry to file"""
        try:
            # Ensure directory exists
            self.registry_file.parent.mkdir(parents=True, exist_ok=True)

            data = {
                'registered_agents': self.registered_agents,
                'last_updated': datetime.now().isoformat(),
                'total_agents': len(self.registered_agents)
            }

            with open(self.registry_file, 'w') as f:
                json.dump(data, f, indent=2)

            self.logger.debug("Registry saved successfully")
        except Exception as e:
            self.logger.error(f"Error saving registry: {e}")

    def register_agent(self, agent: BaseAgent, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Register an agent with the registry"""
        try:
            agent_info = {
                "agent_id": agent.agent_id,
                "name": agent.name,
                "permission_level": agent.permission_level.value,
                "capabilities": [
                    {
                        "name": cap.name,
                        "description": cap.description,
                        "permission_required": cap.permission_required.value,
                        "tools_required": cap.tools_required,
                        "estimated_duration": cap.estimated_duration
                    }
                    for cap in agent.get_capabilities()
                ],
                "status": agent.status,
                "created_at": agent.created_at.isoformat(),
                "registered_at": datetime.now().isoformat(),
                "health_status": "unknown"
            }

            if metadata:
                agent_info.update(metadata)

            self.registered_agents[agent.agent_id] = agent_info
            self.save_registry()

            self.logger.info(f"Agent {agent.agent_id} registered successfully")
            return True

        except Exception as e:
            self.logger.error(f"Error registering agent {agent.agent_id}: {e}")
            return False

    def unregister_agent(self, agent_id: str) -> bool:
        """Unregister an agent from the registry"""
        try:
            if agent_id in self.registered_agents:
                del self.registered_agents[agent_id]
                self.save_registry()
                self.logger.info(f"Agent {agent_id} unregistered successfully")
                return True
            else:
                self.logger.warning(f"Agent {agent_id} not found in registry")
                return False
        except Exception as e:
            self.logger.error(f"Error unregistering agent {agent_id}: {e}")
            return False

    def get_agent_info(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a registered agent"""
        return self.registered_agents.get(agent_id)

    def list_agents(self, permission_filter: Optional[PermissionLevel] = None,
                   capability_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all registered agents with optional filtering"""
        agents = list(self.registered_agents.values())

        if permission_filter:
            agents = [agent for agent in agents
                     if agent.get('permission_level') == permission_filter.value]

        if capability_filter:
            agents = [agent for agent in agents
                     if any(cap.get('name') == capability_filter
                           for cap in agent.get('capabilities', []))]

        return agents

    def get_agents_by_capability(self, capability_name: str) -> List[Dict[str, Any]]:
        """Get agents that have a specific capability"""
        matching_agents = []

        for agent_info in self.registered_agents.values():
            capabilities = agent_info.get('capabilities', [])
            for capability in capabilities:
                if capability.get('name') == capability_name:
                    matching_agents.append(agent_info)
                    break

        return matching_agents

    def get_agents_by_permission(self, permission_level: PermissionLevel) -> List[Dict[str, Any]]:
        """Get agents with specific permission level"""
        return [
            agent for agent in self.registered_agents.values()
            if agent.get('permission_level') == permission_level.value
        ]

    def update_agent_status(self, agent_id: str, status: str,
                           health_info: Optional[Dict[str, Any]] = None) -> bool:
        """Update agent status in registry"""
        try:
            if agent_id in self.registered_agents:
                self.registered_agents[agent_id]['status'] = status
                self.registered_agents[agent_id]['last_updated'] = datetime.now().isoformat()

                if health_info:
                    self.registered_agents[agent_id]['health_status'] = health_info.get('status', 'unknown')
                    self.registered_agents[agent_id]['health_score'] = health_info.get('health_score', 0)

                self.save_registry()
                return True
            else:
                self.logger.warning(f"Agent {agent_id} not found in registry")
                return False
        except Exception as e:
            self.logger.error(f"Error updating agent status for {agent_id}: {e}")
            return False

    def get_registry_stats(self) -> Dict[str, Any]:
        """Get registry statistics"""
        stats = {
            "total_agents": len(self.registered_agents),
            "agents_by_permission": {},
            "agents_by_status": {},
            "last_updated": datetime.now().isoformat()
        }

        # Count by permission level
        for agent in self.registered_agents.values():
            permission = agent.get('permission_level', 'unknown')
            stats['agents_by_permission'][permission] = stats['agents_by_permission'].get(permission, 0) + 1

        # Count by status
        for agent in self.registered_agents.values():
            status = agent.get('status', 'unknown')
            stats['agents_by_status'][status] = stats['agents_by_status'].get(status, 0) + 1

        return stats

    def validate_registry_integrity(self) -> Dict[str, Any]:
        """Validate registry integrity and consistency"""
        issues = []
        warnings = []

        # Check for duplicate agent IDs
        agent_ids = list(self.registered_agents.keys())
        if len(agent_ids) != len(set(agent_ids)):
            issues.append("Duplicate agent IDs found in registry")

        # Check for required fields
        required_fields = ['agent_id', 'name', 'permission_level', 'capabilities']
        for agent_id, agent_info in self.registered_agents.items():
            for field in required_fields:
                if field not in agent_info:
                    issues.append(f"Agent {agent_id} missing required field: {field}")

        # Check permission levels
        valid_permissions = [level.value for level in PermissionLevel]
        for agent_id, agent_info in self.registered_agents.items():
            permission = agent_info.get('permission_level')
            if permission not in valid_permissions:
                issues.append(f"Agent {agent_id} has invalid permission level: {permission}")

        # Check capabilities structure
        for agent_id, agent_info in self.registered_agents.items():
            capabilities = agent_info.get('capabilities', [])
            if not isinstance(capabilities, list):
                issues.append(f"Agent {agent_id} has invalid capabilities structure")
                continue

            for cap in capabilities:
                if not isinstance(cap, dict):
                    issues.append(f"Agent {agent_id} has invalid capability format")
                    continue

                cap_required_fields = ['name', 'description', 'permission_required']
                for field in cap_required_fields:
                    if field not in cap:
                        issues.append(f"Agent {agent_id} capability missing field: {field}")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "total_agents": len(self.registered_agents),
            "validation_time": datetime.now().isoformat()
        }