#!/usr/bin/env python3
"""
Claude Code Agents CLI

CLI interface matching Claude Code /agents command for subagent management.
"""

import argparse
import json
import sys
from pathlib import Path

from agents.claude_code_orchestrator import PlanThenExecuteOrchestrator
from agents.claude_code_subagent_registry import SubagentRegistry


def list_subagents(args):
    """List all available subagents"""
    registry = SubagentRegistry()
    subagents = registry.list_subagents()

    if not subagents:
        print("No subagents found")
        return 1

    print(f"Available subagents ({len(subagents)}):\n")
    for name in sorted(subagents):
        subagent = registry.get_subagent(name)
        if subagent:
            print(f"  {name}")
            print(f"    Description: {subagent.description}")
            print(
                f"    Tools: {', '.join(subagent.tools) if subagent.tools else 'None'}"
            )
            print(f"    Permissions: {subagent.permissions}")
            print(f"    Model: {subagent.model}")
            print()

    return 0


def create_subagent(args):
    """Create a new subagent"""
    registry = SubagentRegistry()
    agents_dir = Path(registry.agents_dir)

    name = args.name
    template = args.template or "default"

    # Check if subagent already exists
    existing = registry.get_subagent(name)
    if existing:
        print(f"Error: Subagent '{name}' already exists")
        return 1

    # Create subagent file
    filename = name.lower().replace(" ", "-") + ".md"
    filepath = agents_dir / filename

    # Template content
    templates = {
        "default": f"""---
name: {name}
description: {args.description or f"Subagent for {name}"}
system_prompt: |
  You are a specialized agent for {name}.
  Your role is to handle tasks related to {name}.
tools:
  - file_operations
model: claude-3-5-sonnet
permissions: READ_EXECUTE
context_isolation: true
sandbox_enabled: false
---

# {name} Subagent

## Purpose

{args.description or f"Subagent for {name}"}

## Capabilities

- Task handling
- Specialized operations

## Usage

Invoke this subagent for tasks related to {name}.
""",
        "security": f"""---
name: {name}
description: Security specialist for security audits and vulnerability detection
system_prompt: |
  You are a Security Auditor specializing in application security.
  Your role is to review code for security vulnerabilities.
tools:
  - file_operations
  - code_analysis
  - security_scanning
model: claude-3-5-sonnet
permissions: READ_EXECUTE
context_isolation: true
sandbox_enabled: false
---

# {name} Subagent

## Purpose

Security specialist for security audits and vulnerability detection.

## Capabilities

- Security code review
- Vulnerability detection
- Security best practices validation

## Usage

Invoke this subagent for security-related tasks.
""",
    }

    content = templates.get(template, templates["default"])

    filepath.write_text(content, encoding="utf-8")
    print(f"Created subagent: {name}")
    print(f"File: {filepath}")

    # Reload registry
    registry.reload()

    return 0


def invoke_subagent(args):
    """Invoke a subagent with a task"""
    registry = SubagentRegistry()
    orchestrator = PlanThenExecuteOrchestrator()

    name = args.name
    task = args.task

    # Get subagent
    subagent = registry.get_subagent(name)
    if not subagent:
        print(f"Error: Subagent '{name}' not found")
        print(f"Available subagents: {', '.join(registry.list_subagents())}")
        return 1

    print(f"Invoking subagent: {name}")
    print(f"Task: {task}\n")

    # Use orchestrator to plan and execute
    try:
        result = orchestrator._plan_and_execute(
            {"objective": task, "subagent": name}, {}
        )

        if result.get("success"):
            print("✅ Task completed successfully")
            if "execution" in result:
                exec_result = result["execution"]
                print(f"Tasks completed: {exec_result.get('tasks_completed', 0)}")
                print(f"Tasks failed: {exec_result.get('tasks_failed', 0)}")
        else:
            print("❌ Task failed")
            if "error" in result:
                print(f"Error: {result['error']}")

        return 0 if result.get("success") else 1

    except Exception as e:
        print(f"Error: {e}")
        return 1


def delete_subagent(args):
    """Delete a subagent"""
    registry = SubagentRegistry()
    agents_dir = Path(registry.agents_dir)

    name = args.name

    # Get subagent
    subagent = registry.get_subagent(name)
    if not subagent:
        print(f"Error: Subagent '{name}' not found")
        return 1

    # Delete file
    filepath = Path(subagent.file_path)
    if filepath.exists():
        filepath.unlink()
        print(f"Deleted subagent: {name}")
        print(f"File removed: {filepath}")

        # Reload registry
        registry.reload()
    else:
        print(f"Warning: File not found: {filepath}")

    return 0


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Claude Code Agents CLI - Manage subagents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # List command
    list_parser = subparsers.add_parser("list", help="List all available subagents")
    list_parser.set_defaults(func=list_subagents)

    # Create command
    create_parser = subparsers.add_parser("create", help="Create a new subagent")
    create_parser.add_argument("--name", required=True, help="Subagent name")
    create_parser.add_argument("--template", help="Template to use (default, security)")
    create_parser.add_argument("--description", help="Subagent description")
    create_parser.set_defaults(func=create_subagent)

    # Invoke command
    invoke_parser = subparsers.add_parser("invoke", help="Invoke a subagent")
    invoke_parser.add_argument("--name", required=True, help="Subagent name")
    invoke_parser.add_argument("--task", required=True, help="Task to execute")
    invoke_parser.set_defaults(func=invoke_subagent)

    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete a subagent")
    delete_parser.add_argument("--name", required=True, help="Subagent name")
    delete_parser.set_defaults(func=delete_subagent)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
