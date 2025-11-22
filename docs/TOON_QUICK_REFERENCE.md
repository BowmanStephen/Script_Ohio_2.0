# TOON Format Quick Reference

## Installation

```bash
npm install -g @toon-format/cli
```

## Quick Commands

### Convert Markdown Plan to Workflow

```bash
# Validate plan
python3 scripts/plan_to_workflow.py plan.md --toon --validate-only

# Convert to workflow JSON
python3 scripts/plan_to_workflow.py plan.md --toon --output workflow.json
```

### Run Smoke Test

```bash
python3 scripts/smoke_test_toon.py
```

### Python Usage

```python
from src.toon_format import encode, decode

# Encode
toon = encode({"data": [{"id": 1}, {"id": 2}]})

# Decode
data = decode(toon)
```

## Plan Template

```markdown
# Plan Title

## Objective
Your objective here

## Tasks

### Task 1: Task Name
- **ID**: task_1
- **Description**: Task description
- **Agent**: model_engine
- **Steps**: step_1
- **Dependencies**: []
- **Estimated Time**: 5.0s

## Steps

### Step 1: Step Name
- **ID**: step_1
- **Task**: task_1
- **Action**: action_name
- **Type**: AGENT_EXECUTION
- **Timeout**: 30s
- **Dependencies**: []
```

## Testing

```bash
# All TOON tests
pytest tests/test_toon_format.py tests/test_plan_to_workflow.py -v

# Smoke test
python3 scripts/smoke_test_toon.py
```

## See Also

- Full guide: `docs/TOON_USAGE_GUIDE.md`
- Plan structure: `docs/PLAN_STRUCTURE.md`

