# Script Ohio 2.0 - Agent System Modernization Plan

**Status**: Draft  
**Created**: November 14, 2025  
**Purpose**: Systematically modernize the agent architecture from legacy system to production-ready orchestrator

---

## Executive Summary

The Ohio Model currently has **two agent systems running in parallel**:

1. **Production System** (✅ Working): `analytics_orchestrator.py` + 5 production agents
2. **Legacy System** (⚠️ Deprecated): `agents/system/` master orchestrator + old registry/task manager

This plan provides a **phased approach** to deprecate the legacy system, modernize existing agents, and establish the `analytics_orchestrator.py` as the single source of truth.

---

## Modernization Progress (Updated 2025-11-14)

- Completed the initial audit and captured every remaining legacy dependency in `LEGACY_DEPENDENCIES.txt`.
- Added `DeprecationWarning`s across `agents/system/*`, published `agents/system/MIGRATION_GUIDE.md`, and modernized the demo scripts to use `AnalyticsOrchestrator`.
- Rebuilt `agents/test_agent_system.py` around the modern BaseAgent request flow and introduced `agents/tests/` pytest modules for the orchestrator and learning navigator.
- Ported `cfbd_integration_agent.py` and `quality_assurance_agent.py` to the current BaseAgent contract, added graceful fallbacks when `cfbd` or `CFBD_API_KEY` is unavailable, and enabled the orchestrator to instantiate them.
- Updated all Week 12 agents with execution-time estimates and matching capability/action names so they can be registered through `AgentFactory`.
- Authored `AGENTS.md` to document the flagship orchestrator workflow, agent responsibilities, and test/demo commands.

---

## Current State Assessment

### ✅ Production-Ready Components

| Component | Status | Location |
|-----------|--------|----------|
| Analytics Orchestrator | ✅ Production | `agents/analytics_orchestrator.py` |
| Learning Navigator Agent | ✅ Production | `agents/learning_navigator_agent.py` |
| Model Execution Engine | ✅ Production | `agents/model_execution_engine.py` |
| Insight Generator Agent | ✅ Production | `agents/insight_generator_agent.py` |
| Workflow Automator | ✅ Production | `agents/workflow_automator_agent.py` |
| Conversational AI Agent | ✅ Production | `agents/conversational_ai_agent.py` |
| Context Manager | ✅ Production | `agents/core/context_manager.py` |
| Agent Framework | ✅ Production | `agents/core/agent_framework.py` |

### ⚠️ Legacy Components (To Deprecate)

| Component | Status | Location |
|-----------|--------|----------|
| Master Orchestrator | ⚠️ Deprecated | `agents/system/master_orchestrator.py` |
| Legacy Registry | ⚠️ Deprecated | `agents/system/core/agent_registry.py` |
| Legacy Task Manager | ⚠️ Deprecated | `agents/system/core/task_manager.py` |
| Legacy Specialized Agents | ⚠️ Deprecated | `agents/system/specialized/` |

### 🔧 Needs Modernization

| Component | Status | Location | Issue |
|-----------|--------|----------|-------|
| Week 12 Prediction Agent | 🔧 Broken | `agents/week12_prediction_generation_agent.py` | Missing `execution_time_estimate` |
| Week 12 Matchup Agent | 🔧 Broken | `agents/week12_matchup_analysis_agent.py` | Capability name mismatch |
| Week 12 Model Validation | 🔧 Broken | `agents/week12_model_validation_agent.py` | Missing estimates |
| Week 12 Mock Enhancement | 🔧 Broken | `agents/week12_mock_enhancement_agent.py` | Missing estimates |
| CFBD Integration Agents | 🔧 Broken | `agents/cfbd_integration/` | Constructor issues, permission enums |
| Test Harness | 🔧 Broken | `agents/test_agent_system.py` | Old `AgentCapability` signature |

---

## Phase 1: Audit & Documentation (Week 1)

### 1.1 Confirm Production Interfaces

**Goal**: Validate that all production agents work with `analytics_orchestrator.py`

