# SP+ and FPI Calibration System

This directory contains scripts to enhance Ohio Model predictions by blending
them with SP+ and FPI ratings from CFBD.

## Overview

The calibration system uses historical performance data (Weeks 1-12) to
empirically determine optimal blend weights between Ohio Model predictions
and SP+ ratings. These validated weights are then used to create enhanced
predictions for current week games.

## Scripts

### 1. `validate_sp_blend_weights.py`

**Purpose:** Validates optimal blend weights using historical data.

**What it does:**
- Loads historical predictions (Weeks 1-12)
- Fetches SP+ and FPI ratings for those weeks via CFBD GraphQL
- Calculates SP+/FPI predicted spreads
- Compares against actual results to find optimal blend weights
- Saves validated weights to `config/calibration_weights.json`

**Usage:**
```bash
export CFBD_API_KEY=your_key_here
python scripts/validate_sp_blend_weights.py
```

**Output:**
- `config/calibration_weights.json` - Validated blend weights
- Console output with validation results and metrics

**When to run:**
- Once before using the enhancement system
- Re-run after significant model changes or mid-season

### 2. `enhance_predictions_with_ratings.py`

**Purpose:** Adds SP+ and FPI predictions to existing predictions and creates
calibrated ensemble.

**What it does:**
- Loads existing predictions (e.g., Week 13)
- Fetches current SP+ and FPI ratings (2025 season) via CFBD GraphQL
- Calculates SP+/FPI predicted spreads
- Loads validated calibration weights
- Creates calibrated ensemble prediction
- Saves enhanced predictions with new columns

**Usage:**
```bash
export CFBD_API_KEY=your_key_here

# Default: Week 13
python scripts/enhance_predictions_with_ratings.py

# Specify week
python scripts/enhance_predictions_with_ratings.py --week 13

# Specify input/output files
python scripts/enhance_predictions_with_ratings.py \
    --input predictions/week13/week13_predictions_all_60_games.csv \
    --output predictions/week13/week13_predictions_enhanced.csv
```

**Output:**
- Enhanced predictions CSV with new columns:
  - `sp_predicted_margin` - SP+ predicted spread
  - `fpi_predicted_margin` - FPI predicted spread
  - `calibrated_margin` - Optimal blend of Ohio Model + SP+
  - `ohio_vs_sp_diff` - Difference between Ohio Model and SP+
  - `ohio_vs_fpi_diff` - Difference between Ohio Model and FPI
  - `model_divergence` - Magnitude of model disagreement
  - `calibrated_predicted_winner` - Winner from calibrated margin

**When to run:**
- After generating weekly predictions
- Before finalizing predictions for betting/competition

## Workflow

### Initial Setup (One-time)

1. **Validate blend weights:**
   ```bash
   python scripts/validate_sp_blend_weights.py
   ```
   
   This creates `config/calibration_weights.json` with optimal weights based
   on Weeks 1-12 historical performance.

### Weekly Prediction Enhancement

1. **Generate base predictions:**
   ```bash
   python scripts/predict_all_week13_games.py
   ```
   
   This creates `predictions/week13/week13_predictions_all_60_games.csv`

2. **Enhance with SP+/FPI:**
   ```bash
   python scripts/enhance_predictions_with_ratings.py --week 13
   ```
   
   This creates `predictions/week13/week13_predictions_enhanced.csv` with:
   - Original predictions (unchanged)
   - SP+ and FPI predictions
   - Calibrated ensemble using validated weights

## Configuration

### Calibration Weights

The validation script generates `config/calibration_weights.json` with structure:

```json
{
  "generated_at": "2025-11-19T12:00:00",
  "season": 2025,
  "weeks_analyzed": [1, 2, 3, ..., 12],
  "games_analyzed": 612,
  "baseline_metrics": {
    "ohio_model": {
      "mae": 12.34,
      "rmse": 15.67
    },
    "sp_alone": {
      "mae": 11.89,
      "rmse": 14.92
    }
  },
  "optimal_weights": {
    "ohio_vs_sp": {
      "ohio_weight": 0.65,
      "sp_weight": 0.35,
      "mae": 11.45,
      "rmse": 14.23,
      "improvement_vs_ohio_pct": 7.2,
      "improvement_vs_sp_pct": 3.7
    }
  }
}
```

### Default Weights

If calibration weights file is not found, the enhancement script uses:
- **Ohio Model: 70%**
- **SP+: 30%**

This is a conservative default that slightly favors your existing models.

## Requirements

### API Access

- **CFBD API Key:** Required (Tier 3+ for GraphQL access)
- **Set via environment variable:** `CFBD_API_KEY`

### Data Files

**For validation script:**
- Historical predictions: `predictions/week{1-12}/*.csv`
- Actual results: `data/weekly_training/training_data_2025_week{1-12}.csv`

**For enhancement script:**
- Week predictions: `predictions/week{week}/week{week}_predictions_all_60_games.csv`

### Dependencies

- `pandas` - Data manipulation
- `numpy` - Numerical calculations
- `src.data_sources.cfbd_graphql` - CFBD GraphQL client

## Output Files

### Enhanced Predictions Format

The enhanced predictions CSV includes all original columns plus:

| Column | Description |
|--------|-------------|
| `sp_predicted_margin` | SP+ predicted spread (home team advantage) |
| `fpi_predicted_margin` | FPI predicted spread (home team advantage) |
| `calibrated_margin` | Optimal blend: `ohio_weight * ohio_margin + sp_weight * sp_predicted_margin` |
| `ohio_vs_sp_diff` | Difference: `ohio_margin - sp_predicted_margin` |
| `ohio_vs_fpi_diff` | Difference: `ohio_margin - fpi_predicted_margin` |
| `model_divergence` | Average absolute difference between models |
| `calibrated_predicted_winner` | Winner from `calibrated_margin` |

## Tips

1. **Run validation periodically:** Re-run validation script mid-season or after
   model changes to update blend weights.

2. **Compare predictions:** Use `ohio_vs_sp_diff` to identify games where
   models disagree significantly.

3. **High divergence games:** Games with large `model_divergence` values may
   require manual review or indicate data quality issues.

4. **Fallback behavior:** If SP+ ratings are unavailable for a game, the
   calibrated margin falls back to Ohio Model predictions.

## Troubleshooting

### "No ratings fetched"

- Check CFBD API key is set correctly
- Verify Tier 3+ subscription for GraphQL access
- Check API key has correct permissions

### "No historical predictions found"

- Ensure prediction files exist for Weeks 1-12
- Check file naming matches expected patterns:
  - `predictions/week{week}/week{week}_predictions_all_60_games.csv`
  - Or files with `ensemble_margin` or `ridge_margin` columns

### "No actual results found"

- Ensure training data files exist:
  - `data/weekly_training/training_data_2025_week{week}.csv`
- Files should have `home_points` and `away_points` columns

### Team name mismatches

The scripts include team name normalization, but some edge cases may require
manual mapping in the `normalize_team_name()` function.

## Next Steps

After enhancing predictions, you can:

1. **Compare predictions:** Analyze divergence between Ohio Model and SP+
2. **Use calibrated predictions:** Use `calibrated_margin` for final predictions
3. **Identify edge cases:** Review games with high `model_divergence`
4. **Validate accuracy:** Compare enhanced predictions vs actual results next week

