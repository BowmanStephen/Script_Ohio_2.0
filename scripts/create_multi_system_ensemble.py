#!/usr/bin/env python3
"""
Create multi-system meta-ensemble predictions.

This script:
1. Loads Ohio Model predictions (from existing pipeline)
2. Loads Prediction_Tracker data
3. Extracts key systems: System Average, Opening Line, Sagarin, SP+ (already integrated)
4. Calculates meta-ensemble using optimized weights
5. Generates enhanced predictions with new meta_ensemble_margin column
6. Saves to predictions/week{XX}/week{XX}_predictions_meta_ensemble.csv
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import warnings

import pandas as pd
import numpy as np

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# Import Prediction_Tracker loader
from scripts.load_prediction_tracker import load_prediction_tracker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')


def load_meta_ensemble_weights() -> Dict[str, float]:
    """Load optimized meta-ensemble weights from config file."""
    weights_path = project_root / 'config' / 'meta_ensemble_weights.json'
    
    if not weights_path.exists():
        logger.warning(f"⚠️  Meta-ensemble weights not found at {weights_path}")
        logger.warning("  Using default weights: Ohio=0.35, System Avg=0.25, Opening=0.20, Sagarin=0.10, SP+=0.10")
        return {
            'ohio_weight': 0.35,
            'system_average_weight': 0.25,
            'opening_line_weight': 0.20,
            'sagarin_weight': 0.10,
            'sp_plus_weight': 0.10
        }
    
    try:
        with open(weights_path, 'r') as f:
            weights = json.load(f)
        
        logger.info(f"✅ Loaded meta-ensemble weights from {weights_path}")
        logger.info(f"  Ohio={weights.get('ohio_weight', 0.35):.3f}, "
                   f"System Avg={weights.get('system_average_weight', 0.25):.3f}, "
                   f"Opening={weights.get('opening_line_weight', 0.20):.3f}, "
                   f"Sagarin={weights.get('sagarin_weight', 0.10):.3f}, "
                   f"SP+={weights.get('sp_plus_weight', 0.10):.3f}")
        
        return weights
        
    except Exception as e:
        logger.error(f"❌ Failed to load meta-ensemble weights: {e}")
        logger.warning("  Using default weights")
        return {
            'ohio_weight': 0.35,
            'system_average_weight': 0.25,
            'opening_line_weight': 0.20,
            'sagarin_weight': 0.10,
            'sp_plus_weight': 0.10
        }


def load_ohio_predictions(week: int, season: int = 2025) -> pd.DataFrame:
    """
    Load Ohio Model predictions for specified week.
    
    Args:
        week: Week number
        season: Season year
    
    Returns:
        DataFrame with Ohio Model predictions
    """
    logger.info(f"📊 Loading Ohio Model predictions for Week {week}...")
    
    # Try multiple prediction file locations
    prediction_paths = [
        project_root / 'predictions' / f'week{week}' / f'week{week}_predictions_all_*.csv',
        project_root / 'predictions' / f'week{week}' / f'week{week}_predictions_enhanced.csv',
        project_root / 'predictions' / f'week{week}' / f'week{week}_predictions.csv',
        project_root / 'predictions' / f'week{week}_predictions.csv',
        project_root / f'week{week}_predictions.csv',
    ]
    
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
                logger.info(f"  ✅ Loaded {len(df)} predictions from {pattern}")
                return df
            except Exception as e:
                logger.warning(f"  ⚠️  Error loading {pattern}: {e}")
    
    logger.error(f"❌ No Ohio Model predictions found for Week {week}")
    return pd.DataFrame()


def calculate_meta_ensemble_margin(
    ohio_margin: float,
    system_avg: Optional[float],
    opening_line: Optional[float],
    sagarin: Optional[float],
    sp_plus: Optional[float],
    weights: Dict[str, float]
) -> Optional[float]:
    """
    Calculate meta-ensemble margin from individual system predictions.
    
    Args:
        ohio_margin: Ohio Model predicted margin
        system_avg: System Average predicted margin
        opening_line: Opening Line predicted margin
        sagarin: Sagarin predicted margin
        sp_plus: SP+ predicted margin
        weights: Weight dictionary
    
    Returns:
        Meta-ensemble predicted margin
    """
    if np.isnan(ohio_margin):
        return None
    
    terms = []
    total_weight = 0.0
    
    # Ohio Model (always present)
    ohio_weight = weights.get('ohio_weight', 0.35)
    terms.append(ohio_weight * ohio_margin)
    total_weight += ohio_weight
    
    # System Average (if available)
    if system_avg is not None and not np.isnan(system_avg):
        sa_weight = weights.get('system_average_weight', 0.25)
        terms.append(sa_weight * system_avg)
        total_weight += sa_weight
    
    # Opening Line (if available)
    if opening_line is not None and not np.isnan(opening_line):
        op_weight = weights.get('opening_line_weight', 0.20)
        terms.append(op_weight * opening_line)
        total_weight += op_weight
    
    # Sagarin (if available)
    if sagarin is not None and not np.isnan(sagarin):
        sag_weight = weights.get('sagarin_weight', 0.10)
        terms.append(sag_weight * sagarin)
        total_weight += sag_weight
    
    # SP+ (if available)
    if sp_plus is not None and not np.isnan(sp_plus):
        sp_weight = weights.get('sp_plus_weight', 0.10)
        terms.append(sp_weight * sp_plus)
        total_weight += sp_weight
    
    if total_weight == 0:
        return None
    
    return sum(terms) / total_weight


def margin_to_win_prob(margin: float) -> float:
    """Convert margin to home win probability using logistic function."""
    scale = 7.0
    return 1.0 / (1.0 + np.exp(-margin / scale))


def match_games(ohio_df: pd.DataFrame, tracker_df: pd.DataFrame) -> pd.DataFrame:
    """
    Match Ohio predictions with Prediction_Tracker data.
    
    Args:
        ohio_df: Ohio Model predictions
        tracker_df: Prediction_Tracker data
    
    Returns:
        Merged DataFrame
    """
    logger.info("🔗 Matching games...")
    
    # Create matching keys
    def create_key(row):
        home = str(row.get('home_team', '')).strip().lower()
        away = str(row.get('away_team', '')).strip().lower()
        week = row.get('week', '')
        season = row.get('season', 2025)
        return f"{season}_{week}_{away}_{home}"
    
    # Add keys
    if 'game_key' not in ohio_df.columns:
        ohio_df['game_key'] = ohio_df.apply(create_key, axis=1)
    if 'game_key' not in tracker_df.columns:
        tracker_df['game_key'] = tracker_df.apply(create_key, axis=1)
    
    # Merge
    merged = ohio_df.merge(
        tracker_df[['game_key', 'system_average', 'opening_line', 'sagarin', 'big_200', 'fpi', 'neutral_site']],
        on='game_key',
        how='left',
        suffixes=('', '_tracker')
    )
    
    logger.info(f"✅ Matched {merged['system_average'].notna().sum()}/{len(merged)} games with Prediction_Tracker data")
    
    return merged


def create_meta_ensemble_predictions(week: int, season: int = 2025) -> pd.DataFrame:
    """
    Create meta-ensemble predictions for specified week.
    
    Args:
        week: Week number
        season: Season year
    
    Returns:
        DataFrame with meta-ensemble predictions
    """
    logger.info("=" * 80)
    logger.info(f"CREATING META-ENSEMBLE PREDICTIONS FOR WEEK {week}")
    logger.info("=" * 80)
    
    # Step 1: Load weights
    weights = load_meta_ensemble_weights()
    
    # Step 2: Load Ohio Model predictions
    ohio_df = load_ohio_predictions(week, season)
    if ohio_df.empty:
        logger.error("❌ Cannot create meta-ensemble without Ohio Model predictions")
        return pd.DataFrame()
    
    # Step 3: Load Prediction_Tracker data
    tracker_df = load_prediction_tracker(week=week, season=season)
    if tracker_df.empty:
        logger.warning("⚠️  No Prediction_Tracker data available. Using Ohio Model only.")
        # Still create output with Ohio Model predictions
        result_df = ohio_df.copy()
        result_df['meta_ensemble_margin'] = result_df.get('ensemble_margin', result_df.get('predicted_margin', np.nan))
        result_df['meta_ensemble_win_prob'] = result_df['meta_ensemble_margin'].apply(
            lambda x: margin_to_win_prob(x) if not np.isnan(x) else np.nan
        )
        return result_df
    
    # Step 4: Match games
    merged_df = match_games(ohio_df, tracker_df)
    
    # Step 5: Calculate meta-ensemble
    logger.info("🔧 Calculating meta-ensemble predictions...")
    
    # Get Ohio Model margin column
    ohio_col = 'ensemble_margin' if 'ensemble_margin' in merged_df.columns else 'predicted_margin'
    
    # Get SP+ margin if available (from enhanced predictions)
    sp_plus_col = 'sp_predicted_margin' if 'sp_predicted_margin' in merged_df.columns else None
    
    merged_df['meta_ensemble_margin'] = merged_df.apply(
        lambda row: calculate_meta_ensemble_margin(
            row.get(ohio_col, np.nan),
            row.get('system_average'),
            row.get('opening_line'),
            row.get('sagarin'),
            row.get(sp_plus_col) if sp_plus_col else row.get('fpi'),
            weights
        ),
        axis=1
    )
    
    # Calculate win probability
    merged_df['meta_ensemble_win_prob'] = merged_df['meta_ensemble_margin'].apply(
        lambda x: margin_to_win_prob(x) if x is not None and not np.isnan(x) else np.nan
    )
    
    # Add divergence columns
    if ohio_col in merged_df.columns:
        merged_df['ohio_vs_system_avg_diff'] = merged_df[ohio_col] - merged_df.get('system_average', np.nan)
        merged_df['ohio_vs_opening_diff'] = merged_df[ohio_col] - merged_df.get('opening_line', np.nan)
        merged_df['meta_vs_ohio_diff'] = merged_df['meta_ensemble_margin'] - merged_df[ohio_col]
    
    # Coverage statistics
    meta_count = merged_df['meta_ensemble_margin'].notna().sum()
    logger.info(f"  ✅ Meta-ensemble predictions: {meta_count}/{len(merged_df)} ({meta_count/len(merged_df)*100:.1f}%)")
    
    return merged_df


def main():
    """Main execution function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Create multi-system meta-ensemble predictions')
    parser.add_argument('--week', type=int, default=13, help='Week number (default: 13)')
    parser.add_argument('--season', type=int, default=2025, help='Season year (default: 2025)')
    parser.add_argument('--output', type=str, help='Output file path (optional)')
    
    args = parser.parse_args()
    
    try:
        # Create meta-ensemble predictions
        result_df = create_meta_ensemble_predictions(args.week, args.season)
        
        if result_df.empty:
            logger.error("❌ No predictions generated")
            return 1
        
        # Save results
        if args.output:
            output_path = Path(args.output)
        else:
            output_dir = project_root / 'predictions' / f'week{args.week}'
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / f'week{args.week}_predictions_meta_ensemble.csv'
        
        result_df.to_csv(output_path, index=False)
        logger.info(f"✅ Saved meta-ensemble predictions to {output_path}")
        
        # Summary
        logger.info("\n" + "=" * 80)
        logger.info("✅ META-ENSEMBLE CREATION COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Total games: {len(result_df)}")
        logger.info(f"Meta-ensemble predictions: {result_df['meta_ensemble_margin'].notna().sum()}")
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Meta-ensemble creation failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())

