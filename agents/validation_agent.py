"""
System Validation Agent - Specialized agent for validating file organization integrity

Extends BaseAgent to provide comprehensive validation and integrity checking
after file organization operations.
"""

import os
import sys
import importlib
import logging
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from datetime import datetime

from agents.core.agent_framework import BaseAgent, AgentCapability, PermissionLevel

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ValidationAgent(BaseAgent):
    """
    Specialized agent for validating file organization and system integrity.

    Capabilities:
    - Validate file moves completed successfully
    - Check Python import integrity after script moves
    - Update .gitignore with appropriate exclusions
    - Generate comprehensive validation reports
    """

    def __init__(self, agent_id: str, tool_loader=None):
        """Initialize the Validation Agent."""
        super().__init__(
            agent_id=agent_id,
            name="System Validation Agent",
            permission_level=PermissionLevel.READ_EXECUTE,
            tool_loader=tool_loader
        )

        self.project_root = Path.cwd()
        self.validation_results = []

    def _define_capabilities(self) -> List[AgentCapability]:
        """Define agent capabilities following BaseAgent pattern."""
        return [
            AgentCapability(
                name="validate_file_moves",
                description="Verify all files moved correctly and exist in destinations",
                permission_required=PermissionLevel.READ_ONLY,
                tools_required=["pathlib", "os"],
                data_access=["filesystem"],
                execution_time_estimate=1.0
            ),
            AgentCapability(
                name="validate_import_integrity",
                description="Check Python imports still work after file reorganization",
                permission_required=PermissionLevel.READ_EXECUTE,
                tools_required=["importlib", "sys"],
                data_access=["python_modules"],
                execution_time_estimate=1.5
            ),
            AgentCapability(
                name="update_gitignore",
                description="Update .gitignore with new exclusions for organized files",
                permission_required=PermissionLevel.READ_EXECUTE_WRITE,
                tools_required=["pathlib"],
                data_access=["filesystem"],
                execution_time_estimate=0.5
            ),
            AgentCapability(
                name="generate_validation_report",
                description="Create comprehensive validation and organization report",
                permission_required=PermissionLevel.READ_ONLY,
                tools_required=["json", "pathlib"],
                data_access=["filesystem"],
                execution_time_estimate=0.5
            )
        ]

    def _execute_action(self, action: str, parameters: Dict[str, Any],
                       user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent actions with proper error handling and logging."""

        try:
            start_time = time.time()

            if action == "validate_file_moves":
                result = self._validate_file_moves(parameters.get("moved_files", {}))
            elif action == "validate_import_integrity":
                result = self._validate_import_integrity()
            elif action == "update_gitignore":
                result = self._update_gitignore()
            elif action == "generate_validation_report":
                result = self._generate_validation_report(parameters.get("organization_log", []))
            else:
                raise ValueError(f"Unknown action: {action}")

            execution_time = time.time() - start_time

            return {
                "status": "success",
                "result": result,
                "execution_time": execution_time,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error in {action}: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def _validate_file_moves(self, moved_files: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Validate that all file moves completed successfully."""

        logger.info("Validating file moves...")

        validated_files = {}
        missing_files = {}
        size_mismatches = {}

        for original_path, move_info in moved_files.items():
            destination_path = move_info.get("destination")
            original_size = move_info.get("original_size", 0)

            if not destination_path:
                missing_files[original_path] = "No destination path recorded"
                continue

            dest_path = Path(destination_path)

            if not dest_path.exists():
                missing_files[original_path] = f"Destination file not found: {destination_path}"
                continue

            # Check file size (if original size was recorded)
            current_size = dest_path.stat().st_size
            if original_size > 0 and current_size != original_size:
                size_mismatches[original_path] = {
                    "original_size": original_size,
                    "current_size": current_size,
                    "destination": destination_path
                }

            validated_files[original_path] = {
                "destination": destination_path,
                "exists": True,
                "size": current_size,
                "category": move_info.get("category", "unknown")
            }

        validation_result = {
            "total_files": len(moved_files),
            "validated_files": len(validated_files),
            "missing_files": len(missing_files),
            "size_mismatches": len(size_mismatches),
            "success_rate": len(validated_files) / len(moved_files) if moved_files else 1.0,
            "validated_details": validated_files,
            "missing_details": missing_files,
            "size_mismatch_details": size_mismatches
        }

        self.validation_results.append({
            "action": "validate_file_moves",
            "result": validation_result,
            "timestamp": datetime.now().isoformat()
        })

        logger.info(f"Validated {len(validated_files)}/{len(moved_files)} files successfully")

        return validation_result

    def _validate_import_integrity(self) -> Dict[str, Any]:
        """Validate that Python imports still work after file reorganization."""

        logger.info("Validating Python import integrity...")

        # Key modules to check
        modules_to_test = [
            "agents.core.agent_framework",
            "agents.analytics_orchestrator",
            "agents.file_organization_agent",  # Our new agent
            "agents.validation_agent",  # This agent
        ]

        import_results = {}
        failed_imports = {}
        warning_imports = {}

        # Add project root to Python path if not already there
        project_root_str = str(self.project_root)
        if project_root_str not in sys.path:
            sys.path.insert(0, project_root_str)

        for module_name in modules_to_test:
            try:
                # Try to import the module
                module = importlib.import_module(module_name)
                import_results[module_name] = {
                    "success": True,
                    "module_path": getattr(module, '__file__', 'built-in'),
                    "module_version": getattr(module, '__version__', 'unknown')
                }

                # Additional checks for agent modules
                if "agent" in module_name.lower():
                    # Check if it has required BaseAgent methods
                    if hasattr(module, 'BaseAgent') or hasattr(module, 'process_request'):
                        import_results[module_name]["agent_compatible"] = True
                    else:
                        warning_imports[module_name] = "Module may not follow agent pattern"

            except ImportError as e:
                failed_imports[module_name] = str(e)
            except Exception as e:
                warning_imports[module_name] = f"Import succeeded but with warnings: {str(e)}"

        validation_result = {
            "total_modules_tested": len(modules_to_test),
            "successful_imports": len(import_results),
            "failed_imports": len(failed_imports),
            "warning_imports": len(warning_imports),
            "import_success_rate": len(import_results) / len(modules_to_test),
            "successful_imports_detail": import_results,
            "failed_imports_detail": failed_imports,
            "warning_imports_detail": warning_imports,
            "python_path_entries": sys.path[:5]  # First 5 entries
        }

        self.validation_results.append({
            "action": "validate_import_integrity",
            "result": validation_result,
            "timestamp": datetime.now().isoformat()
        })

        logger.info(f"Import validation: {len(import_results)}/{len(modules_to_test)} modules imported successfully")

        return validation_result

    def _update_gitignore(self) -> Dict[str, Any]:
        """Update .gitignore with appropriate exclusions for the organized project."""

        logger.info("Updating .gitignore file...")

        gitignore_path = self.project_root / ".gitignore"
        required_exclusions = [
            "# Python",
            "__pycache__/",
            "*.py[cod]",
            "*$py.class",
            "*.so",
            ".Python",
            "build/",
            "develop-eggs/",
            "dist/",
            "downloads/",
            "eggs/",
            ".eggs/",
            "lib/",
            "lib64/",
            "parts/",
            "sdist/",
            "var/",
            "wheels/",
            "*.egg-info/",
            ".installed.cfg",
            "*.egg",
            "",
            "# Virtual environments",
            "venv/",
            "env/",
            "ENV/",
            ".venv/",
            "",
            "# IDE",
            ".vscode/",
            ".idea/",
            "*.swp",
            "*.swo",
            "*~",
            "",
            "# OS",
            ".DS_Store",
            "Thumbs.db",
            "",
            "# Project specific",
            "outputs/",
            "temp/",
            "exports/",
            "*.log",
            ".env",
            "model_pack/*.pkl",  # Exclude large model files from git
            "starter_pack/data/*.csv",  # Exclude large data files
            "",
            "# Documentation builds",
            "_build/",
            "*.md.html",
        ]

        try:
            # Read existing .gitignore if it exists
            existing_exclusions = []
            if gitignore_path.exists():
                with open(gitignore_path, 'r', encoding='utf-8') as f:
                    existing_exclusions = [line.strip() for line in f.readlines()]

            # Find new exclusions to add
            new_exclusions = []
            for exclusion in required_exclusions:
                if exclusion and exclusion not in existing_exclusions:
                    new_exclusions.append(exclusion)

            # Update .gitignore if there are new exclusions
            if new_exclusions:
                with open(gitignore_path, 'a', encoding='utf-8') as f:
                    if existing_exclusions and existing_exclusions[-1]:  # Add blank line if needed
                        f.write('\n')
                    for exclusion in new_exclusions:
                        f.write(f"{exclusion}\n")

            update_result = {
                "gitignore_exists": gitignore_path.exists(),
                "total_required_exclusions": len([e for e in required_exclusions if e]),
                "existing_exclusions": len(existing_exclusions),
                "new_exclusions_added": len(new_exclusions),
                "new_exclusions": new_exclusions,
                "gitignore_updated": len(new_exclusions) > 0
            }

        except Exception as e:
            logger.error(f"Failed to update .gitignore: {e}")
            update_result = {
                "gitignore_exists": gitignore_path.exists(),
                "error": str(e),
                "gitignore_updated": False
            }

        self.validation_results.append({
            "action": "update_gitignore",
            "result": update_result,
            "timestamp": datetime.now().isoformat()
        })

        logger.info(f".gitignore updated: {update_result.get('gitignore_updated', False)}")

        return update_result

    def _generate_validation_report(self, organization_log: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a comprehensive validation and organization report."""

        logger.info("Generating validation report...")

        # Get current directory structure
        root_files = [f.name for f in self.project_root.iterdir() if f.is_file()]
        directories = [d.name for d in self.project_root.iterdir() if d.is_dir()]

        report = {
            "validation_summary": {
                "validation_agent_id": self.agent_id,
                "validation_timestamp": datetime.now().isoformat(),
                "total_validations": len(self.validation_results),
                "validation_types": list(set(v["action"] for v in self.validation_results))
            },
            "organization_summary": {
                "total_organization_actions": len(organization_log),
                "organization_timestamp": organization_log[-1]["timestamp"] if organization_log else None,
                "actions_by_type": {
                    action_type: len([log for log in organization_log if log["action"] == action_type])
                    for action_type in set(log["action"] for log in organization_log)
                }
            },
            "current_project_state": {
                "root_files_count": len(root_files),
                "root_files": root_files,
                "directories_count": len(directories),
                "directories": directories,
                "project_root": str(self.project_root)
            },
            "detailed_validation_results": self.validation_results,
            "organization_log": organization_log,
            "success_criteria": {
                "root_directory_clean": len([f for f in root_files if f not in {".git", ".gitignore", "CLAUDE.md"}]) <= 1,
                "all_validations_passed": all(
                    v.get("result", {}).get("success_rate", 0) >= 0.95
                    for v in self.validation_results
                    if "success_rate" in v.get("result", {})
                )
            }
        }

        # Save report to file
        report_path = self.project_root / "project_management" / "QUALITY_ASSURANCE" / "REPORTS"
        report_path.mkdir(parents=True, exist_ok=True)

        report_file = report_path / f"organization_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        try:
            import json
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, default=str)

            report["report_saved_to"] = str(report_file)
            logger.info(f"Validation report saved to: {report_file}")

        except Exception as e:
            logger.error(f"Failed to save validation report: {e}")
            report["report_save_error"] = str(e)

        return report

    def get_validation_summary(self) -> Dict[str, Any]:
        """Get a summary of all validation actions performed."""
        return {
            "agent_id": self.agent_id,
            "total_validations": len(self.validation_results),
            "validation_types": list(set(v["action"] for v in self.validation_results)),
            "latest_validation": self.validation_results[-1] if self.validation_results else None,
            "project_root": str(self.project_root),
            "timestamp": datetime.now().isoformat()
        }


def create_validation_agent(agent_id: str = "validation_agent") -> ValidationAgent:
    """Factory function to create a ValidationAgent instance."""
    return ValidationAgent(agent_id=agent_id)


if __name__ == "__main__":
    # Demo the agent
    agent = create_validation_agent()

    print("=== Validation Agent Demo ===")
    print(f"Agent ID: {agent.agent_id}")
    print(f"Capabilities: {[cap.name for cap in agent.capabilities]}")

    # Test validation
    print("\n=== Testing Import Validation ===")
    result = agent.process_request("validate_import_integrity", {})
    print(f"Import validation result: {result['status']}")

    if result['status'] == 'success':
        success_rate = result['result']['import_success_rate']
        print(f"Import success rate: {success_rate:.2%}")