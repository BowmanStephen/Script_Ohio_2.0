## Agent Workflow Runbook

### Overview

The Analytics Orchestrator coordinates specialized agents to satisfy user
requests.  Each run should follow the checklist below to ensure consistent
context, observability, and recovery.

### 1. Initialize observability

```python
from src.observability import configure_logging
configure_logging(service_name="agent_runs", environment="production")
```

All agents rely on the structured logger + taxonomy automatically once this
call executes.

### 2. Register capabilities

```python
from agents.core.agent_framework import AgentFactory
from agents.analytics_orchestrator import AnalyticsOrchestrator

factory = AgentFactory()
factory.register_agent_class("cfbd_integration", CFBDIntegrationAgent)
factory.register_agent_class("model_execution", ModelExecutionEngine)
```

Ensure new agents are added to `AGENTS.md` as well so CI smoke tests pick
them up.

### 3. Execute actions

```python
orchestrator = AnalyticsOrchestrator(agent_factory=factory)
response = orchestrator.handle_request(
    agent_type="weekly_matchup_analysis",
    action="analyze_matchups",
    parameters={"week": 14, "season": 2025},
    user_context={"role": "analyst"},
)
```

### 4. Error handling

- Decorate risky entrypoints with `@handle_errors(...)`.
- When catching exceptions manually, instantiate an `ErrorReport` and send
  it to `ObservabilityHub` for parity with automated flows.

### 5. Telemetry + artifacts

- Emit `ObservabilityHub.instance().set_metric(...)` for latency or cache
  hit-rate measurements.
- Persist agent outputs under `reports/` (Markdown summaries) and
  `analysis/weekXX/` (JSON data) so downstream notebooks can consume them.

### 6. Regression safety nets

- Run `python3 agents/test_agent_system.py` before landing changes touching
  the orchestrator or shared base classes.
- Launch the UI smoke test (`npm run build && npm run preview`) when adding
  new agent capabilities referenced by the front-end.

