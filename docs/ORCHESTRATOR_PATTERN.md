# Orchestrator Pattern Guide

## Overview

This document describes the recommended pattern for creating orchestrators in the Script Ohio 2.0 agent system. The pattern is based on `WeeklyAnalysisOrchestrator`, which has proven to be simple, maintainable, and effective in production.

## Key Principles

1. **Inherit from BaseAgent** - For capability definition and framework integration
2. **Direct Agent Instantiation** - No factory/router complexity
3. **Direct execute_task() Calls** - Simple, straightforward execution
4. **No Context/State Management** - Stateless execution
5. **No Workflow Complexity** - Direct agent calls instead of workflow automation
6. **Simple Error Handling** - Clear status tracking and error reporting

## Reference Implementation

The `WeeklyAnalysisOrchestrator` (`agents/weekly_analysis_orchestrator.py`) is the reference implementation. Study it before creating new orchestrators.

## Template

See `agents/orchestrator_template.py` for a complete template you can copy and modify.

## Pattern Structure

### 1. Class Definition

```python
from agents.core.agent_framework import BaseAgent, AgentCapability, PermissionLevel

class YourOrchestrator(BaseAgent):
    """Orchestrator description"""
    
    def __init__(self, param1: str, param2: int = 2025, agent_id: Optional[str] = None):
        # Initialize parameters
        self.param1 = param1
        self.param2 = param2
        
        # Generate agent_id if not provided
        if agent_id is None:
            agent_id = f"{param1}_orchestrator"
        
        # Call BaseAgent.__init__()
        super().__init__(
            agent_id=agent_id,
            name=f"{param1} Orchestrator",
            permission_level=PermissionLevel.ADMIN,
        )
        
        # Directly instantiate sub-agents (no factory/router)
        self.agent1 = SomeAgent(param1=param1, param2=param2)
        self.agent2 = AnotherAgent(param1=param1)
```

### 2. Capability Definition

```python
def _define_capabilities(self) -> List[AgentCapability]:
    """Define orchestrator capabilities"""
    return [
        AgentCapability(
            name="run_complete_analysis",
            description="Run complete analysis pipeline",
            permission_required=PermissionLevel.ADMIN,
            tools_required=["analysis", "validation"],
            data_access=["data/", "analysis/"],
            execution_time_estimate=30.0,
        ),
    ]
```

### 3. Action Execution

```python
def _execute_action(self, action: str, parameters: Dict[str, Any],
                   user_context: Dict[str, Any]) -> Dict[str, Any]:
    """Execute orchestrator actions"""
    if action == "run_complete_analysis":
        return self.run_complete_analysis(parameters, user_context)
    else:
        raise ValueError(f"Unknown action: {action}")
```

### 4. Main Analysis Method

```python
def run_complete_analysis(self, parameters: Dict[str, Any] = None,
                         user_context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Run complete analysis pipeline"""
    try:
        results = {
            'start_time': datetime.now().isoformat(),
            'steps_completed': [],
            'steps_failed': [],
            'final_status': 'in_progress'
        }
        
        # Step 1: Direct agent call
        try:
            step1_result = self.agent1.execute_task(parameters or {})
            results['step1'] = step1_result
            results['steps_completed'].append('step1')
        except Exception as e:
            logger.error(f"Step 1 failed: {e}")
            results['step1'] = {'status': 'error', 'error': str(e)}
            results['steps_failed'].append('step1')
        
        # Step 2: Direct agent call
        try:
            step2_result = self.agent2.execute_task(parameters or {})
            results['step2'] = step2_result
            results['steps_completed'].append('step2')
        except Exception as e:
            logger.error(f"Step 2 failed: {e}")
            results['step2'] = {'status': 'error', 'error': str(e)}
            results['steps_failed'].append('step2')
        
        # Determine final status
        if len(results['steps_failed']) == 0:
            results['final_status'] = 'success'
        elif len(results['steps_completed']) > 0:
            results['final_status'] = 'partial_success'
        else:
            results['final_status'] = 'failed'
        
        results['end_time'] = datetime.now().isoformat()
        return results
        
    except Exception as e:
        logger.error(f"Analysis pipeline failed: {e}")
        return {
            'final_status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }
```

