#!/usr/bin/env python3
"""
Hyperparameter tuning for Ridge Regression and XGBoost models.

This script performs a time-aware hyperparameter search on the historical
college football dataset and persists the tuned models for inference.

Usage:
    python3 scripts/tune_ridge_xgb.py
"""

import logging
import sys
from pathlib import Path
from typing import Dict, Tuple

import joblib
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.linear_model import Ridge
from sklearn.metrics import accuracy_score, mean_absolute_error, roc_auc_score
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV, TimeSeriesSplit

# Add project root to import feature lists
PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from project_management.TOOLS_AND_CONFIG.model_features import (
        RIDGE_FEATURES,
        XGB_FEATURES,
    )
except ImportError:
    sys.path.append(str(PROJECT_ROOT / "project_management" / "TOOLS_AND_CONFIG"))
    from model_features import RIDGE_FEATURES, XGB_FEATURES

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

DATA_PATH = PROJECT_ROOT / "model_pack" / "updated_training_data.csv"
OUTPUT_DIR = PROJECT_ROOT / "model_pack"


def load_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Load and split the dataset into chronological train/test segments."""
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Training data not found at {DATA_PATH}")

    df = pd.read_csv(DATA_PATH, low_memory=False)

    if {"home_points", "away_points"}.issubset(df.columns):
        df = df[df["home_points"].notna() & df["away_points"].notna()].copy()
    else:
        raise ValueError("Dataset must include home_points and away_points columns.")

    df["margin"] = df["home_points"] - df["away_points"]
    df["home_win"] = (df["home_points"] > df["away_points"]).astype(int)

    if "season" in df.columns and "week" in df.columns:
        df = df.sort_values(["season", "week"]).reset_index(drop=True)

    df_2025 = df[df["season"] == 2025]
    if len(df_2025) > 0 and (df_2025["home_points"].sum() > 0):
        train_df = df[df["season"] < 2025].copy()
        test_df = df[df["season"] == 2025].copy()
        logger.info("Using 2025 season as hold-out set.")
    else:
        train_df = df[df["season"] < 2024].copy()
        test_df = df[df["season"] == 2024].copy()
        logger.info("Using 2024 season as hold-out set (no 2025 scores).")

    return train_df, test_df


def _prepare_features(
    df: pd.DataFrame, required_features: Tuple[str, ...]
) -> pd.DataFrame:
    """Ensure all required features exist and fill missing values."""
    working = df.copy()
    for feature in required_features:
        if feature not in working.columns:
            working[feature] = 0.0
    return working[list(required_features)].apply(pd.to_numeric, errors="coerce").fillna(
        0.0
    )


def tune_ridge(train_df: pd.DataFrame, test_df: pd.DataFrame) -> Dict:
    """Run grid search for Ridge Regression and persist the best model."""
    logger.info("Tuning Ridge Regression...")
    X_train = _prepare_features(train_df, tuple(RIDGE_FEATURES))
    y_train = train_df["margin"]
    X_test = _prepare_features(test_df, tuple(RIDGE_FEATURES))
    y_test = test_df["margin"]

    param_grid = {
        "alpha": np.logspace(-3, 3, 10),
        "fit_intercept": [True, False],
    }

    grid = GridSearchCV(
        estimator=Ridge(random_state=42),
        param_grid=param_grid,
        cv=TimeSeriesSplit(n_splits=5),
        scoring="neg_mean_absolute_error",
        n_jobs=-1,
    )
    grid.fit(X_train, y_train)

    best_model = grid.best_estimator_
    preds = best_model.predict(X_test)
    mae = mean_absolute_error(y_test, preds)

    model_path = OUTPUT_DIR / "ridge_model_2025.joblib"
    joblib.dump(best_model, model_path)
    logger.info(
        "Best Ridge params: %s | Hold-out MAE: %.3f | Saved: %s",
        grid.best_params_,
        mae,
        model_path,
    )

    return {
        "best_params": grid.best_params_,
        "mae": mae,
        "model_path": str(model_path),
    }


def tune_xgboost(train_df: pd.DataFrame, test_df: pd.DataFrame) -> Dict:
    """Run randomized search for XGBoost classifier and persist the best model."""
    logger.info("Tuning XGBoost...")
    X_train = _prepare_features(train_df, tuple(XGB_FEATURES))
    y_train = train_df["home_win"]
    X_test = _prepare_features(test_df, tuple(XGB_FEATURES))
    y_test = test_df["home_win"]

    param_distributions = {
        "n_estimators": [200, 350, 500, 650],
        "max_depth": [3, 4, 5, 6],
        "learning_rate": [0.03, 0.05, 0.08, 0.1],
        "subsample": [0.7, 0.85, 1.0],
        "colsample_bytree": [0.7, 0.85, 1.0],
        "min_child_weight": [1, 3, 5],
        "gamma": [0, 0.1, 0.2],
    }

    search = RandomizedSearchCV(
        estimator=xgb.XGBClassifier(
            eval_metric="logloss",
            objective="binary:logistic",
            random_state=42,
            tree_method="hist",
            n_jobs=-1,
        ),
        param_distributions=param_distributions,
        n_iter=20,
        cv=TimeSeriesSplit(n_splits=4),
        scoring="neg_log_loss",
        verbose=1,
        random_state=42,
        n_jobs=-1,
    )
    search.fit(X_train, y_train)

    best_model = search.best_estimator_
    y_pred = best_model.predict(X_test)
    y_proba = best_model.predict_proba(X_test)[:, 1]
    acc = accuracy_score(y_test, y_pred)
    auc = roc_auc_score(y_test, y_proba)

    model_path = OUTPUT_DIR / "xgb_home_win_model_2025.pkl"
    joblib.dump(best_model, model_path)
    logger.info(
        "Best XGBoost params: %s | Hold-out ACC: %.3f | AUC: %.3f | Saved: %s",
        search.best_params_,
        acc,
        auc,
        model_path,
    )

    return {
        "best_params": search.best_params_,
        "accuracy": acc,
        "auc": auc,
        "model_path": str(model_path),
    }


def main():
    train_df, test_df = load_data()
    ridge_report = tune_ridge(train_df, test_df)
    xgb_report = tune_xgboost(train_df, test_df)

    logger.info("Tuning complete.")
    logger.info("Ridge -> %s", ridge_report)
    logger.info("XGBoost -> %s", xgb_report)


if __name__ == "__main__":
    main()
