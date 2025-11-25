#!/usr/bin/env python3
"""
Enhanced Week 14 Predictions with Model Feature Alignment
==========================================================

This script:
1. Loads Week 14 games and features from training_data_2025_week14.csv
2. Transforms features to match model training schema
3. Generates predictions using Ridge, XGBoost, FastAI, Logistic Regression, and Random Forest models
4. Fetches SP+ ratings from GraphQL API (with CSV fallback)
5. Creates weighted ensemble predictions combining all models and SP+
6. Calculates confidence scores and model agreement metrics
7. Saves comprehensive predictions (CSV and JSON)

Optional Features:
- Hyperparameter tuning for Ridge and XGBoost models (--tune-hyperparameters)
- Weighted ensemble with default weights: Ridge 25%, XGBoost 25%, FastAI 15%, Logistic 15%, Random Forest 10%, SP+ 10%

Usage:
    python3 scripts/predict_week14_proper.py
    python3 scripts/predict_week14_proper.py --tune-hyperparameters
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

import pandas as pd
import numpy as np
import joblib
import pickle

from src.observability import (
    ErrorCategory,
    ErrorSeverity,
    configure_logging,
    get_logger,
)

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

configure_logging(service_name="predict_week14")
logger = get_logger(
    __name__, component="prediction_script", service_name="predict_week14"
)

# Ensemble weighting (renormalized based on available model outputs)
ENSEMBLE_WEIGHTS = {
    'ridge': 0.25,
    'xgb': 0.25,
    'fastai': 0.15,
    'logistic': 0.15,
    'random_forest': 0.10,
    'sp': 0.10,
}

# Try importing hyperparameter tuning libraries
try:
    from sklearn.model_selection import GridSearchCV, TimeSeriesSplit
    from sklearn.linear_model import Ridge
    from sklearn.metrics import mean_absolute_error, r2_score, accuracy_score, roc_auc_score
    TUNING_AVAILABLE = True
except ImportError:
    TUNING_AVAILABLE = False
    logger.warning(
        "sklearn not available for hyperparameter tuning",
        extra={
            "event": "dependency_missing",
            "error.category": ErrorCategory.MODEL.value,
            "severity": ErrorSeverity.WARNING.value,
        },
    )

try:
    import xgboost as xgb
    XGB_AVAILABLE = True
except ImportError:
    XGB_AVAILABLE = False

# Try importing GraphQL client for SP+ ratings
try:
    from src.data_sources.cfbd_graphql import CFBDGraphQLClient
    GQL_AVAILABLE = True
except ImportError:
    GQL_AVAILABLE = False
    logger.warning(
        "GraphQL client not available. SP+ ratings will use CSV fallback only.",
        extra={
            "event": "dependency_missing",
            "error.category": ErrorCategory.MODEL.value,
            "severity": ErrorSeverity.WARNING.value,
        },
    )

# Try importing model config
try:
    from config.model_config import get_model_config  # type: ignore
    MODEL_CONFIG_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    MODEL_CONFIG_AVAILABLE = False
    get_model_config = None  # type: ignore
    logger.warning(
        "Model config not available. Using fallback feature lists.",
        extra={
            "event": "dependency_missing",
            "error.category": ErrorCategory.MODEL.value,
            "severity": ErrorSeverity.WARNING.value,
        },
    )


def load_models():
    """Load trained models."""
    model_pack_dir = PROJECT_ROOT / 'model_pack'
    
    models = {}
    
    # Load Ridge model
    ridge_path = model_pack_dir / 'ridge_model_2025.joblib'
    if ridge_path.exists():
        try:
            models['ridge'] = joblib.load(ridge_path)
            logger.info(
                "Loaded Ridge model",
                extra={"event": "model_loaded", "model": "ridge", "path": str(ridge_path)},
            )
        except Exception as e:
            logger.error(
                "Failed to load Ridge model",
                extra={
                    "event": "model_load_failed",
                    "model": "ridge",
                    "path": str(ridge_path),
                    "error.category": ErrorCategory.MODEL.value,
                    "error.detail": str(e),
                },
            )
    else:
        logger.warning(
            "Ridge model not found",
            extra={
                "event": "model_missing",
                "model": "ridge",
                "path": str(ridge_path),
                "error.category": ErrorCategory.MODEL.value,
            },
        )
    
    # Load XGBoost model
    xgb_path = model_pack_dir / 'xgb_home_win_model_2025.pkl'
    if xgb_path.exists():
        try:
            with open(xgb_path, 'rb') as f:
                models['xgb'] = pickle.load(f)
            logger.info(
                "Loaded XGBoost model",
                extra={"event": "model_loaded", "model": "xgboost", "path": str(xgb_path)},
            )
        except Exception as e:
            logger.error(
                "Failed to load XGBoost model",
                extra={
                    "event": "model_load_failed",
                    "model": "xgboost",
                    "path": str(xgb_path),
                    "error.category": ErrorCategory.MODEL.value,
                    "error.detail": str(e),
                },
            )
    else:
        logger.warning(
            "XGBoost model not found",
            extra={
                "event": "model_missing",
                "model": "xgboost",
                "path": str(xgb_path),
                "error.category": ErrorCategory.MODEL.value,
            },
        )

    # Load FastAI model
    fastai_path = model_pack_dir / 'fastai_home_win_model_2025.pkl'
    if fastai_path.exists():
        try:
            from fastai.tabular.all import load_learner
            models['fastai'] = load_learner(fastai_path)
            logger.info(
                "Loaded FastAI model",
                extra={"event": "model_loaded", "model": "fastai", "path": str(fastai_path)},
            )
        except Exception as e:
            logger.error(
                "Failed to load FastAI model",
                extra={
                    "event": "model_load_failed",
                    "model": "fastai",
                    "path": str(fastai_path),
                    "error.category": ErrorCategory.MODEL.value,
                    "error.detail": str(e),
                },
            )
    else:
        logger.warning(
            "FastAI model not found",
            extra={
                "event": "model_missing",
                "model": "fastai",
                "path": str(fastai_path),
                "error.category": ErrorCategory.MODEL.value,
            },
        )
    
    # Load Logistic Regression model
    logistic_path = model_pack_dir / 'logistic_regression_model.joblib'
    if logistic_path.exists():
        try:
            models['logistic'] = joblib.load(logistic_path)
            logger.info(
                "Loaded Logistic Regression model",
                extra={"event": "model_loaded", "model": "logistic", "path": str(logistic_path)},
            )
        except Exception as e:
            logger.error(
                "Failed to load Logistic Regression model",
                extra={
                    "event": "model_load_failed",
                    "model": "logistic",
                    "path": str(logistic_path),
                    "error.category": ErrorCategory.MODEL.value,
                    "error.detail": str(e),
                },
            )
    else:
        logger.warning(
            "Logistic Regression model not found",
            extra={
                "event": "model_missing",
                "model": "logistic",
                "path": str(logistic_path),
                "error.category": ErrorCategory.MODEL.value,
            },
        )
    
    # Load Random Forest model
    rf_path = model_pack_dir / 'random_forest_model_2025.pkl'
    if rf_path.exists():
        try:
            # Try loading as pickle first (if it's a saved RandomForestScorePredictor instance)
            try:
                with open(rf_path, 'rb') as f:
                    models['random_forest'] = pickle.load(f)
                logger.info(
                    "Loaded Random Forest model (pickle)",
                    extra={"event": "model_loaded", "model": "random_forest", "path": str(rf_path)},
                )
            except Exception:
                # Fallback: try loading as joblib
                models['random_forest'] = joblib.load(rf_path)
                logger.info(
                    "Loaded Random Forest model (joblib)",
                    extra={"event": "model_loaded", "model": "random_forest", "path": str(rf_path)},
                )
        except Exception as e:
            logger.error(
                "Failed to load Random Forest model",
                extra={
                    "event": "model_load_failed",
                    "model": "random_forest",
                    "path": str(rf_path),
                    "error.category": ErrorCategory.MODEL.value,
                    "error.detail": str(e),
                },
            )
    else:
        logger.warning(
            "Random Forest model not found",
            extra={
                "event": "model_missing",
                "model": "random_forest",
                "path": str(rf_path),
                "error.category": ErrorCategory.MODEL.value,
            },
        )
    
    return models


def get_model_features(models: Dict[str, Any]) -> Dict[str, List[str]]:
    """Get required features for each model"""
    features = {}
    
    # Use imported get_model_config if available
    get_model_config_func = get_model_config if MODEL_CONFIG_AVAILABLE else None
    
    if 'ridge' in models and hasattr(models['ridge'], 'feature_names_in_'):
        features['ridge'] = list(models['ridge'].feature_names_in_)
        logger.info(f"Ridge features: {len(features['ridge'])} features")
    elif get_model_config_func:
        config = get_model_config_func('ridge')
        if config:
            features['ridge'] = config['features']
    
    if 'xgb' in models:
        try:
            booster = models['xgb'].get_booster()
            features['xgb'] = list(booster.feature_names)
            logger.info(f"XGBoost features: {len(features['xgb'])} features")
        except:
            # Fallback: use config or training data to infer features
            if get_model_config_func:
                config = get_model_config_func('xgb')
                if config:
                    features['xgb'] = config['features']
            else:
                # Legacy fallback
                training_path = PROJECT_ROOT / 'model_pack' / 'updated_training_data.csv'
                if training_path.exists():
                    df = pd.read_csv(training_path, nrows=1)
                    features['xgb'] = [
                        'home_talent', 'away_talent', 'spread', 'home_elo', 'away_elo',
                        'home_adjusted_epa', 'home_adjusted_epa_allowed',
                        'away_adjusted_epa', 'away_adjusted_epa_allowed',
                        'home_adjusted_success', 'home_adjusted_success_allowed',
                        'away_adjusted_success', 'away_adjusted_success_allowed'
                    ]
    
    if 'fastai' in models:
        try:
            # FastAI stores feature names in dls.x_names
            fastai_features = getattr(getattr(models['fastai'], 'dls', None), 'x_names', None)
            if fastai_features:
                features['fastai'] = list(fastai_features)
                logger.info(f"FastAI features: {len(features['fastai'])} features")
            else:
                # Fallback: use same features as XGBoost
                features['fastai'] = features.get('xgb', [])
                logger.info(f"FastAI features (fallback to XGBoost schema): {len(features['fastai'])} features")
        except Exception as e:
            logger.warning(
                "Could not extract FastAI features, using XGBoost schema",
                extra={
                    "event": "feature_schema_fallback",
                    "model": "fastai",
                    "error.category": ErrorCategory.MODEL.value,
                    "error.detail": str(e),
                },
            )
            features['fastai'] = features.get('xgb', [])
    
    # Logistic Regression features
    if 'logistic' in models:
        if hasattr(models['logistic'], 'feature_names_in_'):
            features['logistic'] = list(models['logistic'].feature_names_in_)
            logger.info(f"Logistic Regression features: {len(features['logistic'])} features")
        elif get_model_config_func:
            config = get_model_config_func('logistic')
            if config:
                features['logistic'] = config['features']
                logger.info(f"Logistic Regression features (from config): {len(features['logistic'])} features")
        else:
            # Fallback feature list
            features['logistic'] = [
                'home_adjusted_epa', 'home_adjusted_epa_allowed',
                'away_adjusted_epa', 'away_adjusted_epa_allowed',
                'home_talent', 'away_talent', 'home_elo', 'away_elo'
            ]
            logger.info(f"Logistic Regression features (fallback): {len(features['logistic'])} features")
    
    # Random Forest features
    if 'random_forest' in models:
        try:
            # Check if model has features attribute (RandomForestScorePredictor)
            if hasattr(models['random_forest'], 'features'):
                features['random_forest'] = list(models['random_forest'].features)
                logger.info(f"Random Forest features: {len(features['random_forest'])} features")
            elif get_model_config_func:
                config = get_model_config_func('random_forest')
                if config:
                    features['random_forest'] = config['features']
                    logger.info(f"Random Forest features (from config): {len(features['random_forest'])} features")
            else:
                # Fallback feature list
                features['random_forest'] = [
                    'home_adjusted_success', 'home_adjusted_success_allowed',
                    'away_adjusted_success', 'away_adjusted_success_allowed',
                    'home_adjusted_rushing_epa', 'home_adjusted_rushing_epa_allowed',
                    'away_adjusted_rushing_epa', 'away_adjusted_rushing_epa_allowed',
                    'home_adjusted_passing_epa', 'home_adjusted_passing_epa_allowed',
                    'away_adjusted_passing_epa', 'away_adjusted_passing_epa_allowed'
                ]
                logger.info(f"Random Forest features (fallback): {len(features['random_forest'])} features")
        except Exception as e:
            logger.warning(
                "Could not extract Random Forest features",
                extra={
                    "event": "feature_schema_fallback",
                    "model": "random_forest",
                    "error.category": ErrorCategory.MODEL.value,
                    "error.detail": str(e),
                },
            )
            if get_model_config_func:
                config = get_model_config_func('random_forest')
                if config:
                    features['random_forest'] = config['features']
    
    return features


def load_week14_data():
    """Load Week 14 games and features"""
    # Primary source: training data file for Week 14 (contains features)
    week14_training_path = PROJECT_ROOT / 'data' / 'training' / 'weekly' / 'training_data_2025_week14.csv'
    
    week14_data = {}
    
    if week14_training_path.exists():
        df = pd.read_csv(week14_training_path, low_memory=False)
        week14_data['features'] = df
        week14_data['games'] = df # It contains game info too
        logger.info(f"✅ Loaded Week 14 data from training file: {len(df)} games")
    else:
        logger.warning(
            "Week 14 training data not found",
            extra={
                "event": "data_missing",
                "path": str(week14_training_path),
                "error.category": ErrorCategory.DATA.value,
            },
        )
        
        # Fallback to enhanced features if they exist (unlikely if training data missing but good to check)
        week14_features_path = PROJECT_ROOT / 'data' / 'week14' / 'enhanced' / 'week14_features_86.csv'
        if week14_features_path.exists():
             week14_data['features'] = pd.read_csv(week14_features_path)
             logger.info(f"✅ Loaded Week 14 features from enhanced dir: {len(week14_data['features'])} games")
    
    return week14_data


def get_feature_defaults_from_training() -> Dict[str, float]:
    """Get default feature values from training data"""
    training_path = PROJECT_ROOT / 'model_pack' / 'updated_training_data.csv'
    defaults = {}
    
    if training_path.exists():
        try:
            df = pd.read_csv(training_path)
            # Get median values for numeric columns
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            for col in numeric_cols:
                median_val = df[col].median()
                if pd.notna(median_val):
                    defaults[col] = float(median_val)
            logger.info(f"✅ Loaded {len(defaults)} feature defaults from training data")
        except Exception as e:
            logger.warning(
                "Could not load feature defaults",
                extra={
                    "event": "feature_defaults_failed",
                    "path": str(training_path),
                    "error.category": ErrorCategory.DATA.value,
                    "error.detail": str(e),
                },
            )
    
    return defaults


def tune_ridge_hyperparameters(
    training_data: pd.DataFrame,
    feature_cols: List[str],
    target_col: str = 'margin'
) -> Dict[str, Any]:
    """
    Tune Ridge regression hyperparameters using GridSearchCV.
    
    Args:
        training_data: Training DataFrame with features and target
        feature_cols: List of feature column names
        target_col: Target column name
        
    Returns:
        Dictionary with best parameters and performance metrics
    """
    if not TUNING_AVAILABLE:
        logger.warning(
            "Hyperparameter tuning not available",
            extra={
                "event": "tuning_unavailable",
                "model": "ridge",
                "error.category": ErrorCategory.MODEL.value,
                "severity": ErrorSeverity.WARNING.value,
            },
        )
        return {}
    
    logger.info("🔍 Tuning Ridge hyperparameters...")
    
    X = training_data[feature_cols].fillna(0)
    y = training_data[target_col]
    
    # Define hyperparameter grid
    param_grid = {
        'alpha': [0.01, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 50.0, 100.0]
    }
    
    # Use TimeSeriesSplit for temporal validation
    tscv = TimeSeriesSplit(n_splits=5)
    
    # Grid search
    grid = GridSearchCV(
        Ridge(),
        param_grid,
        cv=tscv,
        scoring='neg_mean_absolute_error',
        n_jobs=-1,
        verbose=1
    )
    
    grid.fit(X, y)
    
    best_params = {
        'alpha': grid.best_params_['alpha'],
        'best_cv_score': -grid.best_score_,
        'best_estimator': grid.best_estimator_
    }
    
    logger.info(f"✅ Best Ridge alpha: {best_params['alpha']}")
    logger.info(f"✅ Best CV MAE: {best_params['best_cv_score']:.3f}")
    
    return best_params


def tune_xgboost_hyperparameters(
    training_data: pd.DataFrame,
    feature_cols: List[str],
    target_col: str = 'home_win'
) -> Dict[str, Any]:
    """
    Tune XGBoost hyperparameters using GridSearchCV.
    
    Args:
        training_data: Training DataFrame with features and target
        feature_cols: List of feature column names
        target_col: Target column name
        
    Returns:
        Dictionary with best parameters and performance metrics
    """
    if not TUNING_AVAILABLE or not XGB_AVAILABLE:
        logger.warning(
            "XGBoost hyperparameter tuning not available",
            extra={
                "event": "tuning_unavailable",
                "model": "xgboost",
                "error.category": ErrorCategory.MODEL.value,
                "severity": ErrorSeverity.WARNING.value,
            },
        )
        return {}
    
    logger.info("🔍 Tuning XGBoost hyperparameters...")
    
    X = training_data[feature_cols].fillna(0)
    y = training_data[target_col]
    
    # Define hyperparameter grid (reduced for faster execution)
    param_grid = {
        'n_estimators': [50, 100, 200],
        'max_depth': [4, 6, 8],
        'learning_rate': [0.05, 0.1, 0.2],
        'subsample': [0.8, 0.9, 1.0],
        'colsample_bytree': [0.8, 0.9, 1.0]
    }
    
    # Use TimeSeriesSplit for temporal validation
    tscv = TimeSeriesSplit(n_splits=3)  # Reduced for speed
    
    # Base model
    base_model = xgb.XGBClassifier(
        eval_metric='logloss',
        random_state=77,
        use_label_encoder=False
    )
    
    # Grid search
    grid = GridSearchCV(
        base_model,
        param_grid,
        cv=tscv,
        scoring='accuracy',
        n_jobs=-1,
        verbose=1
    )
    
    grid.fit(X, y)
    
    best_params = {
        'n_estimators': grid.best_params_['n_estimators'],
        'max_depth': grid.best_params_['max_depth'],
        'learning_rate': grid.best_params_['learning_rate'],
        'subsample': grid.best_params_['subsample'],
        'colsample_bytree': grid.best_params_['colsample_bytree'],
        'best_cv_score': grid.best_score_,
        'best_estimator': grid.best_estimator_
    }
    
    logger.info(f"✅ Best XGBoost params: {best_params}")
    logger.info(f"✅ Best CV Accuracy: {best_params['best_cv_score']:.3f}")
    
    return best_params


def margin_to_probability(margin: Optional[float], scale: float = 14.0) -> Optional[float]:
    """Convert a predicted margin into a home-win probability via logistic mapping."""
    if margin is None or pd.isna(margin):
        return None
    try:
        return float(1.0 / (1.0 + np.exp(-margin / scale)))
    except Exception:
        return None


def normalize_team_name(team_name: str) -> str:
    """
    Normalize team name for matching between different data sources.
    Handles variations like 'Miami-FL' vs 'Miami (FL)' vs 'Miami'.
    """
    if pd.isna(team_name) or not team_name:
        return ""
    
    team = str(team_name).strip()
    
    # Common variations mapping
    variations = {
        'Ohio State': 'Ohio State',
        'Ohio St.': 'Ohio State',
        'Ohio St': 'Ohio State',
        'Miami-FL': 'Miami',
        'Miami (FL)': 'Miami',
        'Miami-Florida': 'Miami',
        'Miami-OH': 'Miami OH',
        'Miami (OH)': 'Miami OH',
        'Miami Ohio': 'Miami OH',
        'UL-Lafayette': 'Louisiana',
        'Louisiana-Lafayette': 'Louisiana',
        'UL-Monroe': 'UL-Monroe',
        'UL Monroe': 'UL-Monroe',
        'Louisiana-Monroe': 'UL-Monroe',
        'Appalachian State': 'Appalachian State',
        'App State': 'Appalachian State',
        'Florida Atlantic': 'FAU',
        'Florida International': 'FIU',
        'San Jose State': 'San Jose State',
        'San José State': 'San Jose State',
        'San Jose St.': 'San Jose State',
        'Hawaii': 'Hawaii',
        "Hawai'i": 'Hawaii',
        'UCF': 'UCF',
        'Central Florida': 'UCF',
        'USF': 'USF',
        'South Florida': 'USF',
    }
    
    # Check exact match first
    if team in variations:
        return variations[team]
    
    # Handle hyphenated names (CSV format: "Miami-FL")
    if '-' in team:
        parts = team.split('-')
        if len(parts) == 2:
            name, suffix = parts
            if suffix.upper() in ['FL', 'OH', 'CA', 'TX', 'NY']:
                if suffix.upper() == 'FL':
                    return 'Miami' if 'Miami' in name else name
                elif suffix.upper() == 'OH':
                    return 'Miami OH' if 'Miami' in name else name + ' OH'
                else:
                    return name
    
    # Remove common suffixes
    for suffix in [' (FL)', ' (OH)', ' St.', ' State', '-FL', '-OH']:
        if team.endswith(suffix):
            team = team[:-len(suffix)]
    
    return team


def load_sp_ratings_from_csv(csv_path: Optional[Path] = None) -> Dict[str, Dict[str, float]]:
    """
    Load SP+ ratings from CSV file.
    
    Args:
        csv_path: Path to SP+ CSV file. If None, tries default location.
    
    Returns:
        Dict mapping team_name -> {'sp': rating, 'fpi': None}
    """
    if csv_path is None:
        # Try default locations
        default_paths = [
            PROJECT_ROOT / '2025 SP+ - FBS Week 14.csv',
            PROJECT_ROOT / 'data' / '2025 SP+ - FBS Week 14.csv',
        ]
        for path in default_paths:
            if path.exists():
                csv_path = path
                break
    
    if csv_path is None or not csv_path.exists():
        logger.debug("⚠️  SP+ CSV file not found, skipping CSV load")
        return {}
    
    try:
        logger.info(f"📂 Loading SP+ ratings from CSV: {csv_path}")
        df = pd.read_csv(csv_path, low_memory=False)
        
        # Map column names (handle variations)
        team_col = 'Team' if 'Team' in df.columns else 'team' if 'team' in df.columns else df.columns[0]
        sp_col = None
        for col in df.columns:
            col_lower = str(col).lower()
            if 'sp+' in col_lower and 'off' not in col_lower and 'def' not in col_lower and 'st' not in col_lower:
                sp_col = col
                break
        
        if sp_col is None:
            logger.warning(f"⚠️  Could not find SP+ column in CSV. Available columns: {list(df.columns)}")
            return {}
        
        team_ratings = {}
        for _, row in df.iterrows():
            team = row[team_col]
            sp_rating = row[sp_col]
            
            if pd.notna(team) and pd.notna(sp_rating):
                team_str = str(team).strip()
                normalized_name = normalize_team_name(team_str)
                
                # Store with original name (primary key)
                if team_str not in team_ratings:
                    team_ratings[team_str] = {
                        'sp': float(sp_rating),
                        'fpi': None  # CSV doesn't have FPI
                    }
                
                # Store with normalized name (only if different from original)
                if normalized_name != team_str and normalized_name not in team_ratings:
                    team_ratings[normalized_name] = {
                        'sp': float(sp_rating),
                        'fpi': None
                    }
        
        logger.info(f"  ✅ Loaded SP+ ratings for {len(team_ratings)} teams from CSV")
        return team_ratings
        
    except Exception as e:
        logger.warning(
            f"⚠️  Error loading SP+ CSV: {e}",
            extra={
                "event": "sp_csv_load_failed",
                "error.category": ErrorCategory.DATA.value,
                "error.detail": str(e),
            },
        )
        return {}


def fetch_sp_fpi_ratings(season: int = 2025, use_csv: bool = True) -> Dict[str, Dict[str, float]]:
    """
    Fetch SP+ and FPI ratings from CFBD GraphQL API, optionally supplemented with CSV.
    
    Args:
        season: Season year
        use_csv: If True, load SP+ from CSV as primary source, use API for FPI
    
    Returns:
        Dict mapping team_name -> {'sp': rating, 'fpi': rating}
    """
    ratings = {}
    
    # Try to load from CSV first (more reliable for SP+)
    if use_csv:
        csv_ratings = load_sp_ratings_from_csv()
        if csv_ratings:
            ratings.update(csv_ratings)
            logger.info(f"✅ Loaded {len(csv_ratings)} SP+ ratings from CSV")
    
    # Fetch from API for FPI (and supplement SP+ if CSV missing some teams)
    if GQL_AVAILABLE:
        api_key = os.getenv("CFBD_API_KEY")
        if api_key:
            try:
                logger.info(f"📡 Fetching SP+/FPI ratings from CFBD GraphQL API...")
                client = CFBDGraphQLClient(api_key=api_key)
                result = client.get_ratings(season=season)
                
                # Handle both response formats
                if 'ratings' in result:
                    api_ratings = result['ratings']
                elif 'data' in result and 'ratings' in result['data']:
                    api_ratings = result['data']['ratings']
                else:
                    logger.warning("⚠️  No ratings data in GraphQL response")
                    api_ratings = []
                
                if api_ratings:
                    # Merge API ratings (prefer CSV for SP+, use API for FPI)
                    for rating in api_ratings:
                        team = rating.get('team')
                        if team:
                            normalized = normalize_team_name(team)
                            
                            # Initialize if not exists
                            if normalized not in ratings:
                                ratings[normalized] = {'sp': None, 'fpi': None}
                            
                            # Use API SP+ only if CSV didn't have it
                            if ratings[normalized]['sp'] is None:
                                ratings[normalized]['sp'] = rating.get('spOverall')
                            
                            # Always use API FPI (CSV doesn't have it)
                            fpi_rating = rating.get('fpi')
                            if fpi_rating is not None:
                                ratings[normalized]['fpi'] = fpi_rating
                    
                    logger.info(f"  ✅ Merged API ratings for {len(api_ratings)} teams")
                
            except Exception as e:
                logger.warning(
                    f"⚠️  Failed to fetch from API: {e}",
                    extra={
                        "event": "sp_api_fetch_failed",
                        "error.category": ErrorCategory.DATA.value,
                        "error.detail": str(e),
                    },
                )
                # Continue with CSV data only
    else:
        logger.info("GraphQL client not available, using CSV only for SP+ ratings")
    
    # Filter out entries with no ratings at all
    ratings = {k: v for k, v in ratings.items() if v.get('sp') is not None or v.get('fpi') is not None}
    
    logger.info(f"✅ Total ratings loaded: {len(ratings)} teams")
    return ratings


def calculate_sp_predicted_margin(home_sp: Optional[float], away_sp: Optional[float], 
                                 neutral_site: bool = False) -> Optional[float]:
    """Calculate predicted margin from SP+ ratings."""
    if home_sp is None or away_sp is None:
        return None
    
    base_margin = home_sp - away_sp
    home_advantage = 2.5 if not neutral_site else 0.0
    return base_margin + home_advantage


def transform_week14_for_models(week14_data: Dict[str, pd.DataFrame], 
                                model_features: Dict[str, List[str]],
                                defaults: Dict[str, float]) -> Dict[str, pd.DataFrame]:
    """Transform Week 14 data to match model feature requirements"""
    
    transformed = {}
    
    # Start with features if available
    if 'features' in week14_data:
        features_df = week14_data['features'].copy()
    else:
        logger.error("❌ No Week 14 features found")
        return {}
    
    # For each model, create aligned feature matrix
    for model_name, required_features in model_features.items():
        aligned_df = pd.DataFrame(index=features_df.index)
        
        for feature in required_features:
            if feature in features_df.columns:
                aligned_df[feature] = pd.to_numeric(features_df[feature], errors='coerce')
            else:
                # Use default value
                default_val = defaults.get(feature, 0.0)
                aligned_df[feature] = default_val
                logger.debug(f"Using default for {feature}: {default_val}")
        
        # Fill any remaining NaN values with defaults
        for feature in required_features:
            if feature in aligned_df.columns:
                aligned_df[feature] = aligned_df[feature].fillna(defaults.get(feature, 0.0))
        
        transformed[model_name] = aligned_df
        logger.info(f"✅ Transformed data for {model_name}: {len(aligned_df)} games, {len(aligned_df.columns)} features")
    
    return transformed


def create_ensemble_prediction(
    ridge_margin: Optional[float],
    xgb_prob: Optional[float],
    fastai_prob: Optional[float],
    logistic_prob: Optional[float] = None,
    rf_margin: Optional[float] = None,
    sp_margin: Optional[float] = None,
    model_weights: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Create ensemble prediction from individual model predictions.
    
    Args:
        ridge_margin: Ridge regression predicted margin
        xgb_prob: XGBoost home win probability
        fastai_prob: FastAI home win probability
        logistic_prob: Logistic Regression home win probability
        rf_margin: Random Forest predicted margin
        sp_margin: SP+ predicted margin
        model_weights: Optional weights for each model
        
    Returns:
        Dictionary with ensemble predictions
    """
    if model_weights is None:
        # Default weights based on model performance
        # Original: Ridge 0.3, XGBoost 0.5, FastAI 0.2
        # Updated with new models: rebalanced to include all 6 (5 ML + SP+)
        model_weights = ENSEMBLE_WEIGHTS.copy()
    
    ensemble = {
        'ensemble_margin': np.nan,
        'ensemble_home_win_prob': np.nan,
        'ensemble_away_win_prob': np.nan,
        'ensemble_confidence': 0.0,
        'models_used': [],
        'model_agreement': 'unknown'
    }
    
    # Collect available predictions
    available_models = []
    margins = []
    probs = []
    weights = []
    
    # Ridge margin (convert to probability for ensemble)
    if ridge_margin is not None and not np.isnan(ridge_margin):
        available_models.append('ridge')
        margins.append(ridge_margin)
        # Convert margin to probability (sigmoid-like transformation)
        # Using a simple linear mapping: margin of +14 = ~75% win prob
        ridge_prob = 0.5 + (ridge_margin / 28.0)  # Scale factor
        ridge_prob = np.clip(ridge_prob, 0.05, 0.95)  # Clip to reasonable range
        probs.append(ridge_prob)
        weights.append(model_weights.get('ridge', 0.3))
    
    # XGBoost probability
    if xgb_prob is not None and not np.isnan(xgb_prob):
        available_models.append('xgb')
        probs.append(xgb_prob)
        weights.append(model_weights.get('xgb', 0.5))
        # Convert probability to margin estimate
        xgb_margin = (xgb_prob - 0.5) * 28.0  # Inverse of above
        margins.append(xgb_margin)
    
    # FastAI probability
    if fastai_prob is not None and not np.isnan(fastai_prob):
        available_models.append('fastai')
        probs.append(fastai_prob)
        weights.append(model_weights.get('fastai', 0.15))
        # Convert probability to margin estimate
        fastai_margin = (fastai_prob - 0.5) * 28.0
        margins.append(fastai_margin)
    
    # Logistic Regression probability
    if logistic_prob is not None and not np.isnan(logistic_prob):
        available_models.append('logistic')
        probs.append(logistic_prob)
        weights.append(model_weights.get('logistic', 0.15))
        # Convert probability to margin estimate
        logistic_margin = (logistic_prob - 0.5) * 28.0
        margins.append(logistic_margin)
    
    # Random Forest margin (convert to probability for ensemble)
    if rf_margin is not None and not np.isnan(rf_margin):
        available_models.append('random_forest')
        margins.append(rf_margin)
        # Convert margin to probability
        rf_prob = 0.5 + (rf_margin / 28.0)
        rf_prob = np.clip(rf_prob, 0.05, 0.95)
        probs.append(rf_prob)
        weights.append(model_weights.get('random_forest', 0.10))
    
    # SP+ margin (convert to probability for ensemble)
    if sp_margin is not None and not np.isnan(sp_margin):
        available_models.append('sp')
        margins.append(sp_margin)
        # Convert margin to probability
        sp_prob = 0.5 + (sp_margin / 28.0)
        sp_prob = np.clip(sp_prob, 0.05, 0.95)
        probs.append(sp_prob)
        weights.append(model_weights.get('sp', 0.10))
    
    if not available_models:
        return ensemble
    
    ensemble['models_used'] = available_models
    
    # Normalize weights
    total_weight = sum(weights)
    if total_weight > 0:
        weights = [w / total_weight for w in weights]
    
    # Weighted average of probabilities
    if probs:
        ensemble['ensemble_home_win_prob'] = np.average(probs, weights=weights)
        ensemble['ensemble_away_win_prob'] = (
            1.0 - ensemble['ensemble_home_win_prob']
        )
        
        # Calculate confidence (agreement between models)
        if len(probs) > 1:
            prob_std = np.std(probs)
            ensemble['ensemble_confidence'] = max(0.0, 1.0 - (prob_std * 2))
        else:
            ensemble['ensemble_confidence'] = 0.5
        
        # Model agreement
        if len(probs) >= 2:
            all_agree_home = all(p > 0.5 for p in probs)
            all_agree_away = all(p < 0.5 for p in probs)
            if all_agree_home or all_agree_away:
                ensemble['model_agreement'] = 'high'
            else:
                ensemble['model_agreement'] = 'moderate'
        else:
            ensemble['model_agreement'] = 'single_model'
    
    # Weighted average of margins
    if margins:
        ensemble['ensemble_margin'] = np.average(margins, weights=weights)
    
    return ensemble


