---
name: CFBD Snapshot System
overview: Create deterministic snapshot system for CFBD data to enable offline bowl predictions. Implements snapshot refresh script, adds snapshot support to cfbd_pull.py, and wires bowls predictions to use snapshots.
todos:
  - id: verify_cfbd_import
    content: Verify CFBD SDK import works (check pydantic version, test cfbd import)
    status: pending
  - id: create_snapshot_script
    content: Create scripts/cfbd_refresh_snapshots.py with --season, --refresh-all, --only flags
    status: pending
  - id: add_teams_method
    content: Add get_teams() method to UnifiedCFBDClient if missing
    status: pending
  - id: update_cfbd_pull
    content: Add --use-snapshots and --refresh flags to cfbd_pull.py with snapshot reading logic
    status: pending
  - id: update_predict_postseason
    content: Add --use-snapshots flag to predict_postseason_2025.py with snapshot validation
    status: pending
  - id: test_verification_commands
    content: Run all verification commands and verify snapshots work end-to-end
    status: pending
---

# CFBD Snapshot System Implementation

## Objective

Create a deterministic snapshot system for CFBD data to enable offline bowl predictions. This makes the pipeline deterministic - predictions can be rerun without hitting CFBD API every time.

## Prerequisites Verification

**CRITICAL**: Before implementing snapshots, verify CFBD SDK is working:

1. Check pydantic version: `python -c "import pydantic; print('pydantic', pydantic.__version__)"`
2. Verify CFBD import: `python -c "import cfbd; print('cfbd import ok')"`
3. If CFBD fails to import:

   - Verify `requirements.txt` has `pydantic>=1.10.13,<2` (compiled from `requirements.in`)
   - Reinstall: `pip install -r requirements.txt`
   - Recompile if using pip-tools: `pip-compile requirements.in`

## Implementation Tasks

### 1. Create Snapshot Refresh Script (`scripts/cfbd_refresh_snapshots.py`)

**Purpose**: Fetch and save CFBD data snapshots to `data/raw/cfbd/` for deterministic pipeline runs.

**Key Features**:

- Fetch games (regular + postseason), teams, talent data
- Write JSON files: `games_regular_{season}.json`, `games_postseason_{season}.json`, `teams_{season}.json`, `talent_{season}.json`
- Write metadata JSON per dataset: `games_regular_{season}.metadata.json`
- Metadata includes: `fetched_at`, `season`, `endpoint_name`, `record_count`, `git_sha`, `cfbd_sdk_version`

**Command-line Flags**:

- `--season 2025` (required)
- `--refresh-all` (force refresh all datasets)
- `--only games_postseason` (optional: refresh specific dataset)
- `--check-freshness` (optional: future enhancement)

**Implementation Notes**:

- Use `UnifiedCFBDClient` from `src/cfbd_client/unified_client.py`
- Call `client.get_games(year=season, season_type="regular")` and `season_type="postseason"`
- Call `client.get_team_talent(year=season)` for talent
- For teams: Use `client.get_teams()` (add wrapper method to UnifiedCFBDClient)
- Write JSON with `json.dump(data, handle, indent=2, default=str)`
- Create `data/raw/cfbd/` directory if missing
- Handle API errors gracefully with logging

**File Structure**:

```
data/raw/cfbd/
├── games_regular_2025.json
├── games_regular_2025.metadata.json
├── games_postseason_2025.json
├── games_postseason_2025.metadata.json
├── teams_2025.json
├── teams_2025.metadata.json
├── talent_2025.json
└── talent_2025.metadata.json
```

### 2. Update `cfbd_pull.py` with Snapshot Support

**Changes to `scripts/cfbd_pull.py`**:

Add two new flags:

- `--use-snapshots`: Read from local JSON snapshots first; don't hit network
- `--refresh`: Force refresh snapshots, then use them

**Default Behavior** (safe):

- If snapshots exist → use them unless `--refresh` is specified
- If snapshots missing → fetch from API and create snapshots
- If `--use-snapshots` is set and snapshots missing → error with helpful message

**Implementation**:

- Add snapshot reading function: `load_snapshot(season, dataset_type)` → returns data or None
- Modify `fetch_games()` to check snapshots first if `--use-snapshots` or snapshots exist
- Add `--refresh` flag to force API fetch and snapshot update
- Log clearly when using snapshots vs API

**Integration Points**:

