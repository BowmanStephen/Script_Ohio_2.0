# TOON Format Usage Guide

Complete guide to using TOON format features in Script Ohio 2.0.

## Quick Start

### 1. Verify TOON CLI Installation

```bash
# Check if TOON CLI is available
npx @toon-format/cli --version

# If not installed, install globally
npm install -g @toon-format/cli

# Or run the smoke test
python3 scripts/smoke_test_toon.py
```

### 2. Run Smoke Test

```bash
python3 scripts/smoke_test_toon.py
```

This verifies all TOON functionality is working correctly.

## Usage Examples

### Example 1: Convert Markdown Plan to Workflow

Create a markdown plan file (e.g., `my_plan.md`):

```markdown
# My Analysis Plan

## Objective
Analyze team performance for Week 13

## Tasks

### Task 1: Generate Predictions
- **ID**: task_1
- **Description**: Generate game predictions
- **Agent**: model_engine
- **Steps**: step_1, step_2
- **Dependencies**: []
- **Estimated Time**: 10.0s

## Steps

### Step 1: Load Models
- **ID**: step_1
- **Task**: task_1
- **Action**: load_models
- **Type**: AGENT_EXECUTION
- **Timeout**: 30s
- **Dependencies**: []

### Step 2: Run Predictions
- **ID**: step_2
- **Task**: task_1
- **Action**: run_prediction
- **Type**: AGENT_EXECUTION
- **Timeout**: 60s
- **Dependencies**: [step_1]

## Shared Inputs
{"week": 13, "season": 2025}

## Workflow Config
- Parallel Execution: false
- Error Recovery: true
- Max Retries: 3
```

Convert to workflow JSON:

```bash
# Validate only
python3 scripts/plan_to_workflow.py my_plan.md --toon --validate-only

# Convert to workflow JSON
python3 scripts/plan_to_workflow.py my_plan.md --toon --output workflow.json
```

### Example 2: Use TOON Format in Python

```python
from src.toon_format import encode, decode, encode_file, decode_file
import json

# Sample data with uniform arrays (best for TOON)
data = {
    "games": [
        {"id": 1, "home": "Ohio State", "away": "Michigan", "score": 42},
        {"id": 2, "home": "Alabama", "away": "Georgia", "score": 35}
    ]
}

# Encode to TOON
toon_output = encode(data)
print(f"TOON format ({len(toon_output)} chars):")
print(toon_output)

# Decode from TOON
decoded = decode(toon_output)
print("\nDecoded:")
print(json.dumps(decoded, indent=2))

# File operations
encode_file("data.json", "data.toon")  # JSON → TOON
decode_file("data.toon", "data_back.json")  # TOON → JSON
```

### Example 3: Convert JSON Plan to TOON

```bash
# If you have a JSON plan
python3 scripts/plan_to_workflow.py plan.json --output workflow.json

# To convert JSON to TOON first
python3 -c "
from src.toon_format import encode
import json

with open('plan.json') as f:
    plan_data = json.load(f)

toon_content = encode(plan_data)
with open('plan.toon', 'w') as f:
    f.write(toon_content)

print('Converted plan.json to plan.toon')
"
```

## Plan Structure

Plans must follow this structure (see `docs/PLAN_STRUCTURE.md` for details):

### Required Sections

1. **Title**: First `#` heading
2. **Objective**: `## Objective` section
3. **Tasks**: `## Tasks` with `### Task N:` subsections
4. **Steps**: `## Steps` with `### Step N:` subsections

### Optional Sections

- **Shared Inputs**: `## Shared Inputs` (JSON format)
- **Workflow Config**: `## Workflow Config` with settings

### Task Fields

Each task must have:
- **ID**: Unique identifier
- **Description**: Task description
- **Agent**: Agent type (e.g., `model_engine`, `insight_generator`)
- **Steps**: Comma-separated step IDs
- **Dependencies**: Array of task IDs (or `[]`)
- **Estimated Time**: Time in seconds (e.g., `5.0s`)

### Step Fields

Each step must have:
- **ID**: Unique identifier
- **Task**: Parent task ID
- **Action**: Action to execute
- **Type**: Step type (`AGENT_EXECUTION`, `DATA_PROCESSING`, `ANALYSIS`, etc.)
- **Timeout**: Timeout in seconds (e.g., `30s`)
- **Dependencies**: Array of step IDs (or `[]`)

## Command-Line Usage

### `plan_to_workflow.py`

```bash
# Convert TOON plan to workflow
python3 scripts/plan_to_workflow.py plan.toon --output workflow.json

# Convert JSON plan to workflow
python3 scripts/plan_to_workflow.py plan.json --output workflow.json

# Convert markdown plan to workflow (with TOON conversion)
python3 scripts/plan_to_workflow.py plan.md --toon --output workflow.json

# Validate plan structure only
python3 scripts/plan_to_workflow.py plan.md --toon --validate-only
```

