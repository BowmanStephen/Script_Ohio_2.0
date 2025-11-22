#!/usr/bin/env python3
"""
Retrain Models with Full Feature Set
====================================

This script retrains the Ridge Regression, XGBoost, and FastAI models using the
complete set of features defined in project_management/TOOLS_AND_CONFIG/model_features.py.
It addresses the issue where previous models were trained on a restricted feature set,
leading to poor performance.

Usage:
    python3 scripts/retrain_models_full_features.py
"""

import sys
import os
import logging
import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, accuracy_score, log_loss, roc_auc_score, f1_score
from sklearn.model_selection import train_test_split, GridSearchCV, TimeSeriesSplit
import xgboost as xgb

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Import feature definitions
try:
    from project_management.TOOLS_AND_CONFIG.model_features import RIDGE_FEATURES, XGB_FEATURES
except ImportError:
    # Fallback if direct import fails (e.g. due to directory structure)
    sys.path.append(str(PROJECT_ROOT / "project_management" / "TOOLS_AND_CONFIG"))
    from model_features import RIDGE_FEATURES, XGB_FEATURES

# FastAI imports
try:
    from fastai.tabular.all import *
    FASTAI_AVAILABLE = True
except ImportError:
    print("Warning: FastAI not available. Neural Network training will be skipped.")
    FASTAI_AVAILABLE = False

# Optuna imports
try:
    import optuna
    OPTUNA_AVAILABLE = True
except ImportError:
    print("Warning: Optuna not available. Hyperparameter tuning will be skipped.")
    OPTUNA_AVAILABLE = False

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def load_data(data_path: Path):
    """Load and prepare the training data."""
    logger.info(f"Loading data from {data_path}")
    df = pd.read_csv(data_path, low_memory=False)
    
    # Sort by season and week for TimeSeriesSplit
    if 'season' in df.columns and 'week' in df.columns:
        df = df.sort_values(['season', 'week']).reset_index(drop=True)
    
    # Filter out games without scores (future games)
    df_with_scores = df[
        (df['home_points'].notna()) & 
        (df['away_points'].notna())
    ].copy()
    
    # Check if 2025 has valid scores (variance > 0 or mean > 0)
    df_2025 = df_with_scores[df_with_scores['season'] == 2025]
    use_2025_test = False
    if len(df_2025) > 0:
        if df_2025['home_points'].sum() > 0 or df_2025['away_points'].sum() > 0:
            use_2025_test = True
            
    if use_2025_test:
        logger.info("Using 2025 season as test set.")
        train_df = df_with_scores[df_with_scores['season'] < 2025].copy()
        test_df = df_with_scores[df_with_scores['season'] == 2025].copy()
    else:
        logger.warning("2025 season has no valid scores. Falling back to 2024 as test set.")
        train_df = df_with_scores[df_with_scores['season'] < 2024].copy()
        test_df = df_with_scores[df_with_scores['season'] == 2024].copy()
    
    # Create target variables
    for d in [train_df, test_df]:
        d['margin'] = d['home_points'] - d['away_points']
        d['home_win'] = (d['home_points'] > d['away_points']).astype(int)
    
    logger.info(f"Training set: {len(train_df)} games")
    logger.info(f"Test set: {len(test_df)} games")
    
    return train_df, test_df

def train_ridge(train_df, test_df, output_dir):
    """Train and evaluate Ridge Regression model."""
    logger.info("Training Ridge Regression model...")
    
    # Ensure all features exist
    missing_features = [f for f in RIDGE_FEATURES if f not in train_df.columns]
    if missing_features:
        logger.warning(f"Missing features for Ridge: {missing_features}")
        for f in missing_features:
            train_df[f] = 0
            test_df[f] = 0
            
    X_train = train_df[RIDGE_FEATURES].fillna(0)
    y_train = train_df['margin']
    X_test = test_df[RIDGE_FEATURES].fillna(0)
    y_test = test_df['margin']
    
    # Define hyperparameter grid
    param_grid = {'alpha': [0.01, 0.1, 1.0, 10.0, 100.0]}
    
    # Initialize GridSearchCV with TimeSeriesSplit
    tscv = TimeSeriesSplit(n_splits=5)
    
    grid = GridSearchCV(
        Ridge(),
        param_grid,
        cv=tscv,
        scoring='neg_mean_absolute_error',
        n_jobs=-1
    )
    
    # Fit grid search
    grid.fit(X_train, y_train)
    
    # Get best model
    model = grid.best_estimator_
    logger.info(f"Best Ridge alpha: {grid.best_params_['alpha']}")
    logger.info(f"Best CV Score (MAE): {-grid.best_score_:.3f}")
    
    # Evaluate
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    
    logger.info(f"Ridge Performance - MAE: {mae:.2f}, R²: {r2:.3f}")
    
    # Save
    model_path = output_dir / 'ridge_model_2025.joblib'
    joblib.dump(model, model_path)
    logger.info(f"Saved Ridge model to {model_path}")
    
    return model