def generate_predictions(
    models: Dict[str, Any],
    transformed_data: Dict[str, pd.DataFrame],
    week14_data: Dict[str, pd.DataFrame],
) -> pd.DataFrame:
    """Generate predictions using models and combine them into an ensemble."""
    
    predictions = []
    ridge_probs = None
    
    # Get game metadata
    if 'features' in week14_data:
        # Use 'id' if available, else 'game_id'
        id_col = 'id' if 'id' in week14_data['features'].columns else 'game_id'
        cols = [id_col, 'home_team', 'away_team']
        # Add other useful cols if present
        for c in ['start_date', 'home_conference', 'away_conference', 'spread']:
            if c in week14_data['features'].columns:
                cols.append(c)
                
        games_meta = week14_data['features'][cols].copy()
        games_meta = games_meta.rename(columns={id_col: 'game_id'})
    else:
        logger.error("❌ No game metadata available")
        return pd.DataFrame()
    
    # Generate Ridge predictions (margin)
    if 'ridge' in models and 'ridge' in transformed_data:
        try:
            X_ridge = transformed_data['ridge']
            ridge_preds = models['ridge'].predict(X_ridge)
            ridge_probs = np.array(
                [margin_to_probability(val) for val in ridge_preds]
            )
            
            logger.info(f"✅ Generated Ridge predictions: {len(ridge_preds)} games")
        except Exception as e:
            logger.error(f"❌ Ridge prediction failed: {e}")
            ridge_preds = None
            ridge_probs = None
    else:
        ridge_preds = None
        ridge_probs = None
    
    # Generate XGBoost predictions (win probability)
    if 'xgb' in models and 'xgb' in transformed_data:
        try:
            X_xgb = transformed_data['xgb']
            xgb_proba = models['xgb'].predict_proba(X_xgb)[:, 1]  # Home win probability
            
            logger.info(f"✅ Generated XGBoost predictions: {len(xgb_proba)} games")
        except Exception as e:
            logger.error(f"❌ XGBoost prediction failed: {e}")
            xgb_proba = None
    else:
        xgb_proba = None
    
    # Generate FastAI predictions (win probability)
    if 'fastai' in models and 'fastai' in transformed_data:
        try:
            X_fastai = transformed_data['fastai']
            fastai_proba = []
            
            # FastAI predict requires row-by-row processing
            for idx in range(len(X_fastai)):
                pred_class, pred_idx, probs = models['fastai'].predict(X_fastai.iloc[idx])
                # probs is a tensor with [away_win_prob, home_win_prob]
                home_win_prob = float(probs[1]) if len(probs) > 1 else float(probs[0])
                home_win_prob = float(np.clip(home_win_prob, 0.0, 1.0))
                fastai_proba.append(home_win_prob)
            
            fastai_proba = np.array(fastai_proba)
            logger.info(f"✅ Generated FastAI predictions: {len(fastai_proba)} games")
        except Exception as e:
            logger.error(f"❌ FastAI prediction failed: {e}")
            fastai_proba = None
    else:
        fastai_proba = None
    
    # Generate Logistic Regression predictions (win probability)
    if 'logistic' in models and 'logistic' in transformed_data:
        try:
            X_logistic = transformed_data['logistic']
            # Logistic regression returns probabilities
            logistic_proba = models['logistic'].predict_proba(X_logistic)[:, 1]  # Home win probability
            
            logger.info(f"✅ Generated Logistic Regression predictions: {len(logistic_proba)} games")
        except Exception as e:
            logger.error(f"❌ Logistic Regression prediction failed: {e}")
            logistic_proba = None
    else:
        logistic_proba = None
    
    # Generate Random Forest predictions (home_points, away_points -> margin)
    rf_preds = None
    rf_home_points = None
    rf_away_points = None
    if 'random_forest' in models and 'random_forest' in transformed_data:
        try:
            X_rf = transformed_data['random_forest']
            rf_model = models['random_forest']
            
            # Check if it's a RandomForestScorePredictor instance
            if hasattr(rf_model, 'predict'):
                # It's a RandomForestScorePredictor - use its predict method
                rf_results = rf_model.predict(X_rf)
                rf_home_points = rf_results['predicted_home_points'].values
                rf_away_points = rf_results['predicted_away_points'].values
                # Note: RandomForestScorePredictor returns margin as away - home
                # We need to convert to home - away for consistency
                rf_preds = rf_home_points - rf_away_points
            else:
                # Assume it's a dict with model_home and model_away
                if isinstance(rf_model, dict) and 'model_home' in rf_model and 'model_away' in rf_model:
                    rf_home_points = rf_model['model_home'].predict(X_rf)
                    rf_away_points = rf_model['model_away'].predict(X_rf)
                    rf_preds = rf_home_points - rf_away_points
                else:
                    logger.warning("Random Forest model format not recognized")
                    rf_preds = None
            
            if rf_preds is not None:
                logger.info(f"✅ Generated Random Forest predictions: {len(rf_preds)} games")
        except Exception as e:
            logger.error(f"❌ Random Forest prediction failed: {e}")
            import traceback
            traceback.print_exc()
            rf_preds = None
            rf_home_points = None
            rf_away_points = None
    else:
        rf_preds = None
        rf_home_points = None
        rf_away_points = None
    
    # Fetch SP+ ratings and calculate predictions
    logger.info("📊 Fetching SP+ ratings...")
    sp_ratings = fetch_sp_fpi_ratings(season=2025, use_csv=True)
    sp_preds = None
    if sp_ratings:
        try:
            sp_preds = []
            for idx, (_, game) in enumerate(games_meta.iterrows()):
                home_team = str(game.get('home_team', ''))
                away_team = str(game.get('away_team', ''))
                neutral_site = bool(game.get('neutral_site', False)) if 'neutral_site' in game else False
                
                # Normalize team names for matching
                home_normalized = normalize_team_name(home_team)
                away_normalized = normalize_team_name(away_team)
                
                # Try to find ratings
                home_rating = None
                away_rating = None
                
                # Try original name first, then normalized
                for team_name in [home_team, home_normalized]:
                    if team_name in sp_ratings:
                        home_rating = sp_ratings[team_name].get('sp')
                        break
                
                for team_name in [away_team, away_normalized]:
                    if team_name in sp_ratings:
                        away_rating = sp_ratings[team_name].get('sp')
                        break
                
                # Calculate SP+ margin
                sp_margin = calculate_sp_predicted_margin(home_rating, away_rating, neutral_site)
                sp_preds.append(sp_margin if sp_margin is not None else np.nan)
            
            sp_preds = np.array(sp_preds)
            sp_count = (~np.isnan(sp_preds)).sum()
            logger.info(f"✅ Generated SP+ predictions: {sp_count}/{len(sp_preds)} games")
        except Exception as e:
            logger.error(f"❌ SP+ prediction calculation failed: {e}")
            import traceback
            traceback.print_exc()
            sp_preds = None
    else:
        logger.warning("⚠️  No SP+ ratings available")
        sp_preds = None
    
    # Combine predictions
    for idx, (_, game) in enumerate(games_meta.iterrows()):
        pred = {
            'game_id': game.get('game_id', f'week14_game_{idx}'),
            'season': 2025,
            'week': 14,
            'home_team': game.get('home_team', 'Unknown'),
            'away_team': game.get('away_team', 'Unknown'),
            'start_date': game.get('start_date'),
            'home_conference': game.get('home_conference'),
            'away_conference': game.get('away_conference'),
            'spread': game.get('spread')
        }
        
        # Add Ridge prediction (margin)
        if ridge_preds is not None and idx < len(ridge_preds):
            pred['ridge_predicted_margin'] = float(ridge_preds[idx])
            pred['predicted_margin'] = float(ridge_preds[idx])
            pred['ridge_home_win_probability'] = (
                float(ridge_probs[idx]) if ridge_probs is not None else np.nan
            )
        else:
            pred['ridge_predicted_margin'] = np.nan
            pred['predicted_margin'] = np.nan
            pred['ridge_home_win_probability'] = np.nan
        
        # Add XGBoost prediction (win probability)
        if xgb_proba is not None and idx < len(xgb_proba):
            pred['xgb_home_win_probability'] = float(xgb_proba[idx])
        else:
            pred['xgb_home_win_probability'] = np.nan
        
        # Add FastAI prediction (win probability)
        if fastai_proba is not None and idx < len(fastai_proba):
            pred['fastai_home_win_probability'] = float(fastai_proba[idx])
        else:
            pred['fastai_home_win_probability'] = np.nan
        
        # Add Logistic Regression prediction (win probability)
        if logistic_proba is not None and idx < len(logistic_proba):
            pred['logistic_home_win_probability'] = float(logistic_proba[idx])
        else:
            pred['logistic_home_win_probability'] = np.nan
        
        # Add Random Forest prediction (margin)
        if rf_preds is not None and idx < len(rf_preds):
            pred['random_forest_predicted_margin'] = float(rf_preds[idx])
            if rf_home_points is not None and idx < len(rf_home_points):
                pred['random_forest_home_points'] = float(rf_home_points[idx])
            if rf_away_points is not None and idx < len(rf_away_points):
                pred['random_forest_away_points'] = float(rf_away_points[idx])
            # Convert margin to probability
            rf_prob = margin_to_probability(rf_preds[idx])
            pred['random_forest_home_win_probability'] = float(rf_prob) if rf_prob is not None else np.nan
        else:
            pred['random_forest_predicted_margin'] = np.nan
            pred['random_forest_home_points'] = np.nan
            pred['random_forest_away_points'] = np.nan
            pred['random_forest_home_win_probability'] = np.nan
        
        # Add SP+ prediction (margin)
        if sp_preds is not None and idx < len(sp_preds):
            sp_margin_val = sp_preds[idx]
            if not np.isnan(sp_margin_val):
                pred['sp_predicted_margin'] = float(sp_margin_val)
                sp_prob = margin_to_probability(sp_margin_val)
                pred['sp_home_win_probability'] = float(sp_prob) if sp_prob is not None else np.nan
            else:
                pred['sp_predicted_margin'] = np.nan
                pred['sp_home_win_probability'] = np.nan
        else:
            pred['sp_predicted_margin'] = np.nan
            pred['sp_home_win_probability'] = np.nan

        # Get individual predictions for ensemble
        ridge_margin = (
            float(ridge_preds[idx]) 
            if ridge_preds is not None and idx < len(ridge_preds) 
            else None
        )
        xgb_prob = (
            float(xgb_proba[idx]) 
            if xgb_proba is not None and idx < len(xgb_proba) 
            else None
        )
        fastai_prob = (
            float(fastai_proba[idx]) 
            if fastai_proba is not None and idx < len(fastai_proba) 
            else None
        )
        logistic_prob = (
            float(logistic_proba[idx])
            if logistic_proba is not None and idx < len(logistic_proba)
            else None
        )
        rf_margin = (
            float(rf_preds[idx])
            if rf_preds is not None and idx < len(rf_preds)
            else None
        )
        sp_margin = (
            float(sp_preds[idx])
            if sp_preds is not None and idx < len(sp_preds) and not np.isnan(sp_preds[idx])
            else None
        )

        # Create ensemble prediction
        ensemble = create_ensemble_prediction(
            ridge_margin, xgb_prob, fastai_prob, logistic_prob, rf_margin, sp_margin
        )

        # Add ensemble results
        pred['ensemble_margin'] = ensemble['ensemble_margin']
        pred['ensemble_home_win_probability'] = (
            ensemble['ensemble_home_win_prob']
        )
        pred['ensemble_away_win_probability'] = (
            ensemble['ensemble_away_win_prob']
        )
        pred['ensemble_confidence'] = ensemble['ensemble_confidence']
        pred['models_used'] = ','.join(ensemble['models_used'])
        pred['model_agreement'] = ensemble['model_agreement']
        
        # Use ensemble predictions for final output
        if not np.isnan(ensemble['ensemble_margin']):
            pred['predicted_margin'] = ensemble['ensemble_margin']
            pred['home_win_probability'] = ensemble['ensemble_home_win_prob']
            pred['away_win_probability'] = ensemble['ensemble_away_win_prob']
            pred['predicted_winner'] = (
                pred['home_team'] 
                if ensemble['ensemble_margin'] > 0 
                else pred['away_team']
            )
        elif not np.isnan(ensemble['ensemble_home_win_prob']):
            pred['home_win_probability'] = ensemble['ensemble_home_win_prob']
            pred['away_win_probability'] = ensemble['ensemble_away_win_prob']
            pred['predicted_winner'] = (
                pred['home_team'] 
                if ensemble['ensemble_home_win_prob'] > 0.5 
                else pred['away_team']
            )
        else:
            # Fallback to individual models
            if ridge_margin is not None:
                pred['predicted_margin'] = ridge_margin
                pred['predicted_winner'] = (
                    pred['home_team'] if ridge_margin > 0 
                    else pred['away_team']
                )
            elif xgb_prob is not None:
                pred['home_win_probability'] = xgb_prob
                pred['away_win_probability'] = 1.0 - xgb_prob
                pred['predicted_winner'] = (
                    pred['home_team'] if xgb_prob > 0.5 
                    else pred['away_team']
                )
            elif fastai_prob is not None:
                pred['home_win_probability'] = fastai_prob
                pred['away_win_probability'] = 1.0 - fastai_prob
                pred['predicted_winner'] = (
                    pred['home_team'] if fastai_prob > 0.5 
                    else pred['away_team']
                )
            elif logistic_prob is not None:
                pred['home_win_probability'] = logistic_prob
                pred['away_win_probability'] = 1.0 - logistic_prob
                pred['predicted_winner'] = (
                    pred['home_team'] if logistic_prob > 0.5 
                    else pred['away_team']
                )
            elif rf_margin is not None:
                pred['predicted_margin'] = rf_margin
                pred['predicted_winner'] = (
                    pred['home_team'] if rf_margin > 0 
                    else pred['away_team']
                )
            elif sp_margin is not None:
                pred['predicted_margin'] = sp_margin
                pred['predicted_winner'] = (
                    pred['home_team'] if sp_margin > 0 
                    else pred['away_team']
                )
            else:
                pred['predicted_winner'] = 'Unknown'
        
        predictions.append(pred)
    
    return pd.DataFrame(predictions)


