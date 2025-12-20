#!/usr/bin/env python3
"""
Validate Subagent Definitions

Validates that all subagent definitions in .claude/agents/*.md have proper
YAML frontmatter and required fields.
"""

import sys
from pathlib import Path

from agents.claude_code_subagent_registry import SubagentRegistry


def validate_subagent_definitions() -> bool:
    """Validate all subagent definitions"""
    registry = SubagentRegistry()
    errors = []

    if not registry.subagents:
        print("⚠️  No subagents found")
        return False

    print(f"Found {len(registry.subagents)} subagents\n")

    for name, subagent in registry.subagents.items():
        print(f"Validating: {name}")

        # Check required fields
        if not subagent.name:
            errors.append(f"{name}: Missing 'name' field")
        if not subagent.description:
            errors.append(f"{name}: Missing 'description' field")
        if not subagent.system_prompt:
            errors.append(f"{name}: Missing 'system_prompt' field")

        # Check permission level
        try:
            perm_level = subagent.get_permission_level()
            print(f"  ✓ Permissions: {subagent.permissions} ({perm_level.name})")
        except Exception as e:
            errors.append(f"{name}: Invalid permission level: {e}")

        # Check tools
        print(f"  ✓ Tools: {len(subagent.tools)} tools")
        print(f"  ✓ Model: {subagent.model}")
        print(f"  ✓ Context isolation: {subagent.context_isolation}")
        print(f"  ✓ Sandbox enabled: {subagent.sandbox_enabled}")
        print()

    if errors:
        print("❌ Validation errors:")
        for error in errors:
            print(f"  - {error}")
        return False

    print("✅ All subagent definitions are valid")
    return True


if __name__ == "__main__":
    success = validate_subagent_definitions()
    sys.exit(0 if success else 1)
