# Week 13 Analysis Orchestrator

**Type**: `weekly_analysis_orchestrator`
**Permission Level**: `ADMIN`
**Source**: [`agents/weekly_analysis_orchestrator.py`](../../agents/weekly_analysis_orchestrator.py)

## Description

Orchestrator that coordinates weekly analysis agents for comprehensive
matchup analysis, model validation, and prediction generation

## Capabilities

| Capability | Description | Permissions | Tools | Est. Time |
| --- | --- | --- | --- | --- |
| `run_weekly_analysis` | Run complete Week 13 analysis pipeline | ADMIN | `matchup_analysis`, `model_validation`, `prediction_generation` | 30.0s |
| `validate_models` | Validate models for Week 13 | READ_EXECUTE_WRITE | `model_validation` | 12.0s |
| `generate_predictions` | Generate predictions for Week 13 | READ_EXECUTE_WRITE | `prediction_generation` | 15.0s |

## Usage Examples

_No examples found in test files._

