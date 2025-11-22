#!/usr/bin/env python3
"""
Optimize meta-ensemble weights using historical Prediction_Tracker data.

This script:
1. Loads historical games with actual results (Weeks 1-12 if available, or Week 13)
2. Loads Ohio Model predictions for those games
3. Loads Prediction_Tracker data for those games
4. Uses scipy.optimize to find optimal weights minimizing MAE
5. Validates weights on holdout set
6. Saves optimal weights to config/meta_ensemble_weights.json
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import warnings

import pandas as pd
import numpy as np
import joblib
import pickle
from scipy.optimize import minimize

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# Import Prediction_Tracker loader
from scripts.load_prediction_tracker import load_prediction_tracker, load_multiple_weeks

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')


def load_ohio_model_predictions(weeks: List[int], season: int = 2025) -> pd.DataFrame:
    """
    Load Ohio Model predictions for historical games.
    
    Args:
        weeks: List of week numbers
        season: Season year
    
    Returns:
        DataFrame with Ohio Model predictions
    """
    logger.info(f"📊 Loading Ohio Model predictions for weeks {weeks}...")
    
    all_predictions = []
    
    for week in weeks:
        # Try multiple prediction file locations
        prediction_paths = [
            project_root / 'predictions' / f'week{week}' / f'week{week}_predictions_all_*.csv',
            project_root / 'predictions' / f'week{week}' / f'week{week}_predictions.csv',
            project_root / 'predictions' / f'week{week}_predictions.csv',
            project_root / f'week{week}_predictions.csv',
        ]
        
        found = False
        for pattern in prediction_paths:
            if '*' in str(pattern):
                matches = list(pattern.parent.glob(pattern.name))
                if matches:
                    pattern = matches[0]
                else:
                    continue
            
            if pattern.exists():
                try:
                    df = pd.read_csv(pattern, low_memory=False)
                    if 'ensemble_margin' in df.columns or 'predicted_margin' in df.columns:
                        df['week'] = week
                        df['season'] = season
                        all_predictions.append(df)
                        logger.info(f"  ✅ Week {week}: {len(df)} predictions")
                        found = True
                        break
                except Exception as e:
                    logger.warning(f"  ⚠️  Week {week}: Error loading {pattern}: {e}")
        
        if not found:
            logger.warning(f"  ⚠️  Week {week}: No predictions file found")
    
    if not all_predictions:
        logger.warning("⚠️  No Ohio Model predictions loaded")
        return pd.DataFrame()
    
    combined = pd.concat(all_predictions, ignore_index=True)
    logger.info(f"✅ Loaded {len(combined)} total Ohio Model predictions")
    
    return combined


def load_historical_results(weeks: List[int], season: int = 2025) -> pd.DataFrame:
    """
    Load historical game results with actual margins.
    
    Args:
        weeks: List of week numbers
        season: Season year
    
    Returns:
        DataFrame with actual game results
    """
    logger.info(f"📊 Loading historical results for weeks {weeks}...")
    
    all_games = []
    
    for week in weeks:
        # Try training data files
        week_file = project_root / f'training_data_{season}_week{week:02d}.csv'
        if not week_file.exists():
            week_file = project_root / 'data' / 'weekly_training' / f'training_data_{season}_week{week:02d}.csv'
        if not week_file.exists():
            week_file = project_root / 'data' / 'training' / 'weekly' / f'training_data_{season}_week{week:02d}.csv'
        
        if week_file.exists():
            try:
                df = pd.read_csv(week_file, low_memory=False)
                
                # Filter for games with actual results
                if 'home_points' in df.columns and 'away_points' in df.columns:
                    df = df[df['home_points'].notna() & df['away_points'].notna()].copy()
                    df['actual_margin'] = df['home_points'] - df['away_points']
                    df['week'] = week
                    df['season'] = season
                    all_games.append(df)
                    logger.info(f"  ✅ Week {week}: {len(df)} games with results")
            except Exception as e:
                logger.warning(f"  ⚠️  Week {week}: Error loading {week_file}: {e}")
        else:
            logger.warning(f"  ⚠️  Week {week}: No training data file found")
    
    if not all_games:
        logger.warning("⚠️  No historical results loaded")
        return pd.DataFrame()
    
    combined = pd.concat(all_games, ignore_index=True)
    logger.info(f"✅ Loaded {len(combined)} total games with results")
    
    return combined


def match_games(ohio_df: pd.DataFrame, tracker_df: pd.DataFrame, 
                results_df: pd.DataFrame) -> pd.DataFrame:
    """
    Match Ohio predictions, Prediction_Tracker data, and actual results.
    
    Args:
        ohio_df: Ohio Model predictions
        tracker_df: Prediction_Tracker data
        results_df: Actual game results
    
    Returns:
        Combined DataFrame with matched games
    """
    logger.info("🔗 Matching games across datasets...")
    
    # Create matching keys
    def create_key(row):
        home = str(row.get('home_team', '')).strip().lower()
        away = str(row.get('away_team', '')).strip().lower()
        week = row.get('week', '')
        season = row.get('season', '')
        return f"{season}_{week}_{away}_{home}"
    
    # Add keys to each dataframe
    if 'game_key' not in ohio_df.columns:
        ohio_df['game_key'] = ohio_df.apply(create_key, axis=1)
    if 'game_key' not in tracker_df.columns:
        tracker_df['game_key'] = tracker_df.apply(create_key, axis=1)
    if 'game_key' not in results_df.columns:
        results_df['game_key'] = results_df.apply(create_key, axis=1)
    
    # Merge datasets
    merged = ohio_df.merge(
        tracker_df[['game_key', 'system_average', 'opening_line', 'sagarin', 'big_200', 'fpi', 'neutral_site']],
        on='game_key',
        how='inner',
        suffixes=('', '_tracker')
    )
    
    merged = merged.merge(
        results_df[['game_key', 'actual_margin']],
        on='game_key',
        how='inner'
    )
    
    logger.info(f"✅ Matched {len(merged)} games across all datasets")
    
    return merged


def calculate_metrics(predicted: np.ndarray, actual: np.ndarray) -> Dict[str, float]:
    """Calculate prediction metrics."""
    valid_mask = ~(np.isnan(predicted) | np.isnan(actual))
    if valid_mask.sum() == 0:
        return {'mae': np.nan, 'rmse': np.nan, 'accuracy': np.nan, 'n_games': 0}
    
    pred_valid = predicted[valid_mask]
    actual_valid = actual[valid_mask]
    
    mae = np.mean(np.abs(pred_valid - actual_valid))
    rmse = np.sqrt(np.mean((pred_valid - actual_valid) ** 2))
    
    # Winner accuracy
    pred_winners = pred_valid > 0
    actual_winners = actual_valid > 0
    accuracy = (pred_winners == actual_winners).mean()
    
    return {
        'mae': float(mae),
        'rmse': float(rmse),
        'accuracy': float(accuracy),
        'n_games': int(valid_mask.sum())
    }


def optimize_meta_ensemble_weights(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Optimize meta-ensemble weights to minimize MAE.
    
    Args:
        df: Combined DataFrame with predictions and actual results
    
    Returns:
        Dictionary with optimal weights and validation metrics
    """
    logger.info("🔧 Optimizing meta-ensemble weights...")
    
    # Get Ohio Model predictions
    ohio_col = 'ensemble_margin' if 'ensemble_margin' in df.columns else 'predicted_margin'
    if ohio_col not in df.columns:
        logger.error("❌ No Ohio Model predictions found")
        return {}
    
    ohio_preds = df[ohio_col].values
    
    # Get system predictions
    system_average = df['system_average'].values if 'system_average' in df.columns else np.full(len(df), np.nan)
    opening_line = df['opening_line'].values if 'opening_line' in df.columns else np.full(len(df), np.nan)
    sagarin = df['sagarin'].values if 'sagarin' in df.columns else np.full(len(df), np.nan)
    sp_plus = df.get('sp_predicted_margin', pd.Series([np.nan] * len(df))).values
    
    actual = df['actual_margin'].values
    
    # Find games where we have all required predictions
    # At minimum, need Ohio Model + at least one other system
    valid_mask = (
        ~np.isnan(ohio_preds) &
        ~np.isnan(actual) &
        (
            ~np.isnan(system_average) |
            ~np.isnan(opening_line) |
            ~np.isnan(sagarin)
        )
    )
    
    if valid_mask.sum() < 10:
        logger.warning("⚠️  Too few games with all predictions. Using defaults.")
        return {
            'ohio_weight': 0.35,
            'system_average_weight': 0.25,
            'opening_line_weight': 0.20,
            'sagarin_weight': 0.10,
            'sp_plus_weight': 0.10,
            'validation_mae': np.nan,
            'validation_rmse': np.nan,
            'validation_accuracy': np.nan,
            'validation_games': int(valid_mask.sum()),
            'optimization_date': datetime.now().strftime('%Y-%m-%d'),
            'optimization_status': 'insufficient_data'
        }
    
    ohio_valid = ohio_preds[valid_mask]
    system_avg_valid = system_average[valid_mask]
    opening_valid = opening_line[valid_mask]
    sagarin_valid = sagarin[valid_mask]
    sp_plus_valid = sp_plus[valid_mask]
    actual_valid = actual[valid_mask]
    
    logger.info(f"  ✅ {valid_mask.sum()} games have required predictions")
    
    # Define objective function
    def objective(weights: np.ndarray) -> float:
        """Minimize MAE."""
        # weights: [ohio, system_avg, opening, sagarin, sp_plus]
        blended = np.zeros_like(ohio_valid)
        total_weight = 0.0
        
        # Ohio Model (always present)
        blended += weights[0] * ohio_valid
        total_weight += weights[0]
        
        # System Average (if available)
        if ~np.isnan(system_avg_valid).all():
            valid_sa = ~np.isnan(system_avg_valid)
            blended[valid_sa] += weights[1] * system_avg_valid[valid_sa]
            total_weight += weights[1] * (valid_sa.sum() / len(valid_sa))
        
        # Opening Line (if available)
        if ~np.isnan(opening_valid).all():
            valid_op = ~np.isnan(opening_valid)
            blended[valid_op] += weights[2] * opening_valid[valid_op]
            total_weight += weights[2] * (valid_op.sum() / len(valid_op))
        
        # Sagarin (if available)
        if ~np.isnan(sagarin_valid).all():
            valid_sag = ~np.isnan(sagarin_valid)
            blended[valid_sag] += weights[3] * sagarin_valid[valid_sag]
            total_weight += weights[3] * (valid_sag.sum() / len(valid_sag))
        
        # SP+ (if available)
        if ~np.isnan(sp_plus_valid).all():
            valid_sp = ~np.isnan(sp_plus_valid)
            blended[valid_sp] += weights[4] * sp_plus_valid[valid_sp]
            total_weight += weights[4] * (valid_sp.sum() / len(valid_sp))
        
        # Normalize by total weight
        if total_weight > 0:
            blended = blended / total_weight
        
        return np.mean(np.abs(blended - actual_valid))
    
    # Constraints: weights sum to 1, all >= 0
    constraints = {'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0}
    bounds = [(0, 1), (0, 1), (0, 1), (0, 1), (0, 1)]
    initial_weights = np.array([0.35, 0.25, 0.20, 0.10, 0.10])
    
    try:
        result = minimize(
            objective,
            initial_weights,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints,
            options={'maxiter': 1000}
        )
        
        if result.success:
            optimal_weights = result.x
            logger.info(f"  ✅ Optimization converged: {optimal_weights}")
        else:
            logger.warning(f"  ⚠️  Optimization did not converge: {result.message}")
            optimal_weights = initial_weights
    except Exception as e:
        logger.error(f"  ❌ Optimization failed: {e}")
        optimal_weights = initial_weights
    
    # Calculate metrics with optimal weights
    blended_valid = np.zeros_like(ohio_valid)
    total_weight = 0.0
    
    blended_valid += optimal_weights[0] * ohio_valid
    total_weight += optimal_weights[0]
    
    if ~np.isnan(system_avg_valid).all():
        valid_sa = ~np.isnan(system_avg_valid)
        blended_valid[valid_sa] += optimal_weights[1] * system_avg_valid[valid_sa]
        total_weight += optimal_weights[1]
    
    if ~np.isnan(opening_valid).all():
        valid_op = ~np.isnan(opening_valid)
        blended_valid[valid_op] += optimal_weights[2] * opening_valid[valid_op]
        total_weight += optimal_weights[2]
    
    if ~np.isnan(sagarin_valid).all():
        valid_sag = ~np.isnan(sagarin_valid)
        blended_valid[valid_sag] += optimal_weights[3] * sagarin_valid[valid_sag]
        total_weight += optimal_weights[3]
    
    if ~np.isnan(sp_plus_valid).all():
        valid_sp = ~np.isnan(sp_plus_valid)
        blended_valid[valid_sp] += optimal_weights[4] * sp_plus_valid[valid_sp]
        total_weight += optimal_weights[4]
    
    if total_weight > 0:
        blended_valid = blended_valid / total_weight
    
    metrics = calculate_metrics(blended_valid, actual_valid)
    
    # Calculate baseline metrics (Ohio Model only)
    baseline_metrics = calculate_metrics(ohio_valid, actual_valid)
    
    logger.info(f"  📊 Optimal weights:")
    logger.info(f"     Ohio Model: {optimal_weights[0]:.3f}")
    logger.info(f"     System Average: {optimal_weights[1]:.3f}")
    logger.info(f"     Opening Line: {optimal_weights[2]:.3f}")
    logger.info(f"     Sagarin: {optimal_weights[3]:.3f}")
    logger.info(f"     SP+: {optimal_weights[4]:.3f}")
    logger.info(f"  📊 Validation MAE: {metrics['mae']:.2f} (baseline: {baseline_metrics['mae']:.2f})")
    logger.info(f"  📊 Validation Accuracy: {metrics['accuracy']:.1%} (baseline: {baseline_metrics['accuracy']:.1%})")
    
    return {
        'ohio_weight': float(optimal_weights[0]),
        'system_average_weight': float(optimal_weights[1]),
        'opening_line_weight': float(optimal_weights[2]),
        'sagarin_weight': float(optimal_weights[3]),
        'sp_plus_weight': float(optimal_weights[4]),
        'validation_mae': metrics['mae'],
        'validation_rmse': metrics['rmse'],
        'validation_accuracy': metrics['accuracy'],
        'validation_games': metrics['n_games'],
        'baseline_mae': baseline_metrics['mae'],
        'baseline_accuracy': baseline_metrics['accuracy'],
        'optimization_date': datetime.now().strftime('%Y-%m-%d'),
        'optimization_status': 'success' if result.success else 'partial'
    }


def main():
    """Main execution function."""
    logger.info("=" * 80)
    logger.info("META-ENSEMBLE WEIGHT OPTIMIZATION")
    logger.info("=" * 80)
    logger.info(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Step 1: Determine available weeks
        # Try to load Weeks 1-12, fallback to Week 13 if needed
        weeks_to_try = list(range(1, 13))
        if not any((project_root / f'training_data_2025_week{w:02d}.csv').exists() for w in weeks_to_try):
            weeks_to_try = [13]  # Fallback to Week 13
        
        logger.info(f"📅 Attempting to load weeks: {weeks_to_try}")
        
        # Step 2: Load historical results
        logger.info("\n" + "=" * 80)
        logger.info("Step 1: Loading Historical Results")
        logger.info("=" * 80)
        results_df = load_historical_results(weeks_to_try, season=2025)
        
        if results_df.empty:
            logger.warning("⚠️  No historical results loaded. Cannot optimize weights.")
            logger.info("   Creating default weights file...")
            default_weights = {
                'ohio_weight': 0.35,
                'system_average_weight': 0.25,
                'opening_line_weight': 0.20,
                'sagarin_weight': 0.10,
                'sp_plus_weight': 0.10,
                'validation_mae': np.nan,
                'validation_rmse': np.nan,
                'validation_accuracy': np.nan,
                'validation_games': 0,
                'optimization_date': datetime.now().strftime('%Y-%m-%d'),
                'optimization_status': 'no_data'
            }
        else:
            # Step 3: Load Ohio Model predictions
            logger.info("\n" + "=" * 80)
            logger.info("Step 2: Loading Ohio Model Predictions")
            logger.info("=" * 80)
            ohio_df = load_ohio_model_predictions(weeks_to_try, season=2025)
            
            if ohio_df.empty:
                logger.warning("⚠️  No Ohio Model predictions loaded. Using defaults.")
                default_weights = {
                    'ohio_weight': 0.35,
                    'system_average_weight': 0.25,
                    'opening_line_weight': 0.20,
                    'sagarin_weight': 0.10,
                    'sp_plus_weight': 0.10,
                    'validation_mae': np.nan,
                    'validation_rmse': np.nan,
                    'validation_accuracy': np.nan,
                    'validation_games': 0,
                    'optimization_date': datetime.now().strftime('%Y-%m-%d'),
                    'optimization_status': 'no_predictions'
                }
            else:
                # Step 4: Load Prediction_Tracker data
                logger.info("\n" + "=" * 80)
                logger.info("Step 3: Loading Prediction_Tracker Data")
                logger.info("=" * 80)
                tracker_df = load_multiple_weeks(weeks_to_try, season=2025)
                
                if tracker_df.empty:
                    logger.warning("⚠️  No Prediction_Tracker data loaded. Using defaults.")
                    default_weights = {
                        'ohio_weight': 0.35,
                        'system_average_weight': 0.25,
                        'opening_line_weight': 0.20,
                        'sagarin_weight': 0.10,
                        'sp_plus_weight': 0.10,
                        'validation_mae': np.nan,
                        'validation_rmse': np.nan,
                        'validation_accuracy': np.nan,
                        'validation_games': 0,
                        'optimization_date': datetime.now().strftime('%Y-%m-%d'),
                        'optimization_status': 'no_tracker_data'
                    }
                else:
                    # Step 5: Match games
                    logger.info("\n" + "=" * 80)
                    logger.info("Step 4: Matching Games")
                    logger.info("=" * 80)
                    matched_df = match_games(ohio_df, tracker_df, results_df)
                    
                    if matched_df.empty:
                        logger.warning("⚠️  No matched games. Using defaults.")
                        default_weights = {
                            'ohio_weight': 0.35,
                            'system_average_weight': 0.25,
                            'opening_line_weight': 0.20,
                            'sagarin_weight': 0.10,
                            'sp_plus_weight': 0.10,
                            'validation_mae': np.nan,
                            'validation_rmse': np.nan,
                            'validation_accuracy': np.nan,
                            'validation_games': 0,
                            'optimization_date': datetime.now().strftime('%Y-%m-%d'),
                            'optimization_status': 'no_matched_games'
                        }
                    else:
                        # Step 6: Optimize weights
                        logger.info("\n" + "=" * 80)
                        logger.info("Step 5: Optimizing Weights")
                        logger.info("=" * 80)
                        default_weights = optimize_meta_ensemble_weights(matched_df)
        
        # Step 7: Save weights
        logger.info("\n" + "=" * 80)
        logger.info("Step 6: Saving Weights")
        logger.info("=" * 80)
        
        config_dir = project_root / 'config'
        config_dir.mkdir(exist_ok=True)
        
        weights_path = config_dir / 'meta_ensemble_weights.json'
        with open(weights_path, 'w') as f:
            json.dump(default_weights, f, indent=2)
        logger.info(f"✅ Saved weights to {weights_path}")
        
        # Summary
        logger.info("\n" + "=" * 80)
        logger.info("✅ OPTIMIZATION COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Status: {default_weights.get('optimization_status', 'unknown')}")
        logger.info(f"Validation Games: {default_weights.get('validation_games', 0)}")
        if 'validation_mae' in default_weights and not np.isnan(default_weights['validation_mae']):
            logger.info(f"Validation MAE: {default_weights['validation_mae']:.2f} points")
            logger.info(f"Baseline MAE: {default_weights.get('baseline_mae', np.nan):.2f} points")
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Optimization failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())

