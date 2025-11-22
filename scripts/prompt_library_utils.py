#!/usr/bin/env python3
"""
Prompt Library Utilities - Shared functions for generating Prompt Library entries

This module provides core utilities for analyzing Claude Code agent files
and generating standardized Prompt Library entries with proper frontmatter.
"""

import re
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    logging.warning("PyYAML not available. YAML frontmatter generation will use basic formatting.")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def ensure_directories_exist(project_root: Path) -> None:
    """
    Create required directories if they don't exist.
    
    Args:
        project_root: Root path of the project
    """
    claude_agents_dir = project_root / ".claude" / "agents"
    prompt_library_dir = project_root / "60 - Prompt Library"
    index_file = prompt_library_dir / "Prompt Library.md"
    
    # Create .claude/agents if missing
    claude_agents_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured directory exists: {claude_agents_dir}")
    
    # Create 60 - Prompt Library if missing
    prompt_library_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured directory exists: {prompt_library_dir}")
    
    # Create index file if missing
    if not index_file.exists():
        index_file.write_text("# Prompt Library\n\n", encoding="utf-8")
        logger.info(f"Created index file: {index_file}")


def read_agent_file(agent_path: Path) -> Dict[str, Any]:
    """
    Read and parse agent markdown file.
    
    Args:
        agent_path: Path to the agent markdown file
        
    Returns:
        Dictionary with content and metadata
    """
    if not agent_path.exists():
        raise FileNotFoundError(f"Agent file not found: {agent_path}")
    
    try:
        content = agent_path.read_text(encoding="utf-8")
        
        return {
            "content": content,
            "filename": agent_path.name,
            "filepath": str(agent_path),
            "size": len(content)
        }
    except Exception as e:
        raise IOError(f"Failed to read agent file {agent_path}: {e}")


def extract_agent_metadata(content: str, filename: str) -> Dict[str, Any]:
    """
    Extract metadata from agent file content.
    
    Args:
        content: Full content of the agent file
        filename: Name of the agent file
        
    Returns:
        Dictionary with extracted metadata
    """
    metadata = {
        "name": filename.replace(".md", "").replace("-", " ").title(),
        "description": "",
        "purpose": "",
        "trigger_phrases": [],
        "workflow_steps": [],
        "quality_standards": [],
        "related_prompts": [],
        "usage_examples": [],
        "capabilities": []
    }
    
    # Extract title/name from first heading
    title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    if title_match:
        metadata["name"] = title_match.group(1).strip()
    
    # Extract description from Purpose section
    purpose_match = re.search(r'(?:^##\s+Purpose|^#\s+Purpose)\s*\n\n(.+?)(?=\n##|\n#|$)', content, re.MULTILINE | re.DOTALL)
    if purpose_match:
        purpose_text = purpose_match.group(1).strip()
        metadata["purpose"] = purpose_text
        # First sentence is usually the description
        sentences = re.split(r'[.!?]\s+', purpose_text)
        if sentences:
            metadata["description"] = sentences[0].strip() + ("." if not sentences[0].endswith(".") else "")
    
    # Extract trigger phrases
    trigger_section = re.search(r'(?:^##\s+Trigger Phrases|^###\s+Trigger Phrases)\s*\n\n(.+?)(?=\n##|\n#|$)', content, re.MULTILINE | re.DOTALL)
    if trigger_section:
        trigger_text = trigger_section.group(1)
        # Extract quoted phrases or list items
        trigger_phrases = re.findall(r'["\']([^"\']+)["\']|^[-*]\s+(.+)$', trigger_text, re.MULTILINE)
        metadata["trigger_phrases"] = [p[0] or p[1] for p in trigger_phrases if p[0] or p[1]]
    
    # Extract workflow steps from "What It Does" section
    what_it_does = re.search(r'(?:^##\s+What It Does|^###\s+What It Does)\s*\n\n(.+?)(?=\n##|\n#|$)', content, re.MULTILINE | re.DOTALL)
    if what_it_does:
        steps_text = what_it_does.group(1)
        # Extract numbered or bulleted items
        steps = re.findall(r'^\d+\.\s+(.+)$|^[-*]\s+(.+)$', steps_text, re.MULTILINE)
        metadata["workflow_steps"] = [s[0] or s[1] for s in steps if s[0] or s[1]]
    
    # Extract quality standards
    quality_section = re.search(r'(?:^##\s+Quality Standards|^###\s+Quality Standards)\s*\n\n(.+?)(?=\n##|\n#|$)', content, re.MULTILINE | re.DOTALL)
    if quality_section:
        quality_text = quality_section.group(1)
        standards = re.findall(r'^\d+\.\s+(.+)$|^[-*]\s+(.+)$|^[-*]\s+(.+)$', quality_text, re.MULTILINE)
        metadata["quality_standards"] = [s[0] or s[1] or s[2] for s in standards if any(s)]
    
    # Extract usage examples
    examples_section = re.search(r'(?:^##\s+Usage Examples|^###\s+Usage Examples)\s*\n\n(.+?)(?=\n##|\n#|$)', content, re.MULTILINE | re.DOTALL)
    if examples_section:
        examples_text = examples_section.group(1)
        # Extract code blocks
        code_blocks = re.findall(r'```[\w]*\n(.*?)```', examples_text, re.DOTALL)
        metadata["usage_examples"] = code_blocks
    
    # Extract related prompts
    related_section = re.search(r'(?:^##\s+Related|^###\s+Related)\s*\n\n(.+?)(?=\n##|\n#|$)', content, re.MULTILINE | re.DOTALL)
    if related_section:
        related_text = related_section.group(1)
        links = re.findall(r'\[([^\]]+)\]\(([^\)]+)\)|\[\[([^\]]+)\]\]', related_text)
        metadata["related_prompts"] = [link[0] or link[2] for link in links]
    
    # If no description found, use first paragraph
    if not metadata["description"]:
        first_para = re.search(r'^([A-Z][^.!?]+[.!?])', content, re.MULTILINE)
        if first_para:
            metadata["description"] = first_para.group(1).strip()
    
    return metadata


