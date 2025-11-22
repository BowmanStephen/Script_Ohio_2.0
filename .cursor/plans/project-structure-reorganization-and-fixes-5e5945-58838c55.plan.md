<!-- 58838c55-1678-435b-bc36-1465707d1fe5 9f6dc85e-2375-4763-ac7b-14f2fb14da26 -->
# Project Structure Reorganization and Fixes

## Phase 1: Critical File Path Fixes

### 1.1 Resolve Week 12 File Mismatch

**Issue**: Scripts reference `training_data_2025_week12_updated.csv` but only `training_data_2025_week12.csv` exists in root.

**Actions**:

- Check if `backup/training_data_2025_20251119/training_data_2025_week12_updated.csv` is newer/better
- If backup version is better: Copy to root as `training_data_2025_week12_updated.csv`
- If root version is current: Update scripts to use `training_data_2025_week12.csv`
- Files to update:
  - `scripts/combine_weeks_5_13_and_retrain.py` (line 72)
  - `scripts/recover_missing_games_local_first.py` (line 52)

### 1.2 Verify Weeks 1-4 Integration Status

**Issue**: Week 1-4 files exist but scripts only use weeks 5-13.

**Actions**:

- Check if weeks 1-4 are already in `model_pack/updated_training_data.csv`:
  ```python
  import pandas as pd
  df = pd.read_csv("model_pack/updated_training_data.csv")
  weeks_1_4 = df[(df['season'] == 2025) & (df['week'].isin([1,2,3,4]))]
  print(f"Weeks 1-4 games: {len(weeks_1_4)}")
  ```

- If weeks 1-4 are missing: Add them to combination scripts OR document why excluded
- Update `scripts/combine_weeks_5_13_and_retrain.py` to include weeks 1-4 if needed

## Phase 2: Reorganize Weekly Training Data Files

### 2.1 Create Organized Directory Structure

**Current**: 13 weekly training files in project root

**Target**: Organized in `data/weekly_training/`

**Actions**:

- Create directory: `data/weekly_training/`
- Move all `training_data_2025_week*.csv` files from root to `data/weekly_training/`
- Preserve file names exactly (including `training_data_2025_week12_updated.csv` if it exists)

### 2.2 Update Script Path References

**Files to update**:

- `scripts/combine_weeks_5_13_and_retrain.py`:
  - Change `self.project_root / week_file` to `self.project_root / 'data' / 'weekly_training' / week_file`
  - Update lines 64-74 to use new path
- `scripts/recover_missing_games_local_first.py`:
  - Update `WEEKLY_TRAINING_FILES` list (lines 44-54) to use `data/weekly_training/` prefix
- `scripts/validate_data_alignment.py`:
  - Update any references to weekly training files

### 2.3 Update Documentation

- Add note in `data/weekly_training/README.md` explaining:
  - Purpose of weekly training files
  - Relationship to `updated_training_data.csv`
  - How they're used in model training

## Phase 3: Fix "Copy" Directory References

### 3.1 Audit All References

**Issue**: Production scripts reference `starter_pack copy` and `model_pack copy`.

**Actions**:

- Search for all references: `grep -r "starter_pack copy\|model_pack copy" scripts/ agents/`
- Files found:
  - `scripts/recover_missing_games_local_first.py` (lines 35-41)

### 3.2 Update or Document Strategy

**Decision needed**: Are "copy" directories:

- A) Templates to keep (update scripts to use main directories)
- B) Outdated backups to remove (update scripts to use main directories)

**Actions**:

- Update `scripts/recover_missing_games_local_first.py`:
  - Change `'starter_pack copy'` → `'starter_pack'`
  - Change `'model_pack copy'` → `'model_pack'`
  - Verify paths exist in main directories
- If "copy" directories are templates: Add README explaining their purpose
- If outdated: Archive to `archive/copy_directories/` or remove

## Phase 4: Consolidate Data Directory Structure

### 4.1 Create Unified Structure

**Current**: Two parallel structures:

- `data/week{XX}/enhanced/` (for weekly agents)
- `training_data_2025_week{XX}.csv` in root (for combination scripts)

**Target**: Unified structure:

```
data/
  weekly_training/          # Weekly training CSV files (moved from root)
    training_data_2025_week01.csv
    ...
    training_data_2025_week13.csv
  week12/
    enhanced/
      week12_features_86.csv
      week12_enhanced_games.csv
  week13/
    enhanced/
      week13_features_86_model_compatible.csv
```

### 4.2 Update Agent Paths (if needed)

**Check**: Do weekly agents need updates?

- `agents/weekly_model_validation_agent.py` (line 288): Expects `data/week{XX}/enhanced/week{XX}_features_86.csv`
- This path is correct and should remain unchanged
- Only weekly training CSV files are being moved

## Phase 5: Backup Directory Cleanup

### 5.1 Document Backup Strategy

**Issue**: `backup/training_data_2025_20251119/` contains duplicates.

**Actions**:

- Create `backup/README.md` explaining:
  - Purpose of backups
  - Which files are source of truth (root or `data/weekly_training/`)
  - When backups were created
- Optionally archive old backups to `archive/backups/` if >30 days old

## Phase 6: Verification and Testing

### 6.1 Create Verification Script

**File**: `scripts/verify_data_structure.py`

**Checks**:

- All weekly training files exist in `data/weekly_training/`
- Scripts can find files at new locations
- Week 12 file exists (either `week12.csv` or `week12_updated.csv`)
- Weeks 1-4 status verified
- No broken path references

### 6.2 Test Critical Workflows

- Run `scripts/combine_weeks_5_13_and_retrain.py` with new paths
- Verify models can be retrained
- Check weekly agents still work with `data/week{XX}/enhanced/` structure

## Implementation Order

1. **Immediate** (Phase 1): Fix week 12 mismatch and verify weeks 1-4
2. **High Priority** (Phase 2): Move files and update scripts
3. **Medium Priority** (Phase 3): Fix "copy" directory references
4. **Low Priority** (Phases 4-5): Consolidation and cleanup
5. **Final** (Phase 6): Verification

## Files to Modify

**Scripts**:

- `scripts/combine_weeks_5_13_and_retrain.py`
- `scripts/recover_missing_games_local_first.py`
- `scripts/validate_data_alignment.py` (if needed)

**New Files**:

- `data/weekly_training/README.md`
- `backup/README.md`
- `scripts/verify_data_structure.py`

**Directories**:

- Create `data/weekly_training/`
- Move 13 CSV files from root to `data/weekly_training/`

### To-dos

- [ ] Resolve week 12 file mismatch: Check backup vs root version, copy correct one or update scripts
- [ ] Verify if weeks 1-4 are already integrated in updated_training_data.csv or need to be added
- [ ] Create data/weekly_training/ directory for organizing weekly CSV files
- [ ] Move all training_data_2025_week*.csv files from root to data/weekly_training/
- [ ] Update scripts/combine_weeks_5_13_and_retrain.py to use data/weekly_training/ paths
- [ ] Update scripts/recover_missing_games_local_first.py to use data/weekly_training/ paths and fix copy directory references
- [ ] Create data/weekly_training/README.md and backup/README.md explaining file organization
- [ ] Create scripts/verify_data_structure.py to verify all paths and file locations
- [ ] Test critical workflows: model retraining and weekly agent execution