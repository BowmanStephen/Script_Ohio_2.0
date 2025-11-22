# Week 13 Prediction Generation Agent

**Type**: `weekly_prediction_generation`
**Permission Level**: `READ_EXECUTE_WRITE`
**Source**: [`agents/weekly_prediction_generation_agent.py`](../../agents/weekly_prediction_generation_agent.py)

## Description

Agent responsible for generating weekly predictions using validated ML models
and enhanced matchup data

## Capabilities

| Capability | Description | Permissions | Tools | Est. Time |
| --- | --- | --- | --- | --- |
| `generate_predictions` | Generate predictions using validated ML models | READ_EXECUTE_WRITE | `model_predictor`, `data_processor`, `confidence_calculator`, `ensemble_generator` | 15.0s |
| `calculate_confidence` | Calculate confidence metrics for predictions | READ_EXECUTE_WRITE | `confidence_calculator` | 2.0s |
| `create_ensemble` | Create ensemble predictions from model outputs | READ_EXECUTE_WRITE | `ensemble_generator` | 4.0s |

## Usage Examples

_No examples found in test files._