### Options

- `--output`, `-o`: Output file path for workflow JSON
- `--toon`: Convert markdown to TOON first (required for `.md` files)
- `--validate-only`: Only validate plan structure, don't convert
- `--execute`: Execute workflow (not yet implemented)

## Python API

### TOON Format Module

```python
from src.toon_format import (
    encode,           # Encode JSON to TOON
    decode,           # Decode TOON to JSON
    encode_file,      # Encode JSON file to TOON file
    decode_file,      # Decode TOON file to JSON file
    estimate_token_savings,  # Estimate token savings
    has_uniform_arrays,      # Check if data has uniform arrays
    _check_toon_cli   # Check if TOON CLI is available
)
```

### Plan to Workflow Module

```python
import importlib.util
from pathlib import Path

# Load the module
plan_to_workflow_path = Path("scripts/plan_to_workflow.py")
spec = importlib.util.spec_from_file_location("plan_to_workflow", plan_to_workflow_path)
plan_to_workflow = importlib.util.module_from_spec(spec)
spec.loader.exec_module(plan_to_workflow)

# Use functions
plan_data = plan_to_workflow.parse_markdown_plan(Path("plan.md"))
plan_to_workflow.validate_plan_structure(plan_data)
workflow_def = plan_to_workflow.convert_to_workflow_definition(plan_data)
```

## Testing

### Run All Tests

```bash
# Run TOON format tests
python3 -m pytest tests/test_toon_format.py -v

# Run plan-to-workflow tests
python3 -m pytest tests/test_plan_to_workflow.py -v

# Run all TOON-related tests
python3 -m pytest tests/test_toon_format.py tests/test_plan_to_workflow.py -v

# Run smoke test
python3 scripts/smoke_test_toon.py
```

### Test Coverage

- ✅ TOON CLI availability
- ✅ Encoding/decoding
- ✅ File operations
- ✅ Markdown parsing
- ✅ Plan validation
- ✅ Workflow conversion
- ✅ End-to-end workflows

## Troubleshooting

### TOON CLI Not Available

```bash
# Install globally
npm install -g @toon-format/cli

# Verify installation
npx @toon-format/cli --version

# Check in Python
python3 -c "from src.toon_format import _check_toon_cli; print(_check_toon_cli())"
```

### Markdown Parsing Errors

- Ensure all required sections are present (Title, Objective, Tasks, Steps)
- Check that task and step IDs are unique
- Verify field names match exactly (case-sensitive)
- Use proper markdown formatting (e.g., `- **ID**: value`)

### Plan Validation Errors

- All tasks must have the same fields (uniform structure)
- All steps must have the same fields (uniform structure)
- Step `task_id` must reference a valid task ID
- Step dependencies must reference valid step IDs

### Workflow Conversion Errors

- Ensure plan structure is valid before conversion
- Check that step types match enum values
- Verify agent types are valid

## Best Practices

1. **Use Uniform Arrays**: TOON format is most efficient with uniform arrays
2. **Validate Early**: Use `--validate-only` before full conversion
3. **Test Incrementally**: Start with simple plans, add complexity gradually
4. **Keep Plans Focused**: Each task should have a single, clear purpose
5. **Document Parameters**: Clearly document what each parameter does

## Token Optimization

TOON format can reduce token usage by 50-70% for uniform arrays:

```python
from src.toon_format import estimate_token_savings, encode

data = {
    "tasks": [
        {"id": "t1", "name": "Task 1", "time": 5.0},
        {"id": "t2", "name": "Task 2", "time": 10.0},
        # ... more tasks
    ]
}

toon_output = encode(data)
savings = estimate_token_savings(data, toon_output)
print(f"Token savings: {savings['token_savings_percent']:.1f}%")
```

## Additional Resources

- **Plan Structure**: `docs/PLAN_STRUCTURE.md` - Complete plan specification
- **TOON Format Guide**: `docs/TOON_FORMAT_GUIDE.md` - TOON format details
- **TOON Plan System**: `docs/TOON_PLAN_SYSTEM.md` - Plan-to-workflow system
- **Bootstrap Script**: `scripts/bootstrap_dev_env.sh` - Includes TOON CLI check

## Support

If you encounter issues:

1. Run the smoke test: `python3 scripts/smoke_test_toon.py`
2. Check TOON CLI: `npx @toon-format/cli --version`
3. Review test output for specific error messages
4. Verify plan structure matches `docs/PLAN_STRUCTURE.md`

