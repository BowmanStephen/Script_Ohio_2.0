#!/usr/bin/env python3
"""
System Validation Agent

Validates the system environment, dependencies, API configurations, and file structure
to ensure the college football prediction system is ready for Week 12 operations.

Author: Urban Meyer Assistant
Created: 2025-11-13
Purpose: Comprehensive system validation for Week 12 readiness
"""

import os
import sys
import json
import subprocess
import importlib
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import logging

# Import agent framework
sys.path.append(str(Path(__file__).parent.parent.parent.parent))
from agents.core.agent_framework import BaseAgent, AgentCapability, PermissionLevel

# Configure logging
logger = logging.getLogger(__name__)

class SystemValidationAgent(BaseAgent):
    """
    System Validation Agent for Week 12 readiness.

    Responsibilities:
    - Validate CFBD API configuration
    - Check Python environment and dependencies
    - Verify file structure and permissions
    - Test agent framework connectivity
    - Validate data directories and model files
    """

    def __init__(self):
        super().__init__(
            agent_id="system_validation_agent",
            name="System Validation Agent",
            permission_level=PermissionLevel.READ_EXECUTE,
        )

        # Define required Python packages
        self.required_packages = [
            "pandas", "numpy", "matplotlib", "seaborn", "scikit-learn",
            "xgboost", "fastai", "shap", "joblib", "pydantic", "pytest",
            "cfbd"  # CFBD API client
        ]

        # Define required file structure
        self.required_files = [
            "model_pack/ridge_model_2025.joblib",
            "model_pack/xgb_home_win_model_2025.pkl",
            "model_pack/fastai_home_win_model_2025_fixed.pkl",
            "model_pack/updated_training_data.csv",
            "starter_pack/data/games.csv",
            "starter_pack/data/team_talent.csv",
            "agents/core/agent_framework.py",
            "agents/analytics_orchestrator.py"
        ]

        # Define required directories
        self.required_directories = [
            "model_pack",
            "starter_pack/data",
            "starter_pack",
            "agents/core",
            "agents",
            "tests",
            "project_management/WEEK12_READINESS"
        ]

    def _define_capabilities(self) -> List[AgentCapability]:
        """Define system validation capabilities"""
        return [
            AgentCapability(
                name="api_validation",
                description="Validate CFBD API configuration and connectivity",
                permission_required=PermissionLevel.READ_EXECUTE,
                tools_required=["api_tester", "credential_checker"],
                data_access=["environment_variables", "api_endpoints"],
                execution_time_estimate=5.0
            ),
            AgentCapability(
                name="environment_validation",
                description="Check Python version and package dependencies",
                permission_required=PermissionLevel.READ_ONLY,
                tools_required=["package_checker", "version_validator"],
                data_access=["python_path", "installed_packages"],
                execution_time_estimate=3.0
            ),
            AgentCapability(
                name="file_structure_validation",
                description="Verify required files and directories exist",
                permission_required=PermissionLevel.READ_ONLY,
                tools_required=["file_checker", "permission_validator"],
                data_access=["project_files", "model_files", "data_files"],
                execution_time_estimate=2.0
            ),
            AgentCapability(
                name="agent_framework_validation",
                description="Test agent framework connectivity and functionality",
                permission_required=PermissionLevel.READ_EXECUTE,
                tools_required=["framework_tester", "agent_launcher"],
                data_access=["agent_configs", "framework_modules"],
                execution_time_estimate=4.0
            )
        ]

    def _execute_action(self, action: str, parameters: Dict[str, Any],
                       user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute system validation actions"""
        try:
            if action == "validate_system":
                return self._validate_complete_system(parameters)
            elif action == "validate_api":
                return self._validate_api_configuration()
            elif action == "validate_environment":
                return self._validate_environment()
            elif action == "validate_file_structure":
                return self._validate_file_structure()
            elif action == "validate_agent_framework":
                return self._validate_agent_framework()
            else:
                return {
                    "success": False,
                    "error_message": f"Unknown action: {action}",
                    "error_code": "UNKNOWN_ACTION"
                }
        except Exception as e:
            logger.error(f"System validation action failed: {e}")
            return {
                "success": False,
                "error_message": str(e),
                "error_code": "VALIDATION_ERROR"
            }

    def execute_week12_task(self, execution_context) -> Dict[str, Any]:
        """Execute Week 12 system validation task"""
        logger.info("Starting Week 12 system validation")

        validation_results = {
            "timestamp": datetime.now().isoformat(),
            "execution_context": execution_context.execution_id,
            "validations": {}
        }

        overall_success = True

        # 1. Validate CFBD API Configuration
        api_result = self._validate_api_configuration()
        validation_results["validations"]["api"] = api_result
        if not api_result["success"]:
            overall_success = False

        # 2. Validate Environment
        env_result = self._validate_environment()
        validation_results["validations"]["environment"] = env_result
        if not env_result["success"]:
            overall_success = False

        # 3. Validate File Structure
        file_result = self._validate_file_structure()
        validation_results["validations"]["file_structure"] = file_result
        if not file_result["success"]:
            overall_success = False

        # 4. Validate Agent Framework
        framework_result = self._validate_agent_framework()
        validation_results["validations"]["agent_framework"] = framework_result
        if not framework_result["success"]:
            overall_success = False

        # 5. Calculate Overall System Readiness
        validation_results["overall_success"] = overall_success
        validation_results["readiness_score"] = self._calculate_readiness_score(validation_results["validations"])
        validation_results["summary"] = self._generate_validation_summary(validation_results["validations"])

        # 6. Provide Recommendations
        validation_results["recommendations"] = self._generate_recommendations(validation_results["validations"])

        logger.info(f"Week 12 system validation completed. Success: {overall_success}")

        return {
            "success": overall_success,
            "validation_results": validation_results,
            "message": self._generate_user_message(validation_results),
            "readiness_score": validation_results["readiness_score"]
        }

    def _validate_api_configuration(self) -> Dict[str, Any]:
        """Validate CFBD API configuration and connectivity"""
        logger.info("Validating CFBD API configuration")

        result = {
            "success": True,
            "api_key_present": False,
            "connectivity_test": False,
            "api_version": None,
            "issues": [],
            "recommendations": []
        }

        try:
            # Check if CFBD API key is present
            cfbd_api_key = os.environ.get("CFBD_API_KEY")
            if not cfbd_api_key:
                result["issues"].append("CFBD_API_KEY environment variable not set")
                result["recommendations"].append("Set CFBD_API_KEY environment variable with your API key")
                result["success"] = False
            else:
                result["api_key_present"] = True
                logger.info("CFBD API key found in environment")

            # Test CFBD package import
            try:
                import cfbd
                result["cfbd_package_installed"] = True
                result["cfbd_version"] = cfbd.__version__ if hasattr(cfbd, '__version__') else "unknown"
                logger.info(f"CFBD package version: {result['cfbd_version']}")
            except ImportError as e:
                result["issues"].append(f"CFBD package not installed: {e}")
                result["recommendations"].append("Install CFBD package: pip install cfbd")
                result["cfbd_package_installed"] = False
                result["success"] = False

            # Test API connectivity (if API key is present)
            if result["api_key_present"] and result["cfbd_package_installed"]:
                try:
                    import cfbd
                    configuration = cfbd.Configuration()
                    configuration.api_key['Authorization'] = cfbd_api_key
                    configuration.api_key_prefix['Authorization'] = 'Bearer'
                    configuration.host = "https://api.collegefootballdata.com"

                    with cfbd.ApiClient(configuration) as api_client:
                        games_api = cfbd.GamesApi(api_client)
                        # Test with a simple request - get 2025 games
                        games = games_api.get_games(year=2025, seasonType='regular')
                        result["connectivity_test"] = True
                        result["api_test_result"] = f"Successfully retrieved {len(games)} 2025 games"
                        logger.info("CFBD API connectivity test successful")

                except Exception as e:
                    result["issues"].append(f"CFBD API connectivity test failed: {e}")
                    result["recommendations"].append("Check CFBD API key and internet connection")
                    result["connectivity_test"] = False
                    result["success"] = False

        except Exception as e:
            result["issues"].append(f"API validation error: {e}")
            result["success"] = False
            logger.error(f"API validation failed: {e}")

        return result

    def _validate_environment(self) -> Dict[str, Any]:
        """Validate Python environment and dependencies"""
        logger.info("Validating Python environment")

        result = {
            "success": True,
            "python_version": sys.version,
            "python_version_ok": False,
            "packages": {},
            "missing_packages": [],
            "issues": [],
            "recommendations": []
        }

        try:
            # Check Python version
            python_version_tuple = sys.version_info
            if python_version_tuple >= (3, 13):
                result["python_version_ok"] = True
                logger.info(f"Python version {python_version_tuple.major}.{python_version_tuple.minor} is acceptable")
            else:
                result["issues"].append(f"Python version {python_version_tuple.major}.{python_version_tuple.minor} is below required 3.13")
                result["recommendations"].append("Upgrade to Python 3.13 or higher")
                result["success"] = False

            # Check required packages
            for package in self.required_packages:
                try:
                    module = importlib.import_module(package)
                    version = getattr(module, '__version__', 'unknown')
                    result["packages"][package] = {
                        "installed": True,
                        "version": version,
                        "import_success": True
                    }
                    logger.debug(f"Package {package} version {version} found")
                except ImportError as e:
                    result["packages"][package] = {
                        "installed": False,
                        "version": None,
                        "import_success": False,
                        "error": str(e)
                    }
                    result["missing_packages"].append(package)
                    result["issues"].append(f"Missing required package: {package}")
                    logger.warning(f"Package {package} not found: {e}")

            # Check critical packages in detail
            critical_packages = ["pandas", "numpy", "scikit-learn", "joblib"]
            for package in critical_packages:
                if package in result["missing_packages"]:
                    result["recommendations"].append(f"Install {package}: pip install {package}")

            if result["missing_packages"]:
                result["success"] = False

        except Exception as e:
            result["issues"].append(f"Environment validation error: {e}")
            result["success"] = False
            logger.error(f"Environment validation failed: {e}")

        return result

    def _validate_file_structure(self) -> Dict[str, Any]:
        """Validate required file structure"""
        logger.info("Validating file structure")

        result = {
            "success": True,
            "files": {},
            "directories": {},
            "missing_files": [],
            "missing_directories": [],
            "issues": [],
            "recommendations": []
        }

        try:
            # Check required directories
            for directory in self.required_directories:
                dir_path = Path(directory)
                exists = dir_path.exists() and dir_path.is_dir()
                readable = dir_path.exists() and os.access(dir_path, os.R_OK)

                result["directories"][directory] = {
                    "exists": exists,
                    "readable": readable,
                    "path": str(dir_path.absolute())
                }

                if not exists:
                    result["missing_directories"].append(directory)
                    result["issues"].append(f"Missing required directory: {directory}")
                    result["recommendations"].append(f"Create directory: {directory}")
                    result["success"] = False
                elif not readable:
                    result["issues"].append(f"Directory not readable: {directory}")
                    result["recommendations"].append(f"Check permissions for: {directory}")
                    result["success"] = False

            # Check required files
            for file_path in self.required_files:
                path = Path(file_path)
                exists = path.exists() and path.is_file()
                readable = path.exists() and os.access(path, os.R_OK)

                # Get file size if exists
                size = None
                if exists:
                    size = path.stat().st_size

                result["files"][file_path] = {
                    "exists": exists,
                    "readable": readable,
                    "size_bytes": size,
                    "path": str(path.absolute())
                }

                if not exists:
                    result["missing_files"].append(file_path)
                    result["issues"].append(f"Missing required file: {file_path}")
                    result["recommendations"].append(f"Ensure file exists: {file_path}")
                    result["success"] = False
                elif not readable:
                    result["issues"].append(f"File not readable: {file_path}")
                    result["recommendations"].append(f"Check permissions for: {file_path}")
                    result["success"] = False
                elif size and size == 0:
                    result["issues"].append(f"File is empty: {file_path}")
                    result["recommendations"].append(f"File appears to be empty: {file_path}")

        except Exception as e:
            result["issues"].append(f"File structure validation error: {e}")
            result["success"] = False
            logger.error(f"File structure validation failed: {e}")

        return result

    def _validate_agent_framework(self) -> Dict[str, Any]:
        """Validate agent framework functionality"""
        logger.info("Validating agent framework")

        result = {
            "success": True,
            "framework_importable": False,
            "base_agent_test": False,
            "analytics_orchestrator_test": False,
            "issues": [],
            "recommendations": []
        }

        try:
            # Test agent framework import
            try:
                from agents.core.agent_framework import BaseAgent
                result["framework_importable"] = True
                logger.info("Agent framework imported successfully")
            except ImportError as e:
                result["issues"].append(f"Cannot import agent framework: {e}")
                result["recommendations"].append("Check agent framework installation and Python path")
                result["success"] = False
                return result

            # Test BaseAgent instantiation
            try:
                test_agent = BaseAgent(
                    agent_id="test_validation_agent",
                    name="Test Validation Agent",
                    permission_level=PermissionLevel.READ_ONLY
                )
                result["base_agent_test"] = True
                logger.info("BaseAgent instantiation successful")
            except Exception as e:
                result["issues"].append(f"BaseAgent instantiation failed: {e}")
                result["success"] = False

            # Test Analytics Orchestrator
            try:
                from agents.analytics_orchestrator import AnalyticsOrchestrator
                # Just test import, don't instantiate to avoid dependencies
                result["analytics_orchestrator_test"] = True
                logger.info("Analytics Orchestrator import successful")
            except ImportError as e:
                result["issues"].append(f"Cannot import Analytics Orchestrator: {e}")
                result["recommendations"].append("Check analytics orchestrator implementation")
                # Don't fail the whole validation for this, but note it

            # Test context manager
            try:
                from agents.core.context_manager import ContextManager
                result["context_manager_test"] = True
                logger.info("Context Manager import successful")
            except ImportError as e:
                result["issues"].append(f"Cannot import Context Manager: {e}")
                result["recommendations"].append("Check context manager implementation")
                # Don't fail for this either

        except Exception as e:
            result["issues"].append(f"Agent framework validation error: {e}")
            result["success"] = False
            logger.error(f"Agent framework validation failed: {e}")

        return result

    def _calculate_readiness_score(self, validations: Dict[str, Any]) -> float:
        """Calculate overall system readiness score"""
        weights = {
            "api": 0.25,        # API access is critical
            "environment": 0.25, # Environment is critical
            "file_structure": 0.25, # File structure is critical
            "agent_framework": 0.25 # Agent framework is critical
        }

        total_score = 0.0
        total_weight = 0.0

        for validation_name, weight in weights.items():
            if validation_name in validations:
                validation = validations[validation_name]
                if validation["success"]:
                    total_score += weight * 100
                else:
                    # Partial credit for partial success
                    success_rate = self._calculate_validation_success_rate(validation)
                    total_score += weight * success_rate
                total_weight += weight

        if total_weight > 0:
            return round(total_score / total_weight, 1)
        return 0.0

    def _calculate_validation_success_rate(self, validation: Dict[str, Any]) -> float:
        """Calculate success rate for a partial validation"""
        # This is a simplified calculation - in practice, you'd want more nuanced logic
        if "files" in validation:
            total_files = len(validation["files"])
            successful_files = sum(1 for f in validation["files"].values() if f.get("exists", False))
            if total_files > 0:
                return (successful_files / total_files) * 100

        if "packages" in validation:
            total_packages = len(validation["packages"])
            successful_packages = sum(1 for p in validation["packages"].values() if p.get("installed", False))
            if total_packages > 0:
                return (successful_packages / total_packages) * 100

        return 0.0

    def _generate_validation_summary(self, validations: Dict[str, Any]) -> str:
        """Generate a human-readable validation summary"""
        summary_parts = []

        for validation_name, validation in validations.items():
            if validation["success"]:
                summary_parts.append(f"✅ {validation_name.replace('_', ' ').title()}: OK")
            else:
                issues_count = len(validation.get("issues", []))
                summary_parts.append(f"❌ {validation_name.replace('_', ' ').title()}: {issues_count} issues")

        return " | ".join(summary_parts)

    def _generate_recommendations(self, validations: Dict[str, Any]) -> List[str]:
        """Generate consolidated recommendations from all validations"""
        all_recommendations = []

        for validation in validations.values():
            recommendations = validation.get("recommendations", [])
            all_recommendations.extend(recommendations)

        # Remove duplicates while preserving order
        seen = set()
        unique_recommendations = []
        for rec in all_recommendations:
            if rec not in seen:
                seen.add(rec)
                unique_recommendations.append(rec)

        return unique_recommendations

    def _generate_user_message(self, validation_results: Dict[str, Any]) -> str:
        """Generate user-friendly message based on validation results"""
        score = validation_results["readiness_score"]

        if validation_results["overall_success"]:
            return (
                f"✅ **System Validation Complete!**\n\n"
                f"Your system is {score}% ready for Week 12 predictions.\n\n"
                f"All critical components are working:\n"
                f"• CFBD API connection established\n"
                f"• Python environment configured\n"
                f"• File structure verified\n"
                f"• Agent framework operational\n\n"
                f"You're ready to proceed with the next steps! 🚀"
            )
        else:
            recommendations = validation_results["recommendations"][:5]  # Show top 5
            rec_text = "\n".join(f"• {rec}" for rec in recommendations)

            return (
                f"⚠️ **System Validation Complete - Issues Found**\n\n"
                f"Your system is {score}% ready for Week 12 predictions.\n\n"
                f"I found some issues that need attention:\n"
                f"{rec_text}\n\n"
                f"Don't worry - I can help fix most of these automatically!\n"
                f"Would you like me to proceed with the automated fixes? 🔧"
            )

def main():
    """Command-line interface for system validation"""
    agent = SystemValidationAgent()

    print("🔍 System Validation Agent")
    print("=" * 40)

    # Create mock execution context for testing
    class MockExecutionContext:
        def __init__(self):
            self.execution_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    result = agent.execute_week12_task(MockExecutionContext())

    print(f"\nValidation completed. Success: {result['success']}")
    print(f"Readiness Score: {result['readiness_score']}%")

    return 0 if result["success"] else 1

if __name__ == "__main__":
    exit(main())