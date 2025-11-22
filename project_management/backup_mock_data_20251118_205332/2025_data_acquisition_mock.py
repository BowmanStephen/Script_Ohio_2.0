#!/usr/bin/env python3
"""
2025 College Football Data Acquisition Agent - Mock Version
===========================================================

This script creates mock 2025 college football data based on historical patterns
and simulates the data acquisition process when API access is limited.

Author: Data Acquisition Agent
Date: November 7, 2025
"""

import os
import sys
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import pandas as pd
import numpy as np

# Import configuration system
_config_dir = Path(__file__).parent / "config"
if str(_config_dir.parent) not in sys.path:
    sys.path.insert(0, str(_config_dir.parent))
from config.data_config import get_data_config
from config.fallback_config import get_fallback_config

# Get configuration
config = get_data_config()
fallback_config = get_fallback_config()

# Use dynamic configuration
CURRENT_SEASON = config.get_season()
CURRENT_WEEK = config.get_week()
OUTPUT_DIR = config.output_dir

# Set up logging
log_file = config.output_dir / "data_acquisition.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(str(log_file)),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class MockDataAcquisitionAgent:
    """
    Mock data acquisition agent that creates realistic 2025 college football data
    based on historical patterns when API access is limited.
    """

    def __init__(self):
        """Initialize the mock agent."""
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

        # Load existing training data to understand patterns
        self.load_historical_data()

    def load_historical_data(self):
        """Load historical training data to understand patterns."""
        try:
            training_data_path = config.get_training_data_path()
            self.historical_data = pd.read_csv(training_data_path)
            logger.info(f"Loaded historical data: {len(self.historical_data)} games from {config.historical_start_year}-{config.get_season()-1}")

            # Get unique teams from historical data
            self.teams = set(self.historical_data['home_team'].unique()) | set(self.historical_data['away_team'].unique())
            logger.info(f"Found {len(self.teams)} unique teams in historical data")

        except Exception as e:
            logger.error(f"Error loading historical data: {str(e)}")
            self.historical_data = pd.DataFrame()
            self.teams = set()

    def generate_mock_games(self) -> pd.DataFrame:
        """
        Generate mock games for current season based on historical patterns.

        Returns:
            DataFrame containing mock game information
        """
        current_season = config.get_season()
        current_week = config.get_week()
        logger.info(f"Generating mock {current_season} games data for Weeks 1-{current_week}...")
        self.quality_report['start_time'] = datetime.now()

        if self.historical_data.empty:
            logger.error("No historical data available for pattern generation")
            return pd.DataFrame()

        # Generate realistic game schedule
        mock_games = []
        teams_list = list(self.teams)
        np.random.shuffle(teams_list)

        current_week = config.get_week()
        games_per_week = len(teams_list) // 2  # Approximate games per week
        total_games_needed = games_per_week * current_week

        logger.info(f"Generating {total_games_needed} mock games across {current_week} weeks")

        for week in range(1, current_week + 1):
            week_games = 0
            available_teams = teams_list.copy()
            np.random.shuffle(available_teams)

            while len(available_teams) >= 2 and week_games < games_per_week:
                home_team = available_teams.pop()
                away_team = available_teams.pop()

                # Generate realistic game data based on historical patterns
                game_data = self.generate_single_game_data(home_team, away_team, week)
                mock_games.append(game_data)
                week_games += 1

            logger.info(f"Generated {week_games} mock games for Week {week}")

        logger.info(f"Total mock games generated: {len(mock_games)}")
        self.quality_report['total_games'] = len(mock_games)

        mock_df = pd.DataFrame(mock_games)
        return mock_df

    def generate_single_game_data(self, home_team: str, away_team: str, week: int) -> Dict:
        """
        Generate realistic data for a single game based on historical patterns.

        Args:
            home_team: Home team name
            away_team: Away team name
            week: Week number

        Returns:
            Dictionary containing game data
        """
        # Get historical averages for teams
        home_historical = self.historical_data[
            (self.historical_data['home_team'] == home_team) |
            (self.historical_data['away_team'] == home_team)
        ]

        away_historical = self.historical_data[
            (self.historical_data['home_team'] == away_team) |
            (self.historical_data['away_team'] == away_team)
        ]

        # Generate realistic Elo ratings based on historical performance
        default_elo = fallback_config.default_elo_rating
        home_elo = default_elo + np.random.normal(0, 100)
        away_elo = default_elo + np.random.normal(0, 100)

        # Generate talent ratings
        default_talent = fallback_config.default_talent_rating
        home_talent = default_talent + np.random.normal(0, 100)
        away_talent = default_talent + np.random.normal(0, 100)

        # Simulate game outcome based on Elo difference
        elo_diff = home_elo - away_elo
        home_win_prob = 1 / (1 + 10 ** (-elo_diff / 400))

        # Generate scores
        if np.random.random() < home_win_prob:
            home_points = int(np.random.normal(35, 12))
            away_points = int(np.random.normal(24, 10))
        else:
            home_points = int(np.random.normal(24, 10))
            away_points = int(np.random.normal(35, 12))

        # Ensure non-negative scores
        home_points = max(0, home_points)
        away_points = max(0, away_points)

        # Generate game date
        current_season = config.get_season()
        season_start = datetime(current_season, 8, 24)  # Approximate start date (late August)
        game_date = season_start + timedelta(weeks=week-1, days=np.random.randint(0, 6))

        # Generate realistic conference data using config
        conferences = config.fbs_conferences
        home_conference = np.random.choice(conferences)
        away_conference = np.random.choice(conferences)

        return {
            'id': f"mock_{current_season}_{week}_{home_team}_{away_team}",
            'start_date': game_date.strftime('%Y-%m-%d %H:%M:%S'),
            'season': current_season,
            'season_type': 'regular',
            'week': week,
            'neutral_site': np.random.random() < 0.1,  # 10% neutral site games
            'home_team': home_team,
            'home_conference': home_conference,
            'away_team': away_team,
            'away_conference': away_conference,
            'home_points': home_points,
            'away_points': away_points,
            'margin': abs(home_points - away_points),
            'home_elo': home_elo,
            'away_elo': away_elo,
            'home_talent': home_talent,
            'away_talent': away_talent,
            'spread': elo_diff / 25  # Rough spread conversion
        }

    def generate_mock_plays(self, games_df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate mock play-by-play data for games.

        Args:
            games_df: DataFrame containing game information

        Returns:
            DataFrame containing mock play-by-play data
        """
        logger.info("Generating mock play-by-play data...")

        all_plays = []
        current_week = config.get_week()
        completed_games = games_df[games_df['week'] <= current_week - 1]  # Assume recent week might not be complete

        logger.info(f"Generating plays for {len(completed_games)} completed games")

        for idx, game in completed_games.head(10).iterrows():  # Limit to 10 games for performance
            plays_in_game = np.random.randint(120, 180)  # Typical number of plays
            home_score = 0
            away_score = 0

            for play_num in range(plays_in_game):
                # Generate play data
                period = 1 if play_num < plays_in_game * 0.3 else 2 if play_num < plays_in_game * 0.6 else 3 if play_num < plays_in_game * 0.8 else 4
                clock = f"{15 - (play_num % 15):02d}:{np.random.randint(0, 59):02d}"

                # Generate yard line
                yard_line = f"home {np.random.randint(1, 50)}" if np.random.random() < 0.5 else f"away {np.random.randint(1, 50)}"

                # Generate down and distance
                if np.random.random() < 0.2:  # 20% of plays are scoring plays
                    scoring = True
                    if np.random.random() < 0.6:  # Home team scores
                        home_score += np.random.choice([2, 3, 6, 7, 8])
                    else:
                        away_score += np.random.choice([2, 3, 6, 7, 8])
                else:
                    scoring = False

                play_types = ['Pass', 'Run', 'Punt', 'Field Goal', 'Kickoff']
                play_type = np.random.choice(play_types)

                play_data = {
                    'game_id': game['id'],
                    'play_id': f"{game['id']}_play_{play_num}",
                    'period': period,
                    'clock': clock,
                    'yard_line': yard_line,
                    'down': np.random.randint(1, 4) if play_type in ['Pass', 'Run'] else None,
                    'distance': np.random.randint(1, 11) if play_type in ['Pass', 'Run'] else None,
                    'play_type': play_type,
                    'scoring': scoring,
                    'home_score': home_score,
                    'away_score': away_score,
                    'text': f"Mock {play_type} play",
                    'home_team': game['home_team'],
                    'away_team': game['away_team']
                }
                all_plays.append(play_data)

            self.quality_report['successful_play_fetches'] += 1
            logger.info(f"Generated {plays_in_game} mock plays for game {game['id']}")

        logger.info(f"Total mock plays generated: {len(all_plays)}")
        return pd.DataFrame(all_plays)

    def generate_mock_talent_ratings(self) -> pd.DataFrame:
        """
        Generate mock talent ratings for teams.

        Returns:
            DataFrame containing mock talent information
        """
        logger.info("Generating mock talent ratings...")

        talent_data = []
        current_season = config.get_season()
        default_talent = fallback_config.default_talent_rating
        
        for team in self.teams:
            # Generate realistic talent ratings based on team name patterns
            # Powerhouse teams get higher ratings (could be made configurable)
            powerhouses = ['Alabama', 'Georgia', 'Ohio State', 'Michigan', 'Clemson', 'Oklahoma', 'Texas', 'LSU']

            if team in powerhouses:
                talent = np.random.normal(850, 50)
            else:
                talent = np.random.normal(default_talent, 150)

            talent_data.append({
                'team': team,
                'talent': max(200, min(1000, talent)),  # Clamp between 200-1000
                'season': current_season,
                'rank': 0  # Will be calculated later
            })

        talent_df = pd.DataFrame(talent_data)
        # Calculate rankings
        talent_df = talent_df.sort_values('talent', ascending=False).reset_index(drop=True)
        talent_df['rank'] = range(1, len(talent_df) + 1)

        logger.info(f"Generated talent ratings for {len(talent_df)} teams")
        return talent_df

    def calculate_advanced_metrics(self, games_df: pd.DataFrame, plays_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate advanced metrics similar to existing training data.

        Args:
            games_df: DataFrame containing game information
            plays_df: DataFrame containing play-by-play data

        Returns:
            Enhanced games DataFrame with advanced metrics
        """
        logger.info("Calculating advanced metrics...")

        if self.historical_data.empty:
            logger.warning("No historical data available for advanced metrics - returning games without changes")
            return games_df

        required_columns = [
            'home_adjusted_epa', 'home_adjusted_epa_allowed',
            'away_adjusted_epa', 'away_adjusted_epa_allowed',
            'home_adjusted_rushing_epa', 'home_adjusted_rushing_epa_allowed',
            'away_adjusted_rushing_epa', 'away_adjusted_rushing_epa_allowed',
            'home_adjusted_passing_epa', 'home_adjusted_passing_epa_allowed',
            'away_adjusted_passing_epa', 'away_adjusted_passing_epa_allowed',
            'home_adjusted_success', 'home_adjusted_success_allowed',
            'away_adjusted_success', 'away_adjusted_success_allowed',
            'home_adjusted_standard_down_success', 'home_adjusted_standard_down_success_allowed',
            'away_adjusted_standard_down_success', 'away_adjusted_standard_down_success_allowed',
            'home_adjusted_passing_down_success', 'home_adjusted_passing_down_success_allowed',
            'away_adjusted_passing_down_success', 'away_adjusted_passing_down_success_allowed',
            'home_adjusted_line_yards', 'home_adjusted_line_yards_allowed',
            'away_adjusted_line_yards', 'away_adjusted_line_yards_allowed',
            'home_adjusted_second_level_yards', 'home_adjusted_second_level_yards_allowed',
            'away_adjusted_second_level_yards', 'away_adjusted_second_level_yards_allowed',
            'home_adjusted_open_field_yards', 'home_adjusted_open_field_yards_allowed',
            'away_adjusted_open_field_yards', 'away_adjusted_open_field_yards_allowed',
            'home_adjusted_explosiveness', 'home_adjusted_explosiveness_allowed',
            'away_adjusted_explosiveness', 'away_adjusted_explosiveness_allowed',
            'home_adjusted_rush_explosiveness', 'home_adjusted_rush_explosiveness_allowed',
            'away_adjusted_rush_explosiveness', 'away_adjusted_rush_explosiveness_allowed',
            'home_adjusted_pass_explosiveness', 'home_adjusted_pass_explosiveness_allowed',
            'away_adjusted_pass_explosiveness', 'away_adjusted_pass_explosiveness_allowed',
            'home_total_havoc_offense', 'home_front_seven_havoc_offense', 'home_db_havoc_offense',
            'away_total_havoc_offense', 'away_front_seven_havoc_offense', 'away_db_havoc_offense',
            'home_total_havoc_defense', 'home_front_seven_havoc_defense', 'home_db_havoc_defense',
            'away_total_havoc_defense', 'away_front_seven_havoc_defense', 'away_db_havoc_defense',
            'home_points_per_opportunity_offense', 'away_points_per_opportunity_offense',
            'home_points_per_opportunity_defense', 'away_points_per_opportunity_defense',
            'home_avg_start_offense', 'home_avg_start_defense',
            'away_avg_start_offense', 'away_avg_start_defense'
        ]

        # Build caches for fast lookups
        home_cache, away_cache, historical_means = self._build_metric_caches(required_columns)

        for col in required_columns:
            if col not in games_df.columns:
                games_df[col] = None

        for idx, game in games_df.iterrows():
            home_team = game.get('home_team')
            away_team = game.get('away_team')

            for col in required_columns:
                if pd.notna(games_df.at[idx, col]):
                    continue

                if col.startswith('home_'):
                    value = home_cache.get(col, {}).get(home_team)
                elif col.startswith('away_'):
                    value = away_cache.get(col, {}).get(away_team)
                else:
                    value = None

                if value is None:
                    value = historical_means.get(col, 0.0)

                games_df.at[idx, col] = value

        logger.info("Advanced metrics filled using historical medians for each team")
        return games_df

    def _build_metric_caches(self, columns: List[str]) -> Tuple[Dict[str, Dict[str, float]], Dict[str, Dict[str, float]], Dict[str, float]]:
        """
        Build caches of historical medians for each advanced metric column.
        """
        home_cache: Dict[str, Dict[str, float]] = {}
        away_cache: Dict[str, Dict[str, float]] = {}
        historical_means: Dict[str, float] = {}

        if self.historical_data.empty:
            return home_cache, away_cache, historical_means

        for col in columns:
            if col not in self.historical_data.columns:
                historical_means[col] = 0.0
                continue

            historical_means[col] = self.historical_data[col].mean()

            if col.startswith('home_'):
                grouped = self.historical_data.groupby('home_team')[col].median().dropna()
                home_cache[col] = grouped.to_dict()
            elif col.startswith('away_'):
                grouped = self.historical_data.groupby('away_team')[col].median().dropna()
                away_cache[col] = grouped.to_dict()

        return home_cache, away_cache, historical_means

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
        fallback_talent = fallback_config.default_talent_rating
        games_df['home_talent'] = games_df['home_team'].map(talent_dict).fillna(fallback_talent)
        games_df['away_talent'] = games_df['away_team'].map(talent_dict).fillna(fallback_talent)

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

        current_season = config.get_season()
        current_week = config.get_week()
        report = f"""
{current_season} COLLEGE FOOTBALL DATA ACQUISITION REPORT (MOCK DATA)
========================================================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Processing Time: {processing_time}
Data Type: Simulated/Mock Data (Based on Historical Patterns)

DATA SUMMARY:
- Total Games Generated: {self.quality_report['total_games']}
- Successful Game Generation: {self.quality_report['successful_game_fetches']}
- Successful Play Generation: {self.quality_report['successful_play_fetches']}
- Failed Generation Attempts: {len(self.quality_report['failed_games'])}
- Failed Play Generation: {len(self.quality_report['failed_plays'])}

DATA CHARACTERISTICS:
- Historical Pattern Analysis: Yes (Based on {config.historical_start_year}-{current_season-1} data)
- Teams Included: {len(self.teams)} unique teams
- Weeks Covered: 1-{current_week}
- Game Scheduling: Realistic based on historical patterns
- Score Generation: Elo-based probability modeling
- Advanced Metrics: Pattern-based generation

LIMITATIONS:
- This is simulated data, not actual 2025 results
- Play-by-play data is algorithmically generated
- Advanced metrics are based on historical averages
- Team talent ratings follow historical patterns
- Real-time factors (injuries, weather, etc.) not included

RECOMMENDATIONS:
- Replace with actual API data when available
- Use this data for testing and development only
- Validate against real 2025 results when season concludes
- Consider updating with actual game results weekly

DATA FILES CREATED:
- {current_season}_raw_games.csv: Mock game data
- {current_season}_plays.csv: Mock play-by-play data
- {current_season}_talent.csv: Mock talent ratings
- {current_season}_data_quality_report.txt: This report
"""

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
            current_season = config.get_season()
            # Save games data
            games_file = config.get_output_path(f"{current_season}_raw_games.csv")
            games_df.to_csv(games_file, index=False)
            logger.info(f"Saved games data: {games_file} ({len(games_df)} games)")

            # Save play-by-play data
            if not plays_df.empty:
                plays_file = config.get_output_path(f"{current_season}_plays.csv")
                plays_df.to_csv(plays_file, index=False)
                logger.info(f"Saved play-by-play data: {plays_file} ({len(plays_df)} plays)")

            # Save talent data
            if not talent_df.empty:
                talent_file = config.get_output_path(f"{current_season}_talent.csv")
                talent_df.to_csv(talent_file, index=False)
                logger.info(f"Saved talent data: {talent_file} ({len(talent_df)} teams)")

            # Generate and save quality report
            report = self.generate_quality_report()
            report_file = config.get_output_path(f"{current_season}_data_quality_report.txt")
            with open(report_file, 'w') as f:
                f.write(report)
            logger.info(f"Saved quality report: {report_file}")

        except Exception as e:
            logger.error(f"Error saving datasets: {str(e)}")
            raise

    def run_complete_acquisition(self):
        """
        Execute the complete mock data acquisition pipeline.
        """
        current_season = config.get_season()
        logger.info("=" * 60)
        logger.info(f"STARTING {current_season} COLLEGE FOOTBALL MOCK DATA ACQUISITION")
        logger.info("=" * 60)

        try:
            # Generate mock games data
            games_df = self.generate_mock_games()
            if games_df.empty:
                raise Exception("No mock games data generated")

            self.quality_report['successful_game_fetches'] = len(games_df)

            # Generate mock play-by-play data
            plays_df = self.generate_mock_plays(games_df)

            # Generate mock talent ratings
            talent_df = self.generate_mock_talent_ratings()

            # Merge talent data
            if not talent_df.empty:
                games_df = self.merge_talent_data(games_df, talent_df)

            # Calculate advanced metrics
            games_df = self.calculate_advanced_metrics(games_df, plays_df)

            # Save all datasets
            self.save_datasets(games_df, plays_df, talent_df)

            logger.info("=" * 60)
            logger.info("MOCK DATA ACQUISITION COMPLETED SUCCESSFULLY")
            logger.info("=" * 60)

            return True

        except Exception as e:
            logger.error(f"Mock data acquisition failed: {str(e)}")
            logger.error("=" * 60)
            logger.error("MOCK DATA ACQUISITION FAILED")
            logger.error("=" * 60)
            return False


def main():
    """Main execution function."""
    agent = MockDataAcquisitionAgent()
    success = agent.run_complete_acquisition()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()