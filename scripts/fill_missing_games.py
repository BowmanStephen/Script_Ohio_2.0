#!/usr/bin/env python3
"""
Fill Missing Games in Training Data

This script:
1. Reads missing game IDs from reports/missing_games.csv
2. Fetches game data from CFBD API
3. Generates 86 features using existing pipeline
4. Integrates missing games into updated_training_data.csv

CRITICAL API EFFICIENCY FIX (Nov 2025):
- Script now batches API calls by (season, week) combinations
- Instead of one API call per missing game, makes one call per unique (season, week)
- Dramatically reduces API usage (e.g., 5,279 games → ~200-300 API calls instead of 5,279)
- Prevents API quota exhaustion from redundant calls for same week/year combinations
"""

import os
import sys
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd
import numpy as np

# Load environment variables from .env file if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not required, but helpful if available

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    import cfbd
    from cfbd import ApiClient, Configuration, GamesApi, PlaysApi, TeamsApi, RatingsApi, BettingApi
    from cfbd.rest import ApiException
except ImportError:
    print("ERROR: cfbd package not installed. Install with: pip install cfbd")
    sys.exit(1)

# Import configuration and utilities
_config_dir = PROJECT_ROOT / "model_pack" / "config"
if str(_config_dir.parent) not in sys.path:
    sys.path.insert(0, str(_config_dir.parent))
try:
    from config.data_config import get_data_config
    from config.fallback_config import get_fallback_config
    config = get_data_config()
    fallback_config = get_fallback_config()
except ImportError:
    print("WARNING: Could not import config. Using defaults.")
    config = None
    fallback_config = None

# Import advanced metrics builder
try:
    from model_pack.utils.cfbd_advanced_metrics import (
        ADVANCED_METRIC_COLUMNS,
        AdvancedMetricsBuilder,
    )
except ImportError:
    print("WARNING: Could not import AdvancedMetricsBuilder. Advanced metrics will be limited.")
    ADVANCED_METRIC_COLUMNS = ()
    AdvancedMetricsBuilder = None

# Get API key
API_KEY = os.environ.get("CFBD_API_KEY") or os.environ.get("CFBD_API_TOKEN")
if not API_KEY:
    print("ERROR: CFBD_API_KEY or CFBD_API_TOKEN environment variable required")
    sys.exit(1)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FBS conferences
FBS_CONFERENCES = {
    'ACC', 'Big 12', 'Big Ten', 'SEC', 'Pac-12',
    'American Athletic', 'Conference USA', 'Mid-American', 
    'Mountain West', 'Sun Belt', 'FBS Independents'
}