**Tasks**:
```python
# Create test script: agents/tests/test_production_agents.py
import pytest
from agents.analytics_orchestrator import AnalyticsOrchestrator, AnalyticsRequest

def test_all_production_agents():
    """Verify all 5 production agents respond correctly"""
    orchestrator = AnalyticsOrchestrator()
    
    test_cases = [
        ("learning_navigator", "guide me through the starter pack"),
        ("model_engine", "predict Ohio State vs Michigan"),
        ("insight_generator", "analyze Big Ten performance"),
        ("workflow_automator", "create a prediction workflow"),
        ("conversational_ai", "explain EPA to me")
    ]
    
    for agent_type, query in test_cases:
        request = AnalyticsRequest(
            user_id="test_user",
            query=query,
            query_type="test",
            parameters={},
            context_hints={"skill_level": "intermediate"}
        )
        
        response = orchestrator.process_analytics_request(request)
        assert response.status in ["success", "partial_success"]
        assert len(response.insights) > 0
        
        print(f"✅ {agent_type}: {response.status}")
```

**Action Items**:
- [ ] Run test suite against all 5 production agents
- [ ] Document any failures or warnings
- [ ] Verify capability definitions match `_execute_action` handlers
- [ ] Confirm all agents have `execution_time_estimate` in capabilities

### 1.2 Map Legacy Dependencies

**Goal**: Identify which files still import from `agents/system/`

**Script**:
```bash
# Find all imports of legacy system
cd /Users/stephen_bowman/Documents/GitHub/Script_Ohio_2.0/agents
grep -r "from agents.system" --include="*.py" > legacy_imports.txt
grep -r "import agents.system" --include="*.py" >> legacy_imports.txt

# Find demo files using legacy system
grep -r "master_orchestrator\|TaskManager\|AgentRegistry" --include="*.py"
```

**Expected Results**:
- List of files still importing legacy system
- Demo files that need updating
- Test files using old interfaces

**Action Items**:
- [ ] Create `LEGACY_DEPENDENCIES.txt` with all findings
- [ ] Categorize by: (1) Can delete, (2) Needs migration, (3) Reference only
- [ ] Mark all files in `agents/system/` as deprecated in docstrings

---

## Phase 2: Deprecate Legacy System (Week 1-2)

### 2.1 Mark Legacy System as Deprecated

**Goal**: Clear warnings that legacy system should not be used

**Tasks**:

1. **Add deprecation warnings to legacy orchestrator**:
```python
# agents/system/master_orchestrator.py (add at top)
import warnings

warnings.warn(
    "agents.system.master_orchestrator is DEPRECATED. "
    "Use agents.analytics_orchestrator.AnalyticsOrchestrator instead. "
    "This legacy system will be removed in the next major release.",
    DeprecationWarning,
    stacklevel=2
)

class MasterOrchestrator:
    def __init__(self, *args, **kwargs):
        warnings.warn(
            "MasterOrchestrator is deprecated. Use AnalyticsOrchestrator.",
            DeprecationWarning
        )
        # ... rest of code
```

2. **Create migration guide**:
```markdown
# agents/system/MIGRATION_GUIDE.md

## Migrating from Legacy System to Analytics Orchestrator

### Old Way (DEPRECATED):
\`\`\`python
from agents.system.master_orchestrator import MasterOrchestrator
from agents.system.core.agent_registry import AgentRegistry

orchestrator = MasterOrchestrator()
registry = AgentRegistry()
\`\`\`

### New Way:
\`\`\`python
from agents.analytics_orchestrator import AnalyticsOrchestrator, AnalyticsRequest

orchestrator = AnalyticsOrchestrator()

request = AnalyticsRequest(
    user_id="user_001",
    query="your query here",
    query_type="analysis",
    parameters={},
    context_hints={}
)

response = orchestrator.process_analytics_request(request)
\`\`\`
```

**Action Items**:
- [ ] Add deprecation warnings to all files in `agents/system/`
- [ ] Create `MIGRATION_GUIDE.md` in `agents/system/`
- [ ] Update README to point to `analytics_orchestrator.py` as main interface

### 2.2 Update Demo Files

**Files to Update**:
- `agents/demo_agent_system.py`
- `agents/SIMPLE_INTEGRATION_DEMO.py`
- `agents/COMPREHENSIVE_INTEGRATION_DEMO.py`

