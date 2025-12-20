# Agent Status Report

Generated: 2025-12-18

## Summary

- **Total Agents**: 6
- **✅ Working**: 2 (33%)
- **⚠️ Partial**: 1 (17%)
- **❌ Broken**: 3 (50%)

## ✅ Working Agents

### 1. Learning Navigator (`default_learning_nav`)
- **Type**: `LearningNavigatorAgent`
- **Status**: ✅ All capabilities working
- **Capabilities** (6/6 working):
  - ✅ `guide_learning_path` - Completed successfully
  - ✅ `explain_concepts` - Completed successfully
  - ✅ `recommend_resources` - Completed successfully
  - ✅ `recommend_content` - Completed successfully
  - ✅ `track_progress` - Completed successfully
  - ✅ `bridge_to_model_pack` - Completed successfully

### 2. Quality Assurance Agent (`default_quality_assurance`)
- **Type**: `QualityAssuranceAgent`
- **Status**: ✅ All capabilities working
- **Capabilities** (2/2 working):
  - ✅ `cfbd_health_check` - Completed successfully
  - ✅ `cfbd_recent_events` - Completed successfully

## ⚠️ Partial Agents

### 3. CFBD Integration Agent (`default_cfbd_integration`)
- **Type**: `CFBDIntegrationAgent`
- **Status**: ⚠️ 3/6 capabilities working (50%)
- **Working Capabilities**:
  - ✅ `live_scoreboard` - Completed successfully
  - ✅ `graphql_plays` - Completed successfully
  - ✅ `graphql_betting_lines` - Completed successfully
- **Broken Capabilities**:
  - ❌ `team_snapshot` - Error: "team parameter required"
  - ❌ `graphql_scoreboard` - Error: "Missing required parameter: season"
  - ❌ `graphql_recruiting` - Error: "Missing required parameter: year (or season)"

**Note**: These failures are due to missing required parameters in test requests, not actual bugs. The capabilities work when called with proper parameters.

## ❌ Broken Agents

### 4. Model Execution Engine (`default_model_engine`)
- **Type**: `ModelExecutionEngine`
- **Status**: ❌ All capabilities broken (0/7 working)
- **Issue**: Agent type mismatch - requests are being rejected with "Agent Model Execution Engine cannot handle request"
- **Broken Capabilities**:
  - ❌ `predict_game_outcome`
  - ❌ `batch_predictions`
  - ❌ `model_comparison`
  - ❌ `model_performance_analysis`
  - ❌ `kelly_criterion_analysis`
  - ❌ `value_betting_detection`
  - ❌ `betting_opportunity_analysis`

**Root Cause**: The agent's `can_handle_request` method is rejecting requests because the `agent_type` in the request doesn't match what the agent expects. The agent derives its type as `model_engine` from the class name `ModelExecutionEngine`, but the request routing may be using a different type.

### 5. Insight Generator (`default_insight_generator`)
- **Type**: `InsightGeneratorAgent`
- **Status**: ❌ All capabilities broken (0/9 working)
- **Issue**: Agent type mismatch - requests are being rejected with "Agent Insight Generator cannot handle request"
- **Broken Capabilities**:
  - ❌ `generate_analysis`
  - ❌ `statistical_analysis`
  - ❌ `create_visualizations`
  - ❌ `comparative_analysis`
  - ❌ `trend_analysis` (duplicate - appears twice)
  - ❌ `cfbd_real_time_analysis`
  - ❌ `graphql_trend_scan`
  - ❌ `generate_infographic`

**Root Cause**: Same as Model Execution Engine - agent type mismatch in request routing.

### 6. Postseason Projection Agent (`default_postseason_projection`)
- **Type**: `PostseasonProjectionAgent`
- **Status**: ❌ All capabilities broken (0/1 working)
- **Issue**: Permission level insufficient - "Insufficient permissions" error
- **Broken Capabilities**:
  - ❌ `run_postseason_pipeline` - Error: "Insufficient permissions"

**Root Cause**: The agent requires higher permission level than `READ_EXECUTE` (likely `READ_EXECUTE_WRITE` or `ADMIN`).

## Recommendations

### High Priority Fixes

1. **Fix Agent Type Matching** (Model Execution Engine & Insight Generator)
   - Issue: `can_handle_request` method is rejecting valid requests
   - Fix: Ensure agent type derivation matches between registration and request routing
   - Files to check:
     - `agents/core/agent_framework.py` (lines 152-260)
     - Agent registration in `agents/analytics_orchestrator.py`
     - Request routing logic

2. **Fix Permission Levels** (Postseason Projection Agent)
   - Issue: Agent requires higher permissions than test provides
   - Fix: Either:
     - Update test to use appropriate permission level (`READ_EXECUTE_WRITE` or `ADMIN`)
     - Or adjust agent's permission requirements if too restrictive

### Low Priority Fixes

3. **Improve Parameter Validation** (CFBD Integration Agent)
   - Issue: Some capabilities fail with missing parameters
   - Fix: Add default parameter handling or better error messages
   - Note: These are not bugs per se, but could be improved for better UX

4. **Remove Duplicate Capability** (Insight Generator)
   - Issue: `trend_analysis` capability appears twice
   - Fix: Remove duplicate from capability list

## Next Steps

1. Investigate agent type derivation logic in `BaseAgent.can_handle_request()`
2. Check how agents are registered vs. how requests are routed
3. Fix permission level requirements for Postseason Projection Agent
4. Re-run diagnostic after fixes to verify

## Diagnostic Tool

Run the diagnostic tool anytime with:
```bash
python3 agents/diagnose_agents.py
```

Results are saved to `agents/diagnostic_results.json`.
