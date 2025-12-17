# Global Cursor Instructions (Short Version)

Use this condensed version if Cursor's settings field has character limits.

---

## Default Planning Behavior

When user says "make a plan", "ship MVP", "multi-step work", or requests
planning:

**Always start with Reality Check:**
- Green: What's working
- Red: What's blocked
- Unknown: What needs discovery

**Then create structured plan with:**
1. YAML frontmatter with todos
2. Architecture overview
3. Phase 0: Discovery (always required)
4. Phase 1+: Implementation with file scopes
5. Final Phase: Verification with acceptance gates

**File Scope Enforcement:**
- List exact files before editing
- Set file limits per component
- If >N files needed, STOP and ask approval

**Coordinator + Sandbox Pattern (3+ tasks):**
- Coordinator manages merges/verification
- Subagents in isolated sandboxes (git worktrees)
- Each subagent has strict file ownership (no overlap)

**Change Discipline:**
- Minimal edits only (no refactors unless asked)
- One commit per phase
- No "while I'm here" changes
- STOP if blocker outside scope

**Verification Discipline:**
- Acceptance gates after each phase
- Exact commands that must pass
- Never assume; run or ask user to run

**Required in Every Plan:**
- Success criteria (checkboxes)
- Integration points (existing/new/modified files)
- Risk mitigation (risk + mitigation)

**Trigger Phrases:** "make a plan", "ship MVP", "create a plan", "multi-step
work", "coordinate", "break this down"

---

## How to Apply

1. Open Cursor Settings (`Cmd/Ctrl + ,`)
2. Search for "Rules" or "Custom Instructions" or "AI Instructions"
3. Paste the content above into the global instructions field
4. Save and restart Cursor

Workspace `.cursorrules` files take precedence over global instructions.
