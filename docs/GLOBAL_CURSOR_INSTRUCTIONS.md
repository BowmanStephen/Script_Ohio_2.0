# Global Cursor Instructions for All Projects

Copy this into Cursor's global settings to make structured planning the default
behavior across all your projects.

## How to Set Global Instructions

### Method 1: Cursor Settings UI (Recommended)

1. Open Cursor Settings:
   - **macOS**: `Cmd + ,` or `Cursor > Settings`
   - **Windows/Linux**: `Ctrl + ,` or `File > Preferences > Settings`

2. Search for: **"Rules"** or **"Custom Instructions"** or **"AI Instructions"**

3. Look for sections like:
   - **"Rules for AI"**
   - **"Custom Instructions"**
   - **"AI Behavior"**
   - **"Default AI Instructions"**

4. Paste the content below into the global instructions field

### Method 2: Direct Config File (Advanced)

The global instructions are typically stored in:
- **macOS**: `~/Library/Application Support/Cursor/User/globalStorage/` or `~/.cursor/`
- **Windows**: `%APPDATA%\Cursor\User\globalStorage\` or `%USERPROFILE%\.cursor\`
- **Linux**: `~/.config/Cursor/User/globalStorage/` or `~/.cursor/`

Look for files like:
- `settings.json`
- `rules.json`
- `ai-instructions.json`

## Global Instructions Template

Copy this entire section into Cursor's global instructions:

---

# Default Planning Behavior (Global)

When the user asks for a plan, multi-step work, or coordination tasks, ALWAYS
follow this structured approach.

## Reality Check (Always Start Here)

Before creating any plan, ALWAYS start with a short "Reality Check":
- **Green (Working)**: What is currently functional and verified
- **Red (Blocked)**: What is broken, missing, or blocking progress
- **Unknown**: What needs discovery or verification

Run discovery commands to establish baseline state before planning.

## Planning Format Requirements

**All plans MUST follow this structure:**

1. **YAML Frontmatter** (if creating plan files):
   ```yaml
   ---
   name: Plan Name
   overview: "One-sentence overview"
   todos:
     - id: phase0_setup
       content: "Phase 0: Discovery"
       status: pending
   ---
   ```

2. **Architecture Overview**: Explain the approach upfront
   - Coordinator + subagent pattern (if multi-agent)
   - Isolation mechanism (git worktrees recommended)
   - Workflow description

3. **Phase-by-Phase Structure**:
   - **Phase 0**: Discovery & Setup (always required)
   - **Phase 1+**: Implementation phases
   - **Final Phase**: Verification & Acceptance

4. **Each Phase MUST Include**:
   - Files to change (exact list)
   - Commands to run (exact commands)
   - Expected output / success criteria
   - Verification commands

5. **File Scope Enforcement**:
   - Each component/subagent has strict file ownership (no overlap)
   - List exact files before editing
   - Set file limits per component
   - If more than N files needed, STOP and ask for approval

## Coordinator + Sandbox Pattern (Default for Multi-Step Work)

**When to Use**: Any plan with 3+ distinct tasks or components that could
conflict.

**Pattern**:
- **Coordinator**: Manages merges, runs verification, coordinates subagents
- **Subagents/Components**: Each has isolated sandbox and strict file scope
- **Isolation Mechanism**: Git worktrees (default) or separate branches

**Git Worktree Setup** (Default Sandbox):
```bash
# Create feature branch
git checkout -b feature/plan-name

# Create worktrees for each subagent
git worktree add ../sandbox-name feature/plan-name
```

**Coordinator Responsibilities**:
- Creates worktrees/branches for subagents
- Merges commits from subagents
- Runs acceptance gates after each merge
- Coordinates fixes if verification fails

**Subagent/Component Requirements**:
- **Sandbox Location**: Explicit isolated location
- **File Scope**: ONLY specific files (list before editing)
- **Current State**: Document what exists now
- **Tasks**: Numbered, specific tasks
- **Deliverables**: Files touched, unified diff, verification commands
- **Stop Condition**: When to stop or escalate

**File Scope Rule** (CRITICAL):
> "Before coding, list the exact files you plan to edit. If it's more than [N]
> files, stop and ask for approval."

## Change Discipline

**Minimal Changes Principle**:
- Prefer minimal edits; do NOT refactor unless explicitly requested
- One commit per phase with clear message
- No "while I'm here" changes
- If blocker found outside scope, STOP and ask for approval

**Commit Strategy**:
- One commit per phase/subagent
- Clear commit message: "Phase X: [component] - [what changed]"
- Include verification results in commit message if applicable

## Verification Discipline

**Acceptance Gates** (Required for Every Plan):
- Define exact verification commands that must pass
- Run after each phase/component
- Never assume; run or ask user to run commands and paste results
- Document expected output for each command

**Example Acceptance Gates**:
```bash
python -c "import module; print('ok')"
python scripts/script.py --flag
npm run test
python -c "import json; json.load(open('output.json')); print('valid')"
```

## Success Criteria (Required in Every Plan)

Every plan MUST include measurable success criteria as checkboxes:
- ✅ [Measurable outcome 1]
- ✅ [Measurable outcome 2]
- ✅ [All acceptance gates pass]

## Integration Points Documentation

Every plan MUST document:
- **Existing Code to Leverage**: Files/components to reuse
- **New Files Created**: What's being added
- **Modified Files**: What's being changed

## Risk Mitigation

Every plan MUST identify:
- **Risk**: Potential issues
- **Mitigation**: How they're prevented

## Trigger Phrases

When user says any of these, automatically use structured planning:
- "make a plan"
- "ship MVP"
- "create a plan"
- "multi-step work"
- "coordinate"
- "break this down"

---

## Workspace-Specific Overrides

If a project has a `.cursorrules` file, those rules take precedence for that
workspace. The global instructions provide the base behavior, and
workspace-specific rules can extend or override as needed.

## Testing the Global Instructions

After setting global instructions, test with:
1. Open a new project (without `.cursorrules`)
2. Say: "Make a plan to add a feature"
3. Verify it follows the structured format with:
   - Reality Check
   - Phase 0: Discovery
   - File scope enforcement
   - Acceptance gates

## Troubleshooting

**If instructions don't apply:**
- Check Cursor version (may need latest)
- Verify instructions are in the correct settings location
- Try restarting Cursor
- Check for workspace-specific `.cursorrules` that might override

**If behavior differs:**
- Workspace `.cursorrules` takes precedence
- Global instructions provide base behavior
- Workspace rules can extend or override