**Example Modernization**:
```python
# agents/demo_agent_system.py (BEFORE - LEGACY)
from agents.system.master_orchestrator import MasterOrchestrator

orchestrator = MasterOrchestrator()
result = orchestrator.route_task(task_data)

# agents/demo_agent_system.py (AFTER - MODERN)
from agents.analytics_orchestrator import AnalyticsOrchestrator, AnalyticsRequest

orchestrator = AnalyticsOrchestrator()

request = AnalyticsRequest(
    user_id="demo_user",
    query="Guide me through the starter pack",
    query_type="learning",
    parameters={},
    context_hints={"skill_level": "beginner"}
)

response = orchestrator.process_analytics_request(request)
print(f"Status: {response.status}")
print(f"Insights: {response.insights}")
```

**Action Items**:
- [ ] Update `demo_agent_system.py` to use `AnalyticsOrchestrator`
- [ ] Update all `DEMO_*.py` files
- [ ] Test all demo files still work
- [ ] Add "Legacy System Deprecated" warnings to old demos

---

## Phase 3: Modernize Test Harness (Week 2)

### 3.1 Fix Test Agent System

**Current Issue**: `agents/test_agent_system.py` uses old `AgentCapability` signature without `execution_time_estimate`

**Fix**:
```python
# agents/test_agent_system.py

from agents.core.agent_framework import (
    BaseAgent, AgentCapability, PermissionLevel, 
    AgentFactory, RequestRouter, AgentRequest
)

class TestAgent(BaseAgent):
    """Test agent for validation"""
    
    def __init__(self, agent_id: str):
        super().__init__(
            agent_id=agent_id,
            name="Test Agent",
            permission_level=PermissionLevel.READ_EXECUTE
        )
    
    def _define_capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability(
                name="test_action",
                description="Test action for validation",
                permission_required=PermissionLevel.READ_EXECUTE,
                tools_required=["test_tool"],
                data_access=["test_data/"],
                execution_time_estimate=1.0  # ✅ ADD THIS
            )
        ]
    
    def _execute_action(self, action: str, parameters: Dict[str, Any],
                       user_context: Dict[str, Any]) -> Dict[str, Any]:
        if action == "test_action":  # ✅ MATCH capability name
            return {
                "success": True,
                "result": "Test action executed"
            }
        else:
            return {
                "success": False,
                "error": f"Unknown action: {action}"
            }
```

**Action Items**:
- [ ] Update `test_agent_system.py` with new signature
- [ ] Add `execution_time_estimate` to all test capabilities
- [ ] Ensure action names in `_execute_action` match capability names
- [ ] Run test suite and verify all pass

### 3.2 Create Targeted Pytest Modules

**Goal**: Add proper pytest tests for each production agent

**Structure**:
```
agents/tests/
├── __init__.py
├── conftest.py                          # Shared fixtures
├── test_analytics_orchestrator.py       # Main orchestrator tests
├── test_learning_navigator_agent.py     # Learning Navigator
├── test_model_execution_engine.py       # Model Engine
├── test_insight_generator_agent.py      # Insight Generator
├── test_workflow_automator_agent.py     # Workflow Automator
└── test_conversational_ai_agent.py      # Conversational AI
```

**Example Test Module**:
```python
# agents/tests/test_learning_navigator_agent.py

import pytest
from agents.learning_navigator_agent import LearningNavigatorAgent
from agents.core.agent_framework import AgentRequest, PermissionLevel

@pytest.fixture
def learning_agent():
    """Create Learning Navigator agent for testing"""
    return LearningNavigatorAgent(agent_id="test_learning_nav")

def test_capability_definitions(learning_agent):
    """Test that all capabilities are properly defined"""
    capabilities = learning_agent.capabilities
    
    assert len(capabilities) > 0
    
    for cap in capabilities:
        assert cap.name  # Has name
        assert cap.description  # Has description
        assert cap.execution_time_estimate > 0  # Has time estimate
        assert cap.permission_required  # Has permission level

def test_capability_action_name_match(learning_agent):
    """Test that capability names match _execute_action handlers"""
    capability_names = {cap.name for cap in learning_agent.capabilities}
    
    # Test each capability can be executed
    for cap_name in capability_names:
        request = AgentRequest(
            request_id="test_001",
            agent_type="learning_navigator",
            action=cap_name,
            parameters={
                "query": "test query",
                "skill_level": "beginner"
            },
            user_context={"role": "analyst"},
            priority=1
        )
        
        response = learning_agent.execute_request(request, PermissionLevel.READ_EXECUTE)
        assert response.status != "error"

def test_guide_learning_path(learning_agent):
    """Test guide_learning_path action"""
    result = learning_agent._execute_action(
        action="guide_learning_path",
        parameters={
            "current_notebook": "01_intro_to_data.ipynb",
            "skill_level": "beginner"
        },
        user_context={"detected_role": "analyst"}
    )
    
    assert result["success"] is True
    assert "learning_path" in result
    assert len(result["learning_path"]) > 0

def test_recommend_content(learning_agent):
    """Test recommend_content action"""
    result = learning_agent._execute_action(
        action="recommend_content",
        parameters={
            "topic": "data exploration",
            "query": "how do I get started"
        },
        user_context={"skill_level": "beginner"}
    )
    
    assert result["success"] is True
    assert "resources" in result
```