def determine_category_and_purpose(agent_data: Dict) -> Tuple[str, str]:
    """
    Determine category and purpose based on agent metadata.
    
    Args:
        agent_data: Extracted agent metadata
        
    Returns:
        Tuple of (category, purpose)
    """
    description = (agent_data.get("description", "") + " " + agent_data.get("purpose", "")).lower()
    name = agent_data.get("name", "").lower()
    
    # Category mapping
    if any(word in description or word in name for word in ["code", "analyze", "pattern", "extract"]):
        category = "code-analysis"
    elif any(word in description or word in name for word in ["content", "create", "generate", "write"]):
        category = "content-creation"
    elif any(word in description or word in name for word in ["document", "doc", "guide", "tutorial"]):
        category = "documentation"
    elif any(word in description or word in name for word in ["workflow", "automate", "process", "pipeline"]):
        category = "workflow-automation"
    elif any(word in description or word in name for word in ["extract", "data", "structure", "parse"]):
        category = "data-extraction"
    elif any(word in description or word in name for word in ["meta", "tool", "agent", "prompt"]):
        category = "meta"
    else:
        category = "meta"  # Default for documentation tools
    
    # Purpose mapping
    if any(word in description or word in name for word in ["extract", "pull", "get", "retrieve"]):
        purpose = "content-extraction"
    elif any(word in description or word in name for word in ["curate", "organize", "select", "filter"]):
        purpose = "content-curation"
    elif any(word in description or word in name for word in ["generate", "create", "write", "produce"]):
        purpose = "content-generation"
    elif any(word in description or word in name for word in ["analyze", "insight", "statistic", "trend"]):
        purpose = "analysis"
    elif any(word in description or word in name for word in ["automate", "workflow", "process"]):
        purpose = "automation"
    elif any(word in description or word in name for word in ["document", "guide", "tutorial"]):
        purpose = "documentation"
    else:
        purpose = "documentation"  # Default
    
    return category, purpose


