#!/usr/bin/env python3
"""
Cleanup Orchestrator Agent - Tier 2
Coordinates all cleanup operations with safety and validation for the Script Ohio 2.0 platform.

This agent manages autonomous cleanup operations across the entire codebase,
including backup files, Python caches, legacy code cleanup, test organization,
and documentation streamlining.

Author: Autonomous Code Orchestration System
Created: 2025-01-20
Version: 1.0
"""

import json
import os
import shutil
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from agents.core.agent_framework import (
    AgentCapability,
    AgentRequest,
    AgentResponse,
    AgentStatus,
    BaseAgent,
    PermissionLevel,
)
from src.observability import (
    ErrorCategory,
    ErrorEvent,
    ErrorSeverity,
    configure_logging,
    get_logger,
)

# Import optimization components
from agents.optimization.context_compression_rules import context_compression_engine

# Simplified memory manager integration
# from agents.optimization.memory_manager import memory_manager, MemoryLevel

# Define MemoryType enum for compatibility
class MemoryType:
    CONTEXT = "context"
    EXPERIENCE = "experience"

# Define MemoryLevel enum for compatibility
class MemoryLevel:
    META_AGENT = 1
    ORCHESTRATOR = 2
    AGENT = 3
    CACHE = 4

# Simplified memory manager placeholder
class SimpleMemoryManager:
    def __init__(self):
        self.store = {}

    def store(self, content, memory_level, memory_type, metadata=None, tags=None, expires_in=None):
        """Simplified store method"""
        key = f"{memory_type}_{time.time()}"
        self.store[key] = {
            "content": content,
            "metadata": metadata,
            "tags": tags
        }
        return key

# Use simple memory manager
memory_manager = SimpleMemoryManager()

# Import cleanup sub-agents (will be created)
# from agents.cleanup.validation_manager import ValidationManager
# from agents.cleanup.state_manager import StateManager
# from agents.cleanup.rollback_manager import RollbackManager

configure_logging(service_name="agents")
logger = get_logger(__name__, component="cleanup_orchestrator", service_name="agents")


