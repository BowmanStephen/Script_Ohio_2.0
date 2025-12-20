#!/usr/bin/env python3
"""
Quality Orchestration Agent - Master Quality System Coordinator
Coordinates all quality assurance activities, testing, and continuous improvement
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import uuid
from collections import defaultdict, deque

from ..core.event_stream_manager import (
    EventStreamManager, Event, EventPriority, EventSubscription
)
from ..core.enhanced_agent_framework import EnhancedBaseAgent
from .comprehensive_quality_system import (
    ComprehensiveQualitySystem, QualityLevel, ValidationSeverity, TestCategory
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QualityOrchestrationMode(Enum):
    """Quality orchestration modes"""
    CONTINUOUS = "continuous"      # Continuous monitoring and validation
    SCHEDULED = "scheduled"        # Scheduled quality assessments
    ON_DEMAND = "on_demand"        # Triggered on-demand validation
    PRE_DEPLOYMENT = "pre_deployment"  # Pre-deployment quality gates
    POST_DEPLOYMENT = "post_deployment"  # Post-deployment monitoring

class OrchestrationPriority(Enum):
    """Orchestration task priority"""
    CRITICAL = "critical"      # System-breaking issues
    HIGH = "high"              # Important quality concerns
    NORMAL = "normal"          # Routine quality tasks
    LOW = "low"                # Nice-to-have improvements

@dataclass
class QualityOrchestrationTask:
    """Individual quality orchestration task"""
    task_id: str
    name: str
    description: str
    mode: QualityOrchestrationMode
    priority: OrchestrationPriority
    components: Set[str] = field(default_factory=set)
    quality_gates: List[str] = field(default_factory=list)
    schedule: Optional[str] = None  # Cron expression
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_executed: Optional[datetime] = None
    execution_history: deque = field(default_factory=lambda: deque(maxlen=10))
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class QualityOrchestrationPolicy:
    """Quality orchestration policy"""
    policy_id: str
    name: str
    description: str
    conditions: Dict[str, Any] = field(default_factory=dict)
    actions: List[str] = field(default_factory=list)
    auto_execute: bool = True
    priority: OrchestrationPriority = OrchestrationPriority.NORMAL
    enabled: bool = True

class QualityOrchestrationAgent(EnhancedBaseAgent):
    """
    Master quality orchestration agent that coordinates all QA activities
    Integrates with comprehensive quality system, CI/CD pipelines, and monitoring
    """

    def __init__(self, agent_id: str = "quality_orchestration_agent"):
        super().__init__(
            agent_id=agent_id,
            agent_name="Quality Orchestration Agent",
            permission_level=self.PermissionLevel.READ_EXECUTE
        )

        # Orchestration configuration
        self.orchestration_config = {
            "continuous_monitoring": True,
            "auto_healing_enabled": False,
            "max_concurrent_tasks": 5,
            "task_timeout_minutes": 60,
            "quality_gate_enforcement": True,
            "notification_enabled": True,
            "metrics_collection_interval": 300,  # 5 minutes
            "cleanup_retention_days": 30
        }

        # Quality system integration
        self.quality_system: Optional[ComprehensiveQualitySystem] = None

        # Orchestration tasks and policies
        self.orchestration_tasks: Dict[str, QualityOrchestrationTask] = {}
        self.orchestration_policies: Dict[str, QualityOrchestrationPolicy] = {}
        self.active_executions: Dict[str, asyncio.Task] = {}

        # Execution queue and history
        self.execution_queue: deque = deque(maxlen=1000)
        self.execution_history: deque = deque(maxlen=10000)

        # Quality gates and thresholds
        self.quality_gates_status: Dict[str, Dict[str, Any]] = {}
        self.threshold_violations: deque = deque(maxlen=1000)

        # CI/CD integration
        self.cicd_integrations: Dict[str, Dict[str, Any]] = {}
        self.deployment_pipelines: Dict[str, Dict[str, Any]] = {}

        # Event stream integration
        self.event_manager: Optional[EventStreamManager] = None

        # Performance metrics
        self.orchestration_metrics = {
            "tasks_executed": 0,
            "tasks_successful": 0,
            "tasks_failed": 0,
            "quality_gates_passed": 0,
            "quality_gates_failed": 0,
            "auto_heals_applied": 0,
            "average_execution_time_minutes": 0.0,
            "continuous_alerts_generated": 0
        }

        # Background processing
        self.monitoring_task: Optional[asyncio.Task] = None
        self.scheduling_task: Optional[asyncio.Task] = None
        self.cleanup_task: Optional[asyncio.Task] = None

        # Continuous monitoring state
        self.monitoring_state = {
            "last_quality_check": datetime.now(timezone.utc),
            "quality_trend": "stable",
            "active_alerts": set(),
            "health_status": "healthy"
        }

    def _define_capabilities(self) -> List['AgentCapability']:
        """Define quality orchestration capabilities"""
        return [
            self.AgentCapability(
                name="orchestrate_quality_pipeline",
                description="Orchestrate end-to-end quality pipeline with automated gates and policies",
                execution_time_estimate=20.0,
                permission_required=[self.PermissionLevel.READ_EXECUTE],
                tools_required=["pipeline_config", "quality_gates", "execution_mode", "components"],
                returns {"pipeline_status": "string", "quality_score": "float", "gate_results": "dict"},
            ),
            self.AgentCapability(
                name="manage_quality_tasks",
                description="Create, schedule, and manage quality orchestration tasks and policies",
                execution_time_estimate=5.0,
                permission_required=[self.PermissionLevel.READ_EXECUTE],
                tools_required=["task_config", "policy_config", "schedule", "auto_execute"],
                data_access=["task_id": "string", "status": "string", "next_execution": "datetime"]
            ),
            self.AgentCapability(
                name="enforce_quality_gates",
                description="Enforce quality gates for deployments and releases with automated validation",
                execution_time_estimate=10.0,
                permission_required=[self.PermissionLevel.READ_EXECUTE],
                tools_required=["gate_name", "deployment_info", "quality_requirements", "blocking_mode"],
                data_access=["gate_status": "string", "violations": "list", "deployment_approved": "bool"]
            ),
            self.AgentCapability(
                name="coordinate_continuous_monitoring",
                description="Coordinate continuous quality monitoring and automated response to quality issues",
                execution_time_estimate=3.0,
                permission_required=[self.PermissionLevel.READ_EXECUTE],
                tools_required=["monitoring_scope", "alert_thresholds", "auto_heal_policies"],
                returns {"monitoring_status": "string", "active_alerts": "list", "healing_actions": "list"}
            )
        ]

    async def initialize(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Initialize the quality orchestration agent

        Args:
            config: Configuration dictionary

        Returns:
            Initialization status
        """
        try:
            # Update configuration
            if "orchestration" in config:
                self.orchestration_config.update(config["orchestration"])

            # Initialize quality system
            quality_config = config.get("quality", {})
            self.quality_system = ComprehensiveQualitySystem()
            quality_result = await self.quality_system.initialize(quality_config)

            if quality_result["status"] != "success":
                logger.error(f"Failed to initialize quality system: {quality_result['error']}")
                return quality_result

            # Initialize event stream manager
            if "event_stream" in config:
                event_config = config["event_stream"]
                self.event_manager = EventStreamManager(event_config)
                await self.event_manager.initialize()
                await self._setup_orchestration_subscriptions()

            # Initialize orchestration tasks
            await self._initialize_orchestration_tasks(config.get("orchestration_tasks", {}))

            # Initialize orchestration policies
            await self._initialize_orchestration_policies(config.get("orchestration_policies", {}))

            # Initialize CI/CD integrations
            await self._initialize_cicd_integrations(config.get("cicd_integrations", {}))

            # Start background tasks
            if self.orchestration_config["continuous_monitoring"]:
                self.monitoring_task = asyncio.create_task(self._continuous_monitoring_loop())

            self.scheduling_task = asyncio.create_task(self._scheduling_loop())
            self.cleanup_task = asyncio.create_task(self._cleanup_loop())

            logger.info("Quality Orchestration Agent initialized successfully")
            return {
                "status": "success",
                "quality_system_status": quality_result["status"],
                "orchestration_tasks": len(self.orchestration_tasks),
                "orchestration_policies": len(self.orchestration_policies),
                "cicd_integrations": len(self.cicd_integrations),
                "continuous_monitoring": self.orchestration_config["continuous_monitoring"],
                "quality_gate_enforcement": self.orchestration_config["quality_gate_enforcement"]
            }

        except Exception as e:
            logger.error(f"Failed to initialize Quality Orchestration Agent: {e}")
            return {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__
            }

    async def _setup_orchestration_subscriptions(self) -> None:
        """Setup event subscriptions for quality orchestration"""
        # Quality-related events
        quality_subscription = EventSubscription(
            subscriber_id="quality_orchestration",
            event_types={
                "quality.*",
                "validation.*",
                "test.*",
                "deployment.*",
                "ci_cd.*"
            },
            priority_filter={EventPriority.HIGH, EventPriority.CRITICAL}
        )
        await self.event_manager.subscribe_to_events(quality_subscription)

        # System events that might trigger quality checks
        system_subscription = EventSubscription(
            subscriber_id="quality_orchestration_system",
            event_types={
                "system.*",
                "pipeline.*",
                "agent.*",
                "error.*"
            }
        )
        await self.event_manager.subscribe_to_events(system_subscription)

    async def _initialize_orchestration_tasks(self, tasks_config: Dict[str, Any]) -> None:
        """Initialize orchestration tasks"""
        # Default orchestration tasks
        default_tasks = [
            QualityOrchestrationTask(
                task_id="daily_quality_assessment",
                name="Daily Quality Assessment",
                description="Comprehensive daily quality assessment across all components",
                mode=QualityOrchestrationMode.SCHEDULED,
                priority=OrchestrationPriority.NORMAL,
                schedule="0 2 * * *",  # Daily at 2 AM
                components=["all"],
                quality_gates=["code_quality", "test_coverage", "performance", "security"]
            ),
            QualityOrchestrationTask(
                task_id="pre_deployment_validation",
                name="Pre-Deployment Validation",
                description="Quality validation before deployment to production",
                mode=QualityOrchestrationMode.PRE_DEPLOYMENT,
                priority=OrchestrationPriority.HIGH,
                components=["application", "database", "api"],
                quality_gates=["code_quality", "test_coverage", "security", "performance"]
            ),
            QualityOrchestrationTask(
                task_id="post_deployment_monitoring",
                name="Post-Deployment Monitoring",
                description="Quality monitoring after deployment to catch issues early",
                mode=QualityOrchestrationMode.POST_DEPLOYMENT,
                priority=OrchestrationPriority.HIGH,
                components=["production", "monitoring", "alerts"],
                quality_gates=["performance", "reliability", "security"]
            ),
            QualityOrchestrationTask(
                task_id="continuous_monitoring",
                name="Continuous Quality Monitoring",
                description="Real-time monitoring of quality metrics and health",
                mode=QualityOrchestrationMode.CONTINUOUS,
                priority=OrchestrationPriority.NORMAL,
                components=["system", "metrics", "alerts"],
                quality_gates=["performance", "reliability", "security"]
            )
        ]

        # Add default tasks
        for task in default_tasks:
            self.orchestration_tasks[task.task_id] = task

        # Add custom tasks from configuration
        for task_id, task_data in tasks_config.items():
            try:
                task = QualityOrchestrationTask(
                    task_id=task_id,
                    name=task_data.get("name", task_id),
                    description=task_data.get("description", ""),
                    mode=QualityOrchestrationMode(task_data.get("mode", "on_demand")),
                    priority=OrchestrationPriority(task_data.get("priority", "normal")),
                    components=set(task_data.get("components", [])),
                    quality_gates=task_data.get("quality_gates", []),
                    schedule=task_data.get("schedule"),
                    metadata=task_data.get("metadata", {})
                )
                self.orchestration_tasks[task_id] = task
            except Exception as e:
                logger.warning(f"Failed to load orchestration task {task_id}: {e}")

        logger.info(f"Initialized {len(self.orchestration_tasks)} orchestration tasks")

    async def _initialize_orchestration_policies(self, policies_config: Dict[str, Any]) -> None:
        """Initialize orchestration policies"""
        # Default policies
        default_policies = [
            QualityOrchestrationPolicy(
                policy_id="auto_deploy_on_success",
                name="Auto-Deploy on Quality Success",
                description="Automatically deploy if quality gates pass",
                conditions={
                    "quality_score": {"minimum": 0.85},
                    "all_gates_passed": True,
                    "no_critical_issues": True
                },
                actions=["deploy_to_production", "notify_success"],
                auto_execute=True,
                priority=OrchestrationPriority.HIGH
            ),
            QualityOrchestrationPolicy(
                policy_id="rollback_on_failure",
                name="Rollback on Quality Failure",
                description="Automatically rollback if quality gates fail critically",
                conditions={
                    "quality_score": {"maximum": 0.6},
                    "critical_issues": {"minimum": 1},
                    "security_gate_failed": True
                },
                actions=["rollback_deployment", "notify_failure", "create_incident"],
                auto_execute=True,
                priority=OrchestrationPriority.CRITICAL
            ),
            QualityOrchestrationPolicy(
                policy_id="notify_on_degradation",
                name="Notify on Quality Degradation",
                description="Send notifications when quality metrics degrade",
                conditions={
                    "quality_trend": "degrading",
                    "score_change": {"minimum": -0.1}
                },
                actions=["notify_team", "create_alert", "schedule_investigation"],
                auto_execute=True,
                priority=OrchestrationPriority.NORMAL
            )
        ]

        # Add default policies
        for policy in default_policies:
            self.orchestration_policies[policy.policy_id] = policy

        # Add custom policies from configuration
        for policy_id, policy_data in policies_config.items():
            try:
                policy = QualityOrchestrationPolicy(
                    policy_id=policy_id,
                    name=policy_data.get("name", policy_id),
                    description=policy_data.get("description", ""),
                    conditions=policy_data.get("conditions", {}),
                    actions=policy_data.get("actions", []),
                    auto_execute=policy_data.get("auto_execute", False),
                    priority=OrchestrationPriority(policy_data.get("priority", "normal"))
                )
                self.orchestration_policies[policy_id] = policy
            except Exception as e:
                logger.warning(f"Failed to load orchestration policy {policy_id}: {e}")

        logger.info(f"Initialized {len(self.orchestration_policies)} orchestration policies")

    async def _initialize_cicd_integrations(self, cicd_config: Dict[str, Any]) -> None:
        """Initialize CI/CD integrations"""
        # Default CI/CD integrations
        default_integrations = {
            "github_actions": {
                "name": "GitHub Actions",
                "webhook_url": "/webhooks/github-actions",
                "supported_events": ["push", "pull_request", "release"],
                "quality_check_stage": "build",
                "deployment_stage": "deploy",
                "auto_merge_on_success": False
            },
            "jenkins": {
                "name": "Jenkins",
                "webhook_url": "/webhooks/jenkins",
                "supported_events": ["build_complete", "test_complete", "deployment_ready"],
                "quality_check_stage": "test",
                "deployment_stage": "deploy",
                "auto_deploy_on_success": False
            },
            "gitlab_ci": {
                "name": "GitLab CI",
                "webhook_url": "/webhooks/gitlab-ci",
                "supported_events": ["pipeline", "deployment"],
                "quality_check_stage": "test",
                "deployment_stage": "deploy",
                "auto_deploy_on_success": False
            }
        }

        # Add default integrations
        for integration_id, integration_config in default_integrations.items():
            self.cicd_integrations[integration_id] = integration_config

        # Add custom integrations from configuration
        for integration_id, integration_config in cicd_config.items():
            self.cicd_integrations[integration_id] = integration_config

        logger.info(f"Initialized {len(self.cicd_integrations)} CI/CD integrations")

    async def _execute_action(self, action: str, parameters: Dict, user_context: Dict) -> Dict[str, Any]:
        """Execute orchestration agent actions"""
        try:
            if action == "orchestrate_quality_pipeline":
                return await self._orchestrate_quality_pipeline(parameters, user_context)
            elif action == "manage_quality_tasks":
                return await self._manage_quality_tasks(parameters, user_context)
            elif action == "enforce_quality_gates":
                return await self._enforce_quality_gates(parameters, user_context)
            elif action == "coordinate_continuous_monitoring":
                return await self._coordinate_continuous_monitoring(parameters, user_context)
            else:
                raise ValueError(f"Unknown action: {action}")

        except Exception as e:
            logger.error(f"Error executing action '{action}': {e}")
            return {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__,
                "agent_id": self.agent_id
            }

    async def _orchestrate_quality_pipeline(self, parameters: Dict, user_context: Dict) -> Dict[str, Any]:
        """Orchestrate end-to-end quality pipeline"""
        pipeline_config = parameters.get("pipeline_config", {})
        quality_gates = parameters.get("quality_gates", ["all"])
        execution_mode = parameters.get("execution_mode", QualityOrchestrationMode.ON_DEMAND.value)
        components = parameters.get("components", ["all"])

        try:
            # Create orchestration context
            pipeline_id = f"pipeline_{uuid.uuid4().hex[:8]}"
            start_time = time.time()

            # Execute quality validation through quality system
            validation_params = {
                "suite_types": ["all"],
                "target_components": components,
                "quality_gates": True
            }

            validation_result = await self.quality_system._execute_validation_suite(validation_params, {})

            # Process validation results
            if validation_result["status"] == "success":
                quality_score = validation_result["quality_score"]
                validation_results = validation_result["validation_results"]
                gate_violations = validation_result.get("gate_violations", [])
                recommendations = validation_result.get("recommendations", [])

                # Check orchestration policies
                policy_results = await self._evaluate_policies({
                    "quality_score": quality_score,
                    "validation_results": validation_results,
                    "gate_violations": gate_violations,
                    "execution_mode": execution_mode,
                    "components": components
                })

                # Execute policy actions
                actions_taken = []
                if policy_results.get("actions"):
                    actions_taken = await self._execute_policy_actions(policy_results["actions"], pipeline_id)

                # Calculate pipeline status
                pipeline_status = "success" if quality_score >= 0.7 and not gate_violations else "failed"
                if pipeline_status == "failed":
                    # Check if any critical issues
                    critical_issues = [
                        r for r in validation_results
                        if r["status"] == "failed" and self.quality_system.validation_rules.get(r["rule_id"]).severity in [ValidationSeverity.CRITICAL, ValidationSeverity.BLOCKER]
                    ]
                    if critical_issues:
                        pipeline_status = "critical_failure"

                # Record execution
                execution_time = (time.time() - start_time) * 1000
                execution_record = {
                    "pipeline_id": pipeline_id,
                    "status": pipeline_status,
                    "quality_score": quality_score,
                    "execution_time_ms": execution_time,
                    "validation_results": len(validation_results),
                    "gate_violations": len(gate_violations),
                    "actions_taken": actions_taken,
                    "timestamp": datetime.now(timezone.utc)
                }

                self.execution_history.append(execution_record)

                # Update metrics
                self.orchestration_metrics["tasks_executed"] += 1
                if pipeline_status == "success":
                    self.orchestration_metrics["tasks_successful"] += 1
                else:
                    self.orchestration_metrics["tasks_failed"] += 1

                # Publish pipeline completion event
                if self.event_manager:
                    event = Event(
                        type="quality.pipeline.completed",
                        source="quality_orchestration_agent",
                        data={
                            "pipeline_id": pipeline_id,
                            "status": pipeline_status,
                            "quality_score": quality_score,
                            "execution_time_ms": execution_time,
                            "gate_violations": len(gate_violations),
                            "actions_taken": len(actions_taken)
                        },
                        priority=EventPriority.HIGH if pipeline_status == "critical_failure" else EventPriority.NORMAL
                    )
                    await self.event_manager.publish_event(event)

                logger.info(f"Quality pipeline {pipeline_id} completed: {pipeline_status} (score: {quality_score:.2f})")

                return {
                    "status": "success",
                    "pipeline_id": pipeline_id,
                    "pipeline_status": pipeline_status,
                    "quality_score": quality_score,
                    "quality_level": validation_result.get("quality_level"),
                    "validation_results": validation_results,
                    "gate_results": {
                        "violations": gate_violations,
                        "passed": len(gate_violations) == 0,
                        "critical_issues": len([r for r in validation_results if r["status"] == "failed"])
                    },
                    "policy_actions": actions_taken,
                    "recommendations": recommendations,
                    "execution_time_ms": execution_time
                }
            else:
                logger.error(f"Quality pipeline validation failed: {validation_result['error']}")
                return {
                    "status": "error",
                    "error": validation_result["error"],
                    "pipeline_id": pipeline_id
                }

        except Exception as e:
            logger.error(f"Failed to orchestrate quality pipeline: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def _manage_quality_tasks(self, parameters: Dict, user_context: Dict) -> Dict[str, Any]:
        """Manage quality orchestration tasks"""
        task_config = parameters.get("task_config", {})
        policy_config = parameters.get("policy_config", {})
        schedule = parameters.get("schedule")
        auto_execute = parameters.get("auto_execute", False)

        try:
            if "task_id" in parameters:
                # Update existing task
                task_id = parameters["task_id"]
                if task_id in self.orchestration_tasks:
                    task = self.orchestration_tasks[task_id]

                    # Update task properties
                    if task_config:
                        task.name = task_config.get("name", task.name)
                        task.description = task_config.get("description", task.description)
                        task.mode = QualityOrchestrationMode(task_config.get("mode", task.mode.value))
                        task.priority = OrchestrationPriority(task_config.get("priority", task.priority.value))
                        task.components = set(task_config.get("components", task.components))
                        task.quality_gates = task_config.get("quality_gates", task.quality_gates)
                        task.schedule = task_config.get("schedule", task.schedule)
                        task.enabled = task_config.get("enabled", task.enabled)

                    return {
                        "status": "success",
                        "task_id": task_id,
                        "action": "updated",
                        "next_execution": self._calculate_next_execution(task)
                    }
                else:
                    return {
                        "status": "error",
                        "error": f"Task {task_id} not found"
                    }
            else:
                # Create new task
                task_id = f"task_{uuid.uuid4().hex[:8]}"

                task = QualityOrchestrationTask(
                    task_id=task_id,
                    name=task_config.get("name", task_id),
                    description=task_config.get("description", ""),
                    mode=QualityOrchestrationMode(task_config.get("mode", "on_demand")),
                    priority=OrchestrationPriority(task_config.get("priority", "normal")),
                    components=set(task_config.get("components", [])),
                    quality_gates=task_config.get("quality_gates", []),
                    schedule=task_config.get("schedule"),
                    metadata=task_config.get("metadata", {})
                )

                self.orchestration_tasks[task_id] = task

                # Execute task if auto_execute is enabled
                if auto_execute:
                    execution_result = await self._execute_orchestration_task(task)
                    task.last_executed = datetime.now(timezone.utc)
                    task.execution_history.append(execution_result)

                return {
                    "status": "success",
                    "task_id": task_id,
                    "action": "created",
                    "auto_executed": auto_execute,
                    "next_execution": self._calculate_next_execution(task)
                }

        except Exception as e:
            logger.error(f"Failed to manage quality task: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def _enforce_quality_gates(self, parameters: Dict, user_context: Dict) -> Dict[str, Any]:
        """Enforce quality gates for deployments"""
        gate_name = parameters.get("gate_name", "default")
        deployment_info = parameters.get("deployment_info", {})
        quality_requirements = parameters.get("quality_requirements", {})
        blocking_mode = parameters.get("blocking_mode", True)

        try:
            # Get current quality metrics
            quality_assessment = await self.quality_system._perform_quality_assessment({
                "assessment_scope": "deployment_preparation",
                "quality_dimensions": ["all"],
                "include_trends": True
            }, {})

            if quality_assessment["status"] != "success":
                return {
                    "status": "error",
                    "error": quality_assessment["error"],
                    "deployment_approved": False
                }

            quality_report = quality_assessment["quality_report"]
            overall_score = quality_report["overall_score"]
            critical_issues = quality_report.get("critical_issues", [])

            # Check gate requirements
            gate_violations = []
            deployment_approved = True

            # Check overall quality score
            min_score = quality_requirements.get("minimum_score", 0.7)
            if overall_score < min_score:
                gate_violations.append(f"Quality score {overall_score:.2f} below minimum {min_score:.2f}")
                if blocking_mode:
                    deployment_approved = False

            # Check critical issues
            if quality_requirements.get("no_critical_issues", True) and critical_issues:
                gate_violations.append(f"Critical issues found: {len(critical_issues)}")
                if blocking_mode:
                    deployment_approved = False

            # Check specific category requirements
            category_scores = quality_report.get("category_scores", {})
            for category, min_score in quality_requirements.get("category_minimums", {}).items():
                current_score = category_scores.get(category, 0)
                if current_score < min_score:
                    gate_violations.append(f"Category '{category}' score {current_score:.2f} below minimum {min_score:.2f}")
                    if blocking_mode:
                        deployment_approved = False

            # Record gate enforcement
            gate_record = {
                "gate_name": gate_name,
                "timestamp": datetime.now(timezone.utc),
                "quality_score": overall_score,
                "deployment_approved": deployment_approved,
                "violations": gate_violations,
                "deployment_info": deployment_info,
                "blocking_mode": blocking_mode
            }

            self.quality_gates_status[gate_name] = gate_record

            # Update metrics
            if deployment_approved:
                self.orchestration_metrics["quality_gates_passed"] += 1
            else:
                self.orchestration_metrics["quality_gates_failed"] += 1

            # Publish gate enforcement event
            if self.event_manager:
                event = Event(
                    type="quality.gate.enforced",
                    source="quality_orchestration_agent",
                    data={
                        "gate_name": gate_name,
                        "deployment_approved": deployment_approved,
                        "quality_score": overall_score,
                        "violations": len(gate_violations),
                        "blocking_mode": blocking_mode
                    },
                    priority=EventPriority.HIGH if not deployment_approved else EventPriority.NORMAL
                )
                await self.event_manager.publish_event(event)

            logger.info(f"Quality gate '{gate_name}' enforced: {deployment_approved} (score: {overall_score:.2f})")

            return {
                "status": "success",
                "gate_name": gate_name,
                "gate_status": "passed" if deployment_approved else "failed",
                "deployment_approved": deployment_approved,
                "quality_score": overall_score,
                "violations": gate_violations,
                "recommendations": quality_report.get("recommendations", []),
                "blocking_mode": blocking_mode
            }

        except Exception as e:
            logger.error(f"Failed to enforce quality gates: {e}")
            return {
                "status": "error",
                "error": str(e),
                "deployment_approved": False
            }

    async def _coordinate_continuous_monitoring(self, parameters: Dict, user_context: Dict) -> Dict[str, Any]:
        """Coordinate continuous quality monitoring"""
        monitoring_scope = parameters.get("monitoring_scope", "all")
        alert_thresholds = parameters.get("alert_thresholds", {})
        auto_heal_policies = parameters.get("auto_heal_policies", [])

        try:
            # Get current quality metrics
            current_time = datetime.now(timezone.utc)
            one_hour_ago = current_time - timedelta(hours=1)

            # Collect quality metrics from the last hour
            quality_metrics = self.quality_system.get_quality_metrics()
            metric_history = self.quality_system.metric_history

            # Analyze quality trends
            trend_analysis = {}
            active_alerts = []

            for metric_id, metric_data in quality_metrics.get("quality_metrics_stats", {}).items():
                if metric_id in metric_history:
                    recent_values = list(metric_history[metric_id])[-10:]  # Last 10 values

                    if len(recent_values) >= 2:
                        # Calculate trend
                        recent_avg = statistics.mean(recent_values[-5:])
                        older_avg = statistics.mean(recent_values[:5]) if len(recent_values) >= 10 else recent_avg

                        if recent_avg > older_avg * 1.05:
                            trend = "improving"
                        elif recent_avg < older_avg * 0.95:
                            trend = "degrading"
                        else:
                            trend = "stable"

                        trend_analysis[metric_id] = {
                            "trend": trend,
                            "recent_average": recent_avg,
                            "change_percentage": ((recent_avg - older_avg) / older_avg * 100) if older_avg != 0 else 0
                        }

                        # Check alert thresholds
                        if metric_id in alert_thresholds:
                            threshold = alert_thresholds[metric_id]
                            current_value = recent_values[-1] if recent_values else 0

                            if threshold.get("min") and current_value < threshold["min"]:
                                active_alerts.append({
                                    "metric_id": metric_id,
                                    "alert_type": "below_threshold",
                                    "current_value": current_value,
                                    "threshold": threshold["min"],
                                    "severity": threshold.get("severity", "warning"),
                                    "timestamp": current_time.isoformat()
                                })
                            elif threshold.get("max") and current_value > threshold["max"]:
                                active_alerts.append({
                                    "metric_id": metric_id,
                                    "alert_type": "above_threshold",
                                    "current_value": current_value,
                                    "threshold": threshold["max"],
                                    "severity": threshold.get("severity", "warning"),
                                    "timestamp": current_time.isoformat()
                                })

            # Update monitoring state
            self.monitoring_state["last_quality_check"] = current_time
            self.monitoring_state["active_alerts"].update([alert["metric_id"] for alert in active_alerts])

            # Calculate overall trend
            if trend_analysis:
                degrading_metrics = [mid for mid, data in trend_analysis.items() if data["trend"] == "degrading"]
                if len(degrading_metrics) > len(trend_analysis) / 2:
                    self.monitoring_state["quality_trend"] = "degrading"
                elif any(data["trend"] == "improving" for data in trend_analysis.values()):
                    self.monitoring_state["quality_trend"] = "improving"
                else:
                    self.monitoring_state["quality_trend"] = "stable"

            # Apply auto-healing if enabled
            healing_actions = []
            if self.orchestration_config["auto_healing_enabled"] and auto_heal_policies and active_alerts:
                healing_actions = await self._apply_auto_healing(active_alerts, auto_heal_policies)

            # Update metrics
            self.orchestration_metrics["continuous_alerts_generated"] += len(active_alerts)
            if healing_actions:
                self.orchestration_metrics["auto_heals_applied"] += len(healing_actions)

            # Publish monitoring event
            if self.event_manager and (active_alerts or healing_actions):
                event = Event(
                    type="quality.monitoring.update",
                    source="quality_orchestration_agent",
                    data={
                        "monitoring_scope": monitoring_scope,
                        "active_alerts": len(active_alerts),
                        "trend_analysis": trend_analysis,
                        "healing_actions_applied": len(healing_actions),
                        "quality_trend": self.monitoring_state["quality_trend"]
                    },
                    priority=EventPriority.HIGH if active_alerts else EventPriority.NORMAL
                )
                await self.event_manager.publish_event(event)

            return {
                "status": "success",
                "monitoring_status": "active",
                "quality_trend": self.monitoring_state["quality_trend"],
                "active_alerts": active_alerts,
                "trend_analysis": trend_analysis,
                "healing_actions": healing_actions,
                "metrics_collected": len(trend_analysis),
                "monitoring_timestamp": current_time.isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to coordinate continuous monitoring: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def _evaluate_policies(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate orchestration policies against context"""
        applicable_actions = []
        triggered_policies = []

        for policy_id, policy in self.orchestration_policies.items():
            if not policy.enabled:
                continue

            policy_triggered = False

            # Evaluate policy conditions
            for condition_key, condition_value in policy.conditions.items():
                if condition_key == "quality_score":
                    min_score = condition_value.get("minimum", 0)
                    max_score = condition_value.get("maximum", 1.0)
                    current_score = context.get("quality_score", 0)

                    if current_score < min_score or current_score > max_score:
                        policy_triggered = True
                        break

                elif condition_key == "all_gates_passed":
                    if not condition_value and context.get("gate_violations"):
                        policy_triggered = True
                        break

                elif condition_key == "no_critical_issues":
                    if condition_value and context.get("critical_issues", []):
                        policy_triggered = True
                        break

            if policy_triggered:
                triggered_policies.append(policy_id)
                applicable_actions.extend(policy.actions)

        return {
            "triggered_policies": triggered_policies,
            "actions": applicable_actions
        }

    async def _execute_policy_actions(self, actions: List[str], pipeline_id: str) -> List[str]:
        """Execute policy actions"""
        actions_taken = []

        for action in actions:
            try:
                if action == "deploy_to_production":
                    # Initiate deployment
                    logger.info(f"Initiating deployment to production for pipeline {pipeline_id}")
                    actions_taken.append("Deployment initiated")
                    # In real implementation, this would trigger actual deployment

                elif action == "rollback_deployment":
                    # Initiate rollback
                    logger.info(f"Initiating rollback for pipeline {pipeline_id}")
                    actions_taken.append("Rollback initiated")
                    # In real implementation, this would trigger actual rollback

                elif action == "notify_success":
                    # Send success notification
                    await self._send_notification("success", f"Pipeline {pipeline_id} passed quality gates", "success")
                    actions_taken.append("Success notification sent")

                elif action == "notify_failure":
                    # Send failure notification
                    await self._send_notification("failure", f"Pipeline {pipeline_id} failed quality gates", "error")
                    actions_taken.append("Failure notification sent")

                elif action == "notify_team":
                    # Send team notification
                    await self._send_notification("team", f"Quality update for pipeline {pipeline_id}", "info")
                    actions_taken.append("Team notification sent")

                elif action == "create_alert":
                    # Create alert
                    await self._create_alert(f"Quality issue in pipeline {pipeline_id}", "warning")
                    actions_taken.append("Alert created")

                elif action == "create_incident":
                    # Create incident
                    await self._create_incident(f"Critical quality failure in pipeline {pipeline_id}", "critical")
                    actions_taken.append("Incident created")

                elif action == "schedule_investigation":
                    # Schedule investigation
                    logger.info(f"Scheduling investigation for pipeline {pipeline_id}")
                    actions_taken.append("Investigation scheduled")

                else:
                    logger.warning(f"Unknown policy action: {action}")

            except Exception as e:
                logger.error(f"Failed to execute policy action {action}: {e}")
                actions_taken.append(f"Failed to execute {action}: {str(e)}")

        return actions_taken

    async def _send_notification(self, notification_type: str, message: str, severity: str) -> None:
        """Send notification"""
        # This would integrate with actual notification systems
        logger.info(f"Notification ({notification_type}, {severity}): {message}")

        # Publish notification event
        if self.event_manager:
            event = Event(
                type="quality.notification.sent",
                source="quality_orchestration_agent",
                data={
                    "notification_type": notification_type,
                    "message": message,
                    "severity": severity,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                },
                priority=EventPriority.HIGH if severity == "critical" else EventPriority.NORMAL
            )
            await self.event_manager.publish_event(event)

    async def _create_alert(self, message: str, severity: str) -> None:
        """Create quality alert"""
        # This would integrate with actual alert systems
        logger.warning(f"Quality alert ({severity}): {message}")

        # Publish alert event
        if self.event_manager:
            event = Event(
                type="quality.alert.created",
                source="quality_orchestration_agent",
                data={
                    "message": message,
                    "severity": severity,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                },
                priority=EventPriority.HIGH
            )
            await self.event_manager.publish_event(event)

    async def _create_incident(self, message: str, severity: str) -> None:
        """Create incident for critical issues"""
        # This would integrate with incident management systems
        logger.error(f"Quality incident ({severity}): {message}")

        # Publish incident event
        if self.event_manager:
            event = Event(
                type="quality.incident.created",
                source="quality_orchestration_agent",
                data={
                    "message": message,
                    "severity": severity,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                },
                priority=EventPriority.CRITICAL
            )
            await self.event_manager.publish_event(event)

    async def _execute_orchestration_task(self, task: QualityOrchestrationTask) -> Dict[str, Any]:
        """Execute a single orchestration task"""
        try:
            start_time = time.time()

            # Execute validation through quality system
            validation_result = await self.quality_system._execute_validation_suite({
                "suite_types": list(task.components) if "all" not in task.components else ["all"],
                "target_components": list(task.components),
                "quality_gates": task.quality_gates
            }, {})

            execution_time = (time.time() - start_time) / 60  # Convert to minutes

            result = {
                "task_id": task.task_id,
                "status": "success" if validation_result["status"] == "success" else "failed",
                "validation_result": validation_result,
                "execution_time_minutes": execution_time,
                "timestamp": datetime.now(timezone.utc)
            }

            logger.info(f"Orchestration task {task.task_id} completed: {result['status']}")
            return result

        except Exception as e:
            logger.error(f"Failed to execute orchestration task {task.task_id}: {e}")
            return {
                "task_id": task.task_id,
                "status": "error",
                "error": str(e),
                "execution_time_minutes": 0,
                "timestamp": datetime.now(timezone.utc)
            }

    def _calculate_next_execution(self, task: QualityOrchestrationTask) -> Optional[datetime]:
        """Calculate next execution time for scheduled tasks"""
        if task.mode != QualityOrchestrationMode.SCHEDULED or not task.schedule:
            return None

        # This would implement cron parsing for accurate scheduling
        # For now, return a simple next execution time
        if task.schedule == "0 2 * * *":  # Daily at 2 AM
            tomorrow = datetime.now(timezone.utc) + timedelta(days=1)
            return tomorrow.replace(hour=2, minute=0, second=0, microsecond=0)

        return None

    async def _apply_auto_healing(self, alerts: List[Dict[str, Any]], policies: List[Dict[str, Any]]) -> List[str]:
        """Apply auto-healing based on alerts and policies"""
        healing_actions = []

        for alert in alerts:
            metric_id = alert["metric_id"]
            alert_type = alert["alert_type"]
            current_value = alert["current_value"]

            # Find applicable healing policies
            applicable_policies = [
                policy for policy in policies
                if policy.get("metric_id") == metric_id or policy.get("alert_type") == alert_type
            ]

            for policy in applicable_policies:
                healing_action = policy.get("action")
                if healing_action:
                    try:
                        # Apply healing action
                        if healing_action == "restart_service":
                            healing_actions.append(f"Restarted service for metric {metric_id}")
                        elif healing_action == "scale_up":
                            healing_actions.append(f"Scaled up resources for metric {metric_id}")
                        elif healing_action == "clear_cache":
                            healing_actions.append(f"Cleared cache for metric {metric_id}")
                        elif healing_action == "adjust_thresholds":
                            healing_actions.append(f"Adjusted thresholds for metric {metric_id}")
                        else:
                            healing_actions.append(f"Applied healing action {healing_action} for metric {metric_id}")

                    except Exception as e:
                        logger.error(f"Failed to apply healing action {healing_action}: {e}")

        return healing_actions

    async def _continuous_monitoring_loop(self) -> None:
        """Background loop for continuous quality monitoring"""
        while True:
            try:
                await self._coordinate_continuous_monitoring({
                    "monitoring_scope": "all",
                    "alert_thresholds": {
                        "api_response_time_ms": {"max": 1000, "severity": "warning"},
                        "error_rate_percentage": {"max": 5.0, "severity": "error"},
                        "quality_score": {"min": 0.7, "severity": "warning"}
                    },
                    "auto_heal_policies": [
                        {"metric_id": "api_response_time_ms", "action": "scale_up"},
                        {"metric_id": "error_rate_percentage", "action": "restart_service"},
                        {"alert_type": "below_threshold", "action": "clear_cache"}
                    ]
                }, {})
                await asyncio.sleep(self.orchestration_config["metrics_collection_interval"])
            except Exception as e:
                logger.error(f"Error in continuous monitoring loop: {e}")
                await asyncio.sleep(60)

    async def _scheduling_loop(self) -> None:
        """Background loop for scheduled task execution"""
        while True:
            try:
                current_time = datetime.now(timezone.utc)

                # Check for scheduled tasks that need execution
                for task in self.orchestration_tasks.values():
                    if (task.enabled and
                        task.mode == QualityOrchestrationMode.SCHEDULED and
                        task.schedule and
                        task.last_executed and
                        current_time >= task.last_executed + timedelta(hours=24)):  # Simplified scheduling

                        # Execute task
                        logger.info(f"Executing scheduled task: {task.name}")
                        execution_result = await self._execute_orchestration_task(task)
                        task.last_executed = current_time
                        task.execution_history.append(execution_result)

                await asyncio.sleep(300)  # Check every 5 minutes
            except Exception as e:
                logger.error(f"Error in scheduling loop: {e}")
                await asyncio.sleep(60)

    async def _cleanup_loop(self) -> None:
        """Background loop for cleanup operations"""
        while True:
            try:
                await self._cleanup_expired_data()
                await asyncio.sleep(3600)  # Cleanup every hour
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
                await asyncio.sleep(300)

    async def _cleanup_expired_data(self) -> None:
        """Clean up expired orchestration data"""
        current_time = datetime.now(timezone.utc)
        retention_days = self.orchestration_config.get("cleanup_retention_days", 30)
        cutoff_time = current_time - timedelta(days=retention_days)

        # Clean up execution history
        self.execution_history = deque(
            (execution for execution in self.execution_history
             if execution.get("timestamp", datetime.min) >= cutoff_time),
            maxlen=10000
        )

        # Clean up threshold violations
        self.threshold_violations = deque(
            (violation for violation in self.threshold_violations
             if violation.get("timestamp", datetime.min) >= cutoff_time),
            maxlen=1000
        )

        logger.debug(f"Orchestration cleanup completed - removed data older than {cutoff_time}")

    def get_orchestration_metrics(self) -> Dict[str, Any]:
        """Get comprehensive orchestration metrics"""
        return {
            "orchestration_metrics": self.orchestration_metrics.copy(),
            "tasks_count": len(self.orchestration_tasks),
            "policies_count": len(self.orchestration_policies),
            "active_executions": len(self.active_executions),
            "execution_history_count": len(self.execution_history),
            "quality_gates_count": len(self.quality_gates_status),
            "cicd_integrations_count": len(self.cicd_integrations),
            "monitoring_state": self.monitoring_state.copy(),
            "continuous_monitoring": self.orchestration_config["continuous_monitoring"],
            "auto_healing_enabled": self.orchestration_config["auto_healing_enabled"],
            "quality_gate_enforcement": self.orchestration_config["quality_gate_enforcement"]
        }

    async def shutdown(self) -> None:
        """Gracefully shutdown the quality orchestration agent"""
        try:
            # Cancel background tasks
            if self.monitoring_task:
                self.monitoring_task.cancel()
                try:
                    await self.monitoring_task
                except asyncio.CancelledError:
                    pass

            if self.scheduling_task:
                self.scheduling_task.cancel()
                try:
                    await self.scheduling_task
                except asyncio.CancelledError:
                    pass

            if self.cleanup_task:
                self.cleanup_task.cancel()
                try:
                    await self.cleanup_task
                except asyncio.CancelledError:
                    pass

            # Cancel active executions
            for execution_id, task in self.active_executions.items():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

            # Shutdown quality system
            if self.quality_system:
                await self.quality_system.shutdown()

            # Shutdown event manager
            if self.event_manager:
                await self.event_manager.shutdown()

            logger.info("Quality Orchestration Agent shutdown complete")

        except Exception as e:
            logger.error(f"Error during shutdown: {e}")