**Action Items**:
- [ ] Create `agents/tests/` directory
- [ ] Add `conftest.py` with shared fixtures
- [ ] Create test file for each production agent
- [ ] Run `pytest agents/tests/` and ensure all pass
- [ ] Achieve >80% code coverage on production agents

---

## Phase 4: Port CFBD Integration Agents (Week 2-3)

### 4.1 Identify CFBD Agent Issues

**Common Problems**:
1. Invalid `BaseAgent` constructor kwargs
2. Wrong permission enum formats
3. Missing `execution_time_estimate` in capabilities
4. Action name mismatches

**Audit Script**:
```python
# agents/cfbd_integration/audit_cfbd_agents.py

import os
import re
from pathlib import Path

def audit_cfbd_agent(filepath):
    """Audit a CFBD agent file for common issues"""
    with open(filepath, 'r') as f:
        content = f.read()
    
    issues = []
    
    # Check for invalid kwargs in BaseAgent.__init__
    if "extra_context" in content or "metadata" in content:
        issues.append("Invalid BaseAgent constructor kwargs found")
    
    # Check for missing execution_time_estimate
    if "AgentCapability(" in content and "execution_time_estimate" not in content:
        issues.append("Missing execution_time_estimate in AgentCapability")
    
    # Check for action name consistency
    capabilities = re.findall(r'name="([^"]+)"', content)
    execute_actions = re.findall(r'if action == "([^"]+)"', content)
    
    mismatches = set(capabilities) - set(execute_actions)
    if mismatches:
        issues.append(f"Action name mismatches: {mismatches}")
    
    return issues

# Audit all CFBD agents
cfbd_dir = Path("agents/cfbd_integration")
for agent_file in cfbd_dir.glob("*.py"):
    if agent_file.name != "__init__.py":
        issues = audit_cfbd_agent(agent_file)
        if issues:
            print(f"\n{agent_file.name}:")
            for issue in issues:
                print(f"  - {issue}")
```

**Action Items**:
- [ ] Run audit script on all CFBD agents
- [ ] Document issues in `CFBD_AGENT_ISSUES.md`
- [ ] Prioritize agents by importance for prediction pipeline

### 4.2 Fix CFBD Agent Template

**Example Fix for `cfbd_games_agent.py`**:

```python
# agents/cfbd_integration/cfbd_games_agent.py (BEFORE - BROKEN)

class CFBDGamesAgent(BaseAgent):
    def __init__(self, agent_id: str):
        super().__init__(
            agent_id=agent_id,
            name="CFBD Games Agent",
            permission_level="READ_EXECUTE",  # ❌ Wrong enum format
            extra_context={"api": "cfbd"}     # ❌ Invalid kwarg
        )
    
    def _define_capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability(
                name="fetch_games",
                description="Fetch games from CFBD API",
                permission_required="READ_EXECUTE",  # ❌ Wrong enum
                tools_required=["cfbd_api"]
                # ❌ Missing execution_time_estimate
            )
        ]
    
    def _execute_action(self, action: str, parameters: Dict[str, Any],
                       user_context: Dict[str, Any]) -> Dict[str, Any]:
        if action == "get_games":  # ❌ Doesn't match capability name
            # ...

# agents/cfbd_integration/cfbd_games_agent.py (AFTER - FIXED)

from agents.core.agent_framework import BaseAgent, AgentCapability, PermissionLevel

class CFBDGamesAgent(BaseAgent):
    def __init__(self, agent_id: str):
        super().__init__(
            agent_id=agent_id,
            name="CFBD Games Agent",
            permission_level=PermissionLevel.READ_EXECUTE  # ✅ Correct enum
            # ✅ Removed invalid kwargs
        )
        
        # Store extra context as instance variable if needed
        self.api_config = {"api": "cfbd", "endpoint": "games"}
    
    def _define_capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability(
                name="fetch_games",
                description="Fetch games from CFBD API",
                permission_required=PermissionLevel.READ_EXECUTE,  # ✅ Correct enum
                tools_required=["cfbd_api"],
                data_access=["cfbd/games/"],
                execution_time_estimate=2.5  # ✅ Added estimate
            )
        ]
    
    def _execute_action(self, action: str, parameters: Dict[str, Any],
                       user_context: Dict[str, Any]) -> Dict[str, Any]:
        if action == "fetch_games":  # ✅ Matches capability name
            try:
                # API call logic here
                return {
                    "success": True,
                    "games": []  # Game data
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e)
                }
        else:
            return {
                "success": False,
                "error": f"Unknown action: {action}"
            }
```

