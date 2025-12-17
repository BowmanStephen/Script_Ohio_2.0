# Cursor Plan Template Guide

Standard template for creating structured, executable Cursor plans that follow
the multi-agent coordinator pattern with clear scoping, deliverables, and
acceptance gates.

## Template Structure

Every Cursor plan should follow this structure:

```markdown
---
name: [Plan Name]
overview: "[One-sentence overview of what this plan accomplishes]"
todos:
  - id: [task_id]
    content: "[Task description]"
    status: [pending|in_progress|completed]
  - id: [task_id_2]
    content: "[Task description]"
    status: [pending|in_progress|completed]
---

# [Plan Title]

## Architecture Overview

[Clear explanation of the approach, workflow, and any special patterns used
(e.g., coordinator + subagents, git worktrees, parallel execution)]

### Workflow

[Optional: Mermaid diagram or text description of the workflow]

## Phase 0: [Setup/Discovery Phase]

**Location**: [Where this phase runs]

**Role**: [What this phase accomplishes]

**Commands/Steps**:
- [Specific commands or steps]

**Output**: [What this phase produces]

## Phase 1: [First Implementation Phase]

[Repeat structure for each phase]

### Subagent/Component A: [Name]

**Sandbox/Scope**: [Isolated location or file scope]

**Scope**: ONLY [specific files or directories]

**Current State**:
- [What exists now]
- [What's missing or broken]

**Tasks**:
1. [Specific task]
2. [Specific task]

**Deliverables**:
- Files touched (list)
- Unified diff
- Verification commands + expected output

**Stop Condition**: [When to stop or escalate]

## Phase N: [Final Phase - Verification/Merge]

**Location**: [Where this runs]

**After each subagent/component completes**:
- [Verification steps]

**Acceptance Gates**:
```bash
[Exact commands that must pass]
```

## File Scope Enforcement

**Critical Rule**: Each subagent/component prompt must start with:

> "Before coding, list the exact files you plan to edit. If it's more than [N]
> files, stop and ask for approval."

**File Limits**:
- Component A: [N] files ([scope description])
- Component B: [N] files ([scope description])

## Success Criteria

- ✅ [Measurable outcome 1]
- ✅ [Measurable outcome 2]
- ✅ [All acceptance gates pass]

## Integration Points

**Existing Code to Leverage**:
- [File/component]: [What it provides]

**New Files Created**:
- [File]: [Purpose]

**Modified Files**:
- [File]: [What changed]

## Risk Mitigation

**Risk**: [Potential issue]
**Mitigation**: [How it's prevented]

## Notes

- [Important constraints or assumptions]
- [Cleanup steps if needed]
```

## Key Principles

### 1. YAML Frontmatter with Todos

Always include todos with status tracking:

```yaml
---
name: Plan Name
overview: "One-sentence overview"
todos:
  - id: phase0_setup
    content: "Phase 0: Setup and discovery"
    status: pending
  - id: phase1_implementation
    content: "Phase 1: Core implementation"
    status: pending
---
```

### 2. Clear Architecture Overview

Explain the approach upfront:
- Coordinator + subagents pattern
- Git worktrees for isolation
- Parallel vs sequential execution
- Any special coordination mechanisms

### 3. Phase-by-Phase Breakdown

Each phase should have:
- **Location**: Where it runs
- **Role**: What it accomplishes
- **Commands/Steps**: Specific actions
- **Output**: What it produces

### 4. Component/Subagent Structure

For each component/subagent, include:

**Sandbox/Scope**: Isolated location or strict file scope

**Current State**: What exists, what's missing

**Tasks**: Numbered, specific tasks

**Deliverables**: 
- Files touched (exact list)
- Unified diff
- Verification commands + expected output

**Stop Condition**: When to stop or escalate

### 5. File Scope Enforcement

**Critical Rule**: Always require listing files before editing:

> "Before coding, list the exact files you plan to edit. If it's more than [N]
> files, stop and ask for approval."

Specify file limits per component to prevent scope creep.

### 6. Acceptance Gates

Define exact verification commands that must pass:

```bash
python -c "import module; print('ok')"
python scripts/script.py --flag
npm -C directory run test
```

### 7. Success Criteria

List measurable outcomes as checkboxes:
- ✅ All components complete without conflicts
- ✅ All acceptance gates pass
- ✅ Specific functionality verified

### 8. Integration Points

Document:
- **Existing Code to Leverage**: Files/components to reuse
- **New Files Created**: What's being added
- **Modified Files**: What's being changed

### 9. Risk Mitigation

For each identified risk, specify:
- **Risk**: What could go wrong
- **Mitigation**: How it's prevented

## Multi-Agent Pattern Template

For plans using coordinator + subagents:

```markdown
## Architecture Overview

This plan implements a **coordinator + subagent** pattern using **[isolation
mechanism]** for sandbox isolation. Each subagent works in a separate
**[location]** to prevent file conflicts and scope creep.

### Workflow

[Diagram or description]

## Phase 0: [Setup Phase]

**Location**: [Main repo or coordinator location]

**Commands**:
```bash
[Setup commands]
```

**Result**: [What gets created]

## Phase 1: Coordinator Setup

**Location**: [Coordinator location]

**Role**: [What coordinator manages]

**Coordinator Prompt Template**:
```
[Template for coordinator prompts]
```

## Phase 2: Subagent Implementations

### Subagent A: [Name]

**Sandbox**: `[isolated location]`

**Scope**: ONLY [specific files]

**Current State**:
- [Current state]

**Tasks**:
1. [Task]

**Deliverables**:
- Files touched
- Unified diff
- Verification commands

## Phase 3: Coordinator Merge & Verification

**Location**: [Main repo]

**After each subagent commits**:
```bash
[Verification steps]
```

**Merge Strategy**:
- [How merges happen]
- [When to verify]
```

