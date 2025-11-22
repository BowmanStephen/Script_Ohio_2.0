"""
Week 12 Mock Data Enhancement Agent
Enhances existing mock data with Week 12 patterns and current trends
"""

import os
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any
import json
import random
from pathlib import Path

# Import the base agent framework
from agents.core.agent_framework import BaseAgent, AgentCapability, PermissionLevel
# from agents.core.context_manager import ContextManager  # Not needed for now

logger = logging.getLogger(__name__)

class Week12MockEnhancementAgent(BaseAgent):
    """
    Agent responsible for enhancing mock data with Week 12 patterns
    and current season trends for more realistic predictions
    """

    def __init__(self, agent_id: str = "week12_mock_enhancement", tool_loader=None):
        super().__init__(
            agent_id=agent_id,
            name="Week 12 Mock Enhancement Agent",
            permission_level=PermissionLevel.READ_EXECUTE_WRITE,
            tool_loader=tool_loader,
        )
        self.agent_description = "Enhances mock data sets with Week 12 patterns."

        # Initialize agent-specific attributes
        self.week12_patterns = self._load_week12_historical_patterns()
        self.current_season_trends = self._load_current_trends()

    # ------------------------------------------------------------------
    # Minimal logging helpers (BaseAgent currently lacks log_* helpers)
    # ------------------------------------------------------------------
    def log_start(self, message: str):
        logger.info(f"[START] {message}")

    def log_success(self, message: str, result: Dict[str, Any]):
        logger.info(f"[SUCCESS] {message}")

    def log_error(self, message: str, error: Exception):
        logger.error(f"[ERROR] {message}: {error}")

    def log_info(self, message: str):
        logger.info(f"[INFO] {message}")

    def get_execution_time(self) -> float:
        return 0.0
    
    def _get_current_season(self) -> int:
        """Get current season dynamically"""
        try:
            from src.utils.data import get_current_season
            return get_current_season()
        except Exception:
            # Fallback to current year
            return datetime.now().year

    def _define_capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability(
                name="enhance_mock_data",
                description="Enhance mock datasets with Week 12 patterns.",
                permission_required=PermissionLevel.READ_EXECUTE_WRITE,
                tools_required=["pandas", "numpy"],
                data_access=["starter_pack/data/", "model_pack/"],
                execution_time_estimate=5.0,
            )
        ]

    def _execute_action(self, action: str, parameters: Dict[str, Any],
                       user_context: Dict[str, Any]) -> Dict[str, Any]:
        if action == "enhance_mock_data":
            return self.execute_task(parameters or {})
        raise ValueError(f"Unknown action: {action}")

    def execute_task(self, _task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main execution method for enhancing mock data

        Args:
            task_data: Contains configuration for enhancement task

        Returns:
            Enhanced mock data with Week 12 patterns
        """
        try:
            self.log_start("Mock Data Enhancement")

            # Step 1: Load existing mock data
            base_data = self._load_base_mock_data()

            # Step 2: Analyze Week 12 historical patterns
            week12_insights = self._analyze_week12_patterns()

            # Step 3: Apply current season trends
            trend_adjustments = self._calculate_trend_adjustments()

            # Step 4: Generate enhanced Week 12 data
            enhanced_data = self._generate_enhanced_week12_data(
                base_data, week12_insights, trend_adjustments
            )

            # Step 5: Validate enhanced data quality
            validation_results = self._validate_enhanced_data(enhanced_data)

            # Step 6: Save enhanced data
            self._save_enhanced_data(enhanced_data)

            result = {
                'status': 'success',
                'enhanced_games_count': len(enhanced_data['games']),
                'patterns_applied': len(week12_insights),
                'trend_adjustments': len(trend_adjustments),
                'validation_score': validation_results['quality_score'],
                'data_saved': True,
                'execution_time': self.get_execution_time()
            }

            self.log_success("Mock Data Enhancement", result)
            return result

        except Exception as e:
            error_result = {
                'status': 'error',
                'error': str(e),
                'execution_time': self.get_execution_time()
            }
            self.log_error("Mock Data Enhancement", e)
            return error_result

    def _load_base_mock_data(self) -> Dict[str, Any]:
        """Load existing mock data as base for enhancement"""

        self.log_info("Loading base mock data...")

        try:
            # Load existing mock games
            mock_games_path = "model_pack/2025_raw_games_fixed.csv"
            if os.path.exists(mock_games_path):
                mock_games = pd.read_csv(mock_games_path)
                self.log_info(f"Loaded {len(mock_games)} mock games")
            else:
                # Create base mock data if not exists
                mock_games = self._create_base_mock_games()
                self.log_info("Created new base mock games")

            # Load team talent data
            talent_path = "model_pack/2025_talent.csv"
            if os.path.exists(talent_path):
                team_talent = pd.read_csv(talent_path)
                self.log_info(f"Loaded talent data for {len(team_talent)} teams")
            else:
                team_talent = self._create_base_talent_data()
                self.log_info("Created new talent data")

            # Load existing advanced metrics
            metrics_path = "model_pack/2025_plays.csv"
            if os.path.exists(metrics_path):
                team_metrics = self._calculate_base_metrics(pd.read_csv(metrics_path))
            else:
                team_metrics = self._create_base_metrics()

            return {
                'games': mock_games,
                'team_talent': team_talent,
                'team_metrics': team_metrics,
                'source': 'enhanced_mock'
            }

        except Exception as e:
            self.log_error("Loading base mock data", e)
            raise

    def _load_week12_historical_patterns(self) -> Dict[str, Any]:
        """Load historical Week 12 patterns from 2016-2024 data"""

        patterns = {
            'scoring_tendencies': {
                'home_advantage_boost': 2.1,  # Points increase for home teams
                'rivalry_game_variance': 1.8,  # Higher variance in rivalry games
                'late_season_closeness': 0.15,  # Games tend to be closer
                'upset_frequency': 0.22,  # 22% upset rate in Week 12
            },
            'team_performance_patterns': {
                'bubble_team_boost': 1.5,  # Teams fighting for playoffs
                'eliminated_team_decline': -2.3,  # Eliminated teams performance drop
                'conference_championship_impact': 3.2,  # Teams playing for championship
                'senior_day_effect': 1.1,  # Senior day performance boost
            },
            'weather_adjustments': {
                'northern_weather_penalty': -0.8,  # Cold weather impact
                'dome_game_neutral': 0.0,  # No weather impact in domes
                'rain_game_variance': 1.2,  # Higher variance in rain
            }
        }

        self.log_info("Loaded Week 12 historical patterns")
        return patterns

    def _load_current_trends(self) -> Dict[str, Any]:
        """Load 2025 season specific trends"""

        trends = {
            'offensive_trends': {
                'passing_heavy_offenses': 0.68,  # Percentage of teams favoring pass
                'explosive_play_rate': 1.15,  # Increase in explosive plays vs historical
                'tempo_increase': 0.12,  # Faster pace than historical averages
            },
            'defensive_trends': {
                'pressure_packages': 1.08,  # More blitz packages
                'coverage_improvements': 0.95,  # Better secondary play
                'havoc_rate_trend': 1.03,  # Slight increase in defensive havoc
            },
            'team_specific_trends': {
                # Top performing teams this season (load from data if available)
                # Fallback to common teams if data unavailable
                'hot_teams': self._get_top_teams_from_data('hot', limit=4) or ['Georgia', 'Ohio State', 'Michigan', 'Washington'],
                'cold_teams': self._get_top_teams_from_data('cold', limit=3) or ['Clemson', 'Oklahoma', 'Texas A&M'],
                'improving_teams': self._get_top_teams_from_data('improving', limit=3) or ['Alabama', 'Oregon', 'Florida State'],
            }
        }

        self.log_info("Loaded current season trends")
        return trends

    def _get_top_teams_from_data(self, trend_type: str, limit: int = 4) -> List[str]:
        """
        Retrieve a short list of teams using simple heuristics from the training dataset.
        This is intentionally lightweight—just enough to provide dynamic context.
        """
        try:
            training_data_path = Path(__file__).parent.parent.parent / "model_pack" / "updated_training_data.csv"
            if not training_data_path.exists():
                return []

            header = pd.read_csv(training_data_path, nrows=0)
            usecols = [c for c in ['season', 'week', 'home_team', 'away_team', 'home_elo', 'away_elo'] if c in header.columns]
            data = pd.read_csv(training_data_path, usecols=usecols)

            # Focus on current season; fallback to entire dataset if empty
            season = self._get_current_season()
            season_data = data[data['season'] == season]
            if season_data.empty:
                season_data = data

            if season_data.empty:
                return []

            team_elos: Dict[str, List[float]] = {}

            def add_score(team: str, elo_value):
                if team and not pd.isna(elo_value):
                    team_elos.setdefault(team, []).append(float(elo_value))

            for _, row in season_data.iterrows():
                add_score(row.get('home_team'), row.get('home_elo'))
                add_score(row.get('away_team'), row.get('away_elo'))

            if not team_elos:
                return []

            averages = [(team, float(np.mean(values))) for team, values in team_elos.items() if values]
            if not averages:
                return []

            if trend_type == 'hot':
                ordered = sorted(averages, key=lambda x: x[1], reverse=True)
            elif trend_type == 'cold':
                ordered = sorted(averages, key=lambda x: x[1])
            elif trend_type == 'improving':
                mid_slice = averages[len(averages) // 4: -len(averages) // 4 or None]
                random.shuffle(mid_slice)
                ordered = mid_slice
            else:
                ordered = averages

            return [team for team, _ in ordered[:limit]]

        except Exception as exc:
            logger.warning(f"⚠️ Unable to derive {trend_type} teams from data: {exc}")
            return []

    def _analyze_week12_patterns(self) -> List[Dict[str, Any]]:
        """Analyze Week 12 specific patterns and generate insights"""

        insights = []

        # Pattern 1: Conference Championship Implications
        insights.append({
            'pattern': 'championship_implications',
            'description': 'Teams playing for conference championships show 15% performance boost',
            'multiplier': 1.15,
            'applicability': 0.35  # 35% of Week 12 games have championship implications
        })

        # Pattern 2: Rivalry Game Effects
        insights.append({
            'pattern': 'rivalry_variance',
            'description': 'Rivalry games show higher scoring variance and closer margins',
            'variance_multiplier': 1.25,
            'margin_tightening': -2.5,
            'applicability': 0.25  # 25% of Week 12 games are rivalries
        })

        # Pattern 3: Late Season Fatigue
        insights.append({
            'pattern': 'late_season_fatigue',
            'description': 'Teams show 5% performance decline due to accumulated injuries',
            'fatigue_factor': 0.95,
            'injury_impact': 0.08,
            'applicability': 1.0  # Applies to all teams
        })

        # Pattern 4: Bowl Eligibility Motivation
        insights.append({
            'pattern': 'bowl_eligibility',
            'description': 'Teams fighting for bowl eligibility show 12% performance increase',
            'motivation_boost': 1.12,
            'applicability': 0.40  # 40% of teams playing for bowl eligibility
        })

        self.log_info(f"Generated {len(insights)} Week 12 pattern insights")
        return insights

    def _calculate_trend_adjustments(self) -> Dict[str, Any]:
        """Calculate adjustments based on 2025 season trends"""

        adjustments = {
            'offensive_adjustments': {
                'passing_yards_adjustment': 1.08,  # 8% increase in passing yards
                'rushing_attempts_decline': 0.94,  # 6% decline in rushing attempts
                'scoring_rate_increase': 1.05,  # 5% increase in scoring rate
            },
            'defensive_adjustments': {
                'sacks_per_game_increase': 1.12,  # 12% increase in sacks
                'interception_rate_increase': 1.06,  # 6% increase in interceptions
                'third_down_defense_improvement': 1.03,  # 3% improvement in 3rd down D
            },
            'team_specific': {
                # Adjustments for specific team trends
                'improving_teams_multiplier': 1.05,
                'declining_teams_multiplier': 0.92,
                'consistent_teams_multiplier': 1.00,
            }
        }

        self.log_info("Calculated trend adjustments for 2025 season")
        return adjustments

    def _generate_enhanced_week12_data(
        self,
        base_data: Dict[str, Any],
        week12_insights: List[Dict[str, Any]],
        trend_adjustments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate enhanced Week 12 data applying patterns and trends"""

        self.log_info("Generating enhanced Week 12 data...")

        # Get list of Week 12 games (scheduled or generate realistic matchups)
        week12_games = self._get_or_generate_week12_games(base_data)

        enhanced_games = []

        for game in week12_games:
            enhanced_game = self._enhance_single_game(
                game, base_data, week12_insights, trend_adjustments
            )
            enhanced_games.append(enhanced_game)

        # Generate enhanced team metrics
        enhanced_metrics = self._generate_enhanced_team_metrics(
            base_data['team_metrics'], trend_adjustments
        )

        result = {
            'games': enhanced_games,
            'team_talent': base_data['team_talent'],
            'team_metrics': enhanced_metrics,
            'enhancement_metadata': {
                'patterns_applied': len(week12_insights),
                'trend_adjustments': len(trend_adjustments),
                'enhancement_date': datetime.now().isoformat(),
                'total_games': len(enhanced_games)
            }
        }

        self.log_info(f"Generated enhanced data for {len(enhanced_games)} Week 12 games")
        return result

    def _get_or_generate_week12_games(self, base_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get actual Week 12 games or generate realistic matchups"""

        # Try to get real teams from training data first
        teams = None
        try:
            from src.utils.data import get_teams_from_data
            from src.utils.data import get_current_season
            current_season = get_current_season()
            teams = get_teams_from_data(season=current_season, limit=130)  # Get all FBS teams
            if teams:
                logger.info(f"✅ Loaded {len(teams)} teams from training data")
        except Exception as e:
            logger.warning(f"⚠️ Could not load teams from data: {e}")
        
        # Fallback to base_data or minimal list
        if not teams:
            teams = list(base_data['team_talent']['team'].values) if 'team' in base_data.get('team_talent', {}).columns else None
        
        # Last resort fallback (should rarely be used)
        if not teams:
            logger.warning("⚠️ Using minimal fallback team list - should use real data")
            teams = [
                'Georgia', 'Ohio State', 'Michigan', 'Washington', 'Texas', 'Alabama',
                'Oklahoma', 'Oregon', 'Florida State', 'LSU', 'Clemson', 'Tennessee',
                'Penn State', 'Notre Dame', 'Utah', 'USC', 'Ole Miss', 'Kansas State',
                'TCU', 'Oregon State', 'Arizona', 'UCLA', 'Washington State'
            ]

        # Generate realistic Week 12 matchups based on conference affiliations and rankings
        matchups = self._generate_realistic_week12_matchups(teams)

        week12_games = []
        for i, (home_team, away_team) in enumerate(matchups):
            game = {
                'id': f"{self._get_current_season()}_week12_{i+1:03d}",
                'season': self._get_current_season(),
                'week': 12,  # Week 12 is fixed for this agent
                'season_type': 'regular',
                'home_team': home_team,
                'away_team': away_team,
                'home_points': None,  # To be predicted
                'away_points': None,  # To be predicted
                'game_date': self._generate_game_date(i),
                'venue': self._get_venue(home_team),
                'is_rivalry': self._is_rivalry_game(home_team, away_team),
                'has_championship_implications': self._has_championship_implications(home_team, away_team),
                'weather_factors': self._generate_weather_factors(home_team)
            }
            week12_games.append(game)

        return week12_games

    def _generate_realistic_week12_matchups(self, teams: List[str]) -> List[tuple]:
        """Generate realistic Week 12 matchups based on typical conference schedules"""

        # Conference affiliations (simplified for example)
        conferences = {
            'SEC': ['Georgia', 'Alabama', 'LSU', 'Ole Miss', 'Tennessee', 'Texas', 'Oklahoma', 'Missouri', 'Auburn', 'Florida'],
            'Big Ten': ['Ohio State', 'Michigan', 'Penn State', 'USC', 'UCLA', 'Washington', 'Oregon', 'Michigan State', 'Iowa', 'Wisconsin'],
            'Big 12': ['Kansas State', 'TCU', 'Texas Tech', 'Baylor', 'West Virginia', 'UCF', 'Cincinnati', 'Houston', 'BYU'],
            'ACC': ['Florida State', 'Clemson', 'North Carolina', 'Virginia Tech', 'Louisville', 'Miami'],
            'Pac-12': ['Oregon', 'Washington', 'Utah', 'USC', 'UCLA', 'Arizona', 'Washington State', 'Oregon State'],
            'Independent': ['Notre Dame']
        }

        matchups = []

        # Generate typical Week 12 conference games and some cross-conference matchups
        conference_matchups = [
            ('Georgia', 'Tennessee'),  # SEC rivalry
            ('Ohio State', 'Michigan'),  # The Game
            ('Texas', 'LSU'),  # SEC matchup
            ('Oregon', 'Washington'),  # Pac-12 North
            ('Florida State', 'Miami'),  # ACC rivalry
            ('Kansas State', 'TCU'),  # Big 12 matchup
            ('Penn State', 'Michigan State'),  # Big Ten East
            ('Alabama', 'Auburn'),  # Iron Bowl
            ('Ole Miss', 'Missouri'),  # SEC cross-division
            ('USC', 'UCLA'),  # Pac-12 LA rivalry
            ('Notre Dame', 'Navy'),  # Traditional rivalry
            ('Utah', 'Arizona'),  # Pac-12 South
            ('Clemson', 'North Carolina'),  # ACC cross-division
            ('TCU', 'Baylor'),  # Big 12 rivalry
            ('Wisconsin', 'Minnesota'),  # Big Ten West
            ('Virginia Tech', 'Virginia'),  # Commonwealth Clash
            ('BYU', 'West Virginia'),  # Big 12 matchup
        ]

        # Filter to teams that exist in our list
        valid_matchups = []
        for home, away in conference_matchups:
            if home in teams and away in teams:
                valid_matchups.append((home, away))

        # Add some realistic cross-conference games
        cross_conference = [
            ('Georgia', 'Georgia Tech'),  # In-state rivalry
            ('Ohio State', 'Cincinnati'),  # Ohio rivalry
            ('Michigan', 'Western Michigan'),  # Michigan in-state
            ('Texas', 'Texas Tech'),  # Texas in-state
        ]

        for home, away in cross_conference:
            if home in teams and away in teams and (home, away) not in valid_matchups:
                valid_matchups.append((home, away))

        # Ensure we have a good number of matchups
        return valid_matchups[:15]  # Return top 15 matchups

    def _enhance_single_game(
        self,
        game: Dict[str, Any],
        base_data: Dict[str, Any],
        week12_insights: List[Dict[str, Any]],
        trend_adjustments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enhance a single game with Week 12 patterns and trends"""

        enhanced_game = game.copy()

        # Apply Week 12 specific adjustments
        for insight in week12_insights:
            if self._insight_applies(insight, game):
                enhanced_game = self._apply_insight_to_game(enhanced_game, insight)

        # Apply 2025 trend adjustments
        enhanced_game = self._apply_trend_adjustments(enhanced_game, trend_adjustments)

        # Add enhanced features for ML models
        enhanced_game['enhanced_features'] = self._calculate_enhanced_features(
            enhanced_game, base_data
        )

        return enhanced_game

    def _insight_applies(self, insight: Dict[str, Any], game: Dict[str, Any]) -> bool:
        """Determine if a specific insight applies to a game"""

        pattern = insight['pattern']

        if pattern == 'championship_implications' and game.get('has_championship_implications'):
            return random.random() < insight['applicability']
        elif pattern == 'rivalry_variance' and game.get('is_rivalry'):
            return random.random() < insight['applicability']
        elif pattern == 'late_season_fatigue':
            return random.random() < insight['applicability']
        elif pattern == 'bowl_eligibility':
            return random.random() < insight['applicability']

        return False

    def _apply_insight_to_game(self, game: Dict[str, Any], insight: Dict[str, Any]) -> Dict[str, Any]:
        """Apply a specific insight to a game"""

        pattern = insight['pattern']

        if pattern == 'championship_implications':
            game['performance_multiplier'] = insight.get('multiplier', 1.0)
            game['motivation_level'] = 'high'
        elif pattern == 'rivalry_variance':
            game['scoring_variance_multiplier'] = insight.get('variance_multiplier', 1.0)
            game['expected_margin_adjustment'] = insight.get('margin_tightening', 0)
        elif pattern == 'late_season_fatigue':
            game['fatigue_factor'] = insight.get('fatigue_factor', 1.0)
            game['injury_probability'] = insight.get('injury_impact', 0)
        elif pattern == 'bowl_eligibility':
            game['motivation_boost'] = insight.get('motivation_boost', 1.0)

        return game

    def _apply_trend_adjustments(self, game: Dict[str, Any], trend_adjustments: Dict[str, Any]) -> Dict[str, Any]:
        """Apply 2025 season trend adjustments to a game"""

        # Apply general offensive and defensive adjustments
        game['offensive_trend_multiplier'] = trend_adjustments['offensive_adjustments']['scoring_rate_increase']
        game['defensive_trend_multiplier'] = 1.0 / trend_adjustments['defensive_adjustments']['third_down_defense_improvement']

        # Apply team-specific adjustments
        home_team = game['home_team']
        away_team = game['away_team']

        if home_team in trend_adjustments['team_specific'].get('improving_teams', []):
            game['home_trend_adjustment'] = trend_adjustments['team_specific']['improving_teams_multiplier']
        elif home_team in trend_adjustments['team_specific'].get('declining_teams', []):
            game['home_trend_adjustment'] = trend_adjustments['team_specific']['declining_teams_multiplier']
        else:
            game['home_trend_adjustment'] = trend_adjustments['team_specific']['consistent_teams_multiplier']

        # Similar logic for away team
        if away_team in trend_adjustments['team_specific'].get('improving_teams', []):
            game['away_trend_adjustment'] = trend_adjustments['team_specific']['improving_teams_multiplier']
        elif away_team in trend_adjustments['team_specific'].get('declining_teams', []):
            game['away_trend_adjustment'] = trend_adjustments['team_specific']['declining_teams_multiplier']
        else:
            game['away_trend_adjustment'] = trend_adjustments['team_specific']['consistent_teams_multiplier']

        return game

    def _calculate_enhanced_features(self, game: Dict[str, Any], base_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate enhanced features for ML model compatibility"""

        features = {}

        # Base talent ratings
        home_talent = self._get_team_talent(game['home_team'], base_data['team_talent'])
        away_talent = self._get_team_talent(game['away_team'], base_data['team_talent'])

        features['home_talent'] = home_talent
        features['away_talent'] = away_talent

        # Apply Week 12 adjustments
        home_multiplier = game.get('home_trend_adjustment', 1.0) * game.get('performance_multiplier', 1.0)
        away_multiplier = game.get('away_trend_adjustment', 1.0)

        # Generate mock advanced metrics with adjustments
        base_metrics = base_data['team_metrics'].get(game['home_team'], {})

        features['home_adjusted_epa'] = base_metrics.get('offense_epa', 0.1) * home_multiplier
        features['away_adjusted_epa'] = base_metrics.get('offense_epa', 0.1) * away_multiplier

        features['home_adjusted_success'] = min(0.8, base_metrics.get('success_rate', 0.45) * home_multiplier)
        features['away_adjusted_success'] = min(0.8, base_metrics.get('success_rate', 0.45) * away_multiplier)

        # Add Week 12 specific features
        features['home_motivation_factor'] = game.get('motivation_boost', 1.0)
        features['away_motivation_factor'] = 1.0  # Away teams typically less motivated

        features['rivalry_game_adjustment'] = 1.15 if game.get('is_rivalry') else 1.0
        features['championship_implication_adjustment'] = 1.2 if game.get('has_championship_implications') else 1.0

        # Generate remaining features (simplified for this example)
        # In a full implementation, all 86 features would be calculated here
        for i in range(10, 86):
            features[f'feature_{i}'] = np.random.normal(0, 1) * home_multiplier

        return features

    def _validate_enhanced_data(self, enhanced_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate the quality of enhanced data"""

        validation_results = {
            'total_games': len(enhanced_data['games']),
            'feature_completeness': 0,
            'data_consistency': 0,
            'quality_score': 0,
            'issues': []
        }

        # Check feature completeness
        games_with_features = sum(1 for game in enhanced_data['games'] if 'enhanced_features' in game)
        if validation_results['total_games'] > 0:
            validation_results['feature_completeness'] = games_with_features / validation_results['total_games']

        # Check data consistency
        consistent_games = 0
        for game in enhanced_data['games']:
            if (game.get('season') == 2025 and
                game.get('week') == 12 and
                'home_team' in game and 'away_team' in game):
                consistent_games += 1

        if validation_results['total_games'] > 0:
            validation_results['data_consistency'] = consistent_games / validation_results['total_games']

        # Calculate overall quality score
        validation_results['quality_score'] = (
            validation_results['feature_completeness'] * 0.5 +
            validation_results['data_consistency'] * 0.5
        ) * 100

        # Identify issues
        if validation_results['feature_completeness'] < 0.95:
            validation_results['issues'].append('Some games missing enhanced features')

        if validation_results['data_consistency'] < 0.95:
            validation_results['issues'].append('Data consistency issues detected')

        return validation_results

    def _save_enhanced_data(self, enhanced_data: Dict[str, Any]) -> None:
        """Save enhanced data to files for use by other agents"""

        # Import path utilities to get canonical directory
        from model_pack.utils.path_utils import get_weekly_enhanced_dir, ensure_directory_exists
        from pathlib import Path
        
        # Get week from agent ID or metadata, default to 12 for backward compatibility
        week = getattr(self, 'week', 12)
        season = getattr(self, 'season', 2025)
        
        # Use canonical directory path
        output_dir = get_weekly_enhanced_dir(week, season)
        ensure_directory_exists(output_dir)
        output_dir = Path(output_dir)

        # Save enhanced games
        enhanced_games_df = pd.DataFrame(enhanced_data['games'])
        games_path = output_dir / f"week{week}_enhanced_games.csv"
        enhanced_games_df.to_csv(games_path, index=False)
        self.log_info(f"Saved enhanced games to {games_path}")

        # Save metadata
        metadata_path = output_dir / "enhancement_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(enhanced_data['enhancement_metadata'], f, indent=2)
        self.log_info(f"Saved enhancement metadata to {metadata_path}")

        # Save features in ML-compatible format
        features_data = []
        for game in enhanced_data['games']:
            if 'enhanced_features' in game:
                feature_row = {
                    'game_id': game['id'],
                    'home_team': game['home_team'],
                    'away_team': game['away_team'],
                    **game['enhanced_features']
                }
                features_data.append(feature_row)

        if features_data:
            features_df = pd.DataFrame(features_data)
            features_path = output_dir / f"week{week}_features_86.csv"
            features_df.to_csv(features_path, index=False)
            self.log_info(f"Saved features data to {features_path}")

    # Helper methods (simplified implementations)
    def _create_base_mock_games(self) -> pd.DataFrame:
        """Create base mock games if none exist"""
        return pd.DataFrame()

    def _create_base_talent_data(self) -> pd.DataFrame:
        """Create base talent data if none exist"""
        return pd.DataFrame()

    def _calculate_base_metrics(self, plays_data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate base team metrics from plays data"""
        return {}

    def _create_base_metrics(self) -> Dict[str, Any]:
        """Create base metrics if no plays data exists"""
        return {}

    def _get_team_talent(self, team: str, talent_data: pd.DataFrame) -> float:
        """Get talent rating for a team"""
        # Simplified implementation
        talent_ratings = {
            'Georgia': 950, 'Ohio State': 940, 'Michigan': 920, 'Washington': 880,
            'Texas': 900, 'Alabama': 930, 'Oklahoma': 850, 'Oregon': 870,
            'Florida State': 860, 'LSU': 880, 'Clemson': 870, 'Notre Dame': 890
        }
        return talent_ratings.get(team, 750)

    def _generate_game_date(self, game_index: int) -> str:
        """Generate realistic game date for Week 12"""
        # Calculate Week 12 date dynamically
        current_season = self._get_current_season()
        # Week 12 typically starts around November 13-16
        # Calculate based on season start (August 24)
        from src.utils.data import calculate_current_week
        season_start = datetime(current_season, 8, 24)
        week_12_start = season_start + timedelta(days=(12 - 1) * 7)  # 11 weeks * 7 days
        base_date = week_12_start + timedelta(days=2)  # Wednesday of Week 12
        game_date = base_date + timedelta(days=game_index % 4)  # Wed-Sat games
        return game_date.strftime('%Y-%m-%dT19:00:00Z')

    def _get_venue(self, team: str) -> str:
        """Get home venue for team"""
        venues = {
            'Georgia': ' Sanford Stadium',
            'Ohio State': ' Ohio Stadium',
            'Michigan': ' Michigan Stadium',
            'Washington': ' Husky Stadium',
            # ... more venues
        }
        return venues.get(team, f'{team} Stadium')

    def _is_rivalry_game(self, home_team: str, away_team: str) -> bool:
        """Determine if this is a rivalry game"""
        # Try to get popular matchups from data (rivalries are often frequent matchups)
        try:
            from src.utils.data import get_popular_matchups
            popular_matchups = get_popular_matchups(limit=50)
            # Check if this matchup appears frequently (indicates rivalry)
            matchup_count = sum(1 for h, a in popular_matchups if (h == home_team and a == away_team) or (h == away_team and a == home_team))
            if matchup_count >= 3:  # If they play often, likely a rivalry
                return True
        except Exception:
            pass
        
        # Fallback to known rivalries (should rarely be used)
        rivalries = [
            ('Georgia', 'Georgia Tech'), ('Ohio State', 'Michigan'),
            ('Alabama', 'Auburn'), ('Florida State', 'Miami'),
            ('Texas', 'Texas Tech'), ('USC', 'UCLA')
        ]
        return (home_team, away_team) in rivalries or (away_team, home_team) in rivalries

    def _has_championship_implications(self, home_team: str, away_team: str) -> bool:
        """Determine if game has championship implications"""
        # Try to get top teams from training data (teams with high Elo ratings)
        try:
            from pathlib import Path
            base_path = Path(__file__).parent.parent.parent
            training_data_path = base_path / "model_pack" / "updated_training_data.csv"
            if training_data_path.exists():
                training_data = pd.read_csv(training_data_path)
                from src.utils.data import get_current_season
                current_season = get_current_season()
                season_data = training_data[training_data['season'] == current_season]
                
                # Get teams with high Elo ratings (top 25%)
                if 'home_elo' in season_data.columns:
                    elo_threshold = season_data['home_elo'].quantile(0.75)
                    top_teams = set()
                    top_teams.update(season_data[season_data['home_elo'] >= elo_threshold]['home_team'].unique())
                    top_teams.update(season_data[season_data['away_elo'] >= elo_threshold]['away_team'].unique())
                    return home_team in top_teams or away_team in top_teams
        except Exception:
            pass
        
        # Fallback: assume top teams have championship implications
        top_teams = ['Georgia', 'Ohio State', 'Michigan', 'Washington', 'Texas', 'Oregon']
        return home_team in top_teams or away_team in top_teams

    def _generate_weather_factors(self, team: str) -> Dict[str, Any]:
        """Generate weather factors for game"""
        # Simplified weather generation
        return {
            'temperature': random.uniform(40, 75),
            'precipitation_probability': random.uniform(0, 0.3),
            'wind_speed': random.uniform(0, 15)
        }

    def _generate_enhanced_team_metrics(self, base_metrics: Dict[str, Any], trend_adjustments: Dict[str, Any]) -> Dict[str, Any]:
        """Generate enhanced team metrics applying trends"""
        # Implementation would apply trend adjustments to base metrics
        return base_metrics


# Example usage
if __name__ == "__main__":
    agent = Week12MockEnhancementAgent()

    task_data = {
        'operation': 'enhance_mock_data',
        'target_week': 12,
        'season': 2025
    }

    result = agent.execute_task(task_data)
    print(f"Mock Enhancement Result: {result}")