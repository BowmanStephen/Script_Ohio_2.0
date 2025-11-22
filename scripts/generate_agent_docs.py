import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any
import argparse

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

from agent_doc_utils import AgentScanner, get_agent_type_mapping, AgentMetadata, ExampleExtractor, EXCLUDED_AGENTS
from validate_agent_docs import DocValidator

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).parent.parent
DOCS_DIR = ROOT_DIR / "docs" / "agents"
AGENTS_MD_PATH = ROOT_DIR / "AGENTS.md"
ORCHESTRATOR_PATH = ROOT_DIR / "agents" / "analytics_orchestrator.py"

def setup_dirs():
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

def update_agents_md(agent_metadata: Dict[str, AgentMetadata]):
    """Update the Agent Cheat Sheet section in AGENTS.md"""
    if not AGENTS_MD_PATH.exists():
        logger.error(f"AGENTS.md not found at {AGENTS_MD_PATH}")
        return

    logger.info("Updating AGENTS.md cheat sheet...")
    
    # Sort agents by name
    sorted_agents = sorted(agent_metadata.values(), key=lambda x: x.name)
    
    # Generate table rows with improved descriptions
    table_rows: list[str] = []
    for agent in sorted_agents:
        capabilities_list = ", ".join([f"`{cap['name']}`" for cap in agent.capabilities])
        agent_type_str = f"(`{agent.agent_type}`)" if agent.agent_type else ""
        
        # Extract full first sentence for "When to Use" column
        description = agent.description or ""
        # Find first sentence (ends with . ! or ?)
        first_sentence = description.split('.')[0] + '.' if '.' in description else description.split('!')[0] + '!' if '!' in description else description.split('?')[0] + '?' if '?' in description else description
        # If first sentence is too short, take first 100 chars
        if len(first_sentence) < 20 and len(description) > len(first_sentence):
            first_sentence = description[:100].rstrip()
            if len(description) > 100:
                first_sentence += "..."
        
        row = f"| {agent.name} {agent_type_str} | {first_sentence} | {capabilities_list} | {agent.permission_level} |"
        table_rows.append(row)
    
    # Read existing content
    with open(AGENTS_MD_PATH, "r") as f:
        lines = f.readlines()
    
    # Find ALL "Agent Cheat Sheet" sections and remove them
    sections_to_remove = []
    i = 0
    while i < len(lines):
        if "## Agent Cheat Sheet" in lines[i]:
            section_start = i
            # Find the end of this section (next ## header or end of file)
            section_end = len(lines)
            for j in range(i + 1, len(lines)):
                if lines[j].startswith("##"):
                    section_end = j
                    break
            sections_to_remove.append((section_start, section_end))
            i = section_end
        else:
            i += 1
    
    # Remove all duplicate sections (in reverse order to maintain indices)
    new_lines = lines[:]
    for section_start, section_end in reversed(sections_to_remove):
        new_lines = new_lines[:section_start] + new_lines[section_end:]
    
    # Find insertion point (after "Agent system quick reference" or at end)
    insertion_idx = len(new_lines)
    for i, line in enumerate(new_lines):
        if "## Agent system quick reference" in line:
            # Find the end of this section
            for j in range(i + 1, len(new_lines)):
                if new_lines[j].startswith("##"):
                    insertion_idx = j
                    break
            if insertion_idx == len(new_lines):
                # No next section, insert after a blank line
                for j in range(i + 1, len(new_lines)):
                    if not new_lines[j].strip():
                        insertion_idx = j + 1
                        break
            break
    
    # Generate new cheat sheet section
    table_content = [
        "## Agent Cheat Sheet\n",
        "| Agent | When to Use | Key Actions | Permission |\n",
        "| --- | --- | --- | --- |\n"
    ]
    table_content.extend([row + "\n" for row in table_rows])
    table_content.append("\n")
    
    # Insert new section
    final_lines = new_lines[:insertion_idx] + table_content + new_lines[insertion_idx:]
    
    with open(AGENTS_MD_PATH, "w") as f:
        f.writelines(final_lines)
    logger.info(f"AGENTS.md updated. Removed {len(sections_to_remove)} duplicate section(s).")