- `fetch_games()` function (line 80-87): Add snapshot check before API call
- `parse_args()` function (line 59-77): Add `--use-snapshots` and `--refresh` flags
- `main()` function: Pass snapshot flags to fetch functions

### 3. Wire Bowls Predictions to Use Snapshots

**Changes to `scripts/predict_postseason_2025.py`**:

Add `--use-snapshots` flag:

- When set, ensures snapshots exist before running predictions
- If snapshots missing, provide helpful error message with command to create them
- This enables offline bowl predictions once snapshots are created

**Implementation**:

- Add `--use-snapshots` flag to `_parse_args()` (line 135-144)
- Add snapshot validation function: `ensure_snapshots_exist(season)` → checks for required files
- In `main()`, if `--use-snapshots` is set, validate snapshots exist before proceeding
- Error message: "Snapshots missing. Run: python scripts/cfbd_refresh_snapshots.py --season 2025 --refresh-all"

**Note**: This script reads from CSV (`training_data_2025_postseason.csv`), so snapshots are for data preparation, not direct consumption. The flag ensures data pipeline used snapshots.

### 4. Add Teams API Method (if missing)

**Check**: Verify `UnifiedCFBDClient` has `get_teams()` method.

**If missing**, add to `src/cfbd_client/unified_client.py`:

```python
def get_teams(self, conference: Optional[str] = None) -> List[Dict]:
    """Get teams data with caching"""
    params = {"conference": conference}
    return self._cached_fetch(
        "teams",
        params,
        lambda: self._to_dict_list(self.teams_api.get_teams(conference=conference)),
        "teams"
    )
```

## Verification Commands

After implementation, run these to verify:

```bash
# 1. Verify CFBD import works
python -c "import pydantic; print('pydantic', pydantic.__version__)"
python -c "import cfbd; print('cfbd import ok')"

# 2. Create snapshots
python scripts/cfbd_refresh_snapshots.py --season 2025 --refresh-all

# 3. Verify snapshots created
ls -lah data/raw/cfbd/

# 4. Test cfbd_pull with snapshots
python scripts/cfbd_pull.py --season 2025 --use-snapshots

# 5. Test bowls predictions with snapshots
python scripts/predict_postseason_2025.py --use-snapshots --format json

# 6. Verify JSON output
python -c "import json; json.load(open('predictions/bowls_2025_predictions.json')); print('json ok')"
```

## Files to Create/Modify

**New Files**:

- `scripts/cfbd_refresh_snapshots.py` (new snapshot refresh script)

**Modified Files**:

- `scripts/cfbd_pull.py` (add `--use-snapshots` and `--refresh` flags, snapshot reading logic)
- `scripts/predict_postseason_2025.py` (add `--use-snapshots` flag, snapshot validation)
- `src/cfbd_client/unified_client.py` (add `get_teams()` method if missing)

**Generated Files** (after running refresh):

- `data/raw/cfbd/games_regular_2025.json`
- `data/raw/cfbd/games_regular_2025.metadata.json`
- `data/raw/cfbd/games_postseason_2025.json`
- `data/raw/cfbd/games_postseason_2025.metadata.json`
- `data/raw/cfbd/teams_2025.json` (optional)
- `data/raw/cfbd/teams_2025.metadata.json` (optional)
- `data/raw/cfbd/talent_2025.json` (optional)
- `data/raw/cfbd/talent_2025.metadata.json` (optional)

## Important Notes

1. **Pydantic Version**: Ensure `pydantic<2` is pinned in `requirements.txt` (compiled from `requirements.in` if using pip-tools). Verify before implementing.

2. **API v1 Only**: Use current SDK patterns (v1). Don't assume v2 compatibility - treat v2 migration as separate task.

3. **Deterministic Pipeline**: Once snapshots exist, predictions can run offline. This is the "ship bowls now" requirement.

4. **Error Handling**: Gracefully handle missing snapshots, API failures, and invalid JSON.

5. **Logging**: Use existing logging patterns from `cfbd_pull.py` (file + console handlers).

## Success Criteria

- ✅ CFBD import works (pydantic<2 verified)
- ✅ Snapshot refresh script creates all required JSON files
- ✅ `cfbd_pull.py --use-snapshots` reads from snapshots without API calls
- ✅ `predict_postseason_2025.py --use-snapshots` validates snapshots exist
- ✅ All verification commands pass
- ✅ Pipeline is deterministic (can rerun predictions offline)
