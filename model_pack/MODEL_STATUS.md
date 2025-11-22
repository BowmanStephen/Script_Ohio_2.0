# Model Status Documentation

**Last Updated:** November 19, 2025

This document provides a comprehensive overview of all models in the Script Ohio 2.0 project, categorizing them into production models, educational-only models, and archived models.

## Production Models

These models are actively used in production for predictions and analytics. They are loaded by the `ModelExecutionEngine` agent and referenced in the configuration system.

### 1. Ridge Regression Model
- **File:** `model_pack/ridge_model_2025.joblib`
- **Type:** Regression
- **Target:** Score margin (home_points - away_points)
- **Notebook:** `01_linear_regression_margin.ipynb`
- **Configuration:** `config/model_config.py` (key: `"ridge"`)
- **Status:** ✅ Production Ready
- **Last Updated:** November 19, 2025

### 2. XGBoost Classifier
- **File:** `model_pack/xgb_home_win_model_2025.pkl`
- **Type:** Classification
- **Target:** Home win probability (binary)
- **Notebook:** `03_xgboost_win_probability.ipynb`
- **Configuration:** `config/model_config.py` (key: `"xgb"`)
- **Status:** ✅ Production Ready
- **Last Updated:** November 19, 2025

### 3. FastAI Neural Network
- **File:** `model_pack/fastai_home_win_model_2025.pkl`
- **Type:** Classification
- **Target:** Home win probability (binary)
- **Notebook:** `04_fastai_win_probability.ipynb`
- **Configuration:** `config/model_config.py` (key: `"fastai"`)
- **Status:** ✅ Production Ready
- **Last Updated:** November 19, 2025

## Educational-Only Models

These models are demonstrated in notebooks for educational purposes but are **not saved as model files** and are **not used in production**. They serve as learning examples and comparison baselines.

### 1. Random Forest Regressor
- **Notebook:** `02_random_forest_team_points.ipynb`
- **Type:** Regression
- **Target:** Individual team scores (home_points, away_points)
- **Purpose:** Educational demonstration of ensemble methods
- **Status:** 📚 Educational Only
- **Note:** Model is trained in the notebook but not saved. Used to demonstrate Random Forest concepts and compare with other regression approaches.

### 2. Logistic Regression Classifier
- **Notebook:** `05_logistic_regression_win_probability.ipynb`
- **Type:** Classification
- **Target:** Home win probability (binary)
- **Purpose:** Educational baseline for interpretable classification
- **Status:** 📚 Educational Only
- **Note:** Model is trained in the notebook but not saved. Used as an interpretable baseline to compare with more complex models.

### 3. Stacked Ensemble
- **Notebook:** `07_stacked_ensemble.ipynb`
- **Type:** Ensemble Method
- **Purpose:** Educational demonstration of model stacking techniques
- **Status:** 📚 Educational Only
- **Note:** This is a **method**, not a saved model. The notebook demonstrates how to combine predictions from multiple base models (XGBoost, Random Forest, Logistic Regression) using a meta-learner. No model file is saved.

## Model Configuration Alignment

All production models are properly configured in:
- **`config/model_config.py`**: Model metadata and file paths
- **`agents/model_execution_engine.py`**: Model loading and execution logic

### Configuration Status
- ✅ Ridge model: `model_pack/ridge_model_2025.joblib` (aligned)
- ✅ XGBoost model: `model_pack/xgb_home_win_model_2025.pkl` (aligned)
- ✅ FastAI model: `model_pack/fastai_home_win_model_2025.pkl` (aligned)

## Archived Models

Outdated and legacy model files have been archived to preserve them for reference while keeping the main directory clean.

### Archive Location
- **Directory:** `model_pack/archived_models/YYYYMMDD/`
- **Purpose:** Preserve legacy models and outdated variants for historical reference

### Archived Files (November 19, 2025)
The following files were archived:
- `ridge_model.joblib` (legacy, no date)
- `ridge_model_2025_fixed.joblib` (outdated variant)
- `xgb_home_win_model.pkl` (legacy, no date)
- `xgb_home_win_model_2025_fixed.pkl` (outdated variant)
- `fastai_home_win_model.pkl` (legacy, no date)
- `fastai_home_win_model_2025_fixed.pkl` (outdated variant)
- `fastai_home_win_model_2025_original.pkl` (backup)
- `fastai_home_win_model_2025_full_features.pkl` (variant)
- Files from `model_pack copy/` directory (duplicate copies)

## Model Training

Production models are retrained using:
- **Primary Script:** `model_pack/model_training_agent.py`
- **Alternative Script:** `scripts/retrain_models_full_features.py`

Both scripts save models with the standard naming convention (no `_fixed` suffix):
- `ridge_model_2025.joblib`
- `xgb_home_win_model_2025.pkl`
- `fastai_home_win_model_2025.pkl`

## Model Usage

### Loading Models in Code

```python
from config.model_config import get_model_config
import joblib

# Get model configuration
ridge_config = get_model_config("ridge")
model = joblib.load(ridge_config["file"])
```

### Using Model Execution Engine

```python
from agents.model_execution_engine import ModelExecutionEngine

engine = ModelExecutionEngine()
# Models are automatically loaded on initialization
```

## Maintenance

### Regular Tasks
1. **Model Retraining:** Retrain models when new season data becomes available
2. **Configuration Updates:** Ensure `config/model_config.py` matches actual file paths
3. **Archive Cleanup:** Periodically review archived models and remove if no longer needed

### Audit Script
Run the model audit script to check for configuration mismatches and orphaned files:
```bash
python scripts/audit_model_files.py
```

## Notes

- **No `_fixed` Suffix:** All production models use the standard naming convention without `_fixed` suffix
- **Educational Models:** Random Forest and Logistic Regression models are not saved; they are demonstration-only
- **Stacked Ensemble:** This is a method/technique, not a saved model file
- **Backup Models:** Backup copies are maintained in `model_pack/backups/` for critical recovery scenarios

