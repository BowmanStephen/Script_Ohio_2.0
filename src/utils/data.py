#!/usr/bin/env python3
"""
Data Utilities - Helper functions for dynamic data retrieval
"""

import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)


def get_current_season() -> int:
    """Get current college football season based on date"""
    today = date.today()
    # College football season starts in August
    # If we're before August, we're still in previous season
    if today.month < 8:
        return today.year - 1
    return today.year


def calculate_current_week(season: int = None) -> int:
    """
    Calculate current week of college football season based on current date.
    
    College football season typically starts in late August (Week 1)
    and runs through early December (Week 15-16 for conference championships/bowls).
    
    Args:
        season: The season year (default: current season)
    
    Returns:
        Current week number (1-16), or 1 if before season start, or 16 if after season end
    """
    if season is None:
        season = get_current_season()
    
    today = date.today()
    
    # Season start: Late August (around August 24)
    season_start = date(season, 8, 24)
    
    # Season end: Early December (around December 7 for regular season)
    season_end = date(season, 12, 7)
    
    # If before season start, return 1
    if today < season_start:
        return 1
    
    # If after season end, return 16 (bowl season)
    if today > season_end:
        return 16
    
    # Calculate weeks since season start
    days_since_start = (today - season_start).days
    weeks_since_start = (days_since_start // 7) + 1
    
    # Clamp to valid range (1-16)
    current_week = max(1, min(weeks_since_start, 16))
    
    return current_week


def get_teams_from_data(csv_path: Optional[Path] = None, season: Optional[int] = None, 
                        limit: Optional[int] = None) -> List[str]:
    """
    Get list of teams from training data.
    
    Args:
        csv_path: Path to training data CSV (default: model_pack/updated_training_data.csv)
        season: Filter by season (default: current season)
        limit: Maximum number of teams to return (default: None = all)
    
    Returns:
        List of unique team names
    """
    if csv_path is None:
        # Try to find training data relative to this file
        base_path = Path(__file__).parent.parent.parent
        csv_path = base_path / "model_pack" / "updated_training_data.csv"
    
    if not csv_path.exists():
        logger.warning(f"⚠️ Training data not found at {csv_path}")
        # Return some common teams as fallback
        return ["Ohio State", "Michigan", "Alabama", "Georgia", "Texas", "USC", "Oregon", "Penn State"]
    
    try:
        df = pd.read_csv(csv_path)
        
        # Filter by season if provided
        if season is not None:
            df = df[df['season'] == season]
        else:
            # Use current season
            current_season = get_current_season()
            df = df[df['season'] == current_season]
        
        # Get unique teams from home and away
        home_teams = df['home_team'].unique().tolist() if 'home_team' in df.columns else []
        away_teams = df['away_team'].unique().tolist() if 'away_team' in df.columns else []
        
        # Combine and deduplicate
        teams = list(set(home_teams + away_teams))
        teams = [t for t in teams if pd.notna(t)]  # Remove NaN values
        teams.sort()  # Sort alphabetically
        
        # Limit if requested
        if limit is not None:
            teams = teams[:limit]
        
        logger.info(f"✅ Loaded {len(teams)} teams from training data")
        return teams
    
    except Exception as e:
        logger.error(f"❌ Error loading teams from data: {e}")
        # Return fallback teams
        return ["Ohio State", "Michigan", "Alabama", "Georgia", "Texas", "USC", "Oregon", "Penn State"]


def get_popular_matchups(csv_path: Optional[Path] = None, season: Optional[int] = None,
                         limit: int = 10) -> List[Tuple[str, str]]:
    """
    Get popular matchups (most frequent games) from training data.
    
    Args:
        csv_path: Path to training data CSV (default: model_pack/updated_training_data.csv)
        season: Filter by season (default: current season)
        limit: Maximum number of matchups to return (default: 10)
    
    Returns:
        List of (home_team, away_team) tuples
    """
    if csv_path is None:
        base_path = Path(__file__).parent.parent.parent
        csv_path = base_path / "model_pack" / "updated_training_data.csv"
    
    if not csv_path.exists():
        logger.warning(f"⚠️ Training data not found at {csv_path}")
        # Return some popular matchups as fallback
        return [
            ("Ohio State", "Michigan"),
            ("Alabama", "Auburn"),
            ("Texas", "Oklahoma"),
            ("USC", "UCLA"),
            ("Oregon", "Washington"),
        ]
    
    try:
        df = pd.read_csv(csv_path)
        
        # Filter by season if provided
        if season is not None:
            df = df[df['season'] == season]
        else:
            current_season = get_current_season()
            df = df[df['season'] == current_season]
        
        # Count matchup frequency
        if 'home_team' in df.columns and 'away_team' in df.columns:
            matchups = df.groupby(['home_team', 'away_team']).size().reset_index(name='count')
            matchups = matchups.sort_values('count', ascending=False)
            
            # Get top matchups
            top_matchups = matchups.head(limit)
            result = [(row['home_team'], row['away_team']) for _, row in top_matchups.iterrows()]
            
            logger.info(f"✅ Loaded {len(result)} popular matchups from training data")
            return result
    
    except Exception as e:
        logger.error(f"❌ Error loading popular matchups: {e}")
    
    # Return fallback matchups
    return [
        ("Ohio State", "Michigan"),
        ("Alabama", "Auburn"),
        ("Texas", "Oklahoma"),
        ("USC", "UCLA"),
        ("Oregon", "Washington"),
    ]


def get_sample_matchup(csv_path: Optional[Path] = None, season: Optional[int] = None) -> Tuple[str, str]:
    """
    Get a sample matchup from training data for demonstrations.
    
    Args:
        csv_path: Path to training data CSV (default: model_pack/updated_training_data.csv)
        season: Filter by season (default: current season)
    
    Returns:
        Tuple of (home_team, away_team)
    """
    matchups = get_popular_matchups(csv_path, season, limit=1)
    if matchups:
        return matchups[0]
    
    # Fallback
    return ("Ohio State", "Michigan")

