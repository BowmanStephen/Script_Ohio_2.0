# Migrating to `AnalyticsOrchestrator`

The legacy `agents.system` stack (master orchestrator, registry, task manager, legacy
workflow helpers) has been superseded by `agents.analytics_orchestrator`. All new
development should target the modern orchestrator and the five production agents.

## Legacy Usage (deprecated)
```python
from system.master_orchestrator import MasterOrchestratorAgent
from system.core.agent_registry import AgentRegistry

orchestrator = MasterOrchestratorAgent()
registry = AgentRegistry()
```

## Modern Usage
```python
from agents.analytics_orchestrator import AnalyticsOrchestrator, AnalyticsRequest

orchestrator = AnalyticsOrchestrator()

request = AnalyticsRequest(
    user_id="demo_user",
    query="Predict Ohio State vs Michigan",
    query_type="prediction",
    parameters={"teams": ["Ohio State", "Michigan"]},
    context_hints={"role": "analyst"}
)

response = orchestrator.process_analytics_request(request)
print(response.status, response.insights)
```

### Key Differences
- **Factory + router built in**: No need for manual registry wiring.
- **Context-aware**: Automatically loads user context, conversation history, and tool
  capabilities.
- **Production agents out of the box**: Learning navigator, model execution engine,
  insight generator, workflow automator, conversational AI.
- **Extensible**: Register new agents through `AgentFactory` using the modern
  `BaseAgent` contract with capability validation and permission enforcement.

### Migration Checklist
1. Replace `from system...` imports with `from agents.analytics_orchestrator...`.
2. Recreate orchestrator requests using `AnalyticsRequest`.
3. Remove references to legacy registry/task manager modules.
4. Register any custom agents via `AgentFactory.register_agent_class`.
5. Delete or archive old logs/demos once new flows are validated.

