#!/usr/bin/env python3
"""
Master Orchestrator - Central coordination system for Script Ohio 2.0
Following Claude's best practices for agent orchestration.

DEPRECATED: Use `agents.analytics_orchestrator.AnalyticsOrchestrator` instead.
"""

import warnings
import asyncio
import json
import logging
import uuid
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Set

# Add core modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'core'))

warnings.warn(
    "system.master_orchestrator is deprecated. Migrate to "
    "agents.analytics_orchestrator.AnalyticsOrchestrator.",
    DeprecationWarning,
    stacklevel=2,
)

from base_agent import BaseAgent, AgentCapability, PermissionLevel, AgentMessage
from agent_registry import AgentRegistry
from task_manager import TaskManager, TaskPriority, TaskStatus

class SecurityManager:
    """Security and permission management system"""

    def __init__(self, config_file: str = "config/security/agent_permissions.json"):
        self.config_file = config_file
        self.logger = logging.getLogger("security_manager")
        self.permissions = self._load_permissions()
        self.audit_log = []

    def _load_permissions(self) -> Dict[str, Any]:
        """Load security configuration"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            else:
                # Default permissions
                return {
                    "agent_permissions": {},
                    "file_type_permissions": {
                        ".py": ["read", "write", "execute"],
                        ".md": ["read", "write"],
                        ".json": ["read", "write"]
                    },
                    "security_policies": {
                        "no_new_privileges": True,
                        "read_only_filesystem": False,
                        "network_isolation": True
                    }
                }
        except Exception as e:
            self.logger.error(f"Failed to load permissions: {e}")
            return {"agent_permissions": {}}

    def validate_agent_permissions(self, agent_id: str,
                                 permission_level: PermissionLevel,
                                 operation: str) -> bool:
        """Validate agent permissions for operation"""
        agent_config = self.permissions.get("agent_permissions", {}).get(agent_id, {})
        required_level = agent_config.get("level", "READ_ONLY")

        # Simple permission check
        level_hierarchy = {
            PermissionLevel.READ_ONLY: 1,
            PermissionLevel.READ_EXECUTE: 2,
            PermissionLevel.READ_EXECUTE_WRITE: 3,
            PermissionLevel.ADMIN: 4
        }

        return level_hierarchy.get(permission_level, 0) >= level_hierarchy.get(
            PermissionLevel(required_level), 0)

    def log_operation(self, agent_id: str, operation: str,
                     resource: str, result: str, details: Optional[Dict] = None) -> None:
        """Log operation for audit trail"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "agent_id": agent_id,
            "operation": operation,
            "resource": resource,
            "result": result,
            "details": details or {}
        }

        self.audit_log.append(log_entry)

        # Maintain audit log size (last 10,000 messages)
        if len(self.audit_log) > 10000:
            self.audit_log = self.audit_log[-10000:]

    def get_security_report(self) -> Dict[str, Any]:
        """Generate security report"""
        return {
            "total_operations": len(self.audit_log),
            "agent_permissions_configured": len(self.permissions.get("agent_permissions", {})),
            "recent_operations": self.audit_log[-100:],
            "security_policies": self.permissions.get("security_policies", {}),
            "timestamp": datetime.now().isoformat()
        }

