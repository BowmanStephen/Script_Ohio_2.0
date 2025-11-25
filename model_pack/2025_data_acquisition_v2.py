#!/usr/bin/env python3
"""
2025 College Football Data Acquisition Agent - Version 2
=========================================================

⚠️ DEPRECATED: This file is deprecated. Please use model_pack/data_acquisition_agent.py instead.

This script fetches complete 2025 college football data through Week 11
from the CollegeFootballData.com API and processes it for compatibility
with existing training_data.csv structure.

Author: Data Acquisition Agent
Date: November 7, 2025
Deprecated: November 19, 2025 - Use data_acquisition_agent.py instead
"""

import argparse
import logging
import os
import re
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

# Add project root to sys.path to allow importing model_pack as a package
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import cfbd
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from cfbd import ApiClient, BettingApi, Configuration, GamesApi, PlaysApi, RatingsApi, TeamsApi

# Load environment variables
load_dotenv()

from cfbd.rest import ApiException

from model_pack.utils.cfbd_advanced_metrics import (
    ADVANCED_METRIC_COLUMNS,
    AdvancedMetricsBuilder,
)
from starter_pack.utils.cfbd_loader import RateLimiter

# Import configuration system
_config_dir = Path(__file__).parent / "config"
# Ensure model_pack is in sys.path so absolute imports work
if str(_config_dir.parent.parent) not in sys.path:
    sys.path.insert(0, str(_config_dir.parent.parent))

# Add project root for validation module
project_root = _config_dir.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from validation.cfbd_data_validator import CFBDDataValidator
try:
    from model_pack.config.data_config import get_data_config
    from model_pack.config.fallback_config import get_fallback_config
except ImportError:
    # Fallback for when running from inside model_pack
    from config.data_config import get_data_config
    from config.fallback_config import get_fallback_config

# Get configuration (needed for OUTPUT_DIR before logging setup)
config_temp = get_data_config()
OUTPUT_DIR_TEMP = config_temp.output_dir

# Set up logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'{OUTPUT_DIR_TEMP}/data_acquisition.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# GraphQL client import
try:
    from src.data_sources.cfbd_graphql import CFBDGraphQLClient
    GQL_AVAILABLE = True
except ImportError:
    CFBDGraphQLClient = None
    GQL_AVAILABLE = False
    logger.warning("GraphQL client not available - will use REST API only")

# Get configuration
config = get_data_config()
fallback_config = get_fallback_config()

# Configuration
# Get API key from environment variable (NEVER hardcode)
API_KEY = os.environ.get("CFBD_API_KEY") or os.environ.get("CFBD_API_TOKEN")
if not API_KEY:
    raise ValueError("CFBD_API_KEY or CFBD_API_TOKEN environment variable required")

# Use dynamic configuration (kept for backward compatibility with existing code)
# Prefer using config.get_season() and config.get_week() directly in new code
CURRENT_SEASON = config.get_season()
CURRENT_WEEK = config.get_week()
OUTPUT_DIR = config.output_dir