def train_xgboost(train_df, test_df, output_dir):
    """Train and evaluate XGBoost model."""
    logger.info("Training XGBoost model...")
    
    # Ensure all features exist
    missing_features = [f for f in XGB_FEATURES if f not in train_df.columns]
    if missing_features:
        logger.warning(f"Missing features for XGBoost: {missing_features}")
        for f in missing_features:
            train_df[f] = 0
            test_df[f] = 0
            
    X_train = train_df[XGB_FEATURES].fillna(0)
    y_train = train_df['home_win']
    X_test = test_df[XGB_FEATURES].fillna(0)
    y_test = test_df['home_win']
    
    model = xgb.XGBClassifier(
        eval_metric='logloss',
        random_state=77,
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1
    )
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]
    
    accuracy = accuracy_score(y_test, y_pred)
    try:
        auc = roc_auc_score(y_test, y_proba)
    except ValueError:
        auc = 0.5 # Handle single class case
        
    logger.info(f"XGBoost Performance - Accuracy: {accuracy:.3f}, AUC: {auc:.3f}")
    
    # Save
    model_path = output_dir / 'xgb_home_win_model_2025.pkl'
    joblib.dump(model, model_path)
    logger.info(f"Saved XGBoost model to {model_path}")
    
    return model

def load_optimized_fastai_params(output_dir):
    """Load optimized FastAI hyperparameters from JSON file if available."""
    params_path = output_dir / 'fastai_best_params.json'
    if params_path.exists():
        logger.info(f"📊 Loading optimized hyperparameters from {params_path}")
        import json
        with open(params_path, 'r') as f:
            best_params = json.load(f)
        return best_params
    else:
        logger.info("⚠️ No optimized hyperparameters found. Using defaults.")
        logger.info("   Run 'python3 scripts/tune_fastai.py' to optimize hyperparameters.")
        return None

def train_fastai(train_df, test_df, output_dir):
    """Train and evaluate FastAI model."""
    if not FASTAI_AVAILABLE:
        return None
        
    logger.info("Training FastAI model...")
    
    # Define features
    cont_names = sorted(list(set(RIDGE_FEATURES + XGB_FEATURES)))
    cat_names = ['week', 'home_conference', 'away_conference', 'neutral_site']
    
    # Ensure columns exist
    for col in cont_names:
        if col not in train_df.columns:
            train_df[col] = 0
            test_df[col] = 0
            
    for col in cat_names:
        if col not in train_df.columns:
            train_df[col] = 'Unknown'
            test_df[col] = 'Unknown'
    
    # Load optimized parameters if available
    best_params = load_optimized_fastai_params(output_dir)
    
    if best_params:
        logger.info("Applying optimized hyperparameters...")
        learning_rate = best_params.get('learning_rate', 1e-2)
        layers = best_params.get('layers', [200, 100])
        dropout = best_params.get('dropout', 0.2)
        batch_size = best_params.get('batch_size', 64)
        n_epochs = best_params.get('n_epochs', 5)
        logger.info(f"Using optimized params: epochs={n_epochs}, batch_size={batch_size}, layers={layers}, dropout={dropout}")
    else:
        logger.info("Using default hyperparameters...")
        learning_rate = 1e-2
        layers = [200, 100]
        dropout = 0.2
        batch_size = 64
        n_epochs = 5

    # Combine for processing
    combined_df = pd.concat([train_df, test_df], ignore_index=True)
    splits = (list(range(len(train_df))), list(range(len(train_df), len(combined_df))))
    
    try:
        dls = TabularDataLoaders.from_df(
            combined_df,
            procs=[Categorify, FillMissing, Normalize],
            cat_names=cat_names,
            cont_names=cont_names,
            y_names='home_win',
            splits=splits,
            bs=batch_size
        )
        
        learn = tabular_learner(
            dls,
            metrics=[accuracy, RocAucBinary()],
            layers=layers,
            config={'ps': dropout}
        )
        
        logger.info(f"Training with: lr={learning_rate:.4f}, layers={layers}, drop={dropout:.2f}, bs={batch_size}")
        learn.fit_one_cycle(n_epochs, learning_rate)
        
        # Evaluate
        preds, targs = learn.get_preds(ds_idx=1)
        acc = accuracy_score(targs, preds.argmax(dim=1))
        logger.info(f"FastAI Performance - Accuracy: {acc:.3f}")
        
        # Save using export
        model_path = output_dir / 'fastai_home_win_model_2025.pkl'
        try:
            learn.export(model_path)
            logger.info(f"Saved FastAI model to {model_path}")
        except Exception as e:
            logger.error(f"Failed to export FastAI model (pickle issue?): {e}")
            # Fallback: try to save state dict if torch is available
            try:
                import torch
                state_path = output_dir / 'fastai_home_win_model_2025.pth'
                torch.save(learn.model.state_dict(), state_path)
                logger.info(f"Saved FastAI state dict to {state_path}")
            except ImportError:
                logger.warning("Could not save model state dict (torch not available)")
        
        return learn
        
    except Exception as e:
        logger.error(f"FastAI training failed: {e}")
        return None

def main():
    data_path = PROJECT_ROOT / 'model_pack' / 'updated_training_data.csv'
    output_dir = PROJECT_ROOT / 'model_pack'
    
    if not data_path.exists():
        logger.error(f"Data file not found: {data_path}")
        return
        
    train_df, test_df = load_data(data_path)
    
    train_ridge(train_df, test_df, output_dir)
    train_xgboost(train_df, test_df, output_dir)
    train_fastai(train_df, test_df, output_dir)
    
    logger.info("Retraining complete!")

if __name__ == "__main__":
    main()
