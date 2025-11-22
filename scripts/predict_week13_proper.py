#!/usr/bin/env python3
"""
Proper Week 13 Predictions with Model Feature Alignment
========================================================

This script:
1. Loads Week 13 games and features
2. Transforms features to match model training schema
3. Generates predictions using Ridge and XGBoost models
4. Saves comprehensive predictions

Usage:
    python3 scripts/predict_week13_proper.py
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

import pandas as pd
import numpy as np
import joblib
import pickle

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_models():
    """Load trained models"""
    model_pack_dir = PROJECT_ROOT / 'model_pack'
    
    models = {}
    
    # Load Ridge model
    ridge_path = model_pack_dir / 'ridge_model_2025.joblib'
    if ridge_path.exists():
        try:
            models['ridge'] = joblib.load(ridge_path)
            logger.info(f"✅ Loaded Ridge model: {ridge_path.name}")
        except Exception as e:
            logger.error(f"❌ Failed to load Ridge model: {e}")
    else:
        logger.warning(f"⚠️  Ridge model not found: {ridge_path}")
    
    # Load XGBoost model
    xgb_path = model_pack_dir / 'xgb_home_win_model_2025.pkl'
    if xgb_path.exists():
        try:
            with open(xgb_path, 'rb') as f:
                models['xgb'] = pickle.load(f)
            logger.info(f"✅ Loaded XGBoost model: {xgb_path.name}")
        except Exception as e:
            logger.error(f"❌ Failed to load XGBoost model: {e}")
    else:
        logger.warning(f"⚠️  XGBoost model not found: {xgb_path}")
    
    return models


def get_model_features(models: Dict[str, Any]) -> Dict[str, List[str]]:
    """Get required features for each model"""
    features = {}
    
    if 'ridge' in models and hasattr(models['ridge'], 'feature_names_in_'):
        features['ridge'] = list(models['ridge'].feature_names_in_)
        logger.info(f"Ridge features: {features['ridge']}")
    
    if 'xgb' in models:
        try:
            booster = models['xgb'].get_booster()
            features['xgb'] = list(booster.feature_names)
            logger.info(f"XGBoost features: {features['xgb']}")
        except:
            # Fallback: use training data to infer features
            training_path = PROJECT_ROOT / 'model_pack' / 'updated_training_data.csv'
            if training_path.exists():
                df = pd.read_csv(training_path, nrows=1)
                # Use the same features as model_training_agent
                features['xgb'] = [
                    'home_talent', 'away_talent', 'spread', 'home_elo', 'away_elo',
                    'home_adjusted_epa', 'home_adjusted_epa_allowed',
                    'away_adjusted_epa', 'away_adjusted_epa_allowed',
                    'home_adjusted_success', 'home_adjusted_success_allowed',
                    'away_adjusted_success', 'away_adjusted_success_allowed'
                ]
    
    return features


def load_week13_data():
    """Load Week 13 games and features"""
    week13_features_path = PROJECT_ROOT / 'data' / 'week13' / 'enhanced' / 'week13_features_86.csv'
    week13_games_path = PROJECT_ROOT / 'data' / 'week13' / 'enhanced' / 'week13_enhanced_games.csv'
    
    # Also check starter pack for games
    games_path = PROJECT_ROOT / 'starter_pack' / 'data' / 'games.csv'
    
    week13_data = {}
    
    # Load features if available
    if week13_features_path.exists():
        week13_data['features'] = pd.read_csv(week13_features_path)
        logger.info(f"✅ Loaded Week 13 features: {len(week13_data['features'])} games")
    else:
        logger.warning(f"⚠️  Week 13 features not found: {week13_features_path}")
    
    # Load enhanced games if available
    if week13_games_path.exists():
        week13_data['enhanced_games'] = pd.read_csv(week13_games_path)
        logger.info(f"✅ Loaded Week 13 enhanced games: {len(week13_data['enhanced_games'])} games")
    
    # Load from starter pack games.csv
    if games_path.exists():
        all_games = pd.read_csv(games_path, low_memory=False)
        week13_games = all_games[(all_games['season'] == 2025) & (all_games['week'] == 13)]
        if len(week13_games) > 0:
            week13_data['games'] = week13_games
            logger.info(f"✅ Loaded Week 13 games from starter pack: {len(week13_games)} games")
    
    return week13_data


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
            logger.warning(f"⚠️  Could not load feature defaults: {e}")
    
    return defaults


def transform_week13_for_models(week13_data: Dict[str, pd.DataFrame], 
                                model_features: Dict[str, List[str]],
                                defaults: Dict[str, float]) -> Dict[str, pd.DataFrame]:
    """Transform Week 13 data to match model feature requirements"""
    
    transformed = {}
    
    # Start with features if available
    if 'features' in week13_data:
        features_df = week13_data['features'].copy()
    elif 'enhanced_games' in week13_data:
        features_df = week13_data['enhanced_games'].copy()
    else:
        logger.error("❌ No Week 13 features or enhanced games found")
        return {}
    
    # Merge with games data if available
    if 'games' in week13_data:
        games_df = week13_data['games'].copy()
        # Try to merge on game_id or id
        if 'game_id' in features_df.columns and 'id' in games_df.columns:
            # Convert to same type for merging
            features_df['game_id'] = features_df['game_id'].astype(str)
            games_df['id'] = games_df['id'].astype(str)
            
            features_df = features_df.merge(
                games_df[['id', 'home_team', 'away_team', 'home_points', 'away_points', 
                         'start_date', 'neutral_site', 'conference_game']],
                left_on='game_id',
                right_on='id',
                how='left',
                suffixes=('', '_games')
            )
            # Clean up duplicate columns
            for col in ['home_team', 'away_team']:
                if f'{col}_games' in features_df.columns:
                    features_df[col] = features_df[f'{col}_games'].fillna(features_df[col])
                    features_df = features_df.drop(columns=[f'{col}_games'])
    
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


def generate_predictions(models: Dict[str, Any], 
                        transformed_data: Dict[str, pd.DataFrame],
                        week13_data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Generate predictions using models"""
    
    predictions = []
    
    # Get game metadata
    if 'features' in week13_data:
        games_meta = week13_data['features'][['game_id', 'home_team', 'away_team']].copy()
    elif 'enhanced_games' in week13_data:
        games_meta = week13_data['enhanced_games'][['id', 'home_team', 'away_team']].copy()
        games_meta = games_meta.rename(columns={'id': 'game_id'})
    else:
        logger.error("❌ No game metadata available")
        return pd.DataFrame()
    
    # Generate Ridge predictions (margin)
    if 'ridge' in models and 'ridge' in transformed_data:
        try:
            X_ridge = transformed_data['ridge']
            ridge_preds = models['ridge'].predict(X_ridge)
            
            logger.info(f"✅ Generated Ridge predictions: {len(ridge_preds)} games")
        except Exception as e:
            logger.error(f"❌ Ridge prediction failed: {e}")
            ridge_preds = None
    else:
        ridge_preds = None
    
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
    
    # Combine predictions
    for idx, (_, game) in enumerate(games_meta.iterrows()):
        pred = {
            'game_id': game.get('game_id', f'week13_game_{idx}'),
            'season': 2025,
            'week': 13,
            'home_team': game.get('home_team', 'Unknown'),
            'away_team': game.get('away_team', 'Unknown'),
        }
        
        # Add Ridge prediction (margin)
        if ridge_preds is not None and idx < len(ridge_preds):
            pred['ridge_predicted_margin'] = float(ridge_preds[idx])
            pred['predicted_margin'] = float(ridge_preds[idx])
        else:
            pred['ridge_predicted_margin'] = np.nan
            pred['predicted_margin'] = np.nan
        
        # Add XGBoost prediction (win probability)
        if xgb_proba is not None and idx < len(xgb_proba):
            pred['xgb_home_win_probability'] = float(xgb_proba[idx])
            pred['home_win_probability'] = float(xgb_proba[idx])
            pred['away_win_probability'] = 1.0 - float(xgb_proba[idx])
        else:
            pred['xgb_home_win_probability'] = np.nan
            pred['home_win_probability'] = np.nan
            pred['away_win_probability'] = np.nan
        
        # Determine predicted winner
        if pd.notna(pred.get('predicted_margin')):
            pred['predicted_winner'] = pred['home_team'] if pred['predicted_margin'] > 0 else pred['away_team']
        elif pd.notna(pred.get('home_win_probability')):
            pred['predicted_winner'] = pred['home_team'] if pred['home_win_probability'] > 0.5 else pred['away_team']
        else:
            pred['predicted_winner'] = 'Unknown'
        
        predictions.append(pred)
    
    return pd.DataFrame(predictions)


