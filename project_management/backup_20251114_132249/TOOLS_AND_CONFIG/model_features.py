"""
Model Features Configuration
Defines feature sets for different models to ensure compatibility
"""

# Feature sets for different models
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

def get_model_features(model_type='ridge'):
    """Get the appropriate feature set for a model type"""
    if model_type.lower() == 'ridge':
        return RIDGE_FEATURES
    elif model_type.lower() == 'xgb':
        return XGB_FEATURES
    else:
        raise ValueError(f"Unknown model type: {model_type}")

def validate_features(df, model_type='ridge'):
    """Validate that required features are present in dataframe"""
    features = get_model_features(model_type)
    missing = [f for f in features if f not in df.columns]
    if missing:
        raise ValueError(f"Missing features for {model_type} model: {missing}")
    return features

if __name__ == "__main__":
    print("Available feature sets:")
    print(f"Ridge ({len(RIDGE_FEATURES)} features): {RIDGE_FEATURES}")
    print(f"XGBoost ({len(XGB_FEATURES)} features): {XGB_FEATURES}")