class DataAcquisitionAgent:
    """
    Comprehensive data acquisition agent for 2025 college football season.
    """

    def __init__(self, use_graphql: Optional[bool] = None, use_rest: bool = False):
        """
        Initialize the agent with API client and configuration.
        
        Args:
            use_graphql: Explicitly enable/disable GraphQL (None = auto-detect)
            use_rest: Force REST API only (overrides use_graphql)
        """
        # Configure CFBD API (REST - FALLBACK)
        configuration = Configuration()
        configuration.access_token = API_KEY
        configuration.host = "https://api.collegefootballdata.com"
        self.api_client = ApiClient(configuration)
        self.games_api = GamesApi(self.api_client)
        self.plays_api = PlaysApi(self.api_client)
        self.teams_api = TeamsApi(self.api_client)
        self.ratings_api = RatingsApi(self.api_client)
        self.betting_api = BettingApi(self.api_client)
        
        self.validator = CFBDDataValidator()

        self.rate_limiter = RateLimiter()
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
        self._historical_elo_cache: Optional[Dict[str, float]] = None
        
        # GraphQL client initialization (PRIMARY METHOD)
        self.use_graphql = False
        self.graphql_client = None
        
        # Determine GraphQL usage based on args and availability
        should_try_graphql = False
        
        if use_rest:
            logger.info("REST API forced via CLI argument")
            should_try_graphql = False
        elif use_graphql is not None:
            should_try_graphql = use_graphql
            if use_graphql:
                logger.info("GraphQL explicitly requested via CLI argument")
            else:
                logger.info("GraphQL explicitly disabled via CLI argument")
        else:
            # Auto-detect (default behavior)
            should_try_graphql = GQL_AVAILABLE and CFBDGraphQLClient is not None

        if should_try_graphql:
            if not GQL_AVAILABLE or CFBDGraphQLClient is None:
                logger.warning("⚠️ GraphQL requested but client not available - falling back to REST")
                self.use_graphql = False
            else:
                try:
                    self.graphql_client = CFBDGraphQLClient(api_key=API_KEY, host="production")
                    # Test connectivity with simple query
                    connectivity_test = self.graphql_client.query("query { __typename }", {})
                    if connectivity_test:
                        self.use_graphql = True
                        logger.info("✅ GraphQL client initialized (PRIMARY METHOD)")
                    else:
                        logger.warning("⚠️ GraphQL connectivity test failed - using REST as fallback")
                        self.use_graphql = False
                except Exception as e:
                    logger.warning(f"⚠️ GraphQL client initialization failed: {e} - using REST as fallback")
                    self.use_graphql = False
                    self.graphql_client = None
        else:
            self.use_graphql = False
            self.graphql_client = None
            if not use_rest and not GQL_AVAILABLE:
                logger.warning("⚠️ GraphQL client not available - will use REST API only")

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
            Exception: If query fails
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
        
        # Convert to DataFrame
        df = self._convert_graphql_to_dataframe(games_data)
        
        logger.info(f"✅ Fetched {len(df)} games via GraphQL")
        return df
    
    def _convert_graphql_to_dataframe(self, records: list) -> pd.DataFrame:
        """
        Convert GraphQL records to DataFrame with proper column normalization.
        
        Args:
            records: List of game records from GraphQL
            
        Returns:
            Normalized DataFrame with snake_case columns
        """
        if not records:
            return pd.DataFrame()
        
        # Use json_normalize to flatten nested structures
        df = pd.json_normalize(records)
        
        # Column renaming dictionary (camelCase -> snake_case)
        column_mapping = {
            "homeTeam": "home_team",
            "awayTeam": "away_team",
            "homePoints": "home_points",
            "awayPoints": "away_points",
            "seasonType": "season_type",
            "startDate": "start_date",
            "homeConference": "home_conference",
            "awayConference": "away_conference",
            "neutralSite": "neutral_site",
            "conferenceGame": "conference_game"
        }
        
        # Rename columns
        df = df.rename(columns=column_mapping)
        
        # Convert start_date to datetime if present
        if "start_date" in df.columns:
            df["start_date"] = pd.to_datetime(df["start_date"], errors='coerce')
        
        return df
    
    def _is_fbs_game_from_df(self, row: pd.Series) -> bool:
        """
        Check if a game row is between FBS teams using DataFrame columns.
        
        Args:
            row: DataFrame row containing game information
            
        Returns:
            True if both teams are FBS, False otherwise
        """
        home_conf = row.get("home_conference") or row.get("homeConference")
        away_conf = row.get("away_conference") or row.get("awayConference")
        
        # Handle string or None values
        if home_conf is None or pd.isna(home_conf):
            home_conf = ""
        if away_conf is None or pd.isna(away_conf):
            away_conf = ""
        
        # Convert to string if needed
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
            # Try to fetch current season info
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
        Fetch all FBS games for the current season from Weeks 1 to current week.
        Uses GraphQL as PRIMARY METHOD with REST as FALLBACK.

        Returns:
            DataFrame containing game information
        """
        current_season = config.get_season()
        current_week = config.get_week()
        logger.info(f"Fetching {current_season} games data for Weeks 1-{current_week}...")
        self.quality_report['start_time'] = datetime.now()

        all_games = []
        method_used = "REST"  # Track which method was used

        for week in range(1, current_week + 1):
            try:
                logger.info(f"Fetching Week {week} games...")
                
                # Try GraphQL first (PRIMARY METHOD)
                if self.use_graphql and self.graphql_client:
                    try:
                        df_week = self.fetch_games_graphql(current_season, week)
                        
                        if not df_week.empty:
                            # Filter for FBS games using DataFrame method
                            fbs_mask = df_week.apply(self._is_fbs_game_from_df, axis=1)
                            fbs_games_df = df_week[fbs_mask]
                            
                            if not fbs_games_df.empty:
                                # Convert DataFrame to dict records for compatibility
                                fbs_games = fbs_games_df.to_dict('records')
                                all_games.extend(fbs_games)
                                method_used = "GraphQL"
                                logger.info(f"Found {len(fbs_games)} FBS games in Week {week} via GraphQL (PRIMARY)")
                                continue  # Success - skip REST fallback
                            else:
                                logger.warning(f"No FBS games found in Week {week} via GraphQL")
                    except Exception as e:
                        logger.warning(f"GraphQL fetch failed for Week {week}: {e} - falling back to REST")
                        # Fall through to REST fallback
                
                # REST fallback (FALLBACK METHOD)
                self._rate_limit()
                games = self.games_api.get_games(year=current_season, week=week)
                method_used = "REST"

                if games:
                    # Filter for FBS games only
                    fbs_games = [g for g in games if self._is_fbs_game(g)]
                    all_games.extend(fbs_games)
                    logger.info(f"Found {len(fbs_games)} FBS games in Week {week} via REST (FALLBACK)")
                else:
                    logger.warning(f"No games found for Week {week}")

            except ApiException as e:
                logger.error(f"API error fetching Week {week} games: {e.status} - {e.reason}")
                self.quality_report['failed_games'].append({'week': week, 'error': f"API {e.status}: {e.reason}"})
                if e.status == 429:
                    logger.warning("Rate limit exceeded - increasing delay")
                    time.sleep(1.0)  # Wait longer on rate limit
            except Exception as e:
                logger.error(f"Error fetching Week {week} games: {str(e)}")
                self.quality_report['failed_games'].append({'week': week, 'error': str(e)})

        logger.info(f"Total games fetched: {len(all_games)} (Method: {method_used})")
        self.quality_report['total_games'] = len(all_games)

        # Convert to DataFrame
        if all_games:
            # Fetch Elo, talent, and spreads once for all games
            elo_dict = self.fetch_elo_ratings(current_season)
            if not elo_dict:
                elo_dict = self.fetch_elo_ratings(current_season - 1)  # Fallback to previous year
            
            talent_df = self.fetch_team_talent_ratings()
            talent_dict = dict(zip(talent_df['team'], talent_df['talent'])) if not talent_df.empty else {}
            
            # Fetch spreads for all weeks
            spreads_dict = {}
            for week in range(1, current_week + 1):
                week_spreads = self.fetch_betting_lines(current_season, week)
                spreads_dict.update(week_spreads)
            
            # Store in instance for use in _process_games_dataframe
            self._elo_dict = elo_dict
            self._talent_dict = talent_dict
            self._spreads_dict = spreads_dict
            
        # Convert to DataFrame
        if all_games:
            games_df = self._process_games_dataframe(all_games)
            
            # Validate data
            validation_result = self.validator.validate_dataframe(games_df)
            if not validation_result.is_valid:
                logger.warning(f"Data validation issues: {validation_result.errors}")
                if validation_result.invalid_ranges:
                    logger.warning(f"Invalid ranges: {validation_result.invalid_ranges}")
                
                # Attempt fix
                games_df, fixed_result = self.validator.fix_data_issues(games_df)
                if not fixed_result.is_valid:
                    logger.error(f"Data validation failed after fix: {fixed_result.errors}")
                else:
                    logger.info("Data validation passed after automatic fixes")
            
            return games_df
        else:
            logger.error("No games were fetched successfully")
            return pd.DataFrame()

    def _is_fbs_game(self, game) -> bool:
        """Check if a game is between FBS teams."""
        # Use FBS conferences from configuration
        fbs_conferences = [
            'ACC', 'Big 12', 'Big Ten', 'SEC', 'Pac-12',
            'American Athletic', 'Conference USA', 'Mid-American', 'Mountain West', 'Sun Belt',
            'FBS Independents'
        ]
        # Handle conference as string or object
        home_conf = game.home_conference
        if hasattr(home_conf, 'name'):
            home_conf = home_conf.name
            
        away_conf = game.away_conference
        if hasattr(away_conf, 'name'):
            away_conf = away_conf.name

        return (config.is_fbs_conference(home_conf) or config.is_fbs_conference(away_conf))

    def _process_games_dataframe(self, games_list) -> pd.DataFrame:
        """Process raw games data to match training_data.csv structure."""
        logger.info("Processing games dataframe structure...")

        processed_data = []
        historical_elo = self._get_historical_elo_baseline()
        historical_talent = self._get_historical_talent_baseline()
        historical_spread = self._get_historical_spread_baseline()

        for game in games_list:
            try:
                # Handle both Game objects (REST) and dict records (GraphQL)
                is_dict = isinstance(game, dict)
                
                if is_dict:
                    # GraphQL path: game is already a dict
                    game_dict = game
                    game_id = game.get('id', '')
                    home_team = game.get('home_team', '')
                    away_team = game.get('away_team', '')
                    home_points = game.get('home_points')
                    away_points = game.get('away_points')
                    start_date = game.get('start_date', '')
                    season = game.get('season', config.get_season())
                    season_type = game.get('season_type', 'regular')
                    week = game.get('week', 0)
                    neutral_site = game.get('neutral_site', False)
                    home_conf = game.get('home_conference', '')
                    away_conf = game.get('away_conference', '')
                else:
                    # REST path: game is a Game object
                    game_dict = game.to_dict() if hasattr(game, 'to_dict') else {}
                    game_id = getattr(game, 'id', '')
                    home_team = getattr(game, 'home_team', '')
                    away_team = getattr(game, 'away_team', '')
                    home_points = getattr(game, 'home_points', None)
                    away_points = getattr(game, 'away_points', None)
                    start_date = getattr(game, 'start_date', '')
                    season = getattr(game, 'season', config.get_season())
                    season_type = getattr(game, 'season_type', 'regular')
                    week = getattr(game, 'week', 0)
                    neutral_site = getattr(game, 'neutral_site', False)
                    # Handle conference as object or string
                    home_conf_obj = getattr(game, 'home_conference', None)
                    home_conf = getattr(home_conf_obj, 'name', '') if home_conf_obj and hasattr(home_conf_obj, 'name') else str(home_conf_obj or '')
                    away_conf_obj = getattr(game, 'away_conference', None)
                    away_conf = getattr(away_conf_obj, 'name', '') if away_conf_obj and hasattr(away_conf_obj, 'name') else str(away_conf_obj or '')
                
                # Get Elo ratings (will be populated by caller with API data)
                # Use fallback values from configuration if not provided by caller
                home_elo = getattr(self, '_elo_dict', {}).get(home_team)
                away_elo = getattr(self, '_elo_dict', {}).get(away_team)

                if home_elo is None:
                    home_elo = historical_elo.get(home_team) or fallback_config.get_fallback_value('elo', home_team)
                if away_elo is None:
                    away_elo = historical_elo.get(away_team) or fallback_config.get_fallback_value('elo', away_team)
                
                # Get talent ratings (will be populated by caller with API data)
                home_talent = getattr(self, '_talent_dict', {}).get(home_team)
                away_talent = getattr(self, '_talent_dict', {}).get(away_team)

                if home_talent is None:
                    home_talent = historical_talent.get(home_team) or fallback_config.get_fallback_value('talent', home_team)
                if away_talent is None:
                    away_talent = historical_talent.get(away_team) or fallback_config.get_fallback_value('talent', away_team)
                
                # Get spread from betting lines (will be populated by caller)
                spread = None
                if getattr(self, '_spreads_dict', None) and game_id:
                    try:
                        spread = self._spreads_dict.get(int(game_id))
                    except (TypeError, ValueError):
                        spread = self._spreads_dict.get(game_id)

                if spread is None:
                    spread = self._extract_spread_from_game(game_dict)

                if spread is None:
                    spread = historical_spread.get(home_team, 0.0)
                
                # Handle missing/future points
                if home_points is not None and away_points is not None:
                    home_points = float(home_points)
                    away_points = float(away_points)
                    margin = home_points - away_points
                else:
                    home_points = np.nan
                    away_points = np.nan
                    margin = np.nan

                processed_game = {
                    'id': game_id,
                    'start_date': start_date,
                    'season': season,
                    'season_type': season_type,
                    'week': week,
                    'neutral_site': neutral_site,
                    'home_team': home_team,
                    'home_conference': home_conf,
                    'home_elo': home_elo,
                    'home_talent': home_talent,
                    'away_team': away_team,
                    'away_conference': away_conf,
                    'away_talent': away_talent,
                    'away_elo': away_elo,
                    'home_points': home_points,
                    'away_points': away_points,
                    'margin': margin,
                    'spread': spread
                }
                processed_data.append(processed_game)

            except Exception as e:
                game_id = game.get('id', 'unknown') if isinstance(game, dict) else getattr(game, 'id', 'unknown')
                logger.warning(f"Error processing game {game_id}: {str(e)}")
                continue

        processed_df = pd.DataFrame(processed_data)
        logger.info(f"Processed {len(processed_df)} games successfully")
        return processed_df

    def fetch_play_by_play_data(self, games_df: pd.DataFrame) -> pd.DataFrame:
        """
        Fetch play-by-play data for all completed games.

        Args:
            games_df: DataFrame containing game information

        Returns:
            DataFrame containing play-by-play data
        """
        logger.info("Fetching play-by-play data for completed games...")

        all_plays = []
        completed_games = games_df[
            (games_df['home_points'] > 0) | (games_df['away_points'] > 0)
        ]

        logger.info(f"Found {len(completed_games)} completed games for play-by-play data")

        for idx, game in completed_games.iterrows():
            try:
                logger.info(f"Fetching plays for game {game['id']} ({game['home_team']} vs {game['away_team']})")
                self._rate_limit()
                plays = self.plays_api.get_plays(game_id=game['id'])

                if plays:
                    for play in plays:
                        play_dict = self._object_to_dict(play)
                        play_data = {
                            'game_id': game['id'],
                            'play_id': play_dict.get('id', ''),
                            'period': play_dict.get('period', 0),
                            'clock': play_dict.get('clock', ''),
                            'yard_line': play_dict.get('yard_line', ''),
                            'down': play_dict.get('down'),
                            'distance': play_dict.get('distance'),
                            'play_type': play_dict.get('play_type') or play_dict.get('play_type_abbreviation', ''),
                            'play_type_id': play_dict.get('play_type_id'),
                            'scoring': play_dict.get('scoring', False),
                            'points': play_dict.get('points') or play_dict.get('play_points'),
                            'home_score': play_dict.get('home_score', 0),
                            'away_score': play_dict.get('away_score', 0),
                            'success': play_dict.get('success'),
                            'ppa': play_dict.get('ppa'),
                            'yards_gained': play_dict.get('yards_gained'),
                            'line_yards': play_dict.get('line_yards'),
                            'rush': play_dict.get('rush'),
                            'pass': play_dict.get('pass'),
                            'sack': play_dict.get('sack'),
                            'offense': play_dict.get('offense') or play_dict.get('offense_team', ''),
                            'defense': play_dict.get('defense') or play_dict.get('defense_team', ''),
                            'offense_conference': play_dict.get('offense_conference'),
                            'defense_conference': play_dict.get('defense_conference'),
                            'text': play_dict.get('text', ''),
                            'home_team': game['home_team'],
                            'away_team': game['away_team']
                        }
                        all_plays.append(play_data)

                    self.quality_report['successful_play_fetches'] += 1
                    logger.info(f"Fetched {len(plays)} plays for game {game['id']}")
                else:
                    logger.warning(f"No play data found for game {game['id']}")
                    self.quality_report['failed_plays'].append({
                        'game_id': game['id'],
                        'error': 'No play data available'
                    })

            except ApiException as e:
                logger.error(f"API error fetching plays for game {game['id']}: {e.status} - {e.reason}")
                self.quality_report['failed_plays'].append({
                    'game_id': game['id'],
                    'error': f"API {e.status}: {e.reason}"
                })
                if e.status == 429:
                    time.sleep(1.0)  # Wait longer on rate limit
            except Exception as e:
                logger.error(f"Error fetching plays for game {game['id']}: {str(e)}")
                self.quality_report['failed_plays'].append({
                    'game_id': game['id'],
                    'error': str(e)
                })

        logger.info(f"Total plays fetched: {len(all_plays)}")
        return pd.DataFrame(all_plays) if all_plays else pd.DataFrame()

    def fetch_team_talent_ratings(self) -> pd.DataFrame:
        """
        Fetch 2025 team talent ratings.

        Returns:
            DataFrame containing team talent information
        """
        logger.info(f"Fetching {config.get_season()} team talent ratings...")

        try:
            self._rate_limit()
            talent_data = self.teams_api.get_talent(year=config.get_season())

            if talent_data:
                processed_talent = []
                for talent in talent_data:
                    talent_dict = self._object_to_dict(talent)
                    team_name = talent_dict.get('team') or talent_dict.get('school') or talent_dict.get('name')
                    if not team_name:
                        continue
                    processed_talent.append({
                        'team': team_name,
                        'talent': talent_dict.get('talent', 0.0),
                        'season': config.get_season(),
                        'rank': talent_dict.get('rank', 0)
                    })

                if processed_talent:
                    self._talent_fetched = True
                    talent_df = pd.DataFrame(processed_talent)
                    logger.info(f"Fetched talent ratings for {len(talent_df)} teams")
                    return talent_df
                logger.warning("Talent API returned data but no teams parsed")
                self._talent_fetched = False
                return pd.DataFrame()
            else:
                self._talent_fetched = False
                logger.warning(f"No talent data available for {config.get_season()}")
                return pd.DataFrame()

        except ApiException as e:
            self._talent_fetched = False
            logger.error(f"API error fetching talent ratings: {e.status} - {e.reason}")
            if e.status == 429:
                logger.warning("Rate limit exceeded - increasing delay")
                time.sleep(1.0)
            return pd.DataFrame()
        except Exception as e:
            self._talent_fetched = False
            logger.error(f"Error fetching talent ratings: {str(e)}")
            return pd.DataFrame()

    def _get_historical_elo_baseline(self) -> Dict[str, float]:
        """
        Load historical Elo ratings from the existing training dataset as a fallback.
        """
        if self._historical_elo_cache is not None:
            return self._historical_elo_cache

        training_path = Path(OUTPUT_DIR) / "updated_training_data.csv"
        if not training_path.exists():
            logger.warning("Historical training data not found for Elo fallback")
            self._historical_elo_cache = {}
            return self._historical_elo_cache

        try:
            logger.info("Loading historical Elo baselines from updated_training_data.csv")
            hist_df = pd.read_csv(
                training_path,
                usecols=['home_team', 'away_team', 'home_elo', 'away_elo'],
                low_memory=False
            )

            frames = []
            if {'home_team', 'home_elo'}.issubset(hist_df.columns):
                home = hist_df[['home_team', 'home_elo']].dropna()
                home.columns = ['team', 'elo']
                frames.append(home)
            if {'away_team', 'away_elo'}.issubset(hist_df.columns):
                away = hist_df[['away_team', 'away_elo']].dropna()
                away.columns = ['team', 'elo']
                frames.append(away)

            if not frames:
                self._historical_elo_cache = {}
                return self._historical_elo_cache

            combined = pd.concat(frames, ignore_index=True)
            self._historical_elo_cache = combined.groupby('team')['elo'].median().to_dict()
            logger.info(f"Historical Elo baselines loaded for {len(self._historical_elo_cache)} teams")
        except Exception as exc:
            logger.error(f"Failed to load historical Elo baseline: {exc}")
            self._historical_elo_cache = {}

        return self._historical_elo_cache

    def _get_historical_talent_baseline(self) -> Dict[str, float]:
        """
        Load historical talent ratings from the existing training dataset as a fallback.
        """
        if self._historical_talent_cache is not None:
            return self._historical_talent_cache

        training_path = Path(OUTPUT_DIR) / "updated_training_data.csv"
        if not training_path.exists():
            logger.warning("Historical training data not found for talent fallback")
            self._historical_talent_cache = {}
            return self._historical_talent_cache

        try:
            logger.info("Loading historical talent baselines from updated_training_data.csv")
            hist_df = pd.read_csv(
                training_path,
                usecols=['home_team', 'away_team', 'home_talent', 'away_talent'],
                low_memory=False
            )

            frames = []
            if {'home_team', 'home_talent'}.issubset(hist_df.columns):
                home = hist_df[['home_team', 'home_talent']].dropna()
                home.columns = ['team', 'talent']
                frames.append(home)
            if {'away_team', 'away_talent'}.issubset(hist_df.columns):
                away = hist_df[['away_team', 'away_talent']].dropna()
                away.columns = ['team', 'talent']
                frames.append(away)

            if not frames:
                self._historical_talent_cache = {}
                return self._historical_talent_cache

            combined = pd.concat(frames, ignore_index=True)
            self._historical_talent_cache = combined.groupby('team')['talent'].median().to_dict()
            logger.info(f"Historical talent baselines loaded for {len(self._historical_talent_cache)} teams")
        except Exception as exc:
            logger.error(f"Failed to load historical talent baseline: {exc}")
            self._historical_talent_cache = {}

        return self._historical_talent_cache

    def _get_historical_spread_baseline(self) -> Dict[str, float]:
        """
        Load historical spreads (home team perspective) as fallback.
        """
        if self._historical_spread_cache is not None:
            return self._historical_spread_cache

        training_path = Path(OUTPUT_DIR) / "updated_training_data.csv"
        if not training_path.exists():
            logger.warning("Historical training data not found for spread fallback")
            self._historical_spread_cache = {}
            return self._historical_spread_cache

        try:
            logger.info("Loading historical spread baselines from updated_training_data.csv")
            hist_df = pd.read_csv(
                training_path,
                usecols=['home_team', 'spread'],
                low_memory=False
            ).dropna()

            if hist_df.empty:
                self._historical_spread_cache = {}
                return self._historical_spread_cache

            self._historical_spread_cache = hist_df.groupby('home_team')['spread'].median().to_dict()
            logger.info(f"Historical spread baselines loaded for {len(self._historical_spread_cache)} teams")
        except Exception as exc:
            logger.error(f"Failed to load historical spread baseline: {exc}")
            self._historical_spread_cache = {}

        return self._historical_spread_cache

    def _resolve_game_identifier(self, game_row: pd.Series) -> str:
        """Create a stable identifier for a game even if the API ID is missing."""
        game_id = game_row.get('id')
        if pd.notna(game_id) and game_id not in ('', None):
            return game_id
        season = game_row.get('season', config.get_season())
        week = game_row.get('week', 0)
        home = game_row.get('home_team', '')
        away = game_row.get('away_team', '')
        return f"{season}_{week}_{home}_{away}"

    def _extract_spread_from_game(self, game_dict: Dict[str, Any]) -> Optional[float]:
        """Attempt to extract spread information embedded within the raw game dict."""
        candidates = [
            game_dict.get('spread'),
            game_dict.get('formatted_spread'),
            game_dict.get('lines')
        ]

        for candidate in candidates:
            spread = self._parse_spread_value(candidate)
            if spread is not None:
                return spread
        return None

    def _parse_spread_value(self, value: Any) -> Optional[float]:
        """Normalize different spread representations to a float."""
        if value is None:
            return None

        if isinstance(value, (int, float)):
            return float(value)

        if isinstance(value, str):
            cleaned = value.strip()
            try:
                return float(cleaned)
            except ValueError:
                match = re.search(r'-?\d+\.?\d*', cleaned)
                if match:
                    try:
                        return float(match.group())
                    except ValueError:
                        return None
                return None

        if isinstance(value, dict):
            for key in ('spread', 'formatted_spread', 'value'):
                nested = self._parse_spread_value(value.get(key))
                if nested is not None:
                    return nested
            return None

        if isinstance(value, (list, tuple)):
            for item in value:
                nested = self._parse_spread_value(item)
                if nested is not None:
                    return nested
            return None

        return None

    @staticmethod
    def _object_to_dict(obj: Any) -> Dict[str, Any]:
        """Convert CFBD SDK objects to plain dicts for easier handling."""
        if isinstance(obj, dict):
            return obj
        to_dict = getattr(obj, "to_dict", None)
        if callable(to_dict):
            return to_dict()
        return {}

    def fetch_elo_ratings(self, year: Optional[int] = None) -> Dict[str, float]:
        """
        Fetch Elo ratings for teams from CFBD API.

        Args:
            year: Season year (default: current season from config)

        Returns:
            Dictionary mapping team names to Elo ratings
        """
        if year is None:
            year = config.get_season()
        logger.info(f"Fetching Elo ratings for {year}...")
        
        elo_dict = {}
        
        try:
            # Fetch most recent Elo ratings (use previous year if current year not available)
            self._rate_limit()
            elo_data = self.ratings_api.get_elo(year=year)
            
            if elo_data:
                # Process Elo data - get most recent rating for each team
                team_elo = {}
                for elo_entry in elo_data:
                    team = getattr(elo_entry, 'team', None) or getattr(elo_entry, 'school', None)
                    elo = getattr(elo_entry, 'elo', None) or getattr(elo_entry, 'rating', None)
                    week = getattr(elo_entry, 'week', None) or getattr(elo_entry, 'year', None)
                    
                    if team and elo:
                        # Keep most recent Elo for each team
                        if team not in team_elo or (week and team_elo[team].get('week', 0) < week):
                            team_elo[team] = {'elo': float(elo), 'week': week or 0}
                
                # Convert to simple dict
                elo_dict = {team: data['elo'] for team, data in team_elo.items()}
                logger.info(f"Fetched Elo ratings for {len(elo_dict)} teams")
            
            # Fallback: Try previous year if current year has no data
            if not elo_dict and year == config.get_season():
                logger.info(f"No Elo data for {year}, trying {year-1}...")
                return self.fetch_elo_ratings(year=year-1)
                
        except ApiException as e:
            logger.warning(f"API error fetching Elo ratings: {e.status} - {e.reason}")
            if e.status == 429:
                time.sleep(1.0)
        except Exception as e:
            logger.warning(f"Error fetching Elo ratings: {str(e)}")
        
        return elo_dict

    def fetch_betting_lines(self, year: int, week: int) -> Dict[int, float]:
        """
        Fetch betting lines/spreads for games.

        Args:
            year: Season year
            week: Week number

        Returns:
            Dictionary mapping game IDs to spreads
        """
        logger.info(f"Fetching betting lines for {year} Week {week}...")
        
        spreads_dict = {}
        
        try:
            self._rate_limit()
            lines = self.betting_api.get_lines(year=year, week=week)

            if not lines:
                return spreads_dict

            for raw_line in lines:
                line = self._object_to_dict(raw_line)
                game_id = line.get('game_id') or line.get('id')
                spread_value = self._parse_spread_value(line.get('spread') or line.get('formatted_spread'))

                line_entries = line.get('lines') or []
                if not spread_value and isinstance(line_entries, list):
                    consensus = next(
                        (entry for entry in line_entries if str(entry.get('provider', '')).lower() == 'consensus'),
                        None
                    )
                    target_entry = consensus or (line_entries[0] if line_entries else None)
                    if target_entry:
                        spread_value = self._parse_spread_value(
                            target_entry.get('spread') or target_entry.get('formatted_spread')
                        )

                if spread_value is None or game_id is None:
                    continue

                try:
                    spreads_dict[int(game_id)] = float(spread_value)
                except (TypeError, ValueError):
                    logger.debug("Could not coerce spread %s for game %s", spread_value, game_id)

            logger.info("Fetched betting lines for %d games (Week %s)", len(spreads_dict), week)

        except ApiException as e:
            logger.warning(f"API error fetching betting lines: {e.status} - {e.reason}")
            if e.status == 429:
                logger.warning("Betting lines rate limit exceeded; sleeping before retry")
                time.sleep(1.0)
        except Exception as e:
            logger.warning(f"Error fetching betting lines: {str(e)}")
        
        return spreads_dict

    def calculate_advanced_metrics(self, games_df: pd.DataFrame, plays_df: pd.DataFrame) -> pd.DataFrame:
        """
        Populate opponent-adjusted advanced metrics using real CFBD data.
        """
        logger.info("Calculating advanced metrics from CFBD Stats + play-by-play data...")

        builder = AdvancedMetricsBuilder(
            api_client=self.api_client,
            season=config.get_season(),
            rate_limit_callback=self._rate_limit,
        )
        advanced_metrics = builder.build_metrics_for_games(games_df, plays_df)

        for column in ADVANCED_METRIC_COLUMNS:
            if column not in games_df.columns:
                games_df[column] = np.nan

        populated_games = 0
        for idx, game in games_df.iterrows():
            game_id = self._resolve_game_identifier(game)
            metrics = advanced_metrics.get(game_id)
            if not metrics:
                continue
            for column, value in metrics.items():
                if column in games_df.columns:
                    games_df.at[idx, column] = value
            populated_games += 1

        logger.info("Advanced metrics populated for %d games before fallback", populated_games)

        historical_data_path = config.get_training_data_path()
        if historical_data_path.exists():
            try:
                historical_df = pd.read_csv(historical_data_path, low_memory=False)
                historical_pre_current = historical_df[historical_df['season'] < config.get_season()].copy()

                for col in ADVANCED_METRIC_COLUMNS:
                    if col in historical_pre_current.columns:
                        missing_count = games_df[col].isna().sum()
                        if missing_count > 0:
                            hist_mean = historical_pre_current[col].mean()
                            games_df[col].fillna(hist_mean, inplace=True)
                            logger.warning(
                                "Historical fallback used for %d rows of %s (mean=%.4f)",
                                missing_count,
                                col,
                                hist_mean if not np.isnan(hist_mean) else 0.0
                            )
                    else:
                        games_df[col].fillna(0.0, inplace=True)
            except Exception as exc:
                logger.warning(f"Could not load historical data for fallback: {exc}")
                for col in ADVANCED_METRIC_COLUMNS:
                    games_df[col].fillna(0.0, inplace=True)
        else:
            logger.warning("Historical data file not found - using 0.0 as fallback for missing metrics")
            for col in ADVANCED_METRIC_COLUMNS:
                games_df[col].fillna(0.0, inplace=True)

        logger.info("Advanced metrics pipeline complete (%d columns)", len(ADVANCED_METRIC_COLUMNS))
        return games_df

    def merge_talent_data(self, games_df: pd.DataFrame, talent_df: pd.DataFrame) -> pd.DataFrame:
        """
        Merge talent ratings into games data.

        Args:
            games_df: DataFrame containing game information
            talent_df: DataFrame containing talent ratings

        Returns:
            Enhanced games DataFrame with talent data
        """
        if talent_df.empty:
            logger.warning("No talent data available to merge")
            return games_df

        logger.info("Merging talent ratings into games data...")

        # Create talent lookup dictionary
        talent_dict = dict(zip(talent_df['team'], talent_df['talent']))

        # Map talent to home and away teams
        games_df['home_talent'] = games_df['home_team'].map(talent_dict)
        games_df['away_talent'] = games_df['away_team'].map(talent_dict)
        
        # Fetch missing talent from API instead of using 500.0 fallback
        missing_home = games_df[games_df['home_talent'].isna()]['home_team'].unique()
        missing_away = games_df[games_df['away_talent'].isna()]['away_team'].unique()
        missing_teams = set(missing_home) | set(missing_away)
        
        if missing_teams:
            logger.warning(
                "Talent missing for %d teams, attempting API fetch (%s)",
                len(missing_teams),
                ", ".join(sorted(missing_teams))[:200]
            )
            fetched_teams: Dict[str, int] = {}
            for season in (config.get_season(), config.get_season() - 1):
                for team in list(missing_teams):
                    if team in fetched_teams:
                        continue
                    try:
                        talent_data = self.teams_api.get_talent(year=season, team=team)
                        self._rate_limit()
                        if talent_data and len(talent_data) > 0:
                            record = self._object_to_dict(talent_data[0])
                            team_talent = record.get('talent')
                            if team_talent is not None:
                                talent_dict[team] = float(team_talent)
                                fetched_teams[team] = season
                                logger.info("Fetched talent %.1f for %s (%s)", float(team_talent), team, season)
                    except Exception as exc:
                        logger.debug("Could not fetch talent for %s (%s): %s", team, season, exc)
                missing_teams -= set(fetched_teams.keys())
                if not missing_teams:
                    break
            
            games_df['home_talent'] = games_df['home_team'].map(talent_dict)
            games_df['away_talent'] = games_df['away_team'].map(talent_dict)
            
            still_missing = games_df[games_df['home_talent'].isna() | games_df['away_talent'].isna()]
            if len(still_missing) > 0:
                missing_names = sorted(set(still_missing['home_team'].dropna().tolist() + still_missing['away_team'].dropna().tolist()))
                fallback_value = fallback_config.get_fallback_value('talent') or 500.0
                logger.warning(
                    "Using fallback %.1f for %d games with missing talent data (%s)",
                    fallback_value,
                    len(still_missing),
                    ", ".join(missing_names)[:200]
                )
                games_df['home_talent'].fillna(fallback_value, inplace=True)
                games_df['away_talent'].fillna(fallback_value, inplace=True)

        logger.info("Talent data merged successfully")
        return games_df

    def generate_quality_report(self) -> str:
        """
        Generate comprehensive data quality report.

        Returns:
            Formatted report string
        """
        end_time = datetime.now()
        processing_time = end_time - self.quality_report['start_time']

        report = f"""
{config.get_season()} COLLEGE FOOTBALL DATA ACQUISITION REPORT
============================================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Processing Time: {processing_time}

