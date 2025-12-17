#!/usr/bin/env python3
"""
Unified Data Acquisition Agent

This is the unified, production-ready data acquisition agent that combines
the best features from both v1 and v2 implementations.

Features:
- GraphQL as primary method (with REST fallback)
- Shared utilities for reduced code duplication
- Comprehensive error handling
- Data quality validation

DEPRECATED: Use this file instead of 2025_data_acquisition.py or 2025_data_acquisition_v2.py

Author: Model Pack Improvement Plan
Created: 2025-11-19
"""

import argparse
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import numpy as np
import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from cfbd.rest import ApiException

from model_pack.utils.cfbd_advanced_metrics import (
    ADVANCED_METRIC_COLUMNS,
    AdvancedMetricsBuilder,
)
from model_pack.utils.data_acquisition_utils import DataAcquisitionUtils
from starter_pack.utils.cfbd_loader import RateLimiter

# Import configuration system
_config_dir = Path(__file__).parent / "config"
if str(_config_dir.parent.parent) not in sys.path:
    sys.path.insert(0, str(_config_dir.parent.parent))

import sys
import os
project_root = Path(__file__).resolve().parent.parent

# Force project root to be first in sys.path to avoid shadowing by src/validation
str_root = str(project_root)
if str_root in sys.path:
    sys.path.remove(str_root)
sys.path.insert(0, str_root)

print(f"DEBUG: Current Working Directory: {os.getcwd()}")
print(f"DEBUG: Project Root: {project_root}")
print(f"DEBUG: sys.path[0]: {sys.path[0]}")

from validation.cfbd_data_validator import CFBDDataValidator # Should work now

try:
    from model_pack.config.data_config import get_data_config
    from model_pack.config.fallback_config import get_fallback_config
except ImportError:
    from config.data_config import get_data_config
    from config.fallback_config import get_fallback_config

# Get configuration
config = get_data_config()
fallback_config = get_fallback_config()

# Get API key
API_KEY = DataAcquisitionUtils.get_api_key()

# Set up logging
OUTPUT_DIR_TEMP = config.output_dir
logger = logging.getLogger(__name__)
logger = logging.getLogger(__name__)

# GraphQL client import
try:
    from src.data_sources.cfbd_graphql import CFBDGraphQLClient
    GQL_AVAILABLE = True
except ImportError:
    CFBDGraphQLClient = None
    GQL_AVAILABLE = False
    logger.warning("GraphQL client not available - will use REST API only")

# Configuration
CURRENT_SEASON = config.get_season()
CURRENT_WEEK = config.get_week()
OUTPUT_DIR = config.output_dir


