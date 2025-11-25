# Web App Data Sync Guide

## Overview

This document describes how the web app gets updated with the latest predictions and models.

## Automatic Sync

Run the sync script to update the web app with the latest data:

```bash
python3 scripts/sync_web_app_data.py
```

This script:
1. Copies latest prediction files from `predictions/week14/` to `web_app/public/`
2. Converts CSV files to JSON when needed
3. Verifies all model files are present
4. Updates API configuration

## Data Files Synced

### Primary Files
- `week14_model_predictions.json` - Standard model predictions (JSON)
- `week14_model_predictions.csv` - Standard model predictions (CSV)
- `week14_ats_full_table.csv` - ATS analysis data
- `week14_ats_data.json` - ATS data (auto-converted from CSV)

### Enhanced Files (Optional)
- `week14_predictions_enhanced_calibrated.json` - Calibrated predictions with market adjustments
- `week14_predictions_unified.json` - Unified predictions from all sources

## Model Files

The following models are verified during sync:
- `ridge_model_2025.joblib` - Ridge Regression model
- `xgb_home_win_model_2025.pkl` - XGBoost model
- `fastai_home_win_model_2025.pkl` - FastAI neural network model

All models are located in `model_pack/` and are accessible to the API.

## Data Priority

The web app and API use the following priority order for predictions:

1. **Calibrated predictions** (`calibrated_margin`, `calibrated_home_win_prob`)
2. **Market-adjusted predictions** (`market_adjusted_margin`)
3. **Ensemble predictions** (`ensemble_margin`, `ensemble_home_win_probability`)
4. **Individual model predictions** (`ridge_predicted_margin`, etc.)

This ensures the most refined predictions are used when available.

## API Updates

The API (`api/prediction_api.py`) automatically:
- Loads enhanced/calibrated predictions if available
- Falls back to standard predictions if enhanced versions aren't found
- Uses dynamic paths (no hardcoded absolute paths)

## Web App Updates

The web app (`web_app/src/utils/`) has been updated to:
- Prefer calibrated predictions when loading data
- Support new fields like `market_adjusted_margin` and `market_adjusted_edge`
- Maintain backward compatibility with standard predictions

## Manual Sync Steps

If you need to manually sync files:

1. Copy prediction files:
   ```bash
   cp predictions/week14/week14_model_predictions.json web_app/public/
   cp predictions/week14/week14_model_predictions.csv web_app/public/
   cp predictions/week14/week14_ats_full_table.csv web_app/public/
   ```

2. Convert CSV to JSON (if needed):
   ```bash
   python3 -c "
   import json, csv
   with open('predictions/week14/week14_ats_full_table.csv') as f:
       reader = csv.DictReader(f)
       data = list(reader)
   with open('web_app/public/week14_ats_data.json', 'w') as f:
       json.dump(data, f, indent=2)
   "
   ```

3. Restart the API server if running

## Verification

After syncing, verify:
- ✅ All files exist in `web_app/public/`
- ✅ JSON files are valid (can be parsed)
- ✅ Model files exist in `model_pack/`
- ✅ Web app loads predictions correctly
- ✅ API returns predictions successfully

## Troubleshooting

**Issue**: Web app shows old predictions
- **Solution**: Clear browser cache and refresh, or restart the dev server

**Issue**: API returns 404 for predictions
- **Solution**: Check that files exist in `web_app/public/` and API path is correct

**Issue**: Models not loading
- **Solution**: Verify model files exist in `model_pack/` and check file permissions

## Next Steps

After syncing data:
1. Restart the API server: `python3 api/prediction_api.py`
2. Restart the web app dev server: `cd web_app && npm run dev`
3. Verify predictions display correctly in the UI
4. Test API endpoints: `curl http://localhost:5001/api/predictions/week/14`