def generate_agent_docs(agent_metadata: Dict[str, AgentMetadata]):
    """Generate individual documentation files for each agent"""
    logger.info("Generating individual agent documentation...")
    
    extractor = ExampleExtractor(str(ROOT_DIR))
    
    for agent in agent_metadata.values():
        if not agent.agent_type:
            continue
            
        filename = f"{agent.agent_type}.md"
        filepath = DOCS_DIR / filename
        
        content = f"# {agent.name}\n\n"
        content += f"**Type**: `{agent.agent_type}`\n"
        content += f"**Permission Level**: `{agent.permission_level}`\n"
        content += f"**Source**: [`{agent.file_path}`](../../{agent.file_path})\n\n"
        
        content += "## Description\n\n"
        content += f"{agent.description}\n\n"
        
        content += "## Capabilities\n\n"
        content += "| Capability | Description | Permissions | Tools | Est. Time |\n"
        content += "| --- | --- | --- | --- | --- |\n"
        
        for cap in agent.capabilities:
            tools = ", ".join([f"`{t}`" for t in cap['tools_required']]) or "None"
            perms = cap.get('permission_required', agent.permission_level)
            # Ensure description is complete (not truncated)
            description = cap.get('description', '')
            # If description seems truncated (ends mid-sentence), try to complete it
            if description and not description[-1] in '.!?':
                # Description might be incomplete, but we'll use it as-is since it comes from the capability definition
                pass
            content += f"| `{cap['name']}` | {description} | {perms} | {tools} | {cap['execution_time_estimate']}s |\n"
            
        content += "\n## Usage Examples\n\n"
        
        examples = extractor.extract_examples(agent.agent_type)
        if examples:
            for i, example in enumerate(examples):
                content += f"### Example {i+1}\n\n"
                content += "```python\n"
                content += example
                content += "\n```\n\n"
        else:
            content += "_No examples found in test files._\n\n"
        
        with open(filepath, "w") as f:
            f.write(content)
            
    logger.info(f"Generated {len(agent_metadata)} agent documentation files.")

def generate_capability_index(agent_metadata: Dict[str, AgentMetadata]):
    """Generate index of all capabilities"""
    logger.info("Generating Capability Index...")
    
    # Collect all capabilities
    all_caps = []
    for agent in agent_metadata.values():
        for cap in agent.capabilities:
            all_caps.append({
                "name": cap['name'],
                "description": cap['description'],
                "agent": agent.name,
                "agent_type": agent.agent_type,
                "permission": cap.get('permission_required', agent.permission_level)
            })
            
    # Sort by capability name
    all_caps.sort(key=lambda x: x['name'])
    
    content = "# Agent Capability Index\n\n"
    content += "Alphabetical list of all capabilities across the agent fleet.\n\n"
    content += "| Capability | Description | Agent | Permission |\n"
    content += "| --- | --- | --- | --- |\n"
    
    for cap in all_caps:
        link = f"[{cap['agent']}]({cap['agent_type']}.md)" if cap['agent_type'] else cap['agent']
        content += f"| `{cap['name']}` | {cap['description']} | {link} | {cap['permission']} |\n"
        
    with open(DOCS_DIR / "CAPABILITY_INDEX.md", "w") as f:
        f.write(content)
    logger.info("CAPABILITY_INDEX.md created.")