## Anti-Patterns to Avoid

### ❌ DON'T: Use ContextManager

```python
# BAD - ContextManager is deprecated
from agents.core.context_manager import ContextManager
self.context_manager = ContextManager()
user_role = self.context_manager.detect_user_role(context_hints)
```

**Why:** ContextManager is deprecated. Production code uses direct agent instantiation without role-based filtering.

**Instead:** Use direct agent calls without context management.

### ❌ DON'T: Use StateAwareAnalyticsSession

```python
# BAD - StateAwareAnalyticsSession is deprecated
from agents.state_aware_analytics_system import StateAwareAnalyticsSession
session = StateAwareAnalyticsSession(session_id, user_id)
```

**Why:** StateAwareAnalyticsSession is deprecated. Production code uses stateless execution.

**Instead:** Use stateless execution - no session management needed.

### ❌ DON'T: Use WorkflowAutomatorAgent

```python
# BAD - WorkflowAutomatorAgent is deprecated
from agents.workflow_automator_agent import WorkflowAutomatorAgent
workflow_agent = WorkflowAutomatorAgent('workflow_001')
workflow_agent.execute_workflow(...)
```

**Why:** WorkflowAutomatorAgent is deprecated. Production code uses direct agent calls.

**Instead:** Call agents directly in sequence.

### ❌ DON'T: Use ToolLoader

```python
# BAD - ToolLoader is deprecated
from agents.core.tool_loader import ToolLoader
tool_loader = ToolLoader()
super().__init__(agent_id, name, permission_level, tool_loader=tool_loader)
```

**Why:** ToolLoader is deprecated. Agents perform work directly without tool abstraction.

**Instead:** Agents should perform work directly in their methods.

### ❌ DON'T: Use AgentFactory/RequestRouter for Simple Orchestration

```python
# BAD - Unnecessary complexity for simple orchestration
self.agent_factory = AgentFactory()
self.request_router = RequestRouter(self.agent_factory)
agent_request = AgentRequest(...)
self.request_router.submit_request(agent_request)
```

**Why:** Adds unnecessary complexity. Direct instantiation and calls are simpler.

**Instead:** Directly instantiate agents and call execute_task().

## Migration Guide

### From Old AnalyticsOrchestrator Pattern

If you have code using the old `AnalyticsOrchestrator` pattern with context/state management:

1. **Remove ContextManager usage:**
   ```python
   # OLD
   user_role = self.context_manager.detect_user_role(context_hints)
   context = self.context_manager.load_context_for_role(user_role, context_hints)
   
   # NEW
   context = {'user_id': user_id, 'role': context_hints.get('role', 'analyst')}
   ```

2. **Remove StateAwareAnalyticsSession:**
   ```python
   # OLD
   session = StateAwareAnalyticsSession(session_id, user_id)
   session.add_conversation_turn(query, response)
   
   # NEW
   # No session management needed - stateless execution
   ```

3. **Remove WorkflowAutomatorAgent:**
   ```python
   # OLD
   workflow_agent.execute_workflow(workflow_definition)
   
   # NEW
   # Call agents directly in sequence
   result1 = agent1.execute_task({})
   result2 = agent2.execute_task({})
   ```

4. **Simplify agent instantiation:**
   ```python
   # OLD
   self.agent_factory.create_agent("agent_type", "agent_id")
   agent = self.agent_factory.agents.get("agent_id")
   
   # NEW
   self.agent = SomeAgent(param1=param1, param2=param2)
   ```

## Examples

### WeeklyAnalysisOrchestrator

See `agents/weekly_analysis_orchestrator.py` for the reference implementation.

### Template

See `agents/orchestrator_template.py` for a complete template.

## Best Practices

1. **Keep it Simple** - Direct calls are better than complex routing
2. **Clear Error Handling** - Track steps completed/failed clearly
3. **No Hidden State** - All state should be explicit in results
4. **Document Capabilities** - Use _define_capabilities() properly
5. **Test Each Step** - Each agent call should be testable independently

## Questions?

- Reference: `agents/weekly_analysis_orchestrator.py`
- Template: `agents/orchestrator_template.py`
- Deprecated components: See deprecation warnings in code

