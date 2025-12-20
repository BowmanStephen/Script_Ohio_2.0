# Claude Code Integration Guide

This guide explains how to use Claude Code's Plan-then-Execute (P-t-E) architecture
in Script Ohio 2.0.

## Overview

The Claude Code integration enables autonomous project development through:
- **Plan-then-Execute Pattern**: Separates strategic planning from tactical implementation
- **Subagent System**: Specialized agents defined in `.claude/agents/*.md` files
- **Context Isolation**: Fresh context windows per subagent
- **Sandboxing**: OS-level isolation for security
- **Sequential Handoffs**: Assembly-line patterns for agent workflows

## Quick Start

### List Available Subagents

```bash
python3 scripts/claude_code_agents.py list
```

### Invoke a Subagent

```bash
python3 scripts/claude_code_agents.py invoke --name "Senior Engineer" --task "Implement feature X"
```

### Create a New Subagent

```bash
python3 scripts/claude_code_agents.py create --name "My Agent" --template default
```

## Architecture

### Plan-then-Execute Orchestrator

The orchestrator separates planning from execution:

1. **Planning Phase**: Analyzes objectives and creates execution plans
2. **Execution Phase**: Delegates tasks to specialized subagents

```python
from agents.claude_code_orchestrator import PlanThenExecuteOrchestrator

orchestrator = PlanThenExecuteOrchestrator()

# Generate plan
plan = orchestrator.plan_phase("Add feature X")

# Execute plan
result = orchestrator.execute_phase(plan)
```

### Subagent Definitions

Subagents are defined in `.claude/agents/*.md` files with YAML frontmatter:

```yaml
---
name: Senior Engineer
description: Senior software engineer focused on clean, maintainable code
system_prompt: |
  You are a senior software engineer with expertise in Python.
  Your role is to write clean, maintainable code.
tools:
  - file_operations
  - code_editing
  - git_operations
model: claude-3-5-sonnet
permissions: READ_EXECUTE_WRITE
context_isolation: true
sandbox_enabled: true
---

# Senior Engineer Subagent

## Purpose

Implementation specialist for code development.

## Capabilities

- Code implementation
- Test writing
- Code review
```

### Context Isolation

Each subagent operates in an isolated context window:

```python
from agents.core.context_isolation import ContextIsolationManager

manager = ContextIsolationManager()

# Create isolated context
context = manager.create_isolated_context("engineer", {"task": "implement"})

# Handoff context between agents
new_context = manager.handoff_context("pm", "engineer", {"result": "specs"})
```

### Sandboxing

OS-level sandboxing provides filesystem and network isolation:

```python
from agents.core.sandbox_manager import SandboxManager

manager = SandboxManager()

if manager.is_available():
    sandbox = manager.create_sandbox(
        "engineer",
        allowed_tools=["read", "edit"],
        network_enabled=False
    )
```

### Sequential Handoffs

Assembly-line patterns for agent workflows:

```python
from agents.core.handoff_manager import HandoffManager

manager = HandoffManager()

# Create handoff chain
chain = manager.create_handoff_chain(["pm", "engineer", "reviewer"])

# Execute chain
results = manager.execute_chain(chain, initial_input={"task": "feature"})
```

## Available Subagents

- **Planner**: Strategic planning and task breakdown
- **Executor**: Tactical code implementation
- **Product Manager**: Business logic and requirements
- **Senior Engineer**: Code implementation
- **QA Engineer**: Testing and validation
- **Security Auditor**: Security audits
- **Data Scientist**: Analytics and modeling

## Best Practices

1. **Use Planning Phase**: Always plan before executing complex tasks
2. **Isolate Contexts**: Each subagent should have a fresh context
3. **Validate Handoffs**: Use validation gates for sequential workflows
4. **Enable Sandboxing**: Use OS-level sandboxing when available
5. **Monitor Execution**: Track metrics and handle failures gracefully

## Integration with Existing Agents

The Claude Code orchestrator integrates with the existing agent system:

- Uses `SubagentRegistry` to load subagent definitions
- Integrates with `MetaAgent` for lifecycle management
- Uses `WorkflowAutomator` for execution coordination
- Leverages `ContextManager` for context optimization

## Troubleshooting

**Subagent not found**: Check `.claude/agents/` directory and file format

**Sandboxing unavailable**: Falls back to permission-based isolation

**Context isolation issues**: Check `ContextIsolationManager` logs

**Handoff failures**: Review validation gates and retry configuration

## References

- Plan-then-Execute Orchestrator: `agents/claude_code_orchestrator.py`
- Subagent Registry: `agents/claude_code_subagent_registry.py`
- Context Isolation: `agents/core/context_isolation.py`
- Sandbox Manager: `agents/core/sandbox_manager.py`
- Handoff Manager: `agents/core/handoff_manager.py`
