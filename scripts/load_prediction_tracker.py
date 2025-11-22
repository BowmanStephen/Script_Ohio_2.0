#!/usr/bin/env python3
"""
Load and normalize Prediction_Tracker data for multi-system ensemble.

This script:
1. Loads Prediction_Tracker CSV files (support multiple weeks)
2. Parses system columns: lineavg (System Average), lineopen (Opening Line), 
   linesag (Sagarin), linebig200 (Big 200), etc.
3. Normalizes team names to match Ohio Model format
4. Maps predictions to game identifiers (home_team, away_team, week, season)
5. Handles missing data gracefully
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
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
    Reuses logic from enhance_predictions_with_ratings.py
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
        'UL-Monroe': 'Louisiana Monroe',
        'Louisiana-Monroe': 'Louisiana Monroe',
        'Appalachian State': 'Appalachian State',
        'Appalachian St.': 'Appalachian State',
        'App State': 'Appalachian State',
        'Florida Atlantic': 'FAU',
        'Florida International': 'FIU',
        'San Jose State': 'San Jose State',
        'San Jose St.': 'San Jose State',
        'UCF': 'UCF',
        'Central Florida': 'UCF',
        'USF': 'USF',
        'South Florida': 'USF',
        'Arkansas St.': 'Arkansas State',
        'Arkansas St': 'Arkansas State',
        'Boise St.': 'Boise State',
        'Boise St': 'Boise State',
        'Colorado St.': 'Colorado State',
        'Colorado St': 'Colorado State',
        'Oklahoma St.': 'Oklahoma State',
        'Oklahoma St': 'Oklahoma State',
        'Oregon St.': 'Oregon State',
        'Oregon St': 'Oregon State',
        'Washington St.': 'Washington State',
        'Washington St': 'Washington State',
        'Michigan St.': 'Michigan State',
        'Michigan St': 'Michigan State',
        'Iowa St.': 'Iowa State',
        'Iowa St': 'Iowa State',
        'Kansas St.': 'Kansas State',
        'Kansas St': 'Kansas State',
        'Kent St.': 'Kent State',
        'Kent St': 'Kent State',
        'NC St.': 'NC State',
        'NC St': 'NC State',
        'Penn St.': 'Penn State',
        'Penn St': 'Penn State',
        'Fresno St.': 'Fresno State',
        'Fresno St': 'Fresno State',
        'Utah St.': 'Utah State',
        'Utah St': 'Utah State',
        'Sam Houston St.': 'Sam Houston State',
        'Sam Houston St': 'Sam Houston State',
        'Middle Tenn.': 'Middle Tennessee',
        'Middle Tenn': 'Middle Tennessee',
        'Northern Ill.': 'Northern Illinois',
        'Northern Ill': 'Northern Illinois',
        'Western Mich.': 'Western Michigan',
        'Western Mich': 'Western Michigan',
        'Central Mich.': 'Central Michigan',
        'Central Mich': 'Central Michigan',
        'Bowling Green': 'Bowling Green',
        'Bowling Green St.': 'Bowling Green',
        'Texas-San Antonio': 'UTSA',
        'UTSA': 'UTSA',
        'Louisiana Tech': 'Louisiana Tech',
        'LA Tech': 'Louisiana Tech',
    }
    
    # Check exact match first
    if team in variations:
        return variations[team]
    
    # Handle hyphenated names (CSV format: "Miami-FL")
    if '-' in team:
        parts = team.split('-')
        if len(parts) == 2:
            name, suffix = parts
            if suffix.upper() in ['FL', 'OH', 'CA', 'TX', 'NY']:
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


def load_prediction_tracker_file(file_path: Path, week: Optional[int] = None, 
                                  season: int = 2025) -> pd.DataFrame:
    """
    Load a single Prediction_Tracker CSV file.
    
    Args:
        file_path: Path to Prediction_Tracker CSV file
        week: Week number (extracted from filename if not provided)
        season: Season year (default 2025)
    
    Returns:
        DataFrame with normalized Prediction_Tracker data
    """
    if not file_path.exists():
        logger.warning(f"⚠️  File not found: {file_path}")
        return pd.DataFrame()
    
    try:
        logger.info(f"📂 Loading Prediction_Tracker from {file_path}")
        df = pd.read_csv(file_path, low_memory=False)
        
        if df.empty:
            logger.warning(f"⚠️  File is empty: {file_path}")
            return pd.DataFrame()
        
        # Extract week from filename if not provided
        if week is None:
            filename = file_path.name
            # Try to extract week from filename (e.g., "Prediction_Tracker_week13.csv")
            if 'week' in filename.lower():
                try:
                    week_str = filename.lower().split('week')[1].split('.')[0]
                    week = int(week_str)
                except (ValueError, IndexError):
                    logger.warning(f"⚠️  Could not extract week from filename: {filename}")
                    week = None
        
        # Normalize team names
        if 'home' in df.columns and 'road' in df.columns:
            df['home_team'] = df['home'].apply(normalize_team_name)
            df['away_team'] = df['road'].apply(normalize_team_name)
        else:
            logger.error(f"❌ Missing 'home' or 'road' columns in {file_path}")
            return pd.DataFrame()
        
        # Add metadata
        df['season'] = season
        if week is not None:
            df['week'] = week
        
        # Extract key system predictions
        system_columns = {
            'lineavg': 'system_average',
            'lineopen': 'opening_line',
            'linesag': 'sagarin',
            'linebig200': 'big_200',
            'linefpi': 'fpi',
            'linemassey': 'massey',
            'lineelo': 'elo',
            'line': 'consensus_line',  # Consensus line (may be different from opening)
        }
        
        # Rename system columns
        for old_col, new_col in system_columns.items():
            if old_col in df.columns:
                df[new_col] = df[old_col]
            else:
                df[new_col] = np.nan
        
        # Extract actual results if available
        if 'phcover' in df.columns:
            df['actual_cover'] = df['phcover']
        if 'phwin' in df.columns:
            df['actual_win'] = df['phwin']
        
        # Extract neutral site flag
        if 'neutral' in df.columns:
            df['neutral_site'] = df['neutral'].fillna(0).astype(bool)
        else:
            df['neutral_site'] = False
        
        # Create game identifier
        df['game_key'] = df.apply(
            lambda row: f"{row['season']}_{row.get('week', 'unknown')}_{row['away_team']}_{row['home_team']}",
            axis=1
        )
        
        logger.info(f"  ✅ Loaded {len(df)} games from {file_path}")
        logger.info(f"  ✅ Week: {week}, Season: {season}")
        
        return df
        
    except Exception as e:
        logger.error(f"❌ Error loading {file_path}: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()


def load_prediction_tracker(week: Optional[int] = None, season: int = 2025,
                            file_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load Prediction_Tracker data for specified week/season.
    
    Args:
        week: Week number (if None, searches for any available file)
        season: Season year (default 2025)
        file_path: Optional explicit file path
    
    Returns:
        DataFrame with normalized Prediction_Tracker data
    """
    if file_path:
        return load_prediction_tracker_file(file_path, week, season)
    
    # Search for Prediction_Tracker files
    search_paths = [
        project_root / f"Prediction_Tracker_week{week}.csv" if week else None,
        project_root / f"Prediction_Tracker_week{week:02d}.csv" if week else None,
        project_root / "Prediction_Tracker_week13.csv",  # Default fallback
        project_root / "Prediction_Tracker*.csv",
    ]
    
    # Also search in data directory
    data_dir = project_root / "data"
    if data_dir.exists():
        search_paths.extend([
            data_dir / f"Prediction_Tracker_week{week}.csv" if week else None,
            data_dir / f"Prediction_Tracker_week{week:02d}.csv" if week else None,
            data_dir / "Prediction_Tracker*.csv",
        ])
    
    for search_path in search_paths:
        if search_path is None:
            continue
        
        if '*' in str(search_path):
            # Glob pattern
            matches = list(project_root.glob("Prediction_Tracker*.csv"))
            if matches:
                # Use most recent file if multiple matches
                search_path = max(matches, key=lambda p: p.stat().st_mtime)
            else:
                continue
        
        if search_path.exists():
            return load_prediction_tracker_file(search_path, week, season)
    
    logger.warning(f"⚠️  No Prediction_Tracker file found for week {week}, season {season}")
    return pd.DataFrame()


