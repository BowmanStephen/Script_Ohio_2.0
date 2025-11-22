#!/usr/bin/env python3
"""
Validate SP+ and FPI blend weights using Weeks 1-12 historical data.

This script:
1. Loads historical game data (Weeks 1-12) with actual results
2. Generates Ohio Model predictions for those games
3. Fetches SP+/FPI ratings from CFBD GraphQL API
4. Calculates SP+/FPI predicted margins
5. Optimizes blend weights to minimize MAE
6. Saves optimal weights to config/calibration_weights.json
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import warnings

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not required if API key set via environment

import pandas as pd
import numpy as np
import joblib
import pickle
from scipy.optimize import minimize

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

# Try to import GraphQL client
try:
    from src.data_sources.cfbd_graphql import CFBDGraphQLClient
    GQL_AVAILABLE = True
except ImportError:
    GQL_AVAILABLE = False
    logger.warning("GraphQL client not available. SP+/FPI ratings will not be fetched.")


def load_models() -> Dict[str, Any]:
    """Load ML models for prediction generation."""
    models = {}
    model_pack_dir = project_root / 'model_pack'
    
    # Load Ridge model
    ridge_path = model_pack_dir / 'ridge_model_2025.joblib'
    if ridge_path.exists():
        try:
            models['ridge'] = joblib.load(ridge_path)
            logger.info("✅ Loaded Ridge model")
        except Exception as e:
            logger.error(f"❌ Failed to load Ridge model: {e}")
    else:
        logger.warning(f"⚠️  Ridge model not found at {ridge_path}")
    
    # Load XGBoost model
    xgb_path = model_pack_dir / 'xgb_home_win_model_2025.pkl'
    if xgb_path.exists():
        try:
            with open(xgb_path, 'rb') as f:
                models['xgb'] = pickle.load(f)
            logger.info("✅ Loaded XGBoost model")
        except Exception as e:
            logger.error(f"❌ Failed to load XGBoost model: {e}")
    else:
        logger.warning(f"⚠️  XGBoost model not found at {xgb_path}")
    
    return models


def get_model_features(model, model_type: str) -> List[str]:
    """Get required features for a model."""
    if hasattr(model, 'feature_names_in_'):
        # Use actual trained features
        return list(model.feature_names_in_)
    else:
        # Fallback to standard feature lists
        if model_type == 'ridge':
            return [
                'home_talent', 'away_talent', 'home_elo', 'away_elo',
                'home_adjusted_epa', 'home_adjusted_epa_allowed',
                'away_adjusted_epa', 'away_adjusted_epa_allowed'
            ]
        elif model_type == 'xgb':
            return [
                'home_talent', 'away_talent', 'spread', 'home_elo', 'away_elo',
                'home_adjusted_epa', 'home_adjusted_epa_allowed',
                'away_adjusted_epa', 'away_adjusted_epa_allowed',
                'home_adjusted_success', 'home_adjusted_success_allowed',
                'away_adjusted_success', 'away_adjusted_success_allowed'
            ]
        else:
            return []


def prepare_features_for_model(df: pd.DataFrame, model, model_type: str) -> np.ndarray:
    """Prepare features for a specific model."""
    required_features = get_model_features(model, model_type)
    
    # Create feature matrix
    feature_matrix = []
    for feature in required_features:
        if feature in df.columns:
            feature_matrix.append(df[feature].fillna(0.0).values)
        else:
            logger.warning(f"⚠️  Feature '{feature}' missing, using 0.0")
            feature_matrix.append(np.zeros(len(df)))
    
    X = np.column_stack(feature_matrix)
    return X


def load_historical_data(weeks: List[int], season: int = 2025) -> pd.DataFrame:
    """Load historical game data for specified weeks."""
    logger.info(f"📊 Loading historical data for weeks {weeks}...")
    
    all_games = []
    
    for week in weeks:
        # Try root directory first
        week_file = project_root / f'training_data_{season}_week{week:02d}.csv'
        if not week_file.exists():
            # Try data/weekly_training directory
            week_file = project_root / 'data' / 'weekly_training' / f'training_data_{season}_week{week:02d}.csv'
        
        if week_file.exists():
            try:
                df = pd.read_csv(week_file, low_memory=False)
                logger.info(f"  ✅ Week {week}: {len(df)} games")
                all_games.append(df)
            except Exception as e:
                logger.warning(f"  ⚠️  Week {week}: Failed to load - {e}")
        else:
            logger.warning(f"  ⚠️  Week {week}: File not found")
    
    if not all_games:
        logger.error("❌ No historical data loaded!")
        return pd.DataFrame()
    
    combined = pd.concat(all_games, ignore_index=True)
    logger.info(f"✅ Loaded {len(combined)} total games from {len(all_games)} weeks")
    
    # Filter for games with actual results
    with_results = combined[
        combined['home_points'].notna() & 
        combined['away_points'].notna()
    ].copy()
    
    if 'margin' not in with_results.columns:
        with_results['margin'] = with_results['home_points'] - with_results['away_points']
    
    logger.info(f"✅ {len(with_results)} games have actual results")
    
    return with_results


def generate_ohio_model_predictions(df: pd.DataFrame, models: Dict[str, Any]) -> pd.DataFrame:
    """Generate Ohio Model predictions for historical games."""
    logger.info("🎯 Generating Ohio Model predictions...")
    
    results = df.copy()
    
    # Ridge predictions
    if 'ridge' in models:
        try:
            ridge_model = models['ridge']
            X_ridge = prepare_features_for_model(df, ridge_model, 'ridge')
            ridge_preds = ridge_model.predict(X_ridge)
            results['ridge_margin'] = ridge_preds
            results['ridge_home_win_prob'] = 1 / (1 + np.exp(-ridge_preds / 7))
            logger.info(f"  ✅ Ridge: {len(ridge_preds)} predictions")
        except Exception as e:
            logger.error(f"  ❌ Ridge predictions failed: {e}")
            results['ridge_margin'] = np.nan
            results['ridge_home_win_prob'] = np.nan
    else:
        results['ridge_margin'] = np.nan
        results['ridge_home_win_prob'] = np.nan
    
    # XGBoost predictions
    if 'xgb' in models:
        try:
            xgb_model = models['xgb']
            X_xgb = prepare_features_for_model(df, xgb_model, 'xgb')
            xgb_proba = xgb_model.predict_proba(X_xgb)[:, 1]
            results['xgb_home_win_prob'] = xgb_proba
            # Estimate margin from probability
            results['xgb_margin'] = (xgb_proba - 0.5) * 14
            logger.info(f"  ✅ XGBoost: {len(xgb_proba)} predictions")
        except Exception as e:
            logger.error(f"  ❌ XGBoost predictions failed: {e}")
            results['xgb_home_win_prob'] = np.nan
            results['xgb_margin'] = np.nan
    else:
        results['xgb_home_win_prob'] = np.nan
        results['xgb_margin'] = np.nan
    
    # Calculate ensemble margin (weighted average)
    if results['ridge_margin'].notna().any() and results['xgb_margin'].notna().any():
        results['ensemble_margin'] = (
            results['ridge_margin'].fillna(0) * 0.6 + 
            results['xgb_margin'].fillna(0) * 0.4
        )
        results['ensemble_home_win_prob'] = (
            results['ridge_home_win_prob'].fillna(0.5) * 0.4 + 
            results['xgb_home_win_prob'].fillna(0.5) * 0.6
        )
    elif results['ridge_margin'].notna().any():
        results['ensemble_margin'] = results['ridge_margin']
        results['ensemble_home_win_prob'] = results['ridge_home_win_prob']
    elif results['xgb_margin'].notna().any():
        results['ensemble_margin'] = results['xgb_margin']
        results['ensemble_home_win_prob'] = results['xgb_home_win_prob']
    else:
        logger.error("❌ No model predictions available!")
        results['ensemble_margin'] = np.nan
        results['ensemble_home_win_prob'] = np.nan
    
    return results


def fetch_sp_fpi_ratings(season: int = 2025) -> Dict[str, Dict[str, float]]:
    """Fetch SP+ and FPI ratings from CFBD GraphQL API."""
    if not GQL_AVAILABLE:
        logger.error("❌ GraphQL client not available. Cannot fetch SP+/FPI ratings.")
        return {}
    
    api_key = os.getenv("CFBD_API_KEY")
    if not api_key:
        logger.error("❌ CFBD_API_KEY not set. Cannot fetch SP+/FPI ratings.")
        return {}
    
    logger.info(f"📡 Fetching SP+/FPI ratings for {season} season...")
    
    try:
        client = CFBDGraphQLClient(api_key=api_key)
        result = client.get_ratings(season=season)
        
        # Handle both response formats: {'ratings': [...]} and {'data': {'ratings': [...]}}
        if 'ratings' in result:
            ratings = result['ratings']
        elif 'data' in result and 'ratings' in result['data']:
            ratings = result['data']['ratings']
        else:
            logger.warning("⚠️  No ratings data in GraphQL response")
            return {}
        logger.info(f"  ✅ Fetched ratings for {len(ratings)} teams")
        
        # Build team ratings dictionary
        team_ratings = {}
        for rating in ratings:
            team = rating.get('team')
            if team:
                team_ratings[team] = {
                    'sp': rating.get('spOverall'),
                    'fpi': rating.get('fpi')
                }
        
        logger.info(f"  ✅ Mapped ratings for {len(team_ratings)} teams")
        return team_ratings
        
    except Exception as e:
        logger.error(f"❌ Failed to fetch SP+/FPI ratings: {e}")
        return {}


def normalize_team_name(team_name: str) -> str:
    """Normalize team name for matching."""
    # Common variations
    variations = {
        'Ohio State': 'Ohio State',
        'Ohio St.': 'Ohio State',
        'Ohio St': 'Ohio State',
        'Miami (FL)': 'Miami',
        'Miami (OH)': 'Miami (OH)',
        'UCF': 'UCF',
        'Central Florida': 'UCF',
    }
    
    if team_name in variations:
        return variations[team_name]
    
    # Remove common suffixes
    team = team_name.strip()
    for suffix in [' (FL)', ' (OH)', ' St.', ' State']:
        if team.endswith(suffix):
            team = team[:-len(suffix)]
    
    return team


def match_team_name(team_name: str, ratings_dict: Dict[str, Dict]) -> Optional[str]:
    """Match team name to ratings dictionary key."""
    normalized = normalize_team_name(team_name)
    
    # Exact match
    if normalized in ratings_dict:
        return normalized
    
    # Try original name
    if team_name in ratings_dict:
        return team_name
    
    # Try fuzzy matching
    for key in ratings_dict.keys():
        if normalize_team_name(key) == normalized:
            return key
    
    return None


def calculate_sp_predicted_margin(home_sp: Optional[float], away_sp: Optional[float], 
                                   neutral_site: bool) -> Optional[float]:
    """Calculate predicted margin from SP+ ratings."""
    if home_sp is None or away_sp is None:
        return None
    
    base_margin = home_sp - away_sp
    home_advantage = 2.5 if not neutral_site else 0.0
    return base_margin + home_advantage


def calculate_fpi_predicted_margin(home_fpi: Optional[float], away_fpi: Optional[float],
                                    neutral_site: bool) -> Optional[float]:
    """Calculate predicted margin from FPI ratings."""
    if home_fpi is None or away_fpi is None:
        return None
    
    base_margin = home_fpi - away_fpi
    home_advantage = 2.5 if not neutral_site else 0.0
    return base_margin + home_advantage


def calculate_sp_fpi_predictions(df: pd.DataFrame, ratings: Dict[str, Dict[str, float]]) -> pd.DataFrame:
    """Calculate SP+ and FPI predicted margins for games."""
    logger.info("📊 Calculating SP+/FPI predicted margins...")
    
    results = df.copy()
    results['sp_predicted_margin'] = np.nan
    results['fpi_predicted_margin'] = np.nan
    
    missing_teams = set()
    
    for idx, row in df.iterrows():
        home_team = row.get('home_team', '')
        away_team = row.get('away_team', '')
        neutral_site = row.get('neutral_site', False)
        
        # Match team names
        home_key = match_team_name(home_team, ratings) if home_team else None
        away_key = match_team_name(away_team, ratings) if away_team else None
        
        if home_key and away_key:
            home_rating = ratings[home_key]
            away_rating = ratings[away_key]
            
            # Calculate SP+ margin
            sp_margin = calculate_sp_predicted_margin(
                home_rating.get('sp'),
                away_rating.get('sp'),
                neutral_site
            )
            results.at[idx, 'sp_predicted_margin'] = sp_margin
            
            # Calculate FPI margin
            fpi_margin = calculate_fpi_predicted_margin(
                home_rating.get('fpi'),
                away_rating.get('fpi'),
                neutral_site
            )
            results.at[idx, 'fpi_predicted_margin'] = fpi_margin
        else:
            if home_team and not home_key:
                missing_teams.add(home_team)
            if away_team and not away_key:
                missing_teams.add(away_team)
    
    if missing_teams:
        logger.warning(f"⚠️  Missing ratings for {len(missing_teams)} teams: {list(missing_teams)[:10]}")
    
    sp_count = results['sp_predicted_margin'].notna().sum()
    fpi_count = results['fpi_predicted_margin'].notna().sum()
    logger.info(f"  ✅ SP+ predictions: {sp_count}/{len(results)}")
    logger.info(f"  ✅ FPI predictions: {fpi_count}/{len(results)}")
    
    return results


def calculate_metrics(predicted: np.ndarray, actual: np.ndarray) -> Dict[str, float]:
    """Calculate prediction metrics."""
    valid_mask = ~(np.isnan(predicted) | np.isnan(actual))
    if valid_mask.sum() == 0:
        return {'mae': np.nan, 'rmse': np.nan, 'accuracy': np.nan}
    
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


def optimize_blend_weights(df: pd.DataFrame) -> Dict[str, Any]:
    """Optimize blend weights to minimize MAE."""
    logger.info("🔧 Optimizing blend weights...")
    
    # Prepare data for optimization
    ohio_preds = df['ensemble_margin'].values
    sp_preds = df['sp_predicted_margin'].values
    fpi_preds = df['fpi_predicted_margin'].values
    actual = df['margin'].values
    
    # Find games where we have all predictions
    valid_mask = (
        ~np.isnan(ohio_preds) &
        ~np.isnan(sp_preds) &
        ~np.isnan(fpi_preds) &
        ~np.isnan(actual)
    )
    
    if valid_mask.sum() < 10:
        logger.warning("⚠️  Too few games with all predictions. Using defaults.")
        return {
            'ohio_model_weight': 0.65,
            'sp_weight': 0.25,
            'fpi_weight': 0.10,
            'validation_mae': np.nan,
            'validation_rmse': np.nan,
            'validation_accuracy': np.nan,
            'validation_games': int(valid_mask.sum()),
            'optimization_date': datetime.now().strftime('%Y-%m-%d'),
            'optimization_status': 'insufficient_data'
        }
    
    ohio_valid = ohio_preds[valid_mask]
    sp_valid = sp_preds[valid_mask]
    fpi_valid = fpi_preds[valid_mask]
    actual_valid = actual[valid_mask]
    
    logger.info(f"  ✅ {valid_mask.sum()} games have all predictions")
    
    # Define objective function
    def objective(weights: np.ndarray) -> float:
        """Minimize MAE."""
        blended = (
            weights[0] * ohio_valid +
            weights[1] * sp_valid +
            weights[2] * fpi_valid
        )
        return np.mean(np.abs(blended - actual_valid))
    
    # Constraints: weights sum to 1, all >= 0
    constraints = {'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0}
    bounds = [(0, 1), (0, 1), (0, 1)]
    initial_weights = np.array([0.65, 0.25, 0.10])
    
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
    blended_valid = (
        optimal_weights[0] * ohio_valid +
        optimal_weights[1] * sp_valid +
        optimal_weights[2] * fpi_valid
    )
    
    metrics = calculate_metrics(blended_valid, actual_valid)
    
    # Calculate baseline metrics (Ohio Model only)
    baseline_metrics = calculate_metrics(ohio_valid, actual_valid)
    
    logger.info(f"  📊 Optimal weights: Ohio={optimal_weights[0]:.3f}, SP+={optimal_weights[1]:.3f}, FPI={optimal_weights[2]:.3f}")
    logger.info(f"  📊 Validation MAE: {metrics['mae']:.2f} (baseline: {baseline_metrics['mae']:.2f})")
    logger.info(f"  📊 Validation Accuracy: {metrics['accuracy']:.1%} (baseline: {baseline_metrics['accuracy']:.1%})")
    
    return {
        'ohio_model_weight': float(optimal_weights[0]),
        'sp_weight': float(optimal_weights[1]),
        'fpi_weight': float(optimal_weights[2]),
        'validation_mae': metrics['mae'],
        'validation_rmse': metrics['rmse'],
        'validation_accuracy': metrics['accuracy'],
        'validation_games': metrics['n_games'],
        'baseline_mae': baseline_metrics['mae'],
        'baseline_accuracy': baseline_metrics['accuracy'],
        'optimization_date': datetime.now().strftime('%Y-%m-%d'),
        'optimization_status': 'success' if result.success else 'partial'
    }


def generate_validation_report(weights: Dict[str, Any], df: pd.DataFrame) -> str:
    """Generate validation report markdown."""
    report_lines = [
        "# SP+ and FPI Blend Weight Validation Report",
        "",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Status:** {weights.get('optimization_status', 'unknown')}",
        "",
        "## Executive Summary",
        "",
        "Optimal blend weights were calculated using Weeks 1-12 historical data.",
        "",
        "## Optimal Weights",
        "",
        f"- **Ohio Model Weight:** {weights['ohio_model_weight']:.3f}",
        f"- **SP+ Weight:** {weights['sp_weight']:.3f}",
        f"- **FPI Weight:** {weights['fpi_weight']:.3f}",
        "",
        "## Validation Metrics",
        "",
        f"- **Validation Games:** {weights['validation_games']}",
        f"- **Validation MAE:** {weights['validation_mae']:.2f} points",
        f"- **Validation RMSE:** {weights['validation_rmse']:.2f} points",
        f"- **Validation Accuracy:** {weights['validation_accuracy']:.1%}",
        "",
        "## Baseline Comparison",
        "",
        f"- **Baseline MAE (Ohio Model Only):** {weights.get('baseline_mae', np.nan):.2f} points",
        f"- **Baseline Accuracy:** {weights.get('baseline_accuracy', np.nan):.1%}",
        "",
        f"- **MAE Improvement:** {weights.get('baseline_mae', np.nan) - weights['validation_mae']:.2f} points",
        f"- **Accuracy Improvement:** {weights['validation_accuracy'] - weights.get('baseline_accuracy', 0.0):.1%} points",
        "",
        "## Usage",
        "",
        "These weights should be used in `enhance_predictions_with_ratings.py`",
        "to create calibrated ensemble predictions for future weeks.",
        "",
        "```python",
        "calibrated_margin = (",
        f"    ohio_model_weight * ensemble_margin +",
        f"    sp_weight * sp_predicted_margin +",
        f"    fpi_weight * fpi_predicted_margin",
        ")",
        "```",
        ""
    ]
    
    return "\n".join(report_lines)


def main():
    """Main execution function."""
    logger.info("=" * 80)
    logger.info("SP+ AND FPI BLEND WEIGHT VALIDATION")
    logger.info("=" * 80)
    logger.info(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Step 1: Load historical data (Weeks 1-12)
        weeks = list(range(1, 13))
        historical_df = load_historical_data(weeks, season=2025)
        
        if historical_df.empty:
            logger.error("❌ No historical data loaded. Cannot proceed.")
            return 1
        
        # Step 2: Load models
        logger.info("\n" + "=" * 80)
        logger.info("Step 2: Loading ML Models")
        logger.info("=" * 80)
        models = load_models()
        
        if not models:
            logger.error("❌ No models loaded. Cannot generate predictions.")
            return 1
        
        # Step 3: Generate Ohio Model predictions
        logger.info("\n" + "=" * 80)
        logger.info("Step 3: Generating Ohio Model Predictions")
        logger.info("=" * 80)
        predictions_df = generate_ohio_model_predictions(historical_df, models)
        
        if predictions_df['ensemble_margin'].isna().all():
            logger.error("❌ No Ohio Model predictions generated.")
            return 1
        
        # Step 4: Fetch SP+/FPI ratings
        logger.info("\n" + "=" * 80)
        logger.info("Step 4: Fetching SP+/FPI Ratings")
        logger.info("=" * 80)
        ratings = fetch_sp_fpi_ratings(season=2025)
        
        if not ratings:
            logger.warning("⚠️  No ratings fetched. Proceeding with Ohio Model only weights.")
            optimal_weights = {
                'ohio_model_weight': 1.0,
                'sp_weight': 0.0,
                'fpi_weight': 0.0,
                'validation_mae': np.nan,
                'validation_rmse': np.nan,
                'validation_accuracy': np.nan,
                'validation_games': len(predictions_df),
                'optimization_date': datetime.now().strftime('%Y-%m-%d'),
                'optimization_status': 'no_ratings'
            }
        else:
            # Step 5: Calculate SP+/FPI predicted margins
            logger.info("\n" + "=" * 80)
            logger.info("Step 5: Calculating SP+/FPI Predicted Margins")
            logger.info("=" * 80)
            predictions_df = calculate_sp_fpi_predictions(predictions_df, ratings)
            
            # Step 6: Optimize blend weights
            logger.info("\n" + "=" * 80)
            logger.info("Step 6: Optimizing Blend Weights")
            logger.info("=" * 80)
            optimal_weights = optimize_blend_weights(predictions_df)
        
        # Step 7: Save results
        logger.info("\n" + "=" * 80)
        logger.info("Step 7: Saving Results")
        logger.info("=" * 80)
        
        # Save weights to config
        config_dir = project_root / 'config'
        config_dir.mkdir(exist_ok=True)
        
        weights_path = config_dir / 'calibration_weights.json'
        with open(weights_path, 'w') as f:
            json.dump(optimal_weights, f, indent=2)
        logger.info(f"✅ Saved weights to {weights_path}")
        
        # Generate and save validation report
        reports_dir = project_root / 'reports'
        reports_dir.mkdir(exist_ok=True)
        
        report_content = generate_validation_report(optimal_weights, predictions_df)
        report_path = reports_dir / 'sp_blend_validation_report.md'
        with open(report_path, 'w') as f:
            f.write(report_content)
        logger.info(f"✅ Saved validation report to {report_path}")
        
        # Summary
        logger.info("\n" + "=" * 80)
        logger.info("✅ VALIDATION COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Optimal Weights: Ohio={optimal_weights['ohio_model_weight']:.3f}, "
                   f"SP+={optimal_weights['sp_weight']:.3f}, "
                   f"FPI={optimal_weights['fpi_weight']:.3f}")
        logger.info(f"Validation MAE: {optimal_weights['validation_mae']:.2f} points")
        logger.info(f"Validation Games: {optimal_weights['validation_games']}")
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Validation failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
