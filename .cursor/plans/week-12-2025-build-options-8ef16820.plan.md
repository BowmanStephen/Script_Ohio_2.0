<!-- 8ef16820-84ba-4dbc-8877-e145730e3466 84f7df67-64cd-4111-b271-2baa7321183c -->
# Comprehensive Data Validation and Enhancement Plan

## Objective

Ensure all 2025 college football data is correct, complete, and ready for ML model predictions by performing comprehensive validation, fixing missing data, verifying consistency between starter pack and model pack, and integrating the provided validation script.

## Current Status Analysis

### Issues Identified:

1. **Missing Columns**: `game_key` (100% missing) and `conference_game` (100% missing) in 2025 data - need to populate
2. **Week Coverage**: Starter pack has Week 16, model pack only through Week 14 - need to decide on inclusion
3. **Opponent-Adjusted Features**: Using historical averages - need to verify methodology matches historical patterns
4. **Team Name Consistency**: Need to verify exact matching between datasets (188 teams only in starter pack are non-FBS, expected)
5. **Conference Data**: Verify conference assignments are correct, some may be missing
6. **Model Feature Validation**: Ensure all required features are present and correctly formatted
7. **Validation Script Integration**: User provided validation script needs column name fixes (`year` → `season`, `home_score` → `home_points`, `away_score` → `away_points`)
8. **Data Quality Metrics**: Need comprehensive validation reporting

## Implementation Steps

### Step 1: Fix Missing Columns

**File**: `model_pack/migrate_starter_pack_data.py`

- **`game_key`**: Generate from game ID or calculate as unique identifier
- **`conference_game`**: Calculate from `home_conference` and `away_conference` (True if same conference)
- Update migration script to populate these columns
- Re-run migration to update 2025 data

### Step 2: Verify and Enhance Week Coverage

**Files**: `model_pack/migrate_starter_pack_data.py`, `starter_pack/data/games.csv`

- Check if Week 15-16 data should be included
- If yes, update migration to include all available weeks
- Verify week filtering logic (currently filters to FBS teams only)

### Step 3: Validate Opponent-Adjusted Feature Methodology

**Files**: `model_pack/migrate_starter_pack_data.py`, `model_pack/metrics_calculation_agent.py`

- Compare placeholder values with historical data patterns
- Verify that historical averages match actual historical distributions
- Document methodology for future real feature calculation
- Ensure feature ranges are reasonable (no extreme outliers)

### Step 4: Team Name Consistency Verification

**Files**: `model_pack/migrate_starter_pack_data.py`, `starter_pack/data/games.csv`, `model_pack/updated_training_data.csv`

- Create team name mapping dictionary
- Verify all FBS teams from starter pack are correctly mapped
- Check for any team name variations or inconsistencies
- Ensure team names match exactly between datasets

### Step 5: Conference Data Validation

**Files**: `model_pack/migrate_starter_pack_data.py`, `starter_pack/data/games.csv`

- Verify conference assignments are correct for all teams
- Check for missing conference data
- Validate conference names match historical data format
- Populate missing conference data if possible

### Step 6: Model Feature Compatibility Check

**Files**: `model_pack/model_training_agent.py`, `model_pack/updated_training_data.csv`

- Verify all required features for Ridge, XGBoost, and FastAI models are present
- Check feature data types match model expectations
- Validate feature ranges are within expected bounds
- Test feature extraction for sample predictions

### Step 7: Comprehensive Data Quality Report

**File**: `model_pack/COMPREHENSIVE_DATA_VALIDATION_REPORT.md` (new)

- Generate detailed validation report
- Document all fixes applied
- List any remaining limitations
- Provide data completeness metrics
- Include sample data verification

### Step 8: Re-merge and Final Verification

**Files**: `model_pack/updated_training_data.csv`, `model_pack/2025_starter_pack_migrated.csv`

- Re-run migration with all fixes
- Merge updated 2025 data with historical data
- Verify no data loss or corruption
- Final quality checks (duplicates, missing values, data types)

## Expected Outcomes

1. ✅ All missing columns populated or removed
2. ✅ Complete week coverage (or documented decision on week limits)
3. ✅ Opponent-adjusted features validated and documented
4. ✅ Team names consistent across all datasets
5. ✅ Conference data complete and accurate
6. ✅ All model features verified and compatible
7. ✅ Comprehensive validation report generated
8. ✅ Final dataset ready for model predictions

## Files to Create/Modify

### New Files to Create:

1. `DATA_VALIDATION_SCRIPT.py` - Comprehensive validation script (fix column names)
2. `DATA_REMEDIATION_SCRIPT.py` - Data fixes and enhancements script
3. `MASTER_ADMIN_SYSTEM_AUDIT.py` - Final system verification script
4. `model_pack/COMPREHENSIVE_DATA_VALIDATION_REPORT.md` - Detailed validation report

### Files to Modify:

1. `model_pack/migrate_starter_pack_data.py` - Add game_key and conference_game population
2. `model_pack/updated_training_data.csv` - Updated with fixes (game_key, conference_game)
3. `model_pack/2025_starter_pack_migrated.csv` - Regenerated with fixes

### Report Files Generated:

1. `project_management/DATA_VALIDATION_REPORT.json` - Validation results
2. `project_management/DATA_REMEDIATION_REPORT.json` - Fixes applied
3. `project_management/AUDIT_RESULTS.json` - System audit results

## Validation Checks

- [ ] All required columns present and populated
- [ ] No missing values in critical features
- [ ] Team names match exactly between datasets
- [ ] Conference data complete
- [ ] Week coverage verified
- [ ] Model features compatible
- [ ] Data types correct
- [ ] No duplicates
- [ ] Value ranges reasonable
- [ ] Ohio State vs UCLA Week 12 game verified

## Notes

- Missing columns (`game_key`, `conference_game`) may not be critical for predictions but should be populated for consistency
- Week 15-16 inclusion depends on user preference
- Opponent-adjusted features using historical averages is acceptable until 2025 advanced stats are available
- All fixes should maintain backward compatibility with existing models

### To-dos

- [ ] Fix missing columns (game_key, conference_game) in 2025 data
- [ ] Verify and enhance week coverage (check Week 15-16 inclusion)
- [ ] Validate opponent-adjusted feature methodology and values
- [ ] Verify team name consistency between starter pack and model pack
- [ ] Validate and fix conference data assignments
- [ ] Verify all model features are present and correctly formatted
- [ ] Generate comprehensive data validation report
- [ ] Re-merge data and perform final verification