def generate_registry(agent_metadata: Dict[str, AgentMetadata]):
    """Generate capability_registry.json and routing_matrix.json"""
    logger.info("Generating registry files...")
    
    registry: Dict[str, Any] = {
        "agent_types": {},
        "capability_index": {}
    }
    
    routing_matrix = {}
    
    for agent in agent_metadata.values():
        if not agent.agent_type:
            continue
            
        # Agent Types
        registry["agent_types"][agent.agent_type] = {
            "class": agent.class_name,
            "permission_level": agent.permission_level,
            "capabilities": {
                cap['name']: {
                    "description": cap['description'],
                    "tools_required": cap['tools_required'],
                    "data_access": cap['data_access'],
                    "execution_time_estimate": cap['execution_time_estimate']
                } for cap in agent.capabilities
            }
        }
        
        # Capability Index
        for cap in agent.capabilities:
            cap_name = cap['name']
            if cap_name not in registry["capability_index"]:
                registry["capability_index"][cap_name] = []
            registry["capability_index"][cap_name].append(agent.agent_type)
            
            # Routing Matrix (Simplified: action -> agent_type)
            # In reality, query_type + action would map.
            # We'll map action -> agent_type for now.
            routing_matrix[cap_name] = agent.agent_type

    with open(DOCS_DIR / "capability_registry.json", "w") as f:
        json.dump(registry, f, indent=2)
        
    with open(DOCS_DIR / "routing_matrix.json", "w") as f:
        json.dump(routing_matrix, f, indent=2)
        
    logger.info("Registry files created.")
    
def generate_readme(agent_metadata: Dict[str, AgentMetadata]):
    """Generate README.md for docs/agents/"""
    content = "# Script Ohio 2.0 Agent Documentation\n\n"
    content += "Comprehensive documentation for the agent fleet.\n\n"
    
    content += "## Indexes\n\n"
    content += "- [Capability Index](CAPABILITY_INDEX.md) - Browse by action\n"
    content += "- [Agent Cheat Sheet](../../AGENTS.md#agent-cheat-sheet) - Quick reference\n\n"
    
    content += "## Agents\n\n"
    
    sorted_agents = sorted(agent_metadata.values(), key=lambda x: x.name)
    for agent in sorted_agents:
        if agent.agent_type:
            content += f"- [{agent.name}]({agent.agent_type}.md) - {agent.description.splitlines()[0] if agent.description else ''}\n"
            
    with open(DOCS_DIR / "README.md", "w") as f:
        f.write(content)
    logger.info("docs/agents/README.md created.")

def main():
    parser = argparse.ArgumentParser(description="Generate Agent Documentation")
    parser.add_argument("--update", action="store_true", help="Update all documentation")
    parser.add_argument("--validate", action="store_true", help="Validate documentation consistency")
    parser.add_argument("--output", type=str, help="Output directory", default=str(DOCS_DIR))
    args = parser.parse_args()
    
    setup_dirs()
    
    scanner = AgentScanner(str(ROOT_DIR))
    logger.info("Scanning for agents...")
    agent_metadata = scanner.scan_directory()
    
    mapping = get_agent_type_mapping(str(ORCHESTRATOR_PATH))
    logger.info(f"Found mappings for {len(mapping)} agents.")
    
    # Apply mappings
    for class_name, metadata in agent_metadata.items():
        if class_name in mapping:
            metadata.agent_type = mapping[class_name]
        else:
            if class_name not in EXCLUDED_AGENTS:
                logger.warning(f"Agent {class_name} not found in orchestrator mappings and not excluded.")
            
    # Filter out agents without types (which effectively excludes them from docs/validation)
    # unless they were excluded via EXCLUDED_AGENTS logic in scan_directory
    
    if args.validate:
        validator = DocValidator(ROOT_DIR)
        issues = validator.validate()
        if issues:
            print("\nValidation Issues:")
            for issue in issues:
                print(f"- {issue}")
            sys.exit(1)
        else:
            print("Validation successful! No issues found.")
        
        # If only validating and not updating, exit
        if not args.update:
            sys.exit(0)
            
    if args.update:
        update_agents_md(agent_metadata)
        generate_agent_docs(agent_metadata)
        generate_capability_index(agent_metadata)
        generate_registry(agent_metadata)
        generate_readme(agent_metadata)
        logger.info("Documentation generation complete.")
    else:
        if not args.validate:
            print("Use --update to generate documentation or --validate to check consistency.")

if __name__ == "__main__":
    main()
