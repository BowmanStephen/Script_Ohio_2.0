#!/usr/bin/env python3
"""
Enhance Week 13 predictions with SP+/FPI ratings and calibrated ensemble.

This script:
1. Loads Week 13 predictions
2. Fetches SP+/FPI ratings from CFBD GraphQL API
3. Calculates SP+/FPI predicted margins
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

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not required if API key set via environment

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

# Try to import GraphQL client
try:
    from src.data_sources.cfbd_graphql import CFBDGraphQLClient
    GQL_AVAILABLE = True
except ImportError:
    GQL_AVAILABLE = False
    logger.warning("GraphQL client not available. SP+/FPI ratings will not be fetched.")

# Try to import Prediction_Tracker loader
try:
    from scripts.load_prediction_tracker import load_prediction_tracker
    TRACKER_AVAILABLE = True
except ImportError:
    TRACKER_AVAILABLE = False
    logger.warning("Prediction_Tracker loader not available. Meta-ensemble will not be calculated.")


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
        'UL-Lafayette': 'Louisiana',
        'Louisiana-Lafayette': 'Louisiana',
        'UL-Monroe': 'Louisiana Monroe',
        'Louisiana-Monroe': 'Louisiana Monroe',
        'Appalachian State': 'Appalachian State',
        'App State': 'Appalachian State',
        'Florida Atlantic': 'FAU',
        'Florida International': 'FIU',
        'San Jose State': 'San Jose State',
        'San Jose St.': 'San Jose State',
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
            # Additional check: ensure it's not a substring match (e.g., Buffalo vs Buffalo State)
            # If one contains the other, prefer the longer match only if lengths are very different
            if len(team_name) == len(key) or (normalized == team_name or normalized == key):
                return key
    
    # 5. Last resort: substring match only if one is clearly a subset (but avoid this if possible)
    # Skip this to avoid false matches - return None instead
    
    return None


def load_sp_ratings_from_csv(csv_path: Optional[Path] = None) -> Dict[str, Dict[str, float]]:
    """
    Load SP+ ratings from CSV file.
    
    Args:
        csv_path: Path to CSV file. If None, searches for "2025 SP+" CSV file in project root.
    
    Returns:
        Dict mapping team_name -> {'sp': rating, 'fpi': None}
    """
    if csv_path is None:
        # Search for SP+ CSV file in project root
        sp_csv_patterns = [
            project_root / "2025 SP+ - TOP 766 Week 13.csv",
            project_root / "*SP*.csv",
            project_root / "*sp*.csv",
        ]
        
        csv_path = None
        for pattern in sp_csv_patterns:
            if pattern.exists():
                csv_path = pattern
                break
            elif '*' in str(pattern):
                # Try glob pattern
                matches = list(project_root.glob(pattern.name))
                if matches:
                    csv_path = matches[0]
                    break
    
    if csv_path is None or not Path(csv_path).exists():
        logger.debug("⚠️  SP+ CSV file not found, skipping CSV load")
        return {}
    
    try:
        logger.info(f"📂 Loading SP+ ratings from CSV: {csv_path}")
        df = pd.read_csv(csv_path, low_memory=False)
        
        # Map column names (handle variations)
        team_col = 'Team' if 'Team' in df.columns else 'team' if 'team' in df.columns else df.columns[0]
        sp_col = 'SP+' if 'SP+' in df.columns else 'sp' if 'sp' in df.columns else 'spOverall' if 'spOverall' in df.columns else None
        
        if sp_col is None:
            logger.warning(f"⚠️  Could not find SP+ column in CSV. Available columns: {list(df.columns)}")
            return {}
        
        team_ratings = {}
        for _, row in df.iterrows():
            team = row[team_col]
            sp_rating = row[sp_col]
            
            if pd.notna(team) and pd.notna(sp_rating):
                team_str = str(team).strip()
                # Normalize team name for matching
                normalized_name = normalize_team_name(team_str)
                
                # Store with original name (primary key)
                if team_str not in team_ratings:
                    team_ratings[team_str] = {
                        'sp': float(sp_rating),
                        'fpi': None  # CSV doesn't have FPI
                    }
                
                # Store with normalized name (only if different from original)
                # This helps with matching variations like "Miami-OH" vs "Miami OH"
                if normalized_name != team_str and normalized_name not in team_ratings:
                    team_ratings[normalized_name] = {
                        'sp': float(sp_rating),
                        'fpi': None
                    }
        
        logger.info(f"  ✅ Loaded SP+ ratings for {len(df)} teams from CSV")
        return team_ratings
        
    except Exception as e:
        logger.warning(f"⚠️  Error loading SP+ CSV: {e}")
        import traceback
        traceback.print_exc()
        return {}


def fetch_sp_fpi_ratings(season: int = 2025, use_csv: bool = True) -> Dict[str, Dict[str, float]]:
    """
    Fetch SP+ and FPI ratings from CFBD GraphQL API, optionally supplemented with CSV.
    
    Args:
        season: Season year
        use_csv: If True, load SP+ from CSV as primary source, use API for FPI
    
    Returns:
        Dict mapping team_name -> {'sp': rating, 'fpi': rating}
    """
    ratings = {}
    
    # Try to load from CSV first (more reliable for SP+)
    if use_csv:
        csv_ratings = load_sp_ratings_from_csv()
        if csv_ratings:
            ratings.update(csv_ratings)
            logger.info(f"✅ Loaded {len(csv_ratings)} SP+ ratings from CSV")
    
    # Fetch from API for FPI (and supplement SP+ if CSV missing some teams)
    if GQL_AVAILABLE:
        api_key = os.getenv("CFBD_API_KEY")
        if api_key:
            try:
                logger.info(f"📡 Fetching SP+/FPI ratings from CFBD GraphQL API...")
                client = CFBDGraphQLClient(api_key=api_key)
                result = client.get_ratings(season=season)
                
                # Handle both response formats
                if 'ratings' in result:
                    api_ratings = result['ratings']
                elif 'data' in result and 'ratings' in result['data']:
                    api_ratings = result['data']['ratings']
                else:
                    logger.warning("⚠️  No ratings data in GraphQL response")
                    api_ratings = []
                
                if api_ratings:
                    # Merge API ratings (prefer CSV for SP+, use API for FPI)
                    for rating in api_ratings:
                        team = rating.get('team')
                        if team:
                            normalized = normalize_team_name(team)
                            
                            # Initialize if not exists
                            if normalized not in ratings:
                                ratings[normalized] = {'sp': None, 'fpi': None}
                            
                            # Use API SP+ only if CSV didn't have it
                            if ratings[normalized]['sp'] is None:
                                ratings[normalized]['sp'] = rating.get('spOverall')
                            
                            # Always use API FPI (CSV doesn't have it)
                            fpi_rating = rating.get('fpi')
                            if fpi_rating is not None:
                                ratings[normalized]['fpi'] = fpi_rating
                    
                    logger.info(f"  ✅ Merged API ratings for {len(api_ratings)} teams")
                
            except Exception as e:
                logger.warning(f"⚠️  Failed to fetch from API: {e}")
                # Continue with CSV data only
    
    # Filter out entries with no ratings at all
    ratings = {k: v for k, v in ratings.items() if v.get('sp') is not None or v.get('fpi') is not None}
    
    logger.info(f"✅ Total ratings loaded: {len(ratings)} teams")
    return ratings


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


def load_calibration_weights() -> Dict[str, float]:
    """Load calibrated weights from config file."""
    weights_path = project_root / 'config' / 'calibration_weights.json'
    
    if not weights_path.exists():
        logger.warning(f"⚠️  Calibration weights not found at {weights_path}")
        logger.warning("  Using default weights: Ohio=0.65, SP+=0.25, FPI=0.10")
        return {
            'ohio_model_weight': 0.65,
            'sp_weight': 0.25,
            'fpi_weight': 0.10
        }
    
    try:
        with open(weights_path, 'r') as f:
            weights = json.load(f)
        
        logger.info(f"✅ Loaded calibration weights from {weights_path}")
        logger.info(f"  Ohio={weights.get('ohio_model_weight', 0.65):.3f}, "
                   f"SP+={weights.get('sp_weight', 0.25):.3f}, "
                   f"FPI={weights.get('fpi_weight', 0.10):.3f}")
        
        return weights
        
    except Exception as e:
        logger.error(f"❌ Failed to load calibration weights: {e}")
        logger.warning("  Using default weights: Ohio=0.65, SP+=0.25, FPI=0.10")
        return {
            'ohio_model_weight': 0.65,
            'sp_weight': 0.25,
            'fpi_weight': 0.10
        }


def load_meta_ensemble_weights() -> Dict[str, float]:
    """Load meta-ensemble weights from config file."""
    weights_path = project_root / 'config' / 'meta_ensemble_weights.json'
    
    if not weights_path.exists():
        logger.debug(f"⚠️  Meta-ensemble weights not found at {weights_path}")
        return {}
    
    try:
        with open(weights_path, 'r') as f:
            weights = json.load(f)
        
        logger.info(f"✅ Loaded meta-ensemble weights from {weights_path}")
        return weights
        
    except Exception as e:
        logger.warning(f"⚠️  Failed to load meta-ensemble weights: {e}")
        return {}


def calculate_meta_ensemble_margin(
    ohio_margin: float,
    system_avg: Optional[float],
    opening_line: Optional[float],
    sagarin: Optional[float],
    sp_plus: Optional[float],
    weights: Dict[str, float]
) -> Optional[float]:
    """Calculate meta-ensemble margin from individual system predictions."""
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


def calculate_calibrated_margin(ensemble_margin: float, sp_margin: Optional[float],
                                 fpi_margin: Optional[float], weights: Dict[str, float]) -> Optional[float]:
    """Calculate calibrated ensemble margin."""
    ohio_weight = weights.get('ohio_model_weight', 0.65)
    sp_weight = weights.get('sp_weight', 0.25)
    fpi_weight = weights.get('fpi_weight', 0.10)
    
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
        # Redistribute SP+ weight to other terms
        redist_weight = sp_weight / (ohio_weight + fpi_weight)
        terms[0] *= (1 + redist_weight)
        if fpi_margin is not None:
            fpi_weight *= (1 + redist_weight)
    
    # FPI (if available)
    if fpi_margin is not None and not np.isnan(fpi_margin):
        terms.append(fpi_weight * fpi_margin)
        total_weight += fpi_weight
    else:
        # Redistribute FPI weight to other terms
        if len(terms) > 0:
            redist_weight = fpi_weight / sum([ohio_weight, sp_weight if sp_margin is not None else 0])
            for i in range(len(terms)):
                terms[i] *= (1 + redist_weight)
    
    if total_weight == 0:
        return None
    
    return sum(terms) / total_weight


def margin_to_win_prob(margin: float) -> float:
    """Convert margin to home win probability using logistic function."""
    # Using logistic transform: p = 1 / (1 + exp(-margin / scale))
    # Scale of 7 is typical for college football
    scale = 7.0
    return 1.0 / (1.0 + np.exp(-margin / scale))


def enhance_predictions(df: pd.DataFrame, ratings: Dict[str, Dict[str, float]],
                        weights: Dict[str, float], tracker_df: Optional[pd.DataFrame] = None,
                        meta_weights: Optional[Dict[str, float]] = None) -> pd.DataFrame:
    """Enhance predictions with SP+/FPI ratings, calibrated ensemble, and meta-ensemble."""
    logger.info("🔧 Enhancing predictions with SP+/FPI ratings...")
    
    enhanced_df = df.copy()
    
    # Initialize new columns
    enhanced_df['sp_predicted_margin'] = np.nan
    enhanced_df['fpi_predicted_margin'] = np.nan
    enhanced_df['calibrated_margin'] = np.nan
    enhanced_df['calibrated_home_win_prob'] = np.nan
    enhanced_df['ohio_vs_sp_diff'] = np.nan
    enhanced_df['ohio_vs_fpi_diff'] = np.nan
    enhanced_df['calibrated_vs_ohio_diff'] = np.nan
    # Meta-ensemble columns
    enhanced_df['meta_ensemble_margin'] = np.nan
    enhanced_df['meta_ensemble_win_prob'] = np.nan
    enhanced_df['ohio_vs_system_avg_diff'] = np.nan
    enhanced_df['meta_vs_ohio_diff'] = np.nan
    
    missing_teams = set()
    
    # Determine neutral_site column name (check common variations)
    neutral_col = None
    for col in ['neutral_site', 'neutralSite', 'neutral']:
        if col in enhanced_df.columns:
            neutral_col = col
            break
    
    for idx, row in enhanced_df.iterrows():
        home_team = row.get('home_team', '')
        away_team = row.get('away_team', '')
        neutral_site = row.get(neutral_col, False) if neutral_col else False
        
        # Get ensemble margin (check common column names)
        ensemble_margin = row.get('ensemble_margin') or row.get('predicted_margin')
        if ensemble_margin is None or np.isnan(ensemble_margin):
            continue
        
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
            if sp_margin is not None:
                enhanced_df.at[idx, 'sp_predicted_margin'] = sp_margin
                enhanced_df.at[idx, 'ohio_vs_sp_diff'] = ensemble_margin - sp_margin
            
            # Calculate FPI margin
            fpi_margin = calculate_fpi_predicted_margin(
                home_rating.get('fpi'),
                away_rating.get('fpi'),
                neutral_site
            )
            if fpi_margin is not None:
                enhanced_df.at[idx, 'fpi_predicted_margin'] = fpi_margin
                enhanced_df.at[idx, 'ohio_vs_fpi_diff'] = ensemble_margin - fpi_margin
            
            # Calculate calibrated ensemble
            calibrated_margin = calculate_calibrated_margin(
                ensemble_margin, sp_margin, fpi_margin, weights
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
    
    # Add meta-ensemble if Prediction_Tracker data available
    if tracker_df is not None and meta_weights:
        logger.info("🔧 Adding meta-ensemble predictions...")
        
        # Create game keys for matching
        def create_key(row):
            home = str(row.get('home_team', '')).strip().lower()
            away = str(row.get('away_team', '')).strip().lower()
            week = row.get('week', '')
            season = row.get('season', 2025)
            return f"{season}_{week}_{away}_{home}"
        
        if 'game_key' not in enhanced_df.columns:
            enhanced_df['game_key'] = enhanced_df.apply(create_key, axis=1)
        if 'game_key' not in tracker_df.columns:
            tracker_df['game_key'] = tracker_df.apply(create_key, axis=1)
        
        # Merge with Prediction_Tracker
        tracker_merged = enhanced_df.merge(
            tracker_df[['game_key', 'system_average', 'opening_line', 'sagarin']],
            on='game_key',
            how='left',
            suffixes=('', '_tracker')
        )
        
        # Calculate meta-ensemble for each game
        ohio_col = 'ensemble_margin' if 'ensemble_margin' in enhanced_df.columns else 'predicted_margin'
        for idx, row in tracker_merged.iterrows():
            ohio_margin = row.get(ohio_col, np.nan)
            if np.isnan(ohio_margin):
                continue
            
            system_avg = row.get('system_average', np.nan)
            opening_line = row.get('opening_line', np.nan)
            sagarin = row.get('sagarin', np.nan)
            sp_plus = row.get('sp_predicted_margin', np.nan)
            
            meta_margin = calculate_meta_ensemble_margin(
                ohio_margin, system_avg, opening_line, sagarin, sp_plus, meta_weights
            )
            
            if meta_margin is not None:
                enhanced_df.at[idx, 'meta_ensemble_margin'] = meta_margin
                enhanced_df.at[idx, 'meta_ensemble_win_prob'] = margin_to_win_prob(meta_margin)
                enhanced_df.at[idx, 'ohio_vs_system_avg_diff'] = ohio_margin - system_avg if not np.isnan(system_avg) else np.nan
                enhanced_df.at[idx, 'meta_vs_ohio_diff'] = meta_margin - ohio_margin
        
        meta_count = enhanced_df['meta_ensemble_margin'].notna().sum()
        logger.info(f"  ✅ Meta-ensemble predictions: {meta_count}/{len(enhanced_df)}")
    
    sp_count = enhanced_df['sp_predicted_margin'].notna().sum()
    fpi_count = enhanced_df['fpi_predicted_margin'].notna().sum()
    calibrated_count = enhanced_df['calibrated_margin'].notna().sum()
    
    logger.info(f"  ✅ SP+ predictions: {sp_count}/{len(enhanced_df)}")
    logger.info(f"  ✅ FPI predictions: {fpi_count}/{len(enhanced_df)}")
    logger.info(f"  ✅ Calibrated predictions: {calibrated_count}/{len(enhanced_df)}")
    
    return enhanced_df


def generate_enhancement_summary(df: pd.DataFrame, weights: Dict[str, float]) -> str:
    """Generate enhancement summary report."""
    sp_count = df['sp_predicted_margin'].notna().sum()
    fpi_count = df['fpi_predicted_margin'].notna().sum()
    calibrated_count = df['calibrated_margin'].notna().sum()
    
    # Calculate divergence statistics
    ohio_vs_sp = df['ohio_vs_sp_diff'].dropna()
    ohio_vs_fpi = df['ohio_vs_fpi_diff'].dropna()
    calibrated_vs_ohio = df['calibrated_vs_ohio_diff'].dropna()
    
    report_lines = [
        "# Week 13 Predictions Enhancement Summary",
        "",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Overview",
        "",
        f"This report summarizes the enhancement of Week 13 predictions with SP+/FPI",
        f"ratings and calibrated ensemble predictions.",
        "",
        "## Calibration Weights",
        "",
        f"- **Ohio Model Weight:** {weights.get('ohio_model_weight', 0.65):.3f}",
        f"- **SP+ Weight:** {weights.get('sp_weight', 0.25):.3f}",
        f"- **FPI Weight:** {weights.get('fpi_weight', 0.10):.3f}",
        "",
        "## Coverage",
        "",
        f"- **Total Games:** {len(df)}",
        f"- **SP+ Predictions:** {sp_count} ({sp_count/len(df)*100:.1f}%)",
        f"- **FPI Predictions:** {fpi_count} ({fpi_count/len(df)*100:.1f}%)",
        f"- **Calibrated Predictions:** {calibrated_count} ({calibrated_count/len(df)*100:.1f}%)",
        "",
        "## Divergence Analysis",
        "",
        "### Ohio Model vs SP+",
        "",
        f"- **Mean Difference:** {ohio_vs_sp.mean():.2f} points",
        f"- **Std Dev:** {ohio_vs_sp.std():.2f} points",
        f"- **Games with SP+:** {len(ohio_vs_sp)}",
        "",
        "### Ohio Model vs FPI",
        "",
        f"- **Mean Difference:** {ohio_vs_fpi.mean():.2f} points",
        f"- **Std Dev:** {ohio_vs_fpi.std():.2f} points",
        f"- **Games with FPI:** {len(ohio_vs_fpi)}",
        "",
        "### Calibrated vs Ohio Model",
        "",
        f"- **Mean Difference:** {calibrated_vs_ohio.mean():.2f} points",
        f"- **Std Dev:** {calibrated_vs_ohio.std():.2f} points",
        f"- **Games Calibrated:** {len(calibrated_vs_ohio)}",
        "",
        "## Key Insights",
        "",
        "1. **Calibration Impact:** The calibrated ensemble adjusts Ohio Model",
        "   predictions based on SP+ and FPI ratings.",
        "",
        "2. **System Agreement:** Large divergences between systems may indicate",
        "   games with higher uncertainty.",
        "",
        "3. **Weight Distribution:** Current weights favor Ohio Model predictions",
        f"   ({weights.get('ohio_model_weight', 0.65):.0%}) with SP+ and FPI providing",
        "   calibration signals.",
        "",
        "## Usage",
        "",
        "The enhanced predictions include:",
        "",
        "- `sp_predicted_margin`: SP+ predicted spread",
        "- `fpi_predicted_margin`: FPI predicted spread",
        "- `calibrated_margin`: Optimal blend prediction",
        "- `calibrated_home_win_prob`: Calibrated win probability",
        "- Divergence columns for analysis",
        "",
        "Use `calibrated_margin` and `calibrated_home_win_prob` for final predictions.",
        ""
    ]
    
    return "\n".join(report_lines)


def main():
    """Main execution function."""
    logger.info("=" * 80)
    logger.info("WEEK 13 PREDICTIONS ENHANCEMENT")
    logger.info("=" * 80)
    logger.info(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Step 1: Load Week 13 predictions
        logger.info("\n" + "=" * 80)
        logger.info("Step 1: Loading Week 13 Predictions")
        logger.info("=" * 80)
        
        predictions_path = project_root / 'predictions' / 'week13' / 'week13_predictions_all_60_games.csv'
        
        if not predictions_path.exists():
            logger.error(f"❌ Predictions file not found: {predictions_path}")
            logger.error("   Run prediction scripts first to generate predictions.")
            return 1
        
        predictions_df = pd.read_csv(predictions_path, low_memory=False)
        logger.info(f"✅ Loaded {len(predictions_df)} predictions from {predictions_path}")
        
        # Step 2: Fetch SP+/FPI ratings
        logger.info("\n" + "=" * 80)
        logger.info("Step 2: Fetching SP+/FPI Ratings")
        logger.info("=" * 80)
        ratings = fetch_sp_fpi_ratings(season=2025)
        
        if not ratings:
            logger.warning("⚠️  No ratings fetched. Cannot enhance predictions.")
            return 1
        
        # Step 3: Load calibration weights
        logger.info("\n" + "=" * 80)
        logger.info("Step 3: Loading Calibration Weights")
        logger.info("=" * 80)
        weights = load_calibration_weights()
        
        # Step 3.5: Load Prediction_Tracker data and meta-ensemble weights
        tracker_df = None
        meta_weights = None
        if TRACKER_AVAILABLE:
            logger.info("\n" + "=" * 80)
            logger.info("Step 3.5: Loading Prediction_Tracker Data")
            logger.info("=" * 80)
            try:
                # Extract week from predictions if available
                week = predictions_df.get('week', pd.Series([13])).iloc[0] if 'week' in predictions_df.columns else 13
                tracker_df = load_prediction_tracker(week=week, season=2025)
                if not tracker_df.empty:
                    logger.info(f"✅ Loaded {len(tracker_df)} games from Prediction_Tracker")
                    meta_weights = load_meta_ensemble_weights()
                    if meta_weights:
                        logger.info("✅ Loaded meta-ensemble weights")
                    else:
                        logger.warning("⚠️  Meta-ensemble weights not available, using defaults")
                        meta_weights = {
                            'ohio_weight': 0.35,
                            'system_average_weight': 0.25,
                            'opening_line_weight': 0.20,
                            'sagarin_weight': 0.10,
                            'sp_plus_weight': 0.10
                        }
                else:
                    logger.warning("⚠️  No Prediction_Tracker data available")
            except Exception as e:
                logger.warning(f"⚠️  Failed to load Prediction_Tracker data: {e}")
        
        # Step 4: Enhance predictions
        logger.info("\n" + "=" * 80)
        logger.info("Step 4: Enhancing Predictions")
        logger.info("=" * 80)
        enhanced_df = enhance_predictions(predictions_df, ratings, weights, tracker_df, meta_weights)
        
        # Step 5: Save enhanced predictions
        logger.info("\n" + "=" * 80)
        logger.info("Step 5: Saving Enhanced Predictions")
        logger.info("=" * 80)
        
        output_dir = project_root / 'predictions' / 'week13'
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_path = output_dir / 'week13_predictions_enhanced.csv'
        enhanced_df.to_csv(output_path, index=False)
        logger.info(f"✅ Saved enhanced predictions to {output_path}")
        
        # Generate and save summary report
        reports_dir = project_root / 'reports'
        reports_dir.mkdir(exist_ok=True)
        
        summary_content = generate_enhancement_summary(enhanced_df, weights)
        summary_path = reports_dir / 'week13_enhancement_summary.md'
        with open(summary_path, 'w') as f:
            f.write(summary_content)
        logger.info(f"✅ Saved enhancement summary to {summary_path}")
        
        # Summary
        logger.info("\n" + "=" * 80)
        logger.info("✅ ENHANCEMENT COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Enhanced {len(enhanced_df)} predictions")
        logger.info(f"SP+ predictions: {enhanced_df['sp_predicted_margin'].notna().sum()}")
        logger.info(f"FPI predictions: {enhanced_df['fpi_predicted_margin'].notna().sum()}")
        logger.info(f"Calibrated predictions: {enhanced_df['calibrated_margin'].notna().sum()}")
        if 'meta_ensemble_margin' in enhanced_df.columns:
            logger.info(f"Meta-ensemble predictions: {enhanced_df['meta_ensemble_margin'].notna().sum()}")
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Enhancement failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