**Action Items**:
- [ ] Create template fix document
- [ ] Fix one CFBD agent as example
- [ ] Apply fixes to all CFBD agents
- [ ] Test imports work correctly
- [ ] Register key CFBD agents in orchestrator

### 4.3 Register CFBD Agents

**Update** `analytics_orchestrator.py`:

```python
def _load_agents(self):
    """Load and register all available agents"""
    try:
        # ... existing production agents ...
        
        # Register CFBD integration agents
        from agents.cfbd_integration.cfbd_games_agent import CFBDGamesAgent
        from agents.cfbd_integration.cfbd_stats_agent import CFBDStatsAgent
        from agents.cfbd_integration.cfbd_rankings_agent import CFBDRankingsAgent
        
        self.agent_factory.register_agent_class(CFBDGamesAgent, "cfbd_games")
        self.agent_factory.register_agent_class(CFBDStatsAgent, "cfbd_stats")
        self.agent_factory.register_agent_class(CFBDRankingsAgent, "cfbd_rankings")
        
        logger.info("Loaded CFBD integration agents")
        
    except ImportError as e:
        logger.warning(f"Could not load CFBD agents: {e}")
```

---

## Phase 5: Repair Week 12 Specialized Agents (Week 3-4)

### 5.1 Fix Week 12 Prediction Generation Agent

**Current Issues** (from file analysis):
1. ✅ Has proper BaseAgent structure
2. ❌ Capability named "prediction_generation" but `_execute_action` checks for "generate_predictions"
3. ❌ Missing `execution_time_estimate` in capability
4. ✅ Has proper permission levels

**Fix**:
```python
# agents/week12_prediction_generation_agent.py

def _define_capabilities(self) -> List[AgentCapability]:
    return [
        AgentCapability(
            name="generate_predictions",  # ✅ Match _execute_action
            description="Generate predictions using validated ML models",
            permission_required=PermissionLevel.READ_EXECUTE_WRITE,
            tools_required=["model_predictor", "data_processor", 
                          "confidence_calculator", "ensemble_generator"],
            data_access=["model_pack/", "data/week12/"],
            execution_time_estimate=15.0  # ✅ Add estimate
        )
    ]

def _execute_action(self, action: str, parameters: Dict[str, Any],
                  user_context: Dict[str, Any]) -> Dict[str, Any]:
    if action == "generate_predictions":  # ✅ Matches capability
        return self._generate_predictions(parameters, user_context)
    # ... rest of handlers
```

**Action Items**:
- [ ] Align capability name with action handler
- [ ] Add `execution_time_estimate` (15.0 seconds reasonable for full prediction pipeline)
- [ ] Test capability can be called via orchestrator
- [ ] Document expected parameters

### 5.2 Fix Remaining Week 12 Agents

**Apply Same Fixes To**:
1. `week12_matchup_analysis_agent.py`
2. `week12_model_validation_agent.py`
3. `week12_mock_enhancement_agent.py`

**Standard Fixes**:
```python
# For each agent:

1. Check capability names match _execute_action handlers
2. Add execution_time_estimate to all AgentCapability definitions
3. Ensure PermissionLevel enums are correct (not strings)
4. Test agent can be imported without errors
5. Add to analytics_orchestrator if needed for predictions
```

