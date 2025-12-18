"""
Meta Agent - Master Controller

The top-level agent that manages the entire agent ecosystem, preventing agent
proliferation while ensuring optimal resource allocation and system health.

Follows OpenAI agents.md best practices:
- Meta-level oversight of all agents
- Lifecycle management (create/modify/destroy agents)
- Resource allocation and load balancing
- System-wide audit trails and compliance
"""

import json
import psutil
import threading
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import time

from agents.core.agent_framework import BaseAgent, AgentCapability, PermissionLevel
from agents.project_management_agent import project_management_agent


@dataclass
class AgentRegistration:
    """Agent registration information"""
    agent_id: str
    agent_name: str
    class_name: str
    file_path: str
    created_at: datetime
    created_by: str
    status: str  # 'active', 'inactive', 'deprecated', 'error'
    capabilities: List[str]
    resource_usage: Dict[str, float]
    health_score: float  # 0-1
    last_health_check: datetime
    dependencies: List[str]
    metadata: Dict[str, Any]


@dataclass
class SystemMetrics:
    """System-wide performance metrics"""
    timestamp: datetime
    total_agents: int
    active_agents: int
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    agent_response_times: Dict[str, float]
    error_count: int
    warning_count: int


class MetaAgent(BaseAgent):
    """
    Meta Agent - Master Controller

    The ultimate authority in the agent ecosystem with these responsibilities:
    - Agent lifecycle management (approve/create/modify/deactivate agents)
    - Resource monitoring and allocation
    - System health and performance monitoring
    - Inter-agent communication coordination
    - Audit trail maintenance
    - Security and compliance enforcement
    """

    def __init__(self):
        super().__init__(
            agent_id="meta_agent",
            name="Meta Agent - Master Controller",
            permission_level=PermissionLevel.ADMIN
        )

        # Agent registry
        self.registry_file = Path("agents/agent_registry.json")
        self.metrics_file = Path("agents/system_metrics.json")
        self.audit_log_file = Path("agents/audit_log.json")

        # Runtime state
        self.agent_registry: Dict[str, AgentRegistration] = {}
        self.system_metrics: List[SystemMetrics] = []
        self.running_agents: Dict[str, BaseAgent] = {}
        self.resource_monitor_thread = None
        self.shutdown_flag = False

        # Configuration limits
        self.max_agents = 20  # Hard limit on number of agents
        self.agent_timeout = 30  # Maximum agent response time in seconds
        self.health_check_interval = 60  # Health check interval in seconds

        # Load existing registry
        self._load_registry()
        self._load_metrics()

        # Start resource monitoring
        self._start_resource_monitoring()

    def _define_capabilities(self) -> List[AgentCapability]:
        """Define meta-level capabilities"""
        return [
            AgentCapability(
                name="register_agent",
                description="Register a new agent in the ecosystem",
                permission_required=PermissionLevel.ADMIN,
                tools_required=["file_operations", "security_validation", "resource_allocation"],
                data_access=["agent_registry", "system_config"],
                execution_time_estimate=2.0
            ),
            AgentCapability(
                name="deactivate_agent",
                description="Deactivate or remove an agent from the ecosystem",
                permission_required=PermissionLevel.ADMIN,
                tools_required=["resource_deallocation", "cleanup_operations"],
                data_access=["agent_registry"],
                execution_time_estimate=1.0
            ),
            AgentCapability(
                name="monitor_system",
                description="Monitor system health and performance metrics",
                permission_required=PermissionLevel.READ_EXECUTE,
                tools_required=["system_monitoring", "performance_analysis"],
                data_access=["system_metrics", "agent_status"],
                execution_time_estimate=1.0
            ),
            AgentCapability(
                name="coordinate_agents",
                description="Coordinate inter-agent communication and workflows",
                permission_required=PermissionLevel.ADMIN,
                tools_required=["message_routing", "workflow_orchestration"],
                data_access=["agent_registry", "communication_channels"],
                execution_time_estimate=2.0
            ),
            AgentCapability(
                name="audit_system",
                description="Perform system audit and compliance checks",
                permission_required=PermissionLevel.ADMIN,
                tools_required=["audit_tools", "compliance_checker"],
                data_access=["audit_logs", "system_history", "agent_registry"],
                execution_time_estimate=5.0
            ),
            AgentCapability(
                name="allocate_resources",
                description="Allocate system resources among agents",
                permission_required=PermissionLevel.ADMIN,
                tools_required=["resource_manager", "load_balancer"],
                data_access=["resource_monitor", "agent_performance"],
                execution_time_estimate=1.5
            )
        ]

    def _execute_action(self, action: str, parameters: Dict, user_context: Dict) -> Dict:
        """Execute meta-agent actions with supreme authority"""
        action_start_time = time.time()

        try:
            # Log action for audit trail
            self._log_action(action, parameters, user_context, "started")

            if action == "register_agent":
                result = self._register_agent(parameters, user_context)
            elif action == "deactivate_agent":
                result = self._deactivate_agent(parameters, user_context)
            elif action == "monitor_system":
                result = self._monitor_system(parameters, user_context)
            elif action == "coordinate_agents":
                result = self._coordinate_agents(parameters, user_context)
            elif action == "audit_system":
                result = self._audit_system(parameters, user_context)
            elif action == "allocate_resources":
                result = self._allocate_resources(parameters, user_context)
            elif action == "get_registry":
                result = self._get_registry(parameters, user_context)
            elif action == "health_check":
                result = self._perform_health_check(parameters, user_context)
            else:
                result = {
                    "success": False,
                    "error": f"Unknown meta-action: {action}",
                    "available_actions": [cap.name for cap in self._define_capabilities()]
                }

            # Log completion
            execution_time = time.time() - action_start_time
            self._log_action(action, parameters, user_context, "completed", execution_time, result)

            return result

        except Exception as e:
            execution_time = time.time() - action_start_time
            error_result = {
                "success": False,
                "error": str(e),
                "action": action,
                "execution_time": execution_time
            }
            self._log_action(action, parameters, user_context, "error", execution_time, error_result)
            return error_result

    def _register_agent(self, params: Dict, context: Dict) -> Dict:
        """Register a new agent with strict validation"""
        required_fields = ["agent_id", "agent_name", "class_name", "file_path", "created_by"]
        for field in required_fields:
            if field not in params:
                return {"success": False, "error": f"Missing required field: {field}"}

        agent_id = params["agent_id"]

        # Check if agent already exists
        if agent_id in self.agent_registry:
            return {"success": False, "error": f"Agent {agent_id} already registered"}

        # Check agent count limit
        active_count = sum(1 for agent in self.agent_registry.values() if agent.status == "active")
        if active_count >= self.max_agents:
            return {
                "success": False,
                "error": f"Maximum agent limit ({self.max_agents}) reached. Current active: {active_count}"
            }

        # Validate agent file exists
        file_path = Path(params["file_path"])
        if not file_path.exists():
            return {"success": False, "error": f"Agent file not found: {file_path}"}

        # Validate agent class
        try:
            # Basic validation - in production, do more thorough inspection
            with open(file_path, 'r') as f:
                content = f.read()
                if params["class_name"] not in content:
                    return {"success": False, "error": f"Agent class {params['class_name']} not found in file"}
        except Exception as e:
            return {"success": False, "error": f"Error validating agent file: {e}"}

        # Create agent registration
        registration = AgentRegistration(
            agent_id=agent_id,
            agent_name=params["agent_name"],
            class_name=params["class_name"],
            file_path=str(file_path),
            created_at=datetime.now(timezone.utc),
            created_by=params["created_by"],
            status="active",
            capabilities=params.get("capabilities", []),
            resource_usage={"cpu": 0.0, "memory": 0.0},
            health_score=1.0,
            last_health_check=datetime.now(timezone.utc),
            dependencies=params.get("dependencies", []),
            metadata=params.get("metadata", {})
        )

        # Add to registry
        self.agent_registry[agent_id] = registration
        self._save_registry()

        # Log to project management
        try:
            project_management_agent._track_progress({
                "plan_id": "super_ai_agent_architecture_v1",
                "milestone": f"Agent registered: {agent_id}",
                "status": "completed",
                "details": {"agent_name": registration.agent_name, "created_by": registration.created_by},
                "completion_percentage": (active_count + 1) / self.max_agents * 100
            }, {"agent_id": self.agent_id})
        except Exception:
            pass  # Don't fail if project management is unavailable

        return {
            "success": True,
            "agent_id": agent_id,
            "status": registration.status,
            "total_active_agents": active_count + 1,
            "registry_size": len(self.agent_registry)
        }

    def _deactivate_agent(self, params: Dict, context: Dict) -> Dict:
        """Deactivate an agent safely"""
        agent_id = params.get("agent_id")
        if not agent_id:
            return {"success": False, "error": "Missing agent_id"}

        if agent_id not in self.agent_registry:
            return {"success": False, "error": f"Agent {agent_id} not found"}

        if agent_id == self.agent_id:
            return {"success": False, "error": "Cannot deactivate the Meta Agent"}

        agent = self.agent_registry[agent_id]
        agent.status = "inactive"
        agent.health_score = 0.0

        # Remove from running agents
        if agent_id in self.running_agents:
            del self.running_agents[agent_id]

        self._save_registry()

        return {
            "success": True,
            "agent_id": agent_id,
            "previous_status": "active",
            "deactivated_at": datetime.now(timezone.utc).isoformat()
        }

    def _monitor_system(self, params: Dict, context: Dict) -> Dict:
        """Collect and return system metrics"""
        metrics = self._collect_system_metrics()

        # Determine system health
        health_issues = []
        if metrics.cpu_usage > 80:
            health_issues.append(f"High CPU usage: {metrics.cpu_usage:.1f}%")
        if metrics.memory_usage > 80:
            health_issues.append(f"High memory usage: {metrics.memory_usage:.1f}%")
        if metrics.error_count > 5:
            health_issues.append(f"High error count: {metrics.error_count}")

        system_health = "healthy" if len(health_issues) == 0 else "degraded" if len(health_issues) <= 2 else "critical"

        return {
            "success": True,
            "metrics": asdict(metrics),
            "health_status": system_health,
            "health_issues": health_issues,
            "recommendations": self._generate_recommendations(metrics)
        }

    def _coordinate_agents(self, params: Dict, context: Dict) -> Dict:
        """Coordinate multi-agent workflows"""
        workflow = params.get("workflow")
        agents = params.get("agents", [])

        if not workflow:
            return {"success": False, "error": "Missing workflow specification"}

        # Validate all agents are available and healthy
        available_agents = []
        for agent_id in agents:
            if agent_id in self.agent_registry:
                agent = self.agent_registry[agent_id]
                if agent.status == "active" and agent.health_score > 0.5:
                    available_agents.append(agent_id)
                else:
                    return {
                        "success": False,
                        "error": f"Agent {agent_id} is not healthy (status: {agent.status}, health: {agent.health_score})"
                    }
            else:
                return {"success": False, "error": f"Agent {agent_id} not found in registry"}

        # For now, just return coordination plan
        # In full implementation, this would execute the workflow
        return {
            "success": True,
            "workflow": workflow,
            "coordinated_agents": available_agents,
            "coordination_plan": f"Execute {workflow} across {len(available_agents)} agents",
            "estimated_duration": len(available_agents) * 2.0  # Rough estimate
        }

    def _audit_system(self, params: Dict, context: Dict) -> Dict:
        """Perform comprehensive system audit"""
        audit_results = {
            "agent_registry": {
                "total_agents": len(self.agent_registry),
                "active_agents": sum(1 for a in self.agent_registry.values() if a.status == "active"),
                "unhealthy_agents": sum(1 for a in self.agent_registry.values() if a.health_score < 0.5)
            },
            "security": {
                "admin_agents": len([a for a in self.agent_registry.values() if "admin" in str(a.metadata).lower()]),
                "suspicious_activity": 0  # Would implement actual security checks
            },
            "performance": self._analyze_performance_trends(),
            "compliance": {
                "agent_documentation": self._check_agent_documentation(),
                "test_coverage": self._estimate_test_coverage(),
                "security_standards": True  # Would implement actual compliance checks
            }
        }

        # Calculate overall compliance score
        compliance_score = (
            audit_results["agent_registry"]["unhealthy_agents"] == 0 and
            audit_results["security"]["suspicious_activity"] == 0 and
            audit_results["compliance"]["agent_documentation"] and
            audit_results["compliance"]["security_standards"]
        )

        return {
            "success": True,
            "audit_results": audit_results,
            "compliance_score": 1.0 if compliance_score else 0.7,
            "audit_timestamp": datetime.now(timezone.utc).isoformat(),
            "recommendations": self._generate_audit_recommendations(audit_results)
        }

    def _allocate_resources(self, params: Dict, context: Dict) -> Dict:
        """Allocate system resources optimally"""
        current_metrics = self._collect_system_metrics()

        # Calculate optimal resource allocation
        total_cpu_available = 100.0 - current_metrics.cpu_usage
        total_memory_available = 100.0 - current_metrics.memory_usage

        # Simple allocation strategy - equal distribution among active agents
        active_agents = [a for a in self.agent_registry.values() if a.status == "active"]

        if not active_agents:
            return {"success": True, "message": "No active agents to allocate resources to"}

        per_agent_cpu = total_cpu_available / len(active_agents)
        per_agent_memory = total_memory_available / len(active_agents)

        allocations = {}
        for agent in active_agents:
            allocations[agent.agent_id] = {
                "cpu_limit": per_agent_cpu,
                "memory_limit": per_agent_memory,
                "priority": "normal"
            }

        return {
            "success": True,
            "allocations": allocations,
            "total_agents": len(active_agents),
            "available_resources": {
                "cpu": total_cpu_available,
                "memory": total_memory_available
            }
        }

    def _get_registry(self, params: Dict, context: Dict) -> Dict:
        """Get current agent registry"""
        include_inactive = params.get("include_inactive", False)

        registry_data = {}
        for agent_id, agent in self.agent_registry.items():
            if include_inactive or agent.status == "active":
                registry_data[agent_id] = asdict(agent)
                registry_data[agent_id]["created_at"] = agent.created_at.isoformat()
                registry_data[agent_id]["last_health_check"] = agent.last_health_check.isoformat()

        return {
            "success": True,
            "registry": registry_data,
            "total_count": len(registry_data),
            "active_count": sum(1 for a in registry_data.values() if a["status"] == "active"),
            "max_agents": self.max_agents
        }

    def _perform_health_check(self, params: Dict, context: Dict) -> Dict:
        """Perform health check on all agents"""
        health_results = {}

        for agent_id, agent in self.agent_registry.items():
            if agent.status == "active":
                # Simple health check based on last update time
                time_since_check = (datetime.now(timezone.utc) - agent.last_health_check).total_seconds()

                if time_since_check > 300:  # 5 minutes
                    health_score = max(0.0, agent.health_score - 0.1)
                    status = "stale"
                elif agent.health_score < 0.5:
                    health_score = agent.health_score
                    status = "unhealthy"
                else:
                    health_score = agent.health_score
                    status = "healthy"

                health_results[agent_id] = {
                    "status": status,
                    "health_score": health_score,
                    "last_check": agent.last_health_check.isoformat(),
                    "issues": [] if health_score > 0.7 else ["Performance degraded"]
                }

                # Update agent health
                agent.health_score = health_score
                agent.last_health_check = datetime.now(timezone.utc)

        self._save_registry()

        return {
            "success": True,
            "health_results": health_results,
            "summary": {
                "total_checked": len(health_results),
                "healthy": sum(1 for r in health_results.values() if r["status"] == "healthy"),
                "unhealthy": sum(1 for r in health_results.values() if r["status"] == "unhealthy"),
                "stale": sum(1 for r in health_results.values() if r["status"] == "stale")
            }
        }

    # Helper methods
    def _collect_system_metrics(self) -> SystemMetrics:
        """Collect current system metrics"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory_percent = psutil.virtual_memory().percent
        disk_percent = psutil.disk_usage('/').percent

        active_agents = sum(1 for a in self.agent_registry.values() if a.status == "active")

        # Calculate agent response times (mock data for now)
        response_times = {agent_id: 0.5 + (hash(agent_id) % 100) / 100 for agent_id in self.agent_registry.keys()}

        return SystemMetrics(
            timestamp=datetime.now(timezone.utc),
            total_agents=len(self.agent_registry),
            active_agents=active_agents,
            cpu_usage=cpu_percent,
            memory_usage=memory_percent,
            disk_usage=disk_percent,
            agent_response_times=response_times,
            error_count=0,  # Would implement actual error tracking
            warning_count=0  # Would implement actual warning tracking
        )

    def _generate_recommendations(self, metrics: SystemMetrics) -> List[str]:
        """Generate system optimization recommendations"""
        recommendations = []

        if metrics.cpu_usage > 70:
            recommendations.append("Consider scaling compute resources or optimizing agent workloads")

        if metrics.memory_usage > 70:
            recommendations.append("Monitor memory usage and consider implementing caching strategies")

        if metrics.active_agents > 15:
            recommendations.append("Approaching agent limit - consider consolidating functionality")

        slow_agents = [aid for aid, rt in metrics.agent_response_times.items() if rt > 2.0]
        if slow_agents:
            recommendations.append(f"Optimize performance for slow agents: {', '.join(slow_agents)}")

        return recommendations

    def _analyze_performance_trends(self) -> Dict:
        """Analyze performance trends from historical metrics"""
        if len(self.system_metrics) < 2:
            return {"trend": "insufficient_data", "recommendation": "Continue monitoring"}

        # Simple trend analysis
        recent = self.system_metrics[-5:] if len(self.system_metrics) >= 5 else self.system_metrics
        avg_cpu = sum(m.cpu_usage for m in recent) / len(recent)
        avg_memory = sum(m.memory_usage for m in recent) / len(recent)

        return {
            "trend": "stable" if avg_cpu < 70 and avg_memory < 70 else "degraded",
            "average_cpu": avg_cpu,
            "average_memory": avg_memory,
            "data_points": len(recent)
        }

    def _check_agent_documentation(self) -> bool:
        """Check if all agents have proper documentation"""
        # Simplified check - would implement actual documentation validation
        return len(self.agent_registry) > 0

    def _estimate_test_coverage(self) -> float:
        """Estimate test coverage for agents"""
        # Simplified estimate - would implement actual test coverage analysis
        test_files = list(Path("agents/tests").glob("test_*.py"))
        return min(len(test_files) / max(len(self.agent_registry), 1), 1.0)

    def _generate_audit_recommendations(self, audit_results: Dict) -> List[str]:
        """Generate recommendations based on audit results"""
        recommendations = []

        if audit_results["agent_registry"]["unhealthy_agents"] > 0:
            recommendations.append("Address unhealthy agents - check logs and restart if necessary")

        if not audit_results["compliance"]["agent_documentation"]:
            recommendations.append("Improve agent documentation for better maintainability")

        if audit_results["compliance"]["test_coverage"] < 0.8:
            recommendations.append("Increase test coverage to ensure system reliability")

        return recommendations

    def _load_registry(self):
        """Load agent registry from file"""
        if self.registry_file.exists():
            try:
                with open(self.registry_file, 'r') as f:
                    data = json.load(f)
                    for agent_id, agent_data in data.items():
                        agent_data["created_at"] = datetime.fromisoformat(agent_data["created_at"])
                        agent_data["last_health_check"] = datetime.fromisoformat(agent_data["last_health_check"])
                        self.agent_registry[agent_id] = AgentRegistration(**agent_data)
            except Exception as e:
                print(f"Error loading registry: {e}")

    def _save_registry(self):
        """Save agent registry to file"""
        try:
            data = {}
            for agent_id, agent in self.agent_registry.items():
                data[agent_id] = asdict(agent)
                data[agent_id]["created_at"] = agent.created_at.isoformat()
                data[agent_id]["last_health_check"] = agent.last_health_check.isoformat()

            with open(self.registry_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving registry: {e}")

    def _load_metrics(self):
        """Load system metrics from file"""
        if self.metrics_file.exists():
            try:
                with open(self.metrics_file, 'r') as f:
                    data = json.load(f)
                    for metric_data in data:
                        metric_data["timestamp"] = datetime.fromisoformat(metric_data["timestamp"])
                        self.system_metrics.append(SystemMetrics(**metric_data))
            except Exception as e:
                print(f"Error loading metrics: {e}")

    def _save_metrics(self):
        """Save system metrics to file (keep only last 100 entries)"""
        try:
            data = []
            for metric in self.system_metrics[-100:]:
                metric_dict = asdict(metric)
                metric_dict["timestamp"] = metric.timestamp.isoformat()
                data.append(metric_dict)

            with open(self.metrics_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving metrics: {e}")

    def _log_action(self, action: str, params: Dict, context: Dict, status: str,
                   execution_time: float = 0, result: Dict = None):
        """Log meta-agent actions for audit trail"""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent_id": self.agent_id,
            "action": action,
            "parameters": params,
            "user_context": context,
            "status": status,
            "execution_time": execution_time,
            "result_summary": result.get("success", False) if result else None
        }

        # Append to audit log
        try:
            audit_logs = []
            if self.audit_log_file.exists():
                with open(self.audit_log_file, 'r') as f:
                    audit_logs = json.load(f)

            audit_logs.append(log_entry)

            # Keep only last 1000 entries
            if len(audit_logs) > 1000:
                audit_logs = audit_logs[-1000:]

            with open(self.audit_log_file, 'w') as f:
                json.dump(audit_logs, f, indent=2)
        except Exception as e:
            print(f"Error logging action: {e}")

    def _start_resource_monitoring(self):
        """Start background resource monitoring"""
        def monitor():
            while not self.shutdown_flag:
                try:
                    metrics = self._collect_system_metrics()
                    self.system_metrics.append(metrics)
                    self._save_metrics()

                    # Perform health check on agents periodically
                    if len(self.system_metrics) % self.health_check_interval == 0:
                        self._perform_health_check({}, {"agent_id": self.agent_id})

                except Exception as e:
                    print(f"Error in resource monitoring: {e}")

                time.sleep(60)  # Monitor every minute

        self.resource_monitor_thread = threading.Thread(target=monitor, daemon=True)
        self.resource_monitor_thread.start()

    def shutdown(self):
        """Graceful shutdown of meta agent"""
        self.shutdown_flag = True
        if self.resource_monitor_thread:
            self.resource_monitor_thread.join(timeout=5)


# Singleton instance for easy access
meta_agent = MetaAgent()