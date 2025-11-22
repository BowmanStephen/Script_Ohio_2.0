# Changelog

All notable changes to this project will be documented in this file.

### [2025-11-13] - Activation Scripts PATH Fix

- **Fixed**: Malformed PATH variable assignments in activation scripts
  - Fixed bash/zsh activate script (line 54)
  - Fixed csh/tcsh activate.csh script (line 15)
  - Fixed fish activate.fish script (line 39)
  - Commit: `N/A (git not available or .venv ignored)`
  - Fixes PATH quoting: `$VIRTUAL_ENV/"bin"` → `$VIRTUAL_ENV/bin`

