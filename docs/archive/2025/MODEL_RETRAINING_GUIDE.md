# Model Retraining Guide

## Overview

After integrating weeks 1-12 data, models should be retrained to include the latest 2025 season data. This ensures optimal prediction accuracy.

## Retraining Script

The retraining script is located at: `scripts/integrate_weeks_1_12_and_retrain.py`

This script:
1. Migrates weeks 1-11 from starter pack data to training format
2. Transforms week12 enhanced data to match training data schema
3. Merges all weeks 1-12 into updated_training_data.csv
4. Retrains Ridge, XGBoost, and FastAI models with the updated dataset

## Current Model Status

- **Ridge Model**: `model_pack/ridge_model_2025.joblib`
- **XGBoost Model**: `model_pack/xgb_home_win_model_2025.pkl`
- **FastAI Model**: `model_pack/fastai_home_win_model_2025.pkl` (uses mock fallback due to pickle protocol issue)

## Data Verification

Before retraining, verify weeks 1-12 are integrated:
```bash
python3 scripts/verify_weeks_1_12_integration.py
```

## Retraining Process

### Step 1: Backup Existing Models

```bash
cd /Users/stephen_bowman/Documents/GitHub/Script_Ohio_2.0
cp model_pack/ridge_model_2025.joblib model_pack/ridge_model_2025.joblib.backup
cp model_pack/xgb_home_win_model_2025.pkl model_pack/xgb_home_win_model_2025.pkl.backup
cp model_pack/fastai_home_win_model_2025.pkl model_pack/fastai_home_win_model_2025.pkl.backup
```

### Step 2: Run Retraining Script

```bash
python3 scripts/integrate_weeks_1_12_and_retrain.py
```

**Note**: This process may take 30-60 minutes depending on system resources.

### Step 3: Verify Models Load Correctly

```python
import joblib
import pickle

# Test Ridge model
ridge = joblib.load("model_pack/ridge_model_2025.joblib")
print("✅ Ridge model loaded")

# Test XGBoost model
xgb = pickle.load(open("model_pack/xgb_home_win_model_2025.pkl", "rb"))
print("✅ XGBoost model loaded")

# FastAI model will use mock fallback if pickle protocol issue persists
```

## FastAI Model Pickle Protocol Fix

If FastAI model fails to load, retrain with protocol 4:

```python
from fastai.tabular.all import *

# ... load and train model ...

# Save with FastAI's native export method (recommended)
learn.export("model_pack/fastai_home_win_model_2025.pkl")
```

## Important Notes

- Models are automatically backed up before retraining
- Retraining includes all weeks 1-12 data (622 games as of verification)
- Feature alignment is handled automatically by the retraining script
- Object columns are excluded from model features during retraining

## Troubleshooting

If retraining fails:
1. Check logs: `logs/weeks_1_12_integration.log`
2. Verify training data exists: `model_pack/updated_training_data.csv`
3. Ensure all dependencies are installed
4. Check that feature preparation functions are working correctly

