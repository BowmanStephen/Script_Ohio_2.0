#!/usr/bin/env python3
"""
Plan to Workflow Converter

Converts TOON-formatted plans to WorkflowAutomatorAgent workflow definitions.
Supports both TOON and JSON input formats.

Usage:
    python scripts/plan_to_workflow.py plan.toon --output workflow.json
    python scripts/plan_to_workflow.py plan.md --toon --output workflow.json
    python scripts/plan_to_workflow.py plan.toon --execute
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

try:
    from toon_format import encode, decode
except ImportError:
    print("Error: TOON format module not found. Ensure src/toon_format.py exists.")
    sys.exit(1)


def parse_toon_plan(toon_path: Path) -> Dict[str, Any]:
    """
    Parse TOON format plan file.
    
    Args:
        toon_path: Path to TOON plan file
        
    Returns:
        Parsed plan data as dictionary
    """
    if not toon_path.exists():
        raise FileNotFoundError(f"Plan file not found: {toon_path}")
    
    try:
        toon_content = toon_path.read_text()
        plan_data = decode(toon_content)
        return plan_data
    except Exception as e:
        raise RuntimeError(f"Failed to parse TOON plan: {e}")


def parse_json_plan(json_path: Path) -> Dict[str, Any]:
    """
    Parse JSON format plan file.
    
    Args:
        json_path: Path to JSON plan file
        
    Returns:
        Parsed plan data as dictionary
    """
    if not json_path.exists():
        raise FileNotFoundError(f"Plan file not found: {json_path}")
    
    try:
        with open(json_path, 'r') as f:
            plan_data = json.load(f)
        return plan_data
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse JSON plan: {e}")


def parse_markdown_plan(md_path: Path) -> Dict[str, Any]:
    """
    Parse markdown format plan file.
    
    Parses markdown plans following the structure defined in docs/PLAN_STRUCTURE.md:
    - Title from first # heading
    - Objective from ## Objective section
    - Tasks from ## Tasks section with ### Task N: subsections
    - Steps from ## Steps section with ### Step N: subsections
    - Optional Shared Inputs and Workflow Config sections
    
    Args:
        md_path: Path to markdown plan file
        
    Returns:
        Parsed plan data as dictionary matching JSON plan structure
    """
    if not md_path.exists():
        raise FileNotFoundError(f"Plan file not found: {md_path}")
    
    content = md_path.read_text()
    lines = content.split('\n')
    
    # Extract title from first # heading
    title = ""
    for line in lines:
        if line.startswith('# ') and not line.startswith('##'):
            title = line[2:].strip()
            break
    
    # Extract objective
    objective = ""
    in_objective = False
    for line in lines:
        if line.strip() == '## Objective':
            in_objective = True
            continue
        elif in_objective:
            if line.startswith('##'):
                break
            if line.strip():
                objective = line.strip()
                break
    
    # Extract tasks
    tasks = []
    in_tasks = False
    current_task = None
    
    for i, line in enumerate(lines):
        if line.strip() == '## Tasks':
            in_tasks = True
            continue
        elif in_tasks:
            if line.startswith('##') and not line.startswith('###'):
                break
            elif line.startswith('### Task'):
                # Save previous task if exists
                if current_task:
                    tasks.append(current_task)
                # Start new task
                task_match = re.match(r'### Task \d+: (.+)', line)
                task_name = task_match.group(1).strip() if task_match else ""
                current_task = {
                    'id': '',
                    'name': task_name,
                    'description': '',
                    'steps': [],
                    'dependencies': [],
                    'agent_type': '',
                    'tools_required': [],
                    'estimated_time': 0.0
                }
            elif current_task and line.strip().startswith('- **'):
                # Parse task fields - handle multi-word field names
                field_match = re.match(r'- \*\*([^*]+)\*\*: (.+)', line)
                if field_match:
                    field_name_raw = field_match.group(1).strip()
                    field_name = field_name_raw.lower().replace(' ', '_')
                    field_value = field_match.group(2).strip()
                    
                    if field_name == 'id':
                        current_task['id'] = field_value
                    elif field_name == 'description':
                        current_task['description'] = field_value
                    elif field_name == 'agent':
                        current_task['agent_type'] = field_value
                    elif field_name == 'steps':
                        # Parse comma-separated step IDs
                        steps_str = field_value.strip('[]')
                        current_task['steps'] = [s.strip() for s in steps_str.split(',') if s.strip()]
                    elif field_name == 'dependencies':
                        # Parse array format
                        deps_str = field_value.strip('[]')
                        if deps_str:
                            current_task['dependencies'] = [d.strip() for d in deps_str.split(',') if d.strip()]
                        else:
                            current_task['dependencies'] = []
                    elif 'estimated' in field_name and 'time' in field_name:
                        # Extract time value (e.g., "5.0s" -> 5.0)
                        time_match = re.search(r'(\d+\.?\d*)', field_value)
                        if time_match:
                            current_task['estimated_time'] = float(time_match.group(1))
    
    # Add last task
    if current_task:
        tasks.append(current_task)
    
    # Extract steps
    steps = []
    in_steps = False
    current_step = None
    
    for line in lines:
        if line.strip() == '## Steps':
            in_steps = True
            continue
        elif in_steps:
            if line.startswith('##') and not line.startswith('###'):
                break
            elif line.startswith('### Step'):
                # Save previous step if exists
                if current_step:
                    steps.append(current_step)
                # Start new step
                step_match = re.match(r'### Step \d+: (.+)', line)
                step_name = step_match.group(1).strip() if step_match else ""
                current_step = {
                    'id': '',
                    'task_id': '',
                    'action': '',
                    'parameters': {},
                    'step_type': 'AGENT_EXECUTION',
                    'timeout': 300,
                    'dependencies': [],
                    'retry_count': 3
                }
            elif current_step and line.strip().startswith('- **'):
                # Parse step fields - handle multi-word field names
                field_match = re.match(r'- \*\*([^*]+)\*\*: (.+)', line)
                if field_match:
                    field_name_raw = field_match.group(1).strip()
                    field_name = field_name_raw.lower().replace(' ', '_')
                    field_value = field_match.group(2).strip()
                    
                    if field_name == 'id':
                        current_step['id'] = field_value
                    elif field_name == 'task':
                        current_step['task_id'] = field_value
                    elif field_name == 'action':
                        current_step['action'] = field_value
                    elif field_name == 'type':
                        current_step['step_type'] = field_value
                    elif field_name == 'parameters':
                        # Try to parse JSON, fallback to empty dict
                        try:
                            current_step['parameters'] = json.loads(field_value)
                        except:
                            current_step['parameters'] = {}
                    elif field_name == 'timeout':
                        # Extract timeout value (e.g., "30s" -> 30)
                        timeout_match = re.search(r'(\d+)', field_value)
                        if timeout_match:
                            current_step['timeout'] = int(timeout_match.group(1))
                    elif field_name == 'dependencies':
                        # Parse array format
                        deps_str = field_value.strip('[]')
                        if deps_str:
                            current_step['dependencies'] = [d.strip() for d in deps_str.split(',') if d.strip()]
                        else:
                            current_step['dependencies'] = []
    
    # Add last step
    if current_step:
        steps.append(current_step)
    
    # Extract shared inputs (optional)
    shared_inputs = {}
    in_shared = False
    for line in lines:
        if line.strip() == '## Shared Inputs':
            in_shared = True
            continue
        elif in_shared:
            if line.startswith('##'):
                break
            # Simple parsing - could be enhanced
            if line.strip() and not line.strip().startswith('('):
                # Try to parse as JSON if it looks like JSON
                try:
                    shared_inputs = json.loads(line.strip())
                except:
                    pass
    
    # Extract workflow config (optional)
    workflow_config = {
        'parallel_execution': False,
        'error_recovery': True,
        'max_retries': 3
    }
    in_config = False
    for line in lines:
        if line.strip() == '## Workflow Config':
            in_config = True
            continue
        elif in_config:
            if line.startswith('##'):
                break
            if line.strip().startswith('- '):
                # Parse config fields
                config_match = re.match(r'- (\w+): (.+)', line)
                if config_match:
                    config_key = config_match.group(1).lower().replace(' ', '_')
                    config_value = config_match.group(2).strip()
                    if config_key == 'parallel_execution':
                        workflow_config['parallel_execution'] = config_value.lower() == 'true'
                    elif config_key == 'error_recovery':
                        workflow_config['error_recovery'] = config_value.lower() == 'true'
                    elif config_key == 'max_retries':
                        workflow_config['max_retries'] = int(config_value)
    
    # Build plan data structure
    plan_data = {
        'metadata': {
            'title': title,
            'objective': objective,
            'version': '1.0'
        },
        'tasks': tasks,
        'steps': steps,
        'shared_inputs': shared_inputs,
        'workflow_config': workflow_config
    }
    
    return plan_data


def validate_plan_structure(plan_data: Dict[str, Any]) -> bool:
    """
    Validate plan structure matches required format.
    
    Args:
        plan_data: Plan data dictionary
        
    Returns:
        True if valid, raises ValueError if invalid
    """
    # Check required top-level keys
    required_keys = ['metadata', 'tasks', 'steps']
    for key in required_keys:
        if key not in plan_data:
            raise ValueError(f"Missing required key: {key}")
    
    # Validate metadata
    metadata = plan_data['metadata']
    if not isinstance(metadata, dict):
        raise ValueError("metadata must be a dictionary")
    if 'title' not in metadata or 'objective' not in metadata:
        raise ValueError("metadata must contain 'title' and 'objective'")
    
    # Validate tasks array
    tasks = plan_data['tasks']
    if not isinstance(tasks, list):
        raise ValueError("tasks must be an array")
    if len(tasks) == 0:
        raise ValueError("tasks array cannot be empty")
    
    # Check uniform structure in tasks
    if len(tasks) > 0:
        first_task_keys = set(tasks[0].keys())
        for i, task in enumerate(tasks):
            if not isinstance(task, dict):
                raise ValueError(f"Task {i} must be a dictionary")
            task_keys = set(task.keys())
            if task_keys != first_task_keys:
                raise ValueError(f"Task {i} has inconsistent structure. Expected keys: {first_task_keys}, got: {task_keys}")
            if 'id' not in task or 'name' not in task:
                raise ValueError(f"Task {i} must contain 'id' and 'name'")
    
    # Validate steps array
    steps = plan_data['steps']
    if not isinstance(steps, list):
        raise ValueError("steps must be an array")
    
    # Check uniform structure in steps
    if len(steps) > 0:
        first_step_keys = set(steps[0].keys())
        step_ids = set()
        for i, step in enumerate(steps):
            if not isinstance(step, dict):
                raise ValueError(f"Step {i} must be a dictionary")
            step_keys = set(step.keys())
            if step_keys != first_step_keys:
                raise ValueError(f"Step {i} has inconsistent structure. Expected keys: {first_step_keys}, got: {step_keys}")
            if 'id' not in step or 'task_id' not in step or 'action' not in step:
                raise ValueError(f"Step {i} must contain 'id', 'task_id', and 'action'")
            if step['id'] in step_ids:
                raise ValueError(f"Duplicate step ID: {step['id']}")
            step_ids.add(step['id'])
    
    # Validate step references
    task_ids = {task['id'] for task in tasks}
    for step in steps:
        if step['task_id'] not in task_ids:
            raise ValueError(f"Step {step['id']} references invalid task_id: {step['task_id']}")
    
    # Validate dependencies
    for step in steps:
        deps = step.get('dependencies', [])
        if deps:
            for dep_id in deps:
                if dep_id not in step_ids:
                    raise ValueError(f"Step {step['id']} has invalid dependency: {dep_id}")
    
    return True


def convert_to_workflow_definition(plan_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert plan data to WorkflowAutomatorAgent workflow definition.
    
    Args:
        plan_data: Validated plan data
        
    Returns:
        Workflow definition compatible with WorkflowAutomatorAgent
    """
    import time
    import importlib.util
    from pathlib import Path
    
    # Lazy import to avoid syntax errors in workflow_automator_agent
    try:
        # Try importing normally first
        from agents.workflow_automator_agent import WorkflowStepType, WorkflowStep
    except SyntaxError:
        # If syntax error, define minimal versions locally
        from enum import Enum
        from dataclasses import dataclass
        from typing import Optional, List, Dict as DictType, Any as AnyType
        
        class WorkflowStepType(Enum):
            AGENT_EXECUTION = "agent_execution"
            DATA_PROCESSING = "data_processing"
            ANALYSIS = "analysis"
            VISUALIZATION = "visualization"
            CONDITION_CHECK = "condition_check"
            PARALLEL_EXECUTION = "parallel_execution"
        
        @dataclass
        class WorkflowStep:
            step_id: str
            step_type: WorkflowStepType
            description: str
            agent_type: Optional[str] = None
            action: Optional[str] = None
            parameters: Optional[DictType[str, AnyType]] = None
            dependencies: Optional[List[str]] = None
            timeout: int = 300
            retry_count: int = 3
    
    metadata = plan_data['metadata']
    tasks = plan_data['tasks']
    steps_data = plan_data['steps']
    shared_inputs = plan_data.get('shared_inputs', {})
    workflow_config = plan_data.get('workflow_config', {})
    
    # Map step types
    step_type_map = {
        'AGENT_EXECUTION': WorkflowStepType.AGENT_EXECUTION,
        'DATA_PROCESSING': WorkflowStepType.DATA_PROCESSING,
        'ANALYSIS': WorkflowStepType.ANALYSIS,
        'VISUALIZATION': WorkflowStepType.VISUALIZATION,
        'CONDITION_CHECK': WorkflowStepType.CONDITION_CHECK,
        'PARALLEL_EXECUTION': WorkflowStepType.PARALLEL_EXECUTION,
    }
    
    # Create workflow steps
    workflow_steps = []
    task_map = {task['id']: task for task in tasks}
    
    for step_data in steps_data:
        task = task_map.get(step_data['task_id'])
        step_type_str = step_data.get('step_type', 'AGENT_EXECUTION')
        step_type = step_type_map.get(step_type_str, WorkflowStepType.AGENT_EXECUTION)
        
        step = WorkflowStep(
            step_id=step_data['id'],
            step_type=step_type,
            description=step_data.get('description', step_data.get('action', '')),
            agent_type=task.get('agent_type') if task else step_data.get('agent_type'),
            action=step_data.get('action'),
            parameters=step_data.get('parameters', {}),
            dependencies=step_data.get('dependencies', []),
            timeout=step_data.get('timeout', 300),
            retry_count=step_data.get('retry_count', 3)
        )
        workflow_steps.append(step)
    
    # Create workflow definition
    workflow_id = f"wf_{int(time.time())}"
    workflow_def = {
        'workflow_id': workflow_id,
        'name': metadata.get('title', 'Unnamed Workflow'),
        'description': metadata.get('objective', ''),
        'steps': workflow_steps,
        'shared_inputs': shared_inputs,
        'metadata': {
            'created_at': metadata.get('created_at', time.time()),
            'author': metadata.get('author', 'unknown'),
            'version': metadata.get('version', '1.0'),
            'parallel_execution': workflow_config.get('parallel_execution', False),
            'error_recovery': workflow_config.get('error_recovery', True),
            'max_retries': workflow_config.get('max_retries', 3)
        }
    }
    
    return workflow_def


