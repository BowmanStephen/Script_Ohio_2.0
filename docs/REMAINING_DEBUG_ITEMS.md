# Remaining Debug Items - Script Ohio 2.0

**Last Updated**: 2025-12-17  
**Status**: Comprehensive inventory of debugging items

## Priority Categories

- 🔴 **CRITICAL**: Blocks functionality or causes failures
- 🟡 **HIGH**: Significant performance/quality issues
- 🟢 **MEDIUM**: Known limitations, nice-to-have improvements
- ⚪ **LOW**: Low-priority items, documentation gaps

---

## 🔴 CRITICAL Priority Items

### 1. Agent Performance & Memory Issues

**Issue**: Agent loading performance and memory explosion
- **AnalyticsOrchestrator**: 253ms to instantiate (target: <50ms)
- **Memory**: 105MB per agent, 844MB+ for all 8 agents
- **Root Cause**: Each agent loads all 4 ML models independently

**Impact**:
- Cold start: 2-3 seconds
- Concurrent users: Limited to 3-4 on 4GB machine
- Response latency: 500ms+ just for agent instantiation

**Files**: `_archived/reports/PERFORMANCE_BASELINE.md`

**Recommended Fix**: Implement model pooling/shared model singleton

---

### 2. Type Checking Errors (1,979 total)

**Status**: Partially addressed (~30 parameter defaults fixed)

**Remaining Issues**:
- **Invalid Assignments**: ~305 errors (type mismatches)
- **Invalid Argument Types**: ~153 errors (function call mismatches)
- **Invalid Parameter Defaults**: ✅ Fixed (~30 errors resolved)

**Files**:
- `docs/TY_FIXES_APPLIED.md`
- `docs/TY_ACTION_PLAN.md`
- `.cursor/ty_postfix*.txt` (detailed error logs)

**Recommended Fix**: Systematic fix per category (see TY_ACTION_PLAN.md)

---

### 3. FastAI Model Loading Issue

**Issue**: FastAI model fails to load with pickle protocol error
- **Error**: "persistent IDs in protocol 0 must be ASCII strings"
- **File**: `model_pack/fastai_home_win_model_2025.pkl`
- **Current**: Mock model fallback in place

**Status**: LOW priority - system works with mock, but should be fixed

**Files**:
- `config/FASTAI_MODEL_RESOLUTION_PLAN_2025.md`
- `src/models/execution/engine.py` (FastAIInterface class)
- `.cursor/plans/fix-all-6-outstanding-issues-9713bad1.plan.md`

**Recommended Fix**: Retrain model with `learn.export()` method

---

## 🟡 HIGH Priority Items

### 4. Agent Interface Mismatch

**Issue**: Request handling interface broken
- **Error**: `process_analytics_request() takes 2 positional arguments but 6 were given`
- **Root Cause**: Interface mismatch between expectation and implementation

**Status**: Needs verification if still broken

**Files**: `_archived/reports/PERFORMANCE_BASELINE.md` (line 19)

**Recommended Fix**: Verify current state, fix method signature

---

### 5. WeeklyAnalysisOrchestrator Missing Dependency

**Issue**: Missing plotly dependency
- **Status**: Reported as broken in agent audit

**Files**: `_archived/reports/AGENT_AUDIT_REPORT.md` (line 22)

**Recommended Fix**: Add plotly to requirements or handle missing dependency gracefully

---

### 6. Data Acquisition - Spread Data Missing

**Issue**: All 2025 games have spread = 0.0
- **Status**: Expected limitation (requires external betting lines API)
- **Priority**: LOW for predictions, but HIGH if spread features are needed

**Files**: `model_pack/ISSUES_FIXED_SUMMARY.md` (line 67)

**Recommended Fix**: Integrate betting lines API if spread features needed

---

## 🟢 MEDIUM Priority Items

### 7. Opponent-Adjusted Features (Expected Limitation)

**Issue**: All opponent-adjusted features use historical averages
- **Reason**: 2025 advanced stats not available in starter pack
- **Impact**: Features work but use placeholders

**Files**: `model_pack/ISSUES_FIXED_SUMMARY.md` (line 73)

**Status**: Cannot fix until 2025 advanced stats available

---

### 8. Agent Consolidation Needed

**Issue**: 68+ agent files, only ~8 are functional
- **Problem**: Massive code duplication
- **Solution**: Consolidate to 3 lean agents (planned but not executed)

**Files**: `_archived/reports/AGENT_AUDIT_REPORT.md`

**Recommended Fix**: Execute consolidation plan when time permits

---

