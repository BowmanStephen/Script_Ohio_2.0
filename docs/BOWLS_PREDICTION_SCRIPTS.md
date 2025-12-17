# Bowls Prediction Scripts Documentation

This document covers all bowl prediction scripts in Script Ohio 2.0, their purposes, usage examples, and safety features.

## Overview

The bowls prediction system provides three different approaches to predicting bowl game outcomes:

1. **Machine Learning Ensemble** (`predict_bowls_2025.py`) - Production-ready ML predictions
2. **Massey Ratings-Based** (`predict_bowls_2025.py --method massey`) - Rating system predictions
3. **Simple Rating Difference** (`predict_bowls_2025.py --method simple`) - Basic predictions

## Primary Script: predict_bowls_2025.py

### Purpose
Production-ready bowl predictions with comprehensive safety features, backup management, and multiple prediction methods.

### Prerequisites
- CFBD API key in environment: `export CFBD_API_KEY="your-key"`
- Python 3.13+ with project dependencies installed
- Trained ML models (for ML method)

### Command Syntax

```bash
python3 scripts/predict_bowls_2025.py [OPTIONS]
```

### Options

| Option | Description | Default | Values |
|--------|-------------|---------|--------|
| `--season` | Season to predict for | 2025 | Any valid season year |
| `--method` | Prediction method to use | ml | ml, massey, simple, all |
| `--force` | Overwrite existing files without confirmation | False | Flag |
| `--dry-run` | Preview actions without creating files | False | Flag |
| `--backup-existing` | Create timestamped backup of existing predictions | False | Flag |

### Usage Examples

#### Basic Usage - Generate ML Predictions
```bash
python3 scripts/predict_bowls_2025.py --season 2025
```

#### Generate All Prediction Methods with Backup
```bash
python3 scripts/prediction_bowls_2025.py --season 2025 --method all --backup-existing --force
```

#### Preview What Would Be Generated
```bash
python3 scripts/predict_bowls_2025.py --season 2025 --dry-run
```

#### Generate Specific Method Only
```bash
python3 scripts/predict_bowls_2025.py --season 2025 --method massey --backup-existing
```

### Output Files

The script generates prediction files with a standardized naming convention to prevent conflicts:

```bash
# Primary ML predictions (default)
predictions/bowls_2025_predictions_ml.json

# Massey ratings-based predictions
predictions/bowls_2025_predictions_massey.json

# Simple rating difference predictions
predictions/bowls_2025_predictions_simple.json

# Backup files (when --backup-existing used)
predictions/bowls_2025_predictions_ml_backup_20251216_214957.json
```

### Output Format

All prediction files follow this JSON structure:

```json
{
  "generated_at": "2025-12-16T21:47:27.308312",
  "model": "ml-ensemble-v1",
  "season": 2025,
  "method": "ml",
  "git_sha": "abc123def456",
  "input_check": {
    "cfbd_api_available": true,
    "massey_ratings_available": true,
    "ml_models_available": true
  },
  "games": [
    {
      "game_id": 401755831,
      "game_type": "playoff-semifinal",
      "bowl_name": "Rose Bowl",
      "home_team": "Oregon",
      "away_team": "Ohio State",
      "predicted_winner": "Ohio State",
      "home_win_probability": 0.42,
      "away_win_probability": 0.58,
      "predicted_margin": -3.2,
      "confidence_score": 0.75,
      "start_time": "2025-01-01T17:00:00",
      "neutral_site": true,
      "venue": "Rose Bowl",
      "line": null,
      "home_team_massey": 3.45,
      "away_team_massey": 6.78
    }
  ]
}
```

### Safety Features

#### 1. Automatic Backup System
```bash
# When --backup-existing is specified:
predictions/bowls_2025_predictions_ml.json.backup_20251216_214957
```

#### 2. Git SHA Tracking
Each prediction file includes the git SHA of the codebase at generation time for reproducibility.

#### 3. Input Validation
The script validates availability of required inputs:
- CFBD API connectivity
- Massey ratings data
- ML model files (for ML method)

#### 4. Dry Run Mode
Preview exactly what files would be generated without creating them:
```bash
python3 scripts/predict_bowls_2025.py --dry-run
```

#### 5. Force Protection
By default, the script prompts for confirmation before overwriting existing files. Use `--force` to bypass.

### Prediction Methods

#### 1. ML Ensemble (`--method ml`)
- **Description**: Uses all three trained models (Ridge, XGBoost, FastAI) with weighted voting
- **Best for**: Maximum prediction accuracy
- **Requirements**: All models in `model_pack/` must be available
- **Features**: Ensemble voting, confidence scores, comprehensive error handling

#### 2. Massey Ratings (`--method massey`)
- **Description**: Uses Massey rating differentials to predict outcomes
- **Best for**: When ML models are unavailable or for comparison
- **Requirements**: Massey ratings data in `src/ratings/massey_ratings_2025.csv`
- **Features**: Proven rating system, no ML dependencies

