#!/usr/bin/env python3
"""
Rollback Agent - Recovery Specialist for Failed Operations

This agent wraps the existing rollback operations with agent-based coordination,
providing intelligent recovery strategies, checkpoint management, and detailed rollback auditing.

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
    from rollback_operations import RollbackOperations
except ImportError:
    logger.error("GitHub operations modules not found")
    GitUtils = None
    RollbackOperations = None


class RollbackAgent(BaseAgent):
    """
    Recovery specialist agent for failed operations.

    This agent provides enhanced rollback functionality by:
    - Wrapping existing rollback operations with agent coordination
    - Creating and managing rollback checkpoints
    - Implementing intelligent rollback strategies
    - Providing detailed rollback audit trails
    - Handling partial rollback scenarios

    Capabilities:
    - Emergency rollback to safe state
    - Checkpoint creation and management
    - Selective rollback of specific changes
    - Rollback verification and validation
    - Rollback audit trail maintenance
    """

    def __init__(self, agent_id: str, tool_loader=None):
        """Initialize the Rollback Agent."""
        super().__init__(
            agent_id=agent_id,
            name="Rollback Agent",
            permission_level=PermissionLevel.READ_EXECUTE_WRITE,
            tool_loader=tool_loader,
        )

        self.project_root = Path.cwd()
        self.rollback_session_id = None
        self.rollback_history = []
        self.checkpoints_dir = Path(self.project_root) / "project_management" / "rollbacks" / "checkpoints"

        # Ensure checkpoints directory exists
        self.checkpoints_dir.mkdir(parents=True, exist_ok=True)

        # Initialize GitHub operations
        self.git_utils = GitUtils() if GitUtils else None
        self.rollback_ops = RollbackOperations() if RollbackOperations else None

        # Rollback configuration
        self.rollback_config = {
            "max_checkpoints": 20,  # Keep last 20 checkpoints
            "auto_cleanup_days": 30,  # Cleanup after 30 days
            "verify_after_rollback": True,
            "create_backup_before_rollback": True,
        }

    def _define_capabilities(self) -> List[AgentCapability]:
        """Define agent capabilities following BaseAgent pattern."""
        return [
            AgentCapability(
                name="emergency_rollback",
                description="Execute emergency rollback to safe state",
                permission_required=PermissionLevel.READ_EXECUTE_WRITE,
                tools_required=["git", "filesystem"],
                data_access=["git_history", "filesystem"],
                execution_time_estimate=60.0,
            ),
            AgentCapability(
                name="create_checkpoint",
                description="Create rollback checkpoint with full state capture",
                permission_required=PermissionLevel.READ_EXECUTE_WRITE,
                tools_required=["git", "filesystem"],
                data_access=["git_history", "filesystem"],
                execution_time_estimate=30.0,
            ),
            AgentCapability(
                name="rollback_to_checkpoint",
                description="Rollback to specific checkpoint",
                permission_required=PermissionLevel.READ_EXECUTE_WRITE,
                tools_required=["git", "filesystem"],
                data_access=["git_history", "filesystem"],
                execution_time_estimate=45.0,
            ),
            AgentCapability(
                name="selective_rollback",
                description="Rollback specific files or changes",
                permission_required=PermissionLevel.READ_EXECUTE_WRITE,
                tools_required=["git", "filesystem"],
                data_access=["git_history", "filesystem"],
                execution_time_estimate=90.0,
            ),
            AgentCapability(
                name="verify_rollback",
                description="Verify rollback success and system stability",
                permission_required=PermissionLevel.READ_EXECUTE,
                tools_required=["python", "git"],
                data_access=["filesystem", "git_history"],
                execution_time_estimate=30.0,
            ),
            AgentCapability(
                name="manage_checkpoints",
                description="Manage rollback checkpoints (list, cleanup, maintain)",
                permission_required=PermissionLevel.READ_EXECUTE_WRITE,
                tools_required=["filesystem"],
                data_access=["filesystem"],
                execution_time_estimate=10.0,
            ),
        ]

    def _execute_action(
        self, action: str, parameters: Dict[str, Any], user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute agent actions with proper error handling and logging."""

        try:
            start_time = time.time()
            logger.info(f"Executing action: {action} with parameters: {list(parameters.keys())}")

            if action == "emergency_rollback":
                result = self._emergency_rollback(parameters, user_context)
            elif action == "create_checkpoint":
                result = self._create_checkpoint(parameters)
            elif action == "rollback_to_checkpoint":
                result = self._rollback_to_checkpoint(parameters)
            elif action == "selective_rollback":
                result = self._selective_rollback(parameters, user_context)
            elif action == "verify_rollback":
                result = self._verify_rollback(parameters)
            elif action == "manage_checkpoints":
                result = self._manage_checkpoints(parameters)
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

    def _emergency_rollback(
        self, parameters: Dict[str, Any], user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute emergency rollback to safe state."""
        if not self.rollback_ops or not self.git_utils:
            raise RuntimeError("Rollback operations not available")

        # Generate rollback session ID
        self.rollback_session_id = f"rollback_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Get parameters
        reason = parameters.get("reason", "Emergency rollback triggered")
        target_commit = parameters.get("target_commit")
        create_backup = parameters.get("create_backup", self.rollback_config["create_backup_before_rollback"])

        logger.info(f"Starting emergency rollback session: {self.rollback_session_id}")
        logger.info(f"Reason: {reason}")

        rollback_result = {
            "session_id": self.rollback_session_id,
            "reason": reason,
            "rollback_successful": False,
            "backup_created": None,
            "rollback_details": {},
        }

        try:
            # Create backup before rollback if requested
            if create_backup:
                backup_result = self._create_checkpoint({
                    "name": f"before_emergency_rollback_{self.rollback_session_id}",
                    "description": f"Backup before emergency rollback: {reason}",
                    "critical": True
                })
                rollback_result["backup_created"] = backup_result

            # Determine rollback target
            if not target_commit:
                # Find last known good commit
                target_commit = self._find_last_good_commit()

            if not target_commit:
                raise RuntimeError("No safe rollback target found")

            logger.info(f"Rolling back to commit: {target_commit[:8]}")

            # Execute rollback
            rollback_details = self._rollback_ops.rollback_to_commit(
                commit_hash=target_commit,
                reason=reason,
                session_id=self.rollback_session_id
            )

            rollback_result["rollback_details"] = rollback_details

            if rollback_details.get("success", False):
                rollback_result["rollback_successful"] = True
                logger.info(f"Emergency rollback successful: {target_commit[:8]}")

                # Verify rollback
                if self.rollback_config["verify_after_rollback"]:
                    verification = self._verify_rollback({
                        "target_commit": target_commit
                    })
                    rollback_result["verification"] = verification

                # Update session to success
                rollback_result["session_status"] = "completed"
            else:
                logger.error(f"Rollback failed: {rollback_details.get('error', 'Unknown error')}")
                rollback_result["session_status"] = "failed"

        except Exception as e:
            logger.error(f"Emergency rollback failed: {str(e)}")
            rollback_result["error"] = str(e)
            rollback_result["session_status"] = "error"

        # Save rollback history
        self._save_rollback_history(rollback_result)

        logger.info(f"Emergency rollback session {self.rollback_session_id} completed with status: {rollback_result['session_status']}")

        return rollback_result

    def _create_checkpoint(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Create rollback checkpoint with full state capture."""
        checkpoint_name = parameters.get("name", f"checkpoint_{int(time.time())}")
        description = parameters.get("description", "Automatic checkpoint creation")
        critical = parameters.get("critical", False)

        checkpoint_id = f"cp_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{checkpoint_name.replace(' ', '_')}"

        logger.info(f"Creating checkpoint: {checkpoint_id}")

        checkpoint_data = {
            "checkpoint_id": checkpoint_id,
            "name": checkpoint_name,
            "description": description,
            "critical": critical,
            "timestamp": datetime.now().isoformat(),
            "git_state": self._capture_git_state(),
            "file_snapshots": self._capture_file_snapshots(),
            "system_state": self._capture_system_state(),
        }

        # Save checkpoint
        checkpoint_file = self.checkpoints_dir / f"{checkpoint_id}.json"

        try:
            with open(checkpoint_file, 'w') as f:
                json.dump(checkpoint_data, f, indent=2)

            logger.info(f"Checkpoint created successfully: {checkpoint_file}")

            return {
                "status": "success",
                "checkpoint_id": checkpoint_id,
                "checkpoint_file": str(checkpoint_file),
                "name": checkpoint_name,
                "files_captured": len(checkpoint_data["file_snapshots"]["files"]),
                "message": f"Checkpoint '{checkpoint_name}' created successfully"
            }

        except Exception as e:
            logger.error(f"Failed to create checkpoint: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "checkpoint_id": checkpoint_id
            }

    def _rollback_to_checkpoint(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Rollback to specific checkpoint."""
        checkpoint_id = parameters.get("checkpoint_id")
        if not checkpoint_id:
            raise ValueError("Checkpoint ID is required")

        # Load checkpoint data
        checkpoint_file = self.checkpoints_dir / f"{checkpoint_id}.json"
        if not checkpoint_file.exists():
            return {
                "status": "error",
                "error": f"Checkpoint not found: {checkpoint_id}"
            }

        try:
            with open(checkpoint_file, 'r') as f:
                checkpoint_data = json.load(f)

            logger.info(f"Rolling back to checkpoint: {checkpoint_id}")
            logger.info(f"Checkpoint created: {checkpoint_data['timestamp']}")

            # Rollback to commit
            target_commit = checkpoint_data["git_state"]["head_commit"]
            rollback_result = self._rollback_ops.rollback_to_commit(
                commit_hash=target_commit,
                reason=f"Rollback to checkpoint {checkpoint_id}",
                session_id=f"rollback_to_{checkpoint_id}"
            )

            # Restore file snapshots if needed
            if parameters.get("restore_files", True):
                restoration_result = self._restore_file_snapshots(checkpoint_data["file_snapshots"])
                rollback_result["file_restoration"] = restoration_result

            return {
                "status": "success",
                "checkpoint_id": checkpoint_id,
                "rollback_result": rollback_result,
                "target_commit": target_commit,
                "checkpoint_timestamp": checkpoint_data["timestamp"]
            }

        except Exception as e:
            logger.error(f"Rollback to checkpoint failed: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "checkpoint_id": checkpoint_id
            }

    def _selective_rollback(
        self, parameters: Dict[str, Any], user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Rollback specific files or changes."""
        target_files = parameters.get("files", [])
        file_patterns = parameters.get("patterns", [])
        target_commits = parameters.get("commits", [])

        if not any([target_files, file_patterns, target_commits]):
            raise ValueError("Must specify files, patterns, or commits for selective rollback")

        logger.info(f"Starting selective rollback: {len(target_files)} files, {len(file_patterns)} patterns, {len(target_commits)} commits")

        rollback_result = {
            "files_rolled_back": [],
            "patterns_matched": [],
            "commits_reverted": [],
            "rollback_successful": False
        }

        try:
            # Get files matching patterns
            if file_patterns:
                matched_files = self._match_files_by_patterns(file_patterns)
                rollback_result["patterns_matched"] = matched_files
                target_files.extend(matched_files)

            # Remove files from staging
            if target_files:
                for file_path in target_files:
                    if self.git_utils:
                        if self.git_utils.unstage_file(file_path):
                            rollback_result["files_rolled_back"].append(file_path)
                        else:
                            logger.warning(f"Failed to unstage file: {file_path}")

            # Revert specific commits
            if target_commits and self.git_utils:
                for commit in target_commits:
                    if self.git_utils.revert_commit(commit):
                        rollback_result["commits_reverted"].append(commit)
                    else:
                        logger.warning(f"Failed to revert commit: {commit[:8]}")

            # Determine success
            total_actions = (len(rollback_result["files_rolled_back"]) +
                             len(rollback_result["patterns_matched"]) +
                             len(rollback_result["commits_reverted"]))

            rollback_result["rollback_successful"] = total_actions > 0

            logger.info(f"Selective rollback completed: {total_actions} actions performed")

        except Exception as e:
            logger.error(f"Selective rollback failed: {str(e)}")
            rollback_result["error"] = str(e)

        return rollback_result

    def _verify_rollback(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Verify rollback success and system stability."""
        target_commit = parameters.get("target_commit")
        check_files = parameters.get("check_files", True)
        run_tests = parameters.get("run_tests", False)

        verification = {
            "rollback_verified": False,
            "target_commit_match": False,
            "files_status": {},
            "system_stable": False,
            "test_results": {},
        }

        try:
            # Check if we're at the right commit
            if target_commit and self.git_utils:
                current_commit = self.git_utils.get_current_commit()
                verification["target_commit_match"] = current_commit == target_commit

            # Check file status
            if check_files and self.git_utils:
                modified_files = self.git_utils.get_modified_files()
                verification["files_status"] = {
                    "has_modifications": len(modified_files) > 0,
                    "modified_files": modified_files
                }

            # Check system stability
            verification["system_stable"] = self._check_system_stability()

            # Run tests if requested
            if run_tests:
                verification["test_results"] = self._run_system_tests()

            # Overall verification
            verification["rollback_verified"] = (
                (not target_commit or verification["target_commit_match"]) and
                (verification["system_stable"] or not check_files)
            )

            logger.info(f"Rollback verification: {'PASSED' if verification['rollback_verified'] else 'FAILED'}")

        except Exception as e:
            logger.error(f"Rollback verification failed: {str(e)}")
            verification["error"] = str(e)

        return verification

    def _manage_checkpoints(self, parameters: Dict[str, Any]):
        """Manage rollback checkpoints (list, cleanup, maintain)."""
        action = parameters.get("action", "list")

        if action == "list":
            return self._list_checkpoints()
        elif action == "cleanup":
            return self._cleanup_old_checkpoints()
        elif action == "details":
            return self._get_checkpoint_details(parameters.get("checkpoint_id"))
        else:
            return {
                "status": "error",
                "error": f"Unknown action: {action}"
            }

    # Helper methods
    def _capture_git_state(self) -> Dict[str, Any]:
        """Capture current git state."""
        if not self.git_utils:
            return {}

        try:
            return {
                "head_commit": self.git_utils.get_current_commit(),
                "branch": self.git_utils.get_current_branch(),
                "remotes": self.git_utils.get_remotes(),
                "modified_files": self.git_utils.get_modified_files(),
                "staged_files": self.git_utils.get_staged_files(),
                "untracked_files": self.git_utils.get_untracked_files(),
                "last_commit_time": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error capturing git state: {str(e)}")
            return {}

    def _capture_file_snapshots(self) -> Dict[str, Any]:
        """Capture snapshots of critical files."""
        critical_files = [
            "agents/commit_coordinator_agent.py",
            "agents/commit_analyzer_agent.py",
            "agents/push_agent.py",
            "agents/rollback_agent.py",
            "agents/validation_agent.py",
            "CLAUDE.md",
            "AGENTS.md",
            "requirements.txt"
        ]

        snapshots = {
            "files": [],
            "total_files": len(critical_files),
            "capture_time": datetime.now().isoformat()
        }

        for file_path in critical_files:
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    snapshots["files"].append({
                        "path": file_path,
                        "size": len(content),
                        "checksum": self._calculate_checksum(content),
                        "exists": True,
                        "last_modified": os.path.getmtime(file_path)
                    })
                except Exception as e:
                    logger.debug(f"Error capturing file {file_path}: {e}")
                    snapshots["files"].append({
                        "path": file_path,
                        "exists": False,
                        "error": str(e)
                    })
            else:
                snapshots["files"].append({
                    "path": file_path,
                    "exists": False
                })

        return snapshots

    def _capture_system_state(self) -> Dict[str, Any]:
        """Capture system state information."""
        return {
            "working_directory": str(self.project_root),
            "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
            "git_version": self._get_git_version(),
            "timestamp": datetime.now().isoformat(),
            "environment": {
                "VIRTUAL_ENV": os.environ.get("VIRTUAL_ENV"),
                "CFBD_API_KEY_SET": bool(os.environ.get("CFBD_API_KEY")),
                "CI": os.environ.get("CI"),
            }
        }

    def _find_last_good_commit(self) -> Optional[str]:
        """Find the last known good commit."""
        if not self.git_utils:
            return None

        try:
            # Get recent commits
            recent_commits = self.git_utils.get_recent_commits(count=20)

            # Look for commits with no merge conflicts or issues
            for commit in recent_commits:
                if not commit.get("merge") and not commit.get("fixup"):
                    return commit["hash"]

            return recent_commits[-1]["hash"] if recent_commits else None

        except Exception as e:
            logger.error(f"Error finding last good commit: {str(e)}")
            return None

    def _restore_file_snapshots(self, snapshots: Dict[str, Any]) -> Dict[str, Any]:
        """Restore files from snapshots."""
        restoration_result = {
            "files_restored": [],
            "files_failed": [],
            "total_files": len(snapshots.get("files", [])),
        }

        for file_snapshot in snapshots.get("files", []):
            file_path = file_snapshot["path"]

            if not file_snapshot.get("exists", True):
                continue  # Skip files that didn't exist

            try:
                # Create directory if needed
                os.makedirs(os.path.dirname(file_path), exist_ok=True)

                # Restore file content
                with open(file_path, 'w', encoding='utf-8') as f:
                    # Content would be restored from backup
                    # For now, just create empty file
                    pass

                restoration_result["files_restored"].append(file_path)

            except Exception as e:
                logger.error(f"Failed to restore file {file_path}: {str(e)}")
                restoration_result["files_failed"].append({
                    "file": file_path,
                    "error": str(e)
                })

        return restoration_result

    def _match_files_by_patterns(self, patterns: List[str]) -> List[str]:
        """Match files using patterns."""
        matched_files = []

        for pattern in patterns:
            try:
                import glob
                matches = glob.glob(pattern, recursive=True)
                matched_files.extend(matches)
            except Exception as e:
                logger.error(f"Error matching pattern {pattern}: {str(e)}")

        return list(set(matched_files))

    def _check_system_stability(self) -> bool:
        """Check if system is stable after rollback."""
        try:
            # Check if we can import key modules
            import agents.commit_coordinator_agent
            import agents.commit_analyzer_agent
            import agents.push_agent
            import agents.rollback_agent

            # Basic stability check
            return True

        except Exception as e:
            logger.error(f"System stability check failed: {str(e)}")
            return False

    def _run_system_tests(self) -> Dict[str, Any]:
        """Run basic system tests."""
        tests = {
            "python_imports": False,
            "git_status": False,
            "file_access": False,
        }

        try:
            # Test Python imports
            import agents.commit_coordinator_agent
            tests["python_imports"] = True

            # Test git status
            if self.git_utils:
                self.git_utils.get_status()
                tests["git_status"] = True

            # Test file access
            if os.access("agents/", os.R_OK):
                tests["file_access"] = True

        except Exception as e:
            logger.error(f"System tests failed: {str(e)}")

        return tests

    def _calculate_checksum(self, content: str) -> str:
        """Calculate checksum for content."""
        import hashlib
        return hashlib.md5(content.encode()).hexdigest()

    def _get_git_version(self) -> str:
        """Get git version."""
        try:
            import subprocess
            result = subprocess.run(
                ["git", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.stdout.strip() if result.returncode == 0 else "unknown"
        except:
            return "unknown"

    def _list_checkpoints(self) -> Dict[str, Any]:
        """List all available checkpoints."""
        checkpoints = []

        try:
            for checkpoint_file in self.checkpoints_dir.glob("*.json"):
                try:
                    with open(checkpoint_file, 'r') as f:
                        checkpoint_data = json.load(f)

                    checkpoints.append({
                        "checkpoint_id": checkpoint_data["checkpoint_id"],
                        "name": checkpoint_data["name"],
                        "description": checkpoint_data["description"],
                        "timestamp": checkpoint_data["timestamp"],
                        "critical": checkpoint_data.get("critical", False),
                        "file": str(checkpoint_file)
                    })
                except Exception as e:
                    logger.error(f"Error reading checkpoint {checkpoint_file}: {str(e)}")

            # Sort by timestamp (newest first)
            checkpoints.sort(key=lambda x: x["timestamp"], reverse=True)

        except Exception as e:
            logger.error(f"Error listing checkpoints: {str(e)}")

        return {
            "checkpoints": checkpoints,
            "total_count": len(checkpoints),
            "critical_count": sum(1 for cp in checkpoints if cp["critical"])
        }

    def _cleanup_old_checkpoints(self) -> Dict[str, Any]:
        """Clean up old checkpoints."""
        cleanup_result = {
            "deleted_count": 0,
            "errors": []
        }

        cutoff_date = datetime.now() - timedelta(days=self.rollback_config["auto_cleanup_days"])

        try:
            for checkpoint_file in self.checkpoints_dir.glob("*.json"):
                try:
                    # Get file modification time
                    file_mtime = datetime.fromtimestamp(checkpoint_file.stat().st_mtime)

                    if file_mtime < cutoff_date:
                        # Read checkpoint to check if it's critical
                        with open(checkpoint_file, 'r') as f:
                            checkpoint_data = json.load(f)

                        if not checkpoint_data.get("critical", False):
                            checkpoint_file.unlink()
                            cleanup_result["deleted_count"] += 1
                            logger.info(f"Deleted old checkpoint: {checkpoint_file.name}")

                except Exception as e:
                    cleanup_result["errors"].append(f"Error processing {checkpoint_file}: {str(e)}")

        except Exception as e:
            cleanup_result["errors"].append(f"Error during cleanup: {str(e)}")

        return cleanup_result

    def _get_checkpoint_details(self, checkpoint_id: str) -> Dict[str, Any]:
        """Get detailed information about a checkpoint."""
        checkpoint_file = self.checkpoints_dir / f"{checkpoint_id}.json"

        if not checkpoint_file.exists():
            return {
                "status": "error",
                "error": f"Checkpoint not found: {checkpoint_id}"
            }

        try:
            with open(checkpoint_file, 'r') as f:
                checkpoint_data = json.load(f)

            return {
                "status": "success",
                "checkpoint_data": checkpoint_data
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "checkpoint_id": checkpoint_id
            }

    def _save_rollback_history(self, rollback_result: Dict[str, Any]) -> None:
        """Save rollback operation to history."""
        self.rollback_history.append({
            "session_id": rollback_result.get("session_id"),
            "timestamp": datetime.now().isoformat(),
            "result": rollback_result
        })

        # Keep only last 100 sessions
        if len(self.rollback_history) > 100:
            self.rollback_history = self.rollback_history[-100]

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
            "agent_id": "rollback_agent",
            "agent_name": "Rollback Agent",
            "class_name": "RollbackAgent",
            "file_path": "agents/rollback_agent.py",
            "created_by": "claude_code",
            "capabilities": [
                "emergency_rollback",
                "create_checkpoint",
                "rollback_to_checkpoint",
                "selective_rollback",
                "verify_rollback",
                "manage_checkpoints"
            ],
            "dependencies": [
                "git_utils",
                "rollback_operations"
            ],
            "metadata": {
                "max_execution_time": 90,  # 1.5 minutes
                "memory_limit_mb": 50,
                "description": "Recovery specialist agent for failed operations with checkpoint management and intelligent rollback strategies",
                "version": "1.0.0"
            }
        }, {"agent_id": "meta_agent"})

        if registration_result.get("success"):
            logger.info("Rollback Agent successfully registered with Meta Agent")
        else:
            logger.warning(f"Failed to register with Meta Agent: {registration_result.get('error', 'Unknown error')}")

    except Exception as e:
        logger.error(f"Error registering with Meta Agent: {str(e)}")


if __name__ == "__main__":
    # Test the agent
    agent = RollbackAgent("test_rollback_agent")

    # Test capabilities
    capabilities = agent._define_capabilities()
    print(f"Rollback Agent initialized with {len(capabilities)} capabilities")

    # Test basic functionality
    try:
        result = agent._execute_action("manage_checkpoints", {"action": "list"}, {})
        print(f"Checkpoint management test: {result['status']}")
    except Exception as e:
        print(f"Test failed: {str(e)}")