def generate_tags(agent_data: Dict) -> List[str]:
    """
    Generate relevant tags from agent metadata.
    
    Args:
        agent_data: Extracted agent metadata
        
    Returns:
        List of lowercase-with-hyphens tags
    """
    tags = []
    description = (agent_data.get("description", "") + " " + agent_data.get("purpose", "")).lower()
    name = agent_data.get("name", "").lower()
    
    # Technology/domain tags
    tech_keywords = {
        "ai": ["ai", "artificial intelligence", "llm", "claude"],
        "code": ["code", "programming", "development", "software"],
        "documentation": ["documentation", "docs", "guide", "tutorial"],
        "prompt": ["prompt", "agent", "instruction"],
        "workflow": ["workflow", "automation", "process"],
        "analysis": ["analysis", "analytics", "insight"]
    }
    
    for tag, keywords in tech_keywords.items():
        if any(keyword in description or keyword in name for keyword in keywords):
            tags.append(tag)
    
    # Action tags
    if "generate" in description or "generate" in name:
        tags.append("generation")
    if "extract" in description or "extract" in name:
        tags.append("extraction")
    if "analyze" in description or "analyze" in name:
        tags.append("analysis")
    if "curate" in description or "curate" in name:
        tags.append("curation")
    
    # Output tags
    if "prompt" in description or "prompt" in name:
        tags.append("prompt-library")
    if "documentation" in description or "documentation" in name:
        tags.append("documentation")
    
    # Remove duplicates and ensure lowercase-with-hyphens
    tags = list(dict.fromkeys(tags))  # Preserve order, remove duplicates
    tags = [tag.lower().replace(" ", "-") for tag in tags]
    
    # Ensure at least one tag
    if not tags:
        tags.append("meta")
    
    return tags


def generate_frontmatter(agent_data: Dict, category: str, purpose: str, tags: List[str]) -> str:
    """
    Generate complete YAML frontmatter.
    
    Args:
        agent_data: Extracted agent metadata
        category: Category for the entry
        purpose: Purpose for the entry
        tags: List of tags
        
    Returns:
        YAML frontmatter string
    """
    title = agent_data.get("name", "Untitled Agent")
    description = agent_data.get("description", "Agent for automated tasks")
    excerpt = description[:100] + "..." if len(description) > 100 else description
    
    # Generate use cases from workflow steps
    use_cases = []
    workflow_steps = agent_data.get("workflow_steps", [])
    if workflow_steps:
        # Use first 3-5 workflow steps as use cases
        for step in workflow_steps[:5]:
            # Clean up step text
            step_clean = re.sub(r'^\d+\.\s*', '', step).strip()
            if step_clean and len(step_clean) < 100:
                use_cases.append(step_clean)
    
    # If no use cases from workflow, generate from description
    if not use_cases:
        use_cases = [
            f"Document {title.lower()} agent",
            f"Standardize {title.lower()} documentation",
            f"Create Prompt Library entry for {title.lower()}"
        ]
    
    # Determine required tools
    required_tools = ["file_system_access", "markdown_editing"]
    if "code" in description.lower() or "code" in title.lower():
        required_tools.append("code_reading")
    if "web" in description.lower():
        required_tools.append("web_search")
    
    frontmatter_dict = {
        "title": title,
        "category": category,
        "purpose": purpose,
        "tags": tags,
        "created": datetime.now().strftime("%Y-%m-%d"),
        "use_cases": use_cases[:5],  # Limit to 5
        "sensitivity": "safe",
        "fileClass": "prompt",
        "status": "published",
        "required_tools": required_tools,
        "description": description,
        "excerpt": excerpt
    }
    
    # Convert to YAML string
    if YAML_AVAILABLE:
        try:
            yaml_str = yaml.dump(frontmatter_dict, default_flow_style=False, sort_keys=False, allow_unicode=True)
            return f"---\n{yaml_str}---\n"
        except Exception as e:
            logger.error(f"Failed to generate YAML frontmatter: {e}")
    
    # Fallback to basic frontmatter (if PyYAML not available or error)
    tags_str = ", ".join([f'"{tag}"' for tag in tags])
    use_cases_str = "\n  - ".join([""] + [f'"{uc}"' for uc in use_cases[:5]])
    tools_str = ", ".join([f'"{tool}"' for tool in required_tools])
    
    return f"""---
title: "{title}"
category: {category}
purpose: {purpose}
tags:
  - {tags_str.replace(', "', '\n  - "')}
created: {datetime.now().strftime("%Y-%m-%d")}
use_cases:{use_cases_str}
sensitivity: safe
fileClass: prompt
status: published
required_tools:
  - {tools_str.replace(', "', '\n  - "')}
description: "{description}"
excerpt: "{excerpt}"
---
"""