### 9. Game Scores (Expected Behavior)

**Issue**: All 2025 games have scores = 0
- **Status**: Expected - games are scheduled, not yet played
- **Impact**: None - correct behavior

**Files**: `model_pack/ISSUES_FIXED_SUMMARY.md` (line 84)

**Status**: Not a bug - expected behavior

---

## ⚪ LOW Priority Items

### 10. Dependency Security Scanning

**Issue**: No automated dependency vulnerability scanning
- **Requirement**: Should run `pip-audit` or `safety check` in CI/CD
- **Status**: Documented but not implemented

**Files**: `.cursorrules` (Security section), `docs/SECURITY_BEST_PRACTICES.md`

**Recommended Fix**: Add to CI/CD pipeline

---

### 11. Code Organization - Large Files

**Issue**: Some files >1000 lines need refactoring
- **Examples**: `agents/analytics_orchestrator.py`
- **Impact**: Maintenance difficulty

**Files**: `docs/ARCHITECTURE_IMPROVEMENTS.md`

**Recommended Fix**: Split into focused modules

---

### 12. Archive/Backup Management

**Issue**: Archive directories in main repo
- **Impact**: Repository size, organization
- **Status**: Low priority cleanup

**Files**: `docs/ARCHITECTURE_IMPROVEMENTS.md`

**Recommended Fix**: Move to separate branch or external storage

---

### 13. Type Checker - Invalid Assignments/Arguments

**Issue**: ~458 remaining type errors (305 assignments + 153 arguments)
- **Status**: Systematic fixes needed
- **Impact**: Code quality, potential runtime bugs

**Files**: `docs/TY_FIXES_APPLIED.md`

**Recommended Fix**: Address incrementally (5-10 per PR)

---

## Documentation & Testing Gaps

### 14. Test Coverage Gaps

**Issue**: Need end-to-end workflow tests
- **Status**: Unit tests exist, integration tests incomplete
- **Impact**: Potential integration issues undetected

**Files**: `docs/ARCHITECTURE_IMPROVEMENTS.md`

**Recommended Fix**: Add E2E tests for critical workflows

---

### 15. API Documentation

**Issue**: API reference documentation incomplete
- **Status**: Inline docs exist, API reference missing
- **Impact**: Developer onboarding

**Files**: `docs/ARCHITECTURE_IMPROVEMENTS.md`

**Recommended Fix**: Auto-generate API docs from code

---

## Summary by Status

### ✅ Resolved/Fixed
- Talent ratings (all 612 games have real data)
- Elo ratings (all 612 games have real Elo)
- Data acquisition script bugs (week variable, early break)
- Syntax errors (Grade F → A+)
- ~30 type parameter default errors

### 🔴 Needs Immediate Attention
- Agent performance/memory (253ms loading, 105MB/agent)
- Type checking errors (~458 remaining)
- FastAI model loading (currently using mock)

### 🟡 Important but Not Blocking
- Agent interface mismatch (needs verification)
- WeeklyAnalysisOrchestrator dependency
- Spread data integration

### 🟢 Known Limitations
- Opponent-adjusted features (waiting for 2025 data)
- Agent consolidation (planned but not urgent)
- Large file refactoring

### ⚪ Low Priority
- Dependency scanning in CI/CD
- Archive management
- Documentation gaps
- Test coverage improvements

---

## Recommended Debugging Order

1. **Verify Current State** (1 hour)
   - Test agent interface mismatch (#4)
   - Verify WeeklyAnalysisOrchestrator dependency (#5)
   - Confirm FastAI model fallback working (#3)

2. **Quick Wins** (2-4 hours)
   - Fix top 20 type assignment errors (#2)
   - Add plotly dependency if needed (#5)
   - Add dependency scanning to CI/CD (#10)

3. **Performance Fixes** (1-2 days)
   - Implement model pooling (#1)
   - Fix agent interface if broken (#4)

4. **Systematic Type Fixes** (ongoing)
   - Address type errors incrementally (#2, #13)
   - 5-10 fixes per PR

5. **Architectural Improvements** (as time permits)
   - Agent consolidation (#8)
   - File refactoring (#11)
   - Test coverage (#14)

---

## Notes

- **FastAI Model**: System works with mock fallback, but should retrain eventually
- **Type Errors**: Many may be false positives, verify before fixing
- **Performance**: Critical for production scaling but not blocking development
- **Data Issues**: Spread/opponent-adjusted features are known limitations, not bugs

---

**Next Steps**: Start with verification phase to confirm current state of critical items, then prioritize based on actual impact.