#### 3. Simple Rating Difference (`--method simple`)
- **Description**: Basic rating difference calculation with adjusted win probability
- **Best for**: Quick predictions, debugging, baseline comparison
- **Requirements**: Minimal dependencies
- **Features**: Fast execution, simple logic

#### 4. All Methods (`--method all`)
- **Description**: Generates predictions using all three methods
- **Best for**: Comprehensive analysis, method comparison
- **Output**: Three separate files with method-specific suffixes

## Supporting Scripts

### bowl_guide_utils.py
Utility functions for bowl-related analysis and betting guide generation.

### generate_bowl_betting_guide.py
Generates comprehensive bowl betting guides with analysis and recommendations.

### predict_bowls_2025_fallback.py
Legacy fallback script for basic bowl predictions (use primary script instead).

## Web App Integration

The bowl predictions are automatically available through the web app API:

```bash
# GET endpoint
http://localhost:8000/api/predictions/bowls/2025

# Returns all available prediction methods
{
  "ml": {...},      # ML ensemble predictions
  "massey": {...},  # Massey ratings predictions
  "simple": {...}   # Simple predictions
}
```

## Production Deployment

### Environment Setup
```bash
# Required environment variables
export CFBD_API_KEY="your-api-key"
export FLASK_ENV="production"  # For web app deployment
```

### Recommended Production Commands
```bash
# 1. Update data
python3 scripts/sync_all_data_sources.py --season 2025 --retrain

# 2. Generate all bowl predictions with backup
python3 scripts/predict_bowls_2025.py --season 2025 --method all --backup-existing --force

# 3. Verify predictions
ls -la predictions/bowls_2025_predictions_*.json

# 4. Start web app
python3 web_app/app.py
```

### Monitoring and Maintenance

#### Prediction File Management
- Backups are created automatically when using `--backup-existing`
- Old backups should be periodically cleaned up to save space
- Keep at least 5 recent backups for rollback capability

#### Performance Monitoring
- ML predictions take ~30-60 seconds to generate
- Massey predictions take ~10-20 seconds
- Simple predictions take ~5-10 seconds

#### Error Handling
- All methods include comprehensive error handling
- Failed predictions generate log entries with specific error details
- Web app gracefully handles missing prediction files

## Troubleshooting

### Common Issues

#### 1. CFBD API Errors
```
❌ CFBD API error: 401 Unauthorized
```
**Solution**: Verify CFBD_API_KEY is set and valid

#### 2. Missing Models
```
❌ Required ML models not found
```
**Solution**: Run model training first:
```bash
python3 scripts/retrain_models_current.py
```

#### 3. Missing Massey Data
```
❌ Massey ratings file not found
```
**Solution**: Generate Massey ratings:
```bash
python3 -c "from src.ratings.massey_ratings import generate_massey_ratings; generate_massey_ratings(2025)"
```

#### 4. Permission Errors
```
❌ Permission denied when creating backup
```
**Solution**: Check write permissions to `predictions/` directory

### Debug Mode
Use dry-run mode to debug issues without creating files:
```bash
python3 scripts/predict_bowls_2025.py --season 2025 --dry-run
```

### Log Files
Check application logs for detailed error information:
```bash
# Web app logs
tail -f logs/app.log

# Script execution logs
python3 scripts/predict_bowls_2025.py --season 2025 2>&1 | tee bowl_prediction.log
```

## Best Practices

### Before Generating Predictions
1. **Verify Data Freshness**: Ensure CFBD data is current
2. **Check Model Training**: Confirm ML models are trained on recent data
3. **Test API Connectivity**: Validate CFBD API access
4. **Run Dry Run**: Preview what will be generated

### After Generating Predictions
1. **Verify Output**: Check generated files for completeness
2. **Monitor Web App**: Confirm predictions appear correctly
3. **Backup Results**: Keep copies of important prediction runs
4. **Document Changes**: Note any manual adjustments or corrections

### Regular Maintenance
1. **Weekly Data Updates**: Keep training data current during season
2. **Model Retraining**: Retrain models after significant games
3. **Backup Cleanup**: Remove old backup files periodically
4. **Performance Monitoring**: Track prediction accuracy over time

## File Structure Summary

```
predictions/
├── bowls_2025_predictions_ml.json              # Primary ML predictions
├── bowls_2025_predictions_massey.json          # Massey predictions
├── bowls_2025_predictions_simple.json          # Simple predictions
├── bowls_2025_predictions_ml_backup_*.json     # Timestamped backups
├── bowls_2025_predictions_massey_backup_*.json # Massey backups
└── bowls_2025_predictions_simple_backup_*.json # Simple backups

scripts/
├── predict_bowls_2025.py                       # Main prediction script
├── bowl_guide_utils.py                         # Utility functions
├── generate_bowl_betting_guide.py              # Betting guide generator
└── predict_bowls_2025_fallback.py              # Legacy fallback

logs/
├── bowl_predictions.log                        # Script execution logs
└── app.log                                     # Web app logs
```

This documentation ensures that bowl predictions can be generated safely, reliably, and with full understanding of all available options and safety features.