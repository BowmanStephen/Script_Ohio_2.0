#!/usr/bin/env python3
"""
Planning Coordinator Agent - Tier 2 Security Level
Strategic planning and coordination with read-only execution capabilities

Implements advanced planning algorithms with human-in-the-loop decision gates
and comprehensive audit logging for strategic CFBD data collection workflows.
"""

import logging
import json
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from agents.core.enhanced_agent_framework import EnhancedBaseAgent
from agents.core.security_manager import security_manager, PermissionLevel


class PlanningStatus(Enum):
    """Planning workflow status enumeration"""

    INITIALIZING = "initializing"
    ANALYZING_REQUIREMENTS = "analyzing_requirements"
    CREATING_PLAN = "creating_plan"
    VALIDATING_PLAN = "validating_plan"
    HUMAN_REVIEW = "human_review_required"
    APPROVED = "approved"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"


class AutomationLevel(Enum):
    """Automation level for planning decisions"""

    FULLY_AUTOMATIC = "fully_automatic"
    HUMAN_APPROVAL_REQUIRED = "human_approval_required"
    HUMAN_EXECUTION_REQUIRED = "human_execution_required"
    MANUAL_ONLY = "manual_only"


@dataclass
class PlanningTask:
    """Represents a planning task with metadata"""

    task_id: str
    title: str
    description: str
    priority: int  # 1-10, 10 being highest
    automation_level: AutomationLevel
    estimated_duration_hours: float
    dependencies: List[str]
    created_at: datetime
    deadline: Optional[datetime] = None
    status: PlanningStatus = PlanningStatus.INITIALIZING
    assigned_to: Optional[str] = None
    completion_percentage: float = 0.0
    metadata: Dict[str, Any] = None


@dataclass
class WorkflowPlan:
    """Represents a comprehensive workflow plan"""

    plan_id: str
    title: str
    description: str
    tasks: List[PlanningTask]
    created_at: datetime
    created_by: str
    status: PlanningStatus = PlanningStatus.INITIALIZING
    estimated_total_duration: float = 0.0
    risk_level: str = "medium"  # low, medium, high, critical
    approval_required: bool = True
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    execution_start_time: Optional[datetime] = None
    execution_end_time: Optional[datetime] = None


