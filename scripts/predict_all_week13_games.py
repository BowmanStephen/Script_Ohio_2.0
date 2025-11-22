#!/usr/bin/env python3
"""
Run predictions for all 60 Week 13 games using ML models
"""

import pandas as pd
import numpy as np
import sys
import joblib
import pickle
from pathlib import Path
import json
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from project_management.TOOLS_AND_CONFIG.model_features import RIDGE_FEATURES, XGB_FEATURES

def load_models():
    """Load ML models"""
    models = {}
    
    # Load Ridge model
    ridge_path = project_root / 'model_pack' / 'ridge_model_2025.joblib'
    if ridge_path.exists():
        try:
            models['ridge'] = joblib.load(ridge_path)
            print(f"✅ Loaded Ridge model")
        except Exception as e:
            print(f"⚠️  Failed to load Ridge model: {e}")
    
    # Load XGBoost model
    xgb_path = project_root / 'model_pack' / 'xgb_home_win_model_2025.pkl'
    if xgb_path.exists():
        try:
            with open(xgb_path, 'rb') as f:
                models['xgb'] = pickle.load(f)
            print(f"✅ Loaded XGBoost model")
        except Exception as e:
            print(f"⚠️  Failed to load XGBoost model: {e}")
    
    return models

def prepare_features_for_model(features_df, model_type='ridge'):
    """Prepare features for specific model - use actual trained features"""
    if model_type == 'ridge':
        # Ridge model was trained with only 8 features
        required_features = [
            'home_talent', 'away_talent', 'home_elo', 'away_elo',
            'home_adjusted_epa', 'home_adjusted_epa_allowed',
            'away_adjusted_epa', 'away_adjusted_epa_allowed'
        ]
    elif model_type == 'xgb':
        # XGBoost model was trained with 13 features
        required_features = [
            'home_talent', 'away_talent', 'spread', 'home_elo', 'away_elo',
            'home_adjusted_epa', 'home_adjusted_epa_allowed',
            'away_adjusted_epa', 'away_adjusted_epa_allowed',
            'home_adjusted_success', 'home_adjusted_success_allowed',
            'away_adjusted_success', 'away_adjusted_success_allowed'
        ]
    else:
        raise ValueError(f"Unknown model type: {model_type}")
    
    # Select only required features
    model_features = []
    missing_features = []
    
    for feature in required_features:
        if feature in features_df.columns:
            model_features.append(feature)
        else:
            missing_features.append(feature)
            # Add with default value
            features_df[feature] = 0.0
            model_features.append(feature)
    
    if missing_features:
        print(f"⚠️  Added missing features with defaults: {missing_features[:5]}...")
    
    # Ensure correct order
    X = features_df[required_features].copy()
    
    # Handle any NaN values
    X = X.fillna(0.0)
    
    return X

