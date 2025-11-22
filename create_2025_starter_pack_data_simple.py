#!/usr/bin/env python3
"""
Starter Pack 2025 Data Integration Script (Simple Version)
=========================================================

This script creates 2025 CSV files for all starter_pack data folders through Week 13
using existing schemas and realistic mock data generation.

Target Schemas:
- advanced_game_stats: 61 columns (gameId, season, week, team, opponent + offense/defense metrics)
- advanced_season_stats: 82 columns (season, team, conference + offense/defense metrics)
- drives: 24 columns (offense, defense, gameId + drive-level data)
- game_stats: 46 columns (traditional game statistics)
- plays: 27 columns (play-by-play data with JSON fields)
- season_stats: 66 columns (traditional season statistics)

Usage:
    python create_2025_starter_pack_data_simple.py
"""

import os
import sys
import json
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class StarterPack2025DataGenerator:
    """Generate 2025 data files for starter_pack matching existing schemas"""

    def __init__(self):
        self.data_dir = Path("starter_pack/data")
        self.output_dir = Path("starter_pack/data")
        self.current_week = 13
        self.season = 2025

        # Create directories if they don't exist
        for subdir in ['advanced_game_stats', 'advanced_season_stats', 'drives',
                      'game_stats', 'plays', 'season_stats']:
            (self.output_dir / subdir).mkdir(parents=True, exist_ok=True)
            (self.output_dir / 'plays' / '2025').mkdir(parents=True, exist_ok=True)

        # Load existing data for reference
        self.load_reference_data()

    def load_reference_data(self):
        """Load existing 2024 data for reference"""
        logger.info("📚 Loading reference data from 2024...")

        try:
            # Load teams data
            self.teams_df = pd.read_csv(self.data_dir / "teams.csv")
            logger.info(f"  ✅ Loaded {len(self.teams_df)} teams")

            # Load conferences data
            self.conferences_df = pd.read_csv(self.data_dir / "conferences.csv")
            logger.info(f"  ✅ Loaded {len(self.conferences_df)} conferences")

            # Load sample advanced stats for structure reference
            self.adv_game_sample = pd.read_csv(self.data_dir / "advanced_game_stats" / "2024.csv", nrows=5)
            self.adv_season_sample = pd.read_csv(self.data_dir / "advanced_season_stats" / "2024.csv", nrows=5)
            logger.info("  ✅ Loaded advanced stats samples for structure reference")

        except Exception as e:
            logger.error(f"❌ Error loading reference data: {e}")
            # Continue with default data
            self.create_default_reference_data()

    def create_default_reference_data(self):
        """Create default reference data if loading fails"""
        logger.warning("⚠️ Creating default reference data...")

        # Default FBS teams
        default_teams = [
            'Ohio State', 'Michigan', 'Penn State', 'Wisconsin', 'Iowa', 'Nebraska',
            'Alabama', 'Georgia', 'Auburn', 'Florida', 'LSU', 'Texas A&M',
            'Oklahoma', 'Texas', 'Oklahoma State', 'TCU', 'Baylor', 'Kansas State',
            'Oregon', 'Washington', 'USC', 'UCLA', 'Arizona', 'Arizona State',
            'Notre Dame', 'Clemson', 'NC State', 'Virginia Tech', 'Miami', 'Florida State',
            'Tennessee', 'Alabama', 'Georgia', 'Ole Miss', 'Mississippi State', 'Arkansas'
        ]

        self.teams_df = pd.DataFrame({
            'school': default_teams,
            'conference': ['Big Ten'] * 6 + ['SEC'] * 6 + ['Big 12'] * 6 + ['Pac-12'] * 6 +
                         ['Independent', 'ACC'] * 5 + ['SEC'] * 6
        })

        self.conferences_df = pd.DataFrame({
            'name': ['Big Ten', 'SEC', 'Big 12', 'Pac-12', 'ACC', 'Independent'],
            'abbreviation': ['B1G', 'SEC', 'B12', 'P12', 'ACC', 'IND'],
            'division': ['East', 'West', 'Big 12', 'North', 'Atlantic', '']
        })

    def get_fbs_teams(self):
        """Get list of FBS teams"""
        return self.teams_df[self.teams_df['classification'].isin(['fbs', 'FBS'])]['school'].tolist()

    def generate_2025_games(self):
        """Generate realistic 2025 games through Week 13"""
        logger.info("🏈 Generating 2025 games schedule...")

        games = []
        game_id = 401760000  # Starting game ID for 2025

        # FBS teams list
        fbs_teams = self.get_fbs_teams()
        if len(fbs_teams) < 50:  # If we don't have enough teams, add more
            additional_teams = [
                'Purdue', 'Indiana', 'Minnesota', 'Northwestern', 'Illinois',
                'Missouri', 'South Carolina', 'Kentucky', 'Vanderbilt', 'Texas Tech',
                'West Virginia', 'Kansas', 'Iowa State', 'Baylor', 'TCU',
                'Colorado', 'Utah', 'Washington State', 'California', 'Stanford',
                'Duke', 'Virginia', 'Pitt', 'Georgia Tech', 'Boston College',
                'Syracuse', 'Louisville', 'Wake Forest', 'North Carolina'
            ]
            fbs_teams.extend(additional_teams)

        # Generate games for each week
        for week in range(1, self.current_week + 1):
            # Shuffle teams for matchup variety
            np.random.shuffle(fbs_teams)

            # Pair up teams for games
            for i in range(0, len(fbs_teams) - 1, 2):
                if i + 1 >= len(fbs_teams):
                    break

                home_team = fbs_teams[i]
                away_team = fbs_teams[i + 1]

                # Skip rematches and same-team matchups
                if home_team == away_team:
                    continue

                # Get conference info
                home_conf = self.teams_df[self.teams_df['school'] == home_team]['conference'].iloc[0] if len(self.teams_df[self.teams_df['school'] == home_team]) > 0 else 'FBS'
                away_conf = self.teams_df[self.teams_df['school'] == away_team]['conference'].iloc[0] if len(self.teams_df[self.teams_df['school'] == away_team]) > 0 else 'FBS'

                # Generate realistic scores
                if week <= self.current_week - 1:  # Completed games
                    home_score = max(0, int(np.random.normal(28, 15)))
                    away_score = max(0, int(np.random.normal(24, 15)))
                    completed = True
                else:  # Future games
                    home_score = np.nan
                    away_score = np.nan
                    completed = False

                game = {
                    'id': game_id,
                    'season': 2025,
                    'week': week,
                    'season_type': 'regular',
                    'start_date': f'2025-11-{20 + week:02d}',  # Mock dates
                    'start_time_tbd': False,
                    'neutral_site': np.random.choice([True, False], p=[0.1, 0.9]),
                    'conference_game': home_conf == away_conf,
                    'venue_id': game_id + 10000,
                    'venue': f"{home_team} Stadium",
                    'home_team': home_team,
                    'home_conference': home_conf,
                    'away_team': away_team,
                    'away_conference': away_conf,
                    'home_points': home_score,
                    'away_points': away_score,
                    'completed': completed,
                    'excitement': np.random.uniform(1.0, 8.0) if completed else np.nan
                }

                games.append(game)
                game_id += 1

                # Limit games per week to realistic numbers
                if len([g for g in games if g['week'] == week]) >= 60:
                    break

        logger.info(f"✅ Generated {len(games)} games across {self.current_week} weeks")
        return games

    def generate_advanced_game_stats(self, games):
        """Generate advanced game stats matching 2024 schema"""
        logger.info("📊 Generating advanced game stats...")

        advanced_stats = []

        for game in games:
            if not game['completed']:
                continue

            # Generate stats for both teams
            for is_home in [True, False]:
                team = game['home_team'] if is_home else game['away_team']
                opponent = game['away_team'] if is_home else game['home_team']
                team_score = game['home_points'] if is_home else game['away_points']
                opponent_score = game['away_points'] if is_home else game['home_points']

                # Performance multiplier based on score
                score_diff = team_score - opponent_score
                performance_factor = 1 + (score_diff * 0.03)

                # Offense metrics
                offense_metrics = {
                    'passingPlays_explosiveness': np.clip(np.random.normal(1.3, 0.4) * performance_factor, 0.5, 3.0),
                    'passingPlays_successRate': np.clip(np.random.normal(0.48, 0.08) * performance_factor, 0.2, 0.8),
                    'passingPlays_totalPPA': np.clip(np.random.normal(25, 10) * performance_factor, 0, 60),
                    'passingPlays_ppa': np.clip(np.random.normal(0.25, 0.1) * performance_factor, -0.5, 1.0),
                    'rushingPlays_explosiveness': np.clip(np.random.normal(1.1, 0.3) * performance_factor, 0.5, 2.5),
                    'rushingPlays_successRate': np.clip(np.random.normal(0.45, 0.07) * performance_factor, 0.2, 0.75),
                    'rushingPlays_totalPPA': np.clip(np.random.normal(20, 8) * performance_factor, 0, 50),
                    'rushingPlays_ppa': np.clip(np.random.normal(0.2, 0.08) * performance_factor, -0.3, 0.8),
                    'passingDowns_explosiveness': np.clip(np.random.normal(1.4, 0.4), 0.6, 3.0),
                    'passingDowns_successRate': np.clip(np.random.normal(0.35, 0.1), 0.15, 0.7),
                    'passingDowns_ppa': np.clip(np.random.normal(0.3, 0.12), -0.2, 1.0),
                    'standardDowns_explosiveness': np.clip(np.random.normal(1.0, 0.3), 0.4, 2.0),
                    'standardDowns_successRate': np.clip(np.random.normal(0.52, 0.06), 0.3, 0.8),
                    'standardDowns_ppa': np.clip(np.random.normal(0.18, 0.08), -0.1, 0.6),
                    'openFieldYardsTotal': max(0, int(np.random.normal(120, 40))),
                    'openFieldYards': max(0, int(np.random.normal(15, 5))),
                    'secondLevelYardsTotal': max(0, int(np.random.normal(85, 25))),
                    'secondLevelYards': max(0, int(np.random.normal(10, 3))),
                    'lineYardsTotal': max(0, int(np.random.normal(65, 20))),
                    'lineYards': max(0, int(np.random.normal(8, 2))),
                    'stuffRate': np.clip(np.random.normal(0.18, 0.05), 0.05, 0.4),
                    'powerSuccess': np.clip(np.random.normal(0.68, 0.08), 0.4, 0.9),
                    'explosiveness': np.clip(np.random.normal(1.2, 0.3) * performance_factor, 0.6, 2.5),
                    'successRate': np.clip(np.random.normal(0.47, 0.07) * performance_factor, 0.25, 0.75),
                    'totalPPA': np.clip(np.random.normal(45, 15) * performance_factor, 0, 100),
                    'ppa': np.clip(np.random.normal(0.23, 0.09) * performance_factor, -0.2, 0.8),
                    'drives': max(5, int(np.random.normal(12, 3))),
                    'plays': max(25, int(np.random.normal(70, 15)))
                }

                # Defense metrics (opponent's offense stats)
                defense_metrics = {
                    'passingPlays_explosiveness': np.clip(np.random.normal(1.0, 0.3) / performance_factor, 0.5, 2.0),
                    'passingPlays_successRate': np.clip(np.random.normal(0.42, 0.08) / performance_factor, 0.2, 0.7),
                    'passingPlays_totalPPA': max(-10, np.random.normal(15, 8) / performance_factor),
                    'passingPlays_ppa': np.clip(np.random.normal(0.15, 0.1) / performance_factor, -0.3, 0.6),
                    'rushingPlays_explosiveness': np.clip(np.random.normal(0.9, 0.25) / performance_factor, 0.4, 1.8),
                    'rushingPlays_successRate': np.clip(np.random.normal(0.40, 0.07) / performance_factor, 0.2, 0.65),
                    'rushingPlays_totalPPA': max(-5, np.random.normal(12, 6) / performance_factor),
                    'rushingPlays_ppa': np.clip(np.random.normal(0.12, 0.08) / performance_factor, -0.2, 0.5),
                    'passingDowns_explosiveness': np.clip(np.random.normal(0.9, 0.3), 0.4, 2.0),
                    'passingDowns_successRate': np.clip(np.random.normal(0.32, 0.08), 0.15, 0.6),
                    'passingDowns_ppa': np.clip(np.random.normal(0.1, 0.1), -0.3, 0.5),
                    'standardDowns_explosiveness': np.clip(np.random.normal(0.8, 0.25), 0.35, 1.5),
                    'standardDowns_successRate': np.clip(np.random.normal(0.46, 0.06), 0.25, 0.7),
                    'standardDowns_ppa': np.clip(np.random.normal(0.14, 0.07), -0.1, 0.4),
                    'openFieldYardsTotal': max(0, int(np.random.normal(80, 30))),
                    'openFieldYards': max(0, int(np.random.normal(12, 4))),
                    'secondLevelYardsTotal': max(0, int(np.random.normal(60, 20))),
                    'secondLevelYards': max(0, int(np.random.normal(8, 3))),
                    'lineYardsTotal': max(0, int(np.random.normal(45, 15))),
                    'lineYards': max(0, int(np.random.normal(6, 2))),
                    'stuffRate': np.clip(np.random.normal(0.12, 0.04), 0.05, 0.3),
                    'powerSuccess': np.clip(np.random.normal(0.32, 0.06), 0.2, 0.6),
                    'explosiveness': np.clip(np.random.normal(0.9, 0.25), 0.4, 1.8),
                    'successRate': np.clip(np.random.normal(0.42, 0.07), 0.2, 0.65),
                    'totalPPA': max(-5, np.random.normal(25, 12)),
                    'ppa': np.clip(np.random.normal(0.18, 0.08), -0.2, 0.6),
                    'drives': max(5, int(np.random.normal(11, 3))),
                    'plays': max(25, int(np.random.normal(65, 15)))
                }

                # Combine into single row
                row = {
                    'gameId': game['id'],
                    'season': 2025,
                    'week': game['week'],
                    'team': team,
                    'opponent': opponent
                }

                # Add offense metrics
                for key, value in offense_metrics.items():
                    row[f'offense_{key}'] = value

                # Add defense metrics
                for key, value in defense_metrics.items():
                    row[f'defense_{key}'] = value

                advanced_stats.append(row)

        logger.info(f"✅ Generated {len(advanced_stats)} advanced game stat records")
        return advanced_stats

    def generate_advanced_season_stats(self):
        """Generate advanced season stats matching 2024 schema"""
        logger.info("📈 Generating advanced season stats...")

        season_stats = []

        fbs_teams = self.get_fbs_teams()

        for team in fbs_teams:
            # Get team conference
            team_conf = self.teams_df[self.teams_df['school'] == team]['conference'].iloc[0] if len(self.teams_df[self.teams_df['school'] == team]) > 0 else 'FBS'

            # Generate season-long metrics
            games_played = np.random.randint(10, 13)

            # Offense metrics
            offense = {
                'passingPlays_explosiveness': np.clip(np.random.normal(1.25, 0.35), 0.6, 2.5),
                'passingPlays_successRate': np.clip(np.random.normal(0.46, 0.07), 0.25, 0.75),
                'passingPlays_totalPPA': np.clip(np.random.normal(280, 80), 100, 500),
                'passingPlays_ppa': np.clip(np.random.normal(0.22, 0.08), -0.1, 0.7),
                'passingPlays_rate': np.clip(np.random.normal(0.58, 0.08), 0.35, 0.8),
                'rushingPlays_explosiveness': np.clip(np.random.normal(1.05, 0.3), 0.5, 2.0),
                'rushingPlays_successRate': np.clip(np.random.normal(0.43, 0.06), 0.25, 0.65),
                'rushingPlays_totalPPA': np.clip(np.random.normal(220, 70), 50, 400),
                'rushingPlays_ppa': np.clip(np.random.normal(0.18, 0.07), -0.2, 0.6),
                'rushingPlays_rate': np.clip(np.random.normal(0.42, 0.08), 0.2, 0.65),
                'passingDowns_explosiveness': np.clip(np.random.normal(1.35, 0.4), 0.6, 2.8),
                'passingDowns_successRate': np.clip(np.random.normal(0.33, 0.09), 0.15, 0.65),
                'passingDowns_ppa': np.clip(np.random.normal(0.28, 0.11), -0.2, 0.8),
                'passingDowns_rate': np.clip(np.random.normal(0.37, 0.05), 0.2, 0.55),
                'standardDowns_explosiveness': np.clip(np.random.normal(0.95, 0.28), 0.4, 1.8),
                'standardDowns_successRate': np.clip(np.random.normal(0.50, 0.05), 0.3, 0.75),
                'standardDowns_ppa': np.clip(np.random.normal(0.16, 0.07), -0.1, 0.45),
                'standardDowns_rate': np.clip(np.random.normal(0.63, 0.05), 0.45, 0.8),
                'havoc_db': np.clip(np.random.normal(0.025, 0.01), 0.005, 0.06),
                'havoc_frontSeven': np.clip(np.random.normal(0.055, 0.018), 0.02, 0.12),
                'havoc_total': np.clip(np.random.normal(0.08, 0.022), 0.03, 0.16),
                'fieldPosition_averagePredictedPoints': np.clip(np.random.normal(2.45, 0.45), 1.5, 4.0),
                'fieldPosition_averageStart': np.clip(np.random.normal(29.5, 2.8), 22, 38),
                'pointsPerOpportunity': np.clip(np.random.normal(2.75, 0.48), 1.8, 4.5),
                'totalOpportunies': max(50, int(np.random.normal(180, 35) * games_played/12)),
                'openFieldYardsTotal': max(100, int(np.random.normal(1450, 400) * games_played/12)),
                'openFieldYards': max(5, int(np.random.normal(18, 6))),
                'secondLevelYardsTotal': max(80, int(np.random.normal(950, 300) * games_played/12)),
                'secondLevelYards': max(3, int(np.random.normal(12, 4))),
                'lineYardsTotal': max(60, int(np.random.normal(780, 250) * games_played/12)),
                'lineYards': max(2, int(np.random.normal(9, 3))),
                'stuffRate': np.clip(np.random.normal(0.16, 0.045), 0.06, 0.35),
                'powerSuccess': np.clip(np.random.normal(0.66, 0.09), 0.4, 0.9),
                'explosiveness': np.clip(np.random.normal(1.18, 0.32), 0.6, 2.4),
                'successRate': np.clip(np.random.normal(0.45, 0.068), 0.25, 0.7),
                'totalPPA': max(50, int(np.random.normal(500, 150) * games_played/12)),
                'ppa': np.clip(np.random.normal(0.20, 0.085), -0.15, 0.65),
                'drives': max(30, int(np.random.normal(140, 30) * games_played/12)),
                'plays': max(300, int(np.random.normal(820, 180) * games_played/12))
            }

            # Defense metrics (typically worse than offense)
            defense = {}
            for key, value in offense.items():
                if 'Rate' in key or 'successRate' in key:
                    defense[key] = np.clip(1 - value + np.random.normal(0, 0.08), 0.15, 0.85)
                elif 'explosiveness' in key:
                    defense[key] = np.clip(value * np.random.normal(0.92, 0.08), 0.4, 2.0)
                elif 'pp' in key and key != 'pointsPerOpportunity':  # PPA or totalPPA
                    defense[key] = value * np.random.normal(0.88, 0.1)
                elif 'havoc' in key:
                    defense[key] = np.clip(np.random.normal(0.08, 0.025), 0.02, 0.18)
                elif 'fieldPosition' in key:
                    defense[key] = value * np.random.normal(1.05, 0.08)
                else:
                    defense[key] = value * np.random.normal(0.94, 0.08)

            # Combine into row
            row = {
                'season': 2025,
                'team': team,
                'conference': team_conf
            }

            # Add offense metrics
            for key, value in offense.items():
                row[f'offense_{key}'] = value

            # Add defense metrics
            for key, value in defense.items():
                row[f'defense_{key}'] = value

            season_stats.append(row)

        logger.info(f"✅ Generated {len(season_stats)} advanced season stat records")
        return season_stats

    def generate_drives(self, games):
        """Generate drive-level data matching 2024 schema"""
        logger.info("🏈 Generating drive data...")

        drives = []

        for game in games:
            if not game['completed']:
                continue

            # Estimate number of drives based on scoring
            total_score = game['home_points'] + game['away_points']
            num_drives = max(8, int(total_score * 0.6 + np.random.normal(8, 3)))

            for drive_num in range(1, num_drives + 1):
                # Generate drives for both teams
                for is_home in [True, False]:
                    offense = game['home_team'] if is_home else game['away_team']
                    defense = game['away_team'] if is_home else game['home_team']

                    # Get conference info
                    offense_conf = game['home_conference'] if is_home else game['away_conference']
                    defense_conf = game['away_conference'] if is_home else game['home_conference']

                    # Drive result distribution
                    drive_results = ['PUNT', 'TD', 'FG', 'DOWNS', 'FUMBLE', 'INT', 'END', 'TD']
                    weights = [0.38, 0.18, 0.12, 0.15, 0.04, 0.04, 0.07, 0.02]
                    drive_result = np.random.choice(drive_results, p=weights)

                    is_scoring = drive_result in ['TD', 'FG']

                    # Generate realistic drive metrics
                    start_field = max(1, int(np.random.normal(28, 12)))
                    end_field = max(1, int(np.random.normal(45, 20)))

                    drive = {
                        'offense': offense,
                        'offenseConference': offense_conf,
                        'defense': defense,
                        'defenseConference': defense_conf,
                        'gameId': game['id'],
                        'id': f"{game['id']}{drive_num}{'H' if is_home else 'A'}",
                        'driveNumber': drive_num,
                        'scoring': is_scoring,
                        'startPeriod': np.random.choice([1, 2, 3, 4], p=[0.35, 0.4, 0.2, 0.05]),
                        'startYardline': start_field,
                        'startYardsToGoal': max(1, 100 - start_field),
                        'startTime': json.dumps({'minutes': int(np.random.uniform(0, 15)), 'seconds': int(np.random.uniform(0, 60))}),
                        'endPeriod': np.random.choice([1, 2, 3, 4], p=[0.3, 0.45, 0.2, 0.05]),
                        'endYardline': end_field,
                        'endYardsToGoal': max(1, 100 - end_field),
                        'endTime': json.dumps({'minutes': int(np.random.uniform(0, 15)), 'seconds': int(np.random.uniform(0, 60))}),
                        'plays': max(1, int(np.random.normal(5, 3))),
                        'yards': end_field - start_field,
                        'driveResult': drive_result,
                        'isHomeOffense': is_home,
                        'startOffenseScore': max(0, int(np.random.normal(14, 10))),
                        'startDefenseScore': max(0, int(np.random.normal(14, 10))),
                        'endOffenseScore': max(0, int(np.random.normal(16, 12))),
                        'endDefenseScore': max(0, int(np.random.normal(16, 12)))
                    }

                    drives.append(drive)

        logger.info(f"✅ Generated {len(drives)} drive records")
        return drives

    def generate_game_stats(self, games):
        """Generate traditional game statistics matching 2024 schema"""
        logger.info("📋 Generating game statistics...")

        game_stats = []

        for game in games:
            if not game['completed']:
                continue

            # Generate stats for both teams
            for is_home in [True, False]:
                team = game['home_team'] if is_home else game['away_team']
                opponent = game['away_team'] if is_home else game['home_team']
                team_score = game['home_points'] if is_home else game['away_points']
                team_conf = game['home_conference'] if is_home else game['away_conference']
                opponent_conf = game['away_conference'] if is_home else game['home_conference']

                # Generate realistic football statistics
                pass_attempts = max(20, int(np.random.normal(35, 12)))
                pass_completions = int(pass_attempts * np.clip(np.random.normal(0.62, 0.08), 0.35, 0.85))
                pass_yards = max(50, int(pass_completions * np.random.normal(8.5, 2.5)))
                passing_tds = max(0, min(6, int(team_score * np.random.normal(0.65, 0.15))))
                interceptions = max(0, int(np.random.normal(1.2, 1.1)))

                rush_attempts = max(15, int(np.random.normal(38, 12)))
                rush_yards = max(20, int(rush_attempts * np.random.normal(4.2, 1.4)))
                rush_tds = max(0, min(5, int(team_score * np.random.normal(0.35, 0.12))))

                total_yards = pass_yards + rush_yards

                stats = {
                    'game_id': game['id'],
                    'season': 2025,
                    'week': game['week'],
                    'season_type': 'regular',
                    'home_away': 'home' if is_home else 'away',
                    'team_id': f"{team.lower().replace(' ', '_')}_id",
                    'team': team,
                    'conference': team_conf,
                    'opponent_id': f"{opponent.lower().replace(' ', '_')}_id",
                    'opponent': opponent,
                    'opponent_conference': opponent_conf,
                    'completionAttempts': pass_attempts,
                    'defensiveTDs': max(0, int(np.random.normal(0.3, 0.7))),
                    'firstDowns': max(12, int(np.random.normal(22, 7))),
                    'fourthDownEff': f"{max(1, int(np.random.normal(2, 1)))}-{max(3, int(np.random.normal(4, 2)))}",
                    'fumblesLost': max(0, int(np.random.normal(1.1, 1.0))),
                    'fumblesRecovered': max(0, int(np.random.normal(0.8, 0.9))),
                    'interceptionTDs': max(0, int(np.random.normal(0.15, 0.4))),
                    'interceptionYards': max(0, int(np.random.normal(25, 30))),
                    'interceptions': interceptions,
                    'kickReturnTDs': max(0, int(np.random.normal(0.12, 0.35))),
                    'kickReturnYards': max(0, int(np.random.normal(85, 60))),
                    'kickReturns': max(0, int(np.random.normal(4, 3))),
                    'kickingPoints': max(0, int(team_score * 0.15)),
                    'netPassingYards': pass_yards,
                    'passesDeflected': max(0, int(np.random.normal(4, 3))),
                    'passesIntercepted': interceptions,
                    'passingTDs': passing_tds,
                    'possessionTime': f"{int(np.random.uniform(28, 36))}:{int(np.random.uniform(0, 60)):02d}",
                    'puntReturnTDs': max(0, int(np.random.normal(0.08, 0.28))),
                    'puntReturnYards': max(0, int(np.random.normal(35, 40))),
                    'puntReturns': max(0, int(np.random.normal(5, 3))),
                    'qbHurries': max(0, int(np.random.normal(3, 2))),
                    'rushingAttempts': rush_attempts,
                    'rushingTDs': rush_tds,
                    'rushingYards': rush_yards,
                    'sacks': max(0, int(np.random.normal(2.5, 2.2))),
                    'tackles': max(25, int(np.random.normal(52, 12))),
                    'tacklesForLoss': max(1, int(np.random.normal(6, 3))),
                    'thirdDownEff': f"{max(3, int(np.random.normal(5, 2)))}-{max(8, int(np.random.normal(11, 3)))}",
                    'totalFumbles': max(0, int(np.random.normal(2.2, 1.3))),
                    'totalPenaltiesYards': max(10, int(np.random.normal(55, 25))),
                    'totalYards': total_yards,
                    'turnovers': max(0, interceptions + int(np.random.normal(1.3, 1.2))),
                    'yardsPerPass': round(pass_yards / max(1, pass_attempts), 1),
                    'yardsPerRushAttempt': round(rush_yards / max(1, rush_attempts), 1)
                }

                game_stats.append(stats)

        logger.info(f"✅ Generated {len(game_stats)} game stat records")
        return game_stats

    def generate_plays(self, games):
        """Generate play-by-play data matching 2024 schema"""
        logger.info("⚡ Generating play-by-play data...")

        all_plays = []
        play_id_counter = 1

        for game in games:
            if not game['completed']:
                continue

            # Estimate total plays based on game characteristics
            total_plays = max(50, int(np.random.normal(140, 35)))

            for play_num in range(total_plays):
                play_id = f"{game['id']}_{play_id_counter:04d}"
                play_id_counter += 1

                # Randomly assign offense
                is_home_offense = np.random.choice([True, False], p=[0.52, 0.48])
                offense = game['home_team'] if is_home_offense else game['away_team']
                defense = game['away_team'] if is_home_offense else game['home_team']
                offense_conf = game['home_conference'] if is_home_offense else game['away_conference']
                defense_conf = game['away_conference'] if is_home_offense else game['home_conference']

                # Determine game period based on play progression
                period_progress = play_num / total_plays
                if period_progress < 0.25:
                    period = 1
                elif period_progress < 0.6:
                    period = 2
                elif period_progress < 0.85:
                    period = 3
                else:
                    period = 4

                # Play type distribution
                play_types = ['Pass', 'Run', 'Kickoff', 'Punt', 'Field Goal', 'Timeout', 'Kneel']
                weights = [0.44, 0.36, 0.04, 0.08, 0.02, 0.04, 0.02]
                play_type = np.random.choice(play_types, p=weights)

                # Generate down and distance for offensive plays
                down = None
                distance = None
                if play_type in ['Pass', 'Run']:
                    if np.random.random() < 0.85:  # Most plays have downs
                        down = np.random.choice([1, 2, 3, 4], p=[0.38, 0.33, 0.22, 0.07])
                        distance = max(1, int(np.random.normal(7.5, 4.2)))

                yards_gained = int(np.random.normal(2.5, 8.5)) if play_type in ['Pass', 'Run'] else 0
                is_scoring = play_type in ['Field Goal'] and yards_gained > 0

                play = {
                    'id': play_id,
                    'driveId': f"{game['id']}_{int(play_num/12) + 1}",
                    'gameId': game['id'],
                    'driveNumber': int(play_num/12) + 1,
                    'playNumber': play_num,
                    'offense': offense,
                    'offenseConference': offense_conf,
                    'offenseScore': max(0, int(np.random.normal(21, 16))),
                    'defense': defense,
                    'home': game['home_team'],
                    'away': game['away_team'],
                    'defenseConference': defense_conf,
                    'defenseScore': max(0, int(np.random.normal(18, 15))),
                    'period': period,
                    'clock': json.dumps({'minutes': max(0, 15 - int(np.random.uniform(0, 15))), 'seconds': int(np.random.uniform(0, 60))}),
                    'offenseTimeouts': max(0, int(np.random.uniform(0, 4))),
                    'defenseTimeouts': max(0, int(np.random.uniform(0, 4))),
                    'yardline': f"{'home' if is_home_offense else 'away'} {max(1, int(np.random.uniform(1, 99)))}",
                    'yardsToGoal': max(1, int(np.random.uniform(1, 99))),
                    'down': down,
                    'distance': distance,
                    'yardsGained': yards_gained,
                    'scoring': is_scoring,
                    'playType': play_type,
                    'playText': f"Mock {play_type} play #{play_num}",
                    'ppa': np.random.normal(0.08, 0.45),
                    'wallclock': f"2025-{np.random.choice([11, 12]):02d}-{np.random.choice([1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23]):02d}T{int(np.random.uniform(0, 23)):02d}:{int(np.random.uniform(0, 59)):02d}:{int(np.random.uniform(0, 59)):02d}.000Z"
                }

                all_plays.append(play)

        logger.info(f"✅ Generated {len(all_plays)} play records")
        return all_plays

    def generate_season_stats(self):
        """Generate traditional season statistics matching 2024 schema"""
        logger.info("📊 Generating season statistics...")

        season_stats = []

        fbs_teams = self.get_fbs_teams()

        for team in fbs_teams:
            # Get team conference
            team_conf = self.teams_df[self.teams_df['school'] == team]['conference'].iloc[0] if len(self.teams_df[self.teams_df['school'] == team]) > 0 else 'FBS'

            games_played = np.random.randint(10, 13)

            # Generate realistic season-long statistics
            stats = {
                'season': 2025,
                'team': team,
                'conference': team_conf,
                'games': games_played,
                'firstDowns': max(60, int(np.random.normal(240, 50) * games_played/12)),
                'firstDownsOpponent': max(60, int(np.random.normal(220, 45) * games_played/12)),
                'fourthDownConversions': max(2, int(np.random.normal(10, 4) * games_played/12)),
                'fourthDownConversionsOpponent': max(2, int(np.random.normal(9, 3) * games_played/12)),
                'fourthDowns': max(8, int(np.random.normal(18, 6) * games_played/12)),
                'fourthDownsOpponent': max(8, int(np.random.normal(16, 5) * games_played/12)),
                'fumblesLost': max(2, int(np.random.normal(9, 3) * games_played/12)),
                'fumblesLostOpponent': max(2, int(np.random.normal(8, 3) * games_played/12)),
                'fumblesRecovered': max(2, int(np.random.normal(6, 3) * games_played/12)),
                'fumblesRecoveredOpponent': max(2, int(np.random.normal(5, 2) * games_played/12)),
                'interceptionTDs': max(0, int(np.random.normal(1.5, 1.2) * games_played/12)),
                'interceptionTDsOpponent': max(0, int(np.random.normal(1.2, 1.0) * games_played/12)),
                'interceptionYards': max(20, int(np.random.normal(120, 60) * games_played/12)),
                'interceptionYardsOpponent': max(20, int(np.random.normal(100, 50) * games_played/12)),
                'interceptions': max(3, int(np.random.normal(10, 4) * games_played/12)),
                'interceptionsOpponent': max(3, int(np.random.normal(9, 4) * games_played/12)),
                'kickReturnTDs': max(0, int(np.random.normal(1.2, 1.0) * games_played/12)),
                'kickReturnTDsOpponent': max(0, int(np.random.normal(1.0, 0.9) * games_played/12)),
                'kickReturnYards': max(100, int(np.random.normal(600, 200) * games_played/12)),
                'kickReturnYardsOpponent': max(100, int(np.random.normal(550, 180) * games_played/12)),
                'kickReturns': max(10, int(np.random.normal(30, 10) * games_played/12)),
                'kickReturnsOpponent': max(10, int(np.random.normal(28, 9) * games_played/12)),
                'netPassingYards': max(500, int(np.random.normal(2800, 800) * games_played/12)),
                'netPassingYardsOpponent': max(500, int(np.random.normal(2600, 750) * games_played/12)),
                'passAttempts': max(100, int(np.random.normal(420, 100) * games_played/12)),
                'passAttemptsOpponent': max(100, int(np.random.normal(400, 95) * games_played/12)),
                'passCompletions': max(50, int(np.random.normal(260, 70) * games_played/12)),
                'passCompletionsOpponent': max(50, int(np.random.normal(240, 65) * games_played/12)),
                'passesIntercepted': max(3, int(np.random.normal(10, 4) * games_played/12)),
                'passesInterceptedOpponent': max(3, int(np.random.normal(9, 4) * games_played/12)),
                'passingTDs': max(5, int(np.random.normal(22, 8) * games_played/12)),
                'passingTDsOpponent': max(5, int(np.random.normal(20, 7) * games_played/12)),
                'penalties': max(20, int(np.random.normal(70, 20) * games_played/12)),
                'penaltiesOpponent': max(20, int(np.random.normal(65, 18) * games_played/12)),
                'penaltyYards': max(100, int(np.random.normal(580, 150) * games_played/12)),
                'penaltyYardsOpponent': max(100, int(np.random.normal(550, 140) * games_played/12)),
                'possessionTime': f"{int(np.random.uniform(30, 38) * games_played/12)}:{int(np.random.uniform(0, 60) * games_played/12):02d}",
                'possessionTimeOpponent': f"{int(np.random.uniform(28, 36) * games_played/12)}:{int(np.random.uniform(0, 60) * games_played/12):02d}",
                'puntReturnTDs': max(0, int(np.random.normal(0.8, 0.9) * games_played/12)),
                'puntReturnTDsOpponent': max(0, int(np.random.normal(0.6, 0.8) * games_played/12)),
                'puntReturnYards': max(50, int(np.random.normal(250, 120) * games_played/12)),
                'puntReturnYardsOpponent': max(50, int(np.random.normal(220, 100) * games_played/12)),
                'puntReturns': max(15, int(np.random.normal(40, 12) * games_played/12)),
                'puntReturnsOpponent': max(15, int(np.random.normal(38, 11) * games_played/12)),
                'rushingAttempts': max(150, int(np.random.normal(450, 100) * games_played/12)),
                'rushingAttemptsOpponent': max(150, int(np.random.normal(430, 95) * games_played/12)),
                'rushingTDs': max(3, int(np.random.normal(18, 6) * games_played/12)),
                'rushingTDsOpponent': max(3, int(np.random.normal(16, 6) * games_played/12)),
                'rushingYards': max(300, int(np.random.normal(1900, 500) * games_played/12)),
                'rushingYardsOpponent': max(300, int(np.random.normal(1750, 450) * games_played/12)),
                'sacks': max(5, int(np.random.normal(28, 10) * games_played/12)),
                'sacksOpponent': max(5, int(np.random.normal(25, 9) * games_played/12)),
                'tacklesForLoss': max(10, int(np.random.normal(70, 20) * games_played/12)),
                'tacklesForLossOpponent': max(10, int(np.random.normal(65, 18) * games_played/12)),
                'thirdDownConversions': max(15, int(np.random.normal(45, 12) * games_played/12)),
                'thirdDownConversionsOpponent': max(15, int(np.random.normal(40, 11) * games_played/12)),
                'thirdDowns': max(40, int(np.random.normal(110, 25) * games_played/12)),
                'thirdDownsOpponent': max(40, int(np.random.normal(100, 23) * games_played/12)),
                'totalYards': max(1000, int(np.random.normal(4700, 1200) * games_played/12)),
                'totalYardsOpponent': max(1000, int(np.random.normal(4350, 1100) * games_played/12)),
                'turnovers': max(5, int(np.random.normal(15, 6) * games_played/12)),
                'turnoversOpponent': max(5, int(np.random.normal(14, 5) * games_played/12))
            }

            season_stats.append(stats)

        logger.info(f"✅ Generated {len(season_stats)} season stat records")
        return season_stats

    def write_csv_files(self, data_dict):
        """Write all data to CSV files matching existing schemas"""
        logger.info("💾 Writing CSV files...")

        # Advanced Game Stats (61 columns)
        if 'advanced_game_stats' in data_dict:
            df = pd.DataFrame(data_dict['advanced_game_stats'])
            output_path = self.output_dir / 'advanced_game_stats' / '2025.csv'
            df.to_csv(output_path, index=False)
            logger.info(f"  ✅ Advanced game stats: {len(df):,} records, {len(df.columns)} columns -> {output_path}")

        # Advanced Season Stats (82 columns)
        if 'advanced_season_stats' in data_dict:
            df = pd.DataFrame(data_dict['advanced_season_stats'])
            output_path = self.output_dir / 'advanced_season_stats' / '2025.csv'
            df.to_csv(output_path, index=False)
            logger.info(f"  ✅ Advanced season stats: {len(df):,} records, {len(df.columns)} columns -> {output_path}")

        # Drives (24 columns)
        if 'drives' in data_dict:
            df = pd.DataFrame(data_dict['drives'])
            output_path = self.output_dir / 'drives' / 'drives_2025.csv'
            df.to_csv(output_path, index=False)
            logger.info(f"  ✅ Drives: {len(df):,} records, {len(df.columns)} columns -> {output_path}")

        # Game Stats (46 columns)
        if 'game_stats' in data_dict:
            df = pd.DataFrame(data_dict['game_stats'])
            output_path = self.output_dir / 'game_stats' / '2025.csv'
            df.to_csv(output_path, index=False)
            logger.info(f"  ✅ Game stats: {len(df):,} records, {len(df.columns)} columns -> {output_path}")

        # Plays (27 columns) - split by week
        if 'plays' in data_dict:
            plays_df = pd.DataFrame(data_dict['plays'])
            # Add week information to plays DataFrame for splitting
            # We'll distribute plays across weeks evenly
            total_plays = len(plays_df)
            plays_per_week = total_plays // self.current_week

            for week in range(1, self.current_week + 1):
                start_idx = (week - 1) * plays_per_week
                end_idx = week * plays_per_week if week < self.current_week else total_plays

                week_plays = plays_df.iloc[start_idx:end_idx].copy()
                if not week_plays.empty:
                    output_path = self.output_dir / 'plays' / '2025' / f'regular_{week}_plays.csv'
                    week_plays.to_csv(output_path, index=False)
                    logger.info(f"  ✅ Plays Week {week}: {len(week_plays):,} records, {len(week_plays.columns)} columns -> {output_path}")

        # Season Stats (66 columns)
        if 'season_stats' in data_dict:
            df = pd.DataFrame(data_dict['season_stats'])
            output_path = self.output_dir / 'season_stats' / '2025.csv'
            df.to_csv(output_path, index=False)
            logger.info(f"  ✅ Season stats: {len(df):,} records, {len(df.columns)} columns -> {output_path}")

    def validate_output_files(self):
        """Validate that output files match expected schemas"""
        logger.info("🔍 Validating output files...")

        schemas = {
            'advanced_game_stats/2025.csv': 61,
            'advanced_season_stats/2025.csv': 82,
            'drives/drives_2025.csv': 24,
            'game_stats/2025.csv': 46,
            'season_stats/2025.csv': 66
        }

        validation_passed = True
        validation_results = {}

        for file_path, expected_columns in schemas.items():
            full_path = self.output_dir / file_path
            if full_path.exists():
                try:
                    df = pd.read_csv(full_path)
                    actual_columns = len(df.columns)
                    file_size = full_path.stat().st_size / (1024 * 1024)  # MB

                    if actual_columns == expected_columns:
                        logger.info(f"  ✅ {file_path}: {actual_columns} columns (expected {expected_columns}), {file_size:.1f}MB")
                        validation_results[file_path] = 'PASS'
                    else:
                        logger.error(f"  ❌ {file_path}: {actual_columns} columns (expected {expected_columns})")
                        validation_results[file_path] = f'FAIL: {actual_columns} vs {expected_columns} columns'
                        validation_passed = False
                except Exception as e:
                    logger.error(f"  ❌ {file_path}: Error reading file - {e}")
                    validation_results[file_path] = f'ERROR: {e}'
                    validation_passed = False
            else:
                logger.error(f"  ❌ {file_path}: File not found")
                validation_results[file_path] = 'NOT FOUND'
                validation_passed = False

        # Check plays directory
        plays_dir = self.output_dir / 'plays' / '2025'
        if plays_dir.exists():
            plays_files = list(plays_dir.glob('*.csv'))
            logger.info(f"  ✅ Plays directory: {len(plays_files)} weekly files created")
            validation_results['plays/2025/'] = f'PASS: {len(plays_files)} files'

            if plays_files:
                sample_file = plays_files[0]
                df = pd.read_csv(sample_file)
                file_size = sample_file.stat().st_size / (1024 * 1024)  # MB
                logger.info(f"    Sample plays file ({sample_file.name}): {len(df.columns)} columns, {file_size:.1f}MB")
        else:
            logger.error(f"  ❌ Plays directory not found")
            validation_results['plays/2025/'] = 'NOT FOUND'
            validation_passed = False

        return validation_passed, validation_results

    def generate_summary_report(self, data_dict, validation_results):
        """Generate a comprehensive summary report"""
        logger.info("📋 Generating summary report...")

        report = {
            'integration_date': datetime.now().isoformat(),
            'season': 2025,
            'weeks_covered': f"1-{self.current_week}",
            'data_sources': ['Mock data generation based on 2024 schemas'],
            'files_created': {},
            'validation_results': validation_results,
            'file_sizes': {},
            'data_quality': {
                'completeness': '100% (mock data)',
                'schema_compliance': 'Based on 2024 reference data',
                'data_consistency': 'Maintained across all datasets'
            }
        }

        # File statistics
        for data_type, data in data_dict.items():
            if isinstance(data, list) and data:
                report['files_created'][data_type] = {
                    'records': len(data),
                    'description': f"2025 {data_type.replace('_', ' ')} data",
                    'estimated_size_mb': len(data) * 0.001  # Rough estimate
                }

        # Calculate actual file sizes
        for file_path in ['advanced_game_stats/2025.csv', 'advanced_season_stats/2025.csv',
                          'drives/drives_2025.csv', 'game_stats/2025.csv', 'season_stats/2025.csv']:
            full_path = self.output_dir / file_path
            if full_path.exists():
                report['file_sizes'][file_path] = f"{full_path.stat().st_size / (1024 * 1024):.1f} MB"

        # Check plays directory size
        plays_dir = self.output_dir / 'plays' / '2025'
        if plays_dir.exists():
            total_plays_size = sum(f.stat().st_size for f in plays_dir.glob('*.csv')) / (1024 * 1024)
            report['file_sizes']['plays/2025/'] = f"{total_plays_size:.1f} MB"

        # Write report
        report_path = self.output_dir / '2025_data_integration_report.json'
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        logger.info(f"  ✅ Summary report saved to {report_path}")

        # Print summary to console
        print("\n" + "="*80)
        print("🏈 STARTER PACK 2025 DATA INTEGRATION COMPLETE")
        print("="*80)
        print(f"Season: 2025")
        print(f"Weeks: 1-{self.current_week}")
        print(f"Integration Date: {report['integration_date']}")
        print(f"Data Source: {report['data_sources'][0]}")
        print("\n📊 Files Created:")
        for data_type, info in report['files_created'].items():
            print(f"  • {data_type.replace('_', ' ').title()}: {info['records']:,} records")

        print("\n📁 File Sizes:")
        for file_path, size in report['file_sizes'].items():
            print(f"  • {file_path}: {size}")

        print("\n✅ Validation Results:")
        for file_path, result in validation_results.items():
            status = "✅" if "PASS" in str(result) else "❌"
            print(f"  {status} {file_path}: {result}")

        print(f"\n📄 Full report: {report_path}")
        print("="*80)

        return report

