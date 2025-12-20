"""
Claude Code Subagent Registry

Loads and manages subagent definitions from .claude/agents/*.md files.
Integrates with Meta Agent for lifecycle management.
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from agents.core.agent_framework import PermissionLevel

logger = logging.getLogger(__name__)


@dataclass
class SubagentDefinition:
    """Subagent definition loaded from YAML frontmatter"""

    name: str
    description: str
    system_prompt: str
    tools: List[str] = field(default_factory=list)
    model: str = "claude-3-5-sonnet"
    permissions: str = "READ_EXECUTE"
    context_isolation: bool = True
    sandbox_enabled: bool = False
    file_path: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_permission_level(self) -> PermissionLevel:
        """Convert permission string to PermissionLevel enum"""
        permission_map = {
            "READ_ONLY": PermissionLevel.READ_ONLY,
            "READ_EXECUTE": PermissionLevel.READ_EXECUTE,
            "READ_EXECUTE_WRITE": PermissionLevel.READ_EXECUTE_WRITE,
            "ADMIN": PermissionLevel.ADMIN,
        }
        return permission_map.get(self.permissions, PermissionLevel.READ_EXECUTE)


class SubagentRegistry:
    """
    Registry for Claude Code subagents.

    Loads subagent definitions from .claude/agents/*.md files
    and provides access to them.
    """

    def __init__(self, agents_dir: Optional[Path] = None):
        """
        Initialize the subagent registry.

        Args:
            agents_dir: Path to .claude/agents directory. Defaults to
                       .claude/agents/ in project root.
        """
        if agents_dir is None:
            project_root = Path(__file__).parent.parent
            agents_dir = project_root / ".claude" / "agents"

        self.agents_dir = Path(agents_dir)
        self.subagents: Dict[str, SubagentDefinition] = {}
        self._load_subagents()

    def _load_subagents(self) -> None:
        """Load all subagent definitions from .claude/agents/*.md files"""
        if not self.agents_dir.exists():
            logger.warning(f"Subagent directory does not exist: {self.agents_dir}")
            return

        for md_file in self.agents_dir.glob("*.md"):
            try:
                subagent = self._load_subagent_from_file(md_file)
                if subagent:
                    self.subagents[subagent.name] = subagent
                    logger.info(f"Loaded subagent: {subagent.name}")
            except Exception as e:
                logger.error(f"Error loading subagent from {md_file}: {e}")

    def _load_subagent_from_file(self, file_path: Path) -> Optional[SubagentDefinition]:
        """
        Load a subagent definition from a Markdown file with YAML frontmatter.

        Args:
            file_path: Path to the .md file

        Returns:
            SubagentDefinition or None if parsing fails
        """
        content = file_path.read_text(encoding="utf-8")

        # Extract YAML frontmatter
        frontmatter_match = re.match(
            r"^---\s*\n(.*?)\n---\s*\n(.*)$", content, re.DOTALL
        )

        if not frontmatter_match:
            logger.warning(f"No YAML frontmatter found in {file_path}")
            return None

        frontmatter_text = frontmatter_match.group(1)
        body_text = frontmatter_match.group(2)

        try:
            frontmatter = yaml.safe_load(frontmatter_text)
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML frontmatter in {file_path}: {e}")
            return None

        # Extract required fields
        name = frontmatter.get("name", file_path.stem)
        description = frontmatter.get("description", "")
        system_prompt = frontmatter.get("system_prompt", body_text.strip())

        # Extract optional fields
        tools = frontmatter.get("tools", [])
        if isinstance(tools, str):
            tools = [t.strip() for t in tools.split(",")]

        model = frontmatter.get("model", "claude-3-5-sonnet")
        permissions = frontmatter.get("permissions", "READ_EXECUTE")
        context_isolation = frontmatter.get("context_isolation", True)
        sandbox_enabled = frontmatter.get("sandbox_enabled", False)

        # Extract any additional metadata
        metadata = {
            k: v
            for k, v in frontmatter.items()
            if k
            not in [
                "name",
                "description",
                "system_prompt",
                "tools",
                "model",
                "permissions",
                "context_isolation",
                "sandbox_enabled",
            ]
        }

        return SubagentDefinition(
            name=name,
            description=description,
            system_prompt=system_prompt,
            tools=tools,
            model=model,
            permissions=permissions,
            context_isolation=context_isolation,
            sandbox_enabled=sandbox_enabled,
            file_path=str(file_path),
            metadata=metadata,
        )

    def get_subagent(self, name: str) -> Optional[SubagentDefinition]:
        """
        Get a subagent definition by name.

        Args:
            name: Subagent name

        Returns:
            SubagentDefinition or None if not found
        """
        return self.subagents.get(name)

    def list_subagents(self) -> List[str]:
        """
        List all registered subagent names.

        Returns:
            List of subagent names
        """
        return list(self.subagents.keys())

    def reload(self) -> None:
        """Reload all subagent definitions from disk"""
        self.subagents.clear()
        self._load_subagents()

    def register_with_meta_agent(
        self, meta_agent, user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Register all subagents with the Meta Agent.

        Args:
            meta_agent: Meta Agent instance
            user_context: User context for registration

        Returns:
            Registration results
        """
        results = {}
        for name, subagent in self.subagents.items():
            try:
                result = meta_agent._register_agent(
                    {
                        "agent_id": f"claude_code_{name.lower().replace(' ', '_')}",
                        "agent_name": subagent.name,
                        "class_name": "ClaudeCodeSubagent",
                        "file_path": subagent.file_path,
                        "created_by": "claude_code_registry",
                        "capabilities": subagent.tools,
                        "dependencies": [],
                        "metadata": {
                            "type": "claude_code_subagent",
                            "model": subagent.model,
                            "permissions": subagent.permissions,
                            "context_isolation": subagent.context_isolation,
                            "sandbox_enabled": subagent.sandbox_enabled,
                            **subagent.metadata,
                        },
                    },
                    user_context,
                )
                results[name] = result
            except Exception as e:
                logger.error(f"Error registering subagent {name} with Meta Agent: {e}")
                results[name] = {"success": False, "error": str(e)}

        return results
