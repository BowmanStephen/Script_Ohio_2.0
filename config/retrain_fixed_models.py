"""
Retrain Models with Corrected 2025 Data
Retrains all models using the fixed dataset with proper quality
"""

import pandas as pd
import numpy as np
import joblib
import pickle
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, r2_score
import xgboost as xgb

# Import fixed feature sets
from model_features import RIDGE_FEATURES, XGB_FEATURES


def _select_features(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Return feature subset with NaNs filled."""
    missing = [c for c in columns if c not in frame.columns]
    if missing:
        raise KeyError(f"Missing required features: {missing}")
    subset = frame[columns].copy()
    return subset.fillna(0)

def load_and_prepare_data():
    """Load and prepare the corrected dataset"""
    print("Loading corrected training data...")
    df = pd.read_csv('model_pack/updated_training_data.csv')
    print(f"Loaded dataset: {len(df)} games")
    print(f"Seasons: {df.season.min()}-{df.season.max()}")
    print(f"2025 games: {len(df[df.season == 2025])}")
    return df

def train_ridge_model(df):
    """Train Ridge regression model with corrected data"""
    print("Training Ridge regression model...")

    # Use temporal validation
    train_df = df[df['season'] < 2025]
    test_df = df[df['season'] == 2025]

    X_train = _select_features(train_df, RIDGE_FEATURES)
    y_train = train_df['margin']
    X_test = _select_features(test_df, RIDGE_FEATURES)
    y_test = test_df['margin']

    print(f"Training data: {len(X_train)} games")
    print(f"Test data: {len(X_test)} games")

    # Train model
    model = Ridge(alpha=1.0)
    model.fit(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    print(f"Ridge model performance:")
    print(f"  MAE: {mae:.2f} points")
    print(f"  R²: {r2:.3f}")

    # Save model
    joblib.dump(model, 'model_pack/ridge_model_2025_fixed.joblib')
    print("✅ Saved: ridge_model_2025_fixed.joblib")

    return model, mae, r2

def train_xgboost_model(df):
    """Train XGBoost classification model with corrected data"""
    print("Training XGBoost classification model...")

    # Use temporal validation
    train_df = df[df['season'] < 2025]
    test_df = df[df['season'] == 2025]

    X_train = _select_features(train_df, XGB_FEATURES)
    y_train = (train_df['margin'] > 0).astype(int)  # Home win indicator
    X_test = _select_features(test_df, XGB_FEATURES)
    y_test = (test_df['margin'] > 0).astype(int)

    print(f"Training data: {len(X_train)} games")
    print(f"Test data: {len(X_test)} games")
    print(f"Home win rate (train): {y_train.mean():.1%}")
    print(f"Home win rate (test): {y_test.mean():.1%}")

    # Train model
    model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1,
        random_state=42,
        n_jobs=-1
    )
    model.fit(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)[:, 1]

    accuracy = (y_pred == y_test).mean()
    print(f"XGBoost model performance:")
    print(f"  Accuracy: {accuracy:.1%}")

    # Save model
    with open('model_pack/xgb_home_win_model_2025_fixed.pkl', 'wb') as f:
        pickle.dump(model, f)
    print("✅ Saved: xgb_home_win_model_2025_fixed.pkl")

    return model, accuracy

def compare_model_performance():
    """Compare performance between original and fixed models"""
    print("Comparing model performance...")

    df = pd.read_csv('model_pack/updated_training_data.csv')
    test_df = df[df['season'] == 2025].head(10)  # Sample for quick test

    # Load original models
    try:
        ridge_original = joblib.load('model_pack/ridge_model_2025.joblib')
        ridge_fixed = joblib.load('model_pack/ridge_model_2025_fixed.joblib')

        # Test on sample
        orig_preds = ridge_original.predict(test_df[RIDGE_FEATURES])
        fixed_preds = ridge_fixed.predict(test_df[RIDGE_FEATURES])
        actuals = test_df['margin'].values

        orig_mae = mean_absolute_error(actuals, orig_preds)
        fixed_mae = mean_absolute_error(actuals, fixed_preds)

        print(f"Ridge Model Comparison (sample):")
        print(f"  Original MAE: {orig_mae:.2f}")
        print(f"  Fixed MAE: {fixed_mae:.2f}")
        print(f"  Improvement: {(orig_mae - fixed_mae)/orig_mae * 100:.1f}%")

    except Exception as e:
        print(f"Could not compare Ridge models: {e}")

    # Compare XGBoost models
    try:
        with open('model_pack/xgb_home_win_model_2025.pkl', 'rb') as f:
            xgb_original = pickle.load(f)
        with open('model_pack/xgb_home_win_model_2025_fixed.pkl', 'rb') as f:
            xgb_fixed = pickle.load(f)

        y_test = (test_df['margin'] > 0).astype(int)

        orig_preds = xgb_original.predict(test_df[XGB_FEATURES])
        fixed_preds = xgb_fixed.predict(test_df[XGB_FEATURES])

        orig_acc = (orig_preds == y_test).mean()
        fixed_acc = (fixed_preds == y_test).mean()

        print(f"XGBoost Model Comparison (sample):")
        print(f"  Original Accuracy: {orig_acc:.1%}")
        print(f"  Fixed Accuracy: {fixed_acc:.1%}")
        print(f"  Improvement: {(fixed_acc - orig_acc)/orig_acc * 100:.1f}%")

    except Exception as e:
        print(f"Could not compare XGBoost models: {e}")

def main():
    print("=== RETRAINING MODELS WITH CORRECTED DATA ===")

    # Load corrected data
    df = load_and_prepare_data()

    # Train models
    ridge_model, ridge_mae, ridge_r2 = train_ridge_model(df)
    xgb_model, xgb_accuracy = train_xgboost_model(df)

    # Compare with original models
    compare_model_performance()

    print("\n=== MODEL RETRAINING COMPLETE ===")
    print("✅ Ridge model retrained with corrected data")
    print("✅ XGBoost model retrained with corrected data")
    print("✅ Models saved with '_fixed' suffix")
    print("✅ Performance comparison completed")

    return ridge_model, xgb_model

if __name__ == "__main__":
    ridge_model, xgb_model = main()