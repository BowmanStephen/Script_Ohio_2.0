# Week12ModelValidation Agent

**Type**: `week12_model_validation`
**Permission Level**: `READ_EXECUTE_WRITE`
**Source**: [`agents/week12_model_validation_agent.py`](../../agents/week12_model_validation_agent.py)

## Description

Backward compatibility wrapper for Week 12 model validation.
Delegates to WeeklyModelValidationAgent with week=12.

## Capabilities

| Capability | Description | Permissions | Tools | Est. Time |
| --- | --- | --- | --- | --- |
| `validate_models` | Run validation suite across Week 12 ML models. | READ_EXECUTE_WRITE | `model_loader`, `data_validator` | 12.0s |
| `check_compatibility` | Assess compatibility between enhanced data and models. | READ_EXECUTE_WRITE | `data_validator` | 4.0s |
| `performance_test` | Benchmark model performance metrics. | READ_EXECUTE_WRITE | `performance_tester` | 6.0s |

## Usage Examples

_No examples found in test files._

