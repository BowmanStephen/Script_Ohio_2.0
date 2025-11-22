# RequestRouter Instrumentation Guide

## Overview

This document describes the instrumentation system added to `RequestRouter` and `AnalyticsOrchestrator` to validate simplification assumptions before removing router complexity. The instrumentation tracks metrics, logs audit events, and provides analysis tooling to make data-driven decisions about router simplification.

## Purpose

The RequestRouter currently includes features like:
- Request queuing
- Priority-based sorting
- Permission checking
- Agent discovery

Before simplifying or removing these features, we need to validate that:
1. They are not being used in practice
2. They don't add significant overhead
3. Removing them won't break existing functionality

The instrumentation system provides the data needed to make these decisions safely.

## Metrics Tracked

### RequestRouter Metrics

The `RequestRouter` class tracks the following metrics:

#### Count Metrics
- **`submit_count`**: Total number of requests submitted to the router
- **`process_count`**: Total number of times `process_requests()` was called
- **`permission_denials`**: Number of requests denied due to insufficient permissions
- **`agent_not_found_count`**: Number of requests where no suitable agent was found
- **`priority_sorts`**: Number of times the queue was sorted by priority
- **`errors_caught`**: Number of exceptions caught during request processing
- **`completed_requests_queries`**: Number of times `get_request_status()` was called

#### Queue Size Metrics
- **`queue_sizes_at_submit`**: List of queue sizes when requests were submitted
- **`queue_sizes_at_process`**: List of queue sizes when requests were processed

#### Performance Metrics
- **`total_overhead_ms`**: Total time spent in router operations (milliseconds)

### AnalyticsOrchestrator Metrics

The `AnalyticsOrchestrator._execute_agent_requests()` method tracks:
- **`request_id`**: Identifier for the orchestrator request
- **`agent_count`**: Number of agents involved in the request
- **`agent_types`**: List of agent types used
- **`priorities`**: List of priorities for the requests
- **`router_overhead_ms`**: Time spent in router operations
- **`total_time_ms`**: Total time for the orchestrator request
- **`successful_agents`**: Number of agents that completed successfully
- **`failed_agents`**: Number of agents that failed

## Audit Logging

All instrumentation events are logged with specific prefixes for easy parsing:

### Router Audit Logs

All router instrumentation uses the `[ROUTER_AUDIT]` prefix:

- **`SUBMIT:`**: Logged when a request is submitted
  - Format: `[ROUTER_AUDIT] SUBMIT: request_id={id} queue_size={size} priority={p} overhead_ms={ms}`
  
- **`PROCESS_START:`**: Logged when processing begins
  - Format: `[ROUTER_AUDIT] PROCESS_START: queue_size={size}`
  
- **`PRIORITY_SORT:`**: Logged when queue is sorted by priority
  - Format: `[ROUTER_AUDIT] PRIORITY_SORT: queue_size={size}`
  
- **`PERMISSION_DENIED:`**: Logged when a request is denied due to permissions
  - Format: `[ROUTER_AUDIT] PERMISSION_DENIED: request_id={id} agent_type={type}`
  
- **`PERMISSION_GRANTED:`**: Logged when a request passes permission check
  - Format: `[ROUTER_AUDIT] PERMISSION_GRANTED: request_id={id} agent_type={type}`
  
- **`AGENT_NOT_FOUND:`**: Logged when no suitable agent is found
  - Format: `[ROUTER_AUDIT] AGENT_NOT_FOUND: request_id={id} agent_type={type}`
  
- **`ERROR_CAUGHT:`**: Logged when an exception is caught
  - Format: `[ROUTER_AUDIT] ERROR_CAUGHT: request_id={id} error={error_message}`
  
- **`STATUS_RETRIEVED:`**: Logged when request status is queried
  - Format: `[ROUTER_AUDIT] STATUS_RETRIEVED: request_id={id}`

### Orchestrator Audit Logs

All orchestrator instrumentation uses the `[ORCHESTRATOR_AUDIT]` prefix:

- **`ROUTER_CALL:`**: Logged for each router interaction
  - Format: `[ORCHESTRATOR_AUDIT] ROUTER_CALL: request_id={id} [additional_fields]`
  - Additional fields may include: `agent_count`, `action`, `router_overhead_ms`, `total_time_ms`, `successful_agents`, `failed_agents`

## Decision Thresholds

The instrumentation system uses the following thresholds to determine if router simplification is safe:

### Threshold Definitions

1. **`permission_denials_threshold: 0`**
   - **Rationale**: If no requests are being denied due to permissions, the permission checking logic may be unnecessary
   - **Pass Condition**: `permission_denials == 0`

2. **`priority_sorts_threshold: 0`**
   - **Rationale**: If the queue is never sorted by priority, priority-based sorting can be removed
   - **Pass Condition**: `priority_sorts == 0`

3. **`queue_always_zero: true`**
   - **Rationale**: If the queue is always empty (size 0), queuing logic may be unnecessary
   - **Pass Condition**: `max(queue_size) == 0`

4. **`router_overhead_threshold_ms: 5.0`**
   - **Rationale**: If router overhead is minimal (< 5ms average), complexity may not be justified
   - **Pass Condition**: `average_overhead_ms <= 5.0`

