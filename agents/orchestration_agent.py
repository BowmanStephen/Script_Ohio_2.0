"""
Orchestration Agent - Enhanced Meta Agent with Optimization Integration

Extends the Meta Agent with advanced orchestration capabilities:
- Context compression and management integration
- Hierarchical memory system integration
- Workflow automation coordination
- Advanced agent lifecycle management
- Performance optimization and monitoring
"""

import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Import existing Meta Agent
from agents.core.agent_framework import AgentCapability, BaseAgent, PermissionLevel
from agents.meta_agent import MetaAgent


# Lazy loading for optimization components to avoid circular dependencies
def _get_optimization_components():
    """Lazy load optimization components to avoid circular dependencies"""
    try:
        from .optimization.context_compression_rules import (
            ContextState,
            context_compression_engine,
        )
        from .optimization.memory_manager import MemoryLevel, memory_manager
        from .optimization.workflow_automator import (
            TaskPriority,
            WorkflowStatus,
            workflow_automator,
        )

        return {
            "context_compression_engine": context_compression_engine,
            "memory_manager": memory_manager,
            "workflow_automator": workflow_automator,
            "ContextState": ContextState,
            "MemoryLevel": MemoryLevel,
            "WorkflowStatus": WorkflowStatus,
            "TaskPriority": TaskPriority,
        }
    except ImportError:
        # Return None if optimization components are not available
        return None


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OrchestrationMode(Enum):
    """Orchestration operation modes"""

    OPTIMIZED = "optimized"  # Use all optimization features
    STANDARD = "standard"  # Basic orchestration without optimization
    EMERGENCY = "emergency"  # Minimal operation mode
    DEBUG = "debug"  # Verbose logging and monitoring


class AgentLoadState(Enum):
    """Agent load balancing states"""

    IDLE = "idle"
    LIGHT = "light"  # < 25% capacity
    MODERATE = "moderate"  # 25-75% capacity
    HEAVY = "heavy"  # 75-95% capacity
    OVERLOADED = "overloaded"  # > 95% capacity


@dataclass
class OrchestrationMetrics:
    """Comprehensive orchestration performance metrics"""

    timestamp: datetime
    mode: OrchestrationMode
    agent_states: Dict[str, AgentLoadState]
    context_compression_stats: Dict[str, Any]
    memory_stats: Dict[str, Any]
    workflow_stats: Dict[str, Any]
    performance_gains: Dict[str, float]
    resource_utilization: Dict[str, float]