def load_multiple_weeks(weeks: List[int], season: int = 2025) -> pd.DataFrame:
    """
    Load Prediction_Tracker data for multiple weeks.
    
    Args:
        weeks: List of week numbers
        season: Season year (default 2025)
    
    Returns:
        Combined DataFrame with all weeks
    """
    all_data = []
    
    for week in weeks:
        df = load_prediction_tracker(week=week, season=season)
        if not df.empty:
            all_data.append(df)
    
    if not all_data:
        logger.warning(f"⚠️  No data loaded for weeks {weeks}")
        return pd.DataFrame()
    
    combined = pd.concat(all_data, ignore_index=True)
    logger.info(f"✅ Loaded {len(combined)} total games from {len(all_data)} weeks")
    
    return combined


def get_system_predictions(df: pd.DataFrame, system_name: str) -> pd.Series:
    """
    Extract predictions for a specific system.
    
    Args:
        df: Prediction_Tracker DataFrame
        system_name: Name of system ('system_average', 'opening_line', 'sagarin', etc.)
    
    Returns:
        Series with predictions (NaN for missing)
    """
    if system_name in df.columns:
        return df[system_name]
    else:
        logger.warning(f"⚠️  System '{system_name}' not found in DataFrame")
        return pd.Series([np.nan] * len(df), index=df.index)


def main():
    """Main execution function for testing."""
    logger.info("=" * 80)
    logger.info("PREDICTION_TRACKER DATA LOADER")
    logger.info("=" * 80)
    
    # Test loading Week 13
    df = load_prediction_tracker(week=13, season=2025)
    
    if df.empty:
        logger.error("❌ No data loaded")
        return 1
    
    logger.info(f"\n✅ Loaded {len(df)} games")
    logger.info(f"\nColumns: {list(df.columns)}")
    logger.info(f"\nSample data:")
    print(df[['home_team', 'away_team', 'system_average', 'opening_line', 'sagarin', 'week']].head(10))
    
    # Check system coverage
    systems = ['system_average', 'opening_line', 'sagarin', 'big_200', 'fpi']
    logger.info(f"\nSystem Coverage:")
    for system in systems:
        if system in df.columns:
            coverage = df[system].notna().sum()
            logger.info(f"  {system}: {coverage}/{len(df)} ({coverage/len(df)*100:.1f}%)")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