5. **`agent_not_found_threshold: 0`**
   - **Rationale**: If agents are always found, agent discovery logic may be simplified
   - **Pass Condition**: `agent_not_found_count == 0`

6. **`errors_caught_threshold: 0`**
   - **Rationale**: If no errors are caught in router, error handling may be simplified
   - **Pass Condition**: `errors_caught == 0`

## Using the Analysis Script

The `scripts/analyze_router_instrumentation.py` script parses instrumentation logs and generates a threshold-based analysis report.

### Basic Usage

```bash
# Analyze default log file (logs/app.log)
python scripts/analyze_router_instrumentation.py

# Analyze specific log file
python scripts/analyze_router_instrumentation.py --log-file logs/custom.log

# Generate JSON report
python scripts/analyze_router_instrumentation.py --output reports/router_analysis.json

# Print human-readable summary
python scripts/analyze_router_instrumentation.py --human-readable
```

### Script Output

The script generates a JSON report with:

1. **Summary**: Overall pass/fail status and totals
2. **Metrics**: All tracked metrics with computed statistics
3. **Threshold Evaluation**: Pass/fail status for each threshold
4. **Recommendation**: Whether simplification is safe

Example output structure:

```json
{
  "timestamp": "2025-11-19T12:00:00",
  "log_file": "logs/app.log",
  "summary": {
    "all_thresholds_passed": true,
    "total_submits": 100,
    "total_processes": 100,
    "total_router_calls": 100
  },
  "metrics": {
    "submit_count": 100,
    "process_count": 100,
    "permission_denials": 0,
    "priority_sorts": 0,
    "average_queue_size_at_submit": 0.0,
    "average_router_overhead_ms": 2.5
  },
  "threshold_evaluation": {
    "permission_denials": {
      "metric": 0,
      "threshold": 0,
      "pass": true,
      "message": "Permission denials: 0 (threshold: 0)"
    },
    ...
  },
  "recommendation": "✅ All thresholds passed. Router simplification is SAFE to proceed."
}
```

## Interpreting Results

### All Thresholds Pass

If all thresholds pass:
- ✅ Router simplification is **SAFE** to proceed
- The router complexity is not being used in practice
- Removing features will not break existing functionality
- Overhead is minimal

### Some Thresholds Fail

If any threshold fails:
- ❌ **DO NOT** simplify router yet
- Review which thresholds failed and why
- Consider:
  - Are the failures expected in your use case?
  - Should thresholds be adjusted?
  - Is the feature actually needed?

### Common Scenarios

#### Queue Always Empty
- **Observation**: `max_queue_size == 0`
- **Implication**: Requests are processed immediately, no queuing needed
- **Action**: Can remove queue management logic

#### No Priority Sorts
- **Observation**: `priority_sorts == 0`
- **Implication**: Priority-based sorting never occurs
- **Action**: Can remove priority sorting logic

#### No Permission Denials
- **Observation**: `permission_denials == 0`
- **Implication**: All requests pass permission checks
- **Action**: Permission checking may be redundant (but verify security requirements)

#### Low Router Overhead
- **Observation**: `average_overhead_ms < 5.0`
- **Implication**: Router operations are fast
- **Action**: Overhead is acceptable, but simplification may still be beneficial for code maintainability

## Accessing Metrics Programmatically

### From RequestRouter

```python
from agents.core.agent_framework import RequestRouter

router = RequestRouter(agent_factory)
report = router.get_instrumentation_report()

print(report['summary'])
print(report['statistics'])
```

### From AnalyticsOrchestrator

```python
from agents.analytics_orchestrator import AnalyticsOrchestrator

orchestrator = AnalyticsOrchestrator()
status = orchestrator.get_system_status()

router_metrics = status['request_router']['instrumentation']
print(router_metrics)
```

## Best Practices

1. **Run Analysis Regularly**: Analyze logs after significant usage periods
2. **Baseline First**: Establish baseline metrics before making changes
3. **Compare Over Time**: Track metrics over time to detect changes
4. **Test Edge Cases**: Ensure instrumentation captures edge cases
5. **Review Thresholds**: Adjust thresholds based on your specific requirements

## Troubleshooting

### No Logs Found

If the analysis script finds no logs:
- Verify log file path is correct
- Check that instrumentation is enabled (should be by default)
- Ensure logs are being written (check file permissions)

### Metrics Seem Incorrect

If metrics don't match expectations:
- Verify log parsing patterns are correct
- Check for log format changes
- Review audit log format consistency

### Thresholds Too Strict/Loose

If thresholds don't match your use case:
- Adjust thresholds in the analysis script
- Document rationale for threshold changes
- Consider use-case-specific thresholds

## Next Steps

After instrumentation analysis:

1. **If thresholds pass**: Proceed with router simplification
2. **If thresholds fail**: Investigate why and adjust approach
3. **Document decisions**: Record why simplification is safe/unsafe
4. **Monitor after changes**: Re-run analysis after simplification to verify

## Related Documentation

- `AGENTS.md`: Agent system architecture
- `agents/core/agent_framework.py`: RequestRouter implementation
- `agents/analytics_orchestrator.py`: AnalyticsOrchestrator implementation

