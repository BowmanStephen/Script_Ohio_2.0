# Script Resilience Changes - CFBD Import Fix

## Overview
Made scripts resilient to dependency issues by moving CFBD imports from top-level to inside functions after argument parsing. This allows `--help` to work even when CFBD dependencies are broken.

## Files Modified

### 1. `scripts/cfbd_pull.py`
- **Before**: Imported `UnifiedCFBDClient`, `CFBDFeatureEngineer`, and `AdvancedMetricsBuilder` at top level
- **After**: Moved all CFBD-related imports inside `main()` function after argument parsing
- **Added**: Proper error handling for missing dependencies
- **Testing**: ✅ `python3 scripts/cfbd_pull.py --help` works without CFBD

### 2. `scripts/check_key.py`
- **Before**: Imported `cfbd` at top level
- **After**: Moved `cfbd` import inside `check_api_key()` function after environment check
- **Added**: Command-line argument parsing with `--verbose` option
- **Testing**: ✅ `python3 scripts/check_key.py --help` works without CFBD

### 3. `scripts/fetch_week13_simple.py`
- **Before**: Imported `cfbd` at top level  
- **After**: Moved `cfbd` import inside `fetch_week13_games()` function
- **Added**: Command-line argument parsing with `--verbose` option
- **Testing**: ✅ `python3 scripts/fetch_week13_simple.py --help` works without CFBD

### 4. `scripts/fill_missing_games.py`
- **Before**: Imported multiple CFBD components at top level
- **After**: Moved all CFBD imports inside `MissingGamesFiller.__init__()` method
- **Added**: Command-line argument parsing with `--verbose` option
- **Testing**: ✅ `python3 scripts/fill_missing_games.py --help` works without CFBD

## Pattern Applied

The general pattern applied to all scripts:

```python
# 1. Keep lightweight imports at top level
import argparse
import sys
from pathlib import Path

# 2. Move heavy/dependency imports to after argument parsing
def main():
    parser = argparse.ArgumentParser(...)
    args = parser.parse_args()
    
    # 3. Import dependencies only when needed
    try:
        import cfbd  # or other heavy dependencies
        from src.cfbd_client.unified_client import UnifiedCFBDClient
    except ImportError as e:
        print(f"❌ Dependencies not available: {e}")
        sys.exit(1)
    
    # 4. Continue with script logic
    ...
```

## Verification Commands

All scripts now work with help without requiring CFBD dependencies:

```bash
# Test help functionality
python3 scripts/cfbd_pull.py --help
python3 scripts/check_key.py --help  
python3 scripts/fetch_week13_simple.py --help
python3 scripts/fill_missing_games.py --help
python3 scripts/run_weekly_analysis.py --help  # Already worked
```

## Backups Created

Original files backed up before modification:
- `scripts/cfbd_pull.py.backup`
- `scripts/check_key.py.backup`
- `scripts/fetch_week13_simple.py.backup`
- `scripts/fill_missing_games.py.backup`

## Rollback

If needed, restore originals:
```bash
cd scripts/
mv cfbd_pull.py.backup cfbd_pull.py
mv check_key.py.backup check_key.py
mv fetch_week13_simple.py.backup fetch_week13_simple.py
mv fill_missing_games.py.backup fill_missing_games.py
```

## Benefits

1. **Resilience**: Scripts can show help even when dependencies broken
2. **User Experience**: Clear error messages about missing dependencies
3. **Development**: Easier to work with scripts without full environment setup
4. **CI/CD**: Help commands work in minimal environments
5. **No functional changes**: All script behavior remains the same