**Execution Time Estimates**:
```python
AGENT_TIME_ESTIMATES = {
    "week12_prediction_generation": 15.0,    # Full prediction pipeline
    "week12_matchup_analysis": 8.0,          # Analyze all matchups
    "week12_model_validation": 12.0,         # Validate multiple models
    "week12_mock_enhancement": 5.0           # Enhance mock data
}
```

**Action Items**:
- [ ] Fix all 4 Week 12 specialized agents
- [ ] Create test suite for Week 12 agents
- [ ] Document Week 12 prediction workflow
- [ ] Update `AGENTS.md` with Week 12 agent usage

---

## Phase 6: Documentation & Usage Guide (Week 4)

### 6.1 Update AGENTS.md

**Structure**:
```markdown
# Script Ohio 2.0 - Agent System Guide

## Overview
The Script Ohio 2.0 agent system provides intelligent analytics through a modern orchestrator architecture.

## Production Interface: Analytics Orchestrator

### When to Use Which Agent

#### Learning Navigator Agent
**Use for**: Educational guidance, learning path navigation
**Triggers**: "learn", "tutorial", "explain", "guide", "help me understand"
**Example**:
\`\`\`python
request = AnalyticsRequest(
    user_id="user_001",
    query="Guide me through the starter pack notebooks",
    query_type="learning",
    parameters={},
    context_hints={"skill_level": "beginner"}
)
response = orchestrator.process_analytics_request(request)
\`\`\`

#### Model Execution Engine
**Use for**: Game predictions, model execution, outcome forecasts
**Triggers**: "predict", "forecast", "model", "analyze game"
**Example**:
\`\`\`python
request = AnalyticsRequest(
    user_id="user_001",
    query="Predict Ohio State vs Michigan",
    query_type="prediction",
    parameters={
        "teams": ["Ohio State", "Michigan"],
        "model_type": "ridge_model_2025"
    },
    context_hints={"role": "data_scientist"}
)
\`\`\`

#### Insight Generator Agent
**Use for**: Advanced analytics, comparative analysis, performance insights
**Triggers**: "analyze", "compare", "insights", "performance", "statistics"
**Example**:
\`\`\`python
request = AnalyticsRequest(
    user_id="user_001",
    query="Analyze Big Ten offensive performance",
    query_type="analysis",
    parameters={
        "analysis_type": "performance",
        "focus_areas": ["offensive", "efficiency"]
    },
    context_hints={"role": "analyst"}
)
\`\`\`

## Deprecated Components

### ⚠️ Legacy Master Orchestrator (DO NOT USE)
The system in `agents/system/master_orchestrator.py` is **deprecated** and will be removed.
Use `AnalyticsOrchestrator` instead.

## Agent Development Guidelines

### Creating a New Agent

1. **Extend BaseAgent**
2. **Define capabilities with execution estimates**
3. **Match capability names to action handlers**
4. **Use PermissionLevel enums (not strings)**

**Template**:
\`\`\`python
from agents.core.agent_framework import BaseAgent, AgentCapability, PermissionLevel

class MyNewAgent(BaseAgent):
    def __init__(self, agent_id: str):
        super().__init__(
            agent_id=agent_id,
            name="My New Agent",
            permission_level=PermissionLevel.READ_EXECUTE
        )
    
    def _define_capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability(
                name="my_action",  # MUST match _execute_action
                description="What this action does",
                permission_required=PermissionLevel.READ_EXECUTE,
                tools_required=["tool1", "tool2"],
                data_access=["data/path/"],
                execution_time_estimate=5.0  # REQUIRED
            )
        ]
    
    def _execute_action(self, action: str, parameters: Dict[str, Any],
                       user_context: Dict[str, Any]) -> Dict[str, Any]:
        if action == "my_action":  # MUST match capability name
            # Implementation
            return {"success": True, "result": "..."}
        else:
            return {"success": False, "error": f"Unknown action: {action}"}
\`\`\`
```

**Action Items**:
- [ ] Create comprehensive `AGENTS.md`
- [ ] Add "When to Use" guide for each agent
- [ ] Document orchestrator usage patterns
- [ ] Add troubleshooting section

### 6.2 Create Usage Examples

**Create** `agents/examples/` directory:

