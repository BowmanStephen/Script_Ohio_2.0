#!/usr/bin/env python3
"""
Rollback Manager - Emergency Rollback and Restore System

Manages system rollback points and provides emergency restoration capabilities
for cleanup operations. Includes file backup, git state management, and
configuration restoration.

Ensures system can be safely restored to previous states after cleanup operations.

Author: Autonomous Code Orchestration System
Created: 2025-01-20
Version: 1.0
"""

import json
import os
import shutil
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.observability import (
    ErrorCategory,
    ErrorEvent,
    ErrorSeverity,
    configure_logging,
    get_logger,
)

configure_logging(service_name="agents")
logger = get_logger(__name__, component="rollback_manager", service_name="agents")


class RollbackPoint:
    """Represents a system rollback point"""

    def __init__(
        self,
        rollback_id: str,
        session_id: str,
        description: str,
        backup_dir: Path
    ):
        self.rollback_id = rollback_id
        self.session_id = session_id
        self.description = description
        self.backup_dir = backup_dir
        self.created_at = time.time()
        self.timestamp = datetime.now().isoformat()
        self.git_commit = self._get_git_commit()
        self.file_manifest = {}
        self.config_snapshots = {}
        self.size_mb = 0

    def _get_git_commit(self) -> str:
        """Get current git commit hash"""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.stdout.strip() if result.returncode == 0 else "unknown"
        except:
            return "unknown"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "rollback_id": self.rollback_id,
            "session_id": self.session_id,
            "description": self.description,
            "created_at": self.created_at,
            "timestamp": self.timestamp,
            "git_commit": self.git_commit,
            "backup_dir": str(self.backup_dir),
            "file_count": len(self.file_manifest),
            "config_count": len(self.config_snapshots),
            "size_mb": self.size_mb
        }