def run_prediction_pipeline(tune_hyperparameters: bool = False) -> int:
    """
    Execute the complete Week 14 prediction workflow programmatically.

    Args:
        tune_hyperparameters: Whether to run model tuning before predictions.

    Returns:
        Process exit code (0=success, 1=failure)
    """
    logger.info("=" * 80)
    logger.info("WEEK 14 PREDICTIONS WITH PROPER MODEL ALIGNMENT")
    logger.info("=" * 80)
    logger.info(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Step 1: Load models
        logger.info("\nStep 1: Loading trained models...")
        models = load_models()
        if not models:
            logger.error("❌ No models loaded. Cannot generate predictions.")
            return 1
        
        # Optional: Hyperparameter tuning
        if tune_hyperparameters:
            logger.info("\n" + "=" * 80)
            logger.info("HYPERPARAMETER TUNING")
            logger.info("=" * 80)
            
            # Load training data
            training_path = (
                PROJECT_ROOT / 'model_pack' / 'updated_training_data.csv'
            )
            if training_path.exists():
                training_df = pd.read_csv(training_path, low_memory=False)
                logger.info(
                    f"Loaded training data: {len(training_df)} games"
                )
                
                # Get feature lists from models
                model_features = get_model_features(models)
                
                # Tune Ridge
                if 'ridge' in models and 'ridge' in model_features:
                    ridge_params = tune_ridge_hyperparameters(
                        training_df,
                        model_features['ridge'],
                        'margin'
                    )
                    if ridge_params:
                        logger.info(
                            f"💾 Best Ridge alpha: "
                            f"{ridge_params['alpha']} "
                            f"(CV MAE: {ridge_params['best_cv_score']:.3f})"
                        )
                
                # Tune XGBoost
                if 'xgb' in models and 'xgb' in model_features:
                    xgb_params = tune_xgboost_hyperparameters(
                        training_df,
                        model_features['xgb'],
                        'home_win'
                    )
                    if xgb_params:
                        logger.info(
                            f"💾 Best XGBoost params: "
                            f"n_estimators={xgb_params['n_estimators']}, "
                            f"max_depth={xgb_params['max_depth']}, "
                            f"learning_rate={xgb_params['learning_rate']} "
                            f"(CV Accuracy: {xgb_params['best_cv_score']:.3f})"
                        )
            else:
                logger.warning(
                    "Training data not found. Skipping tuning.",
                    extra={
                        "event": "data_missing",
                        "path": str(training_path),
                        "error.category": ErrorCategory.DATA.value,
                    },
                )
        
        # Step 2: Get model feature requirements
        logger.info("\nStep 2: Getting model feature requirements...")
        model_features = get_model_features(models)
        if not model_features:
            logger.error(
                "Could not determine model feature requirements",
                extra={
                    "event": "feature_detection_failed",
                    "error.category": ErrorCategory.MODEL.value,
                },
            )
            return 1
        
        # Step 3: Load Week 14 data
        logger.info("\nStep 3: Loading Week 14 data...")
        week14_data = load_week14_data()
        if not week14_data:
            logger.error(
                "No Week 14 data found",
                extra={
                    "event": "data_missing",
                    "error.category": ErrorCategory.DATA.value,
                },
            )
            return 1
        
        # Step 4: Get feature defaults
        logger.info("\nStep 4: Loading feature defaults from training data...")
        defaults = get_feature_defaults_from_training()
        
        # Step 5: Transform Week 14 data for models
        logger.info("\nStep 5: Transforming Week 14 data to match model schemas...")
        transformed_data = transform_week14_for_models(week14_data, model_features, defaults)
        if not transformed_data:
            logger.error("❌ Failed to transform Week 14 data.")
            return 1
        
        # Step 6: Generate predictions
        logger.info("\nStep 6: Generating predictions...")
        predictions_df = generate_predictions(models, transformed_data, week14_data)
        
        if predictions_df.empty:
            logger.error("❌ No predictions generated.")
            return 1
        
        # Step 7: Save predictions
        logger.info("\nStep 7: Saving predictions...")
        output_dir = PROJECT_ROOT / 'predictions' / 'week14'
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_path = output_dir / 'week14_model_predictions.csv'
        predictions_df.to_csv(output_path, index=False)
        logger.info(f"✅ Saved predictions to: {output_path}")
        
        # Also save JSON version
        json_path = output_dir / 'week14_model_predictions.json'
        predictions_df.to_json(json_path, orient='records', indent=2)
        logger.info(f"✅ Saved predictions to: {json_path}")
        
        # Print summary
        logger.info("\n" + "=" * 80)
        logger.info("PREDICTION SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Total games predicted: {len(predictions_df)}")
        
        # Model usage statistics
        if 'models_used' in predictions_df.columns:
            models_used = predictions_df['models_used'].value_counts()
            logger.info(f"\nModel usage:")
            for models_str, count in models_used.items():
                logger.info(f"  {models_str}: {count} games")
        
        # Ensemble statistics
        if 'ensemble_confidence' in predictions_df.columns:
            avg_confidence = predictions_df['ensemble_confidence'].mean()
            logger.info(
                f"\nAverage ensemble confidence: {avg_confidence:.2%}"
            )
        
        logger.info(f"\nSample predictions:")
        for idx, row in predictions_df.head(10).iterrows():
            home = row.get('home_team', '?')
            away = row.get('away_team', '?')
            margin = row.get('ensemble_margin', row.get('predicted_margin', np.nan))
            prob = row.get('ensemble_home_win_probability', row.get('home_win_probability', np.nan))
            winner = row.get('predicted_winner', '?')
            confidence = row.get('ensemble_confidence', np.nan)
            
            if pd.notna(margin):
                conf_str = (
                    f" (confidence: {confidence:.1%})" 
                    if pd.notna(confidence) 
                    else ""
                )
                logger.info(
                    f"  {away} @ {home}: {winner} by "
                    f"{margin:.1f} points{conf_str}"
                )
            elif pd.notna(prob):
                conf_str = (
                    f" (confidence: {confidence:.1%})" 
                    if pd.notna(confidence) 
                    else ""
                )
                logger.info(
                    f"  {away} @ {home}: {winner} "
                    f"({prob:.1%} home win prob){conf_str}"
                )
            else:
                logger.info(f"  {away} @ {home}: {winner}")
        
        logger.info("\n" + "=" * 80)
        logger.info("✅ WEEK 14 PREDICTIONS COMPLETE")
        logger.info("=" * 80)
        
        return 0
        
    except Exception as e:
        logger.error(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description='Generate Week 14 predictions with optional tuning'
    )
    parser.add_argument(
        '--tune-hyperparameters',
        action='store_true',
        help='Run hyperparameter tuning before predictions'
    )
    cli_args = parser.parse_args()
    sys.exit(run_prediction_pipeline(tune_hyperparameters=cli_args.tune_hyperparameters))
