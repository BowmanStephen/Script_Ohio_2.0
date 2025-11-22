# Codebase Consolidation Migration Guide

**Date**: 2025-11-19  
**Goal**: Simplify codebase by removing unused complexity (80% reduction)

## Overview

Analysis revealed that many sophisticated patterns were created but never used in production:
- **ContextManager/Role System**: Only used in one validation script
- **StateAwareAnalyticsSession**: Only used in AnalyticsOrchestrator (which is being simplified)
- **WorkflowAutomatorAgent**: Defined but never called
- **AsyncAgentOrchestrator**: Defined but never used

**What actually works**: `WeeklyAnalysisOrchestrator` pattern - direct agent instantiation and `execute_task()` calls.

## Migration Path

### For Users of AnalyticsOrchestrator

**Before** (complex):
```python
from agents.analytics_orchestrator import AnalyticsOrchestrator, AnalyticsRequest

orchestrator = AnalyticsOrchestrator()
request = AnalyticsRequest(
    user_id="user_001",
    query="Analyze Ohio State",
    query_type="analysis",
    parameters={},
    context_hints={"role": "analyst"}  # Not actually used
)
response = orchestrator.process_analytics_request(request)
```

**After** (simplified):
```python
# Option 1: Use simplified orchestrator (backward compatible)
from agents.simplified_analytics_orchestrator import SimplifiedAnalyticsOrchestrator as AnalyticsOrchestrator, AnalyticsRequest

# Option 2: Use WeeklyAnalysisOrchestrator pattern (recommended)
from agents.weekly_analysis_orchestrator import WeeklyAnalysisOrchestrator

orchestrator = WeeklyAnalysisOrchestrator(week=13, season=2025)
result = orchestrator.run_complete_analysis()
```

### For Users of ContextManager

**Before**:
```python
from agents.core.context_manager import ContextManager, UserRole

cm = ContextManager()
role = cm.detect_user_role(context_hints)
context = cm.load_context_for_role(role, context_hints)
```

**After**:
```python
# Remove role detection - not needed
# Pass parameters directly to agents
context = {
    'user_id': user_id,
    'query': query,
    'parameters': parameters
}
```

### For Users of StateAwareAnalyticsSession

**Before**:
```python
from agents.state_aware_analytics_system import StateAwareAnalyticsSession

session = StateAwareAnalyticsSession(session_id="session_001", user_id="user_001")
session.add_conversation_turn(query, response, agent_id)
session.save_state()
```

**After**:
```python
# Use simple in-memory tracking if needed
session_history = []
session_history.append({
    'query': query,
    'response': response,
    'timestamp': datetime.now().isoformat()
})
# No persistence needed - weekly analysis is stateless
```

### For Users of WorkflowAutomatorAgent

**Before**:
```python
from agents.workflow_automator_agent import WorkflowAutomatorAgent

workflow_agent = WorkflowAutomatorAgent(agent_id="workflow_001")
result = workflow_agent.execute_request(workflow_request)
```

**After**:
```python
# Use direct agent calls in sequence (see WeeklyAnalysisOrchestrator pattern)
from agents.weekly_matchup_analysis_agent import WeeklyMatchupAnalysisAgent
from agents.weekly_prediction_generation_agent import WeeklyPredictionGenerationAgent

matchup_agent = WeeklyMatchupAnalysisAgent(week=13, season=2025)
prediction_agent = WeeklyPredictionGenerationAgent(week=13, season=2025)

result1 = matchup_agent.execute_task({})
result2 = prediction_agent.execute_task({})
```

### For Users of AsyncAgentOrchestrator

**Before**:
```python
from agents.async_agent_framework import AsyncAgentOrchestrator

orchestrator = AsyncAgentOrchestrator()
await orchestrator.start()
await orchestrator.submit_request(request)
```

**After**:
```python
# Use synchronous execution (works fine for weekly analysis)
from agents.weekly_analysis_orchestrator import WeeklyAnalysisOrchestrator

orchestrator = WeeklyAnalysisOrchestrator(week=13, season=2025)
result = orchestrator.run_complete_analysis()  # Synchronous
```

## New Template Pattern

For creating new orchestrators, use this template:

```python
from agents.core.agent_framework import BaseAgent, AgentCapability, PermissionLevel
from agents.some_agent import SomeAgent

class MyOrchestrator(BaseAgent):
    def __init__(self, agent_id: str = None, tool_loader=None):
        super().__init__(agent_id, "My Orchestrator", PermissionLevel.ADMIN, tool_loader)
        
        # Direct agent instantiation (no factory complexity)
        self.some_agent = SomeAgent(agent_id="sub_agent_1", tool_loader=tool_loader)
    
    def run_analysis(self):
        # Direct calls
        result = self.some_agent.execute_task({})
        return result
```

See `agents/orchestrator_template.py` for complete example.

## Deprecation Timeline

- **Week 1 (2025-11-19)**: Deprecation warnings added
- **Week 2-3**: Migration to simplified patterns
- **Week 4 (2025-12-19)**: Remove deprecated components

## Files to Update

### High Priority (Production Code)
- [x] `scripts/validate_cfbd_pipeline.py` - Updated to use SimplifiedAnalyticsOrchestrator
- [ ] `agents/analytics_orchestrator.py` - Replace with simplified version
- [ ] Any scripts that import ContextManager/StateAware

### Medium Priority (Documentation)
- [ ] `AGENTS.md` - Update examples
- [ ] `.cursorrules` - Update patterns
- [ ] Documentation files referencing deprecated components

### Low Priority (Tests)
- [ ] Test files that test deprecated components
- [ ] Update test imports

## Validation

After migration, verify:
```bash
# Weekly analysis still works
python scripts/run_weekly_analysis.py --week 13

# Validation script works
python scripts/validate_cfbd_pipeline.py

# All tests pass
python -m pytest tests/ -v
```

## Questions?

- See `agents/weekly_analysis_orchestrator.py` for the pattern that actually works
- See `agents/simplified_analytics_orchestrator.py` for simplified orchestrator
- See `agents/orchestrator_template.py` for creating new orchestrators