class RollbackManager:
    """
    Manages rollback points and provides emergency restoration capabilities.

    Creates comprehensive system snapshots including files, git state,
    and configuration for complete restoration capability.
    """

    def __init__(self, rollback_dir: Optional[str] = None):
        self.rollback_dir = Path(rollback_dir or "project_management/rollback")
        self.rollback_dir.mkdir(parents=True, exist_ok=True)

        self.active_rollbacks: Dict[str, RollbackPoint] = {}
        self.rollback_index_file = self.rollback_dir / "rollback_index.json"

        # Load existing rollback index
        self._load_rollback_index()

        # File patterns to always backup
        self.critical_patterns = [
            "*.json",
            "*.yaml",
            "*.yml",
            "*.cfg",
            "*.ini",
            "*.toml",
            "*.md",
            "requirements.txt",
            "package.json",
            "tsconfig.json",
            ".gitignore"
        ]

        # Directories to always backup
        self.critical_directories = [
            "agents/core/",
            "src/",
            "config/",
            "web_app/src/",
            ".claude/"
        ]

        logger.info(f"Rollback Manager initialized with directory: {self.rollback_dir}")

    def create_rollback_point(
        self,
        session_id: str,
        description: str,
        scopes: Optional[List[str]] = None,
        include_all: bool = False
    ) -> RollbackPoint:
        """Create a comprehensive rollback point"""

        rollback_id = f"rollback_{int(time.time() * 1000)}"
        backup_dir = self.rollback_dir / rollback_id
        backup_dir.mkdir(parents=True, exist_ok=True)

        rollback_point = RollbackPoint(
            rollback_id=rollback_id,
            session_id=session_id,
            description=description,
            backup_dir=backup_dir
        )

        logger.info(
            f"Creating rollback point: {rollback_id}",
            extra={
                "event": "rollback_create_start",
                "rollback_id": rollback_id,
                "session_id": session_id,
                "description": description
            }
        )

        try:
            # 1. Backup git state
            self._backup_git_state(rollback_point)

            # 2. Backup critical files
            self._backup_critical_files(rollback_point, scopes, include_all)

            # 3. Backup configuration files
            self._backup_configurations(rollback_point)

            # 4. Calculate backup size
            rollback_point.size_mb = self._calculate_directory_size(backup_dir)

            # 5. Create metadata file
            self._save_rollback_metadata(rollback_point)

            # 6. Add to active rollbacks
            self.active_rollbacks[rollback_id] = rollback_point

            # 7. Update index
            self._update_rollback_index()

            logger.info(
                f"Rollback point created successfully: {rollback_id}",
                extra={
                    "event": "rollback_create_complete",
                    "rollback_id": rollback_id,
                    "size_mb": rollback_point.size_mb,
                    "file_count": len(rollback_point.file_manifest)
                }
            )

            return rollback_point

        except Exception as e:
            logger.error(f"Failed to create rollback point {rollback_id}: {e}")
            # Clean up partial backup
            if backup_dir.exists():
                shutil.rmtree(backup_dir)
            raise

    def restore_rollback_point(
        self,
        rollback_id: str,
        force: bool = False,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """Restore system from a rollback point"""

        rollback_point = self.active_rollbacks.get(rollback_id)
        if not rollback_point:
            return {
                "success": False,
                "error": f"Rollback point {rollback_id} not found"
            }

        logger.info(
            f"Restoring from rollback point: {rollback_id}",
            extra={
                "event": "rollback_restore_start",
                "rollback_id": rollback_id,
                "dry_run": dry_run
            }
        )

        restore_plan = {
            "rollback_id": rollback_id,
            "session_id": rollback_point.session_id,
            "dry_run": dry_run,
            "operations": [],
            "success": False,
            "error": None
        }

        try:
            # 1. Validate rollback point
            validation_result = self._validate_rollback_point(rollback_point)
            if not validation_result["valid"] and not force:
                restore_plan["error"] = validation_result["error"]
                return restore_plan

            # 2. Create current state backup before restore
            pre_restore_backup = None
            if not dry_run:
                try:
                    pre_restore_backup = self.create_rollback_point(
                        session_id=f"pre_restore_{rollback_point.session_id}",
                        description=f"Pre-restore backup before restoring {rollback_id}",
                        scopes=["all"],
                        include_all=False
                    )
                    restore_plan["operations"].append({
                        "operation": "pre_restore_backup",
                        "success": True,
                        "backup_id": pre_restore_backup.rollback_id
                    })
                except Exception as e:
                    logger.warning(f"Failed to create pre-restore backup: {e}")

            # 3. Plan restore operations
            restore_operations = self._plan_restore_operations(rollback_point)
            restore_plan["operations"].extend(restore_operations)

            if dry_run:
                restore_plan["success"] = True
                restore_plan["message"] = "Dry run completed - operations planned"
                return restore_plan

            # 4. Execute restore operations
            for operation in restore_operations:
                if operation["operation"] == "restore_files":
                    self._execute_file_restore(rollback_point, operation)
                elif operation["operation"] == "restore_git":
                    self._execute_git_restore(rollback_point, operation)
                elif operation["operation"] == "restore_config":
                    self._execute_config_restore(rollback_point, operation)

            restore_plan["success"] = True
            restore_plan["message"] = f"Successfully restored from rollback point {rollback_id}"

            logger.info(
                f"Rollback restore completed: {rollback_id}",
                extra={
                    "event": "rollback_restore_complete",
                    "rollback_id": rollback_id,
                    "success": True
                }
            )

            return restore_plan

        except Exception as e:
            error_msg = f"Rollback restore failed: {str(e)}"
            restore_plan["error"] = error_msg
            logger.error(error_msg)

            # Attempt emergency rollback to pre-restore state if available
            if pre_restore_backup and not dry_run:
                try:
                    logger.info(f"Attempting emergency rollback to {pre_restore_backup.rollback_id}")
                    emergency_restore = self.restore_rollback_point(
                        pre_restore_backup.rollback_id,
                        force=True
                    )
                    restore_plan["emergency_restore"] = emergency_restore
                except Exception as emergency_error:
                    logger.error(f"Emergency rollback failed: {emergency_error}")
                    restore_plan["emergency_restore_failed"] = True

            return restore_plan

    def list_rollback_points(
        self,
        session_id: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """List available rollback points"""

        rollbacks = list(self.active_rollbacks.values())

        if session_id:
            rollbacks = [r for r in rollbacks if r.session_id == session_id]

        # Sort by creation time (newest first)
        rollbacks.sort(key=lambda r: r.created_at, reverse=True)

        if limit:
            rollbacks = rollbacks[:limit]

        return [r.to_dict() for r in rollbacks]

    def delete_rollback_point(self, rollback_id: str, force: bool = False) -> bool:
        """Delete a rollback point"""

        rollback_point = self.active_rollbacks.get(rollback_id)
        if not rollback_point:
            return False

        try:
            # Delete backup directory
            if rollback_point.backup_dir.exists():
                shutil.rmtree(rollback_point.backup_dir)

            # Remove from active rollbacks
            del self.active_rollbacks[rollback_id]

            # Update index
            self._update_rollback_index()

            logger.info(f"Deleted rollback point: {rollback_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete rollback point {rollback_id}: {e}")
            return False

    def cleanup_old_rollbacks(self, days_to_keep: int = 30) -> int:
        """Clean up old rollback points"""

        cutoff_time = time.time() - (days_to_keep * 24 * 60 * 60)

        old_rollbacks = [
            (rollback_id, rollback_point)
            for rollback_id, rollback_point in self.active_rollbacks.items()
            if rollback_point.created_at < cutoff_time
        ]

        deleted_count = 0
        for rollback_id, rollback_point in old_rollbacks:
            if self.delete_rollback_point(rollback_id):
                deleted_count += 1

        logger.info(
            f"Cleaned up {deleted_count} old rollback points",
            extra={"event": "rollback_cleanup", "deleted_count": deleted_count}
        )

        return deleted_count

    def _backup_git_state(self, rollback_point: RollbackPoint) -> None:
        """Backup git repository state"""

        try:
            # Backup git state info
            git_info = {
                "current_commit": rollback_point.git_commit,
                "branch": self._get_git_branch(),
                "status": self._get_git_status(),
                "remotes": self._get_git_remotes()
            }

            git_backup_file = rollback_point.backup_dir / "git_state.json"
            with open(git_backup_file, 'w') as f:
                json.dump(git_info, f, indent=2)

            # Create patch of uncommitted changes if any
            if git_info["status"]:
                patch_file = rollback_point.backup_dir / "uncommitted_changes.patch"
                subprocess.run(
                    ["git", "diff", "--output", str(patch_file)],
                    check=True,
                    timeout=30
                )

        except Exception as e:
            logger.warning(f"Failed to backup git state: {e}")

    def _backup_critical_files(
        self,
        rollback_point: RollbackPoint,
        scopes: Optional[List[str]],
        include_all: bool
    ) -> None:
        """Backup critical files and directories"""

        files_to_backup = set()
        directories_to_backup = set()

        # Always include critical directories
        for dir_pattern in self.critical_directories:
            for dir_path in Path(".").glob(dir_pattern):
                if dir_path.is_dir():
                    directories_to_backup.add(dir_path)

        # Add critical file patterns
        for pattern in self.critical_patterns:
            for file_path in Path(".").glob(pattern):
                if file_path.is_file():
                    files_to_backup.add(file_path)

        # Add scope-specific files
        if scopes:
            scope_patterns = self._get_scope_patterns(scopes)
            for pattern in scope_patterns:
                for file_path in Path(".").glob(pattern):
                    if file_path.is_file():
                        files_to_backup.add(file_path)

        # Create backup directory structure
        files_backup_dir = rollback_point.backup_dir / "files"
        files_backup_dir.mkdir(exist_ok=True)

        # Backup files
        for file_path in files_to_backup:
            try:
                rel_path = file_path.relative_to(".")
                backup_path = files_backup_dir / rel_path
                backup_path.parent.mkdir(parents=True, exist_ok=True)

                shutil.copy2(file_path, backup_path)

                # Add to manifest
                rollback_point.file_manifest[str(rel_path)] = {
                    "original_path": str(file_path),
                    "backup_path": str(backup_path),
                    "size": file_path.stat().st_size,
                    "modified_time": file_path.stat().st_mtime,
                    "checksum": self._calculate_file_checksum(file_path)
                }

            except Exception as e:
                logger.warning(f"Failed to backup file {file_path}: {e}")

        # Backup directories
        dirs_backup_dir = rollback_point.backup_dir / "directories"
        dirs_backup_dir.mkdir(exist_ok=True)

        for dir_path in directories_to_backup:
            try:
                rel_path = dir_path.relative_to(".")
                backup_path = dirs_backup_dir / rel_path

                if backup_path.exists():
                    shutil.rmtree(backup_path)

                shutil.copytree(dir_path, backup_path)

                # Add to manifest
                rollback_point.file_manifest[f"{rel_path}/"] = {
                    "original_path": str(dir_path),
                    "backup_path": str(backup_path),
                    "type": "directory"
                }

            except Exception as e:
                logger.warning(f"Failed to backup directory {dir_path}: {e}")

    def _backup_configurations(self, rollback_point: RollbackPoint) -> None:
        """Backup configuration files and settings"""

        config_backup_dir = rollback_point.backup_dir / "config"
        config_backup_dir.mkdir(exist_ok=True)

        # Environment variables
        env_backup = {
            "timestamp": datetime.now().isoformat(),
            "variables": {}
        }

        # Backup relevant environment variables
        relevant_env_vars = [
            "CFBD_API_KEY",
            "PYTHONPATH",
            "VIRTUAL_ENV",
            "CONDA_DEFAULT_ENV"
        ]

        for var in relevant_env_vars:
            if var in os.environ:
                env_backup["variables"][var] = os.environ[var]

        env_file = config_backup_dir / "environment.json"
        with open(env_file, 'w') as f:
            json.dump(env_backup, f, indent=2)

        rollback_point.config_snapshots["environment"] = str(env_file)

    def _calculate_file_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum for file"""
        import hashlib

        try:
            with open(file_path, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception:
            return "unknown"

    def _calculate_directory_size(self, directory: Path) -> float:
        """Calculate directory size in MB"""
        try:
            total_size = 0
            for file_path in directory.rglob("*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
            return total_size / (1024 * 1024)
        except Exception:
            return 0.0

    def _save_rollback_metadata(self, rollback_point: RollbackPoint) -> None:
        """Save rollback metadata to file"""
        metadata_file = rollback_point.backup_dir / "metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(rollback_point.to_dict(), f, indent=2)

    def _get_scope_patterns(self, scopes: List[str]) -> List[str]:
        """Get file patterns for specific cleanup scopes"""
        scope_patterns = {
            "backup": ["**/predictions/*backup*", "**/data/*backup*"],
            "cache": ["**/__pycache__/**", "**/*.pyc", "**/*.pyo"],
            "legacy": ["model_pack/legacy_*.py", "scripts/deprecated/**/*.py"],
            "tests": ["**/test_*.py", "**/*_test.py"],
            "docs": ["**/*.md", "**/*.rst", "README*"]
        }

        patterns = []
        for scope in scopes:
            if scope in scope_patterns:
                patterns.extend(scope_patterns[scope])

        return patterns

    def _get_git_branch(self) -> str:
        """Get current git branch"""
        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.stdout.strip() if result.returncode == 0 else "unknown"
        except:
            return "unknown"

    def _get_git_status(self) -> str:
        """Get git status output"""
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.stdout.strip() if result.returncode == 0 else ""
        except:
            return ""

    def _get_git_remotes(self) -> Dict[str, str]:
        """Get git remotes"""
        try:
            result = subprocess.run(
                ["git", "remote", "-v"],
                capture_output=True,
                text=True,
                timeout=5
            )

            remotes = {}
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line:
                        parts = line.split('\t')
                        if len(parts) >= 2:
                            name = parts[0]
                            url = parts[1].split(' ')[0]
                            remotes[name] = url

            return remotes
        except:
            return {}

    def _validate_rollback_point(self, rollback_point: RollbackPoint) -> Dict[str, Any]:
        """Validate rollback point integrity"""

        validation_result = {
            "valid": True,
            "error": None,
            "warnings": []
        }

        try:
            # Check backup directory exists
            if not rollback_point.backup_dir.exists():
                validation_result["valid"] = False
                validation_result["error"] = "Backup directory not found"
                return validation_result

            # Check metadata file exists
            metadata_file = rollback_point.backup_dir / "metadata.json"
            if not metadata_file.exists():
                validation_result["valid"] = False
                validation_result["error"] = "Metadata file not found"
                return validation_result

            # Check file manifest integrity
            for rel_path, file_info in rollback_point.file_manifest.items():
                backup_path = Path(file_info["backup_path"])
                if not backup_path.exists():
                    validation_result["warnings"].append(f"Missing backup file: {rel_path}")

        except Exception as e:
            validation_result["valid"] = False
            validation_result["error"] = f"Validation failed: {str(e)}"

        return validation_result

    def _plan_restore_operations(self, rollback_point: RollbackPoint) -> List[Dict[str, Any]]:
        """Plan restore operations"""

        operations = []

        # Plan file restore operations
        if rollback_point.file_manifest:
            operations.append({
                "operation": "restore_files",
                "description": "Restore files and directories",
                "file_count": len(rollback_point.file_manifest)
            })

        # Plan git restore operations
        git_state_file = rollback_point.backup_dir / "git_state.json"
        if git_state_file.exists():
            operations.append({
                "operation": "restore_git",
                "description": "Restore git repository state"
            })

        # Plan config restore operations
        if rollback_point.config_snapshots:
            operations.append({
                "operation": "restore_config",
                "description": "Restore configuration settings",
                "config_count": len(rollback_point.config_snapshots)
            })

        return operations

    def _execute_file_restore(
        self,
        rollback_point: RollbackPoint,
        operation: Dict[str, Any]
    ) -> None:
        """Execute file restore operation"""

        files_backup_dir = rollback_point.backup_dir / "files"
        dirs_backup_dir = rollback_point.backup_dir / "directories"

        # Restore files
        for rel_path, file_info in rollback_point.file_manifest.items():
            backup_path = Path(file_info["backup_path"])
            original_path = Path(file_info["original_path"])

            try:
                if not backup_path.exists():
                    logger.warning(f"Backup file missing: {backup_path}")
                    continue

                # Create parent directories if needed
                original_path.parent.mkdir(parents=True, exist_ok=True)

                if backup_path.is_file():
                    shutil.copy2(backup_path, original_path)
                elif backup_path.is_dir():
                    if original_path.exists():
                        shutil.rmtree(original_path)
                    shutil.copytree(backup_path, original_path)

            except Exception as e:
                logger.error(f"Failed to restore {rel_path}: {e}")

    def _execute_git_restore(
        self,
        rollback_point: RollbackPoint,
        operation: Dict[str, Any]
    ) -> None:
        """Execute git restore operation"""

        try:
            git_state_file = rollback_point.backup_dir / "git_state.json"
            with open(git_state_file, 'r') as f:
                git_info = json.load(f)

            # Restore to specific commit
            if git_info["current_commit"] != "unknown":
                subprocess.run(
                    ["git", "checkout", git_info["current_commit"]],
                    check=True,
                    timeout=60
                )

            # Apply uncommitted changes if they exist
            patch_file = rollback_point.backup_dir / "uncommitted_changes.patch"
            if patch_file.exists():
                subprocess.run(
                    ["git", "apply", str(patch_file)],
                    check=True,
                    timeout=30
                )

        except Exception as e:
            logger.error(f"Failed to restore git state: {e}")

    def _execute_config_restore(
        self,
        rollback_point: RollbackPoint,
        operation: Dict[str, Any]
    ) -> None:
        """Execute configuration restore operation"""

        # For now, just log what would be restored
        # In practice, you might restore environment variables, etc.
        logger.info(f"Configuration restore available for: {list(rollback_point.config_snapshots.keys())}")

    def _load_rollback_index(self) -> None:
        """Load existing rollback index"""

        try:
            if self.rollback_index_file.exists():
                with open(self.rollback_index_file, 'r') as f:
                    index_data = json.load(f)

                # Load rollback points from index
                for rollback_info in index_data.get("rollbacks", []):
                    rollback_id = rollback_info["rollback_id"]
                    backup_dir = self.rollback_dir / rollback_id

                    if backup_dir.exists():
                        # Load full rollback data
                        metadata_file = backup_dir / "metadata.json"
                        if metadata_file.exists():
                            with open(metadata_file, 'r') as f:
                                metadata = json.load(f)

                            rollback_point = RollbackPoint(
                                rollback_id=metadata["rollback_id"],
                                session_id=metadata["session_id"],
                                description=metadata["description"],
                                backup_dir=backup_dir
                            )

                            rollback_point.created_at = metadata["created_at"]
                            rollback_point.git_commit = metadata["git_commit"]
                            rollback_point.file_manifest = json.loads(
                                metadata.get("file_manifest", "{}")
                            )
                            rollback_point.config_snapshots = json.loads(
                                metadata.get("config_snapshots", "{}")
                            )
                            rollback_point.size_mb = metadata.get("size_mb", 0)

                            self.active_rollbacks[rollback_id] = rollback_point

                logger.info(f"Loaded {len(self.active_rollbacks)} rollback points from index")

        except Exception as e:
            logger.error(f"Failed to load rollback index: {e}")

    def _update_rollback_index(self) -> None:
        """Update rollback index file"""

        try:
            index_data = {
                "updated_at": datetime.now().isoformat(),
                "rollbacks": [
                    rollback_point.to_dict()
                    for rollback_point in self.active_rollbacks.values()
                ]
            }

            with open(self.rollback_index_file, 'w') as f:
                json.dump(index_data, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to update rollback index: {e}")

    def get_rollback_status(self) -> Dict[str, Any]:
        """Get rollback manager status"""

        total_size_mb = sum(rp.size_mb for rp in self.active_rollbacks.values())

        return {
            "status": "active",
            "rollback_points": len(self.active_rollbacks),
            "total_size_mb": round(total_size_mb, 2),
            "backup_directory": str(self.rollback_dir),
            "directory_exists": self.rollback_dir.exists(),
            "oldest_rollback": min((rp.created_at for rp in self.active_rollbacks.values()), default=0),
            "newest_rollback": max((rp.created_at for rp in self.active_rollbacks.values()), default=0)
        }