def main():
    """Main execution"""
    logger.info("=" * 80)
    logger.info("WEEK 13 PREDICTIONS WITH PROPER MODEL ALIGNMENT")
    logger.info("=" * 80)
    logger.info(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Step 1: Load models
        logger.info("\nStep 1: Loading trained models...")
        models = load_models()
        if not models:
            logger.error("❌ No models loaded. Cannot generate predictions.")
            return 1
        
        # Step 2: Get model feature requirements
        logger.info("\nStep 2: Getting model feature requirements...")
        model_features = get_model_features(models)
        if not model_features:
            logger.error("❌ Could not determine model feature requirements.")
            return 1
        
        # Step 3: Load Week 13 data
        logger.info("\nStep 3: Loading Week 13 data...")
        week13_data = load_week13_data()
        if not week13_data:
            logger.error("❌ No Week 13 data found.")
            return 1
        
        # Step 4: Get feature defaults
        logger.info("\nStep 4: Loading feature defaults from training data...")
        defaults = get_feature_defaults_from_training()
        
        # Step 5: Transform Week 13 data for models
        logger.info("\nStep 5: Transforming Week 13 data to match model schemas...")
        transformed_data = transform_week13_for_models(week13_data, model_features, defaults)
        if not transformed_data:
            logger.error("❌ Failed to transform Week 13 data.")
            return 1
        
        # Step 6: Generate predictions
        logger.info("\nStep 6: Generating predictions...")
        predictions_df = generate_predictions(models, transformed_data, week13_data)
        
        if predictions_df.empty:
            logger.error("❌ No predictions generated.")
            return 1
        
        # Step 7: Save predictions
        logger.info("\nStep 7: Saving predictions...")
        output_dir = PROJECT_ROOT / 'predictions' / 'week13'
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_path = output_dir / 'week13_model_predictions.csv'
        predictions_df.to_csv(output_path, index=False)
        logger.info(f"✅ Saved predictions to: {output_path}")
        
        # Print summary
        logger.info("\n" + "=" * 80)
        logger.info("PREDICTION SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Total games predicted: {len(predictions_df)}")
        logger.info(f"\nSample predictions:")
        for idx, row in predictions_df.head(10).iterrows():
            home = row.get('home_team', '?')
            away = row.get('away_team', '?')
            margin = row.get('predicted_margin', np.nan)
            prob = row.get('home_win_probability', np.nan)
            winner = row.get('predicted_winner', '?')
            
            if pd.notna(margin):
                logger.info(f"  {away} @ {home}: {winner} by {margin:.1f} points")
            elif pd.notna(prob):
                logger.info(f"  {away} @ {home}: {winner} ({prob:.1%} home win prob)")
            else:
                logger.info(f"  {away} @ {home}: {winner}")
        
        logger.info("\n" + "=" * 80)
        logger.info("✅ WEEK 13 PREDICTIONS COMPLETE")
        logger.info("=" * 80)
        
        return 0
        
    except Exception as e:
        logger.error(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

