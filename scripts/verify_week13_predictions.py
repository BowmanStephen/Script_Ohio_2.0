#!/usr/bin/env python3
"""
Generate Week 13 Predictions
============================

This script loads the newly retrained models and generates predictions for Week 13 games.
It validates that the models can successfully ingest new data and produce outputs.
"""

import sys
import joblib
import pandas as pd
import numpy as np
from pathlib import Path
import xgboost as xgb

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Import feature definitions
try:
    from project_management.TOOLS_AND_CONFIG.model_features import RIDGE_FEATURES, XGB_FEATURES
except ImportError:
    sys.path.append(str(PROJECT_ROOT / "project_management" / "TOOLS_AND_CONFIG"))
    from model_features import RIDGE_FEATURES, XGB_FEATURES

# FastAI imports
try:
    from fastai.tabular.all import *
    FASTAI_AVAILABLE = True
except ImportError:
    FASTAI_AVAILABLE = False

def main():
    model_pack_dir = PROJECT_ROOT / 'model_pack'
    data_path = model_pack_dir / 'updated_training_data.csv'
    
    # Load data and filter for Week 13 2025
    print(f"Loading data from {data_path}")
    df = pd.read_csv(data_path, low_memory=False)
    
    week13_df = df[(df['season'] == 2025) & (df['week'] == 13)].copy()
    print(f"Found {len(week13_df)} games for Week 13")
    
    if len(week13_df) == 0:
        print("No Week 13 games found!")
        return

    # Load Models
    print("Loading models...")
    try:
        ridge_model = joblib.load(model_pack_dir / 'ridge_model_2025.joblib')
        xgb_model = joblib.load(model_pack_dir / 'xgb_home_win_model_2025.pkl')
        if FASTAI_AVAILABLE:
            fastai_model = load_learner(model_pack_dir / 'fastai_home_win_model_2025.pkl')
        else:
            fastai_model = None
    except Exception as e:
        print(f"Error loading models: {e}")
        return

    # Generate Predictions
    print("Generating predictions...")
    
    # Ridge
    X_ridge = week13_df[RIDGE_FEATURES].fillna(0)
    week13_df['pred_margin'] = ridge_model.predict(X_ridge)
    
    # XGBoost
    X_xgb = week13_df[XGB_FEATURES].fillna(0)
    week13_df['pred_win_prob_xgb'] = xgb_model.predict_proba(X_xgb)[:, 1]
    
    # FastAI
    if fastai_model:
        test_dl = fastai_model.dls.test_dl(week13_df)
        preds, _ = fastai_model.get_preds(dl=test_dl)
        week13_df['pred_win_prob_fastai'] = preds[:, 1].numpy()
    else:
        week13_df['pred_win_prob_fastai'] = np.nan
        
    # Display sample predictions
    cols = ['home_team', 'away_team', 'pred_margin', 'pred_win_prob_xgb', 'pred_win_prob_fastai']
    print("\nSample Predictions (Top 5):")
    print(week13_df[cols].head().to_string(index=False))
    
    # Save predictions
    output_path = model_pack_dir / 'week13_predictions_v2.csv'
    week13_df.to_csv(output_path, index=False)
    print(f"\nSaved predictions to {output_path}")

if __name__ == "__main__":
    main()