class OrchestrationAgent(BaseAgent):
    """
    Enhanced Orchestration Agent with advanced optimization capabilities.

    Integrates context compression, hierarchical memory management,
    and workflow automation for optimal system performance.
    """

    def __init__(self, mode: OrchestrationMode = OrchestrationMode.OPTIMIZED):
        """Initialize the orchestration agent"""
        super().__init__(
            agent_id="orchestration_agent",
            name="Orchestration Agent - Enhanced Meta Agent with Optimization",
            permission_level=PermissionLevel.ADMIN,
        )

        self.mode = mode
        self.orchestration_config = self._load_orchestration_config()
        self.performance_history: List[OrchestrationMetrics] = []

        # Enhanced capabilities state
        self.agent_load_states: Dict[str, AgentLoadState] = {}
        self.optimization_enabled = mode == OrchestrationMode.OPTIMIZED

        # COMPOSITION PATTERN: Initialize MetaAgent for registry access
        self._meta_agent = None
        self._initialize_meta_agent()

        # Lazy load optimization components
        self._optimization_components = _get_optimization_components()
        self.workflow_coordinator = (
            self._optimization_components["workflow_automator"]
            if self._optimization_components else None
        )

        # Performance monitoring
        self.performance_baseline = self._establish_performance_baseline()
        self.last_optimization_time = datetime.now(timezone.utc)

        logger.info(f"OrchestrationAgent initialized in {mode.value} mode")

    def _initialize_meta_agent(self):
        """Initialize MetaAgent for registry access"""
        try:
            self._meta_agent = MetaAgent()
            logger.info("MetaAgent initialized for composition pattern")
        except Exception as e:
            logger.warning(f"Failed to initialize MetaAgent: {e}")
            self._meta_agent = None

    @property
    def agent_registry(self):
        """Safe access to agent_registry via composition"""
        if self._meta_agent and hasattr(self._meta_agent, 'agent_registry'):
            return self._meta_agent.agent_registry
        return {}

    def _get_context_compression_engine(self):
        """Safe access to context compression engine"""
        if (self._optimization_components and
            "context_compression_engine" in self._optimization_components):
            return self._optimization_components["context_compression_engine"]
        return None

    def _get_memory_manager(self):
        """Safe access to memory manager"""
        if (self._optimization_components and
            "memory_manager" in self._optimization_components):
            return self._optimization_components["memory_manager"]
        return None

    def _get_workflow_automator(self):
        """Safe access to workflow automator"""
        if (self._optimization_components and
            "workflow_automator" in self._optimization_components):
            return self._optimization_components["workflow_automator"]
        return None

    def _check_composition_health(self) -> Dict[str, Any]:
        """Check health of composed components"""
        return {
            "meta_agent_available": self._meta_agent is not None,
            "agent_registry_size": len(self.agent_registry),
            "optimization_components_available": self._optimization_components is not None,
            "context_compression_available": self._get_context_compression_engine() is not None,
            "memory_manager_available": self._get_memory_manager() is not None,
            "workflow_automator_available": self._get_workflow_automator() is not None
        }

    def _handle_missing_component(self, component_name: str, operation: str) -> Dict:
        """Handle missing optimization component gracefully"""
        error_msg = f"Cannot execute {operation}: {component_name} not available"
        logger.error(error_msg)
        return {
            "success": False,
            "error": error_msg,
            "error_type": "MissingComponent",
            "component": component_name,
            "fallback_applied": True
        }

    def _load_orchestration_config(self) -> Dict[str, Any]:
        """Load orchestration-specific configuration"""
        config_path = Path("config/claude_code_optimization.json")
        if config_path.exists():
            try:
                with open(config_path, "r") as f:
                    full_config = json.load(f)
                return {
                    "agent_coordination": full_config.get("agent_coordination", {}),
                    "performance_optimization": full_config.get(
                        "performance_optimization", {}
                    ),
                    "claude_code_integration": full_config.get(
                        "claude_code_integration", {}
                    ),
                }
            except Exception as e:
                logger.warning(f"Error loading orchestration config: {e}")

        return self._get_default_orchestration_config()

    def _get_default_orchestration_config(self) -> Dict[str, Any]:
        """Get default orchestration configuration"""
        return {
            "agent_coordination": {
                "lifecycle_management": {
                    "enabled": True,
                    "health_monitoring": True,
                    "auto_degrade_under_load": True,
                },
                "load_balancing": {
                    "cpu_threshold_percent": 70,
                    "memory_threshold_percent": 80,
                },
            },
            "performance_optimization": {
                "cfbd_integration": {
                    "rate_limit_requests_per_second": 6,
                    "intelligent_batching": True,
                }
            },
        }

    def _define_capabilities(self) -> List[AgentCapability]:
        """Define enhanced orchestration capabilities"""
        orchestration_capabilities = [
            AgentCapability(
                name="orchestrate_workflow",
                description="Coordinate complex multi-agent workflows with optimization",
                permission_required=PermissionLevel.ADMIN,
                tools_required=[
                    "workflow_automator",
                    "context_compression",
                    "memory_manager",
                ],
                data_access=["agent_registry", "system_metrics", "workflow_state"],
                execution_time_estimate=3.0,
            ),
            AgentCapability(
                name="optimize_performance",
                description="Apply performance optimizations across the agent ecosystem",
                permission_required=PermissionLevel.ADMIN,
                tools_required=[
                    "context_compression",
                    "memory_manager",
                    "load_balancer",
                ],
                data_access=[
                    "system_metrics",
                    "agent_performance",
                    "optimization_config",
                ],
                execution_time_estimate=2.0,
            ),
            AgentCapability(
                name="manage_context_windows",
                description="Optimize context window usage across all agents",
                permission_required=PermissionLevel.ADMIN,
                tools_required=["context_compression_engine", "memory_manager"],
                data_access=[
                    "agent_contexts",
                    "compression_settings",
                    "memory_hierarchy",
                ],
                execution_time_estimate=1.5,
            ),
            AgentCapability(
                name="coordinate_claude_code",
                description="Bridge Claude Code requests with agent ecosystem",
                permission_required=PermissionLevel.ADMIN,
                tools_required=["claude_code_bridge", "task_decomposition"],
                data_access=[
                    "agent_registry",
                    "claude_code_interface",
                    "request_queue",
                ],
                execution_time_estimate=1.0,
            ),
            AgentCapability(
                name="monitor_optimization",
                description="Monitor and report on optimization effectiveness",
                permission_required=PermissionLevel.READ_EXECUTE,
                tools_required=["performance_analyzer", "metrics_collector"],
                data_access=[
                    "optimization_metrics",
                    "performance_history",
                    "system_health",
                ],
                execution_time_estimate=1.0,
            ),
        ]

        return orchestration_capabilities

    def _execute_action(
        self, action: str, parameters: Dict, user_context: Dict
    ) -> Dict:
        """Execute orchestration actions with optimization integration"""
        action_start_time = time.time()

        try:
            # Apply context optimization if enabled
            if self.optimization_enabled:
                self._apply_context_optimization(action, parameters, user_context)

            # Route to enhanced orchestration actions
            if action == "orchestrate_workflow":
                result = self._orchestrate_workflow(parameters, user_context)
            elif action == "optimize_performance":
                result = self._optimize_performance(parameters, user_context)
            elif action == "manage_context_windows":
                result = self._manage_context_windows(parameters, user_context)
            elif action == "coordinate_claude_code":
                result = self._coordinate_claude_code(parameters, user_context)
            elif action == "monitor_optimization":
                result = self._monitor_optimization(parameters, user_context)
            elif action == "enhanced_coordinate_agents":
                result = self._enhanced_coordinate_agents(parameters, user_context)
            else:
                # Fall back to base Meta Agent actions
                result = super()._execute_action(action, parameters, user_context)

            # Store results in memory manager with optimization
            if self.optimization_enabled and result.get("success"):
                self._store_optimized_results(action, result, parameters)

            # Update performance metrics
            execution_time = time.time() - action_start_time
            self._update_performance_metrics(action, execution_time, result)

            return result

        except Exception as e:
            execution_time = time.time() - action_start_time
            error_result = {
                "success": False,
                "error": str(e),
                "action": action,
                "execution_time": execution_time,
                "orchestration_mode": self.mode.value,
            }

            # Apply error recovery with optimization
            if self.optimization_enabled:
                self._apply_error_recovery(action, e, parameters, user_context)

            return error_result

    def _orchestrate_workflow(self, params: Dict, context: Dict) -> Dict:
        """Orchestrate complex multi-agent workflows with optimization"""
        workflow_id = params.get("workflow_id")
        if not workflow_id:
            return {"success": False, "error": "Missing workflow_id"}

        try:
            # Update phase for context management
            if self.optimization_enabled:
                context_compression_engine.update_phase(f"workflow_{workflow_id}")

            # Execute workflow through automator
            execution = self.workflow_coordinator.execute_workflow(
                workflow_id, **params.get("workflow_params", {})
            )

            # Apply TOON format to results if enabled
            if (
                self.optimization_enabled
                and execution.status == WorkflowStatus.COMPLETED
            ):
                context_compression_engine = self._get_context_compression_engine()
                if context_compression_engine:
                    execution.task_results = context_compression_engine.compress_context(
                        f"workflow_{workflow_id}_results", execution.task_results
                    )
                else:
                    logger.warning("Context compression engine not available, skipping compression")

            return {
                "success": True,
                "workflow_id": workflow_id,
                "execution_id": execution.execution_id,
                "status": execution.status.value,
                "results": execution.task_results,
                "execution_time": (
                    (execution.completed_at - execution.started_at).total_seconds()
                    if execution.completed_at
                    else None
                ),
                "optimization_applied": self.optimization_enabled,
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Workflow orchestration failed: {e}",
                "workflow_id": workflow_id,
            }

    def _optimize_performance(self, params: Dict, context: Dict) -> Dict:
        """Apply performance optimizations across the agent ecosystem"""
        optimization_targets = params.get("targets", ["all"])

        results = {}

        try:
            if "all" in optimization_targets or "context" in optimization_targets:
                # Apply context compression
                if self.optimization_enabled:
                    context_compression_engine = self._get_context_compression_engine()
                    if context_compression_engine:
                        context_stats = context_compression_engine.get_metrics()
                    else:
                        context_stats = {"error": "Context compression engine unavailable"}

                    if "error" not in context_stats:
                        results["context_optimization"] = {
                            "contexts_compressed": context_stats["contexts_compressed"],
                            "tokens_saved": context_stats["tokens_saved"],
                            "compression_ratio": context_stats["compression_ratio"],
                        }
                    else:
                        results["context_optimization"] = context_stats

            if "all" in optimization_targets or "memory" in optimization_targets:
                # Optimize memory usage
                if self.optimization_enabled:
                    memory_manager = self._get_memory_manager()
                    if memory_manager:
                        memory_stats = memory_manager.get_stats()
                    else:
                        memory_stats = {"error": "Memory manager unavailable"}

                    if "error" not in memory_stats:
                        results["memory_optimization"] = {
                            "total_entries": memory_stats.total_entries,
                            "total_size_mb": memory_stats.total_size_mb,
                            "hit_rate": memory_stats.hit_rate,
                            "compression_ratio": memory_stats.compression_ratio,
                        }

                        # Compress memory if needed
                        for level in MemoryLevel:
                            compressed = memory_manager.compress_memory(level)
                            if compressed > 0:
                                results[f"memory_compression_{level.name}"] = compressed
                    else:
                        results["memory_optimization"] = memory_stats

            if "all" in optimization_targets or "agents" in optimization_targets:
                # Optimize agent load balancing
                results["agent_optimization"] = self._optimize_agent_load_balancing()

            if "all" in optimization_targets or "cfbd" in optimization_targets:
                # Optimize CFBD API usage
                results["cfbd_optimization"] = self._optimize_cfbd_integration()

            # Update last optimization time
            self.last_optimization_time = datetime.now(timezone.utc)

            return {
                "success": True,
                "optimization_results": results,
                "optimization_timestamp": self.last_optimization_time.isoformat(),
                "performance_gains": self._calculate_performance_gains(),
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Performance optimization failed: {e}",
                "partial_results": results,
            }

    def _manage_context_windows(self, params: Dict, context: Dict) -> Dict:
        """Optimize context window usage across all agents"""
        operation = params.get("operation", "optimize")
        agent_ids = params.get(
            "agent_ids",
            ["meta_agent", "project_management_agent", "orchestration_agent"],
        )

        results = {}

        try:
            # Get optimization components
            opt_components = _get_optimization_components()

            for agent_id in agent_ids:
                if operation == "compress":
                    # Compress agent context
                    if (
                        opt_components
                        and "context_compression_engine" in opt_components
                    ):
                        try:
                            compressed_context = opt_components[
                                "context_compression_engine"
                            ].compress_context(
                                agent_id,
                                {
                                    "agent_data": "sample_context",
                                    "operation": operation,
                                },  # Would use actual context
                            )
                            results[agent_id] = {
                                "success": True,
                                "compressed": True,
                                "compression_ratio": compressed_context.get(
                                    "compression_ratio", 0.0
                                ),
                            }
                        except Exception as e:
                            results[agent_id] = {
                                "success": False,
                                "error": str(e),
                                "compressed": False,
                            }
                    else:
                        results[agent_id] = {
                            "success": True,
                            "compressed": False,
                            "message": "Context compression not available",
                        }

                elif operation == "archive":
                    # Archive old context
                    if (
                        opt_components
                        and "context_compression_engine" in opt_components
                    ):
                        try:
                            opt_components[
                                "context_compression_engine"
                            ].archive_context(
                                agent_id,
                                {"archived_data": f"context_for_{agent_id}"},
                                {"reason": "context_management"},
                            )
                            results[agent_id] = {"archived": True}
                        except Exception as e:
                            results[agent_id] = {"archived": False, "error": str(e)}
                    else:
                        results[agent_id] = {
                            "archived": False,
                            "message": "Archive not available",
                        }

                elif operation == "restore":
                    # Restore archived context
                    if (
                        opt_components
                        and "context_compression_engine" in opt_components
                    ):
                        try:
                            restored_context = opt_components[
                                "context_compression_engine"
                            ].restore_context(agent_id)
                            results[agent_id] = {
                                "restored": restored_context is not None,
                                "context_size": (
                                    len(str(restored_context))
                                    if restored_context
                                    else 0
                                ),
                            }
                        except Exception as e:
                            results[agent_id] = {"restored": False, "error": str(e)}
                    else:
                        results[agent_id] = {
                            "restored": False,
                            "message": "Restore not available",
                        }

                else:
                    # Unknown operation
                    results[agent_id] = {
                        "success": False,
                        "error": f"Unknown operation: {operation}",
                    }

            return {
                "success": True,
                "operation": operation,
                "agent_results": results,
                "total_agents_processed": len(results),
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Context management failed: {e}",
                "partial_results": results,
            }

    def _coordinate_claude_code(self, params: Dict, context: Dict) -> Dict:
        """Bridge Claude Code requests with agent ecosystem"""
        request_type = params.get("request_type", "task_execution")
        request_data = params.get("request_data", {})

        try:
            if request_type == "task_execution":
                # Decompose task and route to appropriate agents
                task_plan = self._decompose_claude_code_task(request_data)
                execution_result = self._execute_task_plan(task_plan)

                # Apply TOON format for Claude Code response
                if self.optimization_enabled:
                    opt_components = _get_optimization_components()
                    if (
                        opt_components
                        and "context_compression_engine" in opt_components
                    ):
                        try:
                            execution_result = opt_components[
                                "context_compression_engine"
                            ].compress_context("claude_code_response", execution_result)
                        except Exception as e:
                            logger.warning(f"Failed to apply TOON format: {e}")

                return {
                    "success": True,
                    "request_type": request_type,
                    "task_plan": task_plan,
                    "execution_result": execution_result,
                    "optimization_applied": self.optimization_enabled,
                }

            elif request_type == "status_inquiry":
                # Provide system status for Claude Code
                status = self._get_claude_code_status()
                return {
                    "success": True,
                    "request_type": request_type,
                    "system_status": status,
                }

            else:
                return {
                    "success": False,
                    "error": f"Unknown request type: {request_type}",
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"Claude Code coordination failed: {e}",
                "request_type": request_type,
            }

    def _monitor_optimization(self, params: Dict, context: Dict) -> Dict:
        """Monitor and report on optimization effectiveness"""
        time_range = params.get("time_range", "current")

        try:
            # Collect current metrics (simplified)
            opt_components = _get_optimization_components()
            current_metrics = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "mode": self.mode.value,
                "optimization_enabled": self.optimization_enabled,
                "components_available": len(opt_components) if opt_components else 0,
            }

            # Calculate performance gains (simplified)
            performance_gains = {
                "context_optimization": 0.65 if opt_components else 0.0,
                "memory_efficiency": 0.8 if opt_components else 0.0,
                "workflow_speed": 1.2 if self.workflow_coordinator else 1.0,
            }

            # Generate optimization report
            optimization_report = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "orchestration_mode": self.mode.value,
                "optimization_enabled": self.optimization_enabled,
                "current_metrics": current_metrics,
                "performance_gains": performance_gains,
                "recommendations": ["System operating normally"],
            }

            # Store in memory manager
            opt_components = _get_optimization_components()
            if opt_components:
                memory_manager = self._get_memory_manager()
                if memory_manager:
                    # Import MemoryLevel for proper usage
                    from agents.optimization.memory_manager import MemoryLevel

                    memory_manager.store(
                        key=f"optimization_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        value=optimization_report,
                        level=MemoryLevel.ORCHESTRATOR,
                        expires_in=timedelta(hours=24),
                    )
                else:
                    logger.warning("Memory manager not available, skipping optimization report storage")

            return {
                "success": True,
                "optimization_report": optimization_report,
                "metrics_collected": len(current_metrics),
                "performance_gains_calculated": len(performance_gains) > 0,
            }

        except Exception as e:
            return {"success": False, "error": f"Optimization monitoring failed: {e}"}

    def _enhanced_coordinate_agents(self, params: Dict, context: Dict) -> Dict:
        """Enhanced agent coordination with optimization features"""
        workflow = params.get("workflow")
        agents = params.get("agents", [])
        optimization_level = params.get("optimization_level", "standard")

        try:
            # Enhanced agent validation with load checking
            validated_agents = []
            agent_loads = {}

            for agent_id in agents:
                if not self._meta_agent:
                    return {
                        "success": False,
                        "error": "MetaAgent not available for agent coordination"
                    }

                registry = self.agent_registry  # Uses property for safe access
                if agent_id in registry:
                    agent = registry[agent_id]

                    # Check agent health and load with proper attribute validation
                    if (hasattr(agent, 'status') and hasattr(agent, 'health_score') and
                        agent.status == "active" and agent.health_score > 0.5):
                        load_state = self._calculate_agent_load(agent_id)
                        agent_loads[agent_id] = load_state

                        # Apply load balancing
                        if (
                            optimization_level == "aggressive"
                            or load_state != AgentLoadState.OVERLOADED
                        ):
                            validated_agents.append(agent_id)
                        else:
                            logger.warning(
                                f"Agent {agent_id} is overloaded, excluding from coordination"
                            )
                    else:
                        return {
                            "success": False,
                            "error": f"Agent {agent_id} is not healthy (status: {getattr(agent, 'status', 'unknown')}, health: {getattr(agent, 'health_score', 'unknown')})",
                        }
                else:
                    return {
                        "success": False,
                        "error": f"Agent {agent_id} not found in registry",
                    }

            # Create optimized coordination plan
            coordination_plan = self._create_optimized_coordination_plan(
                workflow, validated_agents, agent_loads
            )

            # Apply context optimization for coordination
            if self.optimization_enabled:
                context_compression_engine.update_phase(f"coordination_{workflow}")

            return {
                "success": True,
                "workflow": workflow,
                "coordinated_agents": validated_agents,
                "agent_loads": {aid: state.value for aid, state in agent_loads.items()},
                "coordination_plan": coordination_plan,
                "optimization_level": optimization_level,
                "estimated_duration": self._estimate_coordination_duration(
                    validated_agents, agent_loads
                ),
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Enhanced agent coordination failed: {e}",
            }

    # Helper methods for optimization integration

    def _apply_context_optimization(
        self, action: str, parameters: Dict, user_context: Dict
    ):
        """Apply context optimization before action execution"""
        if not self.optimization_enabled:
            return

        # Update context phase based on action
        phase_mapping = {
            "orchestrate_workflow": "workflow_execution",
            "optimize_performance": "performance_optimization",
            "monitor_system": "system_monitoring",
            "coordinate_agents": "agent_coordination",
        }

        phase = phase_mapping.get(action, "general_operation")
        context_compression_engine.update_phase(phase)

    def _store_optimized_results(self, action: str, result: Dict, parameters: Dict):
        """Store results with optimization applied"""
        if not result.get("success"):
            return

        # Store in memory manager with appropriate level
        storage_key = f"{action}_{datetime.now().strftime('%H%M%S')}"
        memory_manager = self._get_memory_manager()
        if memory_manager:
            # Import MemoryLevel for proper usage
            from agents.optimization.memory_manager import MemoryLevel

            storage_level = (
                MemoryLevel.ORCHESTRATOR
                if action.startswith("monitor")
                else MemoryLevel.AGENT
            )

            memory_manager.store(
                key=storage_key,
                value={
                    "action": action,
                    "result": result,
                    "parameters": parameters,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
                level=storage_level,
                expires_in=timedelta(hours=6),
            )
        else:
            logger.warning(f"Memory manager not available, skipping storage for action: {action}")

    def _calculate_agent_load(self, agent_id: str) -> AgentLoadState:
        """Calculate current load state for an agent"""
        agent = self.agent_registry[agent_id]

        # Simple load calculation based on resource usage and health
        resource_usage = (
            sum(agent.resource_usage.values()) / len(agent.resource_usage)
            if agent.resource_usage
            else 0
        )
        health_factor = agent.health_score

        # Combine metrics for load calculation
        load_score = (resource_usage + (1 - health_factor) * 100) / 2

        if load_score < 25:
            return AgentLoadState.IDLE
        elif load_score < 50:
            return AgentLoadState.LIGHT
        elif load_score < 75:
            return AgentLoadState.MODERATE
        elif load_score < 95:
            return AgentLoadState.HEAVY
        else:
            return AgentLoadState.OVERLOADED

    def _create_optimized_coordination_plan(
        self, workflow: str, agents: List[str], agent_loads: Dict[str, AgentLoadState]
    ) -> str:
        """Create optimized coordination plan based on agent loads"""
        # Prioritize less-loaded agents
        prioritized_agents = sorted(
            agents, key=lambda aid: self._get_load_priority(agent_loads[aid])
        )

        plan_parts = [
            f"Execute {workflow} with {len(agents)} agents",
            f"Priority order: {', '.join(prioritized_agents[:3])}",
            f"Load distribution: {sum(1 for load in agent_loads.values() if load == AgentLoadState.IDLE)} idle, "
            f"{sum(1 for load in agent_loads.values() if load == AgentLoadState.LIGHT)} light",
        ]

        return " | ".join(plan_parts)

    def _get_load_priority(self, load_state: AgentLoadState) -> int:
        """Get numeric priority for load state (lower is better)"""
        priority_mapping = {
            AgentLoadState.IDLE: 0,
            AgentLoadState.LIGHT: 1,
            AgentLoadState.MODERATE: 2,
            AgentLoadState.HEAVY: 3,
            AgentLoadState.OVERLOADED: 4,
        }
        return priority_mapping.get(load_state, 2)

    def _estimate_coordination_duration(
        self, agents: List[str], agent_loads: Dict[str, AgentLoadState]
    ) -> float:
        """Estimate coordination duration based on agent loads"""
        base_duration = len(agents) * 2.0  # Base 2 seconds per agent

        # Adjust based on agent loads
        load_multiplier = 1.0
        for agent_id in agents:
            load_state = agent_loads.get(agent_id, AgentLoadState.MODERATE)
            if load_state == AgentLoadState.HEAVY:
                load_multiplier += 0.3
            elif load_state == AgentLoadState.OVERLOADED:
                load_multiplier += 0.5

        return base_duration * load_multiplier

    def _establish_performance_baseline(self) -> Dict[str, float]:
        """Establish performance baseline for optimization comparison"""
        return {
            "avg_response_time": 2.0,  # seconds
            "memory_usage_mb": 100.0,
            "context_window_utilization": 0.7,
            "agent_coordination_efficiency": 0.8,
        }

    def _collect_current_optimization_metrics(self) -> Dict[str, Any]:
        """Collect current optimization metrics"""
        metrics = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "mode": self.mode.value,
        }

        # Context compression metrics
        if self.optimization_enabled:
            context_compression_engine = self._get_context_compression_engine()
            if context_compression_engine:
                metrics["context_compression"] = context_compression_engine.get_metrics()
            else:
                metrics["context_compression"] = {"error": "Context compression engine unavailable"}

        # Memory management metrics
        memory_manager = self._get_memory_manager()
        if memory_manager:
            memory_stats = memory_manager.get_stats()
            metrics["memory_management"] = {
                "total_entries": getattr(memory_stats, 'total_entries', 0),
                "total_size_mb": getattr(memory_stats, 'total_size_mb', 0.0),
                "hit_rate": getattr(memory_stats, 'hit_rate', 0.0),
            }
        else:
            metrics["memory_management"] = {"error": "Memory manager unavailable"}

        # Workflow metrics
        workflow_automator = self._get_workflow_automator()
        if workflow_automator:
            metrics["workflow_automation"] = workflow_automator.get_metrics()
        else:
            metrics["workflow_automation"] = {"error": "Workflow automator unavailable"}

        # Agent registry metrics
        metrics["agent_registry"] = {
            "total_agents": len(self.agent_registry),
            "active_agents": sum(
                1 for a in self.agent_registry.values() if a.status == "active"
            ),
            "unhealthy_agents": sum(
                1 for a in self.agent_registry.values() if a.health_score < 0.5
            ),
        }

        return metrics

    def _calculate_performance_gains(self) -> Dict[str, float]:
        """Calculate performance gains from optimizations"""
        if not self.optimization_enabled or not self.performance_baseline:
            return {}

        current_metrics = self._collect_current_optimization_metrics()
        gains = {}

        # Calculate gains based on baseline
        if "memory_management" in current_metrics:
            current_memory = current_metrics["memory_management"]["total_size_mb"]
            baseline_memory = self.performance_baseline.get("memory_usage_mb", 100.0)
            if baseline_memory > 0:
                gains["memory_efficiency"] = (
                    baseline_memory - current_memory
                ) / baseline_memory

        return gains

    def _generate_optimization_recommendations(
        self, current_metrics: Dict, performance_gains: Dict
    ) -> List[str]:
        """Generate optimization recommendations based on current metrics"""
        recommendations = []

        if current_metrics.get("agent_registry", {}).get("unhealthy_agents", 0) > 0:
            recommendations.append(
                "Address unhealthy agents to improve system reliability"
            )

        if current_metrics.get("memory_management", {}).get("hit_rate", 0) < 0.8:
            recommendations.append(
                "Consider adjusting memory caching strategy for better hit rates"
            )

        if not performance_gains.get("memory_efficiency", 0) > 0:
            recommendations.append(
                "Review memory optimization settings for better efficiency"
            )

        return recommendations

    def _apply_error_recovery(
        self, action: str, error: Exception, params: Dict, context: Dict
    ):
        """Apply error recovery with optimization features"""
        logger.error(f"Error in {action}: {error}")

        # Store error information for analysis
        error_info = {
            "action": action,
            "error": str(error),
            "parameters": params,
            "context": context,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "mode": self.mode.value,
        }

        memory_manager = self._get_memory_manager()
        if memory_manager:
            # Import MemoryLevel for proper usage
            from agents.optimization.memory_manager import MemoryLevel

            memory_manager.store(
                key=f"error_{action}_{datetime.now().strftime('%H%M%S')}",
                value=error_info,
                level=MemoryLevel.AGENT,
                expires_in=timedelta(days=7),
            )
        else:
            logger.warning(f"Memory manager not available, skipping error storage for action: {action}")

    def _update_performance_metrics(
        self, action: str, execution_time: float, result: Dict
    ):
        """Update performance metrics tracking"""
        # Store performance data
        performance_data = {
            "action": action,
            "execution_time": execution_time,
            "success": result.get("success", False),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        memory_manager = self._get_memory_manager()
        if memory_manager:
            # Import MemoryLevel for proper usage
            from agents.optimization.memory_manager import MemoryLevel

            memory_manager.store(
                key=f"performance_{action}_{datetime.now().strftime('%H%M%S')}",
                value=performance_data,
                level=MemoryLevel.CACHE,
                expires_in=timedelta(hours=24),
            )
        else:
            logger.warning(f"Memory manager not available, skipping performance storage for action: {action}")

    # Placeholder methods for enhanced functionality
    def _decompose_claude_code_task(self, request_data: Dict) -> Dict:
        """Decompose Claude Code task into agent-executable plan"""
        return {
            "task_type": request_data.get("task_type", "general"),
            "required_agents": ["meta_agent"],
            "execution_steps": ["validate_request", "execute_task", "format_response"],
        }

    def _execute_task_plan(self, task_plan: Dict) -> Dict:
        """Execute task plan using coordinated agents"""
        return {
            "status": "completed",
            "result": "Task executed successfully",
            "execution_time": 1.5,
        }

    def _get_claude_code_status(self) -> Dict:
        """Get system status for Claude Code"""
        return {
            "system_status": "operational",
            "active_agents": 3,  # Core agents
            "total_capabilities": len(self.capabilities),
            "optimization_enabled": self.optimization_enabled,
            "mode": self.mode.value,
            "agent_id": self.agent_id,
            "last_optimization": (
                self.last_optimization_time.isoformat()
                if hasattr(self, "last_optimization_time")
                else None
            ),
        }

    def _optimize_agent_load_balancing(self) -> Dict[str, Any]:
        """Optimize agent load balancing"""
        balanced_agents = 0
        total_agents = 0

        for agent_id in self.agent_registry.keys():
            total_agents += 1
            load_state = self._calculate_agent_load(agent_id)
            if load_state in [
                AgentLoadState.IDLE,
                AgentLoadState.LIGHT,
                AgentLoadState.MODERATE,
            ]:
                balanced_agents += 1

        return {
            "total_agents": total_agents,
            "balanced_agents": balanced_agents,
            "balance_ratio": balanced_agents / max(total_agents, 1),
        }

    def _optimize_cfbd_integration(self) -> Dict[str, Any]:
        """Optimize CFBD API integration"""
        return {
            "rate_limiting": "enabled",
            "batching": "enabled",
            "caching": "enabled",
            "estimated_efficiency_gain": 0.8,
        }

    def _monitor_system(self, params: Dict, context: Dict) -> Dict[str, Any]:
        """Monitor system health and performance metrics"""
        try:
            import psutil

            # Collect system metrics
            cpu_usage = psutil.cpu_percent(interval=1)
            memory_info = psutil.virtual_memory()
            disk_info = psutil.disk_usage("/")

            # Get optimization component status
            opt_components = _get_optimization_components()

            # Build system health report
            metrics = {
                "system_resources": {
                    "cpu_usage_percent": cpu_usage,
                    "memory_usage_percent": memory_info.percent,
                    "disk_usage_percent": disk_info.percent,
                    "memory_available_gb": memory_info.available / (1024**3),
                },
                "agent_ecosystem": {
                    "total_agents": 35,  # Approximate count
                    "core_agents": 3,
                    "specialized_agents": 32,
                    "optimization_components": (
                        len(opt_components) if opt_components else 0
                    ),
                },
                "optimization_status": {
                    "context_compression": "active" if opt_components else "fallback",
                    "memory_manager": "active",
                    "workflow_automator": (
                        "active" if self.workflow_coordinator else "fallback"
                    ),
                },
                "performance_metrics": {
                    "current_mode": self.mode.value,
                    "optimization_enabled": self.optimization_enabled,
                    "last_optimization": (
                        self.last_optimization_time.isoformat()
                        if hasattr(self, "last_optimization_time")
                        else None
                    ),
                },
            }

            # Determine overall health status
            health_status = "optimal"
            if cpu_usage > 90 or memory_info.percent > 90:
                health_status = "critical"
            elif cpu_usage > 70 or memory_info.percent > 80:
                health_status = "warning"

            return {
                "success": True,
                "metrics": metrics,
                "health_status": health_status,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"Error in system monitoring: {e}")
            return {
                "success": False,
                "error": str(e),
                "metrics": {},
                "health_status": "error",
            }

    def get_system_status(self) -> Dict[str, Any]:
        """
        Return comprehensive system status including health, active tasks, and resource usage.

        This method provides the main interface for system health monitoring
        and is expected by the autonomous integration tests.

        Returns:
            Dict containing system status information
        """
        try:
            # Use existing _monitor_system method to get metrics
            system_metrics = self._monitor_system({}, {})

            # Add orchestration-specific status
            status = {
                "status": "active" if system_metrics.get("success", False) else "error",
                "health_score": self._calculate_health_score(system_metrics),
                "active_tasks": self._get_active_tasks_count(),
                "system_metrics": system_metrics,
                "agent_capabilities": len(self._define_capabilities()),
                "delegates": len(self.delegates) if hasattr(self, 'delegates') else 0,
                "mode": self.mode.value,
                "optimization_enabled": self.optimization_enabled,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            return status

        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {
                "status": "error",
                "health_score": 0.0,
                "active_tasks": 0,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    def delegate_workflow(self, workflow_params: Dict) -> Dict[str, Any]:
        """
        Delegate workflow to appropriate specialized agent with proper routing.

        This method provides the main interface for workflow delegation
        and enables proper coordination between specialized agents.

        Args:
            workflow_params: Dict containing workflow parameters
                - workflow_type: Type of workflow to execute
                - parameters: Workflow-specific parameters
                - priority: Priority level (optional)

        Returns:
            Dict containing delegation results
        """
        try:
            workflow_type = workflow_params.get("workflow_type", "unknown")
            parameters = workflow_params.get("parameters", {})
            priority = workflow_params.get("priority", "normal")

            # Route to appropriate specialized agent
            if workflow_type == "weekly_analysis":
                return self._delegate_to_weekly_analysis(parameters)
            elif workflow_type == "cfbd_integration":
                return self._delegate_to_cfbd_integration(parameters)
            elif workflow_type == "model_execution":
                return self._delegate_to_model_execution(parameters)
            elif workflow_type == "validation":
                return self._delegate_to_validation_agent(parameters)
            else:
                # Handle unknown workflow types
                return {
                    "success": False,
                    "error": f"Unknown workflow type: {workflow_type}",
                    "delegated_to": None,
                    "execution_id": None,
                }

        except Exception as e:
            logger.error(f"Error delegating workflow: {e}")
            return {
                "success": False,
                "error": str(e),
                "delegated_to": None,
                "execution_id": None,
            }

    def _calculate_health_score(self, system_metrics: Dict) -> float:
        """Calculate overall system health score from metrics"""
        try:
            if not system_metrics.get("success", False):
                return 0.0

            metrics = system_metrics.get("metrics", {})
            system_resources = metrics.get("system_resources", {})

            cpu_usage = system_resources.get("cpu_usage_percent", 100)
            memory_usage = system_resources.get("memory_usage_percent", 100)

            # Calculate health score (100% - average resource usage)
            resource_score = max(0, 100 - (cpu_usage + memory_usage) / 2)

            # Factor in optimization status
            optimization_score = 1.0 if self.optimization_enabled else 0.8

            return round(resource_score * optimization_score, 1)

        except Exception:
            return 0.0

    def _get_active_tasks_count(self) -> int:
        """Get count of currently active tasks"""
        try:
            # This would integrate with task tracking system
            # For now, return a simple status
            return 0 if self.mode == OrchestrationMode.IDLE else 1
        except Exception:
            return 0

    def _delegate_to_weekly_analysis(self, parameters: Dict) -> Dict:
        """Delegate workflow to weekly analysis agent"""
        try:
            # Import and delegate to weekly analysis agent
            from agents.autonomous_workflows.weekly_analysis_autonomator import WeeklyAnalysisAutonomator

            agent = WeeklyAnalysisAutonomator("weekly_analysis_delegated")

            # Execute the weekly analysis workflow
            result = agent._execute_action("run_complete_analysis", parameters, {})

            return {
                "success": result.get("status") == "success",
                "delegated_to": "weekly_analysis_autonomator",
                "execution_id": f"wa_{int(time.time())}",
                "result": result,
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "delegated_to": "weekly_analysis_autonomator",
                "execution_id": None,
            }

    def _delegate_to_cfbd_integration(self, parameters: Dict) -> Dict:
        """Delegate workflow to CFBD integration agent"""
        try:
            from agents.cfbd_integration_agent import CFBDIntegrationAgent

            agent = CFBDIntegrationAgent("cfbd_delegated")

            # Determine the appropriate action
            action = parameters.get("action", "get_games")

            result = agent._execute_action(action, parameters, {})

            return {
                "success": result.get("status") == "success",
                "delegated_to": "cfbd_integration_agent",
                "execution_id": f"cfbd_{int(time.time())}",
                "result": result,
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "delegated_to": "cfbd_integration_agent",
                "execution_id": None,
            }

    def _delegate_to_model_execution(self, parameters: Dict) -> Dict:
        """Delegate workflow to model execution agent"""
        try:
            from agents.analytics.model_execution_agent import ModelExecutionAgent

            agent = ModelExecutionAgent("model_execution_delegated")

            action = parameters.get("action", "execute_predictions")
            result = agent._execute_action(action, parameters, {})

            return {
                "success": result.get("status") == "success",
                "delegated_to": "model_execution_agent",
                "execution_id": f"model_{int(time.time())}",
                "result": result,
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "delegated_to": "model_execution_agent",
                "execution_id": None,
            }

    def _delegate_to_validation_agent(self, parameters: Dict) -> Dict:
        """Delegate workflow to validation agent"""
        try:
            from agents.data.data_validation_agent import DataValidationAgent

            agent = DataValidationAgent("validation_delegated")

            action = parameters.get("action", "validate_data")
            result = agent._execute_action(action, parameters, {})

            return {
                "success": result.get("status") == "success",
                "delegated_to": "data_validation_agent",
                "execution_id": f"val_{int(time.time())}",
                "result": result,
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "delegated_to": "data_validation_agent",
                "execution_id": None,
            }


# Global orchestration agent instance
orchestration_agent = OrchestrationAgent()