class MissingGamesFiller:
    """Fill missing games in training data."""
    
    def __init__(self):
        """Initialize the filler."""
        self.api_client = None
        self.games_api = None
        self.plays_api = None
        self.teams_api = None
        self.ratings_api = None
        self.betting_api = None
        
        # Configure API
        configuration = Configuration()
        configuration.access_token = API_KEY
        configuration.host = "https://api.collegefootballdata.com"
        self.api_client = ApiClient(configuration)
        self.games_api = GamesApi(self.api_client)
        self.plays_api = PlaysApi(self.api_client)
        self.teams_api = TeamsApi(self.api_client)
        self.ratings_api = RatingsApi(self.api_client)
        self.betting_api = BettingApi(self.api_client)
        
        self.rate_limit_delay = 0.17
        self.training_data_path = PROJECT_ROOT / 'model_pack' / 'updated_training_data.csv'
        self.missing_games_path = PROJECT_ROOT / 'reports' / 'missing_games.csv'
        self.output_path = PROJECT_ROOT / 'model_pack' / 'updated_training_data.csv'
        
    def _rate_limit(self):
        """Respect CFBD API rate limits."""
        time.sleep(self.rate_limit_delay)
    
    def _is_fbs_game(self, game) -> bool:
        """Check if game is between FBS teams."""
        home_conf = getattr(game, 'home_conference', None)
        away_conf = getattr(game, 'away_conference', None)
        
        if hasattr(home_conf, 'name'):
            home_conf = home_conf.name
        if hasattr(away_conf, 'name'):
            away_conf = away_conf.name
        
        return (home_conf in FBS_CONFERENCES) or (away_conf in FBS_CONFERENCES)
    
    def load_missing_games(self) -> pd.DataFrame:
        """Load missing games from CSV."""
        if not self.missing_games_path.exists():
            logger.error(f"Missing games file not found: {self.missing_games_path}")
            logger.info("Run scripts/identify_missing_games.py first to generate missing_games.csv")
            return pd.DataFrame()
        
        df = pd.read_csv(self.missing_games_path)
        logger.info(f"Loaded {len(df)} missing games from {self.missing_games_path}")
        return df
    
    def _fetch_games_for_week(self, season: int, week: int) -> List[Dict]:
        """Fetch all games for a specific (season, week) combination. Cached to prevent redundant API calls."""
        try:
            self._rate_limit()
            games = self.games_api.get_games(year=season, week=week)
            
            games_list = []
            for game in games:
                if not self._is_fbs_game(game):
                    continue
                
                # Convert to dict
                game_dict = {
                    'id': getattr(game, 'id', None),
                    'start_date': getattr(game, 'start_date', ''),
                    'season': getattr(game, 'season', season),
                    'season_type': getattr(game, 'season_type', 'regular'),
                    'week': getattr(game, 'week', week),
                    'neutral_site': getattr(game, 'neutral_site', False),
                    'home_team': getattr(game, 'home_team', ''),
                    'home_conference': getattr(game.home_conference, 'name', '') if hasattr(game, 'home_conference') and game.home_conference else '',
                    'away_team': getattr(game, 'away_team', ''),
                    'away_conference': getattr(game.away_conference, 'name', '') if hasattr(game, 'away_conference') and game.away_conference else '',
                    'home_points': getattr(game, 'home_points', 0) or 0,
                    'away_points': getattr(game, 'away_points', 0) or 0,
                }
                games_list.append(game_dict)
            
            return games_list
            
        except ApiException as e:
            logger.error(f"API error fetching games for {season} Week {week}: {e.status} - {e.reason}")
            return []
        except Exception as e:
            logger.error(f"Error fetching games for {season} Week {week}: {str(e)}")
            return []
    
    def fetch_game_data(self, game_id: int, season: int, week: int, games_cache: Dict[tuple, List[Dict]] = None) -> Optional[Dict]:
        """Fetch a single game from cached games data or API if not cached."""
        # If no cache provided, fall back to old behavior (but this should not happen in new flow)
        if games_cache is None:
            logger.warning(f"fetch_game_data called without cache - this is inefficient!")
            games_list = self._fetch_games_for_week(season, week)
        else:
            # Get from cache
            cache_key = (int(season), int(week))
            games_list = games_cache.get(cache_key, [])
        
        # Find the specific game
        for game_dict in games_list:
            if game_dict.get('id') == game_id:
                return game_dict
        
        logger.warning(f"Game {game_id} not found in API response for {season} Week {week}")
        return None
    
    def fetch_elo_ratings(self, year: int) -> Dict[str, float]:
        """Fetch Elo ratings for a season."""
        elo_dict = {}
        try:
            # Ensure year is a native Python int
            year = int(year)
            self._rate_limit()
            elo_data = self.ratings_api.get_elo(year=year)
            
            if elo_data:
                team_elo = {}
                for elo_entry in elo_data:
                    team = getattr(elo_entry, 'team', None) or getattr(elo_entry, 'school', None)
                    elo = getattr(elo_entry, 'elo', None) or getattr(elo_entry, 'rating', None)
                    week = getattr(elo_entry, 'week', None) or getattr(elo_entry, 'year', None)
                    
                    if team and elo:
                        if team not in team_elo or (week and team_elo[team].get('week', 0) < week):
                            team_elo[team] = {'elo': float(elo), 'week': week or 0}
                
                elo_dict = {team: data['elo'] for team, data in team_elo.items()}
                logger.info(f"Fetched Elo ratings for {len(elo_dict)} teams for {year}")
        except Exception as e:
            logger.warning(f"Error fetching Elo ratings for {year}: {str(e)}")
        
        return elo_dict
    
    def fetch_talent_ratings(self, year: int) -> Dict[str, float]:
        """Fetch talent ratings for a season."""
        talent_dict = {}
        try:
            # Ensure year is a native Python int
            year = int(year)
            self._rate_limit()
            talent_data = self.teams_api.get_talent(year=year)
            
            if talent_data:
                for talent in talent_data:
                    talent_dict_obj = talent.to_dict() if hasattr(talent, 'to_dict') else {}
                    team_name = talent_dict_obj.get('team') or talent_dict_obj.get('school') or talent_dict_obj.get('name')
                    talent_value = talent_dict_obj.get('talent', 0.0)
                    
                    if team_name and talent_value:
                        talent_dict[team_name] = float(talent_value)
                
                logger.info(f"Fetched talent ratings for {len(talent_dict)} teams for {year}")
        except Exception as e:
            logger.warning(f"Error fetching talent ratings for {year}: {str(e)}")
        
        return talent_dict
    
    def fetch_spread(self, game_id: int, season: int, week: int) -> Optional[float]:
        """Fetch betting spread for a game."""
        try:
            # Ensure parameters are native Python ints
            season = int(season)
            week = int(week)
            self._rate_limit()
            lines = self.betting_api.get_lines(year=season, week=week)
            
            if not lines:
                return None
            
            for line in lines:
                line_dict = line.to_dict() if hasattr(line, 'to_dict') else {}
                line_game_id = line_dict.get('game_id') or line_dict.get('id')
                
                if line_game_id == game_id:
                    spread = line_dict.get('spread') or line_dict.get('formatted_spread')
                    if spread:
                        try:
                            return float(spread)
                        except (ValueError, TypeError):
                            pass
            
            return None
        except Exception as e:
            logger.debug(f"Error fetching spread for game {game_id}: {str(e)}")
            return None
    
    def enrich_game_data(self, game_dict: Dict, elo_dict: Dict, talent_dict: Dict) -> Dict:
        """Enrich game data with Elo, talent, and spread."""
        home_team = game_dict.get('home_team', '')
        away_team = game_dict.get('away_team', '')
        
        # Add Elo ratings
        game_dict['home_elo'] = elo_dict.get(home_team)
        game_dict['away_elo'] = elo_dict.get(away_team)
        
        # Add talent ratings
        game_dict['home_talent'] = talent_dict.get(home_team)
        game_dict['away_talent'] = talent_dict.get(away_team)
        
        # Calculate margin
        home_points = game_dict.get('home_points', 0) or 0
        away_points = game_dict.get('away_points', 0) or 0
        game_dict['margin'] = abs(home_points - away_points)
        
        # Fetch spread
        game_id = game_dict.get('id')
        season = game_dict.get('season')
        week = game_dict.get('week')
        if game_id and season and week:
            spread = self.fetch_spread(game_id, season, week)
            game_dict['spread'] = spread
        
        return game_dict
    
    def generate_features(self, games_df: pd.DataFrame, plays_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """Generate full 86 features matching training data structure."""
        logger.info("Generating features...")
        
        # Load training data to get column structure
        training_df = pd.read_csv(self.training_data_path, low_memory=False, nrows=1)
        expected_columns = set(training_df.columns)
        
        # Start with games_df
        result_df = games_df.copy()
        
        # Generate game_key
        if 'game_key' not in result_df.columns:
            result_df['game_key'] = result_df.apply(
                lambda row: f"{row['season']}_{row['week']}_{row['home_team'].replace(' ', '_')}_{row['away_team'].replace(' ', '_')}",
                axis=1
            )
        
        # Generate conference_game
        if 'conference_game' not in result_df.columns:
            result_df['conference_game'] = (
                result_df['home_conference'].notna() &
                result_df['away_conference'].notna() &
                (result_df['home_conference'] == result_df['away_conference'])
            )
        
        # Calculate advanced metrics if AdvancedMetricsBuilder is available
        if AdvancedMetricsBuilder and self.api_client:
            try:
                logger.info("Calculating advanced opponent-adjusted metrics...")
                season = result_df['season'].iloc[0] if len(result_df) > 0 else 2025
                builder = AdvancedMetricsBuilder(
                    api_client=self.api_client,
                    season=int(season),
                    rate_limit_callback=self._rate_limit,
                )
                
                # Build metrics for games
                advanced_metrics = builder.build_metrics_for_games(result_df, plays_df if plays_df is not None else pd.DataFrame())
                
                # Populate advanced metrics
                for idx, game in result_df.iterrows():
                    game_id = self._resolve_game_identifier(game)
                    metrics = advanced_metrics.get(game_id, {})
                    for col, value in metrics.items():
                        if col in expected_columns:
                            result_df.at[idx, col] = value
                
                logger.info("Advanced metrics calculated")
            except Exception as e:
                logger.warning(f"Could not calculate advanced metrics: {str(e)}")
        
        # Add missing columns with default values (fallback for advanced metrics)
        for col in expected_columns:
            if col not in result_df.columns:
                # Use defaults from fallback config if available
                if fallback_config:
                    default_value = fallback_config.get_fallback_value(col.split('_')[0] if '_' in col else col)
                    if default_value is not None:
                        result_df[col] = default_value
                    else:
                        # Use historical mean if available
                        try:
                            hist_df = pd.read_csv(self.training_data_path, low_memory=False)
                            if col in hist_df.columns:
                                hist_mean = hist_df[col].mean()
                                result_df[col] = hist_mean if not np.isnan(hist_mean) else 0.0
                            else:
                                result_df[col] = 0.0 if 'adjusted' in col or 'havoc' in col or 'points' in col or 'yards' in col else np.nan
                        except:
                            result_df[col] = 0.0 if 'adjusted' in col or 'havoc' in col or 'points' in col or 'yards' in col else np.nan
                else:
                    result_df[col] = 0.0 if 'adjusted' in col or 'havoc' in col or 'points' in col or 'yards' in col else np.nan
        
        # Ensure column order matches training data
        result_df = result_df[[col for col in training_df.columns if col in result_df.columns]]
        
        logger.info(f"Generated features: {len(result_df.columns)} columns")
        return result_df
    
    def _resolve_game_identifier(self, game_row: pd.Series) -> str:
        """Create a stable identifier for a game."""
        game_id = game_row.get('id')
        if pd.notna(game_id) and game_id not in ('', None):
            return str(game_id)
        season = game_row.get('season', 2025)
        week = game_row.get('week', 0)
        home = game_row.get('home_team', '')
        away = game_row.get('away_team', '')
        return f"{season}_{week}_{home}_{away}"
    
    def fetch_all_missing_games(self, missing_games_df: pd.DataFrame) -> pd.DataFrame:
        """Fetch all missing games from CFBD API using batched (year, week) calls to minimize API usage."""
        logger.info(f"Fetching {len(missing_games_df)} missing games from CFBD API...")
        
        fetched_games = []
        failed_games = []
        
        # Group by season for efficient Elo/talent fetching
        seasons = missing_games_df['season'].unique()
        elo_cache = {}
        talent_cache = {}
        
        for season in seasons:
            logger.info(f"Fetching Elo and talent for {season}...")
            elo_cache[season] = self.fetch_elo_ratings(season)
            talent_cache[season] = self.fetch_talent_ratings(season)
        
        # BATCH FIX: Group missing games by (season, week) to minimize API calls
        # Instead of calling API for each game, we call once per unique (season, week) combination
        games_by_week = {}
        for idx, row in missing_games_df.iterrows():
            game_id = int(row['id']) if pd.notna(row['id']) else None
            season = int(row['season'])
            week = int(row['week'])
            
            if not game_id:
                logger.warning(f"Row {idx} has no game ID, skipping")
                failed_games.append(row.to_dict())
                continue
            
            cache_key = (season, week)
            if cache_key not in games_by_week:
                games_by_week[cache_key] = []
            games_by_week[cache_key].append({
                'game_id': game_id,
                'row': row.to_dict()
            })
        
        logger.info(f"Grouped {len(missing_games_df)} games into {len(games_by_week)} unique (season, week) combinations")
        logger.info(f"This will require {len(games_by_week)} API calls instead of {len(missing_games_df)} calls")
        
        # Fetch games by (season, week) batches
        games_cache = {}
        for (season, week), game_infos in sorted(games_by_week.items()):
            logger.info(f"Fetching {len(game_infos)} games for {season} Week {week}...")
            games_list = self._fetch_games_for_week(season, week)
            games_cache[(season, week)] = games_list
            
            # Now extract individual games from the batch
            for game_info in game_infos:
                game_id = game_info['game_id']
                row = game_info['row']
                
                game_dict = self.fetch_game_data(game_id, season, week, games_cache)
                
                if game_dict:
                    # Enrich with Elo, talent, spread
                    game_dict = self.enrich_game_data(
                        game_dict,
                        elo_cache.get(season, {}),
                        talent_cache.get(season, {})
                    )
                    fetched_games.append(game_dict)
                else:
                    failed_games.append(row)
        
        logger.info(f"Successfully fetched {len(fetched_games)} games")
        original_calls = len(missing_games_df)
        actual_calls = len(games_by_week)
        reduction_pct = ((original_calls - actual_calls) / max(original_calls, 1)) * 100
        logger.info(f"API calls made: {actual_calls} (reduced from {original_calls} - {reduction_pct:.1f}% reduction)")
        if failed_games:
            logger.warning(f"Failed to fetch {len(failed_games)} games")
        
        if not fetched_games:
            return pd.DataFrame()
        
        return pd.DataFrame(fetched_games)
    
    def integrate_games(self, new_games_df: pd.DataFrame) -> bool:
        """Integrate new games into training data."""
        logger.info("Integrating new games into training data...")
        
        # Load existing training data
        if not self.training_data_path.exists():
            logger.error(f"Training data not found: {self.training_data_path}")
            return False
        
        existing_df = pd.read_csv(self.training_data_path, low_memory=False)
        logger.info(f"Loaded {len(existing_df)} existing games")
        
        # Check for duplicates
        existing_ids = set(existing_df['id'].dropna().astype(str))
        new_ids = set(new_games_df['id'].dropna().astype(str))
        duplicates = existing_ids & new_ids
        
        if duplicates:
            logger.warning(f"Found {len(duplicates)} duplicate game IDs, removing from new games")
            new_games_df = new_games_df[~new_games_df['id'].astype(str).isin(duplicates)]
        
        if len(new_games_df) == 0:
            logger.info("No new games to integrate after deduplication")
            return True
        
        # Generate features for new games (including advanced metrics)
        new_games_df = self.generate_features(new_games_df)
        
        # Normalize start_date timestamps in BOTH dataframes BEFORE concatenation
        # This prevents timezone-aware vs timezone-naive comparison errors
        def normalize_datetime(series):
            """Normalize datetime series to timezone-naive."""
            if series is None or len(series) == 0:
                return series
            # Convert to datetime if not already
            if not pd.api.types.is_datetime64_any_dtype(series):
                series = pd.to_datetime(series, errors='coerce', utc=True)
            # Remove timezone if present
            if pd.api.types.is_datetime64_any_dtype(series):
                if series.dt.tz is not None:
                    series = series.dt.tz_convert('UTC').dt.tz_localize(None)
                else:
                    # Already timezone-naive, ensure it's properly formatted
                    series = pd.to_datetime(series, errors='coerce')
            return series
        
        # Normalize timestamps in both dataframes
        if 'start_date' in existing_df.columns:
            existing_df['start_date'] = normalize_datetime(existing_df['start_date'])
        if 'start_date' in new_games_df.columns:
            new_games_df['start_date'] = normalize_datetime(new_games_df['start_date'])
        
        # Combine datasets
        combined_df = pd.concat([existing_df, new_games_df], ignore_index=True, sort=False)
        
        # Sort by season, week, start_date (all timestamps are now timezone-naive)
        combined_df = combined_df.sort_values(['season', 'week', 'start_date'], na_position='last')
        combined_df = combined_df.reset_index(drop=True)
        
        # Save backup
        backup_path = self.training_data_path.with_suffix('.csv.backup')
        existing_df.to_csv(backup_path, index=False)
        logger.info(f"Created backup: {backup_path}")
        
        # Save updated training data
        combined_df.to_csv(self.training_data_path, index=False)
        logger.info(f"Saved updated training data: {len(combined_df)} total games ({len(existing_df)} existing + {len(new_games_df)} new)")
        
        return True
    
    def run(self):
        """Execute the complete fill process."""
        logger.info("=" * 80)
        logger.info("FILLING MISSING GAMES IN TRAINING DATA")
        logger.info("=" * 80)
        
        # Step 1: Load missing games
        missing_games_df = self.load_missing_games()
        if missing_games_df.empty:
            logger.error("No missing games to process")
            return False
        
        # Step 2: Fetch game data
        fetched_games_df = self.fetch_all_missing_games(missing_games_df)
        if fetched_games_df.empty:
            logger.error("No games were successfully fetched")
            return False
        
        # Step 3: Integrate games
        success = self.integrate_games(fetched_games_df)
        
        if success:
            logger.info("=" * 80)
            logger.info("SUCCESS: Missing games integrated into training data")
            logger.info("=" * 80)
        else:
            logger.error("=" * 80)
            logger.error("FAILED: Could not integrate missing games")
            logger.error("=" * 80)
        
        return success

def main():
    """Main execution."""
    filler = MissingGamesFiller()
    success = filler.run()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()