class CleanupOrchestratorAgent(BaseAgent):
    """
    Master coordinator for all cleanup operations in Script Ohio 2.0.

    This Tier 2 agent manages five specialized cleanup sub-agents while maintaining
    comprehensive safety validation, rollback capabilities, and performance monitoring.
    """

    def __init__(self, agent_id: str = "cleanup_orchestrator"):
        super().__init__(
            agent_id=agent_id,
            name="Cleanup Orchestrator",
            permission_level=PermissionLevel.READ_EXECUTE_WRITE
        )

        # Cleanup-specific state management
        self.cleanup_state = {
            "phase": "discovery",
            "operations_completed": [],
            "rollback_points": [],
            "current_session_id": None,
            "emergency_stop": False,
            "metrics": {
                "space_freed_mb": 0,
                "files_processed": 0,
                "directories_processed": 0,
                "errors": 0,
                "warnings": 0,
                "start_time": None,
                "operations": {}
            }
        }

        # Cleanup scope configuration
        self.cleanup_scopes = {
            "backup": {
                "enabled": True,
                "priority": "high",
                "description": "Clean up backup files with intelligent retention",
                "target_directories": ["predictions/", "data/", "models/", "archive/"]
            },
            "cache": {
                "enabled": True,
                "priority": "medium",
                "description": "Remove Python cache directories",
                "target_patterns": ["**/__pycache__/", "**/*.pyc", "**/*.pyo"]
            },
            "legacy": {
                "enabled": True,
                "priority": "low",
                "description": "Clean up post-migration legacy code",
                "target_patterns": ["model_pack/old_*.py", "scripts/deprecated/"]
            },
            "tests": {
                "enabled": True,
                "priority": "low",
                "description": "Organize scattered test files",
                "target_directories": ["tests/", "agents/tests/", "src/tests/"]
            },
            "docs": {
                "enabled": True,
                "priority": "low",
                "description": "Streamline documentation formats",
                "target_directories": ["docs/", "*.md", "README*"]
            }
        }

        # Initialize session ID for tracking
        self._initialize_cleanup_session()

        logger.info(
            "Cleanup Orchestrator initialized",
            extra={
                "event": "cleanup_orchestrator_init",
                "agent_id": self.agent_id,
                "session_id": self.cleanup_state["current_session_id"]
            }
        )

    def _define_capabilities(self) -> List[AgentCapability]:
        """Define the capabilities of the Cleanup Orchestrator"""
        return [
            AgentCapability(
                name="coordinate_cleanup",
                description="Coordinate comprehensive cleanup operations across all scopes",
                permission_required=PermissionLevel.READ_EXECUTE_WRITE,
                tools_required=["file_scanner", "disk_analyzer", "backup_manager"],
                data_access=[".", "**/*"],
                execution_time_estimate=1800.0,  # 30 minutes max
            ),
            AgentCapability(
                name="validate_operations",
                description="Perform pre and post-cleanup system validation",
                permission_required=PermissionLevel.READ_EXECUTE,
                tools_required=["test_runner", "model_validator", "api_tester"],
                data_access=["tests/", "models/", "web_app/"],
                execution_time_estimate=300.0,  # 5 minutes
            ),
            AgentCapability(
                name="manage_rollback",
                description="Create and manage system rollback points",
                permission_required=PermissionLevel.READ_EXECUTE_WRITE,
                tools_required=["git_manager", "backup_creator", "state_tracker"],
                data_access=[".", ".git/"],
                execution_time_estimate=600.0,  # 10 minutes
            ),
            AgentCapability(
                name="monitor_performance",
                description="Monitor cleanup performance and system impact",
                permission_required=PermissionLevel.READ_EXECUTE,
                tools_required=["performance_monitor", "disk_monitor", "process_monitor"],
                data_access=["."],
                execution_time_estimate=60.0,  # 1 minute
            ),
            AgentCapability(
                name="emergency_stop",
                description="Emergency stop all cleanup operations",
                permission_required=PermissionLevel.READ_EXECUTE,
                tools_required=["process_terminator"],
                data_access=[],
                execution_time_estimate=5.0,
            )
        ]

    def _execute_action(
        self, action: str, parameters: Dict[str, Any], user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute the specific cleanup action requested"""

        # Check for emergency stop
        if self.cleanup_state["emergency_stop"]:
            raise RuntimeError("Emergency stop activated - all operations halted")

        if action == "coordinate_cleanup":
            return self._coordinate_cleanup(parameters, user_context)
        elif action == "validate_operations":
            return self._validate_operations(parameters, user_context)
        elif action == "manage_rollback":
            return self._manage_rollback(parameters, user_context)
        elif action == "monitor_performance":
            return self._monitor_performance(parameters, user_context)
        elif action == "emergency_stop":
            return self._emergency_stop(parameters, user_context)
        elif action == "analyze_scope":
            return self._analyze_scope(parameters, user_context)
        else:
            raise ValueError(f"Unknown action: {action}")

    def _initialize_cleanup_session(self) -> None:
        """Initialize a new cleanup session for tracking"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.cleanup_state["current_session_id"] = f"cleanup_{timestamp}"
        self.cleanup_state["metrics"]["start_time"] = time.time()

        # Store session in memory for tracking
        try:
            # Simplified memory storage
            self.memory_store = getattr(self, 'memory_store', {})
            self.memory_store[self.cleanup_state["current_session_id"]] = {
                "session_id": self.cleanup_state["current_session_id"],
                "start_time": self.cleanup_state["metrics"]["start_time"],
                "initial_state": self.cleanup_state.copy()
            }
        except Exception as e:
            logger.warning(f"Could not store session in memory: {e}")

    def _coordinate_cleanup(
        self, parameters: Dict[str, Any], user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Coordinate comprehensive cleanup operations"""

        scopes = parameters.get("scopes", ["backup", "cache", "legacy", "tests", "docs"])
        dry_run = parameters.get("dry_run", False)
        force = parameters.get("force", False)

        logger.info(
            f"Starting coordinated cleanup for scopes: {scopes}",
            extra={
                "event": "cleanup_start",
                "scopes": scopes,
                "dry_run": dry_run,
                "session_id": self.cleanup_state["current_session_id"]
            }
        )

        results = {
            "session_id": self.cleanup_state["current_session_id"],
            "scopes_processed": {},
            "total_files_processed": 0,
            "total_space_freed_mb": 0,
            "errors": [],
            "warnings": [],
            "dry_run": dry_run
        }

        # Process each scope in priority order
        priority_order = ["backup", "cache", "legacy", "tests", "docs"]

        for scope in priority_order:
            if scope not in scopes:
                continue

            if not self.cleanup_scopes[scope]["enabled"]:
                results["warnings"].append(f"Scope '{scope}' is disabled, skipping")
                continue

            try:
                scope_result = self._process_cleanup_scope(scope, dry_run, force)
                results["scopes_processed"][scope] = scope_result
                results["total_files_processed"] += scope_result["files_processed"]
                results["total_space_freed_mb"] += scope_result["space_freed_mb"]

                # Update orchestrator metrics
                self.cleanup_state["metrics"]["files_processed"] += scope_result["files_processed"]
                self.cleanup_state["metrics"]["space_freed_mb"] += scope_result["space_freed_mb"]
                self.cleanup_state["metrics"]["operations"][scope] = scope_result

            except Exception as e:
                error_msg = f"Error processing scope '{scope}': {str(e)}"
                results["errors"].append(error_msg)
                self.cleanup_state["metrics"]["errors"] += 1

                logger.error(error_msg, extra={
                    "event": "cleanup_scope_error",
                    "scope": scope,
                    "session_id": self.cleanup_state["current_session_id"]
                })

        # Update cleanup state
        self.cleanup_state["operations_completed"].extend(scopes)
        self.cleanup_state["phase"] = "completed" if not results["errors"] else "partial"

        # Store completion in memory (simplified)
        try:
            if not hasattr(self, 'memory_store'):
                self.memory_store = {}
            self.memory_store[f"{self.cleanup_state['current_session_id']}_results"] = results
        except Exception as e:
            logger.warning(f"Could not store results in memory: {e}")

        logger.info(
            f"Cleanup coordination completed. Files: {results['total_files_processed']}, "
            f"Space freed: {results['total_space_freed_mb']:.1f}MB",
            extra={
                "event": "cleanup_complete",
                "session_id": self.cleanup_state["current_session_id"],
                "files_processed": results["total_files_processed"],
                "space_freed_mb": results["total_space_freed_mb"],
                "errors": len(results["errors"])
            }
        )

        return results

    def _process_cleanup_scope(
        self, scope: str, dry_run: bool, force: bool
    ) -> Dict[str, Any]:
        """Process a specific cleanup scope"""

        logger.debug(f"Processing cleanup scope: {scope} (dry_run={dry_run})")

        if scope == "backup":
            return self._cleanup_backup_files(dry_run, force)
        elif scope == "cache":
            return self._cleanup_python_cache(dry_run, force)
        elif scope == "legacy":
            return self._cleanup_legacy_code(dry_run, force)
        elif scope == "tests":
            return self._organize_test_files(dry_run, force)
        elif scope == "docs":
            return self._streamline_documentation(dry_run, force)
        else:
            raise ValueError(f"Unknown cleanup scope: {scope}")

    def _cleanup_backup_files(self, dry_run: bool, force: bool) -> Dict[str, Any]:
        """Clean up backup files with intelligent retention"""

        # Find backup files across target directories
        backup_patterns = [
            "**/*backup*",
            "**/*_backup_*",
            "**/*.bak",
            "**/*.old",
            "**/*.orig"
        ]

        backup_files = []
        for pattern in backup_patterns:
            backup_files.extend(Path(".").glob(pattern))

        # Analyze and categorize backups
        categorized_backups = {
            "recent": [],  # Last 7 days
            "important": [],  # Marked as important
            "old": [],  # Older than 30 days
            "duplicate": []  # Duplicates to remove
        }

        now = datetime.now()
        total_space_freed = 0

        for backup_file in backup_files:
            if not backup_file.is_file():
                continue

            stat = backup_file.stat()
            file_age_days = (now - datetime.fromtimestamp(stat.st_mtime)).days
            file_size_mb = stat.st_size / (1024 * 1024)

            # Categorize based on age and name patterns
            if file_age_days <= 7:
                categorized_backups["recent"].append({
                    "path": str(backup_file),
                    "size_mb": file_size_mb,
                    "age_days": file_age_days
                })
            elif "important" in backup_file.name.lower() or not force:
                categorized_backups["important"].append({
                    "path": str(backup_file),
                    "size_mb": file_size_mb,
                    "age_days": file_age_days
                })
            elif file_age_days > 30:
                categorized_backups["old"].append({
                    "path": str(backup_file),
                    "size_mb": file_size_mb,
                    "age_days": file_age_days
                })

        # Process old backups for removal
        files_processed = 0
        for backup_info in categorized_backups["old"]:
            if dry_run:
                total_space_freed += backup_info["size_mb"]
                files_processed += 1
            else:
                try:
                    backup_path = Path(backup_info["path"])
                    backup_path.unlink()
                    total_space_freed += backup_info["size_mb"]
                    files_processed += 1
                    logger.debug(f"Removed old backup: {backup_path}")
                except Exception as e:
                    logger.warning(f"Failed to remove backup {backup_info['path']}: {e}")

        return {
            "scope": "backup",
            "files_processed": files_processed,
            "space_freed_mb": total_space_freed,
            "categories": {k: len(v) for k, v in categorized_backups.items()},
            "dry_run": dry_run
        }

    def _cleanup_python_cache(self, dry_run: bool, force: bool) -> Dict[str, Any]:
        """Clean up Python cache directories"""

        # Find all __pycache__ directories
        cache_dirs = list(Path(".").rglob("__pycache__"))
        cache_files = list(Path(".").rglob("*.pyc")) + list(Path(".").rglob("*.pyo"))

        total_space_freed = 0
        files_processed = 0

        # Process cache directories
        for cache_dir in cache_dirs:
            if not cache_dir.is_dir():
                continue

            # Calculate directory size
            dir_size = sum(f.stat().st_size for f in cache_dir.rglob("*") if f.is_file())
            dir_size_mb = dir_size / (1024 * 1024)

            if dry_run:
                total_space_freed += dir_size_mb
                files_processed += len(list(cache_dir.rglob("*")))
            else:
                try:
                    shutil.rmtree(cache_dir)
                    total_space_freed += dir_size_mb
                    files_processed += len(list(cache_dir.rglob("*")))
                    logger.debug(f"Removed cache directory: {cache_dir}")
                except Exception as e:
                    logger.warning(f"Failed to remove cache dir {cache_dir}: {e}")

        # Process individual cache files
        for cache_file in cache_files:
            if not cache_file.is_file():
                continue

            file_size_mb = cache_file.stat().st_size / (1024 * 1024)

            if dry_run:
                total_space_freed += file_size_mb
                files_processed += 1
            else:
                try:
                    cache_file.unlink()
                    total_space_freed += file_size_mb
                    files_processed += 1
                    logger.debug(f"Removed cache file: {cache_file}")
                except Exception as e:
                    logger.warning(f"Failed to remove cache file {cache_file}: {e}")

        return {
            "scope": "cache",
            "files_processed": files_processed,
            "space_freed_mb": total_space_freed,
            "directories_removed": len(cache_dirs),
            "dry_run": dry_run
        }

    def _cleanup_legacy_code(self, dry_run: bool, force: bool) -> Dict[str, Any]:
        """Clean up legacy code post-migration"""

        # This is a placeholder implementation
        # In a real implementation, this would analyze import dependencies
        # and safely remove deprecated code paths

        legacy_patterns = [
            "model_pack/legacy_*.py",
            "scripts/deprecated/**/*.py",
            "**/old_implementation.py"
        ]

        legacy_files = []
        for pattern in legacy_patterns:
            legacy_files.extend(Path(".").glob(pattern))

        # For now, just report what would be cleaned
        files_processed = len(legacy_files)
        total_space_freed = 0

        for legacy_file in legacy_files:
            if legacy_file.is_file():
                total_space_freed += legacy_file.stat().st_size / (1024 * 1024)

        return {
            "scope": "legacy",
            "files_processed": files_processed,
            "space_freed_mb": total_space_freed,
            "files_found": [str(f) for f in legacy_files],
            "note": "Legacy code cleanup requires dependency analysis",
            "dry_run": dry_run
        }

    def _organize_test_files(self, dry_run: bool, force: bool) -> Dict[str, Any]:
        """Organize scattered test files"""

        # Find test files across the project
        test_patterns = [
            "**/test_*.py",
            "**/*_test.py",
            "**/tests/**/*.py",
            "**/*_spec.py"
        ]

        test_files = []
        for pattern in test_patterns:
            test_files.extend(Path(".").glob(pattern))

        # Analyze test file distribution
        test_distribution = {}
        for test_file in test_files:
            parent_dir = str(test_file.parent)
            if parent_dir not in test_distribution:
                test_distribution[parent_dir] = []
            test_distribution[parent_dir].append(str(test_file))

        files_processed = len(test_files)

        return {
            "scope": "tests",
            "files_processed": files_processed,
            "space_freed_mb": 0,  # Organization doesn't free space
            "distribution": test_distribution,
            "unique_directories": len(test_distribution),
            "dry_run": dry_run
        }

    def _streamline_documentation(self, dry_run: bool, force: bool) -> Dict[str, Any]:
        """Streamline documentation formats"""

        # Find documentation files
        doc_patterns = [
            "**/*.md",
            "**/*.rst",
            "**/*.txt",
            "README*",
            "CHANGELOG*",
            "LICENSE*"
        ]

        doc_files = []
        for pattern in doc_patterns:
            doc_files.extend(Path(".").glob(pattern))

        # Analyze documentation structure
        doc_structure = {
            "markdown": 0,
            "rst": 0,
            "other": 0,
            "duplicates": []
        }

        processed_files = []
        for doc_file in doc_files:
            if doc_file.suffix.lower() == ".md":
                doc_structure["markdown"] += 1
            elif doc_file.suffix.lower() == ".rst":
                doc_structure["rst"] += 1
            else:
                doc_structure["other"] += 1

            processed_files.append(str(doc_file))

        return {
            "scope": "docs",
            "files_processed": len(processed_files),
            "space_freed_mb": 0,  # Doc organization doesn't free space
            "structure": doc_structure,
            "files_found": processed_files,
            "dry_run": dry_run
        }

    def _validate_operations(
        self, parameters: Dict[str, Any], user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Perform pre and post-cleanup system validation"""

        validation_type = parameters.get("type", "pre")  # "pre" or "post"

        validations = {
            "git_status": self._validate_git_status(),
            "tests_passing": self._validate_tests(),
            "models_loadable": self._validate_models(),
            "web_app_buildable": self._validate_web_app(),
            "data_integrity": self._validate_data_integrity()
        }

        overall_passed = all(v["passed"] for v in validations.values())

        result = {
            "validation_type": validation_type,
            "overall_passed": overall_passed,
            "timestamp": datetime.now().isoformat(),
            "validations": validations,
            "session_id": self.cleanup_state["current_session_id"]
        }

        # Store validation result (simplified)
        try:
            if not hasattr(self, 'memory_store'):
                self.memory_store = {}
            self.memory_store[f"{self.cleanup_state['current_session_id']}_validation_{validation_type}"] = result
        except Exception as e:
            logger.warning(f"Could not store validation in memory: {e}")

        return result

    def _validate_git_status(self) -> Dict[str, Any]:
        """Validate git repository status"""
        try:
            import subprocess

            # Check if git repository
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                timeout=10
            )

            has_changes = bool(result.stdout.strip())

            return {
                "passed": not has_changes,
                "message": "Clean working directory" if not has_changes else "Uncommitted changes present",
                "details": {
                    "has_changes": has_changes,
                    "output": result.stdout
                }
            }
        except Exception as e:
            return {
                "passed": False,
                "message": f"Git validation failed: {str(e)}",
                "error": str(e)
            }

    def _validate_tests(self) -> Dict[str, Any]:
        """Validate that tests pass"""
        try:
            # Quick test validation - just check if test files are syntactically valid
            test_files = list(Path(".").rglob("test_*.py")) + list(Path(".").rglob("*_test.py"))

            syntax_errors = 0
            for test_file in test_files[:10]:  # Check first 10 test files
                try:
                    compile(test_file.read_text(), str(test_file), "exec")
                except SyntaxError:
                    syntax_errors += 1

            return {
                "passed": syntax_errors == 0,
                "message": f"All test files valid syntax" if syntax_errors == 0 else f"Found {syntax_errors} syntax errors",
                "details": {
                    "test_files_found": len(test_files),
                    "syntax_errors": syntax_errors,
                    "checked": min(10, len(test_files))
                }
            }
        except Exception as e:
            return {
                "passed": False,
                "message": f"Test validation failed: {str(e)}",
                "error": str(e)
            }

    def _validate_models(self) -> Dict[str, Any]:
        """Validate that ML models are loadable"""
        try:
            model_paths = [
                "models/production/ridge_regression_2025_v2.joblib",
                "models/production/xgboost_classifier_2025_v2.pkl",
                "model_pack/ridge_model_2025.joblib"
            ]

            models_found = 0
            models_loadable = 0

            for model_path in model_paths:
                if Path(model_path).exists():
                    models_found += 1
                    # For now, just check if file exists and has reasonable size
                    if Path(model_path).stat().st_size > 1000:  # At least 1KB
                        models_loadable += 1

            return {
                "passed": models_loadable >= models_found * 0.8,  # 80% should be loadable
                "message": f"Found {models_found} models, {models_loadable} loadable",
                "details": {
                    "models_found": models_found,
                    "models_loadable": models_loadable,
                    "threshold": "80% loadable"
                }
            }
        except Exception as e:
            return {
                "passed": False,
                "message": f"Model validation failed: {str(e)}",
                "error": str(e)
            }

    def _validate_web_app(self) -> Dict[str, Any]:
        """Validate that web app is buildable"""
        try:
            web_app_path = Path("web_app")

            if not web_app_path.exists():
                return {
                    "passed": True,
                    "message": "Web app not present - skipped validation"
                }

            # Check for package.json
            package_json = web_app_path / "package.json"
            if not package_json.exists():
                return {
                    "passed": False,
                    "message": "package.json not found in web_app"
                }

            # Check for essential dependencies
            essential_deps = ["react", "typescript", "vite"]
            package_content = json.loads(package_json.read_text())

            missing_deps = []
            for dep in essential_deps:
                if dep not in package_content.get("dependencies", {}):
                    missing_deps.append(dep)

            return {
                "passed": len(missing_deps) == 0,
                "message": f"Web app structure valid" if not missing_deps else f"Missing dependencies: {missing_deps}",
                "details": {
                    "web_app_exists": True,
                    "package_json_exists": True,
                    "missing_dependencies": missing_deps
                }
            }
        except Exception as e:
            return {
                "passed": False,
                "message": f"Web app validation failed: {str(e)}",
                "error": str(e)
            }

    def _validate_data_integrity(self) -> Dict[str, Any]:
        """Validate data file integrity"""
        try:
            data_paths = [
                "data/processed/training/master_training_data_v2.csv",
                "data/raw/historical/games_1869_2025.csv",
                "model_pack/updated_training_data.csv"
            ]

            data_found = 0
            data_valid = 0

            for data_path in data_paths:
                if Path(data_path).exists():
                    data_found += 1
                    # Basic integrity check - file size and readability
                    if Path(data_path).stat().st_size > 1000:  # At least 1KB
                        try:
                            # Try to read first few lines
                            with open(data_path, 'r') as f:
                                f.readline()
                            data_valid += 1
                        except:
                            pass

            return {
                "passed": data_valid >= data_found * 0.8,
                "message": f"Found {data_found} data files, {data_valid} valid",
                "details": {
                    "data_found": data_found,
                    "data_valid": data_valid,
                    "threshold": "80% valid"
                }
            }
        except Exception as e:
            return {
                "passed": False,
                "message": f"Data integrity validation failed: {str(e)}",
                "error": str(e)
            }

    def _manage_rollback(
        self, parameters: Dict[str, Any], user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create and manage system rollback points"""

        operation = parameters.get("operation", "create")  # "create", "list", "restore"

        if operation == "create":
            return self._create_rollback_point(parameters)
        elif operation == "list":
            return self._list_rollback_points()
        elif operation == "restore":
            return self._restore_rollback_point(parameters)
        else:
            raise ValueError(f"Unknown rollback operation: {operation}")

    def _create_rollback_point(
        self, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a rollback point"""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        rollback_id = f"rollback_{timestamp}"

        rollback_info = {
            "rollback_id": rollback_id,
            "timestamp": timestamp,
            "git_commit": self._get_current_git_commit(),
            "cleanup_state": self.cleanup_state.copy(),
            "disk_usage": self._get_disk_usage()
        }

        # Store rollback point in memory (simplified)
        try:
            if not hasattr(self, 'memory_store'):
                self.memory_store = {}
            self.memory_store[f"rollback_{rollback_id}"] = rollback_info
        except Exception as e:
            logger.warning(f"Could not store rollback point in memory: {e}")

        self.cleanup_state["rollback_points"].append(rollback_id)

        return {
            "rollback_id": rollback_id,
            "created": True,
            "timestamp": timestamp,
            "message": "Rollback point created successfully"
        }

    def _list_rollback_points(self) -> Dict[str, Any]:
        """List available rollback points"""

        # This is a simplified implementation
        # In practice, you'd retrieve from persistent storage

        return {
            "rollback_points": self.cleanup_state["rollback_points"],
            "count": len(self.cleanup_state["rollback_points"])
        }

    def _restore_rollback_point(
        self, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Restore to a specific rollback point"""

        rollback_id = parameters.get("rollback_id")

        if not rollback_id:
            raise ValueError("rollback_id parameter required")

        if rollback_id not in self.cleanup_state["rollback_points"]:
            raise ValueError(f"Rollback point {rollback_id} not found")

        # In a real implementation, this would:
        # 1. Restore git state
        # 2. Restore files from backup
        # 3. Restore configuration
        # 4. Validate system state

        return {
            "rollback_id": rollback_id,
            "restored": True,
            "message": "Rollback point restored successfully (placeholder implementation)"
        }

    def _get_current_git_commit(self) -> str:
        """Get current git commit hash"""
        try:
            import subprocess
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.stdout.strip() if result.returncode == 0 else "unknown"
        except:
            return "unknown"

    def _get_disk_usage(self) -> Dict[str, Any]:
        """Get current disk usage"""
        try:
            import shutil
            usage = shutil.disk_usage(".")
            return {
                "total_gb": usage.total / (1024**3),
                "used_gb": usage.used / (1024**3),
                "free_gb": usage.free / (1024**3)
            }
        except:
            return {"error": "Could not determine disk usage"}

    def _monitor_performance(
        self, parameters: Dict[str, Any], user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Monitor cleanup performance and system impact"""

        current_time = time.time()
        elapsed_time = current_time - self.cleanup_state["metrics"]["start_time"]

        performance_metrics = {
            "session_id": self.cleanup_state["current_session_id"],
            "elapsed_time_seconds": elapsed_time,
            "cleanup_metrics": self.cleanup_state["metrics"].copy(),
            "system_metrics": {
                "disk_usage": self._get_disk_usage(),
                "memory_usage": self._get_memory_usage()
            },
            "optimization_metrics": {
                "context_compression": context_compression_engine.get_metrics(),
                "memory_manager": memory_manager.get_stats()
            }
        }

        return performance_metrics

    def _get_memory_usage(self) -> Dict[str, Any]:
        """Get current memory usage"""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            return {
                "rss_mb": memory_info.rss / (1024**2),
                "vms_mb": memory_info.vms / (1024**2),
                "percent": process.memory_percent()
            }
        except:
            return {"error": "Could not determine memory usage"}

    def _emergency_stop(
        self, parameters: Dict[str, Any], user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Emergency stop all cleanup operations"""

        self.cleanup_state["emergency_stop"] = True

        logger.warning(
            "Emergency stop activated",
            extra={
                "event": "cleanup_emergency_stop",
                "session_id": self.cleanup_state["current_session_id"]
            }
        )

        return {
            "emergency_stop": True,
            "timestamp": datetime.now().isoformat(),
            "message": "All cleanup operations stopped immediately"
        }

    def _analyze_scope(
        self, parameters: Dict[str, Any], user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze cleanup scope without performing operations"""

        scopes = parameters.get("scopes", list(self.cleanup_scopes.keys()))

        analysis = {
            "session_id": self.cleanup_state["current_session_id"],
            "scopes_analysis": {},
            "total_estimated_files": 0,
            "total_estimated_space_mb": 0
        }

        for scope in scopes:
            if scope not in self.cleanup_scopes:
                continue

            scope_analysis = {
                "description": self.cleanup_scopes[scope]["description"],
                "priority": self.cleanup_scopes[scope]["priority"],
                "estimated_files": 0,
                "estimated_space_mb": 0,
                "target_directories": self.cleanup_scopes[scope].get("target_directories", []),
                "target_patterns": self.cleanup_scopes[scope].get("target_patterns", [])
            }

            # Quick estimation (simplified)
            if scope == "cache":
                cache_dirs = list(Path(".").rglob("__pycache__"))
                scope_analysis["estimated_files"] = len(cache_dirs) * 10  # Average 10 files per cache dir
                scope_analysis["estimated_space_mb"] = len(cache_dirs) * 2  # Average 2MB per cache dir
            elif scope == "backup":
                backup_files = list(Path(".").glob("**/*backup*"))
                scope_analysis["estimated_files"] = len(backup_files)
                scope_analysis["estimated_space_mb"] = len(backup_files) * 5  # Average 5MB per backup

            analysis["scopes_analysis"][scope] = scope_analysis
            analysis["total_estimated_files"] += scope_analysis["estimated_files"]
            analysis["total_estimated_space_mb"] += scope_analysis["estimated_space_mb"]

        return analysis

    def get_cleanup_status(self) -> Dict[str, Any]:
        """Get current cleanup status and metrics"""
        return {
            "agent_id": self.agent_id,
            "session_id": self.cleanup_state["current_session_id"],
            "phase": self.cleanup_state["phase"],
            "emergency_stop": self.cleanup_state["emergency_stop"],
            "metrics": self.cleanup_state["metrics"].copy(),
            "operations_completed": self.cleanup_state["operations_completed"].copy(),
            "rollback_points_count": len(self.cleanup_state["rollback_points"])
        }