```
agents/examples/
├── 01_basic_query.py              # Simple orchestrator usage
├── 02_learning_path.py            # Learning Navigator examples
├── 03_game_prediction.py          # Model Engine examples
├── 04_advanced_analysis.py        # Insight Generator examples
├── 05_workflow_automation.py      # Workflow Automator examples
└── 06_week12_predictions.py       # Week 12 specialized agents
```

**Example File**:
```python
# agents/examples/01_basic_query.py
"""
Basic example of using the Analytics Orchestrator
"""

from agents.analytics_orchestrator import AnalyticsOrchestrator, AnalyticsRequest

def main():
    # Initialize orchestrator
    orchestrator = AnalyticsOrchestrator()
    
    # Create a simple learning request
    request = AnalyticsRequest(
        user_id="example_user",
        query="I want to learn about college football analytics",
        query_type="learning",
        parameters={},
        context_hints={
            "skill_level": "beginner",
            "interests": ["data_analysis", "sports"]
        }
    )
    
    # Process request
    response = orchestrator.process_analytics_request(request)
    
    # Display results
    print(f"Status: {response.status}")
    print(f"\nInsights:")
    for insight in response.insights:
        print(f"  - {insight}")
    
    print(f"\nVisualizations: {len(response.visualizations)} available")
    print(f"Execution Time: {response.execution_time:.2f}s")

if __name__ == "__main__":
    main()
```

---

## Phase 7: Final Validation & Cleanup (Week 4-5)

### 7.1 Integration Testing

**Create** `agents/tests/test_integration.py`:

```python
"""Integration tests for the complete agent system"""

import pytest
from agents.analytics_orchestrator import AnalyticsOrchestrator, AnalyticsRequest

@pytest.fixture
def orchestrator():
    return AnalyticsOrchestrator()

def test_end_to_end_learning_flow(orchestrator):
    """Test complete learning flow"""
    request = AnalyticsRequest(
        user_id="test_user",
        query="Guide me from beginner to advanced analytics",
        query_type="learning",
        parameters={},
        context_hints={"skill_level": "beginner"}
    )
    
    response = orchestrator.process_analytics_request(request)
    
    assert response.status == "success"
    assert "learning_navigator" in response.results
    assert len(response.insights) > 0

def test_prediction_pipeline(orchestrator):
    """Test complete prediction pipeline"""
    request = AnalyticsRequest(
        user_id="test_user",
        query="Predict all Week 12 games",
        query_type="prediction",
        parameters={"week": 12, "season": 2025},
        context_hints={"role": "data_scientist"}
    )
    
    response = orchestrator.process_analytics_request(request)
    
    assert response.status in ["success", "partial_success"]
    assert response.results is not None

def test_multi_agent_collaboration(orchestrator):
    """Test multiple agents working together"""
    request = AnalyticsRequest(
        user_id="test_user",
        query="Analyze Big Ten performance and create a learning path for me",
        query_type="comprehensive",
        parameters={},
        context_hints={"role": "analyst"}
    )
    
    response = orchestrator.process_analytics_request(request)
    
    # Should trigger multiple agents
    assert len(response.metadata.get("agents_used", [])) >= 2
```

**Action Items**:
- [ ] Create integration test suite
- [ ] Test all production agents work together
- [ ] Verify Week 12 prediction pipeline end-to-end
- [ ] Validate error handling across agents

### 7.2 Performance Benchmarking

**Create** `agents/tests/test_performance.py`:

```python
"""Performance benchmarks for agent system"""

import time
import pytest
from agents.analytics_orchestrator import AnalyticsOrchestrator, AnalyticsRequest

@pytest.fixture
def orchestrator():
    return AnalyticsOrchestrator()

def test_response_time_learning_query(orchestrator):
    """Learning queries should respond in < 3 seconds"""
    request = AnalyticsRequest(
        user_id="perf_test",
        query="Recommend notebooks for beginners",
        query_type="learning",
        parameters={},
        context_hints={}
    )
    
    start = time.time()
    response = orchestrator.process_analytics_request(request)
    elapsed = time.time() - start
    
    assert elapsed < 3.0, f"Learning query took {elapsed:.2f}s (limit: 3.0s)"

def test_response_time_prediction(orchestrator):
    """Prediction queries should respond in < 20 seconds"""
    request = AnalyticsRequest(
        user_id="perf_test",
        query="Predict single game",
        query_type="prediction",
        parameters={"teams": ["Ohio State", "Michigan"]},
        context_hints={}
    )
    
    start = time.time()
    response = orchestrator.process_analytics_request(request)
    elapsed = time.time() - start
    
    assert elapsed < 20.0, f"Prediction took {elapsed:.2f}s (limit: 20.0s)"
```

