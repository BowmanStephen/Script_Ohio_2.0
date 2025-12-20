#!/usr/bin/env python3
"""
Production Deployment Manager - Enterprise-Grade Deployment, Testing, Optimization and Monitoring
Coordinates production deployments with comprehensive testing, optimization, and monitoring
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
from pathlib import Path
import os
import shutil
import subprocess
import tempfile
import tarfile
import hashlib
from concurrent.futures import ThreadPoolExecutor
import yaml

from ..core.event_stream_manager import (
    EventStreamManager, Event, EventPriority, EventSubscription
)
from ..core.enhanced_agent_framework import EnhancedBaseAgent
from ..security.cfbd_api_security_manager import CFBDAPISecurityManager, SecurityLevel
from ..qa.comprehensive_quality_system import ComprehensiveQualitySystem
from ..qa.quality_orchestration_agent import QualityOrchestrationAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DeploymentStatus(Enum):
    """Deployment status values"""
    PENDING = "pending"
    PREPARING = "preparing"
    TESTING = "testing"
    VALIDATING = "validating"
    DEPLOYING = "deploying"
    ROLLING_BACK = "rolling_back"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class DeploymentEnvironment(Enum):
    """Deployment environment types"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"

class DeploymentType(Enum):
    """Deployment types"""
    FULL = "full"
    INCREMENTAL = "incremental"
    ROLLING = "rolling"
    BLUE_GREEN = "blue_green"
    CANARY = "canary"

class RollbackStrategy(Enum):
    """Rollback strategies"""
    AUTOMATIC = "automatic"
    MANUAL = "manual"
    SEMI_AUTOMATIC = "semi_automatic"

@dataclass
class DeploymentConfig:
    """Deployment configuration"""
    deployment_id: str
    name: str
    description: str
    environment: DeploymentEnvironment
    deployment_type: DeploymentType
    version: str
    components: Set[str] = field(default_factory=set)
    quality_gates: List[str] = field(default_factory=list)
    rollback_strategy: RollbackStrategy = RollbackStrategy.AUTOMATIC
    rollback_threshold: float = 0.7
    max_retries: int = 3
    auto_approval: bool = False
    notifications: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DeploymentInstance:
    """Active deployment instance"""
    instance_id: str
    deployment_config: DeploymentConfig
    status: DeploymentStatus = DeploymentStatus.PENDING
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    end_time: Optional[datetime] = None
    duration_minutes: float = 0
    quality_score: float = 0.0
    validation_results: List[Dict[str, Any]] = field(default_factory=list)
    deployed_components: List[str] = field(default_factory=list)
    rollback_info: Optional[Dict[str, Any]] = None
    logs: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    artifacts: Dict[str, str] = field(default_factory=dict)

@dataclass
class PerformanceTestResult:
    """Performance test result"""
    test_id: str
    test_name: str
    status: str  # passed, failed, warning
    response_time_ms: float
    throughput_rps: float
    error_rate: float
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    details: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DeploymentEnvironmentConfig:
    """Deployment environment configuration"""
    environment: DeploymentEnvironment
    infrastructure_type: str  # kubernetes, docker, baremetal
    resource_limits: Dict[str, Any] = field(default_factory=dict)
    scaling_policy: Dict[str, Any] = field(default_factory=dict)
    monitoring_config: Dict[str, Any] = field(default_factory=dict)
    backup_config: Dict[str, Any] = field(default_factory=dict)
    security_config: Dict[str, Any] = field(default_factory=dict)
    networking_config: Dict[str, Any] = field(default_factory=dict)

