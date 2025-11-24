# Week 14 Data Integration & Model Retraining Summary

## Actions Taken

1.  **Data Organization**:
    *   Moved your provided file `training_data_2025_week14.csv` to the canonical location: `data/training/weekly/training_data_2025_week14.csv`.

2.  **Week 13 Results**:
    *   Fetched the latest game outcomes for Week 13 from the CFBD API.
    *   Verified that Week 13 games now have scores in the training dataset.

3.  **Model Retraining**:
    *   Created and ran a new integration script: `scripts/integrate_weeks_1_14_and_retrain.py`.
    *   This script combined all data from Weeks 1-14.
    *   **Retrained all models** (Ridge Regression, XGBoost, FastAI) using the updated dataset (training on games with known outcomes up to Week 13).

## Current Status

*   **Training Data**: `model_pack/updated_training_data.csv` now includes:
    *   Week 1-13 games (with scores).
    *   Week 14 games (features only, ready for prediction).
*   **Models**: All models in `model_pack/` have been updated with the latest data.

## How to Retrain in Future

You can use the newly created script to retrain at any time:

```bash
python3 scripts/integrate_weeks_1_14_and_retrain.py
```

Or for a generic update (if you add Week 15 data later):
1.  Place the new file in `data/training/weekly/`.
2.  Update the script to include the new file in the `week_files` list.
3.  Run the script.
