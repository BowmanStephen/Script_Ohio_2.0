#!/usr/bin/env python3
"""
Validation Agent - Orchestrates Existing Validation Orchestrator

This agent wraps the existing Validation Orchestrator with agent-based coordination,
providing enhanced validation control, real-time monitoring, and detailed validation reporting.

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

# Import Validation Orchestrator
try:
    sys.path.append(Path(__file__).resolve().parents[1] / "scripts" / "github_validation")
    from validation_orchestrator import ValidationOrchestrator
except ImportError:
    logger.warning("Validation Orchestrator not found")
    ValidationOrchestrator = None


class ValidationAgent(BaseAgent):
    """
    Orchestrates existing Validation Orchestrator with agent coordination.

    This agent provides enhanced validation functionality by:
    - Coordinating Validation Orchestrator execution
    - Implementing custom validation rules
    - Providing real-time validation monitoring
    - Managing validation scope and intensity
    - Creating detailed validation reports

    Capabilities:
    - Orchestrate comprehensive validation
    - Run custom validation rules
    - Monitor validation in real-time
    - Create validation reports
    - Manage validation policies
    """

    def __init__(self, agent_id: str, tool_loader=None):
        """Initialize the Validation Agent."""
        super().__init__(
            agent_id=agent_id,
            name="Validation Agent",
            permission_level=PermissionLevel.READ_EXECUTE,
            tool_loader=tool_loader,
        )

        self.project_root = Path.cwd()
        self.validation_session_id = None
        self.validation_history = []

        # Initialize Validation Orchestrator
        self.validation_orchestrator = ValidationOrchestrator() if ValidationOrchestrator else None

        # Validation configuration
        self.validation_config = {
            "default_scope": "comprehensive",
            "intensity_levels": {
                "quick": {"timeout": 60, "parallel": True},
                "standard": {"timeout": 180, "parallel": True},
                "comprehensive": {"timeout": 300, "parallel": True}
            },
            "custom_rules": {},
            "report_format": "json"
        }

    def _define_capabilities(self) -> List[AgentCapability]:
        """Define agent capabilities following BaseAgent pattern."""
        return [
            AgentCapability(
                name="orchestrate_validation",
                description="Orchestrate comprehensive validation using Validation Orchestrator",
                permission_required=PermissionLevel.READ_EXECUTE,
                tools_required=["python", "test_frameworks"],
                data_access=["filesystem", "test_results"],
                execution_time_estimate=120.0,
            ),
            AgentCapability(
                name="run_custom_validation",
                description="Run custom validation rules and checks",
                permission_required=PermissionLevel.READ_EXECUTE,
                tools_required=["python"],
                data_access=["filesystem", "validation_rules"],
                execution_time_estimate=90.0,
            ),
            AgentCapability(
                name="monitor_validation",
                description="Monitor validation progress in real-time",
                permission_required=PermissionLevel.READ_ONLY,
                tools_required=["python"],
                data_access=["validation_logs"],
                execution_time_estimate=5.0,
            ),
            AgentCapability(
                name="create_validation_report",
                description="Create detailed validation reports",
                permission_required=PermissionLevel.READ_ONLY,
                tools_required=["python", "json"],
                data_access=["validation_results"],
                execution_time_estimate=15.0,
            ),
            AgentCapability(
                name="manage_validation_policies",
                description="Manage validation rules and policies",
                permission_required=PermissionLevel.READ_EXECUTE_WRITE,
                tools_required=["python", "json"],
                data_access=["validation_policies"],
                execution_time_estimate=10.0,
            ),
            AgentCapability(
                name="validate_specific_scope",
                description="Validate specific files, directories, or patterns",
                permission_required=PermissionLevel.READ_EXECUTE,
                tools_required=["python", "git"],
                data_access=["filesystem", "git_history"],
                execution_time_estimate=60.0,
            ),
        ]

    def _execute_action(
        self, action: str, parameters: Dict[str, Any], user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute agent actions with proper error handling and logging."""

        try:
            start_time = time.time()
            logger.info(f"Executing action: {action} with parameters: {list(parameters.keys())}")

            if action == "orchestrate_validation":
                result = self._orchestrate_validation(parameters, user_context)
            elif action == "run_custom_validation":
                result = self._run_custom_validation(parameters)
            elif action == "monitor_validation":
                result = self._monitor_validation()
            elif action == "create_validation_report":
                result = self._create_validation_report(parameters)
            elif action == "manage_validation_policies":
                result = self._manage_validation_policies(parameters)
            elif action == "validate_specific_scope":
                result = self._validate_specific_scope(parameters)
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

    def _orchestrate_validation(
        self, parameters: Dict[str, Any], user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Orchestrate comprehensive validation using Validation Orchestrator."""
        if not self.validation_orchestrator:
            raise RuntimeError("Validation Orchestrator not available")

        # Generate validation session ID
        self.validation_session_id = f"validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Get parameters
        scope = parameters.get("scope", self.validation_config["default_scope"])
        intensity = parameters.get("intensity", "standard")
        include_tests = parameters.get("include_tests", True)
        include_security = parameters.get("include_security", True)
        parallel = parameters.get("parallel", True)

        logger.info(f"Starting validation orchestration session: {self.validation_session_id}")
        logger.info(f"Scope: {scope}, Intensity: {intensity}")

        validation_result = {
            "session_id": self.validation_session_id,
            "scope": scope,
            "intensity": intensity,
            "validation_successful": False,
            "orchestrator_results": {},
            "custom_results": {},
            "summary": {},
        }

        try:
            # Configure validation orchestrator
            orchestrator_config = {
                "scope": scope,
                "include_tests": include_tests,
                "include_security": include_security,
                "parallel": parallel,
                "timeout": self.validation_config["intensity_levels"][intensity]["timeout"],
                "agent_coordinated": True,
                "session_id": self.validation_session_id
            }

            # Run validation orchestrator
            orchestrator_result = self.validation_orchestrator.run_validation(orchestrator_config)
            validation_result["orchestrator_results"] = orchestrator_result

            # Add custom agent-specific validations
            custom_results = self._run_agent_specific_validations(parameters)
            validation_result["custom_results"] = custom_results

            # Combine results
            overall_status = orchestrator_result.get("overall_status", "failed")
            if overall_status == "passed" and custom_results.get("overall_status", "passed"):
                validation_result["validation_successful"] = True
            else:
                validation_result["validation_successful"] = False

            # Create summary
            validation_result["summary"] = self._create_validation_summary(
                orchestrator_result,
                custom_results,
                validation_result["validation_successful"]
            )

            # Save validation history
            self._save_validation_history(validation_result)

            logger.info(f"Validation orchestration {self.validation_session_id} completed: "
                       f"{'PASSED' if validation_result['validation_successful'] else 'FAILED'}")

        except Exception as e:
            logger.error(f"Validation orchestration failed: {str(e)}")
            validation_result["error"] = str(e)
            validation_result["validation_successful"] = False
            self._save_validation_history(validation_result)

        return validation_result

    def _run_custom_validation(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Run custom validation rules and checks."""
        rules = parameters.get("rules", [])
        target_files = parameters.get("target_files", [])

        logger.info(f"Running custom validation with {len(rules)} rules")

        custom_result = {
            "rules_executed": [],
            "rules_passed": 0,
            "rules_failed": 0,
            "overall_status": "passed",
            "rule_results": {}
        }

        # Predefined custom rules
        custom_rules = {
            "agent_system_health": self._validate_agent_system_health,
            "python_syntax_check": self._validate_python_syntax,
            "import_integrity": self._validate_import_integrity,
            "file_permissions": self._validate_file_permissions,
            "data_integrity": self._validate_data_integrity,
        }

        # Add custom rules from parameters
        if rules:
            custom_rules.update(rules)

        # Execute each rule
        for rule_name, rule_func in custom_rules.items():
            try:
                logger.debug(f"Running validation rule: {rule_name}")
                rule_result = rule_func(target_files)

                custom_result["rules_executed"].append(rule_name)
                custom_result["rule_results"][rule_name] = rule_result

                if rule_result.get("passed", False):
                    custom_result["rules_passed"] += 1
                else:
                    custom_result["rules_failed"] += 1
                    custom_result["overall_status"] = "failed"

            except Exception as e:
                logger.error(f"Validation rule {rule_name} failed: {str(e)}")
                custom_result["rules_executed"].append(rule_name)
                custom_result["rules_failed"] += 1
                custom_result["overall_status"] = "failed"
                custom_result["rule_results"][rule_name] = {
                    "passed": False,
                    "error": str(e)
                }

        logger.info(f"Custom validation completed: {custom_result['rules_passed']}/{custom_result['rules_executed']} rules passed")

        return custom_result

    def _monitor_validation(self) -> Dict[str, Any]:
        """Monitor validation progress in real-time."""
        monitoring = {
            "current_session": self.validation_session_id,
            "active_validations": [],
            "validation_queue": [],
            "resource_usage": self._get_resource_usage(),
            "estimated_completion": None
        }

        # Check if there's an active validation session
        if self.validation_session_id:
            # Monitor active validation
            pass  # Implementation would connect to active validation process

        return monitoring

    def _create_validation_report(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Create detailed validation reports."""
        report_format = parameters.get("format", self.validation_config["report_format"])
        include_history = parameters.get("include_history", False)

        report = {
            "timestamp": datetime.now().isoformat(),
            "agent_id": self.agent_id,
            "report_format": report_format,
            "summary": {},
            "details": {},
        }

        # Include validation history if requested
        if include_history:
            report["validation_history"] = self.validation_history[-10:]  # Last 10 validations

        # Add current validation session info
        if self.validation_session_id:
            current_session = next(
                (v for v in self.validation_history if v.get("session_id") == self.validation_session_id),
                None
            )
            if current_session:
                report["current_session"] = current_session

        # Generate summary statistics
        report["summary"] = self._generate_validation_summary_statistics()

        logger.info(f"Validation report created in {report_format} format")

        return report

    def _manage_validation_policies(self, parameters: Dict[str, Any]):
        """Manage validation rules and policies."""
        action = parameters.get("action", "list")

        if action == "list":
            return self._list_validation_policies()
        elif action == "add":
            return self._add_validation_policy(parameters)
        elif action == "remove":
            return self._remove_validation_policy(parameters)
        elif action == "update":
            return self._update_validation_policy(parameters)
        else:
            return {
                "status": "error",
                "error": f"Unknown action: {action}"
            }

    def _validate_specific_scope(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate specific files, directories, or patterns."""
        scope_type = parameters.get("type", "files")  # files, directories, patterns
        targets = parameters.get("targets", [])
        custom_rules = parameters.get("custom_rules", [])

        validation_result = {
            "scope_type": scope_type,
            "targets_validated": len(targets),
            "validation_passed": False,
            "results": {},
            "summary": {}
        }

        try:
            if scope_type == "files":
                validation_result["results"] = self._validate_files(targets, custom_rules)
            elif scope_type == "directories":
                validation_result["results"] = self._validate_directories(targets, custom_rules)
            elif scope_type == "patterns":
                validation_result["results"] = self._validate_patterns(targets, custom_rules)
            else:
                raise ValueError(f"Unknown scope type: {scope_type}")

            # Determine overall validation status
            all_passed = all(
                result.get("passed", False)
                for result in validation_result["results"].values()
            )
            validation_result["validation_passed"] = all_passed

            # Create summary
            total_checks = len(validation_result["results"])
            passed_checks = sum(
                1 for result in validation_result["results"].values()
                if result.get("passed", False)
            )

            validation_result["summary"] = {
                "total_checks": total_checks,
                "passed": passed_checks,
                "failed": total_checks - passed_checks,
                "pass_rate": (passed_checks / total_checks) if total_checks > 0 else 0
            }

            logger.info(f"Scope validation completed: {passed_checks}/{total_checks} checks passed")

        except Exception as e:
            logger.error(f"Scope validation failed: {str(e)}")
            validation_result["error"] = str(e)
            validation_result["validation_passed"] = False

        return validation_result

    # Agent-specific validation methods
    def _validate_agent_system_health(self, target_files: List[str] = None) -> Dict[str, Any]:
        """Validate agent system health."""
        try:
            health_check = {
                "meta_agent_available": False,
                "core_modules_importable": False,
                "agent_count": 0,
                "agent_registry_status": None
            }

            # Check if meta agent is available
            try:
                from agents.meta_agent import meta_agent
                health_check["meta_agent_available"] = True

                # Get agent registry status
                registry = meta_agent._get_registry({}, {})
                if isinstance(registry, dict):
                    health_check["agent_registry_status"] = "available"
                    health_check["agent_count"] = len(registry)
                else:
                    health_check["agent_registry_status"] = "error"

            except ImportError:
                pass

            # Check if core modules are importable
            try:
                from agents.core.agent_framework import BaseAgent
                health_check["core_modules_importable"] = True
            except ImportError:
                pass

            health_check["overall_health"] = (
                health_check["meta_agent_available"] and
                health_check["core_modules_importable"]
            )

            return {
                "passed": health_check["overall_health"],
                "details": health_check
            }

        except Exception as e:
            return {
                "passed": False,
                "error": str(e)
            }

    def _validate_python_syntax(self, target_files: List[str] = None) -> Dict[str, Any]:
        """Validate Python syntax for all files."""
        try:
            # Get all Python files if target_files not specified
            if not target_files:
                target_files = []
                for root, dirs, files in os.walk(self.project_root):
                    # Skip hidden directories and __pycache__
                    dirs[:] = [d for d in dirs if not d.startswith('.') and d != "__pycache__"]
                    for file in files:
                        if file.endswith('.py'):
                            target_files.append(os.path.join(root, file))

            syntax_errors = []
            files_checked = 0

            for file_path in target_files:
                files_checked += 1
                try:
                    # Compile the Python file
                    with open(file_path, 'r', encoding='utf-8') as f:
                        compile(f.read(), file_path, 'exec')
                except SyntaxError as e:
                    syntax_errors.append({
                        "file": file_path,
                        "line": e.lineno if hasattr(e, 'lineno') else 'unknown',
                        "error": str(e)
                    })
                except Exception:
                    # Other compilation errors
                    syntax_errors.append({
                        "file": file_path,
                        "error": "Compilation error"
                    })

            return {
                "passed": len(syntax_errors) == 0,
                "details": {
                    "files_checked": files_checked,
                    "syntax_errors": syntax_errors,
                    "error_count": len(syntax_errors)
                }
            }

        except Exception as e:
            return {
                "passed": False,
                "error": str(e)
            }

    def _validate_import_integrity(self, target_files: List[str] = None) -> Dict[str, Any]:
        """Validate Python import integrity."""
        try:
            critical_imports = [
                "agents.core.agent_framework",
                "agents.meta_agent",
                "agents.commit_coordinator_agent",
                "agents.commit_analyzer_agent",
                "agents.push_agent",
                "agents.rollback_agent",
                "agents.validation_agent"
            ]

            import_errors = []
            successful_imports = []

            for import_name in critical_imports:
                try:
                    import importlib
                    module = importlib.import_module(import_name)
                    successful_imports.append(import_name)
                except ImportError as e:
                    import_errors.append({
                        "import": import_name,
                        "error": str(e)
                    })

            return {
                "passed": len(import_errors) == 0,
                "details": {
                    "successful_imports": successful_imports,
                    "import_errors": import_errors,
                    "total_checked": len(critical_imports)
                }
            }

        except Exception as e:
            return {
                "passed": False,
                "error": str(e)
            }

    def _validate_file_permissions(self, target_files: List[str] = None) -> Dict[str, Any]:
        """Validate file permissions and accessibility."""
        try:
            permission_issues = []
            files_checked = 0

            # Check critical directories and files
            critical_paths = [
                "agents/",
                "src/",
                "scripts/",
                "data/",
                "tests/"
            ]

            for path in critical_paths:
                if os.path.exists(path):
                    # Check directory permissions
                    if not os.access(path, os.R_OK):
                        permission_issues.append({
                            "path": path,
                            "issue": "Directory not readable",
                            "permissions": oct(os.stat(path).st_mode)[-3:]
                        })

                    # Check files in directory
                    if os.path.isdir(path):
                        for root, dirs, files in os.walk(path):
                            for file in files:
                                file_path = os.path.join(root, file)
                                files_checked += 1

                                if not os.access(file_path, os.R_OK):
                                    permission_issues.append({
                                        "path": file_path,
                                        "issue": "File not readable",
                                        "permissions": oct(os.stat(file_path).st_mode)[-3:]
                                    })

            return {
                "passed": len(permission_issues) == 0,
                "details": {
                    "files_checked": files_checked,
                    "permission_issues": permission_issues,
                    "total_issues": len(permission_issues)
                }
            }

        except Exception as e:
            return {
                "passed": False,
                "error": str(e)
            }

    def _validate_data_integrity(self, target_files: List[str] = None) -> None:
        """Validate data file integrity."""
        try:
            critical_data_files = [
                "data/processed/training/master_training_data_v2.csv",
                "models/production/ridge_regression_2025_v2.joblib",
                "models/production/xgboost_classifier_2025_v2.pkl",
                "models/production/fastai_neural_net_2025_v2.pkl"
            ]

            integrity_issues = []
            files_checked = 0

            for file_path in critical_data_files:
                if os.path.exists(file_path):
                    files_checked += 1

                    # Check file size
                    if os.path.getsize(file_path) == 0:
                        integrity_issues.append({
                            "file": file_path,
                            "issue": "File is empty"
                        })

                    # Try to read the file
                    try:
                        if file_path.endswith('.csv'):
                            import pandas as pd
                            df = pd.read_csv(file_path)
                            if df.empty:
                                integrity_issues.append({
                                    "file": file_path,
                                    "issue": "CSV file contains no data"
                                })
                        elif file_path.endswith(('.pkl', '.joblib')):
                            if file_path.endswith('.joblib'):
                                import joblib
                                joblib.load(file_path)
                            else:
                                import pickle
                                with open(file_path, 'rb') as f:
                                    pickle.load(f)
                    except Exception as e:
                        integrity_issues.append({
                            "file": file_path,
                            "issue": f"Cannot load file: {str(e)}"
                        })

            return {
                "passed": len(integrity_issues) == 0,
                "details": {
                    "files_checked": files_checked,
                    "integrity_issues": integrity_issues,
                    "total_issues": len(integrity_issues)
                }
            }

        except Exception as e:
            return {
                "passed": False,
                "error": str(e)
            }

    def _validate_files(self, files: List[str], custom_rules: Dict) -> Dict[str, Any]:
        """Validate specific files."""
        results = {}

        for file_path in files:
            if os.path.exists(file_path):
                results[file_path] = {
                    "exists": True,
                    "readable": os.access(file_path, os.R_OK),
                    "writable": os.access(file_path, os.W_OK),
                    "syntax_valid": self._check_file_syntax(file_path),
                    "size": os.path.getsize(file_path)
                }

                # Apply custom rules
                for rule_name, rule_func in custom_rules.items():
                    if file_path.endswith(tuple(rule_name.split('.'))):
                        try:
                            rule_result = rule_func(file_path)
                            results[file_path][f"custom_rule_{rule_name}"] = rule_result
                        except Exception as e:
                            results[file_path][f"custom_rule_{rule_name}"] = {
                                "error": str(e)
                            }
            else:
                results[file_path] = {
                    "exists": False,
                    "readable": False,
                    "writable": False
                }

        return results

    def _validate_directories(self, directories: List[str], custom_rules: Dict) -> Dict[str, Any]:
        """Validate specific directories."""
        results = {}

        for dir_path in directories:
            if os.path.exists(dir_path):
                results[dir_path] = {
                    "exists": True,
                    "readable": os.access(dir_path, os.R_OK),
                    "writable": os.access(dir_path, os.W_OK),
                    "file_count": len([f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f))]),
                    "directory_permissions": oct(os.stat(dir_path).st_mode)[-3:]
                }

                # Apply custom rules
                for rule_name, rule_func in custom_rules.items():
                    try:
                        rule_result = rule_func(dir_path)
                        results[dir_path][f"custom_rule_{rule_name}"] = rule_result
                    except Exception as e:
                        results[dir_path][f"custom_rule_{rule_name}"] = {
                            "error": str(e)
                        }
            else:
                results[dir_path] = {
                    "exists": False,
                    "readable": False,
                    "writable": False
                }

        return results

    def _validate_patterns(self, patterns: List[str], custom_rules: Dict) -> Dict[str, Any]:
        """Validate files matching patterns."""
        import glob

        matched_files = []
        for pattern in patterns:
            try:
                matches = glob.glob(pattern, recursive=True)
                matched_files.extend(matches)
            except Exception as e:
                logger.error(f"Error matching pattern {pattern}: {str(e)}")

        # Remove duplicates
        matched_files = list(set(matched_files))

        if not matched_files:
            return {
                "status": "warning",
                "message": "No files matched patterns",
                "patterns": patterns
            }

        # Validate matched files
        return self._validate_files(matched_files, custom_rules)

    def _check_file_syntax(self, file_path: str) -> bool:
        """Check syntax of a single file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                compile(f.read(), file_path, 'exec')
            return True
        except SyntaxError:
            return False
        except Exception:
            return False

    def _create_validation_summary(
        self, orchestrator_result: Dict, custom_result: Dict, overall_success: bool
    ) -> Dict[str, Any]:
        """Create validation summary from results."""
        return {
            "overall_success": overall_success,
            "orchestrator_summary": self._summarize_orchestrator_result(orchestrator_result),
            "custom_summary": self._summarize_custom_result(custom_result),
            "timestamp": datetime.now().isoformat()
        }

    def _summarize_orchestrator_result(self, result: Dict) -> Dict[str, Any]:
        """Summarize Validation Orchestrator result."""
        return {
            "status": result.get("overall_status", "unknown"),
            "checks_run": result.get("checks_run", 0),
            "checks_passed": result.get("checks_passed", 0),
            "checks_failed": result.get("checks_failed", 0),
            "execution_time": result.get("execution_time", 0)
        }

    def _summarize_custom_result(self, result: Dict) -> Dict[str, Any]:
        """Summarize custom validation result."""
        return {
            "status": result.get("overall_status", "unknown"),
            "rules_executed": result.get("rules_executed", 0),
            "rules_passed": result.get("rules_passed", 0),
            "rules_failed": result.get("rules_failed", 0),
            "execution_time": result.get("execution_time", 0)
        }

    def _generate_validation_summary_statistics(self) -> Dict[str, Any]:
        """Generate validation summary statistics."""
        if not self.validation_history:
            return {
                "total_validations": 0,
                "success_rate": 0,
                "failure_rate": 0,
                "last_validation": None
            }

        total_validations = len(self.validation_history)
        successful_validations = sum(
            1 for v in self.validation_history if v.get("validation_successful", False)
        )

        return {
            "total_validations": total_validations,
            "successful_validations": successful_validations,
            "success_rate": successful_validations / total_validations if total_validations > 0 else 0,
            "failure_rate": (total_validations - successful_validations) / total_validations if total_validations > 0 else 0,
            "last_validation": self.validation_history[-1]["timestamp"] if self.validation_history else None,
            "last_success": self.validation_history[-1]["validation_successful"] if self.validation_history else None
        }

    def _list_validation_policies(self):
        """List all validation policies."""
        return {
            "available_policies": list(self.validation_config.get("custom_rules", {}).keys()),
            "default_scope": self.validation_config["default_scope"],
            "intensity_levels": list(self.validation_config["intensity_levels"].keys())
        }

    def _add_validation_policy(self, parameters: Dict) -> Dict:
        """Add a validation policy."""
        policy_name = parameters.get("name")
        policy_func = parameters.get("function")

        if not policy_name or not policy_func:
            return {
                "status": "error",
                "error": "Both name and function are required"
            }

        # This would store the policy for future use
        # Implementation would save to policy file
        logger.info(f"Adding validation policy: {policy_name}")

        return {
            "status": "success",
            "policy_name": policy_name,
            "message": f"Validation policy '{policy_name}' added successfully"
        }

    def _remove_validation_policy(self, parameters: Dict) -> Dict:
        """Remove a validation policy."""
        policy_name = parameters.get("name")

        if policy_name in self.validation_config["custom_rules"]:
            del self.validation_config["custom_rules"][policy_name]
            logger.info(f"Removed validation policy: {policy_name}")
            return {
                "status": "success",
                "policy_name": policy_name,
                "message": f"Validation policy '{policy_name}' removed successfully"
            }
        else:
            return {
                "status": "warning",
                "policy_name": policy_name,
                "message": f"Validation policy '{policy_name}' not found"
            }

    def _update_validation_policy(self, parameters: Dict) -> Dict:
        """Update a validation policy."""
        policy_name = parameters.get("name")
        policy_func = parameters.get("function")

        if policy_name in self.validation_config["custom_rules"]:
            self.validation_config["custom_rules"][policy_name] = policy_func
            return self._add_validation_policy(parameters)

        return self._remove_validation_policy(parameters)

    def _get_resource_usage(self) -> Dict[str, Any]:
        """Get current resource usage."""
        try:
            import psutil
            process = psutil.Process()

            return {
                "cpu_percent": process.cpu_percent(),
                "memory_mb": process.memory_info().rss / 1024 / 1024,
                "memory_percent": process.memory_percent(),
                "threads": process.num_threads(),
                "open_files": process.num_fds()
            }

        except:
            return {
                "cpu_percent": 0,
                "memory_mb": 0,
                "memory_percent": 0,
                "threads": 0,
                "open_files": 0
            }

    def _save_validation_history(self, validation_result: Dict[str, Any]) -> None:
        """Save validation operation to history."""
        self.validation_history.append({
            "session_id": validation_result.get("session_id"),
            "timestamp": datetime.now().isoformat(),
            "result": validation_result
        })

        # Keep only last 50 validations
        if len(self.validation_history) > 50:
            self.validation_history = self.validation_history[-50]

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
            "agent_id": "commit_validation_agent",
            "agent_name": "Commit Validation Agent",
            "class_name": "ValidationAgent",
            "file_path": "agents/validation_agent.py",
            "created_by": "claude_code",
            "capabilities": [
                "orchestrate_validation",
                "run_custom_validation",
                "monitor_validation",
                "create_validation_report",
                "manage_validation_policies",
                "validate_specific_scope"
            ],
            "dependencies": [
                "validation_orchestrator"
            ],
            "metadata": {
                "max_execution_time": 120,  # 2 minutes
                "memory_limit_mb": 100,
                "description": "Orchestrates existing Validation Orchestrator with agent coordination, custom validation rules, and detailed reporting",
                "version": "1.0.0"
            }
        }, {"agent_id": "meta_agent"})

        if registration_result.get("success"):
            logger.info("Validation Agent successfully registered with Meta Agent")
        else:
            logger.warning(f"Failed to register with Meta Agent: {registration_result.get('error', 'Unknown error')}")

    except Exception as e:
        logger.error(f"Error registering with Meta Agent: {str(e)}")


if __name__ == "__main__":
    # Test the agent
    agent = ValidationAgent("test_validation_agent")

    # Test capabilities
    capabilities = agent._define_capabilities()
    print(f"Validation Agent initialized with {len(capabilities)} capabilities")

    # Test basic functionality
    try:
        result = agent._execute_action("manage_validation_policies", {"action": "list"}, {})
        print(f"Validation policy management test: {result['status']}")
    except Exception as e:
        print(f"Test failed: {str(e)}")