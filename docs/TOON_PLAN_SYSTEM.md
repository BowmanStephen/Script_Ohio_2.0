# TOON Plan-to-Workflow System User Guide

Complete guide to using TOON-formatted plans with the WorkflowAutomatorAgent system.

## Overview

The TOON Plan-to-Workflow system enables you to:
1. Create human-readable plans in Cursor (markdown)
2. Convert plans to token-efficient TOON format
3. Execute plans as workflows via WorkflowAutomatorAgent
4. Use reusable plan templates for common patterns

## Architecture

```
Cursor Plans (Markdown) → TOON Conversion → Plan Parser → WorkflowAutomatorAgent → Execution
```

## Quick Start

### 1. Create a Plan

Create a plan in `.cursor/plans/` following the structure in `docs/PLAN_STRUCTURE.md`:

```markdown
# My Analysis Plan

## Objective
Analyze team performance for Week 13

## Tasks
### Task 1: Generate Predictions
- **ID**: task_1
- **Agent**: model_engine
- **Steps**: step_1, step_2
- **Estimated Time**: 8.0s

## Steps
### Step 1: Load Models
- **ID**: step_1
- **Task**: task_1
- **Action**: load_models
- **Type**: AGENT_EXECUTION
- **Timeout**: 30s
```

### 2. Convert to TOON

```bash
# Convert plan to TOON format
python scripts/plan_to_workflow.py .cursor/plans/my_plan.plan.md --toon --output my_plan.toon
```

### 3. Execute Workflow

```python
from agents.workflow_automator_agent import WorkflowAutomatorAgent

agent = WorkflowAutomatorAgent(agent_id="workflow_001")
result = agent._execute_action(
    "execute_toon_plan",
    {"plan_path": "my_plan.toon"},
    {"user_id": "user_001"}
)
```

## Using Templates

### Load a Template

```python
from workflows.templates.template_loader import load_template

# Load weekly analysis template
plan_data = load_template('weekly_analysis', {
    'week': 13,
    'season': 2025
})

# Convert to workflow
from scripts.plan_to_workflow import convert_to_workflow_definition
workflow_def = convert_to_workflow_definition(plan_data)
```

### Available Templates

- **data_validation.toon**: Validate and fix missing data columns
- **weekly_analysis.toon**: Generate comprehensive weekly analysis

See `workflows/templates/README.md` for details.

## Plan Structure

Plans must follow the structure defined in `docs/PLAN_STRUCTURE.md`:

### Required Components

1. **Metadata**: Plan title, objective, author, version
2. **Tasks Array**: Uniform structure with id, name, description, agent_type, estimated_time
3. **Steps Array**: Uniform structure with id, task_id, action, step_type, timeout
4. **Shared Inputs**: Data shared across workflow steps
5. **Workflow Config**: Parallel execution, error recovery settings

### Uniform Arrays

**Critical**: All tasks must have identical fields, all steps must have identical fields. This enables TOON's tabular format for maximum token efficiency.

## Conversion Process

### Markdown → TOON → Workflow

1. **Create Plan**: Write plan in markdown format
2. **Validate Structure**: Ensure uniform arrays and required fields
3. **Convert to TOON**: Use `scripts/plan_to_workflow.py`
4. **Parse TOON**: System automatically parses TOON format
5. **Convert to Workflow**: Plan converted to WorkflowAutomatorAgent format
6. **Execute**: WorkflowAutomatorAgent executes the workflow

## CLI Usage

### Convert Plan

```bash
# Convert TOON plan to workflow JSON
python scripts/plan_to_workflow.py plan.toon --output workflow.json

# Convert JSON plan to workflow
python scripts/plan_to_workflow.py plan.json --output workflow.json

# Validate plan structure only
python scripts/plan_to_workflow.py plan.toon --validate-only
```

### Execute Plan

