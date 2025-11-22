"""
Model Configuration
Defines which model files to use and their feature requirements
"""

# Updated model file paths (use fixed versions)
RIDGE_MODEL_FILE = 'model_pack/ridge_model_2025_fixed.joblib'
XGB_MODEL_FILE = 'model_pack/xgb_home_win_model_2025_fixed.pkl'

# Feature sets (imported from model_features.py)
from model_features import RIDGE_FEATURES, XGB_FEATURES

# Model metadata
MODEL_INFO = {
    'ridge': {
        'file': RIDGE_MODEL_FILE,
        'features': RIDGE_FEATURES,
        'type': 'regression',
        'target': 'margin',
        'description': 'Ridge regression for score margin prediction'
    },
    'xgb': {
        'file': XGB_MODEL_FILE,
        'features': XGB_FEATURES,
        'type': 'classification',
        'target': 'home_win',
        'description': 'XGBoost classifier for win probability prediction'
    }
}

def get_model_config(model_type):
    """Get configuration for a specific model type"""
    return MODEL_INFO.get(model_type.lower())

def list_available_models():
    """List all available models with their configurations"""
    for model_type, config in MODEL_INFO.items():
        print(f"{model_type.upper()}:")
        print(f"  File: {config['file']}")
        print(f"  Features: {len(config['features'])}")
        print(f"  Type: {config['type']}")
        print(f"  Description: {config['description']}")
        print()

if __name__ == "__main__":
    print("Available Model Configurations:")
    list_available_models()