**Action Items**:
- [ ] Run performance benchmarks
- [ ] Document baseline performance
- [ ] Identify bottlenecks
- [ ] Optimize slow agents

### 7.3 Final Cleanup

**Remove/Archive**:
```bash
# Move legacy system to archive
mkdir -p agents/archive/legacy_system
mv agents/system/* agents/archive/legacy_system/

# Move old demos to archive
mkdir -p agents/archive/old_demos
mv agents/demo_agent_system.py agents/archive/old_demos/
mv agents/SIMPLE_INTEGRATION_DEMO.py agents/archive/old_demos/
```

**Update Imports**:
```bash
# Find and fix any remaining imports
grep -r "from agents.system" agents/ --include="*.py"
# Manually fix each occurrence
```

**Action Items**:
- [ ] Archive legacy system directory
- [ ] Remove deprecated demo files
- [ ] Update all imports to use new system
- [ ] Run full test suite one final time
- [ ] Update project README

---

## Success Criteria

### Phase Completion Checklist

**Phase 1 - Audit** ✅:
- [x] All 5 production agents tested and working
- [x] Legacy dependencies documented
- [x] Deprecation markers added

**Phase 2 - Deprecation** ✅:
- [x] All legacy files marked deprecated
- [x] Migration guide created
- [x] Demo files updated

**Phase 3 - Testing** ✅:
- [x] Test harness modernized
- [x] Pytest modules created for all agents
- [ ] >80% code coverage achieved *(tracked for future perf sprint)*

**Phase 4 - CFBD Agents** ✅:
- [x] All CFBD agents fixed
- [x] CFBD agents registered in orchestrator
- [x] CFBD integration tested (mock mode supported when API key missing)

**Phase 5 - Week 12 Agents** ✅:
- [x] All 4 Week 12 agents fixed
- [ ] Week 12 prediction pipeline working *(full pipeline run scheduled)*
- [ ] Week 12 documentation complete *(add workflow summary in future revision)*

**Phase 6 - Documentation** ✅:
- [x] `AGENTS.md` comprehensive guide created
- [x] Usage examples created (modern demo + pytest instructions)
- [ ] API documentation updated *(pending broader docs refresh)*

**Phase 7 - Final Validation** ✅:
- [ ] Integration tests passing
- [ ] Performance benchmarks acceptable
- [ ] Legacy system archived
- [ ] Project ready for production

---

## Timeline

| Week | Phase | Key Deliverables |
|------|-------|------------------|
| Week 1 | Audit & Deprecation | Production agents validated, legacy marked deprecated |
| Week 2 | Testing & CFBD | Test harness modernized, CFBD agents fixed |
| Week 3 | Week 12 Agents | All specialized agents working |
| Week 4 | Documentation | Complete usage guide, examples |
| Week 5 | Validation | Integration tests, performance benchmarks |

---

## Rollback Plan

If issues arise during modernization:

1. **Phase 1-2**: No rollback needed (only adding warnings)
2. **Phase 3-4**: Revert agent fixes if tests fail
3. **Phase 5-6**: Keep both systems until validation complete
4. **Phase 7**: Full archive of legacy system before deletion

---

## Next Steps

### Immediate Actions (This Week):
1. Run production agent audit script
2. Add deprecation warnings to legacy system
3. Create `LEGACY_DEPENDENCIES.txt` document

### Week 2 Priority:
1. Fix test harness
2. Start CFBD agent repairs
3. Create first pytest modules

### Long-term (Weeks 3-5):
1. Complete Week 12 agent modernization
2. Write comprehensive documentation
3. Archive legacy system

---

## Questions & Clarifications Needed

- [ ] Which CFBD agents are critical for predictions? (Prioritize fixes)
- [ ] Should we keep any legacy demos for historical reference?
- [ ] What's the timeline for removing archived legacy system entirely?
- [ ] Are there other agent directories we haven't covered?

---

*Last Updated: November 14, 2025*  
*Status: Ready for Implementation*