## Single-Agent Pattern Template

For simpler plans without subagents:

```markdown
## Architecture Overview

[Approach explanation]

## Phase 0: Discovery

**Goal**: [What to discover]

**Commands**:
```bash
[Discovery commands]
```

**Output**: [What's learned]

## Phase 1: Implementation

**Scope**: [Files to modify]

**Current State**:
- [Current state]

**Changes Needed**:
- [What to change]

**Implementation Steps**:
1. [Step]
2. [Step]

**Deliverables**:
- Files touched
- Unified diff
- Verification commands

## Phase 2: Verification

**Acceptance Gates**:
```bash
[Commands]
```

## Success Criteria

- ✅ [Outcome]
```

## Best Practices

### 1. Start with Discovery

Always include a Phase 0 that:
- Detects current state
- Identifies dependencies
- Captures baseline failures
- Documents decision points

### 2. Enforce File Scope

For each component:
- List exact files before editing
- Set file limits
- Prevent scope creep

### 3. Define Clear Deliverables

Each component must provide:
- Files touched (exact list)
- Unified diff
- Verification commands + expected output

### 4. Use Acceptance Gates

Define exact commands that must pass:
- Import tests
- Script execution
- Lint/type checks
- Integration tests

### 5. Document Integration Points

Always document:
- What existing code to leverage
- What new files are created
- What files are modified

### 6. Mitigate Risks

For each risk:
- Identify the risk
- Specify mitigation strategy
- Document fallback plans

### 7. Include Cleanup Steps

If using temporary resources (worktrees, branches, etc.):
- Document cleanup commands
- Specify when to clean up

## Example: Simple Plan

```markdown
---
name: Add JSON Output to Script
overview: "Add --format json option to prediction script"
todos:
  - id: analyze_script
    content: "Analyze current script structure"
    status: pending
  - id: add_json_flag
    content: "Add --format json CLI flag"
    status: pending
  - id: implement_json_output
    content: "Implement JSON output format"
    status: pending
  - id: verify_output
    content: "Verify JSON output is valid"
    status: pending
---

# Add JSON Output to Script

## Architecture Overview

This plan adds JSON output capability to the prediction script while
maintaining backward compatibility with existing CSV output.

## Phase 0: Script Analysis

**Goal**: Understand current script structure

**Commands**:
```bash
cat scripts/predict.py | head -50
rg -n "argparse\|click\|sys.argv" scripts/predict.py
rg -n "\.csv\|to_csv" scripts/predict.py
```

**Output**: Document current argument parsing and output format

## Phase 1: Add JSON Flag

**Scope**: ONLY `scripts/predict.py`

**Current State**:
- Script uses argparse
- Outputs CSV via `df.to_csv()`

**Changes Needed**:
- Add `--format` argument (choices: csv, json)
- Default to 'csv' for backward compatibility

**Implementation Steps**:
1. Add `--format` argument to argparse
2. Add format validation
3. Update help text

**Deliverables**:
- Files touched: `scripts/predict.py`
- Unified diff: [diff]
- Verification:
  ```bash
  python scripts/predict.py --help | grep format
  ```

## Phase 2: Implement JSON Output

**Scope**: ONLY `scripts/predict.py`

**Implementation Steps**:
1. Add JSON serialization function
2. Update output logic to branch on format
3. Ensure JSON is valid and pretty-printed

**Deliverables**:
- Files touched: `scripts/predict.py`
- Unified diff: [diff]
- Verification:
  ```bash
  python scripts/predict.py --format json > output.json
  python -c "import json; json.load(open('output.json')); print('valid')"
  ```

## Success Criteria

- ✅ `--format json` flag exists and works
- ✅ JSON output is valid
- ✅ Default behavior (CSV) unchanged
- ✅ Help text updated

## Integration Points

**Modified Files**:
- `scripts/predict.py`: Added JSON output capability

## Risk Mitigation

**Risk**: Breaking existing CSV output
**Mitigation**: Default to CSV, test both formats
```

## Validation Checklist

Before finalizing a plan, ensure:

- [ ] YAML frontmatter with todos included
- [ ] Architecture overview explains approach
- [ ] Phase 0 (discovery) included
- [ ] Each component has clear scope
- [ ] File limits specified
- [ ] Deliverables defined (files, diff, verification)
- [ ] Acceptance gates with exact commands
- [ ] Success criteria listed
- [ ] Integration points documented
- [ ] Risks identified and mitigated
- [ ] Cleanup steps included (if needed)

## Usage

When creating a new plan:

1. Copy the appropriate template (multi-agent or single-agent)
2. Fill in plan-specific details
3. Ensure all sections are complete
4. Run validation checklist
5. Test acceptance gates if possible

## References

- **Plan Structure Spec**: `docs/PLAN_STRUCTURE.md`
- **TOON Plan System**: `docs/TOON_PLAN_SYSTEM.md`
- **Example Plan**: `.cursor/plans/multi-agent_bowls_mvp_with_git_worktrees_9f6cff85.plan.md`
