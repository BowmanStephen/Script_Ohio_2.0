# ty Type Checker - Action Plan

**Date**: 2025-12-17  
**Status**: Ready for Action

## Quick Start: What to Do Now

### Option 1: Monitor & Learn (Recommended First Step)
**Time**: 5 minutes  
**Action**: Let ty run in CI/CD and observe results

1. **Push your changes** - ty will run automatically
2. **Review CI/CD output** - See what ty finds
3. **No immediate fixes needed** - ty is configured to warn, not fail CI/CD

**Why**: Get familiar with ty's output before making changes

---

### Option 2: Fix High-Value Issues (If You Have Time)
**Time**: 30-60 minutes  
**Action**: Fix the most impactful type errors

**Priority Order**:
1. **Invalid parameter defaults** (86 errors) - Easy fixes, prevent runtime bugs
2. **Invalid assignments** (305 errors) - Type mismatches that could cause issues
3. **Invalid argument types** (153 errors) - Function call errors

**How**:
```bash
# See specific errors
uvx ty check agents/ src/ scripts/ | grep "invalid-parameter-default" | head -10

# Fix one file at a time
uvx ty check src/validation/walk_forward_validator.py
```

---

### Option 3: Suppress False Positives (If Too Noisy)
**Time**: 15 minutes  
**Action**: Tune configuration to reduce noise

**If unresolved-import warnings are overwhelming**:
```toml
# In pyproject.toml
[tool.ty.rules]
unresolved-import = "ignore"  # Change from "warn" to "ignore"
```

**Or add file-specific overrides**:
```toml
[[tool.ty.overrides]]
include = ["agents/__init__.py", "agents/COMPREHENSIVE_INTEGRATION_DEMO.py"]
[tool.ty.overrides.rules]
unresolved-import = "ignore"
```

---

## Recommended Approach: Phased Strategy

### Phase 1: Monitor (Week 1)
**Goal**: Understand ty's output without making changes

- ✅ Let ty run in CI/CD
- ✅ Review warnings/errors in PRs
- ✅ Identify patterns (which errors repeat?)
- ✅ No code changes needed

**Outcome**: Familiarity with ty's findings

---

### Phase 2: Quick Wins (Week 2-3)
**Goal**: Fix easy, high-impact issues

**Target Issues**:
- Invalid parameter defaults (86) - Change `None` to `Optional[...]`
- Unused ignore comments - Remove unnecessary `# type: ignore`
- Invalid type forms - Fix `callable` → `Callable`

**Time Investment**: 1-2 hours total

**How to Find**:
```bash
# Find parameter default issues
uvx ty check agents/ src/ scripts/ | grep "invalid-parameter-default" > /tmp/param_issues.txt

# Review and fix one file at a time
```

**Outcome**: Cleaner code, fewer warnings

---

### Phase 3: Systematic Fixes (Ongoing)
**Goal**: Gradually improve type safety

**Approach**:
- Fix 5-10 errors per PR (don't overwhelm)
- Focus on one category at a time
- Add type hints where missing
- Fix `None` assignment issues

**Time Investment**: 15-30 minutes per PR

**Outcome**: Better type safety over time

---

### Phase 4: Optimize (Future)
**Goal**: Maximize ty's value

**Consider**:
- Replace mypy with ty? (faster CI/CD)
- Increase rule strictness? (as code improves)
- Add ty LSP to editor? (real-time feedback)

**Outcome**: Faster development, better code quality

---

## Immediate Actions (Choose One)

### 🟢 Low Effort: Just Monitor
```bash
# Nothing to do - ty runs automatically in CI/CD
# Just review the output when it appears
```

**Best for**: Busy schedule, want to learn first

---

### 🟡 Medium Effort: Fix Top Issues
```bash
# 1. See what's most common
uvx ty check agents/ src/ scripts/ | grep "^error\[" | cut -d']' -f1 | sort | uniq -c | sort -rn | head -5

# 2. Pick one category (e.g., invalid-parameter-default)
uvx ty check agents/ src/ scripts/ | grep "invalid-parameter-default" | head -5

# 3. Fix those files
# (Edit files, change None defaults to Optional[...])
```

**Best for**: Have 30-60 minutes, want immediate improvement

---

### 🔴 High Effort: Systematic Cleanup
```bash
# 1. Generate full report
uvx ty check agents/ src/ scripts/ > ty_report.txt

# 2. Categorize issues
grep "^error\[" ty_report.txt | cut -d']' -f1 | sort | uniq -c | sort -rn > ty_categories.txt

# 3. Fix category by category
# Start with easiest (invalid-parameter-default)
# Then move to harder ones
```

**Best for**: Dedicated time, want comprehensive improvement

---

## Common Scenarios

### Scenario 1: "CI/CD is failing because of ty"
**Solution**: ty is configured to warn, not error. If it's failing:
- Check if you changed `unresolved-import` to `"error"` in config
- Change it back to `"warn"` in `pyproject.toml`

---

### Scenario 2: "Too many warnings, can't see real issues"
**Solution**: Tune configuration
```toml
[tool.ty.rules]
unresolved-import = "ignore"  # Suppress false positives
unused-ignore-comment = "warn"  # Keep this - it's useful
```

---

### Scenario 3: "Want to fix errors but don't know where to start"
**Solution**: Start with easiest category
1. Run: `uvx ty check agents/ src/ scripts/ | grep "invalid-parameter-default" | head -5`
2. Open those files
3. Change `param: str = None` → `param: Optional[str] = None`
4. Repeat

---

### Scenario 4: "ty is too slow" (unlikely, but...)
**Solution**: ty is already 40-80x faster than mypy
- If it seems slow, check if you're running it on wrong paths
- Use: `uvx ty check agents/ src/ scripts/` (not entire repo)

---

## Decision Tree

```
Do you have time to fix issues now?
├─ No → Just monitor CI/CD output (Option 1)
└─ Yes → How much time?
    ├─ 15 min → Suppress false positives (Option 3)
    ├─ 30-60 min → Fix high-value issues (Option 2)
    └─ 2+ hours → Systematic cleanup (Phase 3)
```

---

## Key Takeaways

1. **You don't have to fix everything** - ty is configured to warn, not block
2. **Start small** - Fix 5-10 issues at a time
3. **Focus on value** - Parameter defaults and assignments are easiest wins
4. **Monitor first** - See what ty finds before making changes
5. **It's a tool, not a burden** - Use it to improve code quality gradually

---

## Questions?

- **"Should I fix all 1,979 errors?"** → No, start with easy ones (parameter defaults)
- **"Will ty slow down development?"** → No, it's 40-80x faster than mypy
- **"Do I need to fix everything now?"** → No, ty warns but doesn't block
- **"What if I ignore ty?"** → That's fine, it's just warnings (for now)

---

## Next Steps (Pick One)

1. **Do nothing** - Let ty run in CI/CD, review output later ✅
2. **Quick fix** - Fix 5-10 parameter default issues (30 min)
3. **Tune config** - Suppress false positives (15 min)
4. **Full cleanup** - Systematic fix of all issues (ongoing)

**Recommendation**: Start with #1 (monitor), then move to #2 (quick fixes) when you have time.
