# Weekly Analysis Scripts

This directory contains scripts for preparing and running weekly college football analysis.

## Quick Start

### 1. Prepare for Week 13 Analysis
```bash
python scripts/prepare_week13_analysis.py
```

This will:
- Check CFBD API key availability
- Fetch Week 13 schedule (if API key available)
- Validate Week 12 results are in training data
- Check model file status
- Create Week 13 directory structure
- Provide recommendations for next steps

### 2. Run Week 13 Analysis
```bash
python scripts/run_weekly_analysis.py --week 13
```

This will execute the complete analysis pipeline:
1. Model validation
2. Matchup analysis
3. Prediction generation

## Scripts Overview

### `prepare_weekly_analysis.py`
Generic preparation script for any week.

**Usage:**
```bash
python scripts/prepare_weekly_analysis.py --week 13 --season 2025
python scripts/prepare_weekly_analysis.py --week 14 --skip-fetch
python scripts/prepare_weekly_analysis.py --week 15 --skip-validation
```

**Options:**
- `--week`: Week number (required)
- `--season`: Season year (default: 2025)
- `--skip-fetch`: Skip fetching schedule from CFBD API
- `--skip-validation`: Skip previous week validation check

### `prepare_week13_analysis.py`
Convenience wrapper for Week 13 preparation.

**Usage:**
```bash
python scripts/prepare_week13_analysis.py
```

### `run_weekly_analysis.py`
Runs the complete weekly analysis pipeline.

**Usage:**
```bash
# Complete analysis
python scripts/run_weekly_analysis.py --week 13

# Specific steps only
python scripts/run_weekly_analysis.py --week 13 --step validation
python scripts/run_weekly_analysis.py --week 13 --step matchup
python scripts/run_weekly_analysis.py --week 13 --step predictions

# Verbose output
python scripts/run_weekly_analysis.py --week 13 --verbose
```

**Options:**
- `--week`: Week number (required)
- `--season`: Season year (default: 2025)
- `--step`: Which step to run: `all`, `validation`, `matchup`, or `predictions` (default: `all`)
- `--verbose`, `-v`: Enable verbose logging

## Output Locations

After running analysis, results are saved to:

- **Analysis Results**: `analysis/week{XX}/`
  - `week{XX}_comprehensive_analysis.json`
  - `week{XX}_strategic_recommendations.csv`
  - `week{XX}_power_rankings.csv`
  - `week{XX}_upset_alerts.csv`

- **Predictions**: `predictions/week{XX}/`
  - `week{XX}_comprehensive_predictions.csv`
  - `week{XX}_predictions.json`
  - `week{XX}_recommendations.csv`
  - `prediction_insights.json`
  - `week{XX}_prediction_summary.json`

- **Validation Reports**: `validation/week{XX}/`
  - `week{XX}_model_validation_report.json`
  - `validation_summary.csv`

## Example Workflow

```bash
# 1. Prepare for Week 13
python scripts/prepare_week13_analysis.py

# 2. (If needed) Update training data with Week 12 results
python project_management/core_tools/data_workflows.py refresh-training --max-week 13

# 3. (If needed) Retrain models
python config/retrain_fixed_models.py

# 4. Run Week 13 analysis
python scripts/run_weekly_analysis.py --week 13

# 5. Check results
ls -lh analysis/week13/
ls -lh predictions/week13/
```

## Troubleshooting

### "Week XX features not found"
Generate features using your feature generation pipeline or CFBD integration.

### "Week XX directory not found"
Run the preparation script to create directories:
```bash
python scripts/prepare_weekly_analysis.py --week XX
```

### "No games found for week XX"
CFBD API may not be updated yet. Wait 24-48 hours or check manually.

### "Models not loading"
Check that model files exist in `model_pack/`:
- `ridge_model_2025.joblib`
- `xgb_home_win_model_2025.pkl`
- `fastai_home_win_model_2025.pkl`

If missing, retrain models using the training workflow.