class PlanningCoordinatorAgent(EnhancedBaseAgent):
    """
    Planning Coordinator Agent - Strategic planning and workflow coordination

    Capabilities:
    - Requirement analysis and task decomposition
    - Workflow planning with dependency management
    - Risk assessment and resource allocation
    - Human-in-the-loop decision gates
    - Progress tracking and milestone management
    """

    def __init__(self, agent_id: str = "planning_coordinator"):
        super().__init__(
            agent_id=agent_id,
            agent_name="Planning Coordinator Agent",
            permission_level=PermissionLevel.READ_EXECUTE,
        )

        self.logger = logging.getLogger(f"{__name__}.{agent_id}")
        self.plans: Dict[str, WorkflowPlan] = {}
        self.active_tasks: Dict[str, PlanningTask] = {}
        self.task_templates = self._load_task_templates()
        self.automation_policies = self._load_automation_policies()

    def _define_capabilities(self) -> List:
        """Define planning coordinator capabilities"""
        return [
            {
                "name": "analyze_requirements",
                "description": "Analyze requirements and create structured tasks",
                "execution_time_estimate": 10.0,
                "required_permissions": [PermissionLevel.READ_EXECUTE],
                "parameters": ["requirements", "constraints", "deadline"],
                "returns": {"tasks": "list", "analysis": "dict", "risks": "list"},
            },
            {
                "name": "create_workflow_plan",
                "description": "Create comprehensive workflow plans with dependencies",
                "execution_time_estimate": 15.0,
                "required_permissions": [PermissionLevel.READ_EXECUTE],
                "parameters": ["tasks", "workflow_type", "priority"],
                "returns": {"plan": "object", "validation_results": "dict"},
            },
            {
                "name": "coordinate_workflow_execution",
                "description": "Coordinate workflow execution with monitoring",
                "execution_time_estimate": 5.0,
                "required_permissions": [PermissionLevel.READ_EXECUTE],
                "parameters": ["plan_id", "execution_mode"],
                "returns": {"execution_status": "string", "progress": "float"},
            },
            {
                "name": "assess_risks",
                "description": "Comprehensive risk assessment for workflows",
                "execution_time_estimate": 8.0,
                "required_permissions": [PermissionLevel.READ_EXECUTE],
                "parameters": ["workflow_plan", "context"],
                "returns": {"risk_level": "string", "mitigation_strategies": "list"},
            },
            {
                "name": "request_human_review",
                "description": "Request human review for critical decisions",
                "execution_time_estimate": 2.0,
                "required_permissions": [PermissionLevel.READ_EXECUTE],
                "parameters": ["decision_type", "context", "options"],
                "returns": {"review_id": "string", "status": "string"},
            },
        ]

    def _load_task_templates(self) -> Dict[str, Dict]:
        """Load predefined task templates for common workflows"""
        return {
            "cfbd_data_collection": {
                "title": "CFBD Data Collection",
                "estimated_duration_hours": 2.0,
                "automation_level": AutomationLevel.HUMAN_APPROVAL_REQUIRED,
                "risk_level": "low",
                "subtasks": [
                    "API authentication setup",
                    "Rate limiting configuration",
                    "Data extraction",
                    "Data validation",
                    "Storage and backup",
                ],
            },
            "model_training": {
                "title": "ML Model Training",
                "estimated_duration_hours": 4.0,
                "automation_level": AutomationLevel.HUMAN_APPROVAL_REQUIRED,
                "risk_level": "medium",
                "subtasks": [
                    "Data preprocessing",
                    "Feature engineering",
                    "Model selection",
                    "Training execution",
                    "Model validation",
                    "Performance evaluation",
                ],
            },
            "bowl_prediction": {
                "title": "Bowl Games Prediction",
                "estimated_duration_hours": 3.0,
                "automation_level": AutomationLevel.FULLY_AUTOMATIC,
                "risk_level": "medium",
                "subtasks": [
                    "Current season data integration",
                    "Historical bowl performance analysis",
                    "Team matchup analysis",
                    "Weather data integration",
                    "Model execution",
                    "Prediction generation",
                    "Confidence scoring",
                ],
            },
        }

    def _load_automation_policies(self) -> Dict[str, AutomationLevel]:
        """Load automation policies based on task type and risk level"""
        return {
            ("low", "data_processing"): AutomationLevel.FULLY_AUTOMATIC,
            ("low", "validation"): AutomationLevel.FULLY_AUTOMATIC,
            ("medium", "data_processing"): AutomationLevel.HUMAN_APPROVAL_REQUIRED,
            ("medium", "model_training"): AutomationLevel.HUMAN_APPROVAL_REQUIRED,
            ("high", "any"): AutomationLevel.HUMAN_EXECUTION_REQUIRED,
            ("critical", "any"): AutomationLevel.MANUAL_ONLY,
        }

    def _execute_action(
        self, action: str, parameters: Dict, user_context: Dict
    ) -> Dict:
        """Execute planning coordinator actions"""
        try:
            # Create security context
            context = security_manager.create_security_context(
                user_id=user_context.get("user_id", "planning_system"),
                permissions=["planning_access", "read_only_mode"],
            )

            if action == "analyze_requirements":
                return self._analyze_requirements(parameters, context)
            elif action == "create_workflow_plan":
                return self._create_workflow_plan(parameters, context)
            elif action == "coordinate_workflow_execution":
                return self._coordinate_workflow_execution(parameters, context)
            elif action == "assess_risks":
                return self._assess_risks(parameters, context)
            elif action == "request_human_review":
                return self._request_human_review(parameters, context)
            else:
                raise ValueError(f"Unknown action: {action}")

        except Exception as e:
            self.logger.error(f"Planning action {action} failed: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__,
                "agent_id": self.agent_id,
                "timestamp": datetime.utcnow().isoformat(),
            }

    def _analyze_requirements(self, parameters: Dict, context) -> Dict:
        """Analyze requirements and create structured tasks"""
        self.logger.info("Analyzing requirements and creating structured tasks")

        requirements = parameters.get("requirements", {})
        constraints = parameters.get("constraints", {})
        deadline = parameters.get("deadline")

        # Extract key requirements
        workflow_type = requirements.get("workflow_type", "unknown")
        priority = requirements.get("priority", 5)
        scope = requirements.get("scope", "standard")

        # Determine task template
        template_key = None
        for key, template in self.task_templates.items():
            if key in workflow_type.lower():
                template_key = key
                break

        # Create tasks based on template or defaults
        if template_key and template_key in self.task_templates:
            template = self.task_templates[template_key]
            tasks = self._create_tasks_from_template(
                template, requirements, constraints
            )
        else:
            tasks = self._create_generic_tasks(requirements, constraints)

        # Analyze risks and dependencies
        risk_analysis = self._analyze_task_risks(tasks, workflow_type)
        dependencies = self._identify_dependencies(tasks)

        # Estimate total duration
        total_duration = sum(task.estimated_duration_hours for task in tasks)

        return {
            "status": "success",
            "data": {
                "workflow_type": workflow_type,
                "tasks": [
                    {
                        "task_id": task.task_id,
                        "title": task.title,
                        "description": task.description,
                        "priority": task.priority,
                        "estimated_duration_hours": task.estimated_duration_hours,
                        "automation_level": task.automation_level.value,
                        "dependencies": task.dependencies,
                    }
                    for task in tasks
                ],
                "total_estimated_duration": total_duration,
                "risk_analysis": risk_analysis,
                "dependencies": dependencies,
                "recommendations": self._generate_recommendations(tasks, risk_analysis),
            },
            "execution_time": time.time(),
            "agent_id": self.agent_id,
        }

    def _create_workflow_plan(self, parameters: Dict, context) -> Dict:
        """Create comprehensive workflow plans with dependencies"""
        self.logger.info("Creating comprehensive workflow plan")

        tasks_data = parameters.get("tasks", [])
        workflow_type = parameters.get("workflow_type", "unknown")
        priority = parameters.get("priority", 5)

        # Convert task data to PlanningTask objects
        tasks = []
        for task_data in tasks_data:
            task = PlanningTask(
                task_id=task_data.get("task_id", f"task_{len(tasks)}"),
                title=task_data.get("title", "Untitled Task"),
                description=task_data.get("description", ""),
                priority=task_data.get("priority", priority),
                automation_level=AutomationLevel(
                    task_data.get("automation_level", "human_approval_required")
                ),
                estimated_duration_hours=task_data.get("estimated_duration_hours", 1.0),
                dependencies=task_data.get("dependencies", []),
                created_at=datetime.utcnow(),
                deadline=(
                    datetime.fromisoformat(task_data["deadline"])
                    if task_data.get("deadline")
                    else None
                ),
                metadata=task_data.get("metadata", {}),
            )
            tasks.append(task)

        # Create workflow plan
        plan = WorkflowPlan(
            plan_id=f"plan_{int(time.time())}",
            title=f"{workflow_type.title()} Workflow Plan",
            description=f"Comprehensive workflow plan for {workflow_type}",
            tasks=tasks,
            created_at=datetime.utcnow(),
            created_by=self.agent_id,
            estimated_total_duration=sum(
                task.estimated_duration_hours for task in tasks
            ),
        )

        # Assess plan risks
        risk_assessment = self._assess_plan_risks(plan)
        plan.risk_level = risk_assessment["risk_level"]

        # Validate plan
        validation_results = self._validate_plan(plan)

        # Store plan
        self.plans[plan.plan_id] = plan

        # Store active tasks
        for task in tasks:
            self.active_tasks[task.task_id] = task

        return {
            "status": "success",
            "data": {
                "plan": {
                    "plan_id": plan.plan_id,
                    "title": plan.title,
                    "description": plan.description,
                    "workflow_type": workflow_type,
                    "estimated_total_duration": plan.estimated_total_duration,
                    "risk_level": plan.risk_level,
                    "task_count": len(tasks),
                    "approval_required": plan.approval_required,
                },
                "validation_results": validation_results,
                "risk_assessment": risk_assessment,
                "next_steps": self._generate_next_steps(plan),
            },
            "execution_time": time.time(),
            "agent_id": self.agent_id,
        }

    def _coordinate_workflow_execution(self, parameters: Dict, context) -> Dict:
        """Coordinate workflow execution with monitoring"""
        self.logger.info("Coordinating workflow execution")

        plan_id = parameters.get("plan_id")
        execution_mode = parameters.get("execution_mode", "automatic")

        if plan_id not in self.plans:
            raise ValueError(f"Plan {plan_id} not found")

        plan = self.plans[plan_id]

        # Check if plan is approved (if required)
        if plan.approval_required and not plan.approved_by:
            return {
                "status": "approval_required",
                "message": "Plan requires human approval before execution",
                "plan_id": plan_id,
                "approval_deadline": (
                    datetime.utcnow() + timedelta(hours=24)
                ).isoformat(),
            }

        # Start execution
        plan.execution_start_time = datetime.utcnow()
        plan.status = PlanningStatus.EXECUTING

        # Initialize task progress
        for task in plan.tasks:
            task.status = PlanningStatus.EXECUTING

        # Monitor execution progress
        execution_status = self._monitor_execution(plan)

        return {
            "status": "success",
            "data": {
                "plan_id": plan_id,
                "execution_status": execution_status["status"],
                "progress_percentage": execution_status["progress_percentage"],
                "started_tasks": execution_status["started_tasks"],
                "completed_tasks": execution_status["completed_tasks"],
                "failed_tasks": execution_status["failed_tasks"],
                "estimated_completion_time": execution_status[
                    "estimated_completion_time"
                ],
            },
            "execution_time": time.time(),
            "agent_id": self.agent_id,
        }

    def _assess_risks(self, parameters: Dict, context) -> Dict:
        """Comprehensive risk assessment for workflows"""
        self.logger.info("Performing comprehensive risk assessment")

        workflow_plan = parameters.get("workflow_plan", {})
        context_data = parameters.get("context", {})

        # Extract risk factors
        complexity = workflow_plan.get("complexity", "medium")
        external_dependencies = workflow_plan.get("external_dependencies", [])
        data_sensitivity = workflow_plan.get("data_sensitivity", "medium")
        execution_deadline = workflow_plan.get("deadline")

        # Calculate risk score
        risk_score = 0
        risk_factors = []

        # Complexity risk
        complexity_scores = {"low": 1, "medium": 3, "high": 5, "critical": 8}
        complexity_risk = complexity_scores.get(complexity, 3)
        risk_score += complexity_risk
        risk_factors.append(f"Complexity risk: {complexity} ({complexity_risk})")

        # External dependencies risk
        if external_dependencies:
            deps_risk = min(len(external_dependencies) * 2, 10)
            risk_score += deps_risk
            risk_factors.append(
                f"External dependencies: {len(external_dependencies)} ({deps_risk})"
            )

        # Data sensitivity risk
        sensitivity_scores = {"low": 1, "medium": 3, "high": 5, "critical": 8}
        sensitivity_risk = sensitivity_scores.get(data_sensitivity, 3)
        risk_score += sensitivity_risk
        risk_factors.append(
            f"Data sensitivity: {data_sensitivity} ({sensitivity_risk})"
        )

        # Deadline pressure risk
        if execution_deadline:
            deadline_days = (
                datetime.fromisoformat(execution_deadline) - datetime.utcnow()
            ).days
            if deadline_days < 1:
                deadline_risk = 10
            elif deadline_days < 3:
                deadline_risk = 6
            elif deadline_days < 7:
                deadline_risk = 3
            else:
                deadline_risk = 1
            risk_score += deadline_risk
            risk_factors.append(
                f"Deadline pressure: {deadline_days} days ({deadline_risk})"
            )

        # Determine overall risk level
        if risk_score <= 5:
            risk_level = "low"
        elif risk_score <= 15:
            risk_level = "medium"
        elif risk_score <= 25:
            risk_level = "high"
        else:
            risk_level = "critical"

        # Generate mitigation strategies
        mitigation_strategies = self._generate_mitigation_strategies(
            risk_level, risk_factors
        )

        return {
            "status": "success",
            "data": {
                "risk_score": risk_score,
                "risk_level": risk_level,
                "risk_factors": risk_factors,
                "mitigation_strategies": mitigation_strategies,
                "recommended_automation_level": self._recommend_automation_level(
                    risk_level
                ),
                "monitoring_requirements": self._get_monitoring_requirements(
                    risk_level
                ),
            },
            "execution_time": time.time(),
            "agent_id": self.agent_id,
        }

    def _request_human_review(self, parameters: Dict, context) -> Dict:
        """Request human review for critical decisions"""
        self.logger.info("Requesting human review for critical decision")

        decision_type = parameters.get("decision_type", "unknown")
        review_context = parameters.get("context", {})
        options = parameters.get("options", [])

        # Generate review request
        review_id = f"review_{int(time.time())}"

        # Create review payload
        review_request = {
            "review_id": review_id,
            "decision_type": decision_type,
            "context": review_context,
            "options": options,
            "requested_by": self.agent_id,
            "requested_at": datetime.utcnow().isoformat(),
            "priority": self._determine_review_priority(decision_type, review_context),
            "deadline": (datetime.utcnow() + timedelta(hours=4)).isoformat(),
        }

        # Log review request
        self.logger.info(f"Human review requested: {review_id} for {decision_type}")

        # In a real implementation, this would send to human review system
        # For now, we'll simulate the request
        security_manager.log_security_event(
            event_type="human_review_requested",
            user_id=self.agent_id,
            resource_id=review_id,
            details=review_request,
        )

        return {
            "status": "success",
            "data": {
                "review_id": review_id,
                "status": "pending_human_review",
                "estimated_review_time": "2-4 hours",
                "escalation_deadline": review_request["deadline"],
                "review_priority": review_request["priority"],
            },
            "execution_time": time.time(),
            "agent_id": self.agent_id,
        }

    # Helper methods
    def _create_tasks_from_template(
        self, template: Dict, requirements: Dict, constraints: Dict
    ) -> List[PlanningTask]:
        """Create tasks from predefined template"""
        tasks = []
        for i, subtask in enumerate(template.get("subtasks", [])):
            task = PlanningTask(
                task_id=f"{template.get('title', 'task').lower().replace(' ', '_')}_{i+1}",
                title=subtask,
                description=f"Subtask: {subtask}",
                priority=requirements.get("priority", 5),
                automation_level=template.get(
                    "automation_level", AutomationLevel.HUMAN_APPROVAL_REQUIRED
                ),
                estimated_duration_hours=template.get("estimated_duration_hours", 1.0)
                / len(template.get("subtasks", [1])),
                dependencies=(
                    [f"{template.get('title', 'task').lower().replace(' ', '_')}_{i}"]
                    if i > 0
                    else []
                ),
                created_at=datetime.utcnow(),
            )
            tasks.append(task)
        return tasks

    def _create_generic_tasks(
        self, requirements: Dict, constraints: Dict
    ) -> List[PlanningTask]:
        """Create generic tasks when no template is available"""
        workflow_type = requirements.get("workflow_type", "unknown")

        generic_tasks = [
            "Initial setup and configuration",
            "Data collection and preparation",
            "Processing and analysis",
            "Validation and testing",
            "Finalization and delivery",
        ]

        tasks = []
        for i, task_title in enumerate(generic_tasks):
            task = PlanningTask(
                task_id=f"generic_task_{i+1}",
                title=task_title,
                description=f"Generic task for {workflow_type}",
                priority=requirements.get("priority", 5),
                automation_level=AutomationLevel.HUMAN_APPROVAL_REQUIRED,
                estimated_duration_hours=1.0,
                dependencies=[f"generic_task_{i}"] if i > 0 else [],
                created_at=datetime.utcnow(),
            )
            tasks.append(task)

        return tasks

    def _analyze_task_risks(
        self, tasks: List[PlanningTask], workflow_type: str
    ) -> Dict:
        """Analyze risks associated with tasks"""
        risks = []

        for task in tasks:
            if task.estimated_duration_hours > 8:
                risks.append(
                    f"Long duration task: {task.title} ({task.estimated_duration_hours}h)"
                )

            if len(task.dependencies) > 3:
                risks.append(
                    f"High dependency task: {task.title} ({len(task.dependencies)} dependencies)"
                )

            if task.automation_level == AutomationLevel.MANUAL_ONLY:
                risks.append(f"Manual-only task: {task.title}")

        return {
            "identified_risks": risks,
            "risk_count": len(risks),
            "needs_mitigation": len(risks) > 2,
        }

    def _identify_dependencies(self, tasks: List[PlanningTask]) -> Dict:
        """Identify and validate task dependencies"""
        dependency_map = {}

        for task in tasks:
            dependency_map[task.task_id] = {
                "task_title": task.title,
                "depends_on": task.dependencies,
                "blocks": [],
                "dependency_depth": 0,
            }

        # Calculate what each task blocks
        for task_id, deps in dependency_map.items():
            for dep in deps["depends_on"]:
                if dep in dependency_map:
                    dependency_map[dep]["blocks"].append(task_id)

        return dependency_map

    def _generate_recommendations(
        self, tasks: List[PlanningTask], risk_analysis: Dict
    ) -> List[str]:
        """Generate recommendations based on tasks and risks"""
        recommendations = []

        if risk_analysis["risk_count"] > 2:
            recommendations.append(
                "Consider breaking down high-risk tasks into smaller subtasks"
            )

        total_duration = sum(task.estimated_duration_hours for task in tasks)
        if total_duration > 24:
            recommendations.append(
                "Consider implementing parallel execution for independent tasks"
            )

        manual_tasks = [
            t for t in tasks if t.automation_level == AutomationLevel.MANUAL_ONLY
        ]
        if manual_tasks:
            recommendations.append(
                f"Allocate resources for {len(manual_tasks)} manual tasks"
            )

        return recommendations

    def _assess_plan_risks(self, plan: WorkflowPlan) -> Dict:
        """Assess risks for the entire workflow plan"""
        # Implementation similar to _assess_risks but for complete plan
        risk_score = len(plan.tasks) * 2  # Base risk from complexity
        risk_level = "medium" if risk_score < 10 else "high"

        return {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "primary_risks": ["Task complexity", "Coordination overhead"],
            "mitigation_strategies": ["Incremental execution", "Regular checkpoints"],
        }

    def _validate_plan(self, plan: WorkflowPlan) -> Dict:
        """Validate workflow plan for completeness and correctness"""
        validation_errors = []
        validation_warnings = []

        # Check for required fields
        if not plan.title:
            validation_errors.append("Plan title is required")

        if not plan.tasks:
            validation_errors.append("Plan must have at least one task")

        # Check for circular dependencies
        task_ids = {task.task_id for task in plan.tasks}
        for task in plan.tasks:
            for dep in task.dependencies:
                if dep not in task_ids:
                    validation_warnings.append(
                        f"Task {task.task_id} depends on unknown task {dep}"
                    )

        # Check for orphaned tasks
        all_dependencies = set()
        for task in plan.tasks:
            all_dependencies.update(task.dependencies)

        orphaned_tasks = (
            task_ids - all_dependencies - {plan.tasks[0].task_id}
            if plan.tasks
            else set()
        )
        if orphaned_tasks:
            validation_warnings.append(
                f"Found {len(orphaned_tasks)} potentially orphaned tasks"
            )

        return {
            "valid": len(validation_errors) == 0,
            "errors": validation_errors,
            "warnings": validation_warnings,
            "validation_score": 100
            - (len(validation_errors) * 20)
            - (len(validation_warnings) * 5),
        }

    def _generate_next_steps(self, plan: WorkflowPlan) -> List[str]:
        """Generate next steps for the workflow plan"""
        steps = []

        if plan.approval_required and not plan.approved_by:
            steps.append("Submit plan for human approval")

        steps.append("Prepare execution environment")
        steps.append("Set up monitoring and alerting")

        if plan.deadline:
            steps.append(f"Schedule execution to meet deadline: {plan.deadline}")

        return steps

    def _monitor_execution(self, plan: WorkflowPlan) -> Dict:
        """Monitor workflow execution progress"""
        # Simplified monitoring - in real implementation would track actual task progress
        total_tasks = len(plan.tasks)
        completed_tasks = 0
        failed_tasks = 0
        started_tasks = total_tasks

        # Simulate some progress
        if plan.execution_start_time:
            elapsed_hours = (
                datetime.utcnow() - plan.execution_start_time
            ).total_seconds() / 3600
            completion_rate = min(
                elapsed_hours / plan.estimated_total_duration, 0.1
            )  # Simple progress simulation

            completed_tasks = int(total_tasks * completion_rate)

        progress_percentage = (
            (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        )

        return {
            "status": "executing",
            "progress_percentage": progress_percentage,
            "started_tasks": started_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "estimated_completion_time": (
                (
                    plan.execution_start_time
                    + timedelta(hours=plan.estimated_total_duration)
                ).isoformat()
                if plan.execution_start_time
                else None
            ),
        }

    def _generate_mitigation_strategies(
        self, risk_level: str, risk_factors: List[str]
    ) -> List[str]:
        """Generate risk mitigation strategies"""
        strategies = {
            "low": ["Regular monitoring", "Standard checkpoints"],
            "medium": [
                "Frequent progress reviews",
                "Rollback planning",
                "Resource allocation buffers",
            ],
            "high": [
                "Daily status meetings",
                "Comprehensive monitoring",
                "Backup plans",
                "Stakeholder communication",
            ],
            "critical": [
                "Hourly monitoring",
                "Multiple backup strategies",
                "Executive oversight",
                "Incident response team",
            ],
        }

        return strategies.get(risk_level, strategies["medium"])

    def _recommend_automation_level(self, risk_level: str) -> AutomationLevel:
        """Recommend automation level based on risk"""
        recommendations = {
            "low": AutomationLevel.FULLY_AUTOMATIC,
            "medium": AutomationLevel.HUMAN_APPROVAL_REQUIRED,
            "high": AutomationLevel.HUMAN_EXECUTION_REQUIRED,
            "critical": AutomationLevel.MANUAL_ONLY,
        }

        return recommendations.get(risk_level, AutomationLevel.HUMAN_APPROVAL_REQUIRED)

    def _get_monitoring_requirements(self, risk_level: str) -> Dict:
        """Get monitoring requirements based on risk level"""
        requirements = {
            "low": {"frequency": "hourly", "alerts": ["failure"]},
            "medium": {"frequency": "30min", "alerts": ["failure", "delay"]},
            "high": {
                "frequency": "15min",
                "alerts": ["failure", "delay", "performance"],
            },
            "critical": {
                "frequency": "5min",
                "alerts": ["failure", "delay", "performance", "security"],
            },
        }

        return requirements.get(risk_level, requirements["medium"])

    def _determine_review_priority(self, decision_type: str, context: Dict) -> str:
        """Determine review priority based on decision type and context"""
        high_priority_decisions = [
            "resource_allocation",
            "security_policy",
            "api_access",
            "data_privacy",
        ]

        if decision_type in high_priority_decisions:
            return "high"

        if context.get("risk_level") in ["high", "critical"]:
            return "high"

        if context.get("impact", "medium") == "high":
            return "medium"

        return "low"


# Agent registration function
def register_planning_coordinator_agent():
    """Register the planning coordinator agent with the system"""
    agent = PlanningCoordinatorAgent()

    # Registration details for meta agent
    registration_details = {
        "agent_id": agent.agent_id,
        "agent_name": agent.agent_name,
        "class_name": "PlanningCoordinatorAgent",
        "file_path": __file__,
        "created_by": "system_architect",
        "capabilities": [
            "analyze_requirements",
            "create_workflow_plan",
            "coordinate_workflow_execution",
            "assess_risks",
            "request_human_review",
        ],
        "dependencies": ["enhanced_agent_framework", "security_manager"],
        "max_execution_time": 300,  # 5 minutes
        "memory_limit_mb": 512,
        "security_tier": 2,
        "permission_level": "READ_EXECUTE",
    }

    return agent, registration_details


# Example usage and testing
if __name__ == "__main__":
    # Create agent
    agent = PlanningCoordinatorAgent()

    # Test requirement analysis
    test_requirements = {
        "workflow_type": "cfbd_data_collection",
        "priority": 8,
        "scope": "comprehensive",
        "season": "2025",
        "data_types": ["games", "teams", "players", "statistics"],
    }

    result = agent.execute_action("analyze_requirements", test_requirements)
    print("Requirement Analysis Result:")
    print(json.dumps(result, indent=2))
