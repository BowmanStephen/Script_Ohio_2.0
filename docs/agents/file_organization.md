# File Organization Agent

**Type**: `file_organization`
**Permission Level**: `READ_EXECUTE_WRITE`
**Source**: [`agents/file_organization_agent.py`](../../agents/file_organization_agent.py)

## Description

Specialized agent for organizing misplaced project files into appropriate
subdirectories according to CLAUDE.md specifications.

Capabilities:
- Classify root directory files by type
- Create missing directory structure
- Move files with proper naming conventions
- Handle special cases like Desktop screenshots

## Capabilities

| Capability | Description | Permissions | Tools | Est. Time |
| --- | --- | --- | --- | --- |
| `classify_root_files` | Identify and categorize misplaced files in root directory | READ_ONLY | `pathlib`, `os` | 1.0s |
| `create_missing_directories` | Create missing directory structure per CLAUDE.md | READ_EXECUTE_WRITE | `pathlib`, `os` | 0.5s |
| `organize_into_directories` | Move files to appropriate subdirectories with proper naming | READ_EXECUTE_WRITE | `shutil`, `pathlib`, `os` | 2.0s |

## Usage Examples

_No examples found in test files._

