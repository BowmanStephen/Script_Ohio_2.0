<!-- 9520f4a6-6d4c-4d20-85c3-da3426b0d8e7 17194fe0-63b0-4a50-a70a-a2410edef254 -->
# Plan: Align 2025 Data with Model Pack Standards

## 1. Analyze Data Generation Logic

- Review `create_2025_starter_pack_data.py` and `model_pack/2025_data_acquisition_v2.py` to identify where feature extraction happens.
- Determine why `home_points`, `away_points`, and `margin` are currently excluded from the output.

## 2. Implement Outcome Columns

- Modify the data generation script to fetch and include:
  - `home_points`
  - `away_points`
  - `margin` (calculated as `away_points - home_points`)
- Ensure these fields are populated for completed games and left as `NaN` (or appropriate null value) for future games to maintain "prediction-ready" status without data leakage.
- Verify the final column count reaches 92 (86 features + 6 outcome/metadata columns).

## 3. Create Alignment Validation Script

- Create `scripts/validate_data_alignment.py` to:
  - Load both the historical `model_pack/training_data.csv` and the new `training_data_2025_*.csv` files.
  - Compare column schemas (names, types, order).
  - Check for distribution anomalies in key features (e.g., `adjusted_epa`) to ensure calculation methodologies match.
  - Verify that opponent adjustments are being applied consistently.

## 4. Regenerate and Verify 2025 Data

- Run the updated data generation script to overwrite the existing 2025 weekly CSVs.
- Run the validation script to confirm the "issue" is resolved and the datasets are compatible.

## Detailed Implementation Steps

### Step 1.1: Locate Data Generation Entry Point

- Search for scripts that create `training_data_2025_week*.csv` files in the project root
- Review `scripts/combine_weeks_5_13_and_retrain.py` lines 101-150 to understand how weekly files are loaded
- Check `model_pack/2025_data_acquisition_v2.py` lines 236-400 for the `process_games_dataframe` method that structures the output
- Identify where the final DataFrame columns are defined before CSV export

### Step 1.2: Trace Game Data Flow

- In `model_pack/2025_data_acquisition_v2.py`, locate where `GamesApi.get_games()` is called (around line 200-300)
- Verify that `game.home_points` and `game.away_points` are available from the CFBD API response
- Check if these fields are being extracted in `_object_to_dict()` method or similar conversion functions
- Document the current data flow from API response to final CSV structure

### Step 1.3: Identify Column Definition Location

- Find where the final column list is assembled (likely in `process_games_dataframe` method around line 236)
- Check if there's a predefined column schema that excludes outcome columns
- Look for any filtering logic that might be removing `home_points`, `away_points`, or `margin` columns
- Compare with `model_pack copy/training_data.csv` header to see exact column order expected

### Step 2.1: Modify Data Processing Method

- In `model_pack/2025_data_acquisition_v2.py`, locate the `process_games_dataframe` method
- Add extraction of `home_points` and `away_points` from game objects:
  ```python
  home_points = game_dict.get('home_points') or getattr(game, 'home_points', None)
  away_points = game_dict.get('away_points') or getattr(game, 'away_points', None)
  ```

- Ensure these are added to the processed_data dictionary before DataFrame creation
- Handle None values appropriately (use `np.nan` for incomplete games)

### Step 2.2: Add Margin Calculation

- After extracting `home_points` and `away_points`, calculate `margin`:
  ```python
  if pd.notna(home_points) and pd.notna(away_points):
      margin = away_points - home_points  # Model pack convention: away - home
  else:
      margin = np.nan
  ```

- Verify margin calculation matches model pack convention (check `model_pack copy/training_data.csv` line 2: `margin` = away - home)
- Add `margin` to the processed_data dictionary

### Step 2.3: Update Column Order

- Ensure outcome columns are inserted in the correct position to match model pack structure:
  - After `spread` column (position ~14)
  - Before `home_adjusted_epa` column (position ~15)
- Reference: `model_pack copy/training_data.csv` header shows: `...,spread,home_points,away_points,margin,home_adjusted_epa,...`
- Update any column ordering logic to maintain this sequence

