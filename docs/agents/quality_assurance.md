# Quality Assurance Agent

**Type**: `quality_assurance`
**Permission Level**: `READ_EXECUTE`
**Source**: [`agents/quality_assurance_agent.py`](../../agents/quality_assurance_agent.py)

## Description

Surfaces telemetry summaries, schema diff alerts, and health checks.

## Capabilities

| Capability | Description | Permissions | Tools | Est. Time |
| --- | --- | --- | --- | --- |
| `cfbd_health_check` | Summarize CFBD client telemetry and error rates | READ_EXECUTE | `telemetry` | 0.5s |
| `cfbd_recent_events` | Return the latest telemetry events for inspection | READ_EXECUTE | `telemetry` | 0.2s |

## Usage Examples

_No examples found in test files._

