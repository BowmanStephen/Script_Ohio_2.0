# Insight Generator

**Type**: `insight_generator`
**Permission Level**: `READ_EXECUTE_WRITE`
**Source**: [`agents/insight_generator_agent.py`](../../agents/insight_generator_agent.py)

## Description

Agent responsible for generating advanced analytics insights, statistical analysis,
and sophisticated visualizations for complex college football data.

## Capabilities

| Capability | Description | Permissions | Tools | Est. Time |
| --- | --- | --- | --- | --- |
| `generate_analysis` | Generate advanced analytics insights and statistical analysis | READ_EXECUTE_WRITE | `analyze_feature_importance`, `create_learning_path_chart`, `export_analysis_results` | 3.0s |
| `statistical_analysis` | Perform comprehensive statistical analysis and hypothesis testing | READ_EXECUTE_WRITE | `analyze_feature_importance` | 4.0s |
| `create_visualizations` | Generate sophisticated data visualizations and charts | READ_EXECUTE_WRITE | `create_learning_path_chart` | 2.5s |
| `comparative_analysis` | Compare teams, players, and seasons using advanced metrics | READ_EXECUTE_WRITE | `analyze_feature_importance`, `export_analysis_results` | 3.5s |
| `trend_analysis` | Analyze temporal trends and patterns in college football data | READ_EXECUTE_WRITE | `analyze_feature_importance`, `create_learning_path_chart` | 3.0s |
| `cfbd_real_time_analysis` | Pull live CFBD REST/NEXT data and align it with the 86-feature schema. | READ_EXECUTE_WRITE | `cfbd_rest_client`, `feature_engineering` | 2.5s |
| `graphql_trend_scan` | Analyze recruiting/talent trends using GraphQL API (requires Patreon Tier 3+ access). | READ_EXECUTE_WRITE | `cfbd_graphql_client`, `gql` | 2.5s |
| `generate_infographic` | Generate interactive infographic components for documentation and reports | READ_EXECUTE_WRITE | `create_visualizations` | 2.5s |

## Usage Examples

_No examples found in test files._