def generate_prompt_library_content(agent_data: Dict, frontmatter: str) -> str:
    """
    Generate full Prompt Library entry markdown content.
    
    Args:
        agent_data: Extracted agent metadata
        frontmatter: YAML frontmatter string
        
    Returns:
        Complete markdown content for the entry
    """
    title = agent_data.get("name", "Untitled Agent")
    purpose = agent_data.get("purpose", agent_data.get("description", ""))
    trigger_phrases = agent_data.get("trigger_phrases", [])
    workflow_steps = agent_data.get("workflow_steps", [])
    quality_standards = agent_data.get("quality_standards", [])
    usage_examples = agent_data.get("usage_examples", [])
    related_prompts = agent_data.get("related_prompts", [])
    
    content = frontmatter + "\n"
    content += f"# {title}\n\n"
    
    # Purpose section
    content += "## Purpose\n\n"
    if purpose:
        content += f"{purpose}\n\n"
    else:
        content += f"This agent {agent_data.get('description', 'provides automated functionality')}.\n\n"
    
    # How to Use section
    content += "## How to Use\n\n"
    content += "This agent is designed to be used with Claude Code when you have agents defined in `.claude/agents/` and want to document them in your Prompt Library.\n\n"
    content += "### Steps:\n\n"
    content += "1. Create or identify an agent in `.claude/agents/[name].md`\n"
    content += "2. Invoke this agent with the agent name\n"
    content += "3. The agent will analyze the agent file and generate a complete Prompt Library entry\n"
    content += "4. It will update the Prompt Library index automatically\n\n"
    content += "### Best Practices:\n\n"
    content += "- Use this agent whenever you create a new Claude Code agent\n"
    content += "- Run it to standardize existing Prompt Library entries\n"
    content += "- Ensure agent files have clear descriptions and workflows\n"
    content += "- Review generated frontmatter for accuracy\n"
    content += "- Keep the Prompt Library index updated\n\n"
    
    # Trigger Phrases section
    if trigger_phrases:
        content += "## Trigger Phrases\n\n"
        for phrase in trigger_phrases:
            # Clean up phrase and use single quotes
            phrase_clean = phrase.strip().strip('"').strip("'")
            content += f'- "{phrase_clean}"\n'
        content += "\n"
    
    # What It Does section
    if workflow_steps:
        content += "## What It Does\n\n"
        for i, step in enumerate(workflow_steps, 1):
            # Clean up step text
            step_clean = re.sub(r'^\d+\.\s*', '', step).strip()
            content += f"{i}. {step_clean}\n"
        content += "\n"
    
    # Quality Standards section
    if quality_standards:
        content += "## Quality Standards\n\n"
        for standard in quality_standards:
            standard_clean = re.sub(r'^\d+\.\s*|^[-*]\s*', '', standard).strip()
            content += f"- {standard_clean}\n"
        content += "\n"
    
    # Usage Examples section
    if usage_examples:
        content += "## Usage Examples\n\n"
        for example in usage_examples[:3]:  # Limit to 3 examples
            content += f"```\n{example.strip()}\n```\n\n"
    
    # Prompt section (include original agent content)
    content += "## Prompt\n\n"
    content += "```\n"
    # Include a reference to the original agent file
    filename = agent_data.get('filename', 'agent.md')
    content += f"See: .claude/agents/{filename}\n"
    content += "```\n\n"
    
    # Notes section
    content += "## Notes\n\n"
    content += f"- **Meta-tool** for documenting other tools - enables self-documentation\n"
    content += f"- **Standardizes format** across all Prompt Library entries\n"
    content += f"- **Extracts structure** from agent files automatically\n"
    content += f"- **Ensures completeness** with canonical frontmatter fields\n"
    content += f"- **Maintains index** in alphabetical order\n"
    content += f"- **Category/purpose taxonomy** provides consistent classification\n\n"
    
    # Related section
    if related_prompts:
        content += "## Related\n\n"
        for related in related_prompts:
            content += f"- [[{related}]]\n"
        content += "\n"
    
    return content


def write_prompt_library_entry(title: str, content: str, library_path: Path) -> Path:
    """
    Write Prompt Library entry to file.
    
    Args:
        title: Title of the entry (used for filename)
        content: Full markdown content
        library_path: Path to Prompt Library directory
        
    Returns:
        Path to the created file
    """
    # Convert title to filename: Title Case -> Title Case.md
    filename = f"{title}.md"
    file_path = library_path / filename
    
    # Ensure directory exists
    library_path.mkdir(parents=True, exist_ok=True)
    
    # Write content
    file_path.write_text(content, encoding="utf-8")
    logger.info(f"Written Prompt Library entry: {file_path}")
    
    return file_path


