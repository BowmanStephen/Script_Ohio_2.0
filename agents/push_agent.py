#!/usr/bin/env python3
"""
Push Agent - Safe Push Operations with Agent Coordination

This agent wraps the existing GitHub push operations with agent-based coordination,
providing enhanced safety, retry logic, and real-time monitoring.

Author: Claude Code Assistant
Created: 2025-12-20
Version: 1.0
"""

import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

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
except ImportError:
    logger.error("GitHub operations modules not found")
    GitUtils = None
    PushOperations = None


class PushAgent(BaseAgent):
    """
    Safe push operations agent with agent coordination.

    This agent provides enhanced push functionality by:
    - Wrapping existing push operations with agent coordination
    - Implementing intelligent retry logic with exponential backoff
    - Providing real-time push status monitoring
    - Handling push conflicts and resolution strategies
    - Maintaining detailed push audit trails

    Capabilities:
    - Safe push operations with validation
    - Batch push coordination
    - Conflict detection and resolution
    - Push status monitoring
    - Automatic retry with backoff
    """

    def __init__(self, agent_id: str, tool_loader=None):
        """Initialize the Push Agent."""
        super().__init__(
            agent_id=agent_id,
            name="Push Agent",
            permission_level=PermissionLevel.READ_EXECUTE_WRITE,
            tool_loader=tool_loader,
        )

        self.project_root = Path.cwd()
        self.push_session_id = None
        self.push_history = []

        # Initialize GitHub operations
        self.git_utils = GitUtils() if GitUtils else None
        self.push_ops = PushOperations() if PushOperations else None

        # Push configuration
        self.push_config = {
            "max_retries": 3,
            "retry_delay_base": 5,  # seconds
            "max_retry_delay": 60,  # seconds
            "push_timeout": 300,  # seconds
            "batch_size": 10,  # max commits per batch
        }

    def _define_capabilities(self) -> List[AgentCapability]:
        """Define agent capabilities following BaseAgent pattern."""
        return [
            AgentCapability(
                name="safe_push",
                description="Safely push commits with validation and monitoring",
                permission_required=PermissionLevel.READ_EXECUTE_WRITE,
                tools_required=["git", "github_api"],
                data_access=["git_history", "remote_repo"],
                execution_time_estimate=60.0,
            ),
            AgentCapability(
                name="batch_push",
                description="Push multiple commits in coordinated batches",
                permission_required=PermissionLevel.READ_EXECUTE_WRITE,
                tools_required=["git", "github_api"],
                data_access=["git_history", "remote_repo"],
                execution_time_estimate=120.0,
            ),
            AgentCapability(
                name="validate_before_push",
                description="Run comprehensive validation before pushing",
                permission_required=PermissionLevel.READ_EXECUTE,
                tools_required=["python", "git"],
                data_access=["filesystem", "git_history"],
                execution_time_estimate=30.0,
            ),
            AgentCapability(
                name="handle_push_conflicts",
                description="Detect and resolve push conflicts intelligently",
                permission_required=PermissionLevel.READ_EXECUTE_WRITE,
                tools_required=["git"],
                data_access=["git_history", "filesystem"],
                execution_time_estimate=45.0,
            ),
            AgentCapability(
                name="monitor_push_status",
                description="Monitor push operations in real-time",
                permission_required=PermissionLevel.READ_ONLY,
                tools_required=["python", "git"],
                data_access=["git_history"],
                execution_time_estimate=5.0,
            ),
            AgentCapability(
                name="retry_failed_push",
                description="Retry failed pushes with exponential backoff",
                permission_required=PermissionLevel.READ_EXECUTE_WRITE,
                tools_required=["git"],
                data_access=["git_history"],
                execution_time_estimate=90.0,
            ),
        ]

    def _execute_action(
        self, action: str, parameters: Dict[str, Any], user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute agent actions with proper error handling and logging."""

        try:
            start_time = time.time()
            logger.info(f"Executing action: {action} with parameters: {list(parameters.keys())}")

            if action == "safe_push":
                result = self._safe_push(parameters, user_context)
            elif action == "batch_push":
                result = self._batch_push(parameters, user_context)
            elif action == "validate_before_push":
                result = self._validate_before_push(parameters)
            elif action == "handle_push_conflicts":
                result = self._handle_push_conflicts(parameters)
            elif action == "monitor_push_status":
                result = self._monitor_push_status()
            elif action == "retry_failed_push":
                result = self._retry_failed_push(parameters)
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

    def _safe_push(
        self, parameters: Dict[str, Any], user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Safely push commits with validation and monitoring."""
        if not self.push_ops or not self.git_utils:
            raise RuntimeError("GitHub operations not available")

        # Generate push session ID
        self.push_session_id = f"push_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Get parameters
        commits = parameters.get("commits", [])
        branch = parameters.get("branch", "main")
        remote = parameters.get("remote", "origin")
        validate_first = parameters.get("validate_first", True)

        logger.info(f"Starting safe push session: {self.push_session_id}")

        push_result = {
            "session_id": self.push_session_id,
            "commits_pushed": [],
            "commits_failed": [],
            "validation_results": None,
            "push_summary": {},
        }

        try:
            # Pre-push validation
            if validate_first:
                validation_result = self._validate_before_push({
                    "commits": commits,
                    "branch": branch
                })
                push_result["validation_results"] = validation_result

                if not validation_result.get("passed", True):
                    raise RuntimeError(f"Pre-push validation failed: {validation_result.get('failures', [])}")

            # Check remote connection
            if not self._check_remote_connection(remote):
                raise RuntimeError(f"Cannot connect to remote: {remote}")

            # Get current branch
            current_branch = self.git_utils.get_current_branch()
            if current_branch != branch:
                logger.info(f"Switching to branch: {branch}")
                if not self.git_utils.switch_branch(branch):
                    raise RuntimeError(f"Failed to switch to branch: {branch}")

            # Push commits
            for commit in commits:
                commit_result = self._push_single_commit(commit, branch, remote)

                if commit_result["success"]:
                    push_result["commits_pushed"].append({
                        "commit": commit,
                        "result": commit_result
                    })
                    logger.info(f"Successfully pushed: {commit[:8]}")
                else:
                    push_result["commits_failed"].append({
                        "commit": commit,
                        "error": commit_result.get("error", "Unknown error")
                    })
                    logger.error(f"Failed to push: {commit[:8]} - {commit_result.get('error')}")

            # Create push summary
            push_result["push_summary"] = {
                "total_commits": len(commits),
                "successful": len(push_result["commits_pushed"]),
                "failed": len(push_result["commits_failed"]),
                "success_rate": len(push_result["commits_pushed"]) / len(commits) if commits else 0,
                "session_duration": time.time() - start_time
            }

            # Save push history
            self._save_push_history(push_result)

            logger.info(f"Safe push session {self.push_session_id} completed: "
                       f"{push_result['push_summary']['successful']}/{push_result['push_summary']['total']} commits pushed")

            return push_result

        except Exception as e:
            logger.error(f"Safe push session failed: {str(e)}")
            push_result["error"] = str(e)
            push_result["session_duration"] = time.time() - start_time
            self._save_push_history(push_result)
            raise

    def _batch_push(
        self, parameters: Dict[str, Any], user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Push multiple commits in coordinated batches."""
        commits = parameters.get("commits", [])
        batch_size = parameters.get("batch_size", self.push_config["batch_size"])

        if not commits:
            return {"status": "success", "message": "No commits to push"}

        batches = [
            commits[i:i + batch_size]
            for i in range(0, len(commits), batch_size)
        ]

        batch_results = {
            "total_batches": len(batches),
            "batch_results": [],
            "overall_summary": {}
        }

        logger.info(f"Starting batch push: {len(batches)} batches, {len(commits)} total commits")

        for i, batch in enumerate(batches):
            logger.info(f"Processing batch {i+1}/{len(batches)} with {len(batch)} commits")

            try:
                batch_result = self._safe_push({
                    "commits": batch,
                    "batch_number": i + 1,
                    "validate_first": i == 0  # Only validate first batch
                }, user_context)

                batch_results["batch_results"].append({
                    "batch_number": i + 1,
                    "commits_count": len(batch),
                    "result": batch_result
                })

                # Delay between batches
                if i < len(batches) - 1:
                    time.sleep(5)

            except Exception as e:
                logger.error(f"Batch {i+1} failed: {str(e)}")
                batch_results["batch_results"].append({
                    "batch_number": i + 1,
                    "commits_count": len(batch),
                    "error": str(e)
                })

        # Calculate overall summary
        total_commits = len(commits)
        successful_commits = sum(
            len(br["result"].get("commits_pushed", []))
            for br in batch_results["batch_results"]
            if "result" in br
        )

        batch_results["overall_summary"] = {
            "total_commits": total_commits,
            "successful_commits": successful_commits,
            "success_rate": successful_commits / total_commits if total_commits > 0 else 0,
            "successful_batches": sum(1 for br in batch_results["batch_results"] if "error" not in br)
        }

        logger.info(f"Batch push completed: {batch_results['overall_summary']['successful_commits']}/"
                   f"{batch_results['overall_summary']['total_commits']} commits pushed")

        return batch_results

    def _validate_before_push(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Run comprehensive validation before pushing."""
        commits = parameters.get("commits", [])
        branch = parameters.get("branch", "main")

        validation = {
            "passed": True,
            "checks": {},
            "warnings": [],
            "failures": []
        }

        logger.info("Running pre-push validation...")

        # Check if commits exist locally
        validation["checks"]["commits_exist"] = self._check_commits_exist(commits)
        if not validation["checks"]["commits_exist"]["all_exist"]:
            validation["failures"].append("Some commits do not exist locally")
            validation["passed"] = False

        # Check working directory status
        if self.git_utils:
            modified_files = self.git_utils.get_modified_files()
            if modified_files:
                validation["warnings"].append(f"Working directory has {len(modified_files)} uncommitted changes")

        # Check remote status
        validation["checks"]["remote_status"] = self._check_remote_status()
        if not validation["checks"]["remote_status"]["connected"]:
            validation["failures"].append("Cannot connect to remote repository")
            validation["passed"] = False

        # Check branch status
        validation["checks"]["branch_status"] = self._check_branch_status(branch)
        if not validation["checks"]["branch_status"]["exists"]:
            validation["warnings"].append(f"Branch {branch} does not exist remotely")

        # Check for recent pushes
        validation["checks"]["recent_pushes"] = self._check_recent_pushes()

        logger.info(f"Pre-push validation completed: {'PASSED' if validation['passed'] else 'FAILED'}")

        return validation

    def _handle_push_conflicts(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Detect and resolve push conflicts intelligently."""
        conflict_info = parameters.get("conflict_info", {})

        resolution = {
            "conflict_detected": False,
            "conflict_type": None,
            "resolution_strategy": None,
            "resolution_result": None,
        }

        if not self.git_utils:
            return {
                "status": "failed",
                "error": "GitUtils not available for conflict resolution"
            }

        # Check for conflicts
        conflict_check = self._detect_conflicts()
        if conflict_check["has_conflicts"]:
            resolution["conflict_detected"] = True
            resolution["conflict_type"] = conflict_check["type"]

            # Determine resolution strategy
            if conflict_check["type"] == "fast_forward":
                resolution["resolution_strategy"] = "pull_latest"
                resolution_result = self._resolve_fast_forward_conflict()
            elif conflict_check["type"] == "diverged":
                resolution["resolution_strategy"] = "rebase_and_merge"
                resolution_result = self._resolve_diverged_conflict()
            else:
                resolution["resolution_strategy"] = "manual_intervention"
                resolution_result = {"status": "requires_manual"}

            resolution["resolution_result"] = resolution_result
        else:
            resolution["conflict_detected"] = False

        return resolution

    def _monitor_push_status(self) -> Dict[str, Any]:
        """Monitor push operations in real-time."""
        status = {
            "current_session": self.push_session_id,
            "active_pushes": [],
            "recent_history": self.push_history[-5:],  # Last 5 push sessions
            "git_status": None,
            "remote_status": None,
        }

        # Get current git status
        if self.git_utils:
            status["git_status"] = {
                "clean": len(self.git_utils.get_modified_files()) == 0,
                "current_branch": self.git_utils.get_current_branch(),
                "last_commit": self.git_utils.get_current_commit(),
            }

        # Get remote status
        status["remote_status"] = self._check_remote_status()

        return status

    def _retry_failed_push(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Retry failed pushes with exponential backoff."""
        failed_push_info = parameters.get("failed_push_info", {})
        max_retries = parameters.get("max_retries", self.push_config["max_retries"])

        retry_result = {
            "retry_successful": False,
            "attempts": 0,
            "final_result": None,
            "retry_history": []
        }

        for attempt in range(max_retries + 1):
            retry_delay = min(
                self.push_config["retry_delay_base"] * (2 ** attempt),
                self.push_config["max_retry_delay"]
            )

            if attempt > 0:
                logger.info(f"Retry attempt {attempt}/{max_retries} after {retry_delay}s delay")
                time.sleep(retry_delay)

            retry_result["attempts"] += 1

            try:
                # Attempt the push again
                push_result = self._safe_push(failed_push_info, {})
                retry_result["retry_history"].append({
                    "attempt": attempt + 1,
                    "delay": retry_delay,
                    "result": push_result
                })

                if push_result.get("push_summary", {}).get("success_rate", 0) == 1.0:
                    retry_result["retry_successful"] = True
                    retry_result["final_result"] = push_result
                    logger.info(f"Push successful on attempt {attempt + 1}")
                    break

            except Exception as e:
                logger.error(f"Retry attempt {attempt + 1} failed: {str(e)}")
                retry_result["retry_history"].append({
                    "attempt": attempt + 1,
                    "delay": retry_delay,
                    "error": str(e)
                })

        return retry_result

    # Helper methods
    def _push_single_commit(
        self, commit: str, branch: str, remote: str
    ) -> Dict[str, Any]:
        """Push a single commit."""
        try:
            # Use existing push operations
            push_result = self.push_ops.push_to_remote(
                commit_hashes=[commit],
                branch=branch,
                remote=remote,
                force=False
            )

            return push_result

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _check_remote_connection(self, remote: str) -> bool:
        """Check connection to remote repository."""
        try:
            if self.git_utils:
                return self.git_utils.check_remote_connection(remote)
            return False
        except:
            return False

    def _check_commits_exist(self, commits: List[str]) -> Dict[str, Any]:
        """Check if all commits exist locally."""
        if not self.git_utils:
            return {"all_exist": False, "missing": commits}

        missing = []
        for commit in commits:
            if not self.git_utils.commit_exists(commit):
                missing.append(commit)

        return {
            "all_exist": len(missing) == 0,
            "missing": missing,
            "checked_count": len(commits)
        }

    def _check_remote_status(self) -> Dict[str, Any]:
        """Check remote repository status."""
        try:
            if self.git_utils:
                remotes = self.git_utils.get_remotes()
                return {
                    "connected": len(remotes) > 0,
                    "remotes": remotes,
                    "default_remote": remotes[0] if remotes else None
                }
            return {"connected": False, "remotes": []}
        except:
            return {"connected": False, "remotes": []}

    def _check_branch_status(self, branch: str) -> Dict[str, Any]:
        """Check branch status."""
        try:
            if self.git_utils:
                branches = self.git_utils.get_remote_branches()
                return {
                    "exists": branch in branches,
                    "remote_branches": branches,
                    "is_tracking": self.git_utils.is_tracking_branch(branch)
                }
            return {"exists": False, "remote_branches": []}
        except:
            return {"exists": False, "remote_branches": []}

    def _check_recent_pushes(self) -> Dict[str, Any]:
        """Check for recent pushes to avoid conflicts."""
        try:
            if self.git_utils:
                recent_commits = self.git_utils.get_recent_commits(count=5)
                return {
                    "has_recent_pushes": len(recent_commits) > 0,
                    "recent_commits": recent_commits,
                    "last_push_time": recent_commits[0]["date"] if recent_commits else None
                }
            return {"has_recent_pushes": False}
        except:
            return {"has_recent_pushes": False}

    def _detect_conflicts(self) -> Dict[str, Any]:
        """Detect type of git conflicts."""
        try:
            if self.git_utils:
                # Check if we're ahead or behind
                ahead_behind = self.git_utils.get_ahead_behind()

                if ahead_behind["behind"] > 0:
                    if ahead_behind["ahead"] > 0:
                        return {"has_conflicts": True, "type": "diverged"}
                    else:
                        return {"has_conflicts": True, "type": "behind"}
                elif ahead_behind["ahead"] > 0:
                    return {"has_conflicts": False, "type": "ahead"}
                else:
                    return {"has_conflicts": False, "type": "up_to_date"}

            return {"has_conflicts": False, "type": "unknown"}
        except:
            return {"has_conflicts": False, "type": "error"}

    def _resolve_fast_forward_conflict(self) -> Dict[str, Any]:
        """Resolve fast-forward conflicts by pulling latest changes."""
        try:
            if self.git_utils:
                pull_result = self.git_utils.pull_latest()
                return {
                    "status": "success",
                    "message": "Fast-forward conflict resolved by pulling latest changes",
                    "pull_result": pull_result
                }
            return {"status": "failed", "error": "GitUtils not available"}
        except Exception as e:
            return {"status": "failed", "error": str(e)}

    def _resolve_diverged_conflict(self) -> Dict[str, Any]:
        """Resolve diverged conflicts."""
        # This is complex - for now return manual intervention
        return {
            "status": "requires_manual",
            "message": "Diverged history detected - manual intervention required",
            "recommendation": "Consider rebasing or merging manually"
        }

    def _save_push_history(self, push_result: Dict[str, Any]) -> None:
        """Save push operation to history."""
        self.push_history.append({
            "session_id": push_result.get("session_id"),
            "timestamp": datetime.now().isoformat(),
            "result": push_result
        })

        # Keep only last 50 sessions
        if len(self.push_history) > 50:
            self.push_history = self.push_history[-50:]

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


# Register agent with Meta Agent if available
if meta_agent and __name__ != "__main__":
    try:
        registration_result = meta_agent._register_agent({
            "agent_id": "push_agent",
            "agent_name": "Push Agent",
            "class_name": "PushAgent",
            "file_path": "agents/push_agent.py",
            "created_by": "claude_code",
            "capabilities": [
                "safe_push",
                "batch_push",
                "validate_before_push",
                "handle_push_conflicts",
                "monitor_push_status",
                "retry_failed_push"
            ],
            "dependencies": [
                "git_utils",
                "push_operations"
            ],
            "metadata": {
                "max_execution_time": 120,  # 2 minutes
                "memory_limit_mb": 50,
                "description": "Safe push operations with agent coordination, validation, and automatic retry capabilities",
                "version": "1.0.0"
            }
        }, {"agent_id": "meta_agent"})

        if registration_result.get("success"):
            logger.info("Push Agent successfully registered with Meta Agent")
        else:
            logger.warning(f"Failed to register with Meta Agent: {registration_result.get('error', 'Unknown error')}")

    except Exception as e:
        logger.error(f"Error registering with Meta Agent: {str(e)}")


if __name__ == "__main__":
    # Test the agent
    agent = PushAgent("test_push_agent")

    # Test capabilities
    capabilities = agent._define_capabilities()
    print(f"Push Agent initialized with {len(capabilities)} capabilities")

    # Test basic functionality
    try:
        result = agent._execute_action("monitor_push_status", {}, {})
        print(f"Push status monitoring test: {result['status']}")
    except Exception as e:
        print(f"Test failed: {str(e)}")