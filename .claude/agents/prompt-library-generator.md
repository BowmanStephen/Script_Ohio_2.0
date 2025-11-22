# Prompt Library Generator Agent

## Purpose

This agent analyzes Claude Code agents and transforms them into well-documented Prompt Library entries. It's designed to standardize agent documentation, ensure proper frontmatter metadata, and make agents discoverable and reusable.

This is particularly useful when you want to document agents for future reference, share agent patterns, or maintain a consistent Prompt Library structure.

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

- "create a prompt library entry for this agent"
- "document this agent in the prompt library"
- "make a prompt from this agent"
- "generate prompt library entry"
- "standardize prompt library entry"

## What It Does

1. **Analyzes Agent File**: Reads `.claude/agents/[name].md` to understand purpose, workflow, triggers, quality standards, and outputs

2. **Extracts Key Information**:
   - Agent name and description
   - Concrete capabilities
   - Trigger phrases and usage patterns
   - Quality standards
   - Related tools or prompts

3. **Structures Prompt Library Entry**: Creates documentation with:
   - Complete frontmatter metadata
   - Purpose section explaining what and why
   - How to Use section with steps and best practices
   - Trigger Phrases list
   - What It Does numbered workflow
   - Quality Standards
   - Usage Examples in code blocks
   - Related links

4. **Generates Proper Frontmatter**: Includes all canonical fields:
   - title, category, purpose
   - tags array
   - created date (YYYY-MM-DD)
   - use_cases array
   - sensitivity, fileClass, status
   - required_tools array
   - description, excerpt

5. **Creates File**: Writes to `60 - Prompt Library/[Title Case Name].md`

6. **Updates Index**: Adds wikilink to `60 - Prompt Library/Prompt Library.md` in alphabetical order

7. **Standardizes Existing Entries**: Can update existing entries to match canonical format

## Quality Standards

- Complete and properly formatted YAML frontmatter
- Dates in YYYY-MM-DD format
- One clear sentence descriptions
- Compelling action-oriented excerpts
- Relevant lowercase-with-hyphen tags
- Realistic usage examples
- Accurate related links
- Title Case file naming
- Alphabetical index ordering
- Clear numbered workflows
- Comprehensive but concise documentation

## Usage Examples

```
Create a prompt library entry based on the newsletter-curator agent
```

```
Document the interactive-infographics agent in the prompt library
```

```
Make a prompt library entry from agent-foo and update the index
```

```
Standardize the existing Newsletter Curator prompt to match the canonical format
```

## Implementation Instructions

When invoked, follow these steps:

1. **Read the agent file**: Use the file system to read `.claude/agents/[agent_name].md`

2. **Analyze the content**: Using Claude's understanding, extract:
   - Purpose and description from the Purpose section
   - Trigger phrases from any Trigger Phrases section
   - Workflow steps from "What It Does" sections
   - Quality standards from Quality Standards sections
   - Usage examples from code blocks
   - Related prompts from Related sections

3. **Call Python utilities**: Use the utility functions from `scripts/prompt_library_utils.py`:
   ```python
   from scripts.prompt_library_utils import (
       read_agent_file,
       extract_agent_metadata,
       determine_category_and_purpose,
       generate_tags,
       generate_frontmatter,
       generate_prompt_library_content,
       write_prompt_library_entry,
       update_prompt_library_index
   )
   ```

4. **Generate the entry**: 
   - Extract metadata using `extract_agent_metadata()`
   - Determine category and purpose using `determine_category_and_purpose()`
   - Generate tags using `generate_tags()`
   - Create frontmatter using `generate_frontmatter()`
   - Generate full content using `generate_prompt_library_content()`
   - Write the entry using `write_prompt_library_entry()`
   - Update the index using `update_prompt_library_index()`

5. **Verify the result**: Check that:
   - The entry file was created correctly
   - The frontmatter is valid YAML
   - The index was updated alphabetically
   - All required fields are present

## Frontmatter Field Guide

### category

Choose based on agent purpose:

- `code-analysis`: Analyzes codebases, extracts patterns
- `content-creation`: Creates or curates content
- `documentation`: Generates or improves docs
- `workflow-automation`: Automates processes
- `data-extraction`: Extracts and structures info
- `meta`: Tools for creating other tools

### purpose

Choose based on primary function:

- `content-extraction`: Pulls insights from sources
- `content-curation`: Organizes and selects content
- `content-generation`: Creates new content
- `analysis`: Analyzes and provides insights
- `automation`: Automates tasks/workflows
- `documentation`: Documents systems/processes

### required_tools

Common tools:

- `file_system_access`
- `directory_traversal`
- `code_reading`
- `web_search`
- `git_history_access`
- `markdown_editing`
- `note_creation`

## Notes

- **Meta-tool** for documenting other tools - enables self-documentation
- **Standardizes format** across all Prompt Library entries
- **Extracts structure** from agent files automatically
- **Ensures completeness** with canonical frontmatter fields
- **Maintains index** in alphabetical order
- **Category/purpose taxonomy** provides consistent classification

## Related

- [[Prompt Library]]
- [[Agent Documentation]]

