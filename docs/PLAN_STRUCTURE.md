# Plan Structure Specification for TOON Conversion

This document defines the structure for plans that can be efficiently converted to TOON format and executed via the WorkflowAutomatorAgent.

## Overview

Plans are structured as JSON-compatible dictionaries with uniform arrays to maximize TOON format efficiency. The structure is designed to be:
- Human-readable in markdown format
- TOON-optimized (uniform arrays for token efficiency)
- Compatible with WorkflowAutomatorAgent workflow definitions

## Core Structure

```json
{
  "metadata": {
    "title": "Plan Title",
    "objective": "Clear plan objective",
    "created_at": "2025-11-19T12:00:00Z",
    "author": "user_id",
    "version": "1.0"
  },
  "tasks": [
    {
      "id": "task_1",
      "name": "Task Name",
      "description": "Task description",
      "steps": ["step_1", "step_2"],
      "dependencies": [],
      "agent_type": "model_engine",
      "tools_required": ["tool1", "tool2"],
      "estimated_time": 5.0
    }
  ],
  "steps": [
    {
      "id": "step_1",
      "task_id": "task_1",
      "action": "run_prediction",
      "parameters": {},
      "step_type": "AGENT_EXECUTION",
      "timeout": 30,
      "dependencies": []
    }
  ],
  "shared_inputs": {},
  "workflow_config": {
    "parallel_execution": false,
    "error_recovery": true,
    "max_retries": 3
  }
}
```

## TOON Format Example

When converted to TOON, the structure becomes:

```yaml
metadata:
  title: Plan Title
  objective: Clear plan objective
  created_at: 2025-11-19T12:00:00Z
  author: user_id
  version: "1.0"
tasks[1]{id,name,description,agent_type,estimated_time}:
  task_1,Task Name,Task description,model_engine,5.0
steps[1]{id,task_id,action,step_type,timeout}:
  step_1,task_1,run_prediction,AGENT_EXECUTION,30
shared_inputs: {}
workflow_config:
  parallel_execution: false
  error_recovery: true
  max_retries: 3
```

## Field Specifications

### Metadata Object
- **title** (string, required): Plan title
- **objective** (string, required): Clear objective statement
- **created_at** (string, ISO 8601): Creation timestamp
- **author** (string): User ID or identifier
- **version** (string): Plan version

### Tasks Array (Uniform Structure)
All tasks must have the same fields:
- **id** (string, required): Unique task identifier
- **name** (string, required): Task name
- **description** (string, required): Task description
- **steps** (array of strings): Step IDs belonging to this task
- **dependencies** (array of strings): Task IDs this task depends on
- **agent_type** (string): Agent type to execute task (e.g., "model_engine", "insight_generator")
- **tools_required** (array of strings): Required tools for this task
- **estimated_time** (float): Estimated execution time in seconds

### Steps Array (Uniform Structure)
All steps must have the same fields:
- **id** (string, required): Unique step identifier
- **task_id** (string, required): Parent task ID
- **action** (string, required): Action to execute (e.g., "run_prediction", "generate_analysis")
- **parameters** (object): Action-specific parameters
- **step_type** (string, required): One of:
  - `AGENT_EXECUTION`: Execute agent action
  - `DATA_PROCESSING`: Process data
  - `ANALYSIS`: Perform analysis
  - `VISUALIZATION`: Create visualization
  - `CONDITION_CHECK`: Check condition
  - `PARALLEL_EXECUTION`: Execute steps in parallel
- **timeout** (integer): Step timeout in seconds (default: 300)
- **dependencies** (array of strings): Step IDs this step depends on
- **retry_count** (integer): Number of retries on failure (default: 3)

### Shared Inputs
- **shared_inputs** (object): Data shared across all workflow steps
- Keys can be any string, values can be any JSON-serializable type

