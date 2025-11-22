"""
Prompt Library Agent - Generates Prompt Library entries from Claude Code agents

Extends BaseAgent to provide automated documentation of Claude Code agents
as standardized Prompt Library entries with complete frontmatter metadata.
"""

import time
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from agents.core.agent_framework import BaseAgent, AgentCapability, PermissionLevel

# Import utility functions
import sys
import os
import importlib.util
# Add project root to path and load utils module
project_root = Path(__file__).resolve().parents[1]
utils_path = project_root / "scripts" / "prompt_library_utils.py"
spec = importlib.util.spec_from_file_location("prompt_library_utils", utils_path)
prompt_library_utils = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prompt_library_utils)

# Import functions from the module
ensure_directories_exist = prompt_library_utils.ensure_directories_exist
read_agent_file = prompt_library_utils.read_agent_file
extract_agent_metadata = prompt_library_utils.extract_agent_metadata
determine_category_and_purpose = prompt_library_utils.determine_category_and_purpose
generate_tags = prompt_library_utils.generate_tags
generate_frontmatter = prompt_library_utils.generate_frontmatter
generate_prompt_library_content = prompt_library_utils.generate_prompt_library_content
write_prompt_library_entry = prompt_library_utils.write_prompt_library_entry
update_prompt_library_index = prompt_library_utils.update_prompt_library_index
validate_frontmatter = prompt_library_utils.validate_frontmatter

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PromptLibraryAgent(BaseAgent):
    """
    Specialized agent for generating Prompt Library entries from Claude Code agents.
    
    Capabilities:
    - Analyze Claude Code agent files
    - Extract metadata, trigger phrases, workflows
    - Generate standardized Prompt Library entries
    - Update Prompt Library index automatically
    """

    def __init__(self, agent_id: str, tool_loader=None):
        """Initialize the Prompt Library Agent."""
        super().__init__(
            agent_id=agent_id,
            name="Prompt Library Generator Agent",
            permission_level=PermissionLevel.READ_EXECUTE_WRITE,
            tool_loader=tool_loader
        )

        self.project_root = Path.cwd()
        # Ensure directories exist on initialization
        ensure_directories_exist(self.project_root)

    def _define_capabilities(self) -> List[AgentCapability]:
        """Define agent capabilities following BaseAgent pattern."""
        return [
            AgentCapability(
                name="generate_prompt_library_entry",
                description="Analyzes Claude Code agent files and generates standardized Prompt Library entries with complete frontmatter metadata",
                permission_required=PermissionLevel.READ_EXECUTE_WRITE,
                tools_required=["file_system_access", "markdown_editing"],
                data_access=["claude_agents_directory", "prompt_library_directory"],
                execution_time_estimate=5.0
            )
        ]

    def _execute_action(self, action: str, parameters: Dict[str, Any],
                       user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent actions with proper error handling and logging."""

        try:
            start_time = time.time()

            if action == "generate_prompt_library_entry":
                result = self._generate_prompt_library_entry(parameters)
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

    def _generate_prompt_library_entry(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate Prompt Library entry from Claude Code agent file.
        
        Args:
            parameters: Dictionary with:
                - agent_name (required): Name of agent file without .md extension
                - standardize_existing (optional): If True, update existing entry
        
        Returns:
            Dictionary with entry details and file paths
        """
        agent_name = parameters.get("agent_name")
        if not agent_name:
            raise ValueError("agent_name parameter is required")
        
        standardize_existing = parameters.get("standardize_existing", False)
        
        # Construct agent file path
        agent_file = self.project_root / ".claude" / "agents" / f"{agent_name}.md"
        
        if not agent_file.exists():
            raise FileNotFoundError(f"Agent file not found: {agent_file}")
        
        logger.info(f"Processing agent file: {agent_file}")
        
        # Read agent file
        agent_file_data = read_agent_file(agent_file)
        content = agent_file_data["content"]
        
        # Extract metadata
        agent_data = extract_agent_metadata(content, agent_file.name)
        logger.info(f"Extracted metadata for: {agent_data['name']}")
        
        # Determine category and purpose
        category, purpose = determine_category_and_purpose(agent_data)
        logger.info(f"Category: {category}, Purpose: {purpose}")
        
        # Generate tags
        tags = generate_tags(agent_data)
        logger.info(f"Generated tags: {tags}")
        
        # Generate frontmatter
        frontmatter = generate_frontmatter(agent_data, category, purpose, tags)
        
        # Validate frontmatter
        is_valid, error_msg = validate_frontmatter(frontmatter)
        if not is_valid:
            logger.warning(f"Frontmatter validation warning: {error_msg}")
            # Continue anyway, but log the warning
        
        # Generate full content
        entry_content = generate_prompt_library_content(agent_data, frontmatter)
        
        # Determine entry title (Title Case)
        entry_title = agent_data["name"]
        
        # Check if entry already exists
        library_dir = self.project_root / "60 - Prompt Library"
        existing_entry = library_dir / f"{entry_title}.md"
        
        if existing_entry.exists() and not standardize_existing:
            logger.warning(f"Entry already exists: {existing_entry}")
            return {
                "status": "exists",
                "message": f"Entry already exists at {existing_entry}",
                "entry_path": str(existing_entry),
                "entry_title": entry_title
            }
        
        # Write entry
        entry_path = write_prompt_library_entry(entry_title, entry_content, library_dir)
        logger.info(f"Created Prompt Library entry: {entry_path}")
        
        # Update index
        index_path = library_dir / "Prompt Library.md"
        update_prompt_library_index(entry_title, entry_path, index_path)
        logger.info(f"Updated Prompt Library index")
        
        return {
            "status": "created",
            "entry_title": entry_title,
            "entry_path": str(entry_path),
            "index_path": str(index_path),
            "category": category,
            "purpose": purpose,
            "tags": tags,
            "frontmatter_valid": is_valid
        }


def create_prompt_library_agent(agent_id: str = "prompt_library_generator") -> PromptLibraryAgent:
    """Factory function to create a PromptLibraryAgent instance."""
    return PromptLibraryAgent(agent_id=agent_id)


if __name__ == "__main__":
    # Demo the agent
    agent = create_prompt_library_agent()
    
    print("=== Prompt Library Generator Agent Demo ===")
    print(f"Agent ID: {agent.agent_id}")
    print(f"Capabilities: {[cap.name for cap in agent.capabilities]}")
    
    # Test with a sample agent (if exists)
    test_agent_name = "test-agent"
    agent_file = Path(".claude/agents") / f"{test_agent_name}.md"
    
    if agent_file.exists():
        print(f"\n=== Testing with {test_agent_name} ===")
        result = agent._execute_action(
            "generate_prompt_library_entry",
            {"agent_name": test_agent_name},
            {}
        )
        print(f"Result: {result['status']}")
        if result['status'] == 'success':
            print(f"Entry created: {result['result'].get('entry_path')}")
    else:
        print(f"\nTest agent file not found: {agent_file}")
        print("Create a test agent file to run the demo")