### Step 2.4: Handle Incomplete Games

- For games that haven't been played yet (future games), set:
  - `home_points = np.nan`
  - `away_points = np.nan`
  - `margin = np.nan`
- Check game completion status using `game.completed` attribute or similar field
- Ensure this doesn't break downstream processing that expects numeric types

### Step 2.5: Update Weekly File Generation

- If weekly files are generated separately, locate that script (possibly in `scripts/` directory)
- Apply the same changes to include outcome columns in weekly CSV exports
- Ensure column order consistency across all weekly files

### Step 3.1: Create Validation Script Structure

- Create `scripts/validate_data_alignment.py` with the following structure:
  ```python
  import pandas as pd
  import numpy as np
  from pathlib import Path
  
  def validate_schema_alignment():
      # Load model pack reference
      # Load 2025 weekly files
      # Compare schemas
      
  def validate_feature_distributions():
      # Compare key feature statistics
      
  def validate_opponent_adjustments():
      # Check adjustment methodology consistency
      
  def main():
      # Run all validations
  ```


### Step 3.2: Implement Schema Comparison

- Load `model_pack copy/training_data.csv` and extract column names, types, and order
- Load all `training_data_2025_week*.csv` files from project root
- Compare:
  - Column count (should be 92 for model pack, 92 for updated 2025 data)
  - Column names (exact match required)
  - Column order (must match model pack structure)
  - Data types (numeric columns should be float/int, categorical should be object/string)
- Report any mismatches with specific details

### Step 3.3: Implement Distribution Validation

- For key features like `home_adjusted_epa`, `away_adjusted_epa`, `spread`:
  - Calculate mean, std, min, max, median for both datasets
  - Compare distributions using statistical tests (Kolmogorov-Smirnov test or similar)
  - Flag significant deviations (>2 standard deviations from expected)
- Check for reasonable value ranges:
  - Adjusted EPA: typically -2 to +2
  - Success rates: 0 to 1
  - Spread: typically -50 to +50

### Step 3.4: Implement Opponent Adjustment Validation

- Sample 10-20 games from 2025 data
- Manually verify opponent adjustment calculation for one metric (e.g., `home_adjusted_epa`)
- Formula should be: `adjusted_metric = team_raw_metric - opponent_avg_allowed`
- Compare with model pack calculation methodology in `docs/calculation_methodology.md`
- Report any inconsistencies in adjustment logic

### Step 3.5: Add Outcome Column Validation

- Verify that `home_points`, `away_points`, and `margin` are present in all 2025 files
- Check that completed games have non-null outcome values
- Verify margin calculation: `margin = away_points - home_points`
- Ensure future games have `NaN` for outcomes (no data leakage)

### Step 4.1: Backup Existing Files

- Before regeneration, create backup directory: `backup/training_data_2025_$(date +%Y%m%d)/`
- Copy all existing `training_data_2025_week*.csv` files to backup directory
- Document backup location in validation report

### Step 4.2: Run Updated Data Generation

- Execute the modified data generation script (likely `model_pack/2025_data_acquisition_v2.py` or similar)
- Process all weeks 5-13 to regenerate weekly CSV files
- Monitor for errors during generation
- Verify file sizes and row counts match expectations

### Step 4.3: Run Validation Script

- Execute `scripts/validate_data_alignment.py` on the regenerated files
- Review validation report for:
  - Schema alignment status
  - Distribution comparison results
  - Opponent adjustment verification
  - Outcome column presence and correctness
- Address any issues found before proceeding

### Step 4.4: Verify Column Count

- Manually verify one regenerated file has exactly 92 columns
- Compare with `model_pack copy/training_data.csv` column count
- Ensure column order matches exactly (use `pd.read_csv().columns.tolist()` comparison)

### Step 4.5: Test Model Compatibility

- Load a sample of regenerated 2025 data
- Attempt to load with existing model training code (if available)
- Verify that models can process the new data structure without errors
- Check that feature extraction logic works with the updated schema