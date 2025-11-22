#!/usr/bin/env python3
"""
MIGRATE REAL 2025 DATA FROM STARTER PACK TO MODEL PACK
======================================================

This script extracts real 2025 college football data from the starter pack
and processes it to match the model pack's 81-feature format (88 total columns).

Author: Data Migration Agent
Date: 2025-11-14
"""

import warnings

warnings.filterwarnings('ignore')

import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from cfbd import ApiClient, Configuration
from model_pack.utils.cfbd_advanced_metrics import (
    ADVANCED_METRIC_COLUMNS,
    AdvancedMetricsBuilder,
)

# Import configuration system
_config_dir = Path(__file__).parent / "config"
if str(_config_dir.parent) not in sys.path:
    sys.path.insert(0, str(_config_dir.parent))
from config.data_config import get_data_config
from config.fallback_config import get_fallback_config

# Get configuration
config = get_data_config()
fallback_config = get_fallback_config()

API_KEY = os.environ.get("CFBD_API_KEY") or os.environ.get("CFBD_API_TOKEN")
if not API_KEY:
    print("⚠️  CFBD_API_KEY not found - will rely on pre-calculated metrics instead of live StatsApi pulls.")

class StarterPackDataMigrator:
    """
    Migrates real data from starter pack to model pack format for the current season.
    """
    
    def __init__(self):
        self.base_path = Path(__file__).parent.parent
        self.starter_pack_path = self.base_path / "starter_pack" / "data"
        self.model_pack_path = self.base_path / "model_pack"
        
        # File paths using configuration
        self.starter_games = config.get_starter_pack_data_path("data/games.csv")
        self.training_data = config.get_training_data_path()
        current_season = config.get_season()
        self.output_file = config.get_output_path(f"{current_season}_starter_pack_migrated.csv")
        self.processed_metrics_path = config.get_output_path(f"{current_season}_processed_features.csv")
        self.min_processed_week = None
        self.max_processed_week = None
        self._load_processed_week_range()
        self.api_client = None
        if API_KEY:
            configuration = Configuration()
            configuration.api_key['Authorization'] = API_KEY
            configuration.api_key_prefix['Authorization'] = 'Bearer'
            configuration.host = "https://api.collegefootballdata.com"
            self.api_client = ApiClient(configuration)
        self.rate_limit_delay = 0.17
        
        # GraphQL client (optional - for future use)
        self.graphql_client = None
        self.use_graphql = False
        try:
            from src.data_sources.cfbd_graphql import CFBDGraphQLClient
            if API_KEY:
                try:
                    self.graphql_client = CFBDGraphQLClient(api_key=API_KEY, host="production")
                    self.use_graphql = True
                    print("✅ GraphQL client available (for future enhancements)")
                except Exception as e:
                    print(f"⚠️ GraphQL initialization failed: {e}")
        except ImportError:
            print("⚠️ GraphQL client not available")
        
        # Data storage
        self.starter_current_season = None
        self.historical_data = None
        self.processed_current_season = None
        
        current_season = config.get_season()
        print("=" * 80)
        print(f"STARTER PACK DATA MIGRATOR - {current_season} REAL DATA")
        print("=" * 80)
        print(f"Initialized: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Season: {current_season}")
        print(f"Starter pack: {self.starter_games}")
        print(f"Model pack: {self.model_pack_path}")

    def _rate_limit(self):
        """Respect CFBD API rate limits."""
        time.sleep(self.rate_limit_delay)
    
    def fetch_games_graphql(self, season: int, week: int) -> pd.DataFrame:
        """
        Fetch games data using GraphQL API.
        
        Args:
            season: Season year
            week: Week number
            
        Returns:
            DataFrame containing game information
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
        return self._convert_graphql_to_dataframe(games_data)

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

    def load_starter_pack_data(self):
        """Load current season games from starter pack or fetch via GraphQL/REST if missing."""
        print("\n1. LOADING STARTER PACK DATA")
        print("-" * 50)
        
        games_df = None
        
        if os.path.exists(self.starter_games):
            print(f"Loading games from: {self.starter_games}")
            try:
                games_df = pd.read_csv(self.starter_games, low_memory=False)
            except Exception as e:
                print(f"⚠️ Failed to read starter pack CSV: {e}")
                games_df = None
        else:
            print(f"⚠️ Starter pack file not found: {self.starter_games}")

        # Fallback to API if file missing or failed
        if games_df is None or games_df.empty:
            print("🔄 Attempting to fetch data via API (GraphQL/REST)...")
            current_season = config.get_season()
            current_week = config.get_week()
            
            all_games = []
            for week in range(1, current_week + 1):
                # Try GraphQL first
                if self.use_graphql and self.graphql_client:
                    try:
                        print(f"  Fetching Week {week} via GraphQL...")
                        df_week = self.fetch_games_graphql(current_season, week)
                        if not df_week.empty:
                            all_games.append(df_week)
                            print(f"  ✅ Fetched {len(df_week)} games via GraphQL")
                            continue
                    except ValueError as e:
                        # GraphQL client not initialized
                        print(f"  ⚠️ GraphQL client not available: {e} - falling back to REST")
                    except Exception as e:
                        error_msg = str(e).lower()
                        if "401" in error_msg or "unauthorized" in error_msg or "auth" in error_msg:
                            print(f"  ⚠️ GraphQL authentication failed (Tier 3+ required): {e} - falling back to REST")
                        else:
                            print(f"  ⚠️ GraphQL fetch failed for Week {week}: {e} - falling back to REST")
                
                # REST Fallback
                if self.api_client:
                    try:
                        print(f"  Fetching Week {week} via REST...")
                        from cfbd import GamesApi
                        games_api = GamesApi(self.api_client)
                        self._rate_limit()
                        games = games_api.get_games(year=current_season, week=week)
                        if games:
                            # Convert to dicts
                            game_dicts = [g.to_dict() for g in games]
                            # Convert to DF
                            df_week = pd.DataFrame(game_dicts)
                            all_games.append(df_week)
                    except Exception as e:
                        print(f"  ⚠️ REST fetch failed for Week {week}: {e}")

            if all_games:
                games_df = pd.concat(all_games, ignore_index=True)
                print(f"✅ Fetched {len(games_df)} games from API")
            else:
                raise RuntimeError("Failed to load games from file OR API")

        # Filter for current season
        current_season = config.get_season()
        # Ensure season column is int
        if 'season' in games_df.columns:
            games_df['season'] = pd.to_numeric(games_df['season'], errors='coerce').fillna(0).astype(int)
            
        self.starter_current_season = games_df[games_df['season'] == current_season].copy()
        
        print(f"Total {current_season} games in starter pack: {len(self.starter_current_season)}")
        print(f"Weeks covered: {sorted(self.starter_current_season['week'].unique())}")
        current_week = config.get_week()
        print(f"Week {current_week} games: {len(self.starter_current_season[self.starter_current_season['week'] == current_week])}")
        
        # Verify Ohio State vs UCLA (if week 12 exists)
        if current_week >= 12:
            osu_ucla = self.starter_current_season[
                (self.starter_current_season['week'] == 12) &
                (self.starter_current_season['home_team'].str.contains('Ohio State', case=False, na=False)) &
                (self.starter_current_season['away_team'].str.contains('UCLA', case=False, na=False))
            ]
            print(f"Ohio State vs UCLA Week 12: {len(osu_ucla)} game(s)")
            if len(osu_ucla) > 0:
                game_id = osu_ucla.iloc[0].get('id', 'Unknown')
                start_date = osu_ucla.iloc[0].get('start_date', 'Unknown')
                print(f"  Game ID: {game_id}")
                print(f"  Date: {start_date}")
        
        return True
    
    def _load_processed_week_range(self):
        """Detect coverage range from processed metrics file (if present)."""
        if not self.processed_metrics_path.exists():
            return
        try:
            weeks_df = pd.read_csv(self.processed_metrics_path, usecols=['week'])
            if not weeks_df.empty:
                self.min_processed_week = int(weeks_df['week'].min())
                self.max_processed_week = int(weeks_df['week'].max())
        except Exception:
            self.min_processed_week = None
            self.max_processed_week = None
    
    def load_historical_structure(self):
        """Load historical training data to understand structure and get Elo ratings"""
        print("\n2. LOADING HISTORICAL DATA STRUCTURE")
        print("-" * 50)
        
        print(f"Loading training data from: {self.training_data}")
        # Load full historical data to get Elo ratings
        self.historical_data_full = pd.read_csv(self.training_data, low_memory=False)
        self.historical_data = self.historical_data_full.head(100)  # Sample for structure
        
        print(f"Historical data columns: {len(self.historical_data.columns)}")
        print(f"Required columns: {list(self.historical_data.columns)}")
        
        # Calculate most recent Elo ratings from historical data (end of previous season)
        print("\nCalculating most recent Elo ratings from historical data...")
        # Filter out current season data - only use pre-current-season data for Elo calculation
        current_season = config.get_season()
        historical_pre_current = self.historical_data_full[self.historical_data_full['season'] < current_season].copy()
        latest_season = historical_pre_current['season'].max()
        latest_season_data = historical_pre_current[historical_pre_current['season'] == latest_season].copy()
        print(f"Using {latest_season} season data (excluding {current_season}) for Elo calculation")
        
        # Get the latest week in the latest season
        latest_week = latest_season_data['week'].max()
        latest_week_data = latest_season_data[latest_season_data['week'] == latest_week].copy()
        
        print(f"Using Elo from {latest_season} season, week {latest_week}")
        
        self.team_elo_dict = {}
        
        # Build Elo dictionary from latest week games
        # Use end-of-season Elo ratings from the latest week
        for idx, row in latest_week_data.iterrows():
            # Store Elo for home team
            if pd.notna(row['home_elo']) and row['home_elo'] != 0:
                if row['home_team'] not in self.team_elo_dict:
                    self.team_elo_dict[row['home_team']] = row['home_elo']
            
            # Store Elo for away team
            if pd.notna(row['away_elo']) and row['away_elo'] != 0:
                if row['away_team'] not in self.team_elo_dict:
                    self.team_elo_dict[row['away_team']] = row['away_elo']
        
        # For teams not in latest week, get from most recent game in latest season
        all_teams_latest_season = set(latest_season_data['home_team'].unique()) | set(latest_season_data['away_team'].unique())
        missing_teams = all_teams_latest_season - set(self.team_elo_dict.keys())
        
        if missing_teams:
            print(f"Finding Elo for {len(missing_teams)} teams not in latest week...")
            # Sort by week descending to get most recent games first
            latest_season_sorted = latest_season_data.sort_values(['week'], ascending=False)
            
            for team in missing_teams:
                # Find most recent game with this team
                team_games = latest_season_sorted[
                    (latest_season_sorted['home_team'] == team) |
                    (latest_season_sorted['away_team'] == team)
                ]
                
                if len(team_games) > 0:
                    most_recent = team_games.iloc[0]
                    if most_recent['home_team'] == team and pd.notna(most_recent['home_elo']):
                        self.team_elo_dict[team] = most_recent['home_elo']
                    elif most_recent['away_team'] == team and pd.notna(most_recent['away_elo']):
                        self.team_elo_dict[team] = most_recent['away_elo']
                    else:
                        self.team_elo_dict[team] = 1500.0
                else:
                    self.team_elo_dict[team] = 1500.0
        
        print(f"Calculated Elo ratings for {len(self.team_elo_dict)} teams")
        if len(self.team_elo_dict) > 0:
            elo_values = [v for v in self.team_elo_dict.values() if v != 1500.0 and pd.notna(v)]
            if elo_values:
                print(f"Elo range: {min(elo_values):.1f} to {max(elo_values):.1f}")
                print(f"Teams with real Elo (not 1500.0): {len(elo_values)}/{len(self.team_elo_dict)}")
            else:
                print(f"All teams have default Elo (1500.0)")
        
        # Sample a few teams
        sample_teams = ['Ohio State', 'UCLA', 'Michigan', 'Alabama', 'Georgia']
        print(f"\nSample team Elo ratings:")
        for team in sample_teams:
            if team in self.team_elo_dict:
                print(f"  {team}: {self.team_elo_dict[team]:.1f}")
        
        return True
    
    def filter_fbs_teams(self):
        """Filter to FBS teams only (matching model pack scope)"""
        print("\n3. FILTERING TO FBS TEAMS")
        print("-" * 50)
        
        # Get FBS teams from historical data
        historical_source = self.historical_data_full if hasattr(self, "historical_data_full") else self.historical_data
        historical_teams = set(historical_source['home_team'].unique()) | \
                          set(historical_source['away_team'].unique())
        
        print(f"FBS teams in historical data: {len(historical_teams)}")
        
        # Filter starter pack to FBS teams only
        before_count = len(self.starter_current_season)
        self.starter_current_season = self.starter_current_season[
            (self.starter_current_season['home_team'].isin(historical_teams)) &
            (self.starter_current_season['away_team'].isin(historical_teams))
        ].copy()
        
        after_count = len(self.starter_current_season)
        print(f"Games before FBS filter: {before_count}")
        print(f"Games after FBS filter: {after_count}")
        print(f"Removed: {before_count - after_count} non-FBS games")
        
        return True
    
    def map_to_training_format(self):
        """Map starter pack data to model pack training format"""
        print("\n4. MAPPING TO TRAINING DATA FORMAT")
        print("-" * 50)
        
        # Start with basic game info
        processed = pd.DataFrame()
        
        # Core game metadata
        processed['id'] = self.starter_current_season['id']
        processed['start_date'] = pd.to_datetime(self.starter_current_season['start_date'])
        processed['season'] = self.starter_current_season['season']
        processed['season_type'] = self.starter_current_season['season_type']
        processed['week'] = self.starter_current_season['week']
        processed['neutral_site'] = self.starter_current_season['neutral_site'].fillna(False)
        
        # Team info
        processed['home_team'] = self.starter_current_season['home_team']
        processed['home_conference'] = self.starter_current_season['home_conference']
        processed['away_team'] = self.starter_current_season['away_team']
        processed['away_conference'] = self.starter_current_season['away_conference']
        
        # Elo ratings - use from starter pack if available, otherwise from historical data
        default_elo = fallback_config.default_elo_rating
        processed['home_elo'] = self.starter_current_season['home_start_elo'].fillna(
            processed['home_team'].map(self.team_elo_dict).fillna(default_elo)
        )
        processed['away_elo'] = self.starter_current_season['away_start_elo'].fillna(
            processed['away_team'].map(self.team_elo_dict).fillna(default_elo)
        )
        
        # Talent ratings - load from current season talent file
        current_season = config.get_season()
        talent_path = config.get_output_path(f"{current_season}_talent.csv")
        if talent_path.exists():
            talent_df = pd.read_csv(talent_path)
            talent_dict = dict(zip(talent_df['team'], talent_df['talent']))
            processed['home_talent'] = processed['home_team'].map(talent_dict)
            processed['away_talent'] = processed['away_team'].map(talent_dict)
        else:
            # Fallback to config default if talent file doesn't exist
            default_talent = fallback_config.default_talent_rating
            processed['home_talent'] = default_talent
            processed['away_talent'] = default_talent
        
        # Game outcomes
        processed['home_points'] = self.starter_current_season['home_points'].fillna(0).astype(int)
        processed['away_points'] = self.starter_current_season['away_points'].fillna(0).astype(int)
        processed['margin'] = processed['home_points'] - processed['away_points']
        
        # Spread (if available)
        processed['spread'] = 0.0  # Will need to be filled from external source
        
        # Generate game_key: unique identifier for each game
        # Format: {season}_{week}_{home_team}_{away_team} (normalized)
        processed['game_key'] = processed.apply(
            lambda row: f"{row['season']}_{row['week']}_{row['home_team'].replace(' ', '_')}_{row['away_team'].replace(' ', '_')}",
            axis=1
        )
        
        # Calculate conference_game: True if both teams in same conference
        processed['conference_game'] = (
            processed['home_conference'].notna() & 
            processed['away_conference'].notna() &
            (processed['home_conference'] == processed['away_conference'])
        )
        
        print(f"Mapped {len(processed)} games with basic fields")
        print(f"Columns created: {len(processed.columns)}")
        print(f"  game_key: Generated for all games")
        print(f"  conference_game: Calculated ({processed['conference_game'].sum()} conference games)")
        
        self.processed_current_season = processed
        return True

    def apply_week_filter(self, min_week: int = 5, max_week: Optional[int] = None) -> bool:
        """Filter out games outside the processed metrics coverage window."""
        if self.processed_current_season is None:
            print("No processed season data found before week filtering.")
            return False

        print("\n5. APPLYING WEEK FILTER")
        print("-" * 50)
        before = len(self.processed_current_season)
        effective_min = max(min_week, self.min_processed_week or min_week)
        effective_max = max_week or self.max_processed_week

        mask = self.processed_current_season['week'] >= effective_min
        if effective_max is not None:
            mask &= self.processed_current_season['week'] <= effective_max
        filtered = self.processed_current_season[mask].copy()
        removed = before - len(filtered)
        self.processed_current_season = filtered
        range_desc = f"Week {effective_min}+"
        if effective_max is not None:
            range_desc = f"Week {effective_min}-{effective_max}"
        print(f"Applied {range_desc} filter: {len(filtered)} games kept, {removed} removed.")
        return len(filtered) > 0

    def populate_advanced_features(self) -> bool:
        """
        Populate advanced opponent-adjusted features using CFBD data.
        """
        print("\n6. POPULATING ADVANCED METRICS WITH REAL DATA")
        print("-" * 50)

        if self.processed_current_season is None or self.processed_current_season.empty:
            print("No processed season data available for advanced metrics.")
            return False

        games_for_builder = self.processed_current_season[['home_team', 'away_team', 'season', 'week']].copy()
        games_for_builder = games_for_builder.assign(id=self.processed_current_season['game_key'])

        if not self.api_client:
            print("CFBD API client unavailable; skipping direct StatsApi fetch.")
            return False

        builder = AdvancedMetricsBuilder(
            api_client=self.api_client,
            season=config.get_season(),
            rate_limit_callback=self._rate_limit,
        )
        metrics = builder.build_metrics_for_games(games_for_builder, pd.DataFrame())

        if not metrics:
            print("CFBD advanced metrics were unavailable; placeholders may be required.")
            return False

        for column in ADVANCED_METRIC_COLUMNS:
            if column not in self.processed_current_season.columns:
                self.processed_current_season[column] = np.nan

        populated_games = 0
        for idx, row in self.processed_current_season.iterrows():
            game_id = row['game_key']
            metric_values = metrics.get(game_id)
            if not metric_values:
                continue
            for column, value in metric_values.items():
                if column in self.processed_current_season.columns:
                    self.processed_current_season.at[idx, column] = value
            populated_games += 1

        missing_values = self.processed_current_season[ADVANCED_METRIC_COLUMNS].isna().sum().sum()
        print(f"Advanced metrics populated for {populated_games} games")
        if missing_values:
            print(f"⚠️  {missing_values} metric values remain missing after CFBD fetch (will use historical fallback).")

        return populated_games > 0

    def merge_precalculated_metrics(self) -> bool:
        """
        Merge opponent-adjusted metrics from the metrics calculation agent output.
        """
        season = config.get_season()
        metrics_path = self.processed_metrics_path
        if not metrics_path.exists():
            print("No pre-calculated metrics file found; skipping merge.")
            return False

        if self.processed_current_season is None or self.processed_current_season.empty:
            print("No processed season data available for metrics merge.")
            return False

        print("\n7. MERGING PRE-CALCULATED METRICS")
        print("-" * 50)
        print(f"Loading processed metrics from: {metrics_path}")

        metrics_df = pd.read_csv(metrics_path, low_memory=False)
        metrics_df = metrics_df[metrics_df['season'] == season].copy()
        metrics_full = metrics_df.copy()

        if metrics_df.empty:
            print("Processed metrics file contains no matching season rows.")
            return False

        key_cols = ['season', 'week', 'home_team', 'away_team']
        for col in key_cols:
            if col in metrics_df.columns:
                metrics_df[col] = metrics_df[col].astype(str).str.strip()
            if col in self.processed_current_season.columns:
                self.processed_current_season[col] = self.processed_current_season[col].astype(str).str.strip()

        merge_cols = key_cols + list(ADVANCED_METRIC_COLUMNS)
        available_cols = [col for col in merge_cols if col in metrics_df.columns]
        metrics_subset = metrics_df[available_cols].copy()

        adv_cols_list = list(ADVANCED_METRIC_COLUMNS)
        for adv_col in adv_cols_list:
            if adv_col not in self.processed_current_season.columns:
                self.processed_current_season[adv_col] = np.nan

        merged = self.processed_current_season.merge(
            metrics_subset,
            on=key_cols,
            how='left',
            suffixes=('', '_calculated')
        )

        filled_columns = 0
        for column in adv_cols_list:
            source_col = f"{column}_calculated"
            if source_col in merged.columns:
                col_before = merged[column].notna().sum() if column in merged.columns else 0
                if column not in merged.columns:
                    merged[column] = merged[source_col]
                else:
                    merged[column] = merged[column].where(merged[column].notna(), merged[source_col])
                col_after = merged[column].notna().sum()
                if col_after > col_before:
                    filled_columns += 1
                merged = merged.drop(columns=[source_col])

        matched_rows = merged[adv_cols_list].notna().any(axis=1).sum()
        if matched_rows == 0:
            print("No overlapping games found between starter data and processed metrics.")
            dataset = metrics_full.copy()
            if 'game_key' not in dataset.columns:
                dataset['game_key'] = dataset.apply(
                    lambda row: f"{row['season']}_{row['week']}_{row['home_team'].replace(' ', '_')}_{row['away_team'].replace(' ', '_')}",
                    axis=1
                )
            if 'conference_game' not in dataset.columns and 'home_conference' in dataset.columns and 'away_conference' in dataset.columns:
                dataset['conference_game'] = (
                    dataset['home_conference'].notna() &
                    dataset['away_conference'].notna() &
                    (dataset['home_conference'] == dataset['away_conference'])
                )
            self.processed_current_season = dataset
            total_missing = self.processed_current_season[adv_cols_list].isna().sum().sum()
            print("Replaced migrated dataset with processed metrics output to avoid placeholders.")
            return total_missing == 0

        self.processed_current_season = merged
        total_missing = self.processed_current_season[adv_cols_list].isna().sum().sum()
        print(f"Filled advanced metrics for {filled_columns} columns using processed features.")
        print(f"Remaining missing advanced metric values: {int(total_missing)}")

        return filled_columns > 0
    
    def add_placeholder_features(self, allow_placeholders: bool = False):
        """
        Add placeholder opponent-adjusted features.
        
        WARNING: This method uses historical averages as placeholders.
        For production use, these should be:
        1. Calculated from play-by-play data (see metrics_calculation_agent.py)
        2. Fetched from CFBD API advanced stats endpoints
        3. Calculated using proper opponent-adjusted methodology
        
        These placeholder values are acceptable only when real calculations are not available.
        """
        warnings.warn(
            "add_placeholder_features is deprecated. Use populate_advanced_features instead.",
            DeprecationWarning,
        )
        if not allow_placeholders:
            raise RuntimeError(
                "Placeholder features are disabled. Pass allow_placeholders=True explicitly to override."
            )

        print("\n6. ADDING PLACEHOLDER FEATURES (DEPRECATED)")
        print("-" * 50)
        print("⚠️  WARNING: Using historical averages as placeholders")
        print("   Real calculations from play-by-play data or CFBD API are preferred")
        
        # Get all required columns from historical data
        required_cols = list(self.historical_data.columns)
        existing_cols = list(self.processed_current_season.columns)
        missing_cols = [col for col in required_cols if col not in existing_cols]
        
        print(f"Required columns: {len(required_cols)}")
        print(f"Existing columns: {len(existing_cols)}")
        print(f"Missing columns: {len(missing_cols)}")
        
        # Add missing columns with placeholder values
        # These should be calculated from advanced stats, but for now use historical averages
        placeholder_count = 0
        for col in missing_cols:
            if col in self.historical_data.columns:
                # Use historical mean as placeholder (with warning)
                mean_val = self.historical_data[col].mean()
                self.processed_current_season[col] = mean_val
                placeholder_count += 1
            else:
                # Use zero as fallback
                self.processed_current_season[col] = 0.0
        
        # Ensure column order matches historical data
        self.processed_current_season = self.processed_current_season[required_cols]
        
        print(f"Added {len(missing_cols)} placeholder feature columns")
        print(f"⚠️  {placeholder_count} columns using historical averages (not real calculations)")
        print(f"Final column count: {len(self.processed_current_season.columns)}")

        if placeholder_count > 0:
            self._document_placeholder_features(missing_cols)

        return True

    def _document_placeholder_features(self, placeholder_columns):
        """
        Persist a reminder that certain columns are still placeholders.
        """
        report_path = Path(self.output_file).with_suffix('.placeholder_warning.txt')
        note_lines = [
            "PLACEHOLDER FEATURE NOTICE",
            "==========================",
            "",
            "The migration process inserted historical averages for the following columns:",
            ", ".join(sorted(placeholder_columns)),
            "",
            "These values are NOT real opponent-adjusted calculations. Replace them by running:",
            "  python model_pack/metrics_calculation_agent.py",
            "",
            "That agent recalculates advanced features using play-by-play data and CFBD APIs.",
            ""
        ]
        with open(report_path, 'w', encoding='utf-8') as handle:
            handle.write("\n".join(note_lines))
        print(f"📄 Placeholder report written to {report_path}")
    
    def save_migrated_data(self):
        """Save migrated data to file"""
        print("\n8. SAVING MIGRATED DATA")
        print("-" * 50)
        
        self.processed_current_season.to_csv(self.output_file, index=False)
        print(f"Saved to: {self.output_file}")
        print(f"Games: {len(self.processed_current_season)}")
        print(f"Columns: {len(self.processed_current_season.columns)}")
        
        # Summary by week
        print("\nGames by week:")
        week_counts = self.processed_current_season.groupby('week').size()
        for week, count in week_counts.items():
            print(f"  Week {week}: {count} games")
        
        return True
    
    def run_migration(self):
        """Execute full migration process"""
        try:
            self.load_starter_pack_data()
            self.load_historical_structure()
            self.filter_fbs_teams()
            self.map_to_training_format()
            self.apply_week_filter()
            cfbd_metrics = self.populate_advanced_features()
            precalc_metrics = self.merge_precalculated_metrics()
            metrics_populated = cfbd_metrics or precalc_metrics
            placeholders_used = False
            if not metrics_populated:
                print("⚠️  Falling back to placeholder features due to missing CFBD data.")
                self.add_placeholder_features(allow_placeholders=True)
                placeholders_used = True
            self.save_migrated_data()
            
            print("\n" + "=" * 80)
            print("MIGRATION COMPLETED SUCCESSFULLY")
            print("=" * 80)
            print(f"Output file: {self.output_file}")
            print(f"Total games migrated: {len(self.processed_current_season)}")
            if placeholders_used:
                print("\nNOTE: Advanced features rely on historical placeholders.")
                print("      Re-run populate_advanced_features once CFBD data becomes available.")
            elif cfbd_metrics:
                print("\nAdvanced metrics populated directly from CFBD advanced stats.")
            elif precalc_metrics:
                print("\nAdvanced metrics sourced from metrics_calculation_agent output.")
            
            return True
            
        except Exception as e:
            print(f"\nERROR: Migration failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == "__main__":
    migrator = StarterPackDataMigrator()
    success = migrator.run_migration()
    sys.exit(0 if success else 1)