def generate_predictions(features_df, models):
    """Generate predictions using ML models"""
    print(f"\n🎯 Generating predictions for {len(features_df)} games...")
    
    predictions = []
    
    for idx, row in features_df.iterrows():
        game_id = row.get('game_id', f'game_{idx}')
        home_team = row.get('home_team', 'Unknown')
        away_team = row.get('away_team', 'Unknown')
        
        pred_result = {
            'game_id': game_id,
            'home_team': home_team,
            'away_team': away_team,
            'season': 2025,
            'week': 13,
        }
        
        # Ridge predictions
        if 'ridge' in models:
            try:
                X_ridge = prepare_features_for_model(pd.DataFrame([row]), 'ridge')
                ridge_pred = models['ridge'].predict(X_ridge)[0]
                pred_result['ridge_margin'] = float(ridge_pred)
                pred_result['ridge_home_win_prob'] = float(1 / (1 + np.exp(-ridge_pred / 7)))  # Convert margin to prob
            except Exception as e:
                print(f"⚠️  Ridge prediction failed for {home_team} vs {away_team}: {e}")
                pred_result['ridge_margin'] = None
                pred_result['ridge_home_win_prob'] = None
        
        # XGBoost predictions
        if 'xgb' in models:
            try:
                X_xgb = prepare_features_for_model(pd.DataFrame([row]), 'xgb')
                xgb_proba = models['xgb'].predict_proba(X_xgb)[0]
                pred_result['xgb_home_win_prob'] = float(xgb_proba[1])
                # Estimate margin from probability (rough conversion)
                pred_result['xgb_margin'] = float((xgb_proba[1] - 0.5) * 14)  # Rough estimate
            except Exception as e:
                print(f"⚠️  XGBoost prediction failed for {home_team} vs {away_team}: {e}")
                pred_result['xgb_home_win_prob'] = None
                pred_result['xgb_margin'] = None
        
        # Ensemble prediction
        if pred_result.get('ridge_margin') is not None and pred_result.get('xgb_home_win_prob') is not None:
            # Weighted average
            ensemble_margin = (pred_result['ridge_margin'] * 0.6 + pred_result['xgb_margin'] * 0.4)
            ensemble_prob = (pred_result['ridge_home_win_prob'] * 0.4 + pred_result['xgb_home_win_prob'] * 0.6)
            pred_result['ensemble_margin'] = float(ensemble_margin)
            pred_result['ensemble_home_win_prob'] = float(ensemble_prob)
            pred_result['predicted_winner'] = home_team if ensemble_prob > 0.5 else away_team
        elif pred_result.get('ridge_margin') is not None:
            pred_result['ensemble_margin'] = pred_result['ridge_margin']
            pred_result['ensemble_home_win_prob'] = pred_result['ridge_home_win_prob']
            pred_result['predicted_winner'] = home_team if pred_result['ridge_home_win_prob'] > 0.5 else away_team
        elif pred_result.get('xgb_home_win_prob') is not None:
            pred_result['ensemble_margin'] = pred_result['xgb_margin']
            pred_result['ensemble_home_win_prob'] = pred_result['xgb_home_win_prob']
            pred_result['predicted_winner'] = home_team if pred_result['xgb_home_win_prob'] > 0.5 else away_team
        else:
            pred_result['ensemble_margin'] = None
            pred_result['ensemble_home_win_prob'] = None
            pred_result['predicted_winner'] = 'Unknown'
        
        predictions.append(pred_result)
        
        if (idx + 1) % 10 == 0:
            print(f"  Predicted {idx + 1}/{len(features_df)} games...")
    
    return pd.DataFrame(predictions)

def main():
    print("=" * 80)
    print("PREDICT ALL WEEK 13 GAMES (60 GAMES)")
    print("=" * 80)
    
    # Load features
    features_path = project_root / 'data' / 'week13' / 'enhanced' / 'week13_features_86_model_compatible.csv'
    if not features_path.exists():
        print(f"❌ Features file not found: {features_path}")
        print("   Run scripts/expand_week13_coverage.py first")
        return 1
    
    print(f"\n📊 Loading features from: {features_path}")
    features_df = pd.read_csv(features_path)
    print(f"✅ Loaded {len(features_df)} games with {len(features_df.columns)} features")
    
    # Load models
    print(f"\n📊 Loading ML models...")
    models = load_models()
    if not models:
        print("❌ No models loaded. Cannot generate predictions.")
        return 1
    
    # Generate predictions
    predictions_df = generate_predictions(features_df, models)
    
    # Load external data for comparison
    enhanced_games_path = project_root / 'data' / 'week13' / 'enhanced' / 'week13_enhanced_games_all_60.csv'
    if enhanced_games_path.exists():
        enhanced_games = pd.read_csv(enhanced_games_path)
        predictions_df = predictions_df.merge(
            enhanced_games[['id', 'external_line', 'external_margin', 'external_prob']],
            left_on='game_id',
            right_on='id',
            how='left'
        )
    
    # Save predictions
    output_dir = project_root / 'predictions' / 'week13'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = output_dir / 'week13_predictions_all_60_games.csv'
    predictions_df.to_csv(output_path, index=False)
    print(f"\n✅ Saved predictions to: {output_path}")
    
    # Create summary
    summary = {
        'total_games': int(len(predictions_df)),
        'models_used': list(models.keys()),
        'ridge_predictions': int(predictions_df['ridge_margin'].notna().sum()),
        'xgb_predictions': int(predictions_df['xgb_home_win_prob'].notna().sum()),
        'ensemble_predictions': int(predictions_df['ensemble_margin'].notna().sum()),
        'generation_time': datetime.now().isoformat(),
    }
    
    summary_path = output_dir / 'week13_predictions_summary.json'
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"✅ Saved summary to: {summary_path}")
    
    # Print sample predictions
    print("\n" + "=" * 80)
    print("SAMPLE PREDICTIONS")
    print("=" * 80)
    display_cols = ['home_team', 'away_team', 'predicted_winner', 'ensemble_margin', 
                   'ensemble_home_win_prob', 'external_line', 'external_margin']
    available_cols = [col for col in display_cols if col in predictions_df.columns]
    print(predictions_df[available_cols].head(10).to_string(index=False))
    
    print("\n" + "=" * 80)
    print("✅ PREDICTIONS COMPLETE")
    print("=" * 80)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

