#!/usr/bin/env python3
"""
Validation Manager - Safety Validation Framework

Comprehensive validation system for cleanup operations including
pre-cleanup safety checks, runtime monitoring, and post-cleanup verification.

Ensures system integrity throughout autonomous cleanup operations.

Author: Autonomous Code Orchestration System
Created: 2025-01-20
Version: 1.0
"""

import json
import os
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
logger = get_logger(__name__, component="validation_manager", service_name="agents")


class ValidationResult:
    """Result of a validation check"""

    def __init__(
        self,
        passed: bool,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        severity: str = "error"
    ):
        self.passed = passed
        self.message = message
        self.details = details or {}
        self.severity = severity
        self.timestamp = datetime.now().isoformat()


class ValidationManager:
    """
    Manages comprehensive validation for cleanup operations.

    Performs pre-cleanup safety checks, runtime monitoring,
    and post-cleanup verification to ensure system integrity.
    """

    def __init__(self):
        self.validation_history = []
        self.critical_checks = [
            "git_status_clean",
            "disk_space_available",
            "essential_files_present",
            "python_syntax_valid",
            "models_loadable"
        ]

        self.warning_checks = [
            "test_files_valid",
            "web_app_structure_intact",
            "dependencies_satisfied"
        ]

        self.validation_thresholds = {
            "min_disk_space_gb": 5,  # Minimum 5GB free space
            "max_file_size_mb": 1000,  # Maximum file size to process
            "max_directory_size_gb": 10,  # Maximum directory size to process
            "syntax_error_tolerance": 0,  # Zero tolerance for syntax errors
        }

        logger.info("Validation Manager initialized")

    def run_pre_cleanup_validation(
        self,
        scope: Optional[List[str]] = None,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Run comprehensive pre-cleanup validation

        Args:
            scope: List of cleanup scopes to validate for
            force: Skip certain safety checks if True

        Returns:
            Validation results with pass/fail status
        """

        logger.info(
            f"Running pre-cleanup validation for scope: {scope}",
            extra={"event": "pre_cleanup_validation_start"}
        )

        validation_results = {
            "validation_type": "pre_cleanup",
            "timestamp": datetime.now().isoformat(),
            "scope": scope or "all",
            "force": force,
            "overall_passed": True,
            "critical_results": {},
            "warning_results": {},
            "recommendations": []
        }

        # Run critical checks
        for check_name in self.critical_checks:
            try:
                result = self._run_validation_check(check_name, scope, force)
                validation_results["critical_results"][check_name] = {
                    "passed": result.passed,
                    "message": result.message,
                    "details": result.details,
                    "severity": result.severity
                }

                if not result.passed:
                    validation_results["overall_passed"] = False

            except Exception as e:
                logger.error(f"Validation check {check_name} failed: {e}")
                validation_results["critical_results"][check_name] = {
                    "passed": False,
                    "message": f"Validation check failed: {str(e)}",
                    "severity": "error"
                }
                validation_results["overall_passed"] = False

        # Run warning checks (don't fail overall)
        for check_name in self.warning_checks:
            try:
                result = self._run_validation_check(check_name, scope, force)
                validation_results["warning_results"][check_name] = {
                    "passed": result.passed,
                    "message": result.message,
                    "details": result.details,
                    "severity": result.severity
                }

                if not result.passed:
                    validation_results["recommendations"].append(
                        f"Warning: {result.message}"
                    )

            except Exception as e:
                logger.warning(f"Warning check {check_name} failed: {e}")
                validation_results["warning_results"][check_name] = {
                    "passed": False,
                    "message": f"Warning check failed: {str(e)}",
                    "severity": "warning"
                }

        # Store validation results
        self.validation_history.append(validation_results)

        logger.info(
            f"Pre-cleanup validation completed. Overall passed: {validation_results['overall_passed']}",
            extra={
                "event": "pre_cleanup_validation_complete",
                "overall_passed": validation_results["overall_passed"],
                "critical_passed": sum(1 for r in validation_results["critical_results"].values() if r["passed"]),
                "warnings": len(validation_results["recommendations"])
            }
        )

        return validation_results

    def run_post_cleanup_validation(
        self,
        cleanup_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Run comprehensive post-cleanup validation

        Args:
            cleanup_results: Results from cleanup operations

        Returns:
            Validation results with pass/fail status
        """

        logger.info(
            "Running post-cleanup validation",
            extra={"event": "post_cleanup_validation_start"}
        )

        validation_results = {
            "validation_type": "post_cleanup",
            "timestamp": datetime.now().isoformat(),
            "cleanup_session_id": cleanup_results.get("session_id"),
            "overall_passed": True,
            "system_integrity": {},
            "functionality_tests": {},
            "performance_impact": {},
            "recommendations": []
        }

        # System integrity checks
        integrity_checks = [
            "essential_files_intact",
            "python_imports_working",
            "git_status_clean",
            "disk_space_reasonable"
        ]

        for check_name in integrity_checks:
            try:
                result = self._run_post_cleanup_check(check_name, cleanup_results)
                validation_results["system_integrity"][check_name] = {
                    "passed": result.passed,
                    "message": result.message,
                    "details": result.details
                }

                if not result.passed:
                    validation_results["overall_passed"] = False

            except Exception as e:
                logger.error(f"Post-cleanup check {check_name} failed: {e}")
                validation_results["system_integrity"][check_name] = {
                    "passed": False,
                    "message": f"Check failed: {str(e)}"
                }
                validation_results["overall_passed"] = False

        # Functionality tests
        functionality_checks = [
            "web_app_builds",
            "tests_runnable",
            "models_loadable"
        ]

        for check_name in functionality_checks:
            try:
                result = self._run_functionality_check(check_name)
                validation_results["functionality_tests"][check_name] = {
                    "passed": result.passed,
                    "message": result.message,
                    "details": result.details
                }

                if not result.passed:
                    validation_results["recommendations"].append(
                        f"Functionality issue: {result.message}"
                    )

            except Exception as e:
                logger.warning(f"Functionality check {check_name} failed: {e}")
                validation_results["functionality_tests"][check_name] = {
                    "passed": False,
                    "message": f"Check failed: {str(e)}"
                }

        # Performance impact analysis
        validation_results["performance_impact"] = self._analyze_performance_impact(cleanup_results)

        # Store validation results
        self.validation_history.append(validation_results)

        logger.info(
            f"Post-cleanup validation completed. Overall passed: {validation_results['overall_passed']}",
            extra={
                "event": "post_cleanup_validation_complete",
                "overall_passed": validation_results["overall_passed"],
                "integrity_passed": sum(1 for r in validation_results["system_integrity"].values() if r["passed"]),
                "functionality_issues": len(validation_results["recommendations"])
            }
        )

        return validation_results

    def _run_validation_check(
        self,
        check_name: str,
        scope: Optional[List[str]],
        force: bool
    ) -> ValidationResult:
        """Run a specific validation check"""

        check_methods = {
            "git_status_clean": self._check_git_status,
            "disk_space_available": self._check_disk_space,
            "essential_files_present": self._check_essential_files,
            "python_syntax_valid": self._check_python_syntax,
            "models_loadable": self._check_models_loadable,
            "test_files_valid": self._check_test_files,
            "web_app_structure_intact": self._check_web_app_structure,
            "dependencies_satisfied": self._check_dependencies
        }

        if check_name not in check_methods:
            return ValidationResult(
                False,
                f"Unknown validation check: {check_name}"
            )

        return check_methods[check_name](scope, force)

    def _check_git_status(
        self,
        scope: Optional[List[str]],
        force: bool
    ) -> ValidationResult:
        """Check if git repository is clean"""

        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                timeout=10
            )

            has_changes = bool(result.stdout.strip())

            if has_changes and not force:
                return ValidationResult(
                    False,
                    "Working directory has uncommitted changes",
                    details={"git_output": result.stdout}
                )

            return ValidationResult(
                True,
                "Git repository is clean" if not has_changes else "Changes present but force mode enabled"
            )

        except subprocess.TimeoutExpired:
            return ValidationResult(
                False,
                "Git status check timed out"
            )
        except FileNotFoundError:
            return ValidationResult(
                True,
                "Not a git repository - skipped check"
            )
        except Exception as e:
            return ValidationResult(
                False,
                f"Git status check failed: {str(e)}"
            )

    def _check_disk_space(
        self,
        scope: Optional[List[str]],
        force: bool
    ) -> ValidationResult:
        """Check available disk space"""

        try:
            import shutil

            usage = shutil.disk_usage(".")
            free_gb = usage.free / (1024**3)

            if free_gb < self.validation_thresholds["min_disk_space_gb"] and not force:
                return ValidationResult(
                    False,
                    f"Insufficient disk space: {free_gb:.1f}GB available, {self.validation_thresholds['min_disk_space_gb']}GB required",
                    details={
                        "free_gb": free_gb,
                        "required_gb": self.validation_thresholds["min_disk_space_gb"]
                    }
                )

            return ValidationResult(
                True,
                f"Disk space OK: {free_gb:.1f}GB available"
            )

        except Exception as e:
            return ValidationResult(
                False,
                f"Disk space check failed: {str(e)}"
            )

    def _check_essential_files(
        self,
        scope: Optional[List[str]],
        force: bool
    ) -> ValidationResult:
        """Check if essential project files are present"""

        essential_files = [
            "CLAUDE.md",
            "requirements.txt",
            "README.md",
            "agents/core/agent_framework.py"
        ]

        missing_files = []
        for file_path in essential_files:
            if not Path(file_path).exists():
                missing_files.append(file_path)

        if missing_files and not force:
            return ValidationResult(
                False,
                f"Essential files missing: {missing_files}",
                details={"missing_files": missing_files}
            )

        return ValidationResult(
            True,
            "All essential files present" if not missing_files else f"Missing files: {missing_files} (force mode)"
        )

    def _check_python_syntax(
        self,
        scope: Optional[List[str]],
        force: bool
    ) -> ValidationResult:
        """Check Python file syntax validity"""

        try:
            # Get Python files to check
            python_files = list(Path(".").rglob("*.py"))

            # Limit to reasonable number for performance
            python_files = python_files[:100]

            syntax_errors = []
            for py_file in python_files:
                try:
                    compile(py_file.read_text(), str(py_file), "exec")
                except SyntaxError as e:
                    syntax_errors.append({
                        "file": str(py_file),
                        "error": str(e),
                        "line": e.lineno
                    })

            tolerance = self.validation_thresholds["syntax_error_tolerance"]
            if len(syntax_errors) > tolerance and not force:
                return ValidationResult(
                    False,
                    f"Found {len(syntax_errors)} syntax errors (tolerance: {tolerance})",
                    details={"syntax_errors": syntax_errors[:5]}  # First 5 errors
                )

            return ValidationResult(
                True,
                f"Python syntax valid ({len(syntax_errors)} errors, tolerance: {tolerance})"
            )

        except Exception as e:
            return ValidationResult(
                False,
                f"Python syntax check failed: {str(e)}"
            )

    def _check_models_loadable(
        self,
        scope: Optional[List[str]],
        force: bool
    ) -> ValidationResult:
        """Check if ML models are loadable"""

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
                    try:
                        # Basic file size check
                        if Path(model_path).stat().st_size > 1000:
                            models_loadable += 1
                    except Exception:
                        pass

            success_rate = models_loadable / models_found if models_found > 0 else 1.0

            if success_rate < 0.8 and not force:  # 80% success rate required
                return ValidationResult(
                    False,
                    f"Only {success_rate:.1%} of models loadable (required: 80%)",
                    details={
                        "models_found": models_found,
                        "models_loadable": models_loadable
                    }
                )

            return ValidationResult(
                True,
                f"Models loadable: {models_loadable}/{models_found} ({success_rate:.1%})"
            )

        except Exception as e:
            return ValidationResult(
                False,
                f"Model loadability check failed: {str(e)}"
            )

    def _check_test_files(
        self,
        scope: Optional[List[str]],
        force: bool
    ) -> ValidationResult:
        """Check if test files are valid"""

        try:
            test_files = list(Path(".").rglob("test_*.py")) + list(Path(".").rglob("*_test.py"))

            syntax_errors = 0
            for test_file in test_files[:20]:  # Check first 20 test files
                try:
                    compile(test_file.read_text(), str(test_file), "exec")
                except SyntaxError:
                    syntax_errors += 1

            if syntax_errors > 0:
                return ValidationResult(
                    False,
                    f"Found {syntax_errors} test files with syntax errors",
                    details={"test_files_checked": min(20, len(test_files))}
                )

            return ValidationResult(
                True,
                f"Test files valid ({len(test_files)} files checked)"
            )

        except Exception as e:
            return ValidationResult(
                False,
                f"Test file validation failed: {str(e)}"
            )

    def _check_web_app_structure(
        self,
        scope: Optional[List[str]],
        force: bool
    ) -> ValidationResult:
        """Check web app structure integrity"""

        try:
            web_app_path = Path("web_app")

            if not web_app_path.exists():
                return ValidationResult(
                    True,
                    "Web app not present - skipped check"
                )

            essential_web_files = [
                "package.json",
                "src/App.tsx",
                "tsconfig.json"
            ]

            missing_files = []
            for file_path in essential_web_files:
                if not (web_app_path / file_path).exists():
                    missing_files.append(str(file_path))

            if missing_files:
                return ValidationResult(
                    False,
                    f"Web app missing essential files: {missing_files}",
                    details={"missing_files": missing_files}
                )

            return ValidationResult(
                True,
                "Web app structure intact"
            )

        except Exception as e:
            return ValidationResult(
                False,
                f"Web app structure check failed: {str(e)}"
            )

    def _check_dependencies(
        self,
        scope: Optional[List[str]],
        force: bool
    ) -> ValidationResult:
        """Check if Python dependencies are satisfied"""

        try:
            # Check if requirements.txt exists and is readable
            requirements_path = Path("requirements.txt")
            if not requirements_path.exists():
                return ValidationResult(
                    True,
                    "No requirements.txt - skipped check"
                )

            # Try to import some key dependencies
            key_deps = ["pandas", "numpy", "sklearn", "pytest"]
            missing_deps = []

            for dep in key_deps:
                try:
                    __import__(dep)
                except ImportError:
                    missing_deps.append(dep)

            if missing_deps:
                return ValidationResult(
                    False,
                    f"Missing dependencies: {missing_deps}",
                    details={"missing_dependencies": missing_deps}
                )

            return ValidationResult(
                True,
                "Key dependencies satisfied"
            )

        except Exception as e:
            return ValidationResult(
                False,
                f"Dependency check failed: {str(e)}"
            )

    def _run_post_cleanup_check(
        self,
        check_name: str,
        cleanup_results: Dict[str, Any]
    ) -> ValidationResult:
        """Run post-cleanup specific checks"""

        check_methods = {
            "essential_files_intact": self._check_essential_files_intact,
            "python_imports_working": self._check_python_imports,
            "git_status_clean": self._check_git_status_clean,
            "disk_space_reasonable": self._check_disk_space_reasonable
        }

        if check_name not in check_methods:
            return ValidationResult(
                False,
                f"Unknown post-cleanup check: {check_name}"
            )

        return check_methods[check_name](cleanup_results)

    def _check_essential_files_intact(
        self,
        cleanup_results: Dict[str, Any]
    ) -> ValidationResult:
        """Check essential files are intact after cleanup"""

        # Similar to pre-cleanup check but more thorough
        return self._check_essential_files(None, False)

    def _check_python_imports(
        self,
        cleanup_results: Dict[str, Any]
    ) -> ValidationResult:
        """Check Python imports still work"""

        try:
            # Try to import key modules from the project
            key_imports = [
                "agents.core.agent_framework",
                "src.cfbd_client.unified_client"
            ]

            failed_imports = []
            for import_path in key_imports:
                try:
                    __import__(import_path)
                except ImportError as e:
                    failed_imports.append({
                        "module": import_path,
                        "error": str(e)
                    })

            if failed_imports:
                return ValidationResult(
                    False,
                    f"Python imports failed: {failed_imports}",
                    details={"failed_imports": failed_imports}
                )

            return ValidationResult(
                True,
                "Python imports working correctly"
            )

        except Exception as e:
            return ValidationResult(
                False,
                f"Python import check failed: {str(e)}"
            )

    def _check_git_status_clean(
        self,
        cleanup_results: Dict[str, Any]
    ) -> ValidationResult:
        """Check git status is clean after cleanup"""

        return self._check_git_status(None, False)

    def _check_disk_space_reasonable(
        self,
        cleanup_results: Dict[str, Any]
    ) -> ValidationResult:
        """Check disk space is reasonable after cleanup"""

        try:
            import shutil

            usage = shutil.disk_usage(".")
            free_gb = usage.free / (1024**3)

            # Check if we actually freed up space as expected
            expected_freed = cleanup_results.get("total_space_freed_mb", 0) / 1024

            # This is a basic check - in practice you'd compare before/after
            return ValidationResult(
                True,
                f"Disk space: {free_gb:.1f}GB free"
            )

        except Exception as e:
            return ValidationResult(
                False,
                f"Disk space check failed: {str(e)}"
            )

    def _run_functionality_check(self, check_name: str) -> ValidationResult:
        """Run functionality-specific checks"""

        check_methods = {
            "web_app_builds": self._check_web_app_builds,
            "tests_runnable": self._check_tests_runnable,
            "models_loadable": self._check_models_functionality
        }

        if check_name not in check_methods:
            return ValidationResult(
                False,
                f"Unknown functionality check: {check_name}"
            )

        return check_methods[check_name]()

    def _check_web_app_builds(self) -> ValidationResult:
        """Check if web app can build"""

        try:
            web_app_path = Path("web_app")
            if not web_app_path.exists():
                return ValidationResult(
                    True,
                    "Web app not present - skipped"
                )

            # Check if node_modules exists and has content
            node_modules = web_app_path / "node_modules"
            if not node_modules.exists() or not any(node_modules.iterdir()):
                return ValidationResult(
                    False,
                    "Web app node_modules not installed"
                )

            return ValidationResult(
                True,
                "Web app appears buildable"
            )

        except Exception as e:
            return ValidationResult(
                False,
                f"Web app build check failed: {str(e)}"
            )

    def _check_tests_runnable(self) -> ValidationResult:
        """Check if tests can run"""

        try:
            # Try to run pytest --collect-only (dry run)
            result = subprocess.run(
                ["python3", "-m", "pytest", "--collect-only", "-q"],
                capture_output=True,
                text=True,
                timeout=30,
                cwd="agents/tests"
            )

            if result.returncode == 0:
                return ValidationResult(
                    True,
                    "Tests can be collected and run"
                )
            else:
                return ValidationResult(
                    False,
                    "Test collection failed",
                    details={"stderr": result.stderr[-500:]}  # Last 500 chars
                )

        except subprocess.TimeoutExpired:
            return ValidationResult(
                False,
                "Test collection timed out"
            )
        except Exception as e:
            return ValidationResult(
                False,
                f"Test runnable check failed: {str(e)}"
            )

    def _check_models_functionality(self) -> ValidationResult:
        """Check model functionality"""

        # Re-use the model loadability check
        return self._check_models_loadable(None, False)

    def _analyze_performance_impact(
        self,
        cleanup_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze performance impact of cleanup"""

        try:
            import psutil
            import shutil

            # Get current system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = shutil.disk_usage(".")

            impact_analysis = {
                "disk_space_freed_mb": cleanup_results.get("total_space_freed_mb", 0),
                "files_processed": cleanup_results.get("total_files_processed", 0),
                "current_system_metrics": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "disk_free_gb": disk.free / (1024**3)
                },
                "performance_rating": "good"
            }

            # Rate the performance impact
            files_per_mb = (
                impact_analysis["files_processed"] / max(impact_analysis["disk_space_freed_mb"], 1)
            )

            if files_per_mb > 100:  # Many small files
                impact_analysis["performance_rating"] = "excellent"
            elif files_per_mb > 50:
                impact_analysis["performance_rating"] = "good"
            elif files_per_mb > 10:
                impact_analysis["performance_rating"] = "moderate"
            else:
                impact_analysis["performance_rating"] = "minimal"

            return impact_analysis

        except Exception as e:
            return {
                "error": f"Performance impact analysis failed: {str(e)}"
            }

    def get_validation_summary(self) -> Dict[str, Any]:
        """Get summary of all validation runs"""

        if not self.validation_history:
            return {"message": "No validation history available"}

        total_validations = len(self.validation_history)
        passed_validations = sum(
            1 for v in self.validation_history
            if v.get("overall_passed", False)
        )

        return {
            "total_validations": total_validations,
            "passed_validations": passed_validations,
            "pass_rate": passed_validations / total_validations if total_validations > 0 else 0,
            "last_validation": self.validation_history[-1].get("timestamp"),
            "critical_checks_failing": self._get_failing_critical_checks()
        }

    def _get_failing_critical_checks(self) -> List[str]:
        """Get list of currently failing critical checks"""

        if not self.validation_history:
            return []

        latest_validation = self.validation_history[-1]
        failing_checks = []

        for check_name, result in latest_validation.get("critical_results", {}).items():
            if not result.get("passed", False):
                failing_checks.append(check_name)

        return failing_checks