def read_prompt_library_index(index_path: Path) -> List[str]:
    """
    Read existing index entries from Prompt Library index.
    
    Args:
        index_path: Path to index file
        
    Returns:
        List of entry titles (from wikilinks)
    """
    if not index_path.exists():
        return []
    
    try:
        content = index_path.read_text(encoding="utf-8")
        # Extract wikilinks: [[Entry Title]]
        entries = re.findall(r'\[\[([^\]]+)\]\]', content)
        return entries
    except Exception as e:
        logger.error(f"Failed to read index file: {e}")
        return []


def update_prompt_library_index(entry_title: str, entry_path: Path, index_path: Path) -> None:
    """
    Update Prompt Library index with new entry (alphabetically).
    
    Args:
        entry_title: Title of the new entry
        entry_path: Path to the entry file
        index_path: Path to index file
    """
    # Read existing entries
    existing_entries = read_prompt_library_index(index_path)
    
    # Add new entry if not already present
    if entry_title not in existing_entries:
        existing_entries.append(entry_title)
    
    # Sort alphabetically (case-insensitive)
    existing_entries.sort(key=str.lower)
    
    # Read existing index content to preserve structure
    if index_path.exists():
        index_content = index_path.read_text(encoding="utf-8")
    else:
        index_content = "# Prompt Library\n\n"
    
    # Rebuild index with sorted entries
    # Find where entries are listed (after first heading)
    lines = index_content.split("\n")
    header_lines = []
    entry_lines = []
    in_entry_section = False
    
    for line in lines:
        if line.startswith("#") and not in_entry_section:
            header_lines.append(line)
            in_entry_section = True
        elif in_entry_section and line.strip():
            # Skip old entries (we'll regenerate)
            if not line.strip().startswith("[["):
                entry_lines.append(line)
        else:
            header_lines.append(line)
    
    # Build new index content
    new_content = "\n".join(header_lines)
    if not new_content.endswith("\n"):
        new_content += "\n"
    
    # Add sorted entries
    for entry in existing_entries:
        new_content += f"[[{entry}]]\n"
    
    # Write updated index
    index_path.write_text(new_content, encoding="utf-8")
    logger.info(f"Updated Prompt Library index with {len(existing_entries)} entries")


def validate_frontmatter(frontmatter: str) -> Tuple[bool, Optional[str]]:
    """
    Validate YAML frontmatter structure.
    
    Args:
        frontmatter: YAML frontmatter string
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        # Remove --- markers
        yaml_content = re.sub(r'^---\s*\n?', '', frontmatter, flags=re.MULTILINE)
        yaml_content = re.sub(r'\n?---\s*$', '', yaml_content, flags=re.MULTILINE)
        
        # Parse YAML if available, otherwise do basic validation
        if YAML_AVAILABLE:
            try:
                data = yaml.safe_load(yaml_content)
                
                if not isinstance(data, dict):
                    return False, "Frontmatter must be a YAML dictionary"
                
                # Check required fields
                required_fields = ["title", "category", "purpose", "tags", "created", "description"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    return False, f"Missing required fields: {', '.join(missing_fields)}"
                
                # Validate date format
                if "created" in data:
                    try:
                        datetime.strptime(data["created"], "%Y-%m-%d")
                    except ValueError:
                        return False, "Date must be in YYYY-MM-DD format"
                
                return True, None
            except yaml.YAMLError as e:
                return False, f"Invalid YAML syntax: {str(e)}"
        else:
            # Basic validation without PyYAML - check for required fields as strings
            required_fields = ["title", "category", "purpose", "tags", "created", "description"]
            missing_fields = [field for field in required_fields if f"{field}:" not in yaml_content]
            
            if missing_fields:
                return False, f"Missing required fields: {', '.join(missing_fields)}"
            
            # Check date format
            date_match = re.search(r'created:\s*(\d{4}-\d{2}-\d{2})', yaml_content)
            if date_match:
                try:
                    datetime.strptime(date_match.group(1), "%Y-%m-%d")
                except ValueError:
                    return False, "Date must be in YYYY-MM-DD format"
            else:
                return False, "Missing or invalid date field"
            
            return True, None
        
    except Exception as e:
        return False, f"Validation error: {str(e)}"

