#!/usr/bin/env python3
"""
Enhance Week 14 predictions with SP+ ratings and calibrated ensemble.

This script:
1. Loads Week 14 predictions
2. Parses SP+ ratings from CSV file
3. Calculates SP+ predicted margins
4. Loads calibrated weights from config/calibration_weights.json
5. Calculates calibrated ensemble predictions
6. Adds new columns to predictions
7. Saves enhanced predictions
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Optional, Any
from datetime import datetime
import warnings

import pandas as pd
import numpy as np

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
        # Split and check if it's a location suffix
        parts = team.split('-')
        if len(parts) == 2:
            name, suffix = parts
            if suffix.upper() in ['FL', 'OH', 'CA', 'TX', 'NY']:
                # It's a location suffix, normalize
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


def match_team_name(team_name: str, ratings_dict: Dict[str, Dict]) -> Optional[str]:
    """
    Match team name to ratings dictionary key.
    Prioritizes exact matches to avoid false matches (e.g., Buffalo vs Buffalo State).
    """
    if not team_name or pd.isna(team_name):
        return None
    
    team_name = str(team_name).strip()
    normalized = normalize_team_name(team_name)
    
    # 1. Exact match (original name)
    if team_name in ratings_dict:
        return team_name
    
    # 2. Exact match (normalized name)
    if normalized in ratings_dict:
        return normalized
    
    # 3. Case-insensitive exact match
    team_lower = team_name.lower()
    for key in ratings_dict.keys():
        if key.lower() == team_lower:
            return key
    
    # 4. Normalized match (must be exact after normalization)
    for key in ratings_dict.keys():
        key_normalized = normalize_team_name(key)
        if key_normalized == normalized and normalized:
            # Additional check: ensure it's not a substring match
            if len(team_name) == len(key) or (normalized == team_name or normalized == key):
                return key
    
    return None


def load_sp_ratings_from_csv(csv_path: Path) -> Dict[str, Dict[str, float]]:
    """
    Load SP+ ratings from CSV file.
    
    Args:
        csv_path: Path to SP+ CSV file
    
    Returns:
        Dict mapping team_name -> {sp, sp_off, sp_def, sp_st, sp_rank, sp_off_rank, sp_def_rank, sp_st_rank}
    """
    if not csv_path.exists():
        logger.error(f"❌ SP+ CSV file not found: {csv_path}")
        return {}
    
    try:
        logger.info(f"📂 Loading SP+ ratings from CSV: {csv_path}")
        df = pd.read_csv(csv_path, low_memory=False)
        
        # Find the Team column
        team_col = None
        for col in df.columns:
            if col.lower() in ['team', 'team name']:
                team_col = col
                break
        
        if team_col is None:
            logger.error("❌ Could not find Team column in CSV")
            logger.error(f"Available columns: {list(df.columns)}")
            return {}
        
        # Map column names based on header row
        # Expected columns: Team, Conference, Record, SP+, Rk, Off. SP+, Rk, Def. SP+, Rk, ST SP+, Rk, LW Rk, Rk Chg
        col_map = {}
        for col in df.columns:
            col_lower = str(col).lower().strip()
            if col_lower == 'team':
                col_map['team'] = col
            elif 'sp+' in col_lower and 'off' not in col_lower and 'def' not in col_lower and 'st' not in col_lower:
                col_map['sp'] = col
            elif 'off' in col_lower and 'sp+' in col_lower:
                col_map['sp_off'] = col
            elif 'def' in col_lower and 'sp+' in col_lower:
                col_map['sp_def'] = col
            elif 'st sp+' in col_lower or ('special' in col_lower and 'sp+' in col_lower):
                col_map['sp_st'] = col
        
        # Find rank columns - they appear after each SP+ component
        # First Rk after SP+ is overall rank, second is Off rank, third is Def rank, fourth is ST rank
        rank_cols = []
        for i, col in enumerate(df.columns):
            if str(col).strip().lower() == 'rk':
                rank_cols.append((i, col))
        
        # Map ranks based on position
        if len(rank_cols) >= 1:
            col_map['sp_rank'] = rank_cols[0][1]
        if len(rank_cols) >= 2:
            col_map['sp_off_rank'] = rank_cols[1][1]
        if len(rank_cols) >= 3:
            col_map['sp_def_rank'] = rank_cols[2][1]
        if len(rank_cols) >= 4:
            col_map['sp_st_rank'] = rank_cols[3][1]
        
        if 'sp' not in col_map:
            logger.error("❌ Could not find SP+ column in CSV")
            logger.error(f"Available columns: {list(df.columns)}")
            return {}
        
        team_ratings = {}
        for _, row in df.iterrows():
            team = row[col_map['team']]
            
            # Skip rows where team is empty or NaN
            if pd.isna(team) or not str(team).strip() or str(team).strip() == '':
                continue
            
            team_str = str(team).strip()
            
            # Extract ratings
            sp_rating = row[col_map['sp']] if 'sp' in col_map and pd.notna(row[col_map['sp']]) else None
            sp_off_rating = row[col_map['sp_off']] if 'sp_off' in col_map and pd.notna(row[col_map['sp_off']]) else None
            sp_def_rating = row[col_map['sp_def']] if 'sp_def' in col_map and pd.notna(row[col_map['sp_def']]) else None
            sp_st_rating = row[col_map['sp_st']] if 'sp_st' in col_map and pd.notna(row[col_map['sp_st']]) else None
            sp_rank = row[col_map['sp_rank']] if 'sp_rank' in col_map and pd.notna(row[col_map['sp_rank']]) else None
            sp_off_rank = row[col_map['sp_off_rank']] if 'sp_off_rank' in col_map and pd.notna(row[col_map['sp_off_rank']]) else None
            sp_def_rank = row[col_map['sp_def_rank']] if 'sp_def_rank' in col_map and pd.notna(row[col_map['sp_def_rank']]) else None
            sp_st_rank = row[col_map['sp_st_rank']] if 'sp_st_rank' in col_map and pd.notna(row[col_map['sp_st_rank']]) else None
            
            # Only add if we have at least overall SP+ rating
            if sp_rating is not None:
                try:
                    team_ratings[team_str] = {
                        'sp': float(sp_rating),
                        'sp_off': float(sp_off_rating) if sp_off_rating is not None and not pd.isna(sp_off_rating) else None,
                        'sp_def': float(sp_def_rating) if sp_def_rating is not None and not pd.isna(sp_def_rating) else None,
                        'sp_st': float(sp_st_rating) if sp_st_rating is not None and not pd.isna(sp_st_rating) else None,
                        'sp_rank': int(sp_rank) if sp_rank is not None and not pd.isna(sp_rank) else None,
                        'sp_off_rank': int(sp_off_rank) if sp_off_rank is not None and not pd.isna(sp_off_rank) else None,
                        'sp_def_rank': int(sp_def_rank) if sp_def_rank is not None and not pd.isna(sp_def_rank) else None,
                        'sp_st_rank': int(sp_st_rank) if sp_st_rank is not None and not pd.isna(sp_st_rank) else None,
                    }
                    
                    # Also store with normalized name for matching
                    normalized_name = normalize_team_name(team_str)
                    if normalized_name != team_str and normalized_name not in team_ratings:
                        team_ratings[normalized_name] = team_ratings[team_str].copy()
                except (ValueError, TypeError) as e:
                    logger.warning(f"⚠️  Skipping row for {team_str}: {e}")
                    continue
        
        logger.info(f"  ✅ Loaded SP+ ratings for {len(team_ratings)} teams")
        return team_ratings
        
    except Exception as e:
        logger.error(f"❌ Error loading SP+ CSV: {e}")
        import traceback
        traceback.print_exc()
        return {}


def calculate_sp_margin(home_sp: Optional[float], away_sp: Optional[float], 
                       neutral_site: bool = False) -> Optional[float]:
    """Calculate predicted margin from SP+ ratings."""
    if home_sp is None or away_sp is None:
        return None
    
    base_margin = home_sp - away_sp
    home_advantage = 2.5 if not neutral_site else 0.0
    return base_margin + home_advantage


def margin_to_win_prob(margin: float, scale: float = 7.0) -> float:
    """Convert margin to home win probability using logistic function."""
    return 1.0 / (1.0 + np.exp(-margin / scale))


def load_calibration_weights() -> Dict[str, float]:
    """Load calibrated weights from config file."""
    weights_path = project_root / 'config' / 'calibration_weights.json'
    
    if not weights_path.exists():
        logger.warning(f"⚠️  Calibration weights not found at {weights_path}")
        logger.warning("  Using default weights: Ohio=0.65, SP+=0.35")
        return {
            'ohio_model_weight': 0.65,
            'sp_weight': 0.35
        }
    
    try:
        with open(weights_path, 'r') as f:
            weights = json.load(f)
        
        logger.info(f"✅ Loaded calibration weights from {weights_path}")
        logger.info(f"  Ohio={weights.get('ohio_model_weight', 0.65):.3f}, "
                   f"SP+={weights.get('sp_weight', 0.35):.3f}")
        
        return weights
        
    except Exception as e:
        logger.error(f"❌ Failed to load calibration weights: {e}")
        logger.warning("  Using default weights: Ohio=0.65, SP+=0.35")
        return {
            'ohio_model_weight': 0.65,
            'sp_weight': 0.35
        }


def calculate_calibrated_margin(ensemble_margin: float, sp_margin: Optional[float],
                                weights: Dict[str, float]) -> Optional[float]:
    """Calculate calibrated ensemble margin."""
    ohio_weight = weights.get('ohio_model_weight', 0.65)
    sp_weight = weights.get('sp_weight', 0.35)
    
    # Calculate weighted average, handling missing values
    terms = []
    total_weight = 0.0
    
    # Ohio model (always present)
    terms.append(ohio_weight * ensemble_margin)
    total_weight += ohio_weight
    
    # SP+ (if available)
    if sp_margin is not None and not np.isnan(sp_margin):
        terms.append(sp_weight * sp_margin)
        total_weight += sp_weight
    else:
        # Redistribute SP+ weight to Ohio model
        redist_weight = sp_weight / ohio_weight
        terms[0] *= (1 + redist_weight)
    
    if total_weight == 0:
        return None
    
    return sum(terms) / total_weight


def enhance_predictions(df: pd.DataFrame, ratings: Dict[str, Dict[str, float]],
                        weights: Dict[str, float]) -> pd.DataFrame:
    """Enhance predictions with SP+ ratings, calibrated ensemble, and matchup analysis."""
    logger.info("🔧 Enhancing predictions with SP+ ratings...")
    
    enhanced_df = df.copy()
    
    # Initialize new columns
    # SP+ Ratings
    enhanced_df['home_sp'] = np.nan
    enhanced_df['away_sp'] = np.nan
    enhanced_df['home_sp_off'] = np.nan
    enhanced_df['away_sp_off'] = np.nan
    enhanced_df['home_sp_def'] = np.nan
    enhanced_df['away_sp_def'] = np.nan
    enhanced_df['home_sp_st'] = np.nan
    enhanced_df['away_sp_st'] = np.nan
    enhanced_df['home_sp_rank'] = np.nan
    enhanced_df['away_sp_rank'] = np.nan
    
    # SP+ Predictions
    enhanced_df['sp_predicted_margin'] = np.nan
    enhanced_df['sp_home_win_prob'] = np.nan
    enhanced_df['ohio_vs_sp_diff'] = np.nan
    
    # Calibrated Ensemble
    enhanced_df['calibrated_margin'] = np.nan
    enhanced_df['calibrated_home_win_prob'] = np.nan
    enhanced_df['calibrated_vs_ohio_diff'] = np.nan
    
    # Matchup Analysis
    enhanced_df['offense_matchup'] = np.nan
    enhanced_df['defense_matchup'] = np.nan
    enhanced_df['sp_matchup_advantage'] = np.nan
    
    missing_teams = set()
    
    # Determine neutral_site column name
    neutral_col = None
    for col in ['neutral_site', 'neutralSite', 'neutral']:
        if col in enhanced_df.columns:
            neutral_col = col
            break
    
    for idx, row in enhanced_df.iterrows():
        home_team = row.get('home_team', '')
        away_team = row.get('away_team', '')
        neutral_site = row.get(neutral_col, False) if neutral_col else False
        
        # Get ensemble margin
        ensemble_margin = row.get('ensemble_margin') or row.get('predicted_margin')
        if ensemble_margin is None or np.isnan(ensemble_margin):
            continue
        
        # Match team names
        home_key = match_team_name(home_team, ratings) if home_team else None
        away_key = match_team_name(away_team, ratings) if away_team else None
        
        if home_key and away_key:
            home_rating = ratings[home_key]
            away_rating = ratings[away_key]
            
            # Add SP+ ratings
            enhanced_df.at[idx, 'home_sp'] = home_rating.get('sp')
            enhanced_df.at[idx, 'away_sp'] = away_rating.get('sp')
            enhanced_df.at[idx, 'home_sp_off'] = home_rating.get('sp_off')
            enhanced_df.at[idx, 'away_sp_off'] = away_rating.get('sp_off')
            enhanced_df.at[idx, 'home_sp_def'] = home_rating.get('sp_def')
            enhanced_df.at[idx, 'away_sp_def'] = away_rating.get('sp_def')
            enhanced_df.at[idx, 'home_sp_st'] = home_rating.get('sp_st')
            enhanced_df.at[idx, 'away_sp_st'] = away_rating.get('sp_st')
            enhanced_df.at[idx, 'home_sp_rank'] = home_rating.get('sp_rank')
            enhanced_df.at[idx, 'away_sp_rank'] = away_rating.get('sp_rank')
            
            # Calculate SP+ margin
            sp_margin = calculate_sp_margin(
                home_rating.get('sp'),
                away_rating.get('sp'),
                neutral_site
            )
            if sp_margin is not None:
                enhanced_df.at[idx, 'sp_predicted_margin'] = sp_margin
                enhanced_df.at[idx, 'sp_home_win_prob'] = margin_to_win_prob(sp_margin)
                enhanced_df.at[idx, 'ohio_vs_sp_diff'] = ensemble_margin - sp_margin
            
            # Calculate matchup analysis
            if home_rating.get('sp_off') is not None and away_rating.get('sp_def') is not None:
                enhanced_df.at[idx, 'offense_matchup'] = (
                    home_rating.get('sp_off') - away_rating.get('sp_def')
                )
            
            if home_rating.get('sp_def') is not None and away_rating.get('sp_off') is not None:
                enhanced_df.at[idx, 'defense_matchup'] = (
                    home_rating.get('sp_def') - away_rating.get('sp_off')
                )
            
            if home_rating.get('sp') is not None and away_rating.get('sp') is not None:
                enhanced_df.at[idx, 'sp_matchup_advantage'] = (
                    home_rating.get('sp') - away_rating.get('sp')
                )
            
            # Calculate calibrated ensemble
            calibrated_margin = calculate_calibrated_margin(
                ensemble_margin, sp_margin, weights
            )
            
            if calibrated_margin is not None:
                enhanced_df.at[idx, 'calibrated_margin'] = calibrated_margin
                enhanced_df.at[idx, 'calibrated_home_win_prob'] = margin_to_win_prob(calibrated_margin)
                enhanced_df.at[idx, 'calibrated_vs_ohio_diff'] = calibrated_margin - ensemble_margin
        else:
            if home_team and not home_key:
                missing_teams.add(home_team)
            if away_team and not away_key:
                missing_teams.add(away_team)
    
    if missing_teams:
        logger.warning(f"⚠️  Missing ratings for {len(missing_teams)} teams: {list(missing_teams)[:10]}")
    
    sp_count = enhanced_df['sp_predicted_margin'].notna().sum()
    calibrated_count = enhanced_df['calibrated_margin'].notna().sum()
    
    logger.info(f"  ✅ SP+ predictions: {sp_count}/{len(enhanced_df)}")
    logger.info(f"  ✅ Calibrated predictions: {calibrated_count}/{len(enhanced_df)}")
    
    return enhanced_df


def main():
    """Main execution function."""
    logger.info("=" * 80)
    logger.info("WEEK 14 PREDICTIONS ENHANCEMENT WITH SP+ RATINGS")
    logger.info("=" * 80)
    logger.info(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Step 1: Load Week 14 predictions
        logger.info("\n" + "=" * 80)
        logger.info("Step 1: Loading Week 14 Predictions")
        logger.info("=" * 80)
        
        predictions_path = project_root / 'predictions' / 'week14' / 'week14_model_predictions.csv'
        
        if not predictions_path.exists():
            logger.error(f"❌ Predictions file not found: {predictions_path}")
            return 1
        
        predictions_df = pd.read_csv(predictions_path, low_memory=False)
        logger.info(f"✅ Loaded {len(predictions_df)} predictions from {predictions_path}")
        
        # Step 2: Load SP+ ratings from CSV
        logger.info("\n" + "=" * 80)
        logger.info("Step 2: Loading SP+ Ratings from CSV")
        logger.info("=" * 80)
        
        sp_csv_path = project_root / '2025 SP+ - FBS Week 14.csv'
        ratings = load_sp_ratings_from_csv(sp_csv_path)
        
        if not ratings:
            logger.error("❌ No ratings loaded. Cannot enhance predictions.")
            return 1
        
        # Step 3: Load calibration weights
        logger.info("\n" + "=" * 80)
        logger.info("Step 3: Loading Calibration Weights")
        logger.info("=" * 80)
        weights = load_calibration_weights()
        
        # Step 4: Enhance predictions
        logger.info("\n" + "=" * 80)
        logger.info("Step 4: Enhancing Predictions")
        logger.info("=" * 80)
        enhanced_df = enhance_predictions(predictions_df, ratings, weights)
        
        # Step 5: Save enhanced predictions
        logger.info("\n" + "=" * 80)
        logger.info("Step 5: Saving Enhanced Predictions")
        logger.info("=" * 80)
        
        output_dir = project_root / 'predictions' / 'week14'
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_path = output_dir / 'week14_predictions_enhanced.csv'
        enhanced_df.to_csv(output_path, index=False)
        logger.info(f"✅ Saved enhanced predictions to {output_path}")
        
        # Summary
        logger.info("\n" + "=" * 80)
        logger.info("✅ ENHANCEMENT COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Enhanced {len(enhanced_df)} predictions")
        logger.info(f"SP+ predictions: {enhanced_df['sp_predicted_margin'].notna().sum()}")
        logger.info(f"Calibrated predictions: {enhanced_df['calibrated_margin'].notna().sum()}")
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Enhancement failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())

