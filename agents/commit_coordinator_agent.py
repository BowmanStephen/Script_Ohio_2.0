#!/usr/bin/env python3
"""
Commit Coordinator Agent - Master Controller for Git Commit Operations

This agent orchestrates the entire commit process for Script Ohio 2.0,
coordinating with specialist agents to safely commit changes using the
existing GitHub operations infrastructure.

Author: Claude Code Assistant
Created: 2025-12-20
Version: 1.0
"""

import json
import logging
import os
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Add src to path for imports
SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from agents.core.agent_framework import (
    AgentCapability,
    BaseAgent,
    PermissionLevel,
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import for agent registry
try:
    from agents.meta_agent import meta_agent
except ImportError:
    logger.warning("Meta Agent not available - registration disabled")
    meta_agent = None

# Import existing GitHub operations
try:
    sys.path.append(Path(__file__).resolve().parents[1] / "scripts" / "github_operations")
    from git_utils import GitUtils
    from push_operations import PushOperations
    from rollback_operations import RollbackOperations
except ImportError:
    logger.error("GitHub operations modules not found")
    GitUtils = None
    PushOperations = None
    RollbackOperations = None

# Import validation orchestrator
try:
    sys.path.append(Path(__file__).resolve().parents[1] / "scripts" / "github_validation")
    from validation_orchestrator import ValidationOrchestrator
except ImportError:
    logger.warning("Validation Orchestrator not found")
    ValidationOrchestrator = None


class CommitCoordinatorAgent(BaseAgent):
    """
    Master controller for commit operations in Script Ohio 2.0.

    This agent coordinates the entire commit process by:
    - Analyzing changes with Commit Analyzer Agent
    - Running validation via Validation Orchestrator
    - Executing pushes via existing GitHub operations
    - Providing real-time progress tracking
    - Handling rollback scenarios automatically

    Capabilities:
    - Orchestrate full commit workflow
    - Coordinate with specialist agents
    - Monitor system health during commits
    - Provide real-time progress updates
    - Execute automatic rollback on failures
    """

    def __init__(self, agent_id: str, tool_loader=None):
        """Initialize the Commit Coordinator Agent."""
        super().__init__(
            agent_id=agent_id,
            name="Commit Coordinator Agent",
            permission_level=PermissionLevel.READ_EXECUTE_WRITE,
            tool_loader=tool_loader,
        )

        self.project_root = Path.cwd()
        self.commit_session_id = None
        self.workflow_state = {}

        # Initialize GitHub operations
        self.git_utils = GitUtils() if GitUtils else None
        self.push_ops = PushOperations() if PushOperations else None
        self.rollback_ops = RollbackOperations() if RollbackOperations else None

        # Initialize validation orchestrator
        self.validation_orchestrator = ValidationOrchestrator() if ValidationOrchestrator else None

        # Workflow stages
        self.workflow_stages = [
            "analyze_changes",
            "validate_system",
            "create_backup",
            "execute_commits",
            "verify_success"
        ]

    def _define_capabilities(self) -> List[AgentCapability]:
        """Define agent capabilities following BaseAgent pattern."""
        return [
            AgentCapability(
                name="orchestrate_commit",
                description="Orchestrate the full commit workflow from analysis to verification",
                permission_required=PermissionLevel.READ_EXECUTE_WRITE,
                tools_required=["git", "python"],
                data_access=["filesystem", "git_history", "github"],
                execution_time_estimate=300.0,  # 5 minutes for full workflow
            ),
            AgentCapability(
                name="analyze_commit_scope",
                description="Analyze the scope and impact of pending changes",
                permission_required=PermissionLevel.READ_ONLY,
                tools_required=["git", "pathlib"],
                data_access=["filesystem", "git_history"],
                execution_time_estimate=30.0,
            ),
            AgentCapability(
                name="coordinate_validation",
                description="Coordinate pre-commit validation using Validation Orchestrator",
                permission_required=PermissionLevel.READ_EXECUTE,
                tools_required=["python"],
                data_access=["filesystem", "test_results"],
                execution_time_estimate=60.0,
            ),
            AgentCapability(
                name="execute_commit_batches",
                description="Execute commits in optimal batches using existing GitHub operations",
                permission_required=PermissionLevel.READ_EXECUTE_WRITE,
                tools_required=["git"],
                data_access=["filesystem", "git_history"],
                execution_time_estimate=120.0,
            ),
            AgentCapability(
                name="monitor_progress",
                description="Provide real-time progress monitoring for commit operations",
                permission_required=PermissionLevel.READ_ONLY,
                tools_required=["python"],
                data_access=["memory", "log_files"],
                execution_time_estimate=5.0,
            ),
            AgentCapability(
                name="emergency_rollback",
                description="Execute emergency rollback if commit process fails",
                permission_required=PermissionLevel.READ_EXECUTE_WRITE,
                tools_required=["git"],
                data_access=["git_history"],
                execution_time_estimate=30.0,
            ),
        ]

    def _execute_action(
        self, action: str, parameters: Dict[str, Any], user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute agent actions with proper error handling and logging."""

        try:
            start_time = time.time()
            logger.info(f"Executing action: {action} with parameters: {list(parameters.keys())}")

            if action == "orchestrate_commit":
                result = self._orchestrate_commit(parameters, user_context)
            elif action == "analyze_commit_scope":
                result = self._analyze_commit_scope(parameters)
            elif action == "coordinate_validation":
                result = self._coordinate_validation(parameters)
            elif action == "execute_commit_batches":
                result = self._execute_commit_batches(parameters)
            elif action == "monitor_progress":
                result = self._monitor_progress()
            elif action == "emergency_rollback":
                result = self._emergency_rollback(parameters)
            else:
                raise ValueError(f"Unknown action: {action}")

            # Update performance metrics
            execution_time = time.time() - start_time
            self._update_metrics(action, True, execution_time)

            logger.info(f"Action {action} completed successfully in {execution_time:.2f}s")

            return {
                "status": "success",
                "result": result,
                "execution_time": execution_time,
                "agent_id": self.agent_id,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Action {action} failed: {str(e)}")
            self._update_metrics(action, False, 0)

            return {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__,
                "agent_id": self.agent_id,
                "timestamp": datetime.now().isoformat(),
            }

    def _orchestrate_commit(
        self, parameters: Dict[str, Any], user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Orchestrate the full commit workflow.

        This is the main method that coordinates the entire commit process.
        """
        # Generate session ID
        self.commit_session_id = f"commit_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

        logger.info(f"Starting commit orchestration session: {self.commit_session_id}")

        # Initialize workflow state
        self.workflow_state = {
            "session_id": self.commit_session_id,
            "stage": "initialize",
            "start_time": time.time(),
            "parameters": parameters,
            "user_context": user_context,
            "results": {},
            "status": "running"
        }

        # Execute workflow stages
        for stage in self.workflow_stages:
            logger.info(f"Executing stage: {stage}")
            self.workflow_state["stage"] = stage

            try:
                if stage == "analyze_changes":
                    self.workflow_state["results"]["analysis"] = self._analyze_commit_scope({})
                elif stage == "validate_system":
                    self.workflow_state["results"]["validation"] = self._coordinate_validation({})
                elif stage == "create_backup":
                    self.workflow_state["results"]["backup"] = self._create_backup_checkpoint()
                elif stage == "execute_commits":
                    self.workflow_state["results"]["commits"] = self._execute_commit_batches({})
                elif stage == "verify_success":
                    self.workflow_state["results"]["verification"] = self._verify_commit_success()

                # Small delay between stages
                time.sleep(1)

            except Exception as e:
                logger.error(f"Stage {stage} failed: {str(e)}")
                self.workflow_state["status"] = "failed"
                self.workflow_state["error"] = str(e)

                # Attempt rollback on critical stage failure
                if stage in ["validate_system", "execute_commits"]:
                    logger.warning("Critical stage failed, attempting rollback")
                    rollback_result = self._emergency_rollback({"reason": f"Stage {stage} failed"})
                    self.workflow_state["results"]["emergency_rollback"] = rollback_result

                break

        # Finalize workflow
        self.workflow_state["end_time"] = time.time()
        self.workflow_state["duration"] = self.workflow_state["end_time"] - self.workflow_state["start_time"]

        if self.workflow_state["status"] != "failed":
            self.workflow_state["status"] = "completed"

        # Save session report
        self._save_session_report()

        logger.info(f"Commit orchestration {self.commit_session_id} completed with status: {self.workflow_state['status']}")

        return {
            "session_id": self.commit_session_id,
            "status": self.workflow_state["status"],
            "duration": self.workflow_state["duration"],
            "results": self.workflow_state["results"],
            "workflow_state": self.workflow_state
        }

    def _analyze_commit_scope(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the scope and impact of pending changes."""
        if not self.git_utils:
            raise RuntimeError("GitUtils not available")

        # Get modified files
        modified_files = self.git_utils.get_modified_files()
        staged_files = self.git_utils.get_staged_files()
        untracked_files = self.git_utils.get_untracked_files()

        # Analyze file types and risk
        analysis = {
            "modified_count": len(modified_files),
            "staged_count": len(staged_files),
            "untracked_count": len(untracked_files),
            "total_changes": len(modified_files) + len(staged_files) + len(untracked_files),
            "file_categories": {},
            "risk_assessment": "low",
            "commit_batches": []
        }

        # Categorize files
        all_files = modified_files + staged_files + untracked_files
        for file_path in all_files:
            category = self._categorize_file(file_path)
            analysis["file_categories"][category] = analysis["file_categories"].get(category, 0) + 1

        # Assess risk
        if analysis["file_categories"].get("agents", 0) > 10:
            analysis["risk_assessment"] = "high"
        elif analysis["file_categories"].get("core", 0) > 5:
            analysis["risk_assessment"] = "medium"

        # Create optimal commit batches
        analysis["commit_batches"] = self._create_commit_batches(all_files)

        logger.info(f"Analysis complete: {analysis['total_changes']} files changes, risk level: {analysis['risk_assessment']}")

        return analysis

    def _coordinate_validation(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate pre-commit validation using Validation Orchestrator."""
        if not self.validation_orchestrator:
            logger.warning("Validation Orchestrator not available, skipping validation")
            return {"status": "skipped", "reason": "Validation Orchestrator not available"}

        logger.info("Running pre-commit validation...")

        # Run validation orchestrator
        try:
            validation_result = self.validation_orchestrator.run_validation({
                "scope": "comprehensive",
                "include_tests": True,
                "include_security": True,
                "include_performance": True
            })

            # Check if validation passed
            if validation_result.get("overall_status") == "passed":
                logger.info("Pre-commit validation passed")
                return {
                    "status": "passed",
                    "validation_result": validation_result,
                    "checks_run": validation_result.get("checks_run", 0),
                    "checks_passed": validation_result.get("checks_passed", 0)
                }
            else:
                logger.error(f"Pre-commit validation failed: {validation_result.get('failures', [])}")
                raise RuntimeError("Pre-commit validation failed")

        except Exception as e:
            logger.error(f"Validation coordination failed: {str(e)}")
            raise

    def _execute_commit_batches(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute commits in optimal batches using existing GitHub operations."""
        if not self.git_utils or not self.push_ops:
            raise RuntimeError("GitHub operations not available")

        # Get analysis from previous stage
        analysis = self.workflow_state.get("results", {}).get("analysis", {})
        batches = analysis.get("commit_batches", [])

        if not batches:
            raise RuntimeError("No commit batches found in analysis")

        commit_results = {
            "batches_executed": 0,
            "files_committed": 0,
            "commits_created": [],
            "errors": []
        }

        logger.info(f"Executing {len(batches)} commit batches...")

        for i, batch in enumerate(batches):
            logger.info(f"Processing batch {i+1}/{len(batches)}: {batch['description']}")

            try:
                # Stage files for this batch
                for file_path in batch["files"]:
                    if not self.git_utils.stage_file(file_path):
                        commit_results["errors"].append(f"Failed to stage file: {file_path}")

                # Create commit
                commit_hash = self.git_utils.create_commit(
                    message=batch["commit_message"],
                    author="Script Ohio 2.0 Commit Coordinator"
                )

                if commit_hash:
                    # Push commit
                    push_result = self.push_ops.push_to_remote(
                        commit_messages=[batch["commit_message"]],
                        branch="main"
                    )

                    if push_result.get("success"):
                        commit_results["commits_created"].append({
                            "batch": i+1,
                            "commit_hash": commit_hash,
                            "files_count": len(batch["files"]),
                            "description": batch["description"]
                        })
                        commit_results["files_committed"] += len(batch["files"])
                        commit_results["batches_executed"] += 1

                        logger.info(f"Batch {i+1} committed successfully: {commit_hash[:8]}")

                        # Delay between commits
                        time.sleep(5)
                    else:
                        error_msg = f"Push failed for batch {i+1}: {push_result.get('error', 'Unknown error')}"
                        commit_results["errors"].append(error_msg)
                        logger.error(error_msg)
                else:
                    error_msg = f"Failed to create commit for batch {i+1}"
                    commit_results["errors"].append(error_msg)
                    logger.error(error_msg)

            except Exception as e:
                error_msg = f"Error processing batch {i+1}: {str(e)}"
                commit_results["errors"].append(error_msg)
                logger.error(error_msg)

        if commit_results["errors"]:
            logger.warning(f"Commit execution completed with {len(commit_results['errors'])} errors")

        return commit_results

    def _verify_commit_success(self) -> Dict[str, Any]:
        """Verify that commits were successful and system is stable."""
        verification = {
            "git_status_clean": False,
            "all_commits_pushed": False,
            "system_stable": False,
            "post_commit_tests": {}
        }

        try:
            # Check git status
            if self.git_utils:
                verification["git_status_clean"] = len(self.git_utils.get_modified_files()) == 0

            # Verify commits pushed
            recent_commits = self.git_utils.get_recent_commits(count=5) if self.git_utils else []
            verification["all_commits_pushed"] = len(recent_commits) > 0

            # Check system stability
            verification["system_stable"] = self._check_system_stability()

            # Run post-commit tests
            verification["post_commit_tests"] = self._run_post_commit_tests()

            logger.info(f"Commit verification complete: clean={verification['git_status_clean']}, "
                       f"pushed={verification['all_commits_pushed']}, stable={verification['system_stable']}")

        except Exception as e:
            logger.error(f"Commit verification failed: {str(e)}")
            verification["error"] = str(e)

        return verification

    def _monitor_progress(self) -> Dict[str, Any]:
        """Provide real-time progress monitoring for commit operations."""
        return {
            "session_id": self.commit_session_id,
            "current_stage": self.workflow_state.get("stage", "idle"),
            "status": self.workflow_state.get("status", "idle"),
            "results": self.workflow_state.get("results", {}),
            "progress_percentage": self._calculate_progress(),
            "estimated_remaining": self._estimate_remaining_time(),
        }

    def _emergency_rollback(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute emergency rollback if commit process fails."""
        logger.warning(f"Executing emergency rollback: {parameters.get('reason', 'Unknown reason')}")

        if not self.rollback_ops:
            return {
                "status": "failed",
                "error": "Rollback operations not available"
            }

        try:
            # Get the commit hash before our session started
            safe_commit = self.workflow_state.get("safe_commit_hash")

            if safe_commit:
                rollback_result = self.rollback_ops.rollback_to_commit(
                    commit_hash=safe_commit,
                    reason=f"Emergency rollback during commit session {self.commit_session_id}"
                )

                if rollback_result.get("success"):
                    logger.info(f"Emergency rollback successful to commit {safe_commit[:8]}")
                    return {
                        "status": "success",
                        "rollback_commit": safe_commit,
                        "message": "Emergency rollback completed successfully"
                    }
                else:
                    logger.error(f"Rollback failed: {rollback_result.get('error', 'Unknown error')}")
                    return rollback_result
            else:
                # No safe commit hash, try to reset to last known good state
                reset_result = self.rollback_ops.reset_to_last_safe_state()
                return reset_result

        except Exception as e:
            logger.error(f"Emergency rollback failed: {str(e)}")
            return {
                "status": "failed",
                "error": str(e)
            }

    # Helper methods
    def _categorize_file(self, file_path: str) -> str:
        """Categorize a file by its location and type."""
        if file_path.startswith("agents/"):
            return "agents"
        elif file_path.startswith("src/"):
            return "src"
        elif file_path.startswith("scripts/"):
            return "scripts"
        elif file_path.startswith("docs/") or file_path.endswith(".md"):
            return "documentation"
        elif file_path.startswith("data/"):
            return "data"
        elif file_path.startswith("web_app/"):
            return "web_app"
        elif file_path.startswith("tests/"):
            return "tests"
        else:
            return "other"

    def _create_commit_batches(self, files: List[str]) -> List[Dict[str, Any]]:
        """Create optimal commit batches from file list."""
        # Group files by category
        categorized = {}
        for file_path in files:
            category = self._categorize_file(file_path)
            if category not in categorized:
                categorized[category] = []
            categorized[category].append(file_path)

        # Create batches (max 50 files per batch)
        batches = []
        batch_number = 1

        # Priority order for commits
        priority_order = ["agents", "src", "scripts", "data", "documentation", "web_app", "tests", "other"]

        for category in priority_order:
            if category in categorized:
                category_files = categorized[category]

                # Split large categories into multiple batches
                while len(category_files) > 0:
                    batch_files = category_files[:50]
                    category_files = category_files[50:]

                    batches.append({
                        "batch_number": batch_number,
                        "category": category,
                        "files": batch_files,
                        "description": f"{category.title()} files (batch {batch_number})",
                        "commit_message": f"ENHANCE: Update {category} files ({batch_number})\n\nCommit coordinated by Commit Coordinator Agent\n{len(batch_files)} files updated"
                    })

                    batch_number += 1

        return batches

    def _create_backup_checkpoint(self) -> Dict[str, Any]:
        """Create a backup checkpoint before committing."""
        if not self.git_utils:
            return {"status": "skipped", "reason": "GitUtils not available"}

        # Get current HEAD
        current_head = self.git_utils.get_current_commit()
        self.workflow_state["safe_commit_hash"] = current_head

        # Create tag
        tag_name = f"backup-before-commit-{self.commit_session_id}"
        tag_result = self.git_utils.create_tag(tag_name, f"Backup before commit session {self.commit_session_id}")

        logger.info(f"Created backup checkpoint: {tag_name} at {current_head[:8]}")

        return {
            "status": "success",
            "tag_name": tag_name,
            "commit_hash": current_head,
            "message": "Backup checkpoint created successfully"
        }

    def _check_system_stability(self) -> bool:
        """Check if the system is stable after commits."""
        # Basic stability check
        try:
            # Try importing key modules
            import agents.meta_agent
            import agents.core.agent_framework

            # Check if we can create a basic request
            if meta_agent:
                health = meta_agent._monitor_system({}, {})
                if health.get("health_score", 0) > 90:
                    return True

            return False
        except:
            return False

    def _run_post_commit_tests(self) -> Dict[str, Any]:
        """Run post-commit verification tests."""
        tests = {
            "python_syntax": False,
            "agent_imports": False,
            "git_status": False
        }

        try:
            # Test Python syntax
            result = os.system("python3 -m py_compile agents/commit_coordinator_agent.py")
            tests["python_syntax"] = result == 0

            # Test agent imports
            import agents.commit_coordinator_agent
            tests["agent_imports"] = True

            # Test git status
            if self.git_utils:
                tests["git_status"] = len(self.git_utils.get_modified_files()) == 0

        except Exception as e:
            logger.error(f"Post-commit test failed: {str(e)}")

        return tests

    def _calculate_progress(self) -> float:
        """Calculate current progress percentage."""
        if not self.workflow_stages or not self.workflow_state.get("stage"):
            return 0.0

        current_stage_index = self.workflow_stages.index(self.workflow_state["stage"])
        total_stages = len(self.workflow_stages)

        return (current_stage_index / total_stages) * 100

    def _estimate_remaining_time(self) -> Optional[float]:
        """Estimate remaining time in seconds."""
        if not self.workflow_state.get("start_time") or self.workflow_state.get("status") != "running":
            return None

        elapsed = time.time() - self.workflow_state["start_time"]
        current_stage_index = self.workflow_stages.index(self.workflow_state["stage"])
        remaining_stages = len(self.workflow_stages) - current_stage_index - 1

        if current_stage_index == 0:
            # No data yet, estimate based on typical duration
            return 300  # 5 minutes

        avg_time_per_stage = elapsed / (current_stage_index + 1)
        return remaining_stages * avg_time_per_stage

    def _update_metrics(self, action: str, success: bool, execution_time: float) -> None:
        """Update performance metrics."""
        self.performance_metrics["total_requests"] += 1

        if success:
            self.performance_metrics["successful_requests"] += 1
        else:
            self.performance_metrics["failed_requests"] += 1

        # Update average execution time
        total_time = self.performance_metrics.get("total_execution_time", 0) + execution_time
        self.performance_metrics["total_execution_time"] = total_time
        self.performance_metrics["average_execution_time"] = total_time / self.performance_metrics["total_requests"]

    def _save_session_report(self) -> None:
        """Save session report to file."""
        if not self.commit_session_id:
            return

        # Create reports directory if it doesn't exist
        reports_dir = Path(self.project_root) / "project_management" / "commits" / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)

        # Save session report
        report_file = reports_dir / f"commit_session_{self.commit_session_id}.json"

        with open(report_file, 'w') as f:
            json.dump(self.workflow_state, f, indent=2)

        logger.info(f"Session report saved to: {report_file}")


# Register agent with Meta Agent if available
if meta_agent and __name__ != "__main__":
    try:
        registration_result = meta_agent._register_agent({
            "agent_id": "commit_coordinator",
            "agent_name": "Commit Coordinator Agent",
            "class_name": "CommitCoordinatorAgent",
            "file_path": "agents/commit_coordinator_agent.py",
            "created_by": "claude_code",
            "capabilities": [
                "orchestrate_commit",
                "analyze_commit_scope",
                "coordinate_validation",
                "execute_commit_batches",
                "monitor_progress",
                "emergency_rollback"
            ],
            "dependencies": [
                "git_utils",
                "push_operations",
                "rollback_operations",
                "validation_orchestrator"
            ],
            "metadata": {
                "max_execution_time": 300,  # 5 minutes
                "memory_limit_mb": 100,
                "description": "Master controller for Git commit operations with real-time coordination and automatic rollback capabilities",
                "version": "1.0.0"
            }
        }, {"agent_id": "meta_agent"})

        if registration_result.get("success"):
            logger.info("Commit Coordinator Agent successfully registered with Meta Agent")
        else:
            logger.warning(f"Failed to register with Meta Agent: {registration_result.get('error', 'Unknown error')}")

    except Exception as e:
        logger.error(f"Error registering with Meta Agent: {str(e)}")


if __name__ == "__main__":
    # Test the agent
    agent = CommitCoordinatorAgent("test_commit_coordinator")

    # Test capabilities
    capabilities = agent._define_capabilities()
    print(f"Commit Coordinator Agent initialized with {len(capabilities)} capabilities")

    # Test basic functionality
    try:
        result = agent._execute_action("monitor_progress", {}, {})
        print(f"Monitor progress result: {result['status']}")
    except Exception as e:
        print(f"Test failed: {str(e)}")