DATA SUMMARY:
- Season: {config.get_season()}
- Current Week: {config.get_week()}
- Total Games Targeted: {self.quality_report['total_games']}
- Successful Game Fetches: {self.quality_report['successful_game_fetches']}
- Successful Play Fetches: {self.quality_report['successful_play_fetches']}
- Failed Game Fetches: {len(self.quality_report['failed_games'])}
- Failed Play Fetches: {len(self.quality_report['failed_plays'])}

ERROR SUMMARY:
"""

        if self.quality_report['failed_games']:
            report += "Failed Game Fetches:\n"
            for failed in self.quality_report['failed_games']:
                report += f"  - Week {failed['week']}: {failed['error']}\n"

        if self.quality_report['failed_plays']:
            report += "Failed Play Fetches:\n"
            for failed in self.quality_report['failed_plays']:
                report += f"  - Game {failed['game_id']}: {failed['error']}\n"

        report += f"""
DATA COVERAGE:
- Weeks Covered: 1-{config.get_week()}
- FBS Games Only: Yes
- Play-by-Play Coverage: {self.quality_report['successful_play_fetches']} games
- Talent Ratings: {'Included' if 'talent_df' in locals() and not talent_df.empty else 'Not Available'}

RECOMMENDATIONS:
"""

        if len(self.quality_report['failed_games']) > 0:
            report += "- Investigate failed game fetches for data gaps\n"
        if len(self.quality_report['failed_plays']) > 0:
            report += "- Review play-by-play data availability for recent games\n"
        if self.quality_report['successful_play_fetches'] < self.quality_report['total_games']:
            report += "- Some games may not have complete play-by-play data\n"

        return report

    def save_datasets(self, games_df: pd.DataFrame, plays_df: pd.DataFrame, talent_df: pd.DataFrame):
        """
        Save all datasets to files.

        Args:
            games_df: Processed games data
            plays_df: Play-by-play data
            talent_df: Team talent data
        """
        logger.info("Saving datasets...")

        try:
            # Save games data
            games_file = config.get_output_path(f"{config.get_season()}_raw_games.csv")
            games_df.to_csv(games_file, index=False)
            logger.info(f"Saved games data: {games_file} ({len(games_df)} games)")

            # Save weekly training data files (for validation and model compatibility)
            project_root = Path(__file__).parent.parent
            for week in games_df['week'].unique():
                week_df = games_df[games_df['week'] == week].copy()
                if not week_df.empty:
                    # Save as training_data_2025_week{week}.csv in project root
                    # Ensure week is 2 digits
                    filename = f"training_data_{config.get_season()}_week{int(week):02d}.csv"
                    week_file = project_root / filename
                    week_df.to_csv(week_file, index=False)
                    logger.info(f"Saved weekly training data: {filename} ({len(week_df)} games)")

            # Save play-by-play data
            if not plays_df.empty:
                plays_file = config.get_output_path(f"{config.get_season()}_plays.csv")
                plays_df.to_csv(plays_file, index=False)
                logger.info(f"Saved play-by-play data: {plays_file} ({len(plays_df)} plays)")

            # Save talent data
            if not talent_df.empty:
                talent_file = config.get_output_path(f"{config.get_season()}_talent.csv")
                talent_df.to_csv(talent_file, index=False)
                logger.info(f"Saved talent data: {talent_file} ({len(talent_df)} teams)")

            # Generate and save quality report
            report = self.generate_quality_report()
            report_file = config.get_output_path(f"{config.get_season()}_data_quality_report.txt")
            with open(report_file, 'w') as f:
                f.write(report)
            logger.info(f"Saved quality report: {report_file}")

        except Exception as e:
            logger.error(f"Error saving datasets: {str(e)}")
            raise

    def run_complete_acquisition(self):
        """
        Execute the complete data acquisition pipeline.
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

            self.quality_report['successful_game_fetches'] = len(games_df)

            # Fetch play-by-play data
            plays_df = self.fetch_play_by_play_data(games_df)

            # Fetch talent ratings
            talent_df = self.fetch_team_talent_ratings()

            # Merge talent data
            if not talent_df.empty:
                games_df = self.merge_talent_data(games_df, talent_df)

            # Calculate advanced metrics (placeholder implementation)
            games_df = self.calculate_advanced_metrics(games_df, plays_df)

            # Save all datasets
            self.save_datasets(games_df, plays_df, talent_df)

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


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description="2025 CFBD Data Acquisition Agent")
    parser.add_argument("--use-graphql", action="store_true", help="Prefer GraphQL API (default: auto-detect)")
    parser.add_argument("--no-graphql", action="store_true", help="Disable GraphQL API")
    parser.add_argument("--use-rest", action="store_true", help="Force REST API only (same as --no-graphql)")
    
    args = parser.parse_args()
    
    # Determine settings
    use_graphql = None
    use_rest = False
    
    if args.use_rest or args.no_graphql:
        use_rest = True
        use_graphql = False
    elif args.use_graphql:
        use_graphql = True
    
    agent = DataAcquisitionAgent(use_graphql=use_graphql, use_rest=use_rest)
    success = agent.run_complete_acquisition()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
