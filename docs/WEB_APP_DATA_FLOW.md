# Web App Data Flow

## Overview

The new Next.js web app uses a **hybrid data mode**:
- **Default**: Reads directly from repository artifacts (no file copying needed)
- **Optional**: Can proxy to Python API servers if `PY_API_BASE_URL` env var is set

## Data Sources

### Weekly Predictions

**Location**: `predictions/week{N}/week{N}_model_predictions.json`

**Format**: Array of game prediction objects with:
- `game_id`, `season`, `week`
- `home_team`, `away_team`
- `spread`, `predicted_margin`
- Model-specific predictions (`ridge_*`, `xgb_*`, `fastai_*`)
- Ensemble predictions (`ensemble_*`)

**Web App Route**: `/week/[week]`

**Example**:
```bash
# Validate week 14 predictions exist
python scripts/sync_web_app_data.py --week 14

# Access in web app
curl http://localhost:3000/week/14
```

### Bowl Predictions

**Location**: `data/outputs/predictions/2025/bowl_season/bowls_2025_predictions_ml.json`

**Format**: JSON object with:
- `generated_at`, `season`, `model_type`
- `games`: Array of bowl game predictions

**Web App Route**: `/bowls`

**Example**:
```bash
# Validate bowl predictions exist
python scripts/sync_web_app_data.py --bowls-only

# Access in web app
curl http://localhost:3000/bowls
```

### Model Analytics

**Location**: `data/outputs/analysis/external_model_analysis_*.json`

**Format**: JSON object with:
- `models`: Array of external model comparisons
- `insights`: Competitive analysis
- `recommendations`: Improvement suggestions

**Web App Route**: `/analytics`

**Example**:
```bash
# Validate analytics files exist
python scripts/sync_web_app_data.py --analytics-only

# Access in web app
curl http://localhost:3000/analytics
```

## Weekly Workflow

When a new week's predictions are generated:

1. **Generate predictions** (using existing Python scripts):
   ```bash
   python scripts/predict_week14_proper.py
   # or
   python scripts/run_weekly_analysis.py --week 15
   ```

2. **Validate files exist**:
   ```bash
   python scripts/sync_web_app_data.py --week 15
   ```

3. **Access in web app**:
   - Navigate to `http://localhost:3000/week/15`
   - Or update navigation to include the new week

## Hybrid Mode (Optional API Proxy)

If you want to use live API data instead of static files:

1. **Set environment variable**:
   ```bash
   export PY_API_BASE_URL=http://localhost:5001
   ```

2. **Start Next.js dev server**:
   ```bash
   cd web_app
   npm run dev
   ```

3. **Web app will attempt API calls first**, falling back to artifacts if API is unavailable.

## Data Validation

The sync script (`scripts/sync_web_app_data.py`) now validates that required files exist and are properly formatted. It does **not** copy files anymore since the web app reads directly from the repository structure.

Run validation:
```bash
# Validate all data sources
python scripts/sync_web_app_data.py --week 14

# Validate specific data source
python scripts/sync_web_app_data.py --bowls-only
python scripts/sync_web_app_data.py --analytics-only
```

## Troubleshooting

**"Predictions not found" error**:
- Ensure prediction files are generated first
- Check file paths match expected structure
- Run validation script to identify missing files

**"Invalid format" error**:
- Check JSON structure matches expected schema
- Validate files with `jq` or Python JSON parser
- Re-generate predictions if corrupted

**API proxy not working**:
- Verify `PY_API_BASE_URL` is set correctly
- Check Python API server is running
- Review browser console for API errors
- Web app will automatically fall back to artifacts
