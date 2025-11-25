"""Model configuration metadata used by notebooks, scripts, and QA tests."""

from dataclasses import dataclass
from typing import Dict, List, Optional

# Try to import from model_features, fallback to direct definitions
try:
    from model_features import RIDGE_FEATURES, XGB_FEATURES
except (ImportError, FileNotFoundError):
    # Fallback: define features directly if import fails
    RIDGE_FEATURES = [
        'home_talent', 'away_talent', 'home_elo', 'away_elo',
        'home_adjusted_epa', 'home_adjusted_epa_allowed',
        'away_adjusted_epa', 'away_adjusted_epa_allowed'
    ]
    
    XGB_FEATURES = [
        'home_talent', 'away_talent', 'spread', 'home_elo', 'away_elo',
        'home_adjusted_epa', 'home_adjusted_epa_allowed',
        'away_adjusted_epa', 'away_adjusted_epa_allowed',
        'home_adjusted_success', 'home_adjusted_success_allowed',
        'away_adjusted_success', 'away_adjusted_success_allowed'
    ]

# Feature definitions for additional models
LOGISTIC_FEATURES = [
    'home_adjusted_epa', 'home_adjusted_epa_allowed', 
    'away_adjusted_epa', 'away_adjusted_epa_allowed',
    'home_talent', 'away_talent', 'home_elo', 'away_elo'
    # Note: Logistic regression also uses one-hot encoded conference features
    # (week, home_conference, away_conference) which are dynamically generated
]

RANDOM_FOREST_FEATURES = [
    'home_adjusted_success', 'home_adjusted_success_allowed', 
    'away_adjusted_success', 'away_adjusted_success_allowed',
    'home_adjusted_rushing_epa', 'home_adjusted_rushing_epa_allowed', 
    'away_adjusted_rushing_epa', 'away_adjusted_rushing_epa_allowed',
    'home_adjusted_passing_epa', 'home_adjusted_passing_epa_allowed', 
    'away_adjusted_passing_epa', 'away_adjusted_passing_epa_allowed'
]


@dataclass(frozen=True)
class ModelConfig:
    """Simple descriptor for a trained model artifact."""

    file: str
    features: List[str]
    type: str  # regression or classification
    target: str
    description: str


MODEL_INFO: Dict[str, ModelConfig] = {
    "ridge": ModelConfig(
        file="model_pack/ridge_model_2025.joblib",
        features=RIDGE_FEATURES,
        type="regression",
        target="margin",
        description="Ridge regression predicting scoring margin",
    ),
    "xgb": ModelConfig(
        file="model_pack/xgb_home_win_model_2025.pkl",
        features=XGB_FEATURES,
        type="classification",
        target="home_win",
        description="XGBoost classifier returning home win probabilities",
    ),
    "fastai": ModelConfig(
        file="model_pack/fastai_home_win_model_2025.pkl",
        features=XGB_FEATURES,  # FastAI uses same features as XGBoost
        type="classification",
        target="home_win",
        description="FastAI neural network returning home win probabilities",
    ),
    "logistic": ModelConfig(
        file="model_pack/logistic_regression_model.joblib",
        features=LOGISTIC_FEATURES,
        type="classification",
        target="home_win",
        description="Logistic regression classifier returning home win probabilities",
    ),
    "random_forest": ModelConfig(
        file="model_pack/random_forest_model_2025.pkl",
        features=RANDOM_FOREST_FEATURES,
        type="regression",
        target="points",  # Predicts both home_points and away_points
        description="Random Forest regressor predicting home and away team points",
    ),
}


def get_model_config(model_type: str) -> Optional[Dict[str, object]]:
    """
    Return dictionary representation of the requested model configuration.

    The function returns a plain dict to stay backward compatible with scripts
    that mutate the returned object.
    """
    key = (model_type or "").lower()
    config = MODEL_INFO.get(key)
    if config is None:
        return None
    return {
        "file": config.file,
        "features": list(config.features),
        "type": config.type,
        "target": config.target,
        "description": config.description,
    }


def list_available_models() -> Dict[str, Dict[str, object]]:
    """Return shallow copy of every registered model config."""
    return {name: get_model_config(name) for name in MODEL_INFO}


__all__ = ["get_model_config", "list_available_models", "MODEL_INFO", "ModelConfig"]