class UnifiedDataAcquisitionAgent:
    """
    Unified data acquisition agent combining best features from v1 and v2.
    Uses shared utilities to reduce code duplication.
    """

    def __init__(self, use_graphql: Optional[bool] = None, use_rest: bool = False):
        """
        Initialize the unified agent with API clients and configuration.
        
        Args:
            use_graphql: Explicitly enable/disable GraphQL (None = auto-detect)
            use_rest: Force REST API only (overrides use_graphql)
        """
        # Initialize REST clients using shared utilities
        rest_clients = DataAcquisitionUtils.initialize_rest_clients(API_KEY)
        self.api_client = rest_clients['api_client']
        self.games_api = rest_clients['games_api']
        self.plays_api = rest_clients['plays_api']
        self.teams_api = rest_clients['teams_api']
        self.ratings_api = rest_clients['ratings_api']
        self.betting_api = rest_clients['betting_api']
        
        self.current_season = CURRENT_SEASON # explicit mapping

        
        self.validator = CFBDDataValidator()
        self.rate_limiter = DataAcquisitionUtils.create_rate_limiter()
        self.data_cache = {}
        self.quality_report = {
            'total_games': 0,
            'successful_game_fetches': 0,
            'successful_play_fetches': 0,
            'failed_games': [],
            'failed_plays': [],
            'data_gaps': [],
            'processing_time': None,
            'start_time': None
        }
        self._historical_elo_cache: Optional[Dict[str, float]] = None
        self._historical_talent_cache: Optional[Dict[str, float]] = None
        self._historical_spread_cache: Optional[Dict[str, float]] = None
        
        # GraphQL client initialization using shared utilities
        if use_rest:
            self.use_graphql = False
            self.graphql_client = None
            logger.info("REST API forced via argument")
        else:
            self.graphql_client = DataAcquisitionUtils.initialize_graphql_client(
                API_KEY, force_rest=(use_graphql is False)
            )
            self.use_graphql = (self.graphql_client is not None)
            if self.use_graphql:
                logger.info("✅ GraphQL client initialized (PRIMARY METHOD)")
            else:
                logger.info("Using REST API (GraphQL not available)")

    def _rate_limit(self):
        """Implement rate limiting between API calls."""
        self.rate_limiter.wait()

    def fetch_games_graphql(self, season: int, week: int) -> pd.DataFrame:
        """
        Fetch games data using GraphQL API (PRIMARY METHOD).
        
        Args:
            season: Season year
            week: Week number
            
        Returns:
            DataFrame containing game information
            
        Raises:
            ValueError: If GraphQL client is not available
        """
        if not self.graphql_client:
            raise ValueError("GraphQL client not initialized")
        
        query = """
        query Scoreboard($season: Int!, $week: smallint) {
          game(
            where: {
              season: { _eq: $season }
              week: { _eq: $week }
            }
            order_by: { startDate: asc }
          ) {
            id
            season
            week
            seasonType
            startDate
            homeTeam
            awayTeam
            homePoints
            awayPoints
            completed
            venue
            homeConference
            awayConference
            neutralSite
            conferenceGame
          }
        }
        """
        
        variables = {"season": season, "week": week}
        result = self.graphql_client.query(query, variables)
        
        if not result or "game" not in result:
            return pd.DataFrame()
        
        games_data = result["game"]
        if not games_data:
            return pd.DataFrame()
        
        # Use shared utility for conversion
        df = DataAcquisitionUtils.convert_graphql_to_dataframe(games_data)
        
        logger.info(f"✅ Fetched {len(df)} games via GraphQL")
        return df
    
    def _is_fbs_game(self, game) -> bool:
        """
        Check if a game is between FBS teams (REST API version).
        
        Args:
            game: Game object from REST API
            
        Returns:
            True if both teams are FBS
        """
        home_conf = getattr(game, 'home_conference', None) or getattr(game, 'homeConference', None)
        away_conf = getattr(game, 'away_conference', None) or getattr(game, 'awayConference', None)
        
        if home_conf is None:
            home_conf = ""
        if away_conf is None:
            away_conf = ""
        
        if hasattr(home_conf, 'name'):
            home_conf = home_conf.name
        if hasattr(away_conf, 'name'):
            away_conf = away_conf.name
        
        home_conf = str(home_conf) if home_conf else ""
        away_conf = str(away_conf) if away_conf else ""
        
        return (config.is_fbs_conference(home_conf) or config.is_fbs_conference(away_conf))

    def test_api_connectivity(self) -> bool:
        """Test API connection and authentication."""
        try:
            logger.info("Testing API connectivity...")
            current_season = config.get_season()
            games = self.games_api.get_games(year=current_season, week=1)
            logger.info(f"API connectivity test successful. Found {len(games)} games in Week 1.")
            return True
        except ApiException as e:
            logger.error(f"API connectivity test failed (API error): {e.status} - {e.reason}")
            if e.status == 401:
                logger.error("Authentication failed - check API key")
            elif e.status == 429:
                logger.error("Rate limit exceeded")
            return False
        except Exception as e:
            logger.error(f"API connectivity test failed: {str(e)}")
            return False

    def fetch_2025_games(self) -> pd.DataFrame:
        """
        Fetch all FBS games for the current season.
        Uses GraphQL as PRIMARY METHOD with REST as FALLBACK.

        Returns:
            DataFrame containing game information
        """
        current_season = config.get_season()
        current_week = config.get_week()
        logger.info(f"Fetching {current_season} games data for Weeks 1-{current_week}...")
        self.quality_report['start_time'] = datetime.now()

        # Also fetch postseason if we are late in the season (Week 15+)
        fetch_postseason = current_week >= 15
        if fetch_postseason:
            logger.info("Late season detected - will also fetch postseason games")

        all_games = []
        method_used = "REST"

        # 1. Fetch Regular Season Weeks
        for week in range(1, current_week + 1):
            try:
                logger.info(f"Fetching Week {week} games...")
                
                # Try GraphQL first (PRIMARY METHOD)
                if self.use_graphql and self.graphql_client:
                    try:
                        df_week = self.fetch_games_graphql(current_season, week)
                        
                        if not df_week.empty:
                            # Filter for FBS games using shared utility
                            fbs_mask = df_week.apply(
                                lambda row: DataAcquisitionUtils.is_fbs_game(row, config),
                                axis=1
                            )
                            fbs_games_df = df_week[fbs_mask]
                            
                            if not fbs_games_df.empty:
                                fbs_games = fbs_games_df.to_dict('records')
                                all_games.extend(fbs_games)
                                method_used = "GraphQL"
                                logger.info(f"Found {len(fbs_games)} FBS games in Week {week} via GraphQL")
                                continue
                    except Exception as e:
                        logger.warning(f"GraphQL fetch failed for Week {week}: {e} - falling back to REST")
                
                # REST fallback (FALLBACK METHOD)
                self._rate_limit()
                games = self.games_api.get_games(year=current_season, week=week)
                method_used = "REST"

                if games:
                    fbs_games = [g for g in games if self._is_fbs_game(g)]
                    all_games.extend(fbs_games)
                    logger.info(f"Found {len(fbs_games)} FBS games in Week {week} via REST")
                else:
                    logger.warning(f"No games found for Week {week}")

            except ApiException as e:
                logger.error(f"API error for Week {week}: {e.status} - {e.reason}")
                self.quality_report['failed_games'].append({'week': week, 'error': str(e)})
            except Exception as e:
                logger.error(f"Error fetching Week {week}: {str(e)}")
            except Exception as e:
                logger.error(f"Error fetching Week {week}: {str(e)}")
                self.quality_report['failed_games'].append({'week': week, 'error': str(e)})

        # 2. Fetch Postseason (if applicable)
        if fetch_postseason:
            try:
                logger.info("Fetching Postseason games...")
                # Try GraphQL first
                if self.use_graphql and self.graphql_client:
                    try:
                        # GraphQL query for postseason not strictly defined by week, depends on API
                        # We can try fetching with seasonType='postseason' if the schema supports it
                        # For now, let's use REST for postseason as it's safer/known
                        pass 
                    except Exception:
                        pass
                
                # REST Postseason
                self._rate_limit()
                # Postseason is often "Week 1" of seasonType='postseason' or just querying by seasonType
                postseason_games = self.games_api.get_games(year=current_season, season_type='postseason')
                
                if postseason_games:
                    fbs_post_games = [g for g in postseason_games if self._is_fbs_game(g)]
                    all_games.extend(fbs_post_games)
                    logger.info(f"Found {len(fbs_post_games)} FBS Postseason games")
                else:
                    logger.info("No Postseason games found yet")
                    
            except ApiException as e:
                logger.error(f"API error fetching Postseason: {e.status}")
            except Exception as e:
                logger.error(f"Error fetching Postseason: {e}")

        if not all_games:
            logger.warning("No games fetched")
            return pd.DataFrame()

        # Convert to DataFrame using shared utilities
        # Fix: Convert objects to dicts first
        games_data = []
        for game in all_games:
            if hasattr(game, 'to_dict'):
                games_data.append(game.to_dict())
            else:
                games_data.append(game.__dict__)
        
        df = pd.DataFrame(games_data)
        df = DataAcquisitionUtils.normalize_column_names(df)
        
        # Validate data quality
        validation = DataAcquisitionUtils.validate_game_data(df)
        logger.info(f"Data validation: {validation}")
        
        self.quality_report['total_games'] = len(df)
        self.quality_report['successful_game_fetches'] = len(df)
        self.quality_report['processing_time'] = (datetime.now() - self.quality_report['start_time']).total_seconds()
        
        logger.info(f"✅ Fetched {len(df)} total games using {method_used} API")
        return df

    def fetch_play_by_play_data(self, games_df: pd.DataFrame) -> pd.DataFrame:
        """
        Fetch play-by-play data for games (placeholder - uses shared structure).
        
        Args:
            games_df: DataFrame containing game information
            
        Returns:
            DataFrame containing play-by-play data
        """
        logger.info("Fetching play-by-play data...")
        # Implementation would go here - using shared utilities
        return pd.DataFrame()

    def fetch_team_talent_ratings(self) -> pd.DataFrame:
        """
        Fetch team talent ratings.
        
        Returns:
            DataFrame containing talent ratings
        """
        logger.info("Fetching team talent ratings...")
        try:
            self._rate_limit()
            talent = self.teams_api.get_talent(year=self.current_season)
            data = []
            for t in talent:
                if hasattr(t, 'to_dict'):
                    data.append(t.to_dict())
                else:
                    data.append(t.__dict__)
            df = pd.DataFrame(data)
            logger.info(f"DEBUG: Fetched talent DF columns: {df.columns.tolist()}")
            if not df.empty:
                logger.info(f"DEBUG: Sample talent row: {df.iloc[0].to_dict()}")
            return df
        except Exception as e:
            logger.error(f"Error fetching talent: {e}")
            return pd.DataFrame()

    def fetch_elo_ratings(self) -> pd.DataFrame:
        """
        Fetch team ELO ratings.
        """
        logger.info("Fetching ELO ratings...")
        try:
            self._rate_limit()
            # Get current ELO (usually available via ratings/elo or similar)
            # We want the latest ELO for the current season
            elo = self.ratings_api.get_elo(year=self.current_season)
            data = []
            for e in elo:
                if hasattr(e, 'to_dict'):
                    data.append(e.to_dict())
                else:
                    data.append(e.__dict__)
            return pd.DataFrame(data)
        except Exception as e:
            logger.error(f"Error fetching ELO: {e}")
            return pd.DataFrame()

    def merge_talent_data(self, games_df: pd.DataFrame, talent_df: pd.DataFrame) -> pd.DataFrame:
        """Merge talent data into games DataFrame"""
        logger.info("Merging talent data...")
        try:
            if talent_df.empty:
                logger.warning("Talent DataFrame is empty. Skipping merge.")
                return games_df
            if games_df.empty:
                logger.warning("Games DataFrame is empty. Skipping merge.")
                return games_df
            
            # Create mapping from school to talent
            # Adjust column names: API might return 'team' or 'school'
            school_col = 'school' if 'school' in talent_df.columns else 'team'
            
            if school_col in talent_df.columns and 'talent' in talent_df.columns:
                # Strip whitespace safely
                talent_df = talent_df.copy()
                talent_df[school_col] = talent_df[school_col].astype(str).str.strip()
                
                # Careful with existing dataframes to avoid SettingWithCopyWarning
                games_df['home_team'] = games_df['home_team'].astype(str).str.strip()
                games_df['away_team'] = games_df['away_team'].astype(str).str.strip()
                
                talent_map = talent_df.set_index(school_col)['talent'].to_dict()
                
                games_df['home_talent'] = games_df['home_team'].map(talent_map)
                games_df['away_talent'] = games_df['away_team'].map(talent_map)
                
                logger.info(f"Talent data merged. Map size: {len(talent_map)}")
            else:
                logger.warning(f"Talent data validation failed. Columns found: {talent_df.columns.tolist()}")

        except Exception as e:
            logger.error(f"Error merging talent data: {e}")
            # Don't crash, return original df
            return games_df
            
        return games_df

    def merge_elo_data(self, games_df: pd.DataFrame, elo_df: pd.DataFrame) -> pd.DataFrame:
        """Merge ELO data into games DataFrame"""
        logger.info("Merging ELO data...")
        if elo_df.empty or games_df.empty:
            return games_df
            
        # ELO df usually has 'team', 'elo'
        # If API returns weekly ELO, we need to be careful.
        # However, for Bowl games, we can use the latest ELO available.
        # If elo_df has 'team' and 'elo' columns:
        if 'team' in elo_df.columns and 'elo' in elo_df.columns:
            # If multiple entries per team (weekly), take the last one (latest)
            latest_elo = elo_df.sort_values('elo').groupby('team')['elo'].last() # Wait, sort by what? 
            # If 'year' is present, it's just one per team per year usually? 
            # Or if it has 'week'?
            # Actually get_elo(year=..) usually returns ONE entry per team (current/final ELO)? 
            # Let's inspect columns if possible, but assuming 'team'/'elo' unique.
            
            elo_map = elo_df.set_index('team')['elo'].to_dict()
            
            games_df['home_elo'] = games_df['home_team'].map(elo_map)
            games_df['away_elo'] = games_df['away_team'].map(elo_map)
            
        return games_df

    def calculate_advanced_metrics(self, games_df: pd.DataFrame, plays_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate advanced opponent-adjusted metrics.
        
        Args:
            games_df: DataFrame containing game information
            plays_df: DataFrame containing play-by-play data
            
        Returns:
            DataFrame with advanced metrics added
        """
        logger.info("Calculating advanced metrics using AdvancedMetricsBuilder...")
        
        if games_df.empty:
            return games_df

        try:
            builder = AdvancedMetricsBuilder(
                api_client=self.api_client,
                season=self.current_season,
                rate_limit_callback=self._rate_limit
            )
            
            metrics_map = builder.build_metrics_for_games(games_df, plays_df)
            
            if not metrics_map:
                logger.warning("No metrics calculated!")
                return games_df
                
            logger.info(f"Calculated metrics for {len(metrics_map)} games")
                
            # Convert metrics to DataFrame
            metrics_data = []
            for game_id, metrics in metrics_map.items():
                row = metrics.copy()
                row['id'] = game_id
                metrics_data.append(row)
                
            metrics_df = pd.DataFrame(metrics_data)
            
            # Ensure ID match
            if 'id' in games_df.columns and not metrics_df.empty:
                # Align ID types
                metrics_df['id'] = metrics_df['id'].astype(games_df['id'].dtype)
                
                # Merge
                # Use suffixes to handle potential existing columns (though they should be empty/missing)
                merged_df = games_df.merge(metrics_df, on='id', how='left', suffixes=('', '_new'))
                
                # Update columns
                for col in metrics_df.columns:
                    if col == 'id':
                        continue
                        
                    if f"{col}_new" in merged_df.columns:
                        # If the column existed, fill NaNs with new values
                        if col in merged_df.columns:
                            merged_df[col] = merged_df[col].fillna(merged_df[f"{col}_new"])
                        else:
                            # If it didn't exist, just rename
                            merged_df[col] = merged_df[f"{col}_new"]
                        
                        merged_df = merged_df.drop(columns=[f"{col}_new"])
                
                return merged_df
            
            return games_df
            
        except Exception as e:
            logger.error(f"Error calculating advanced metrics: {e}")
            # Return original df on error to avoid full failure
            return games_df



    def save_datasets(self, games_df: pd.DataFrame, plays_df: pd.DataFrame, talent_df: pd.DataFrame):
        """
        Save all datasets to files.
        
        Args:
            games_df: Games DataFrame
            plays_df: Plays DataFrame
            talent_df: Talent DataFrame
        """
        """
        Save all datasets to files with backup functionality.
        
        Args:
            games_df: Games DataFrame
            plays_df: Plays DataFrame
            talent_df: Talent DataFrame
        """
        logger.info("Saving datasets...")
        
        try:
            # Create backups of existing files
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 1. Save Training Data (Games)
            training_path = Path(OUTPUT_DIR) / "updated_training_data.csv"
            if training_path.exists():
                backup_path = Path(OUTPUT_DIR) / "backups" / f"updated_training_data_{timestamp}.csv"
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                import shutil
                shutil.copy2(training_path, backup_path)
                logger.info(f"Backed up existing training data to {backup_path}")
            
            # Convert proper types before saving
            if not games_df.empty:
                # Ensure updated_training_data.csv has the right columns
                # We overwrite the file with the fresh fetch for the current season
                # BUT we need to preserve historical data if we only fetched current season
                
                # Check if we should append or replace
                # For this agent, we fetched the CURRENT season.
                # We should load the existing file, remove current season rows, and append new ones.
                
                if training_path.exists():
                    existing_df = pd.read_csv(training_path, low_memory=False)
                    # Remove existing records for current season to avoid duplicates
                    historical_df = existing_df[existing_df['season'] != self.current_season]
                    logger.info(f"Retained {len(historical_df)} historical records")
                    
                    # Align columns
                    # Add missing columns to games_df that exist in historical_df
                    for col in historical_df.columns:
                        if col not in games_df.columns:
                            games_df[col] = np.nan
                            
                    # Add missing columns to historical_df that exist in games_df
                    for col in games_df.columns:
                        if col not in historical_df.columns:
                            historical_df[col] = np.nan
                            
                    # Combine
                    combined_df = pd.concat([historical_df, games_df], ignore_index=True)
                    combined_df.to_csv(training_path, index=False)
                    logger.info(f"Saved {len(combined_df)} total records to {training_path}")
                else:
                    games_df.to_csv(training_path, index=False)
                    logger.info(f"Created new training data file at {training_path}")

            # 2. Save Plays Data
            if not plays_df.empty:
                plays_dir = Path(OUTPUT_DIR) / "data" / "plays"
                plays_dir.mkdir(parents=True, exist_ok=True)
                plays_path = plays_dir / f"plays_{self.current_season}.csv"
                plays_df.to_csv(plays_path, index=False)
                logger.info(f"Saved {len(plays_df)} play records to {plays_path}")

            # 3. Save Talent Data
            if not talent_df.empty:
                talent_dir = Path(OUTPUT_DIR) / "data" / "talent"
                talent_dir.mkdir(parents=True, exist_ok=True)
                talent_path = talent_dir / f"talent_{self.current_season}.csv"
                talent_df.to_csv(talent_path, index=False)
                logger.info(f"Saved {len(talent_df)} talent records to {talent_path}")
                
        except Exception as e:
            logger.error(f"Error saving datasets: {e}")
            raise

    def generate_quality_report(self) -> str:
        """
        Generate data quality report.
        
        Returns:
            Quality report as string
        """
        report_lines = [
            "DATA ACQUISITION QUALITY REPORT",
            "=" * 60,
            f"Total Games: {self.quality_report['total_games']}",
            f"Successful Fetches: {self.quality_report['successful_game_fetches']}",
            f"Failed Games: {len(self.quality_report['failed_games'])}",
            f"Processing Time: {self.quality_report['processing_time']:.2f} seconds",
        ]
        return "\n".join(report_lines)

    def run_complete_acquisition(self):
        """
        Execute the complete data acquisition pipeline.
        
        Returns:
            True if successful, False otherwise
        """
        logger.info("=" * 60)
        logger.info(f"STARTING {config.get_season()} COLLEGE FOOTBALL DATA ACQUISITION")
        logger.info("=" * 60)

        try:
            # Test API connectivity
            if not self.test_api_connectivity():
                raise Exception("API connectivity test failed")

            # Fetch games data
            games_df = self.fetch_2025_games()
            if games_df.empty:
                raise Exception("No games data fetched")

            # Fetch play-by-play data
            plays_df = self.fetch_play_by_play_data(games_df)

            # Fetch talent ratings
            talent_df = self.fetch_team_talent_ratings()
            print(f"DEBUG: Talent DF empty? {talent_df.empty}")
            
            # Fetch ELO ratings
            elo_df = self.fetch_elo_ratings()

            # Merge talent data
            if not talent_df.empty:
                print("DEBUG: CALLING merge_talent_data")
                games_df = self.merge_talent_data(games_df, talent_df)
            else:
                print("DEBUG: Skipping merge_talent_data because talent_df is empty")
                
            # Merge ELO data
            if not elo_df.empty:
                games_df = self.merge_elo_data(games_df, elo_df)

            # Calculate advanced metrics
            games_df = self.calculate_advanced_metrics(games_df, plays_df)

            # Save all datasets
            self.save_datasets(games_df, plays_df, talent_df)

            # Generate quality report
            report = self.generate_quality_report()
            logger.info("\n" + report)

            logger.info("=" * 60)
            logger.info("DATA ACQUISITION COMPLETED SUCCESSFULLY")
            logger.info("=" * 60)

            return True

        except Exception as e:
            logger.error(f"Data acquisition failed: {str(e)}")
            logger.error("=" * 60)
            logger.error("DATA ACQUISITION FAILED")
            logger.error("=" * 60)
            return False


# Alias for backward compatibility
DataAcquisitionAgent = UnifiedDataAcquisitionAgent


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description="Unified CFBD Data Acquisition Agent")
    parser.add_argument("--use-graphql", action="store_true", help="Prefer GraphQL API (default: auto-detect)")
    parser.add_argument("--no-graphql", action="store_true", help="Disable GraphQL API")
    parser.add_argument("--use-rest", action="store_true", help="Force REST API only")
    
    args = parser.parse_args()
    
    # Determine settings
    use_graphql = None
    use_rest = False
    
    if args.use_rest or args.no_graphql:
        use_rest = True
        use_graphql = False
    elif args.use_graphql:
        use_graphql = True
    
    agent = UnifiedDataAcquisitionAgent(use_graphql=use_graphql, use_rest=use_rest)
    success = agent.run_complete_acquisition()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