### Workflow Config
- **parallel_execution** (boolean): Allow parallel step execution
- **error_recovery** (boolean): Enable error recovery mechanisms
- **max_retries** (integer): Maximum retry attempts for failed steps

## TOON Optimization Guidelines

### Uniform Arrays
- **Tasks array**: All tasks must have identical field structure
- **Steps array**: All steps must have identical field structure
- This enables TOON's tabular format, achieving 50-70% token reduction

### Nested Structures
- Keep nested objects simple (metadata, shared_inputs, workflow_config)
- Avoid deeply nested non-uniform structures
- Use flat arrays where possible

### Field Ordering
- Maintain consistent field order across array items
- This improves TOON encoding efficiency

## Markdown Plan Format

When creating plans in `.cursor/plans/`, use this structure:

```markdown
# Plan Title

## Objective
Clear plan objective

## Tasks

### Task 1: Task Name
- **ID**: task_1
- **Description**: Task description
- **Agent**: model_engine
- **Steps**: step_1, step_2
- **Dependencies**: []
- **Estimated Time**: 5.0s

## Steps

### Step 1: Action Name
- **ID**: step_1
- **Task**: task_1
- **Action**: run_prediction
- **Type**: AGENT_EXECUTION
- **Parameters**: {}
- **Timeout**: 30s
- **Dependencies**: []

## Shared Inputs
(Optional shared data)

## Workflow Config
- Parallel Execution: false
- Error Recovery: true
- Max Retries: 3
```

## Conversion Process

1. **Markdown → JSON**: Parse markdown plan into structured JSON
2. **Validate Structure**: Ensure uniform arrays and required fields
3. **JSON → TOON**: Convert using `src/toon_format.encode()`
4. **TOON → Workflow**: Parse TOON and convert to WorkflowAutomatorAgent format
5. **Execute**: WorkflowAutomatorAgent executes the workflow

## Validation Rules

1. All tasks must have the same fields
2. All steps must have the same fields
3. Step IDs must be unique
4. Task IDs must be unique
5. Step dependencies must reference valid step IDs
6. Task dependencies must reference valid task IDs
7. Step `task_id` must reference a valid task ID
8. `step_type` must be a valid WorkflowStepType enum value

## Example: Data Validation Plan

```json
{
  "metadata": {
    "title": "Data Validation Plan",
    "objective": "Validate and fix missing data columns",
    "created_at": "2025-11-19T12:00:00Z",
    "author": "user_001"
  },
  "tasks": [
    {
      "id": "task_1",
      "name": "Fix Missing Columns",
      "description": "Populate game_key and conference_game columns",
      "steps": ["step_1", "step_2"],
      "dependencies": [],
      "agent_type": "workflow_automator",
      "tools_required": ["data_loading", "export_analysis_results"],
      "estimated_time": 10.0
    }
  ],
  "steps": [
    {
      "id": "step_1",
      "task_id": "task_1",
      "action": "load_data",
      "parameters": {"file": "model_pack/updated_training_data.csv"},
      "step_type": "DATA_PROCESSING",
      "timeout": 60,
      "dependencies": []
    },
    {
      "id": "step_2",
      "task_id": "task_1",
      "action": "fix_columns",
      "parameters": {"columns": ["game_key", "conference_game"]},
      "step_type": "DATA_PROCESSING",
      "timeout": 120,
      "dependencies": ["step_1"]
    }
  ],
  "shared_inputs": {},
  "workflow_config": {
    "parallel_execution": false,
    "error_recovery": true,
    "max_retries": 3
  }
}
```

## Best Practices

1. **Keep tasks focused**: Each task should have a single, clear purpose
2. **Minimize dependencies**: Reduce complexity by limiting dependencies
3. **Use uniform structures**: Ensure all array items have identical fields
4. **Document parameters**: Clearly document what each parameter does
5. **Estimate accurately**: Provide realistic time estimates for planning
6. **Test incrementally**: Validate plans before full execution

