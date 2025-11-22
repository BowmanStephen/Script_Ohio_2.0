# Workflow Templates

This directory contains reusable TOON-formatted plan templates for common workflows.

## Available Templates

### data_validation.toon
Validates and fixes missing data columns in training datasets.

**Usage:**
```python
from workflows.templates.template_loader import load_template

template = load_template('data_validation', {
    'data_file': 'model_pack/updated_training_data.csv'
})
```

### weekly_analysis.toon
Generates comprehensive weekly analysis including predictions, insights, and visualizations.

**Usage:**
```python
template = load_template('weekly_analysis', {
    'week': 13,
    'season': 2025
})
```

## Template Format

Templates use TOON format with variable placeholders:
- Variables: `{{variable_name}}`
- Example: `"week": "{{week}}"` → replaced with actual value

## Creating New Templates

1. Create a `.toon` file in this directory
2. Follow the structure defined in `docs/PLAN_STRUCTURE.md`
3. Use `{{variable_name}}` for parameterized values
4. Ensure uniform arrays (same fields for all items)
5. Document usage in this README

## Template Loader

Use the template loader to instantiate templates:

```python
from workflows.templates.template_loader import load_template

# Load and instantiate template
plan_data = load_template('weekly_analysis', {
    'week': 13,
    'season': 2025
})

# Convert to workflow and execute
from scripts.plan_to_workflow import convert_to_workflow_definition
workflow_def = convert_to_workflow_definition(plan_data)
```

