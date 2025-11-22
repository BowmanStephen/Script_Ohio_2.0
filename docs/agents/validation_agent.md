# System Validation Agent

**Type**: `validation_agent`
**Permission Level**: `READ_EXECUTE`
**Source**: [`agents/validation_agent.py`](../../agents/validation_agent.py)

## Description

Specialized agent for validating file organization and system integrity.

Capabilities:
- Validate file moves completed successfully
- Check Python import integrity after script moves
- Update .gitignore with appropriate exclusions
- Generate comprehensive validation reports

## Capabilities

| Capability | Description | Permissions | Tools | Est. Time |
| --- | --- | --- | --- | --- |
| `validate_file_moves` | Verify all files moved correctly and exist in destinations | READ_ONLY | `pathlib`, `os` | 1.0s |
| `validate_import_integrity` | Check Python imports still work after file reorganization | READ_EXECUTE | `importlib`, `sys` | 1.5s |
| `update_gitignore` | Update .gitignore with new exclusions for organized files | READ_EXECUTE_WRITE | `pathlib` | 0.5s |
| `generate_validation_report` | Create comprehensive validation and organization report | READ_ONLY | `json`, `pathlib` | 0.5s |

## Usage Examples

_No examples found in test files._

