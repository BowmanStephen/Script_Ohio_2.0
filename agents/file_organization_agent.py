"""
File Organization Agent - Specialized agent for organizing project files

Extends BaseAgent to provide intelligent file organization capabilities
following Script Ohio 2.0 project structure standards.
"""

import os
import shutil
import time
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from agents.core.agent_framework import BaseAgent, AgentCapability, PermissionLevel

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FileOrganizationAgent(BaseAgent):
    """
    Specialized agent for organizing misplaced project files into appropriate
    subdirectories according to CLAUDE.md specifications.

    Capabilities:
    - Classify root directory files by type
    - Create missing directory structure
    - Move files with proper naming conventions
    - Handle special cases like Desktop screenshots
    """

    def __init__(self, agent_id: str, tool_loader=None):
        """Initialize the File Organization Agent."""
        super().__init__(
            agent_id=agent_id,
            name="File Organization Agent",
            permission_level=PermissionLevel.READ_EXECUTE_WRITE,
            tool_loader=tool_loader
        )

        self.project_root = Path.cwd()
        self.organization_log = []

    def _define_capabilities(self) -> List[AgentCapability]:
        """Define agent capabilities following BaseAgent pattern."""
        return [
            AgentCapability(
                name="classify_root_files",
                description="Identify and categorize misplaced files in root directory",
                permission_required=PermissionLevel.READ_ONLY,
                tools_required=["pathlib", "os"],
                data_access=["root_directory"],
                execution_time_estimate=1.0
            ),
            AgentCapability(
                name="create_missing_directories",
                description="Create missing directory structure per CLAUDE.md",
                permission_required=PermissionLevel.READ_EXECUTE_WRITE,
                tools_required=["pathlib", "os"],
                data_access=["filesystem"],
                execution_time_estimate=0.5
            ),
            AgentCapability(
                name="organize_into_directories",
                description="Move files to appropriate subdirectories with proper naming",
                permission_required=PermissionLevel.READ_EXECUTE_WRITE,
                tools_required=["shutil", "pathlib", "os"],
                data_access=["filesystem", "root_directory"],
                execution_time_estimate=2.0
            )
        ]

    def _execute_action(self, action: str, parameters: Dict[str, Any],
                       user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent actions with proper error handling and logging."""

        try:
            start_time = time.time()

            if action == "classify_root_files":
                result = self._classify_root_files()
            elif action == "create_missing_directories":
                result = self._create_missing_directories()
            elif action == "organize_into_directories":
                result = self._organize_into_directories()
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

    def _classify_root_files(self) -> Dict[str, List[str]]:
        """Classify files in root directory by type and destination."""

        logger.info("Classifying root directory files...")

        # File classification mapping
        file_categories = {
            "config_files": {
                "files": [],
                "destination": "project_management/config/",
                "patterns": ["requirements*.txt", ".env", "Makefile", "Dockerfile"]
            },
            "python_scripts": {
                "files": [],
                "destination": "project_management/core_tools/SCRIPTS/",
                "patterns": ["*.py"]
            },
            "documentation": {
                "files": [],
                "destination": "documentation/",
                "patterns": ["*.md", "*.txt", "*.rst"]
            },
            "images": {
                "files": [],
                "destination": "documentation/images/",
                "patterns": ["*.png", "*.jpg", "*.jpeg", "*.gif", "*.svg"]
            }
        }

        # Skip these files in root
        skip_files = {".git", ".gitignore", "CLAUDE.md", ".DS_Store", "__pycache__"}

        root_files = [f for f in self.project_root.iterdir()
                     if f.is_file() and f.name not in skip_files]

        classified_files = {}

        for file_path in root_files:
            file_name = file_path.name

            # Classify by pattern matching
            for category, info in file_categories.items():
                for pattern in info["patterns"]:
                    if Path(file_name).match(pattern):
                        info["files"].append(file_path)
                        classified_files[str(file_path)] = {
                            "category": category,
                            "destination": info["destination"],
                            "original_path": str(file_path)
                        }
                        break
                else:
                    continue
                break

        # Special case: look for screenshot on Desktop
        desktop_path = Path.home() / "Desktop"
        if desktop_path.exists():
            for file_path in desktop_path.iterdir():
                if file_path.is_file() and "Screenshot" in file_path.name:
                    screenshot_info = {
                        "category": "images",
                        "destination": "documentation/images/",
                        "original_path": str(file_path),
                        "is_desktop_screenshot": True
                    }
                    classified_files[str(file_path)] = screenshot_info
                    file_categories["images"]["files"].append(file_path)
                    logger.info(f"Found Desktop screenshot: {file_path.name}")

        # Log classification results
        self.organization_log.append({
            "action": "classify",
            "files_found": len(classified_files),
            "categories": {cat: len(info["files"]) for cat, info in file_categories.items()},
            "timestamp": datetime.now().isoformat()
        })

        logger.info(f"Classified {len(classified_files)} files")

        return {
            "classified_files": classified_files,
            "file_categories": file_categories,
            "total_files": len(classified_files)
        }

    def _create_missing_directories(self) -> Dict[str, bool]:
        """Create missing directory structure per CLAUDE.md specifications."""

        logger.info("Creating missing directory structure...")

        required_directories = [
            "project_management/CONFIG",
            "project_management/core_tools/SCRIPTS",
            "documentation/images",
            "project_management/quality_assurance/REPORTS"
        ]

        created_directories = {}

        for dir_path in required_directories:
            full_path = self.project_root / dir_path

            if full_path.exists():
                created_directories[dir_path] = False
                logger.info(f"Directory already exists: {dir_path}")
            else:
                try:
                    full_path.mkdir(parents=True, exist_ok=True)
                    created_directories[dir_path] = True
                    logger.info(f"Created directory: {dir_path}")

                    self.organization_log.append({
                        "action": "create_directory",
                        "directory": dir_path,
                        "success": True,
                        "timestamp": datetime.now().isoformat()
                    })

                except Exception as e:
                    logger.error(f"Failed to create directory {dir_path}: {e}")
                    created_directories[dir_path] = False

        return {
            "created_directories": created_directories,
            "total_created": sum(created_directories.values())
        }

    def _organize_into_directories(self) -> Dict[str, Any]:
        """Move classified files to appropriate directories with proper naming."""

        logger.info("Organizing files into directories...")

        # First classify files
        classification_result = self._classify_root_files()
        classified_files = classification_result["classified_files"]

        # Ensure directories exist
        self._create_missing_directories()

        moved_files = {}
        failed_moves = {}

        for file_path_str, file_info in classified_files.items():
            file_path = Path(file_path_str)
            destination_dir = self.project_root / file_info["destination"]

            # Handle special case for Desktop screenshot
            if "Screenshot" in file_path.name and "Desktop" in str(file_path):
                new_name = f"screenshot_{datetime.now().strftime('%Y-%m-%d')}.png"
                destination_path = destination_dir / new_name
            else:
                destination_path = destination_dir / file_path.name

            try:
                # Handle file name conflicts
                if destination_path.exists():
                    base_name = destination_path.stem
                    extension = destination_path.suffix
                    counter = 1
                    while destination_path.exists():
                        new_name = f"{base_name}_{counter}{extension}"
                        destination_path = destination_dir / new_name
                        counter += 1

                # Move the file
                shutil.move(str(file_path), str(destination_path))

                moved_files[str(file_path)] = {
                    "destination": str(destination_path),
                    "category": file_info["category"],
                    "original_size": file_path.stat().st_size if file_path.exists() else 0
                }

                self.organization_log.append({
                    "action": "move_file",
                    "source": str(file_path),
                    "destination": str(destination_path),
                    "category": file_info["category"],
                    "success": True,
                    "timestamp": datetime.now().isoformat()
                })

                logger.info(f"Moved: {file_path.name} → {file_info['destination']}")

            except Exception as e:
                logger.error(f"Failed to move {file_path}: {e}")
                failed_moves[str(file_path)] = {
                    "error": str(e),
                    "category": file_info["category"]
                }

        return {
            "moved_files": moved_files,
            "failed_moves": failed_moves,
            "total_moved": len(moved_files),
            "total_failed": len(failed_moves)
        }

    def get_organization_summary(self) -> Dict[str, Any]:
        """Get a summary of all organization actions performed."""

        return {
            "agent_id": self.agent_id,
            "total_actions": len(self.organization_log),
            "actions_by_type": {
                action_type: len([log for log in self.organization_log if log["action"] == action_type])
                for action_type in set(log["action"] for log in self.organization_log)
            },
            "detailed_log": self.organization_log,
            "project_root": str(self.project_root),
            "timestamp": datetime.now().isoformat()
        }


def create_file_organization_agent(agent_id: str = "file_org_agent") -> FileOrganizationAgent:
    """Factory function to create a FileOrganizationAgent instance."""
    return FileOrganizationAgent(agent_id=agent_id)


if __name__ == "__main__":
    # Demo the agent
    agent = create_file_organization_agent()

    print("=== File Organization Agent Demo ===")
    print(f"Agent ID: {agent.agent_id}")
    print(f"Capabilities: {[cap.name for cap in agent.capabilities]}")

    # Test classification
    print("\n=== Classifying Files ===")
    result = agent.process_request("classify_root_files", {})
    print(f"Classification result: {result['status']}")

    if result['status'] == 'success':
        classified = result['result']['total_files']
        print(f"Found {classified} files to organize")