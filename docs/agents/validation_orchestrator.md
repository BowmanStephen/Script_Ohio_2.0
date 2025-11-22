# Validation Orchestrator

**Type**: `validation_orchestrator`
**Permission Level**: `ADMIN`
**Source**: [`agents/validation_orchestrator.py`](../../agents/validation_orchestrator.py)

## Description

Meta Coordinator for Activation Fix System Validation

Coordinates specialized sub-agents to validate and document the
existing activation fix implementation using hierarchical orchestration.

## Capabilities

| Capability | Description | Permissions | Tools | Est. Time |
| --- | --- | --- | --- | --- |
| `coordinate_validation` | Coordinate validation phases and sub-agent execution | ADMIN | `file_system`, `agent_framework`, `analytics` | 120.0s |
| `discover_system` | Discover and analyze activation fix system architecture | READ_EXECUTE | `file_system`, `code_analysis` | 30.0s |
| `validate_comprehensive` | Execute comprehensive validation across all components | READ_EXECUTE | `testing_framework`, `performance_analysis` | 45.0s |
| `document_system` | Create comprehensive documentation and educational content | READ_EXECUTE_WRITE | `documentation_generator`, `tutorial_creator` | 30.0s |
| `quality_assurance` | Execute quality assurance testing and grading | READ_EXECUTE | `testing_framework`, `quality_metrics` | 30.0s |
| `synthesize_results` | Synthesize all findings and create final recommendations | READ_EXECUTE_WRITE | `report_generator`, `project_management` | 15.0s |

## Usage Examples

_No examples found in test files._

