# Quick Setup: Global Cursor Instructions

Make structured planning the default for ALL projects in 3 steps.

## Step 1: Open Cursor Settings

- **macOS**: `Cmd + ,` (or `Cursor > Settings`)
- **Windows/Linux**: `Ctrl + ,` (or `File > Preferences > Settings`)

## Step 2: Find AI Instructions Field

Search for one of these in Settings:
- "Rules"
- "Custom Instructions"
- "AI Instructions"
- "AI Behavior"
- "Default Instructions"

## Step 3: Paste Instructions

**Option A: Full Version** (Recommended)
- Copy from: `docs/GLOBAL_CURSOR_INSTRUCTIONS.md`
- Paste into the global instructions field

**Option B: Short Version** (If character limit)
- Copy from: `docs/GLOBAL_CURSOR_INSTRUCTIONS_SHORT.md`
- Paste into the global instructions field

## Step 4: Save & Test

1. Save settings
2. Restart Cursor (may be required)
3. Test in a new project:
   - Say: "Make a plan to add a feature"
   - Verify it includes Reality Check, phases, file scopes, acceptance gates

## How It Works

- **Global Instructions**: Apply to ALL projects by default
- **Workspace `.cursorrules`**: Override/extend global for specific projects
- **Best Practice**: Keep global rules generic, workspace rules specific

## Troubleshooting

**Can't find the settings field?**
- Cursor version may not support it yet
- Look in "Features" or "AI" sections
- Check Cursor documentation for your version

**Instructions not applying?**
- Verify you saved settings
- Try restarting Cursor
- Check if workspace has `.cursorrules` that overrides

**Want to disable for a project?**
- Create `.cursorrules` in that project with different rules
- Workspace rules take precedence over global

## Files Created

- `docs/GLOBAL_CURSOR_INSTRUCTIONS.md` - Full detailed version
- `docs/GLOBAL_CURSOR_INSTRUCTIONS_SHORT.md` - Condensed version
- `docs/CURSOR_GLOBAL_SETUP.md` - This quick guide

## Next Steps

1. Set up global instructions (steps above)
2. Test in a new project
3. Keep workspace-specific rules in `.cursorrules` for this repo

Done! All future projects will default to structured planning.
