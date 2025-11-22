---
title: Comprehensive Test Agent
category: code-analysis
purpose: content-extraction
tags:
- prompt
- extraction
- prompt-library
created: '2025-11-20'
use_cases:
- Tests metadata extraction
sensitivity: safe
fileClass: prompt
status: published
required_tools:
- file_system_access
- markdown_editing
description: This agent tests all features of the Prompt Library Generator including
  metadata extraction, frontmatter generation, and index management.
excerpt: This agent tests all features of the Prompt Library Generator including metadata
  extraction, frontma...
---

# Comprehensive Test Agent

## Purpose

This agent tests all features of the Prompt Library Generator including metadata extraction, frontmatter generation, and index management.

## How to Use

This agent is designed to be used with Claude Code when you have agents defined in `.claude/agents/` and want to document them in your Prompt Library.

### Steps:

1. Create or identify an agent in `.claude/agents/[name].md`
2. Invoke this agent with the agent name
3. The agent will analyze the agent file and generate a complete Prompt Library entry
4. It will update the Prompt Library index automatically

### Best Practices:

- Use this agent whenever you create a new Claude Code agent
- Run it to standardize existing Prompt Library entries
- Ensure agent files have clear descriptions and workflows
- Review generated frontmatter for accuracy
- Keep the Prompt Library index updated

## Trigger Phrases

- "test comprehensive agent"

## What It Does

1. Tests metadata extraction

## Quality Standards

- Complete frontmatter

## Prompt

```
See: .claude/agents/agent.md
```

## Notes

- **Meta-tool** for documenting other tools - enables self-documentation
- **Standardizes format** across all Prompt Library entries
- **Extracts structure** from agent files automatically
- **Ensures completeness** with canonical frontmatter fields
- **Maintains index** in alphabetical order
- **Category/purpose taxonomy** provides consistent classification