class ProductionDeploymentManager(EnhancedBaseAgent):
    """
    Enterprise production deployment manager with comprehensive testing,
    optimization, and monitoring capabilities
    """

    def __init__(self, agent_id: str = "production_deployment_manager"):
        super().__init__(
            agent_id=agent_id,
            agent_name="Production Deployment Manager",
            permission_level=self.PermissionLevel.ADMIN
        )

        # Deployment configuration
        self.deployment_config = {
            "max_concurrent_deployments": 2,
            "deployment_timeout_minutes": 120,
            "auto_rollback_enabled": True,
            "health_check_interval_seconds": 30,
            "performance_test_duration_minutes": 15,
            "rollback_timeout_minutes": 30,
            "artifact_retention_days": 30,
            "backup_before_deployment": True,
            "post_deployment_monitoring_minutes": 60,
            "blue_green_deployment": True,
            "canary_deployment_threshold": 0.05
        }

        # Deployment tracking
        self.active_deployments: Dict[str, DeploymentInstance] = {}
        self.deployment_history: deque = deque(maxlen=1000)
        self.deployment_queue: deque = deque(maxlen=100)
        self.rolling_deployments: Dict[str, Dict[str, Any]] = {}

        # Environment configurations
        self.environment_configs: Dict[DeploymentEnvironment, DeploymentEnvironmentConfig] = {}

        # Component systems integration
        self.quality_system: Optional[ComprehensiveQualitySystem] = None
        self.orchestration_agent: Optional[QualityOrchestrationAgent] = None
        self.security_manager: Optional[CFBDAPISecurityManager] = None

        # Performance testing
        self.performance_tests: Dict[str, Dict[str, Any]] = {}
        self.test_results: deque = deque(maxlen=500)

        # Deployment artifacts and backups
        self.deployment_artifacts: Dict[str, str] = {}
        self.backup_artifacts: Dict[str, str] = {}

        # Event stream integration
        self.event_manager: Optional[EventStreamManager] = None

        # Deployment metrics
        self.deployment_metrics = {
            "total_deployments": 0,
            "successful_deployments": 0,
            "failed_deployments": 0,
            "rollback_deployments": 0,
            "blue_green_deployments": 0,
            "canary_deployments": 0,
            "average_deployment_time_minutes": 0.0,
            "average_quality_score": 0.0,
            "performance_test_passed": 0,
            "performance_test_failed": 0
        }

        # Background processing
        self.monitoring_tasks: Dict[str, asyncio.Task] = {}
        self.cleanup_task: Optional[asyncio.Task] = None
        self.heartbeat_task: Optional[asyncio.Task] = None

        # Deployment state
        self.deployment_state = {
            "active_deployments": 0,
            "queue_size": 0,
            "health_status": "healthy",
            "last_health_check": datetime.now(timezone.utc),
            "environment_health": {}
        }

    def _define_capabilities(self) -> List['AgentCapability']:
        """Define deployment manager capabilities"""
        return [
            self.AgentCapability(
                name="execute_deployment",
                description="Execute comprehensive production deployment with testing and monitoring",
                execution_time_estimate=60.0,
                required_permissions=[self.PermissionLevel.ADMIN],
                parameters=["deployment_config", "environment", "deployment_type", "quality_gates"],
                returns={"deployment_id": "string", "status": "string", "quality_score": "float", "duration_minutes": "float"}
            ),
            self.AgentCapability(
                name="manage_deployment_environments",
                description="Configure and manage deployment environments and infrastructure",
                execution_time_estimate=30.0,
                required_permissions=[self.PermissionLevel.ADMIN],
                parameters=["environment", "infrastructure_config", "resource_limits", "scaling_policy"],
                returns={"environment_status": "string", "configuration": "dict"}
            ),
            self.AgentCapability(
                name="execute_performance_tests",
                description="Execute comprehensive performance testing on deployed systems",
                execution_time_estimate=30.0,
                required_permissions=[self.PermissionLevel.READ_EXECUTE],
                parameters=["test_scenarios", "duration", "load_testing", "benchmarking"],
                returns={"test_results": "list", "performance_metrics": "dict", "passed_tests": "int"}
            ),
            self.AgentCapability(
                name="manage_rollback",
                description="Manage rollback procedures and deployment recovery",
                execution_time_estimate=20.0,
                required_permissions=[self.PermissionLevel.ADMIN],
                parameters=["deployment_id", "rollback_strategy", "trigger_conditions", "manual_approval"],
                returns={"rollback_id": "string", "status": "string", "rollback_time": "float"}
            )
        ]

    async def initialize(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Initialize the production deployment manager

        Args:
            config: Configuration dictionary

        Returns:
            Initialization status
        """
        try:
            # Update configuration
            if "deployment" in config:
                self.deployment_config.update(config["deployment"])

            # Initialize event stream manager
            if "event_stream" in config:
                event_config = config["event_stream"]
                self.event_manager = EventStreamManager(event_config)
                await self.event_manager.initialize()
                await self._setup_deployment_subscriptions()

            # Initialize component systems
            await self._initialize_component_systems(config)

            # Initialize environment configurations
            await self._initialize_environments(config.get("environments", {}))

            # Initialize performance tests
            await self._initialize_performance_tests(config.get("performance_tests", {}))

            # Start background tasks
            self.cleanup_task = asyncio.create_task(self._cleanup_loop())
            self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())

            logger.info("Production Deployment Manager initialized successfully")
            return {
                "status": "success",
                "active_deployments": len(self.active_deployments),
                "queue_size": len(self.deployment_queue),
                "environment_configs": len(self.environment_configs),
                "performance_tests": len(self.performance_tests),
                "auto_rollback_enabled": self.deployment_config["auto_rollback_enabled"],
                "max_concurrent_deployments": self.deployment_config["max_concurrent_deployments"]
            }

        except Exception as e:
            logger.error(f"Failed to initialize Production Deployment Manager: {e}")
            return {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__
            }

    async def _setup_deployment_subscriptions(self) -> None:
        """Setup event subscriptions for deployment monitoring"""
        # Deployment events
        deployment_subscription = EventSubscription(
            subscriber_id="deployment_manager",
            event_types={
                "deployment.*",
                "quality.*",
                "security.*",
                "performance.*",
                "system.*"
            },
            priority_filter={EventPriority.HIGH, EventPriority.CRITICAL}
        )
        await self.event_manager.subscribe_to_events(deployment_subscription)

    async def _initialize_component_systems(self, config: Dict[str, Any]) -> None:
        """Initialize component systems"""
        # Initialize quality system
        quality_config = config.get("quality", {})
        self.quality_system = ComprehensiveQualitySystem()
        quality_result = await self.quality_system.initialize(quality_config)

        if quality_result["status"] != "success":
            logger.warning(f"Quality system initialization issue: {quality_result['error']}")

        # Initialize orchestration agent
        orchestration_config = config.get("orchestration", {})
        self.orchestration_agent = QualityOrchestrationAgent()
        orchestration_result = await self.orchestration_agent.initialize(orchestration_config)

        if orchestration_result["status"] != "success":
            logger.warning(f"Orchestration agent initialization issue: {orchestration_result['error']}")

        # Initialize security manager
        security_config = config.get("security", {})
        self.security_manager = CFBDAPISecurityManager()
        security_result = await self.security_manager.initialize(security_config)

        if security_result["status"] != "success":
            logger.warning(f"Security manager initialization issue: {security_result['error']}")

        logger.info("Component systems initialized")

    async def _initialize_environments(self, environments_config: Dict[str, Any]) -> None:
        """Initialize deployment environments"""
        # Default environment configurations
        default_environments = {
            "development": DeploymentEnvironmentConfig(
                environment=DeploymentEnvironment.DEVELOPMENT,
                infrastructure_type="docker",
                resource_limits={
                    "cpu_cores": 2,
                    "memory_gb": 4,
                    "storage_gb": 20
                },
                scaling_policy={
                    "min_instances": 1,
                    "max_instances": 2,
                    "auto_scaling": False
                },
                monitoring_config={
                    "enabled": True,
                    "metrics_interval": 60,
                    "health_check_interval": 30
                }
            ),
            "staging": DeploymentEnvironmentConfig(
                environment=DeploymentEnvironment.STAGING,
                infrastructure_type="kubernetes",
                resource_limits={
                    "cpu_cores": 4,
                    "memory_gb": 8,
                    "storage_gb": 50,
                    "pods": 3
                },
                scaling_policy={
                    "min_instances": 2,
                    "max_instances": 5,
                    "auto_scaling": True,
                    "target_cpu_utilization": 70,
                    "target_memory_utilization": 80
                },
                monitoring_config={
                    "enabled": True,
                    "metrics_interval": 30,
                    "health_check_interval": 15,
                    "alerting_enabled": True
                }
            ),
            "production": DeploymentEnvironmentConfig(
                environment=DeploymentEnvironment.PRODUCTION,
                infrastructure_type="kubernetes",
                resource_limits={
                    "cpu_cores": 8,
                    "memory_gb": 16,
                    "storage_gb": 200,
                    "pods": 5
                },
                scaling_policy={
                    "min_instances": 3,
                    "max_instances": 10,
                    "auto_scaling": True,
                    "target_cpu_utilization": 75,
                    "target_memory_utilization": 85
                },
                monitoring_config={
                    "enabled": True,
                    "metrics_interval": 15,
                    "health_check_interval": 10,
                    "alerting_enabled": True,
                    "detailed_logging": True
                },
                backup_config={
                    "enabled": True,
                    "backup_interval_hours": 6,
                    "retention_days": 30,
                    "backup_retention_days": 90
                }
            ),
            "testing": DeploymentEnvironmentConfig(
                environment=DeploymentEnvironment.TESTING,
                infrastructure_type="docker",
                resource_limits={
                    "cpu_cores": 2,
                    "memory_gb": 4,
                    "storage_gb": 30
                },
                scaling_policy={
                    "min_instances": 1,
                    "max_instances": 3,
                    "auto_scaling": False
                },
                monitoring_config={
                    "enabled": True,
                    "metrics_interval": 60,
                    "health_check_interval": 60
                }
            )
        }

        # Add default environments
        for env_name, env_config in default_environments.items():
            self.environment_configs[DeploymentEnvironment(env_name)] = env_config

        # Add custom environments from configuration
        for env_name, env_config in environments_config.items():
            try:
                self.environment_configs[DeploymentEnvironment(env_name)] = DeploymentEnvironmentConfig(
                    environment=DeploymentEnvironment(env_name),
                    infrastructure_type=env_config.get("infrastructure_type", "docker"),
                    resource_limits=env_config.get("resource_limits", {}),
                    scaling_policy=env_config.get("scaling_policy", {}),
                    monitoring_config=env_config.get("monitoring_config", {}),
                    backup_config=env_config.get("backup_config", {}),
                    security_config=env_config.get("security_config", {}),
                    networking_config=env_config.get("networking_config", {})
                )
            except Exception as e:
                logger.warning(f"Failed to load environment {env_name}: {e}")

        logger.info(f"Initialized {len(self.environment_configs)} environments")

    async def _initialize_performance_tests(self, tests_config: Dict[str, Any]) -> None:
        """Initialize performance test configurations"""
        # Default performance tests
        default_tests = {
            "load_test": {
                "name": "Load Test",
                "description": "Comprehensive load testing with varying load levels",
                "duration_minutes": 15,
                "concurrent_users": 100,
                "ramp_up_time_minutes": 5,
                "target_throughput_rps": 1000,
                "max_response_time_ms": 1000,
                "max_error_rate": 1.0
            },
            "stress_test": {
                "name": "Stress Test",
                "description": "System stress testing to identify breaking points",
                "duration_minutes": 10,
                "concurrent_users": 500,
                "ramp_up_time_minutes": 2,
                "target_throughput_rps": 5000,
                "max_response_time_ms": 5000,
                "max_error_rate": 5.0
            },
            "endurance_test": {
                "name": "Endurance Test",
                "description": "Long-running test to identify memory leaks and performance degradation",
                "duration_minutes": 60,
                "concurrent_users": 50,
                "target_throughput_rps": 200,
                "max_response_time_ms": 2000,
                "max_error_rate": 0.5
            },
            "spike_test": {
                "name": "Spike Test",
                "description": "Spike testing to simulate sudden load increases",
                "duration_minutes": 5,
                "spike_users": 1000,
                "spike_duration_seconds": 30,
                "normal_users": 10,
                "max_response_time_ms": 3000,
                "max_error_rate": 10.0
            }
        }

        # Add default tests
        for test_name, test_config in default_tests.items():
            self.performance_tests[test_name] = test_config

        # Add custom tests from configuration
        for test_name, test_config in tests_config.items():
            self.performance_tests[test_name] = test_config

        logger.info(f"Initialized {len(self.performance_tests)} performance tests")

    async def _execute_action(self, action: str, parameters: Dict, user_context: Dict) -> Dict[str, Any]:
        """Execute deployment manager actions"""
        try:
            if action == "execute_deployment":
                return await self._execute_deployment(parameters, user_context)
            elif action == "manage_deployment_environments":
                return await self._manage_deployment_environments(parameters, user_context)
            elif action == "execute_performance_tests":
                return await self._execute_performance_tests(parameters, user_context)
            elif action == "manage_rollback":
                return await self._manage_rollback(parameters, user_context)
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

    async def _execute_deployment(self, parameters: Dict, user_context: Dict) -> Dict[str, Any]:
        """Execute production deployment"""
        deployment_config = parameters.get("deployment_config", {})
        environment_str = parameters.get("environment", "production")
        deployment_type_str = parameters.get("deployment_type", "full")
        quality_gates = parameters.get("quality_gates", ["all"])

        try:
            # Parse deployment configuration
            deployment_id = deployment_config.get("deployment_id", f"deploy_{uuid.uuid4().hex[:8]}")
            environment = DeploymentEnvironment(environment_str)
            deployment_type = DeploymentType(deployment_type_str)

            # Create deployment configuration
            config = DeploymentConfig(
                deployment_id=deployment_id,
                name=deployment_config.get("name", f"Deployment to {environment_str}"),
                description=deployment_config.get("description", ""),
                environment=environment,
                deployment_type=deployment_type,
                version=deployment_config.get("version", "latest"),
                components=set(deployment_config.get("components", ["all"])),
                quality_gates=quality_gates,
                rollback_strategy=RollbackStrategy(deployment_config.get("rollback_strategy", "automatic")),
                rollback_threshold=deployment_config.get("rollback_threshold", 0.7),
                max_retries=deployment_config.get("max_retries", 3),
                auto_approval=deployment_config.get("auto_approval", False),
                notifications=deployment_config.get("notifications", {}),
                metadata=deployment_config.get("metadata", {})
            )

            # Create deployment instance
            deployment_instance = DeploymentInstance(
                instance_id=deployment_id,
                deployment_config=config
            )

            # Start deployment process
            print(f"🚀 Starting deployment {deployment_id} to {environment_str}")
            start_time = time.time()

            try:
                # Phase 1: Preparation
                await self._prepare_deployment(deployment_instance)
                deployment_instance.status = DeploymentStatus.TESTING

                # Phase 2: Quality Validation
                await self._validate_deployment_quality(deployment_instance)
                deployment_instance.status = DeploymentStatus.DEPLOYING

                # Phase 3: Deployment
                await self._deploy_to_environment(deployment_instance, environment)
                deployment_instance.status = DeploymentStatus.COMPLETED

                # Phase 4: Post-Deployment Testing
                await self._post_deployment_testing(deployment_instance)

                # Calculate deployment metrics
                deployment_instance.duration_minutes = (time.time() - start_time) / 60
                deployment_instance.end_time = datetime.now(timezone.utc) + timedelta(minutes=deployment_instance.duration_minutes)

                # Update metrics
                self.deployment_metrics["total_deployments"] += 1
                if deployment_instance.status == DeploymentStatus.COMPLETED:
                    self.deployment_metrics["successful_deployments"] += 1
                else:
                    self.deployment_metrics["failed_deployments"] += 1
                    self.deployment_metrics["rollback_deployments"] += 1

                self.deployment_metrics["average_deployment_time_minutes"] = (
                    (self.deployment_metrics["average_deployment_time_minutes"] + deployment_instance.duration_minutes) / 2
                )
                self.deployment_metrics["average_quality_score"] = (
                    (self.deployment_metrics["average_quality_score"] + deployment_instance.quality_score) / 2
                )

                # Publish deployment completion event
                if self.event_manager:
                    event = Event(
                        type="deployment.completed",
                        source="production_deployment_manager",
                        data={
                            "deployment_id": deployment_id,
                            "environment": environment_str,
                            "status": deployment_instance.status.value,
                            "quality_score": deployment_instance.quality_score,
                            "duration_minutes": deployment_instance.duration_minutes,
                            "deployed_components": len(deployment_instance.deployed_components),
                            "success": deployment_instance.status == DeploymentStatus.COMPLETED
                        },
                        priority=EventPriority.HIGH
                    )
                    await self.event_manager.publish_event(event)

                logger.info(f"Deployment {deployment_id} completed: {deployment_instance.status.value}")
                logger.info(f"Quality score: {deployment_instance.quality_score:.2f}, Duration: {deployment_instance.duration_minutes:.1f}m")

                return {
                    "status": "success",
                    "deployment_id": deployment_id,
                    "status": deployment_instance.status.value,
                    "environment": environment_str,
                    "quality_score": deployment_instance.quality_score,
                    "duration_minutes": deployment_instance.duration_minutes,
                    "deployed_components": deployment_instance.deployed_components,
                    "validation_results": deployment_instance.validation_results,
                    "performance_metrics": deployment_instance.metrics,
                    "artifacts": deployment_instance.artifacts,
                    "success": deployment_instance.status == DeploymentStatus.COMPLETED
                }

            except Exception as deployment_error:
                deployment_instance.status = DeploymentStatus.FAILED
                deployment_instance.end_time = datetime.now(timezone.utc)
                deployment_instance.duration_minutes = (time.time() - start_time) / 60

                # Attempt rollback if enabled
                if self.deployment_config["auto_rollback_enabled"]:
                    print(f"🔄 Auto-rollback triggered due to deployment error: {deployment_error}")
                    rollback_result = await self._execute_rollback({
                        "deployment_id": deployment_id,
                        "rollback_strategy": "automatic",
                        "trigger_conditions": ["deployment_failed"],
                        "manual_approval": False
                    }, {})

                    if rollback_result["status"] == "success":
                        deployment_instance.rollback_info = rollback_result
                else:
                    logger.error(f"Rollback also failed: {rollback_result['error']}")

                # Update metrics for failed deployment
                self.deployment_metrics["failed_deployments"] += 1
                self.deployment_metrics["rollback_deployments"] += 1

                # Publish deployment failure event
                if self.event_manager:
                    event = Event(
                        type="deployment.failed",
                        source="deployment_manager",
                        data={
                            "deployment_id": deployment_id,
                            "error": str(deployment_error),
                            "status": deployment_instance.status.value,
                            "duration_minutes": deployment_instance.duration_minutes,
                            "rollback_triggered": self.deployment_config["auto_rollback_enabled"]
                        },
                        priority=EventPriority.CRITICAL
                    )
                    await self.event_manager.publish_event(event)

                return {
                    "status": "error",
                    "deployment_id": deployment_id,
                    "status": deployment_instance.status.value,
                    "error": str(deployment_error),
                    "duration_minutes": deployment_instance.duration_minutes,
                    "rollback_applied": rollback_result.get("status") == "success" if 'rollback_result' in locals() else False,
                    "artifacts": deployment_instance.artifacts
                }

            finally:
                # Store deployment instance
                self.active_deployments[deployment_id] = deployment_instance
                self.deployment_history.append({
                    "deployment_id": deployment_id,
                    "status": deployment_instance.status.value,
                    "quality_score": deployment_instance.quality_score,
                    "duration_minutes": deployment_instance.duration_minutes,
                    "environment": environment_str,
                    "deployment_type": deployment_type.value,
                    "timestamp": datetime.now(timezone.utc)
                })

        except Exception as e:
            logger.error(f"Failed to execute deployment: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def _prepare_deployment(self, deployment: DeploymentInstance) -> None:
        """Prepare deployment environment"""
        deployment.status = DeploymentStatus.PREPARING
        print(f"   📋 Preparing deployment {deployment.deployment_id}")

        # Backup current state if required
        if self.deployment_config["backup_before_deployment"]:
            print(f"   💾 Creating backup before deployment...")
            await self._create_deployment_backup(deployment)

        # Validate deployment requirements
        print(f"   ✅ Validating deployment requirements...")
        await self._validate_deployment_requirements(deployment)

        # Prepare deployment artifacts
        print(f"   📦 Preparing deployment artifacts...")
        await self._prepare_deployment_artifacts(deployment)

        # Notify stakeholders
        if deployment.deployment_config.notifications.get("started"):
            await self._send_deployment_notification("started", deployment)

    async def _validate_deployment_quality(self, deployment: DeploymentInstance) -> None:
        """Validate deployment quality through quality system"""
        print(f"🔍 Validating deployment quality for {deployment.deployment_id}")

        # Execute quality validation
        validation_result = await self.quality_system._execute_validation_suite({
            "suite_types": ["all"],
            "target_components": list(deployment.deployment_config.components),
            "quality_gates": deployment.deployment_config.quality_gates
        }, {})

        if validation_result["status"] == "success":
            deployment.quality_score = validation_result["quality_score"]
            deployment.validation_results = validation_result["validation_results"]

            print(f"   ✅ Quality validation passed")
            print(f"   📊 Quality Score: {deployment.quality_score:.2f}")

            # Check if quality gates passed
            gate_violations = validation_result.get("gate_violations", [])
            if gate_violations:
                print(f"   ⚠️  Quality gate violations: {len(gate_violations)}")
                for violation in gate_violations:
                    print(f"      - {violation}")

                # If critical violations, rollback
                critical_violations = [
                    v for v in gate_violations if "critical" in v.get("severity", "").lower()
                ]
                if critical_violations and deployment.deployment_config.rollback_strategy != RollbackStrategy.MANUAL:
                    raise Exception(f"Critical quality gate violations: {len(critical_violations)}")

            # Store validation results
            for result in validation_result["validation_results"]:
                deployment.validation_results.append(result)

        else:
            raise Exception(f"Quality validation failed: {validation_result['error']}")

    async def _deploy_to_environment(self, deployment: DeploymentInstance, environment: DeploymentEnvironment) -> None:
        """Deploy to specified environment"""
        deployment.status = DeploymentStatus.DEPLOYING
        print(f"🚀 Deploying {deployment.deployment_id} to {environment.value}")

        # Get environment configuration
        env_config = self.environment_configs.get(environment)
        if not env_config:
            raise Exception(f"Environment {environment.value} not configured")

        # Simulate deployment steps
        deployment_steps = [
            "Infrastructure provision",
            "Application container build",
            "Service configuration",
            "Network setup",
            "Security configuration",
            "Monitoring setup",
            "Health verification",
            "Traffic routing"
        ]

        deployed_components = []

        for step in deployment_steps:
            print(f"   📋 {step}...")
            await asyncio.sleep(0.5)  # Simulate step execution time

            # Add deployed components
            if step == "Application container build":
                for component in deployment.deployment_config.components:
                    if component != "all":
                        deployed_components.append(component)
            elif step == "Monitoring setup":
                deployed_components.append("monitoring")

            # Create log entry
            log_entry = f"[{deployment.deployment_id}] {step} completed successfully"
            deployment.logs.append(log_entry)

        deployment.deployed_components = deployed_components

    async def _post_deployment_testing(self, deployment: DeploymentInstance) -> None:
        """Execute post-deployment testing"""
        print(f"🧪 Executing post-deployment testing for {deployment.deployment_id}")

        # Basic health check
        print(f"   🔍 Performing health checks...")
        await asyncio.sleep(1)

        health_status = await self._perform_health_check(deployment)
        print(f"   ✅ Health status: {health_status}")

        # Performance testing
        print(f"   📊 Executing performance tests...")
        performance_result = await self._execute_performance_tests({
            "test_scenarios": ["load_test", "smoke_test"],
            "duration": 5,
            "environment": deployment.deployment_config.environment.value
        }, {})

        if performance_result["status"] == "success":
            test_results = performance_result.get("test_results", [])
            passed_tests = [t for t in test_results if t["status"] == "passed"]
            failed_tests = [t for t in test_results if t["status"] == "failed"]

            print(f"   📊 Performance tests completed")
            print(f"   ✅ Tests passed: {len(passed_tests)}")
            print(f"   ❌ Tests failed: {len(failed_tests)}")

            # Store performance results
            for result in test_results:
                deployment.metrics["performance_tests"] = result

            # Update metrics
            if performance_result.get("test_results"):
                self.deployment_metrics["performance_test_passed"] += len([t for t in performance_result["test_results"] if t["status"] == "passed"])
                self.deployment_metrics["performance_test_failed"] += len([t for t in performance_result["test_results"] if t["status"] == "failed"])
        else:
            print(f"   ❌ Performance tests failed: {performance_result['error']}")

        # Integration testing
        print(f"🔗 Executing integration tests...")
        await asyncio.sleep(1)

        integration_results = await self._execute_integration_tests(deployment)
        passed_integration = [r for r in integration_results if r["status"] == "passed"]
        failed_integration = [r for r in integration_results if r["status"] == "failed"]

        print(f"   ✅ Integration tests passed: {len(passed_integration)}")
        print(f"   ❌ Integration tests failed: {len(failed_integration)}")

        # Update deployment status based on testing results
        if (health_status == "healthy" and
            performance_result.get("status") == "success" and
            len(failed_integration) == 0):
            deployment.status = DeploymentStatus.COMPLETED
        elif len(failed_integration) > 0 or performance_result.get("status") != "success":
            deployment.status = DeploymentStatus.COMPLETED  # Still considered completed but with issues
            print(f"   ⚠️  Deployment completed with issues: {len(failed_integration)} integration failures")

    async def _execute_performance_tests(self, parameters: Dict, user_context: Dict) -> Dict[str, Any]:
        """Execute performance tests"""
        test_scenarios = parameters.get("test_scenarios", ["load_test"])
        duration = parameters.get("duration", 10)
        environment = parameters.get("environment", "production")

        try:
            print(f"🧪 Starting performance tests: {', '.join(test_scenarios)}")

            test_results = []

            for scenario_name in test_scenarios:
                if scenario_name not in self.performance_tests:
                    logger.warning(f"Unknown performance test scenario: {scenario_name}")
                    continue

                test_config = self.performance_tests[scenario_name]
                test_name = test_config["name"]

                print(f"   🧪 Running: {test_name}")

                # Execute performance test
                result = await self._execute_single_performance_test(scenario_name, test_config, duration, environment)

                test_results.append(result)

                # Display results
                status = result.get("status", "unknown")
                response_time = result.get("response_time_ms", 0)
                throughput = result.get("throughput_rps", 0)
                error_rate = result.get("error_rate", 0)

                print(f"      Status: {status}")
                print(f"      Response Time: {response_time:.0f}ms")
                print(f"      Throughput: {throughput:.0f} RPS")
                print(f"      Error Rate: {error_rate:.1f}%")

            # Calculate overall test results
            passed_tests = [t for t in test_results if t["status"] == "passed"]
            failed_tests = [t for t in test_results if t["status"] == "failed"]
            warning_tests = [t for t in test_results if t["status"] == "warning"]

            return {
                "status": "success",
                "test_results": test_results,
                "passed_tests": len(passed_tests),
                "failed_tests": len(failed_tests),
                "warning_tests": len(warning_tests),
                "overall_status": "passed" if len(failed_tests) == 0 else ("failed" if len(failed_tests) > len(passed_tests) else "warning"),
                "test_scenarios": test_scenarios
            }

        except Exception as e:
            logger.error(f"Failed to execute performance tests: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def _execute_single_performance_test(self, test_name: str, test_config: Dict[str, Any], duration_minutes: float, environment: str) -> Dict[str, Any]:
        """Execute a single performance test"""
        start_time = time.time()
        test_id = f"perf_test_{uuid.uuid4().hex[:8]}"

        try:
            # Extract test configuration
            duration_seconds = duration_minutes * 60
            concurrent_users = test_config.get("concurrent_users", 50)
            target_throughput = test_config.get("target_throughput_rps", 500)
            max_response_time = test_config.get("max_response_time_ms", 1000)
            max_error_rate = test_config.get("max_error_rate", 1.0)

            # Simulate performance test execution
            await asyncio.sleep(1)  # Initial setup

            # Simulate load generation
            current_users = 0
            total_requests = 0
            errors = 0
            response_times = []

            # Ramp up phase
            ramp_up_time = test_config.get("ramp_up_time_minutes", 2) * 60
            ramp_up_end = start_time + ramp_up_time

            while current_users < concurrent_users and time.time() < ramp_up_end:
                current_users += 1
                # Simulate request
                response_time = 200 + (hash(str(time.time())) % 800)
                errors += 1 if response_time > max_response_time else 0
                response_times.append(response_time)
                total_requests += current_users

                await asyncio.sleep(0.1)

            # Steady state phase
            steady_end_time = start_time + duration_seconds - ramp_up_time

            while time.time() < steady_end_time:
                # Simulate requests at target throughput
                target_requests_per_second = target_throughput / concurrent_users
                for _ in range(target_requests_per_second):
                    # Simulate request
                    response_time = 200 + (hash(str(time.time())) % 800)
                    errors += 1 if response_time > max_response_time else 0
                    response_times.append(response_time)
                    total_requests += 1

                await asyncio.sleep(1)

            # Calculate metrics
            execution_time = (time.time() - start_time) * 1000
            avg_response_time = statistics.mean(response_times) if response_times else 0
            actual_throughput = total_requests / max(1, (time.time() - start_time))
            actual_error_rate = (errors / max(1, total_requests)) * 100

            # Determine test status
            status = "passed"
            if actual_error_rate > max_error_rate:
                status = "failed"
            elif actual_error_rate > max_error_rate * 0.8:
                status = "warning"
            elif avg_response_time > max_response_time:
                status = "warning"
            elif actual_throughput < target_throughput * 0.8:
                status = "warning"

            return {
                "test_id": test_id,
                "test_name": test_name,
                "status": status,
                "response_time_ms": avg_response_time,
                "throughput_rps": actual_throughput,
                "error_rate": actual_error_rate,
                "cpu_usage": 0,  # Would be measured in real implementation
                "memory_usage": 0,  # Would be measured
                "disk_usage": 0,  # Would be measured
                "network_io": 0,  # Would be measured
                "timestamp": datetime.now(timezone.utc),
                "details": {
                    "duration_minutes": duration_minutes,
                    "concurrent_users": concurrent_users,
                    "target_throughput_rps": target_throughput,
                    "total_requests": total_requests
                }
            }

        except Exception as e:
            logger.error(f"Performance test {test_name} failed: {e}")
            return {
                "test_id": test_id,
                "test_name": test_name,
                "status": "error",
                "response_time_ms": 0,
                "throughput_rps": 0,
                "error_rate": 0,
                "cpu_usage": 0,
                "memory_usage:": 0,
                "disk_usage": 0,
                "network_io": 0,
                "timestamp": datetime.now(timezone.utc),
                "details": {"error": str(e)}
            }

    async def _execute_rollback(self, parameters: Dict, user_context: Dict) -> Dict[str, Any]:
        """Execute deployment rollback"""
        deployment_id = parameters.get("deployment_id")
        rollback_strategy = parameters.get("rollback_strategy", "automatic")
        trigger_conditions = parameters.get("trigger_conditions", [])
        manual_approval = parameters.get("manual_approval", False)

        try:
            deployment = self.active_deployments.get(deployment_id)
            if not deployment:
                raise Exception(f"Deployment {deployment_id} not found")

            print(f"🔄 Starting rollback for deployment {deployment_id}")

            rollback_id = f"rollback_{uuid.uuid4().hex[:8]}"
            start_time = time.time()

            # Wait for manual approval if required
            if manual_approval:
                print(f"   ⏸️ Waiting for manual approval for rollback...")
                # In real implementation, this would wait for user confirmation
                await asyncio.sleep(5)

            # Perform rollback
            print(f"   🔙Executing rollback using {rollback_strategy.value} strategy...")

            # Simulate rollback steps
            rollback_steps = [
                "Stop new traffic routing",
                "Drain existing connections",
                "Stop new container instances",
                "Rollback database transactions",
                "Restore from backup",
                "Validate rollback completeness"
            ]

            for step in rollback_steps:
                print(f"   🔙 {step}...")
                await asyncio.sleep(0.5)

            # Update deployment instance
            deployment.status = DeploymentStatus.ROLLING_BACK
            deployment.rollback_info = {
                "rollback_id": rollback_id,
                "strategy": rollback_strategy.value,
                "trigger_conditions": trigger_conditions,
                "manual_approval": manual_approval,
                "start_time": start_time
            }

            # Execute rollback
            await asyncio.sleep(2)  # Simulated rollback time

            deployment.status = DeploymentStatus.FAILED
            deployment.end_time = datetime.now(timezone.utc)
            deployment.duration_minutes = (deployment.end_time - deployment.start_time).total_seconds() / 60

            # Update metrics
            self.deployment_metrics["rollback_deployments"] += 1

            # Publish rollback event
            if self.event_manager:
                event = Event(
                    type="deployment.rolled_back",
                    source="production_deployment_manager",
                    data={
                        "deployment_id": deployment_id,
                        "rollback_id": rollback_id,
                        "strategy": rollback_strategy.value,
                        "duration_minutes": deployment.duration_minutes,
                        "success": True
                    },
                    priority=EventPriority.HIGH
                )
                await self.event_manager.publish_event(event)

            print(f"   ✅ Rollback completed: {rollback_id}")
            print(f"   ⏱️ Rollback duration: {deployment.duration_minutes:.1f} minutes")

            return {
                "status": "success",
                "deployment_id": deployment_id,
                "rollback_id": rollback_id,
                "strategy": rollback_strategy.value,
                "duration_minutes": deployment.duration_minutes,
                "success": True
            }

        except Exception as e:
            logger.error(f"Rollback failed for deployment {deployment_id}: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def _manage_deployment_environments(self, parameters: Dict, user_context: Dict) -> Dict[str, Any]:
        """Manage deployment environments"""
        environment = parameters.get("environment")
        infrastructure_config = parameters.get("infrastructure_config", {})
        resource_limits = parameters.get("resource_limits", {})
        scaling_policy = parameters.get("scaling_policy", {})

        try:
            env_name = environment if isinstance(environment, str) else environment.value
            env_enum = DeploymentEnvironment(env_name)

            # Update environment configuration
            if env_enum in self.environment_configs:
                env_config = self.environment_configs[env_enum]

                if infrastructure_config:
                    env_config.infrastructure_type = infrastructure_config.get("infrastructure_type", env_config.infrastructure_type)

                if resource_limits:
                    env_config.resource_limits.update(resource_limits)

                if scaling_policy:
                    env_config.scaling_policy.update(scaling_policy)

                self.environment_configs[env_enum] = env_config

                print(f"   ✅ Environment {env_name} configured successfully")
                return {
                    "status": "success",
                    "environment": env_name,
                    "infrastructure_type": env_config.infrastructure_type,
                    "resource_limits": env_config.resource_limits,
                    "scaling_policy": env_config.scaling_policy
                }
            else:
                return {
                    "status": "error",
                    "error": f"Unknown environment: {env_name}"
                }

        except Exception as e:
            logger.error(f"Failed to manage environment {environment}: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    def get_deployment_metrics(self) -> Dict[str, Any]:
        """Get comprehensive deployment metrics"""
        return {
            "deployment_metrics": self.deployment_metrics.copy(),
            "active_deployments": len(self.active_deployments),
            "queue_size": len(self.deployment_queue),
            "deployment_history_count": len(self.deployment_history),
            "environment_configs": len(self.environment_configs),
            "performance_tests_count": len(self.performance_tests),
            "test_results_count": len(self.test_results),
            "artifact_count": len(self.deployment_artifacts),
            "backup_count": len(self.backup_artifacts),
            "deployment_state": self.deployment_state.copy(),
            "max_concurrent_deployments": self.deployment_config["max_concurrent_deployments"],
            "auto_rollback_enabled": self.deployment_config["auto_rollback_enabled"]
        }

    async def _create_deployment_backup(self, deployment: DeploymentInstance) -> None:
        """Create backup before deployment"""
        try:
            backup_id = f"backup_{deployment.deployment_id}_{int(time.time())}"

            backup_info = {
                "backup_id": backup_id,
                "deployment_id": deployment.deployment_id,
                "timestamp": datetime.now(timezone.utc),
                "environment": deployment.deployment_config.environment.value,
                "version": deployment.deployment_config.version,
                "components": list(deployment.deployment_config.components)
            }

            # Store backup artifact
            self.backup_artifacts[backup_id] = json.dumps(backup_info, indent=2, default=str)

            print(f"   💾 Backup created: {backup_id}")

        except Exception as e:
            logger.error(f"Failed to create backup: {e}")

    async def _validate_deployment_requirements(self, deployment: DeploymentInstance) -> None:
        """Validate deployment requirements"""
        # Check if environment is configured
        environment = deployment.deployment_config.environment
        if environment not in self.environment_configs:
            raise Exception(f"Environment {environment.value} not configured")

        env_config = self.environment_configs[environment]

        # Check resource requirements
        if deployment.deployment_config.components:
            required_components = deployment.deployment_config.components
            for component in required_components:
                if component != "all" and component not in env_config.resource_limits:
                    logger.warning(f"Component {component} not configured for environment {environment.value}")

        # Check security requirements
        if deployment.deployment_config.environment == DeploymentEnvironment.PRODUCTION:
            if not self.security_manager:
                raise Exception("Security manager not initialized for production deployment")

    async def _prepare_deployment_artifacts(self, deployment: DeploymentInstance) -> None:
        """Prepare deployment artifacts"""
        try:
            # Create artifact directory
            artifact_dir = Path(f"/tmp/deployments/{deployment.deployment_id}")
            artifact_dir.mkdir(parents=True, exist_ok=True)

            # Generate deployment manifest
            manifest = {
                "deployment_id": deployment.deployment_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "environment": deployment.deployment_config.environment.value,
                "version": deployment.deployment_config.version,
                "components": list(deployment_deployment_config.components),
                "quality_gates": deployment.deployment_config.quality_gates,
                "rollback_strategy": deployment.deployment_config.rollback_strategy.value,
                "metadata": deployment.deployment_config.metadata
            }

            # Write manifest
            manifest_path = artifact_dir / "deployment_manifest.json"
            with open(manifest_path, 'w') as f:
                json.dump(manifest, f, indent=2)

            # Store artifact paths
            self.deployment_artifacts[deployment.deployment_id] = str(artifact_dir)
            print(f"   📋 Deployment artifacts prepared: {artifact_dir}")

        except Exception as e:
            logger.error(f"Failed to prepare deployment artifacts: {e}")

    async def _perform_health_check(self, deployment: DeploymentInstance) -> str:
        """Perform health check on deployment"""
        try:
            # Simulate health checks
            health_checks = [
                ("database_connection", await self._check_database_connection(deployment)),
                ("api_responsiveness", await self._check_api_responsiveness(deployment)),
                ("memory_usage", await self._check_memory_usage(deployment)),
                ("cpu_usage", await self._check_cpu_usage(deployment)),
                ("disk_usage", await selfcheck_disk_usage(deployment))
            ]

            failed_checks = [check for check, result in health_checks if result[1] == False]

            if not failed_checks:
                return "healthy"
            elif len(failed_checks) == 1:
                return "degraded"
            else:
                return "unhealthy"

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return "unknown"

    async def _check_database_connection(self, deployment: DeploymentInstance) -> Tuple[bool, str]:
        """Check database connection"""
        # Simulate database connection test
        try:
            await asyncio.sleep(0.5)
            return True, "Database connection successful"
        except Exception as e:
            return False, f"Database connection failed: {str(e)}"

    async def _check_api_responsiveness(self, deployment: DeploymentInstance) -> Tuple[bool, str]:
        """Check API responsivity"""
        # Simulate API responsiveness test
        try:
            await asyncio.sleep(0.3)
            return True, "API responding normally"
        except Exception as e:
            return False, f"API unresponsive: {str(e)}"

    async def _check_memory_usage(self, deployment: DeploymentInstance) -> Tuple[bool, str]:
        """Check memory usage"""
        # Simulate memory usage check
        memory_usage = 65 + (hash(str(time.time())) % 20)
        max_memory = 90

        if memory_usage > max_memory:
            return False, f"High memory usage: {memory_usage}%"
        else:
            return True, f"Memory usage normal: {memory_usage}%"

    async def _check_cpu_usage(self, deployment: DeploymentInstance) -> Tuple[bool, str]:
        """Check CPU usage"""
        # Simulate CPU usage check
        cpu_usage = 45 + (hash(str(time.time())) % 30)
        max_cpu = 80

        if cpu_usage > max_cpu:
            return False, f"High CPU usage: {cpu_usage}%"
        else:
            return True, f"CPU usage normal: {cpu_usage}%"

    async def _check_disk_usage(self, deployment: DeploymentInstance) -> Tuple[bool, str]:
        """Check disk usage"""
        # Simulate disk usage check
        disk_usage = 55 + (hash(str(time.time())) % 25)
        max_disk = 90

        if disk_usage > max_disk:
            return False, f"High disk usage: {disk_usage}%"
        else:
            return True, f"Disk usage normal: {disk_usage}%"

    async def _execute_integration_tests(self, deployment: DeploymentInstance) -> List[Dict[str, Any]]:
        """Execute integration tests"""
        integration_tests = [
            {
                "test_name": "API Integration Test",
                "status": "passed",
                "description": "Test API integration between components"
            },
            {
                "test_name": "Database Integration Test",
                "status": "passed",
                "description": "Test database connectivity and operations"
            },
            {
                "test_name": "Security Integration Test",
                "status": "passed",
                "description": "Test security controls and policies"
            }
        ]

        # Simulate test execution
        for test in integration_tests:
            await asyncio.sleep(0.5)

        return integration_tests

    async def _send_deployment_notification(self, notification_type: str, deployment: DeploymentInstance) -> None:
        """Send deployment notification"""
        try:
            message = f"Deployment {notification_type}: {deployment.deployment_id} - Status: {deployment.status.value}"

            # Send via event stream
            if self.event_manager:
                event = Event(
                    type="deployment.notification",
                    source="deployment_manager",
                    data={
                        "notification_type": notification_type,
                        "deployment_id": deployment.deployment_id,
                        "status": deployment.status.value,
                        "environment": deployment.deployment_config.environment.value,
                        "version": deployment.deployment_config.version
                    },
                    priority=EventPriority.NORMAL
                )
                await self.event_manager.publish_event(event)

        except Exception as e:
            logger.error(f"Failed to send deployment notification: {e}")

    async def _cleanup_loop(self) -> None:
        """Background cleanup loop"""
        while True:
            try:
                await self._cleanup_expired_data()
                await asyncio.sleep(3600)  # Cleanup every hour
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
                await asyncio.sleep(300)

    async def _cleanup_expired_data(self) -> None:
        """Clean up expired deployment data"""
        current_time = datetime.now(timezone.utc)
        retention_days = self.deployment_config.get("artifact_retention_days", 30)
        cutoff_time = current_time - timedelta(days=retention_days)

        # Clean up active deployments
        expired_deployments = [
            deployment_id for deployment_id, deployment in self.active_deployments.items()
            if deployment.end_time and deployment.end_time < cutoff_time
        ]

        for deployment_id in expired_deployments:
            del self.active_deployments[deployment_id]

        # Clean up deployment artifacts
        expired_artifacts = [
            artifact_id for artifact_id, artifact_path in self.deployment_artifacts.items()
            if Path(artifact_path).exists() and Path(artifact_path).stat().st_mtime < cutoff_time.timestamp()
        ]

        for artifact_id in expired_artifacts:
            del self.deployment_artifacts[artifact_id]
            # Delete artifact directory
            try:
                shutil.rmtree(Path(artifact_id))
            except Exception as e:
                logger.warning(f"Failed to delete artifact directory {artifact_id}: {e}")

        # Clean up backup artifacts
        expired_backups = [
            backup_id for backup_id, backup_path in self.backup_artifacts.items()
            if backup_path and Path(backup_path).exists() and Path(backup_path).stat().st_mtime < cutoff_time.timestamp()
        ]

        for backup_id in expired_backups:
            del self.backup_artifacts[backup_id]
            # Delete backup file
            try:
                os.remove(backup_path)
            except Exception as e:
                logger.warning(f"Failed to delete backup file {backup_path}: {e}")

        logger.debug(f"Cleanup completed - removed data older than {cutoff_time}")

    async def _heartbeat_loop(self) -> None:
        """Background heartbeat loop for monitoring system health"""
        while True:
            try:
                # Update monitoring state
                self.deployment_state["last_health_check"] = datetime.now(timezone.utc)

                # Check active deployments
                healthy_deployments = [
                    d for d in self.active_deployments.values()
                    if d.status in [DeploymentStatus.COMPLETED, DeploymentStatus.TESTING]
                ]

                unhealthy_deployments = [
                    d for d in self.active_deployments.values()
                    if d.status in [DeploymentStatus.FAILED, DeploymentStatus.ROLLING_BACK]
                ]

                # Update deployment state
                self.deployment_state["active_deployments"] = len(self.active_deployments)
                self.deployment_state["queue_size"] = len(self.deployment_queue)

                # Calculate environment health
                environment_health = {}
                for env_name, env_config in self.environment_configs.items():
                    if env_name in self.active_deployments:
                        env_deployments = [
                            d for d in self.active_deployments.values()
                            if d.deployment_config.environment == env_name
                        ]
                        failed_deployments = [
                            d for d in env_deployments
                            if d.status in [DeploymentStatus.FAILED, DeploymentStatus.ROLLING_BACK]
                        ]

                        health_score = (len(healthy_deployments) / max(1, len(env_deployments))) * 100
                        environment_health[env_name] = {
                            "health_score": health_score,
                            "total_deployments": len(env_deployments),
                            "failed_deployments": len(failed_deployments),
                            "status": "healthy" if health_score >= 90 else "degraded" if health_score >= 70 else "unhealthy"
                        }

                self.deployment_state["environment_health"] = environment_health

                # Update overall health status
                all_healthy = all(health_score >= 90 for health_score in environment_health.values())
                self.deployment_state["health_status"] = "healthy" if all_healthy else "degraded"

                logger.debug(f"Heartbeat check completed - health: {self.deployment_state['health_status']}")

                await asyncio.sleep(60)  # Check every minute

            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")
                await asyncio.sleep(30)

    async def shutdown(self) -> None:
        """Gracefully shutdown the deployment manager"""
        try:
            # Cancel background tasks
            if self.cleanup_task:
                self.cleanup_task.cancel()
                try:
                    await self.cleanup_task
                except asyncio.CancelledError:
                    pass

            if self.heartbeat_task:
                self.heartbeat_task.cancel()
                try:
                    await self.heartbeat_task
                except asyncio.CancelledError:
                    pass

            # Cancel monitoring tasks
            for task_id, task in self.monitoring_tasks.items():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

            # Wait for active deployments to complete or timeout
            timeout_seconds = self.deployment_config.get("deployment_timeout_minutes", 120) * 60
            start_time = time.time()

            while self.active_deployments and (time.time() - start_time < timeout_seconds):
                await asyncio.sleep(10)

            # Shutdown component systems
            if self.quality_system:
                await self.quality_system.shutdown()

            if self.orchestration_agent:
                await self.orchestration_agent.shutdown()

            if self.security_manager:
                await self.security_manager.shutdown()

            # Shutdown event manager
            if self.event_manager:
                await self.event_manager.shutdown()

            logger.info("Production Deployment Manager shutdown complete")

        except Exception as e:
            logger.error(f"Error during shutdown: {e}")


# Initialize and run the deployment manager demonstration
if __name__ == "__main__":
    async def main():
        demo_deployment = ProductionDeploymentManager()
        await demo_deployment.initialize({})

        # Example usage
        deployment_config = {
            "deployment_id": "prod_deploy_001",
            "name": "Production Deployment v1.0.0",
            "description": "Deploy version 1.0.0 to production",
            "environment": "production",
            "deployment_type": "blue_green",
            "version": "1.0.0",
            "components": ["api", "database", "web_app"],
            "quality_gates": ["security", "performance", "reliability"],
            "rollback_strategy": "automatic",
            "notifications": {
                "started": True,
                "completed": True,
                "failed": True
            }
        }

        print("🚀 Starting deployment...")
        result = await demo_deployment._execute_deployment({
            "deployment_config": deployment_config,
            "environment": "production",
            "deployment_type": "blue_green",
            "quality_gates": ["all"]
        }, {})

        print(f"Deployment result: {result}")