def main():
    parser = argparse.ArgumentParser(
        description="Convert TOON/JSON plans to WorkflowAutomatorAgent workflow definitions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert TOON plan to workflow JSON
  python scripts/plan_to_workflow.py plan.toon --output workflow.json
  
  # Convert JSON plan to workflow
  python scripts/plan_to_workflow.py plan.json --output workflow.json
  
  # Convert markdown plan (via TOON conversion)
  python scripts/plan_to_workflow.py plan.md --toon --output workflow.json
  
  # Execute workflow directly (requires orchestrator)
  python scripts/plan_to_workflow.py plan.toon --execute
        """
    )
    
    parser.add_argument(
        'plan_path',
        help='Path to plan file (.toon, .json, or .md)'
    )
    
    parser.add_argument(
        '--output', '-o',
        help='Output file path for workflow definition (JSON)'
    )
    
    parser.add_argument(
        '--toon',
        action='store_true',
        help='Convert markdown to TOON first (for .md files)'
    )
    
    parser.add_argument(
        '--execute',
        action='store_true',
        help='Execute workflow via WorkflowAutomatorAgent (requires orchestrator)'
    )
    
    parser.add_argument(
        '--validate-only',
        action='store_true',
        help='Only validate plan structure, do not convert'
    )
    
    args = parser.parse_args()
    
    plan_path = Path(args.plan_path)
    if not plan_path.exists():
        print(f"Error: Plan file not found: {plan_path}", file=sys.stderr)
        sys.exit(1)
    
    # Parse plan based on extension
    try:
        if plan_path.suffix == '.toon':
            plan_data = parse_toon_plan(plan_path)
        elif plan_path.suffix == '.json':
            plan_data = parse_json_plan(plan_path)
        elif plan_path.suffix == '.md':
            if args.toon:
                # Parse markdown plan
                plan_data = parse_markdown_plan(plan_path)
                # Convert to TOON format
                try:
                    toon_content = encode(plan_data)
                    # Optionally save TOON version (could add --save-toon flag)
                    print("✓ Converted markdown plan to TOON format", file=sys.stderr)
                except RuntimeError as e:
                    print(f"Warning: Could not convert to TOON format: {e}", file=sys.stderr)
                    print("Continuing with parsed JSON structure...", file=sys.stderr)
            else:
                # Parse markdown but don't convert to TOON
                plan_data = parse_markdown_plan(plan_path)
        else:
            # Try to parse as JSON
            try:
                plan_data = parse_json_plan(plan_path)
            except:
                print(f"Error: Unsupported file format: {plan_path.suffix}", file=sys.stderr)
                sys.exit(1)
    except Exception as e:
        print(f"Error parsing plan: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Validate plan structure
    try:
        validate_plan_structure(plan_data)
        print("✓ Plan structure validated", file=sys.stderr)
    except ValueError as e:
        print(f"Error: Invalid plan structure: {e}", file=sys.stderr)
        sys.exit(1)
    
    if args.validate_only:
        print("Validation successful!", file=sys.stderr)
        sys.exit(0)
    
    # Convert to workflow definition
    try:
        workflow_def = convert_to_workflow_definition(plan_data)
        print(f"✓ Converted plan to workflow definition", file=sys.stderr)
    except Exception as e:
        print(f"Error converting to workflow: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Output workflow definition
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert WorkflowStep objects to dicts for JSON serialization
        workflow_dict = {
            'workflow_id': workflow_def['workflow_id'],
            'name': workflow_def['name'],
            'description': workflow_def['description'],
            'steps': [
                {
                    'step_id': step.step_id,
                    'step_type': step.step_type.value,
                    'description': step.description,
                    'agent_type': step.agent_type,
                    'action': step.action,
                    'parameters': step.parameters or {},
                    'dependencies': step.dependencies or [],
                    'timeout': step.timeout,
                    'retry_count': step.retry_count
                }
                for step in workflow_def['steps']
            ],
            'shared_inputs': workflow_def['shared_inputs'],
            'metadata': workflow_def['metadata']
        }
        
        with open(output_path, 'w') as f:
            json.dump(workflow_dict, f, indent=2, default=str)
        
        print(f"✓ Workflow definition written to {output_path}", file=sys.stderr)
    else:
        # Print to stdout
        print(json.dumps(workflow_def, indent=2, default=str))
    
    # Execute if requested
    if args.execute:
        print("Execution via WorkflowAutomatorAgent not yet implemented in CLI", file=sys.stderr)
        print("Use the orchestrator or agent system to execute workflows", file=sys.stderr)
        # TODO: Implement execution via orchestrator


if __name__ == "__main__":
    main()

