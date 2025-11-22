# Codebase Consolidation Checklist

**Date**: 2025-11-19  
**Goal**: Remove unused complexity, reduce from 100+ patterns to ~20 (80% reduction)

## Pre-Consolidation Validation

- [ ] Run all weekly analysis scripts to establish baseline
  ```bash
  python scripts/run_weekly_analysis.py --week 13
  python scripts/generate_comprehensive_week13_analysis.py
  ```
- [ ] Run all tests to ensure current state works
  ```bash
  python -m pytest tests/ -v
  python scripts/validate_cfbd_pipeline.py
  ```
- [ ] Document current file counts and complexity metrics

## Phase 1: Deprecation Warnings (Week 1)

- [ ] Add deprecation warnings to:
  - [x] `agents/core/context_manager.py` → `.deprecated`
  - [x] `agents/state_aware_analytics_system.py` → `.deprecated`
  - [x] `agents/workflow_automator_agent.py` → `.deprecated`
  - [x] `agents/async_agent_framework.py` → `.deprecated`
- [ ] Update imports to show deprecation warnings
- [ ] Run tests to verify deprecation warnings appear
- [ ] Check for any code that still uses deprecated components

## Phase 2: Simplified Orchestrator (Week 1-2)

- [x] Create `agents/simplified_analytics_orchestrator.py` based on WeeklyAnalysisOrchestrator pattern
- [ ] Update `scripts/validate_cfbd_pipeline.py` to use SimplifiedAnalyticsOrchestrator
- [ ] Test simplified orchestrator with validation script
- [ ] Verify backward compatibility (AnalyticsOrchestrator alias)

## Phase 3: Remove Unused Components (Week 2-3)

### ContextManager Removal
- [ ] Find all imports of ContextManager
  ```bash
  grep -r "from agents.core.context_manager import" .
  grep -r "import.*ContextManager" .
  ```
- [ ] Update files that import ContextManager:
  - [ ] `agents/analytics_orchestrator.py` (already simplified)
  - [ ] `agents/learning_navigator_agent.py` (check if actually used)
  - [ ] `agents/insight_generator_agent.py` (check if actually used)
  - [ ] `agents/workflow_automator_agent.py` (deprecated)
  - [ ] Documentation files (can be updated later)
- [ ] Remove ContextManager from `agents/core/__init__.py`
- [ ] Delete `agents/core/context_manager.py` after deprecation period

### StateAwareAnalyticsSession Removal
- [ ] Find all imports of StateAwareAnalyticsSession
  ```bash
  grep -r "StateAwareAnalyticsSession" .
  ```
- [ ] Update `agents/analytics_orchestrator.py` (already simplified)
- [ ] Remove from `agents/__init__.py` if present
- [ ] Delete `agents/state_aware_analytics_system.py` after deprecation period

### WorkflowAutomatorAgent Removal
- [ ] Find all imports of WorkflowAutomatorAgent
  ```bash
  grep -r "WorkflowAutomatorAgent" .
  ```
- [ ] Remove from `agents/analytics_orchestrator.py` (already simplified)
- [ ] Delete `agents/workflow_automator_agent.py` after deprecation period

### AsyncAgentOrchestrator Removal
- [ ] Find all imports of AsyncAgentOrchestrator
  ```bash
  grep -r "AsyncAgentOrchestrator" .
  ```
- [ ] Delete `agents/async_agent_framework.py` after deprecation period

## Phase 4: Simplify AnalyticsOrchestrator (Week 2)

- [ ] Replace `agents/analytics_orchestrator.py` with simplified version
- [ ] Remove context/role detection code
- [ ] Remove state management code
- [ ] Remove workflow automation code
- [ ] Keep only: agent factory, request router, direct execution
- [ ] Test with `scripts/validate_cfbd_pipeline.py`

## Phase 5: Create Template (Week 2)

- [x] Create `agents/orchestrator_template.py` based on WeeklyAnalysisOrchestrator
- [ ] Document template usage in `AGENTS.md`
- [ ] Add examples showing how to use template

## Phase 6: Validation (Week 3)

- [ ] Run all weekly analysis scripts
  ```bash
  python scripts/run_weekly_analysis.py --week 13
  python scripts/generate_comprehensive_week13_analysis.py
  ```
- [ ] Run all tests
  ```bash
  python -m pytest tests/ -v
  ```
- [ ] Run validation script
  ```bash
  python scripts/validate_cfbd_pipeline.py
  ```
- [ ] Verify no broken imports
  ```bash
  python -c "from agents.analytics_orchestrator import AnalyticsOrchestrator; print('OK')"
  ```
- [ ] Check for orphaned dependencies
- [ ] Verify performance metrics (should be same or better)

## Phase 7: Cleanup (Week 4)

- [ ] Remove deprecated files after 30-day period
- [ ] Update all documentation to reflect simplified architecture
- [ ] Update `.cursorrules` to reference new patterns
- [ ] Update `AGENTS.md` with simplified examples
- [ ] Remove unused imports from all files
- [ ] Clean up test files that test deprecated components

## Post-Consolidation Metrics

- [ ] Count total patterns (target: ~20, down from 100+)
- [ ] Measure code reduction (lines of code removed)
- [ ] Verify test coverage maintained
- [ ] Document complexity reduction percentage

## Rollback Plan

If issues arise:
1. Revert to previous commit
2. Restore deprecated files from `.deprecated` versions
3. Re-enable ContextManager/StateAware if needed
4. Document what broke and why

## Success Criteria

- [ ] All weekly analysis scripts work
- [ ] All tests pass
- [ ] Validation script works
- [ ] No production code breaks
- [ ] 80% reduction in complexity achieved
- [ ] Documentation updated
- [ ] Code is simpler and easier to maintain