```python
# Via WorkflowAutomatorAgent
from agents.workflow_automator_agent import WorkflowAutomatorAgent

agent = WorkflowAutomatorAgent(agent_id="workflow_001")
result = agent._execute_action(
    "execute_toon_plan",
    {"plan_path": "path/to/plan.toon"},
    {"user_id": "user_001"}
)
```

## Agent Integration

### WorkflowAutomatorAgent Capabilities

The `execute_toon_plan` capability:
- Parses TOON-formatted plans
- Validates plan structure
- Converts to workflow definition
- Executes via existing workflow system

### Tool Integration

The `convert_to_toon` tool (available via ToolLoader):
- Converts JSON data to TOON format
- Estimates token savings
- Supports file output

```python
from agents.core.tool_loader import ToolLoader

tool_loader = ToolLoader()
result = tool_loader.tools['convert_to_toon'].execute(
    {
        'data': my_data,
        'output_path': 'output.toon',
        'estimate_savings': True
    },
    {}
)
```

## Best Practices

### Plan Design

1. **Keep tasks focused**: Each task should have a single, clear purpose
2. **Minimize dependencies**: Reduce complexity by limiting dependencies
3. **Use uniform structures**: Ensure all array items have identical fields
4. **Document parameters**: Clearly document what each parameter does
5. **Estimate accurately**: Provide realistic time estimates for planning

### TOON Optimization

1. **Uniform arrays**: All tasks/steps must have same fields
2. **Flat structures**: Avoid deeply nested non-uniform structures
3. **Group related data**: Use arrays for related items
4. **Test conversion**: Validate TOON conversion before execution

### Workflow Execution

1. **Test incrementally**: Validate plans before full execution
2. **Monitor progress**: Use workflow monitoring capabilities
3. **Handle errors**: Implement error recovery in workflow config
4. **Log results**: Track execution results for debugging

## Troubleshooting

### Plan Validation Errors

**Error**: "Missing required key: tasks"
- **Solution**: Ensure plan has `metadata`, `tasks`, and `steps` keys

**Error**: "Task 1 has inconsistent structure"
- **Solution**: All tasks must have identical fields. Check field names match exactly.

**Error**: "Step references invalid task_id"
- **Solution**: Ensure all step `task_id` values reference valid task IDs

### TOON Conversion Errors

**Error**: "TOON CLI not available"
- **Solution**: Install TOON CLI: `npm install -g @toon-format/cli`

**Error**: "TOON encoding failed"
- **Solution**: Check plan structure is valid JSON. Ensure uniform arrays.

### Execution Errors

**Error**: "Plan file not found"
- **Solution**: Use absolute paths or paths relative to project root

**Error**: "Invalid plan structure"
- **Solution**: Validate plan with `--validate-only` flag first

## Examples

### Example 1: Simple Data Validation

```json
{
  "metadata": {
    "title": "Data Validation",
    "objective": "Fix missing columns"
  },
  "tasks": [
    {
      "id": "task_1",
      "name": "Fix Columns",
      "description": "Populate missing columns",
      "agent_type": "workflow_automator",
      "estimated_time": 10.0
    }
  ],
  "steps": [
    {
      "id": "step_1",
      "task_id": "task_1",
      "action": "fix_columns",
      "step_type": "DATA_PROCESSING",
      "timeout": 120
    }
  ]
}
```

### Example 2: Weekly Analysis Workflow

See `workflows/templates/weekly_analysis.toon` for complete example.

## Reference

- **Plan Structure**: `docs/PLAN_STRUCTURE.md`
- **TOON Format**: `docs/TOON_FORMAT_GUIDE.md`
- **Templates**: `workflows/templates/README.md`
- **WorkflowAutomatorAgent**: `agents/workflow_automator_agent.py`
- **Plan Converter**: `scripts/plan_to_workflow.py`

## Support

For issues or questions:
1. Check plan structure against `docs/PLAN_STRUCTURE.md`
2. Validate plan with `--validate-only` flag
3. Review TOON format in `docs/TOON_FORMAT_GUIDE.md`
4. Check workflow execution logs