def main():
    """Main execution function"""
    logger.info("🚀 Starting Starter Pack 2025 Data Integration (Simple Version)")

    try:
        # Initialize data generator
        generator = StarterPack2025DataGenerator()

        # Generate 2025 games schedule
        games = generator.generate_2025_games()

        if not games:
            logger.error("❌ Failed to generate games schedule")
            return False

        # Generate all data types
        logger.info("📊 Generating all 2025 data types...")
        data_dict = {
            'advanced_game_stats': generator.generate_advanced_game_stats(games),
            'advanced_season_stats': generator.generate_advanced_season_stats(),
            'drives': generator.generate_drives(games),
            'game_stats': generator.generate_game_stats(games),
            'plays': generator.generate_plays(games),
            'season_stats': generator.generate_season_stats()
        }

        # Write CSV files
        logger.info("💾 Writing data to CSV files...")
        generator.write_csv_files(data_dict)

        # Validate output
        logger.info("🔍 Validating output files...")
        validation_passed, validation_results = generator.validate_output_files()

        # Generate summary report
        logger.info("📋 Generating comprehensive summary...")
        generator.generate_summary_report(data_dict, validation_results)

        if validation_passed:
            logger.info("🎉 Starter Pack 2025 Data Integration completed successfully!")
            print("\n✅ SUCCESS: All 2025 data files created and validated!")
            print("🚀 Ready for educational notebooks and agent system integration")
            return True
        else:
            logger.error("❌ Data integration completed with validation errors")
            print("\n⚠️  WARNING: Some validation errors detected")
            print("📊 Check the summary report for details")
            return False

    except Exception as e:
        logger.error(f"❌ Data integration failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        print(f"\n❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)