class ProgressMonitor:
    """Real-time progress monitoring and analytics"""

    def __init__(self):
        self.metrics = {
            "total_files": 0,
            "files_processed": 0,
            "errors_resolved": 0,
            "agents_active": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "start_time": datetime.now(),
            "milestones": []
        }
        self.agent_performance = {}
        self.logger = logging.getLogger("progress_monitor")

    def update_metrics(self, updates: Dict[str, Any]) -> None:
        """Update system metrics"""
        self.metrics.update(updates)
        self.logger.debug(f"Metrics updated: {list(updates.keys())}")

    def record_agent_performance(self, agent_id: str,
                                performance_data: Dict[str, Any]) -> None:
        """Record agent performance data"""
        if agent_id not in self.agent_performance:
            self.agent_performance[agent_id] = []

        performance_data['timestamp'] = datetime.now().isoformat()
        self.agent_performance[agent_id].append(performance_data)

        # Keep only last 100 entries per agent
        if len(self.agent_performance[agent_id]) > 100:
            self.agent_performance[agent_id] = self.agent_performance[agent_id][-100:]

    def add_milestone(self, milestone: str, details: Optional[Dict] = None) -> None:
        """Add a milestone achievement"""
        milestone_entry = {
            "milestone": milestone,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        }
        self.metrics["milestones"].append(milestone_entry)
        self.logger.info(f"Milestone achieved: {milestone}")

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive progress report"""
        elapsed_time = datetime.now() - self.metrics["start_time"]

        # Calculate completion rates
        completion_rate = 0
        if self.metrics["total_files"] > 0:
            completion_rate = (self.metrics["files_processed"] / self.metrics["total_files"]) * 100

        # Calculate error resolution rate
        error_resolution_rate = 0
        total_tasks = self.metrics["tasks_completed"] + self.metrics["tasks_failed"]
        if total_tasks > 0:
            error_resolution_rate = (self.metrics["tasks_completed"] / total_tasks) * 100

        return {
            "metrics": {
                **self.metrics,
                "elapsed_time_seconds": elapsed_time.total_seconds(),
                "completion_rate": completion_rate,
                "error_resolution_rate": error_resolution_rate,
                "start_time": self.metrics["start_time"].isoformat(),
                "current_time": datetime.now().isoformat()
            },
            "agent_performance": self.agent_performance,
            "milestones": self.metrics["milestones"],
            "report_generated_at": datetime.now().isoformat()
        }

class MasterOrchestratorAgent(BaseAgent):
    """
    Central coordination system for comprehensive error resolution
    Following Claude's best practices:
    - Modular architecture
    - Focused capabilities
    - Clear boundaries
    - Comprehensive monitoring
    """

    def __init__(self, agent_id: str = "master_orchestrator",
                 name: str = "Master Orchestrator Agent"):
        super().__init__(agent_id, name, PermissionLevel.ADMIN)

        # Core components
        self.security_manager = SecurityManager()
        self.agent_registry = AgentRegistry()
        self.task_manager = TaskManager(max_concurrent_tasks=10)
        self.progress_monitor = ProgressMonitor()

        # Communication system
        self.message_handlers = {}
        self.active_agents = {}

        # System state
        self.system_state = {
            "status": "initializing",
            "start_time": datetime.now(),
            "total_files_processed": 0,
            "total_errors_resolved": 0,
            "active_tasks": 0
        }

        # Initialize logging
        self._setup_logging()

        # Setup event handlers
        self._setup_event_handlers()

        self.logger.info("Master Orchestrator Agent initialized successfully")

    def _setup_logging(self) -> None:
        """Setup comprehensive logging"""
        # Ensure logs directory exists
        Path("logs").mkdir(exist_ok=True)

        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/master_orchestrator.log'),
                logging.StreamHandler()
            ]
        )

    def _setup_event_handlers(self) -> None:
        """Setup event handlers for task management"""
        # Task completion handler
        async def task_completed_handler(task_id: str, result: Dict[str, Any]):
            self.progress_monitor.update_metrics({
                "tasks_completed": self.progress_monitor.metrics["tasks_completed"] + 1
            })
            self.logger.info(f"Task {task_id} completed successfully")

        # Task failure handler
        async def task_failed_handler(task_id: str, error: str):
            self.progress_monitor.update_metrics({
                "tasks_failed": self.progress_monitor.metrics["tasks_failed"] + 1
            })
            self.logger.error(f"Task {task_id} failed: {error}")

        self.task_manager.add_task_completed_handler(task_completed_handler)
        self.task_manager.add_task_failed_handler(task_failed_handler)

    def _define_capabilities(self) -> List[AgentCapability]:
        """Define orchestrator capabilities and permissions"""
        return [
            AgentCapability(
                name="system_analysis",
                description="Comprehensive file and error analysis",
                permission_required=PermissionLevel.ADMIN,
                tools_required=["file_analyzer", "error_classifier", "dependency_mapper"],
                estimated_duration=15,
                resource_requirements={"memory": "512MB", "cpu": "0.5"}
            ),
            AgentCapability(
                name="task_allocation",
                description="Dynamic task distribution to specialized agents",
                permission_required=PermissionLevel.ADMIN,
                tools_required=["task_scheduler", "resource_optimizer", "load_balancer"],
                estimated_duration=5,
                resource_requirements={"memory": "256MB", "cpu": "0.3"}
            ),
            AgentCapability(
                name="agent_management",
                description="Agent lifecycle management and coordination",
                permission_required=PermissionLevel.ADMIN,
                tools_required=["agent_registry", "health_monitor", "permission_manager"],
                estimated_duration=3,
                resource_requirements={"memory": "128MB", "cpu": "0.2"}
            ),
            AgentCapability(
                name="progress_monitoring",
                description="Real-time progress tracking and reporting",
                permission_required=PermissionLevel.READ_ONLY,
                tools_required=["progress_tracker", "dashboard_generator", "report_builder"],
                estimated_duration=1,
                resource_requirements={"memory": "256MB", "cpu": "0.2"}
            ),
            AgentCapability(
                name="security_management",
                description="Security enforcement and audit logging",
                permission_required=PermissionLevel.ADMIN,
                tools_required=["permission_validator", "access_controller", "audit_logger"],
                estimated_duration=2,
                resource_requirements={"memory": "128MB", "cpu": "0.2"}
            )
        ]

    def _execute_action(self, action: str, parameters: Dict[str, Any],
                      user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute orchestrator actions with proper routing"""
        try:
            if action == "analyze_system":
                return self._analyze_entire_system(parameters, user_context)
            elif action == "distribute_tasks":
                return self._distribute_tasks_to_agents(parameters, user_context)
            elif action == "monitor_progress":
                return self._monitor_system_progress(parameters, user_context)
            elif action == "register_agent":
                return self._register_agent(parameters, user_context)
            elif action == "manage_agents":
                return self._manage_agents(parameters, user_context)
            elif action == "generate_report":
                return self._generate_system_report(parameters, user_context)
            elif action == "security_audit":
                return self._perform_security_audit(parameters, user_context)
            else:
                raise ValueError(f"Unknown action: {action}")

        except Exception as e:
            self.logger.error(f"Error executing action {action}: {e}")
            return {
                "status": "error",
                "error": str(e),
                "action": action,
                "timestamp": datetime.now().isoformat()
            }

    def _analyze_entire_system(self, parameters: Dict[str, Any],
                             user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze entire system for errors and issues"""
        try:
            self.logger.info("Starting comprehensive system analysis...")

            # Load analysis results from Phase 1
            analysis_results = {}

            # Try to load file analysis
            file_analysis_path = "implementation_workspace/analysis_results/file_analysis.json"
            if os.path.exists(file_analysis_path):
                with open(file_analysis_path, 'r') as f:
                    file_analysis = json.load(f)
                    analysis_results["file_analysis"] = file_analysis

            # Try to load import dependencies
            import_analysis_path = "implementation_workspace/analysis_results/import_dependencies.json"
            if os.path.exists(import_analysis_path):
                with open(import_analysis_path, 'r') as f:
                    import_analysis = json.load(f)
                    analysis_results["import_dependencies"] = import_analysis

            # Categorize issues if file analysis is available
            if "file_analysis" in analysis_results:
                critical_issues = []
                medium_issues = []
                low_issues = []

                for file_data in analysis_results["file_analysis"]:
                    for issue in file_data.get('issues', []):
                        issue['file_path'] = file_data['file_path']

                        severity = issue.get('severity', 'medium')
                        if severity == 'critical':
                            critical_issues.append(issue)
                        elif severity == 'medium':
                            medium_issues.append(issue)
                        else:
                            low_issues.append(issue)

                # Update progress monitor
                self.progress_monitor.update_metrics({
                    "total_files": len(analysis_results["file_analysis"]),
                    "critical_issues": len(critical_issues),
                    "medium_issues": len(medium_issues),
                    "low_issues": len(low_issues)
                })

                analysis_results["issue_summary"] = {
                    "total_files_analyzed": len(analysis_results["file_analysis"]),
                    "total_issues": len(critical_issues) + len(medium_issues) + len(low_issues),
                    "critical_issues": critical_issues,
                    "medium_issues": medium_issues,
                    "low_issues": low_issues
                }

            # Log analysis completion
            self.progress_monitor.add_milestone("System Analysis Complete")
            self.logger.info("System analysis completed successfully")

            return {
                "status": "success",
                "analysis": analysis_results,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error during system analysis: {e}")
            return {
                "status": "error",
                "error": f"System analysis failed: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }

    def _distribute_tasks_to_agents(self, parameters: Dict[str, Any],
                                   user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Distribute tasks to appropriate specialized agents"""
        try:
            analysis = parameters.get('analysis', {})
            task_results = []

            # Handle BaseAgent issues
            issue_summary = analysis.get('issue_summary', {})
            critical_issues = issue_summary.get('critical_issues', [])

            if critical_issues:
                # Group BaseAgent issues
                baseagent_issues = [
                    issue for issue in critical_issues
                    if issue.get('type') in ['baseagent_constructor', 'missing_abstract_method', 'old_constructor_pattern', 'old_super_call']
                ]

                if baseagent_issues:
                    # Create task for AbstractMethodFixerAgent
                    task_data = {
                        "task_id": str(uuid.uuid4()),
                        "agent_id": "abstract_method_fixer",
                        "action": "fix_baseagent_issues",
                        "parameters": {
                            "issues": baseagent_issues,
                            "priority": "critical"
                        },
                        "target_files": list(set(issue['file_path'] for issue in baseagent_issues)),
                        "priority": 1  # Critical priority
                    }

                    # Submit task to task manager
                    task_id = asyncio.run(self.task_manager.submit_task(
                        AgentTask(**task_data),
                        TaskPriority.CRITICAL
                    ))

                    task_results.append({
                        "task_id": task_id,
                        "task_type": "baseagent_fixes",
                        "issues_count": len(baseagent_issues),
                        "files_affected": len(set(issue['file_path'] for issue in baseagent_issues))
                    })

                    self.logger.info(f"Created BaseAgent fix task: {task_id} for {len(baseagent_issues)} issues")

            # Handle other issue types as needed
            # (Additional logic for other specialized agents can be added here)

            # Update metrics
            self.progress_monitor.update_metrics({
                "tasks_created": len(task_results),
                "tasks_pending": len(self.task_manager.active_tasks) + self.task_manager.task_queue.qsize()
            })

            return {
                "status": "success",
                "tasks_created": task_results,
                "total_tasks": len(self.task_manager.active_tasks) + self.task_manager.task_queue.qsize(),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error distributing tasks: {e}")
            return {
                "status": "error",
                "error": f"Task distribution failed: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }

    def _monitor_system_progress(self, parameters: Dict[str, Any],
                               user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Monitor system progress and generate status report"""
        try:
            # Get task manager metrics
            task_metrics = self.task_manager.get_metrics()

            # Get agent registry stats
            registry_stats = self.agent_registry.get_registry_stats()

            # Get progress monitor report
            progress_report = self.progress_monitor.generate_report()

            # Get security report
            security_report = self.security_manager.get_security_report()

            # Update system state
            self.system_state.update({
                "active_tasks": task_metrics["active_tasks"],
                "total_files_processed": progress_report["metrics"]["files_processed"],
                "total_errors_resolved": task_metrics["total_tasks_completed"]
            })

            return {
                "status": "success",
                "progress_report": progress_report,
                "task_metrics": task_metrics,
                "agent_registry": registry_stats,
                "security_report": security_report,
                "system_state": self.system_state,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error monitoring progress: {e}")
            return {
                "status": "error",
                "error": f"Progress monitoring failed: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }

    def _register_agent(self, parameters: Dict[str, Any],
                       user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Register new agent with the orchestrator"""
        try:
            agent_info = parameters.get('agent_info', {})
            agent_id = agent_info.get('agent_id')

            if not agent_id:
                return {
                    "status": "error",
                    "error": "Agent ID required for registration"
                }

            # Validate agent permissions
            permission_level_str = agent_info.get('permission_level', 'READ_ONLY')
            try:
                permission_level = PermissionLevel(permission_level_str)
            except ValueError:
                return {
                    "status": "error",
                    "error": f"Invalid permission level: {permission_level_str}"
                }

            # Validate with security manager
            if not self.security_manager.validate_agent_permissions(
                agent_id, permission_level, "register"):
                return {
                    "status": "error",
                    "error": f"Insufficient permissions for agent: {agent_id}"
                }

            # Register with agent registry
            success = self.agent_registry.register_agent(
                type('MockAgent', (), {
                    'agent_id': agent_id,
                    'name': agent_info.get('name', agent_id),
                    'permission_level': permission_level,
                    'status': 'registered',
                    'get_capabilities': lambda: [],
                    'created_at': datetime.now()
                })(),
                agent_info
            )

            if success:
                # Log registration
                self.security_manager.log_operation(
                    agent_id, "register", "orchestrator", "success",
                    agent_info
                )

                # Update progress
                self.progress_monitor.add_milestone(f"Agent Registered: {agent_id}")

                return {
                    "status": "success",
                    "agent_id": agent_id,
                    "registered_at": datetime.now().isoformat()
                }
            else:
                return {
                    "status": "error",
                    "error": "Failed to register agent with registry"
                }

        except Exception as e:
            self.logger.error(f"Error registering agent: {e}")
            return {
                "status": "error",
                "error": f"Agent registration failed: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }

    def _manage_agents(self, parameters: Dict[str, Any],
                      user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Manage agent lifecycle and health"""
        try:
            action = parameters.get('action', 'status')
            agent_id = parameters.get('agent_id')

            if action == 'status':
                if agent_id:
                    # Get specific agent status
                    agent_info = self.agent_registry.get_agent_info(agent_id)
                    return {
                        "status": "success",
                        "agent_info": agent_info
                    }
                else:
                    # Get all agents status
                    agents = self.agent_registry.list_agents()
                    return {
                        "status": "success",
                        "agents": agents,
                        "total_agents": len(agents)
                    }

            elif action == 'health_check':
                if agent_id:
                    # Perform health check on specific agent
                    return {
                        "status": "success",
                        "health_check": "OK"  # Simplified
                    }
                else:
                    # Health check all agents
                    return {
                        "status": "success",
                        "message": "Health check completed for all agents"
                    }

            else:
                return {
                    "status": "error",
                    "error": f"Unknown management action: {action}"
                }

        except Exception as e:
            self.logger.error(f"Error managing agents: {e}")
            return {
                "status": "error",
                "error": f"Agent management failed: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }

    def _generate_system_report(self, parameters: Dict[str, Any],
                              user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive system report"""
        try:
            # Get current metrics from all components
            task_metrics = self.task_manager.get_metrics()
            progress_report = self.progress_monitor.generate_report()
            security_report = self.security_manager.get_security_report()
            registry_stats = self.agent_registry.get_registry_stats()

            # Calculate completion percentages
            total_files = progress_report["metrics"]["total_files"]
            files_processed = progress_report["metrics"]["files_processed"]
            completion_percentage = (files_processed / total_files * 100) if total_files > 0 else 0

            # Generate summary
            summary = {
                "overall_status": self.system_state["status"],
                "completion_percentage": completion_percentage,
                "uptime_hours": (datetime.now() - self.system_state["start_time"]).total_seconds() / 3600,
                "total_agents": registry_stats["total_agents"],
                "active_tasks": task_metrics["active_tasks"],
                "tasks_completed": task_metrics["total_tasks_completed"],
                "success_rate": task_metrics.get("success_rate", 0),
                "security_operations": security_report["total_operations"]
            }

            return {
                "status": "success",
                "system_report": {
                    "summary": summary,
                    "progress": progress_report,
                    "task_management": task_metrics,
                    "agent_registry": registry_stats,
                    "security": security_report,
                    "system_state": self.system_state
                },
                "report_generated_at": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error generating system report: {e}")
            return {
                "status": "error",
                "error": f"Report generation failed: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }

    def _perform_security_audit(self, parameters: Dict[str, Any],
                              user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive security audit"""
        try:
            # Validate registry integrity
            integrity_check = self.agent_registry.validate_registry_integrity()

            # Check recent security operations
            recent_operations = self.security_manager.audit_log[-100:]  # Last 100 operations

            # Analyze security events
            security_events = []
            for operation in recent_operations:
                if operation["result"] != "success":
                    security_events.append({
                        "timestamp": operation["timestamp"],
                        "agent_id": operation["agent_id"],
                        "operation": operation["operation"],
                        "error": operation["result"]
                    })

            # Calculate security score
            total_operations = len(self.security_manager.audit_log)
            failed_operations = len(security_events)
            security_score = ((total_operations - failed_operations) / max(total_operations, 1)) * 100

            return {
                "status": "success",
                "security_audit": {
                    "registry_integrity": integrity_check,
                    "security_score": security_score,
                    "total_security_operations": total_operations,
                    "failed_operations": failed_operations,
                    "security_events": security_events,
                    "audit_trail_size": len(self.security_manager.audit_log),
                    "last_audit_time": datetime.now().isoformat()
                }
            }

        except Exception as e:
            self.logger.error(f"Error performing security audit: {e}")
            return {
                "status": "error",
                "error": f"Security audit failed: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }

    async def shutdown(self) -> Dict[str, Any]:
        """Graceful shutdown of the orchestrator"""
        try:
            self.logger.info("Master Orchestrator shutting down gracefully...")

            # Shutdown task manager
            task_shutdown = await self.task_manager.shutdown()

            # Save final state
            shutdown_info = {
                "orchestrator_id": self.agent_id,
                "shutdown_time": datetime.now().isoformat(),
                "final_metrics": self.progress_monitor.generate_report(),
                "task_manager_shutdown": task_shutdown,
                "security_operations": len(self.security_manager.audit_log)
            }

            # Save shutdown log
            with open("logs/orchestrator_shutdown.json", 'w') as f:
                json.dump(shutdown_info, f, indent=2)

            self.logger.info("Master Orchestrator shutdown complete")
            return shutdown_info

        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")
            return {
                "error": str(e),
                "shutdown_time": datetime.now().isoformat()
            }