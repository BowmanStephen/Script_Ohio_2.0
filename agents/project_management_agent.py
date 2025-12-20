"""
Project Management Agent

Manages project plans, progress tracking, and milestone management for the Script Ohio 2.0 multi-agent system.

Follows OpenAI agents.md best practices:
- Single responsibility: Project management and progress tracking only
- Clear interfaces: Well-defined API for plan storage/retrieval
- State management: Persistent storage of project state
- Communication: Clean handoff protocols with other agents
"""

import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.toon_format import decode, encode

from agents.core.agent_framework import AgentCapability, BaseAgent, PermissionLevel


@dataclass
class ProjectPlan:
    """Structure for project plans"""

    plan_id: str
    title: str
    description: str
    created_at: datetime
    created_by: str
    status: str  # 'draft', 'active', 'completed', 'archived'
    milestones: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    toon_data: Optional[str] = None  # TOON format for LLM processing


@dataclass
class ProgressEntry:
    """Structure for progress tracking"""

    plan_id: str
    timestamp: datetime
    agent_id: str
    milestone: str
    status: str  # 'started', 'in_progress', 'completed', 'failed'
    details: Dict[str, Any]
    completion_percentage: float


class ProjectManagementAgent(BaseAgent):
    """
    Project Management Agent

    Manages the complete project lifecycle including:
    - Plan creation and storage
    - Progress tracking and milestone management
    - Archive management
    - Cross-agent coordination for project workflows
    """

    def __init__(self):
        super().__init__(
            agent_id="project_management_agent",
            name="Project Management Agent",
            permission_level=PermissionLevel.READ_EXECUTE_WRITE,
        )

        # Set up directory structure
        self.base_dir = Path("project_management")
        self.plans_dir = self.base_dir / "plans"
        self.progress_dir = self.base_dir / "progress"
        self.archives_dir = self.base_dir / "archives"
        self.templates_dir = self.base_dir / "templates"

        # Ensure directories exist
        for dir_path in [
            self.plans_dir,
            self.progress_dir,
            self.archives_dir,
            self.templates_dir,
        ]:
            dir_path.mkdir(parents=True, exist_ok=True)

    def _define_capabilities(self) -> List[AgentCapability]:
        """Define agent capabilities following OpenAI best practices"""
        return [
            AgentCapability(
                name="create_plan",
                description="Create new project plan with milestones",
                permission_required=PermissionLevel.READ_EXECUTE_WRITE,
                tools_required=["file_operations", "toon_encoder"],
                data_access=["project_management/plans", "project_management/progress"],
                execution_time_estimate=2.0,
            ),
            AgentCapability(
                name="track_progress",
                description="Track and update project progress",
                permission_required=PermissionLevel.READ_EXECUTE_WRITE,
                tools_required=["file_operations", "state_management"],
                data_access=["project_management/progress"],
                execution_time_estimate=1.0,
            ),
            AgentCapability(
                name="get_plan_status",
                description="Get current status of project plans",
                permission_required=PermissionLevel.READ_EXECUTE,
                tools_required=["file_operations", "state_query"],
                data_access=["project_management/plans", "project_management/progress"],
                execution_time_estimate=0.5,
            ),
            AgentCapability(
                name="archive_plan",
                description="Archive completed plans",
                permission_required=PermissionLevel.READ_EXECUTE_WRITE,
                tools_required=["file_operations"],
                data_access=["project_management/plans", "project_management/archives"],
                execution_time_estimate=1.0,
            ),
            AgentCapability(
                name="list_active_plans",
                description="List all active project plans",
                permission_required=PermissionLevel.READ_EXECUTE,
                tools_required=["file_operations"],
                data_access=["project_management/plans"],
                execution_time_estimate=0.5,
            ),
        ]

    def _execute_action(
        self, action: str, parameters: Dict, user_context: Dict
    ) -> Dict:
        """Execute agent actions with proper error handling"""
        try:
            if action == "create_plan":
                return self._create_plan(parameters, user_context)
            elif action == "track_progress":
                return self._track_progress(parameters, user_context)
            elif action == "get_plan_status":
                return self._get_plan_status(parameters, user_context)
            elif action == "archive_plan":
                return self._archive_plan(parameters, user_context)
            elif action == "list_active_plans":
                return self._list_active_plans(parameters, user_context)
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}",
                    "available_actions": [
                        cap.name for cap in self._define_capabilities()
                    ],
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "action": action,
                "parameters": parameters,
            }

    def _create_plan(self, params: Dict, context: Dict) -> Dict:
        """Create a new project plan"""
        required_fields = ["plan_id", "title", "description", "milestones"]
        for field in required_fields:
            if field not in params:
                return {"success": False, "error": f"Missing required field: {field}"}

        # Create plan object
        plan = ProjectPlan(
            plan_id=params["plan_id"],
            title=params["title"],
            description=params["description"],
            created_at=datetime.now(timezone.utc),
            created_by=context.get("user_id", "system"),
            status=params.get("status", "draft"),
            milestones=params["milestones"],
            metadata=params.get("metadata", {}),
        )

        # Convert to TOON format for LLM processing
        plan_data = asdict(plan)
        plan_data["created_at"] = plan.created_at.isoformat()
        plan.toon_data = encode(plan_data)

        # Save plan
        plan_file = self.plans_dir / f"{plan.plan_id}.json"
        with open(plan_file, "w") as f:
            json.dump(plan_data, f, indent=2)

        # Save TOON version for efficient LLM access
        toon_file = self.plans_dir / f"{plan.plan_id}.toon"
        with open(toon_file, "w") as f:
            f.write(plan.toon_data)

        return {
            "success": True,
            "plan_id": plan.plan_id,
            "status": plan.status,
            "milestone_count": len(plan.milestones),
            "files_created": [str(plan_file), str(toon_file)],
        }

    def _track_progress(self, params: Dict, context: Dict) -> Dict:
        """Track progress on a project milestone"""
        required_fields = ["plan_id", "milestone", "status"]
        for field in required_fields:
            if field not in params:
                return {"success": False, "error": f"Missing required field: {field}"}

        # Create progress entry
        progress = ProgressEntry(
            plan_id=params["plan_id"],
            timestamp=datetime.now(timezone.utc),
            agent_id=context.get("agent_id", "user"),
            milestone=params["milestone"],
            status=params["status"],
            details=params.get("details", {}),
            completion_percentage=params.get("completion_percentage", 0.0),
        )

        # Save progress entry
        progress_file = self.progress_dir / f"{progress.plan_id}_progress.json"

        # Load existing progress or create new
        existing_progress = []
        if progress_file.exists():
            with open(progress_file, "r") as f:
                existing_progress = json.load(f)

        # Add new entry
        progress_data = asdict(progress)
        progress_data["timestamp"] = progress.timestamp.isoformat()
        existing_progress.append(progress_data)

        # Save updated progress
        with open(progress_file, "w") as f:
            json.dump(existing_progress, f, indent=2)

        return {
            "success": True,
            "plan_id": progress.plan_id,
            "milestone": progress.milestone,
            "status": progress.status,
            "completion_percentage": progress.completion_percentage,
            "total_entries": len(existing_progress),
        }

    def _get_plan_status(self, params: Dict, context: Dict) -> Dict:
        """Get current status of a project plan"""
        plan_id = params.get("plan_id")
        if not plan_id:
            return {"success": False, "error": "Missing plan_id"}

        # Load plan
        plan_file = self.plans_dir / f"{plan_id}.json"
        if not plan_file.exists():
            return {"success": False, "error": f"Plan {plan_id} not found"}

        with open(plan_file, "r") as f:
            plan = json.load(f)

        # Load progress
        progress_file = self.progress_dir / f"{plan_id}_progress.json"
        progress = []
        if progress_file.exists():
            with open(progress_file, "r") as f:
                progress = json.load(f)

        # Calculate completion percentage
        if progress:
            latest_completion = max(
                entry.get("completion_percentage", 0) for entry in progress
            )
        else:
            latest_completion = 0.0

        return {
            "success": True,
            "plan": plan,
            "progress_entries": len(progress),
            "completion_percentage": latest_completion,
            "last_updated": (
                max([entry["timestamp"] for entry in progress])
                if progress
                else plan["created_at"]
            ),
        }

    def _archive_plan(self, params: Dict, context: Dict) -> Dict:
        """Archive a completed project plan"""
        plan_id = params.get("plan_id")
        if not plan_id:
            return {"success": False, "error": "Missing plan_id"}

        # Move plan files to archive
        archive_dir = self.archives_dir / datetime.now().strftime("%Y-%m")
        archive_dir.mkdir(exist_ok=True)

        files_to_archive = [
            self.plans_dir / f"{plan_id}.json",
            self.plans_dir / f"{plan_id}.toon",
            self.progress_dir / f"{plan_id}_progress.json",
        ]

        archived_files = []
        for file_path in files_to_archive:
            if file_path.exists():
                archive_path = archive_dir / file_path.name
                file_path.rename(archive_path)
                archived_files.append(str(archive_path))

        return {
            "success": True,
            "plan_id": plan_id,
            "archived_files": archived_files,
            "archive_location": str(archive_dir),
        }

    def _list_active_plans(self, params: Dict, context: Dict) -> Dict:
        """List all active project plans"""
        active_plans = []

        for plan_file in self.plans_dir.glob("*.json"):
            try:
                with open(plan_file, "r") as f:
                    plan = json.load(f)
                    if plan.get("status") in ["draft", "active"]:
                        # Get progress summary
                        progress_file = (
                            self.progress_dir / f"{plan['plan_id']}_progress.json"
                        )
                        progress_count = 0
                        if progress_file.exists():
                            with open(progress_file, "r") as f:
                                progress = json.load(f)
                                progress_count = len(progress)

                        active_plans.append(
                            {
                                "plan_id": plan["plan_id"],
                                "title": plan["title"],
                                "status": plan["status"],
                                "created_at": plan["created_at"],
                                "milestone_count": len(plan.get("milestones", [])),
                                "progress_entries": progress_count,
                            }
                        )
            except Exception as e:
                continue  # Skip corrupted files

        return {
            "success": True,
            "active_plans": active_plans,
            "total_count": len(active_plans),
        }


# Singleton instance for easy access
project_management_agent = ProjectManagementAgent()
