"""
Weekly Matchup Analysis Agent
Analyzes weekly matchups using enhanced data and provides strategic insights
"""

import os
import logging
import pandas as pd
import numpy as np
import random
from datetime import datetime
from typing import Dict, List, Any, Optional
import json

# Import the base agent framework
from agents.core.agent_framework import BaseAgent, AgentCapability, PermissionLevel

# Import path utilities
from model_pack.utils.path_utils import (
    get_weekly_enhanced_file,
    get_master_training_data_path
)

logger = logging.getLogger(__name__)

class WeeklyMatchupAnalysisAgent(BaseAgent):
    """
    Agent responsible for analyzing weekly matchups and generating strategic insights
    using enhanced mock data and historical patterns
    """

    def __init__(self, week: int, season: int = 2025, agent_id: Optional[str] = None):
        self.week = week
        self.season = season
        
        if agent_id is None:
            agent_id = f"week{week}_matchup_analysis"
        
        super().__init__(
            agent_id=agent_id,
            name=f"Week {week} Matchup Analysis Agent",
            permission_level=PermissionLevel.READ_EXECUTE_WRITE,
        )
        self.agent_description = f"Analyzes Week {week} matchups and produces strategic insights."

        # Initialize agent-specific attributes
        self.analysis_weights = self._load_analysis_weights()
        self.strategic_factors = self._load_strategic_factors()

    # ------------------------------------------------------------------
    # Simple logging helpers (BaseAgent in this repo doesn't provide them)
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

    def _define_capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability(
                name="analyze_matchups",
                description=f"Analyze Week {self.week} matchups and generate insights.",
                permission_required=PermissionLevel.READ_EXECUTE_WRITE,
                tools_required=["pandas", "numpy"],
                data_access=["model_pack/", "starter_pack/data/"],
                execution_time_estimate=8.0,
            )
        ]

    def _execute_action(self, action: str, parameters: Dict[str, Any],
                       user_context: Dict[str, Any]) -> Dict[str, Any]:
        if action == "analyze_matchups":
            return self.execute_task(parameters or {})
        raise ValueError(f"Unknown action: {action}")

    def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main execution method for weekly matchup analysis

        Args:
            task_data: Contains configuration for analysis task

        Returns:
            Comprehensive matchup analysis with strategic insights
        """
        try:
            self.log_start(f"Week {self.week} Matchup Analysis")

            # Step 1: Load enhanced weekly data
            enhanced_data = self._load_enhanced_weekly_data()

            # Step 2: Perform head-to-head analysis
            head_to_head_analysis = self._analyze_head_to_head_matchups(enhanced_data)

            # Step 3: Calculate team strength metrics
            strength_metrics = self._calculate_team_strength_metrics(enhanced_data)

            # Step 4: Generate matchup-specific insights
            matchup_insights = self._generate_matchup_insights(enhanced_data, strength_metrics)

            # Step 5: Analyze situational factors
            situational_analysis = self._analyze_situational_factors(enhanced_data)

            # Step 6: Calculate advanced matchup statistics
            advanced_stats = self._calculate_advanced_matchup_stats(enhanced_data)

            # Step 7: Generate strategic recommendations
            strategic_recommendations = self._generate_strategic_recommendations(
                enhanced_data, head_to_head_analysis, strength_metrics, matchup_insights
            )

            # Step 8: Compile comprehensive analysis
            comprehensive_analysis = self._compile_comprehensive_analysis(
                enhanced_data, head_to_head_analysis, strength_metrics,
                matchup_insights, situational_analysis, advanced_stats, strategic_recommendations
            )

            # Step 9: Save analysis results
            self._save_analysis_results(comprehensive_analysis)

            result = {
                'status': 'success',
                'matchups_analyzed': len(enhanced_data['games']),
                'insights_generated': len(matchup_insights),
                'strategic_recommendations': len(strategic_recommendations),
                'analysis_completion': 1.0,
                'data_saved': True,
                'execution_time': self.get_execution_time()
            }

            self.log_success(f"Week {self.week} Matchup Analysis", result)
            return result

        except Exception as e:
            error_result = {
                'status': 'error',
                'error': str(e),
                'execution_time': self.get_execution_time()
            }
            self.log_error(f"Week {self.week} Matchup Analysis", e)
            return error_result

    def _load_enhanced_weekly_data(self) -> Dict[str, Any]:
        """Load enhanced weekly data from mock enhancement agent and training data"""

        self.log_info(f"Loading enhanced Week {self.week} data...")

        # Load enhanced games using path utility
        try:
            enhanced_data_path = get_weekly_enhanced_file(self.week, 'games', self.season)
            enhanced_games = pd.read_csv(enhanced_data_path)
            self.log_info(f"Loaded {len(enhanced_games)} enhanced games from {enhanced_data_path}")
        except FileNotFoundError:
            raise FileNotFoundError(f"Enhanced Week {self.week} games data not found. Run mock enhancement agent first.")

        # Load features using path utility
        try:
            features_path = get_weekly_enhanced_file(self.week, 'features', self.season)
            features_data = pd.read_csv(features_path)
            self.log_info(f"Loaded {len(features_data)} feature records from {features_path}")
        except FileNotFoundError:
            raise FileNotFoundError(f"Week {self.week} features data not found.")

        # Load training data for win-loss records and completed games using path utility
        training_data = None
        try:
            training_data_path = get_master_training_data_path()
            training_data = pd.read_csv(training_data_path)
            # Filter to only completed games (those with scores for both teams)
            training_data = training_data[
                training_data['home_points'].notna() & 
                training_data['away_points'].notna() &
                (training_data['home_points'] > 0) & (training_data['away_points'] > 0)
            ]
            self.log_info(f"Loaded {len(training_data)} completed games from training data at {training_data_path}")
        except FileNotFoundError:
            self.log_info(f"Warning: Training data not found, win-loss calculations may be limited")

        # Load metadata using path utility (optional)
        try:
            metadata_path = get_weekly_enhanced_file(self.week, 'metadata', self.season)
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            self.log_info(f"Loaded metadata from {metadata_path}")
        except FileNotFoundError:
            metadata = {}
            self.log_info("No metadata found - using empty metadata")

        return {
            'games': enhanced_games,
            'features': features_data,
            'training_data': training_data,
            'metadata': metadata,
            'load_time': datetime.now().isoformat()
        }

    def _analyze_head_to_head_matchups(self, enhanced_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze head-to-head historical matchups and current form"""

        self.log_info("Analyzing head-to-head matchups...")

        head_to_head_results = {}

        for _, game in enhanced_data['games'].iterrows():
            home_team = game['home_team']
            away_team = game['away_team']
            matchup_key = f"{home_team}_vs_{away_team}"

            # Historical head-to-head analysis (using historical patterns)
            h2h_record = self._get_historical_h2h_record(home_team, away_team)
            recent_form = self._get_recent_team_form(home_team, away_team)

            head_to_head_results[matchup_key] = {
                'historical_record': h2h_record,
                'recent_form': recent_form,
                'series_trend': self._calculate_series_trend(h2h_record),
                'momentum_advantage': self._calculate_momentum_advantage(recent_form),
                'rivalry_intensity': self._calculate_rivalry_intensity(home_team, away_team)
            }

        self.log_info(f"Analyzed head-to-head data for {len(head_to_head_results)} matchups")
        return head_to_head_results

    def _calculate_team_strength_metrics(self, enhanced_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate comprehensive team strength metrics"""

        self.log_info("Calculating team strength metrics...")

        strength_metrics = {}

        # Get unique teams
        all_teams = set(enhanced_data['games']['home_team'].tolist() +
                       enhanced_data['games']['away_team'].tolist())

        for team in all_teams:
            # Get team data from features
            team_games = enhanced_data['features'][
                (enhanced_data['features']['home_team'] == team) |
                (enhanced_data['features']['away_team'] == team)
            ]

            if not team_games.empty:
                # Calculate various strength metrics
                strength_metrics[team] = {
                    'offensive_rating': self._calculate_offensive_rating(team, enhanced_data),
                    'defensive_rating': self._calculate_defensive_rating(team, enhanced_data),
                    'special_teams_rating': self._calculate_special_teams_rating(team, enhanced_data),
                    'overall_rating': self._calculate_overall_rating(team, enhanced_data),
                    'strength_of_schedule': self._calculate_strength_of_schedule(team, enhanced_data),
                    'injury_factor': self._estimate_injury_impact(team, enhanced_data),
                    'consistency_rating': self._calculate_consistency_rating(team, enhanced_data),
                    'clutch_performance': self._calculate_clutch_performance(team, enhanced_data),
                    'adjusted_rating': self._calculate_adjusted_rating(team, enhanced_data)
                }

        self.log_info(f"Calculated strength metrics for {len(strength_metrics)} teams")
        return strength_metrics

    def _generate_matchup_insights(self, enhanced_data: Dict[str, Any], strength_metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate specific insights for each matchup"""

        self.log_info("Generating matchup insights...")

        insights = []

        for _, game in enhanced_data['games'].iterrows():
            home_team = game['home_team']
            away_team = game['away_team']

            matchup_insight = {
                'game_id': game['id'],
                'home_team': home_team,
                'away_team': away_team,
                'key_matchups': self._identify_key_positional_matchups(home_team, away_team, strength_metrics),
                'offensive_comparison': self._compare_offenses(home_team, away_team, strength_metrics),
                'defensive_comparison': self._compare_defenses(home_team, away_team, strength_metrics),
                'special_teams_battle': self._compare_special_teams(home_team, away_team, strength_metrics),
                'coaching_matchup': self._analyze_coaching_matchup(home_team, away_team),
                'x_factors': self._identify_x_factors(home_team, away_team, strength_metrics),
                'game_flow_prediction': self._predict_game_flow(home_team, away_team, strength_metrics),
                'critical_situations': self._analyze_critical_situations(home_team, away_team, strength_metrics)
            }

            insights.append(matchup_insight)

        self.log_info(f"Generated insights for {len(insights)} matchups")
        return insights

    def _analyze_situational_factors(self, enhanced_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze situational factors affecting weekly games"""

        self.log_info("Analyzing situational factors...")

        situational_analysis = {
            'weather_impacts': {},
            'travel_factors': {},
            'motivational_factors': {},
            'injury_situations': {},
            'playoff_implications': {},
            'rivalry_factors': {}
        }

        for _, game in enhanced_data['games'].iterrows():
            home_team = game['home_team']
            away_team = game['away_team']
            game_id = game['id']

            # Weather analysis
            situational_analysis['weather_impacts'][game_id] = self._analyze_weather_impact(game)

            # Travel factors
            situational_analysis['travel_factors'][game_id] = self._analyze_travel_factors(home_team, away_team)

            # Motivational factors
            situational_analysis['motivational_factors'][game_id] = self._analyze_motivation_factors(game)

            # Injury situations
            situational_analysis['injury_situations'][game_id] = self._estimate_injury_situation(home_team, away_team)

            # Playoff implications
            situational_analysis['playoff_implications'][game_id] = self._analyze_playoff_implications(game)

            # Rivalry factors
            situational_analysis['rivalry_factors'][game_id] = self._analyze_rivalry_factors(home_team, away_team)

        self.log_info(f"Analyzed situational factors for {len(situational_analysis['weather_impacts'])} games")
        return situational_analysis

    def _calculate_advanced_matchup_stats(self, enhanced_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate advanced matchup statistics"""

        self.log_info("Calculating advanced matchup statistics...")

        advanced_stats = {}

        for _, game in enhanced_data['games'].iterrows():
            home_team = game['home_team']
            away_team = game['away_team']
            game_id = game['id']

            advanced_stats[game_id] = {
                'pace_prediction': self._predict_game_pace(home_team, away_team),
                'scoring_probability': self._calculate_scoring_probability(home_team, away_team),
                'turnover_projection': self._project_turnovers(home_team, away_team),
                'explosive_play_probability': self._calculate_explosive_play_probability(home_team, away_team),
                'third_down_efficiency_projection': self._project_third_down_efficiency(home_team, away_team),
                'red_zone_efficiency_projection': self._project_red_zone_efficiency(home_team, away_team),
                'time_of_possession_prediction': self._predict_time_of_possession(home_team, away_team),
                'penalty_projection': self._project_penalties(home_team, away_team),
                'sack_projection': self._project_sacks(home_team, away_team),
                'big_play_projection': self._project_big_plays(home_team, away_team)
            }

        self.log_info(f"Calculated advanced statistics for {len(advanced_stats)} games")
        return advanced_stats

    def _generate_strategic_recommendations(
        self,
        enhanced_data: Dict[str, Any],
        head_to_head_analysis: Dict[str, Any],
        strength_metrics: Dict[str, Any],
        matchup_insights: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate strategic recommendations for each matchup"""

        self.log_info("Generating strategic recommendations...")

        recommendations = []

        for _, game in enhanced_data['games'].iterrows():
            home_team = game['home_team']
            away_team = game['away_team']
            game_id = game['id']

            # Find corresponding insight
            game_insight = next((insight for insight in matchup_insights if insight['game_id'] == game_id), {})

            recommendation = {
                'game_id': game_id,
                'home_team': home_team,
                'away_team': away_team,
                'winner_recommendation': self._predict_winner(home_team, away_team, strength_metrics),
                'confidence_level': self._calculate_prediction_confidence(home_team, away_team, strength_metrics),
                'score_prediction': self._predict_score(home_team, away_team, strength_metrics),
                'spread_analysis': self._analyze_spread(home_team, away_team, strength_metrics),
                'over_under_analysis': self._analyze_over_under(home_team, away_team, strength_metrics),
                'betting_recommendations': self._generate_betting_recommendations(home_team, away_team, strength_metrics),
                'upset_probability': self._calculate_upset_probability(home_team, away_team, strength_metrics),
                'key_factors': self._identify_key_factors(home_team, away_team, strength_metrics, game_insight),
                'strategic_advantages': self._identify_strategic_advantages(home_team, away_team, strength_metrics),
                'game_script_prediction': self._predict_game_script(home_team, away_team, strength_metrics)
            }

            recommendations.append(recommendation)

        self.log_info(f"Generated strategic recommendations for {len(recommendations)} games")
        return recommendations

    def _compile_comprehensive_analysis(
        self,
        enhanced_data: Dict[str, Any],
        head_to_head_analysis: Dict[str, Any],
        strength_metrics: Dict[str, Any],
        matchup_insights: List[Dict[str, Any]],
        situational_analysis: Dict[str, Any],
        advanced_stats: Dict[str, Any],
        strategic_recommendations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Compile all analyses into a comprehensive report"""

        self.log_info("Compiling comprehensive analysis...")

        comprehensive_analysis = {
            'analysis_metadata': {
                'analysis_date': datetime.now().isoformat(),
                'week': self.week,
                'season': self.season,
                'total_games_analyzed': len(enhanced_data['games']),
                'analysis_components': [
                    'head_to_head_analysis',
                    'team_strength_metrics',
                    'matchup_insights',
                    'situational_factors',
                    'advanced_statistics',
                    'strategic_recommendations'
                ]
            },
            'team_rankings': self._generate_power_rankings(strength_metrics, enhanced_data),
            'top_matchups': self._identify_top_matchups(enhanced_data, strategic_recommendations),
            'upset_alerts': self._identify_upset_alerts(strategic_recommendations),
            'playoff_implications': self._analyze_playoff_picture(enhanced_data, strategic_recommendations),
            'conference_races': self._analyze_conference_races(enhanced_data, strength_metrics),
            'heisman_implications': self._analyze_heisman_implications(enhanced_data, strength_metrics),
            'coaching_hot_seat': self._analyze_coaching_situations(enhanced_data, strength_metrics),
            'bowl_projections': self._project_bowl_implications(enhanced_data, strategic_recommendations),
            'detailed_analysis': {
                'head_to_head': head_to_head_analysis,
                'team_strengths': strength_metrics,
                'matchup_insights': matchup_insights,
                'situational_factors': situational_analysis,
                'advanced_stats': advanced_stats,
                'recommendations': strategic_recommendations
            }
        }

        self.log_info("Comprehensive analysis compiled successfully")
        return comprehensive_analysis

    def _save_analysis_results(self, comprehensive_analysis: Dict[str, Any]) -> None:
        """Save comprehensive analysis results to files"""

        # Create output directory
        output_dir = f"analysis/week{self.week}"
        os.makedirs(output_dir, exist_ok=True)

        # Save full analysis
        analysis_path = os.path.join(output_dir, f"week{self.week}_comprehensive_analysis.json")
        with open(analysis_path, 'w') as f:
            json.dump(comprehensive_analysis, f, indent=2, default=str)
        self.log_info(f"Saved comprehensive analysis to {analysis_path}")

        # Save strategic recommendations as CSV
        if comprehensive_analysis['detailed_analysis']['recommendations']:
            recommendations_df = pd.DataFrame(comprehensive_analysis['detailed_analysis']['recommendations'])
            rec_path = os.path.join(output_dir, f"week{self.week}_strategic_recommendations.csv")
            recommendations_df.to_csv(rec_path, index=False)
            self.log_info(f"Saved strategic recommendations to {rec_path}")

        # Save team rankings
        rankings_df = pd.DataFrame(comprehensive_analysis['team_rankings'])
        rankings_path = os.path.join(output_dir, f"week{self.week}_power_rankings.csv")
        rankings_df.to_csv(rankings_path, index=False)
        self.log_info(f"Saved power rankings to {rankings_path}")

        # Save upset alerts
        if comprehensive_analysis['upset_alerts']:
            upset_df = pd.DataFrame(comprehensive_analysis['upset_alerts'])
            upset_path = os.path.join(output_dir, f"week{self.week}_upset_alerts.csv")
            upset_df.to_csv(upset_path, index=False)
            self.log_info(f"Saved upset alerts to {upset_path}")

    # Helper method implementations (simplified for this example)
    def _load_analysis_weights(self) -> Dict[str, float]:
        """Load weights for different analysis components"""
        return {
            'head_to_head': 0.25,
            'team_strength': 0.30,
            'situational': 0.20,
            'advanced_stats': 0.15,
            'historical_trends': 0.10
        }

    def _load_strategic_factors(self) -> Dict[str, Any]:
        """Load strategic factors for analysis"""
        return {
            'home_field_advantage': 2.5,
            'rivalry_boost': 1.2,
            'motivation_multiplier': 1.1,
            'injury_penalty': -0.8,
            'weather_impact': 0.5
        }

    def _get_historical_h2h_record(self, home_team: str, away_team: str) -> Dict[str, int]:
        """Get historical head-to-head record (mock data)"""
        # Simplified mock implementation
        return {
            'home_wins': random.randint(3, 8),
            'away_wins': random.randint(2, 6),
            'total_games': random.randint(10, 15)
        }

    def _get_recent_team_form(self, home_team: str, away_team: str) -> Dict[str, Any]:
        """Get recent team form for both teams"""
        return {
            'home_team': {
                'last_5_record': f"{random.randint(2, 5)}-{random.randint(0, 3)}",
                'points_per_game': random.uniform(20, 45),
                'points_allowed_per_game': random.uniform(15, 35)
            },
            'away_team': {
                'last_5_record': f"{random.randint(2, 5)}-{random.randint(0, 3)}",
                'points_per_game': random.uniform(20, 45),
                'points_allowed_per_game': random.uniform(15, 35)
            }
        }

    def _calculate_series_trend(self, h2h_record: Dict[str, int]) -> str:
        """Calculate series trend"""
        total = h2h_record['total_games']
        if total == 0:
            return 'No history'
        home_pct = h2h_record['home_wins'] / total
        if home_pct > 0.6:
            return 'Home team dominates'
        elif home_pct < 0.4:
            return 'Away team dominates'
        else:
            return 'Evenly matched'

    def _calculate_momentum_advantage(self, recent_form: Dict[str, Any]) -> str:
        """Calculate momentum advantage based on recent form"""
        home_points = recent_form['home_team']['points_per_game'] - recent_form['home_team']['points_allowed_per_game']
        away_points = recent_form['away_team']['points_per_game'] - recent_form['away_team']['points_allowed_per_game']

        if home_points > away_points + 5:
            return 'Home team'
        elif away_points > home_points + 5:
            return 'Away team'
        else:
            return 'Even'

    def _calculate_rivalry_intensity(self, home_team: str, away_team: str) -> float:
        """Calculate rivalry game intensity factor"""
        # Try to get popular matchups from data (rivalries are often frequent)
        try:
            from src.utils.data import get_popular_matchups
            popular_matchups = get_popular_matchups(limit=50)
            # Check if this matchup appears frequently (indicates rivalry)
            matchup_count = sum(1 for h, a in popular_matchups if (h == home_team and a == away_team) or (h == away_team and a == home_team))
            if matchup_count >= 3:  # If they play often, likely a rivalry
                return 1.5
        except Exception:
            pass
        
        # Fallback to known rivalries (should rarely be used)
        rivalries = [
            ('Georgia', 'Georgia Tech'), ('Ohio State', 'Michigan'),
            ('Alabama', 'Auburn'), ('Texas', 'Texas Tech')
        ]
        if (home_team, away_team) in rivalries or (away_team, home_team) in rivalries:
            return 1.5
        return 1.0

    # More helper methods would be implemented here...
    def _calculate_offensive_rating(self, team: str, data: Dict[str, Any]) -> float:
        """Calculate offensive rating from home_adjusted_epa and away_adjusted_epa"""
        # Try games first, then features as fallback
        enhanced_games = data.get('games', pd.DataFrame())
        features_data = data.get('features', pd.DataFrame())
        
        # Use features if games don't have the column
        if not enhanced_games.empty and 'home_adjusted_epa' in enhanced_games.columns:
            data_source = enhanced_games
        elif not features_data.empty and 'home_adjusted_epa' in features_data.columns:
            data_source = features_data
        else:
            return 75.0  # Default neutral rating
        
        # Get team's offensive EPA from games where they played
        home_games = data_source[data_source['home_team'] == team]
        away_games = data_source[data_source['away_team'] == team]
        
        home_epa = home_games['home_adjusted_epa'].mean() if not home_games.empty and 'home_adjusted_epa' in home_games.columns else 0.0
        away_epa = away_games['away_adjusted_epa'].mean() if not away_games.empty and 'away_adjusted_epa' in away_games.columns else 0.0
        
        # Average EPA and scale to 0-100 rating (EPA typically ranges -0.3 to 0.3)
        avg_epa = np.mean([h for h in [home_epa, away_epa] if not pd.isna(h) and h != 0.0])
        if pd.isna(avg_epa) or avg_epa == 0.0:
            return 75.0
        
        # Scale EPA to 0-100: EPA of 0.2 = 90, EPA of 0 = 75, EPA of -0.2 = 60
        rating = 75.0 + (avg_epa * 75.0)  # Scale factor: 0.2 EPA -> 15 point boost
        return max(0.0, min(100.0, rating))

    def _calculate_defensive_rating(self, team: str, data: Dict[str, Any]) -> float:
        """Calculate defensive rating from home_adjusted_epa_allowed and away_adjusted_epa_allowed"""
        # Try games first, then features as fallback
        enhanced_games = data.get('games', pd.DataFrame())
        features_data = data.get('features', pd.DataFrame())
        
        # Use features if games don't have the column
        if not enhanced_games.empty and 'home_adjusted_epa_allowed' in enhanced_games.columns:
            data_source = enhanced_games
        elif not features_data.empty and 'home_adjusted_epa_allowed' in features_data.columns:
            data_source = features_data
        else:
            return 75.0  # Default neutral rating
        
        # Get team's defensive EPA allowed (lower is better for defense)
        home_games = data_source[data_source['home_team'] == team]
        away_games = data_source[data_source['away_team'] == team]
        
        home_epa_allowed = home_games['home_adjusted_epa_allowed'].mean() if not home_games.empty and 'home_adjusted_epa_allowed' in home_games.columns else 0.0
        away_epa_allowed = away_games['away_adjusted_epa_allowed'].mean() if not away_games.empty and 'away_adjusted_epa_allowed' in away_games.columns else 0.0
        
        # Average EPA allowed (lower is better, so we invert)
        avg_epa_allowed = np.mean([h for h in [home_epa_allowed, away_epa_allowed] if not pd.isna(h) and h != 0.0])
        if pd.isna(avg_epa_allowed) or avg_epa_allowed == 0.0:
            return 75.0
        
        # Invert: lower EPA allowed = higher defensive rating
        # EPA allowed of 0.2 = 60 rating, EPA allowed of 0 = 75, EPA allowed of -0.2 = 90
        rating = 75.0 - (avg_epa_allowed * 75.0)  # Invert the scale
        return max(0.0, min(100.0, rating))

    def _calculate_special_teams_rating(self, team: str, data: Dict[str, Any]) -> float:
        """Calculate special teams rating as average of offensive and defensive ratings"""
        offensive = self._calculate_offensive_rating(team, data)
        defensive = self._calculate_defensive_rating(team, data)
        return (offensive + defensive) / 2.0

    def _calculate_overall_rating(self, team: str, data: Dict[str, Any]) -> float:
        """Calculate overall rating using Elo + talent + EPA*1000 formula from final_analysis.py"""
        # Try games first, then features as fallback
        enhanced_games = data.get('games', pd.DataFrame())
        features_data = data.get('features', pd.DataFrame())
        
        # Use games if available, otherwise features
        if not enhanced_games.empty:
            data_source = enhanced_games
        elif not features_data.empty:
            data_source = features_data
        else:
            return 75.0
        
        # Get team's Elo and talent ratings
        home_games = data_source[data_source['home_team'] == team]
        away_games = data_source[data_source['away_team'] == team]
        
        # Average Elo
        home_elo = home_games['home_elo'].mean() if not home_games.empty and 'home_elo' in home_games.columns else 1500.0
        away_elo = away_games['away_elo'].mean() if not away_games.empty and 'away_elo' in away_games.columns else 1500.0
        avg_elo = np.mean([h for h in [home_elo, away_elo] if not pd.isna(h)])
        
        # Average talent
        home_talent = home_games['home_talent'].mean() if not home_games.empty and 'home_talent' in home_games.columns else 500.0
        away_talent = away_games['away_talent'].mean() if not away_games.empty and 'away_talent' in away_games.columns else 500.0
        avg_talent = np.mean([h for h in [home_talent, away_talent] if not pd.isna(h)])
        
        # Average EPA
        home_epa = home_games['home_adjusted_epa'].mean() if not home_games.empty and 'home_adjusted_epa' in home_games.columns else 0.0
        away_epa = away_games['away_adjusted_epa'].mean() if not away_games.empty and 'away_adjusted_epa' in away_games.columns else 0.0
        avg_epa = np.mean([h for h in [home_epa, away_epa] if not pd.isna(h) and h != 0.0])
        if pd.isna(avg_epa):
            avg_epa = 0.0
        
        # Combined strength: Elo + talent + (EPA * 1000) as per final_analysis.py
        combined_strength = avg_elo + avg_talent + (avg_epa * 1000)
        
        # Scale to 0-100 rating (typical range: 1500-2500 Elo, 200-1000 talent, -300 to 300 EPA*1000)
        # Combined strength range roughly 1400-3800, normalize to 0-100
        # Use a scaling factor: (strength - 1400) / (3800 - 1400) * 100
        rating = ((combined_strength - 1400) / 2400) * 100
        return max(0.0, min(100.0, rating))

    def _calculate_strength_of_schedule(self, team: str, data: Dict[str, Any]) -> float:
        """Calculate strength of schedule from opponents' average Elo ratings"""
        enhanced_games = data.get('games', pd.DataFrame())
        
        if enhanced_games.empty:
            return 0.5  # Default neutral
        
        # Get all opponents this team has faced
        team_games = enhanced_games[
            (enhanced_games['home_team'] == team) | (enhanced_games['away_team'] == team)
        ]
        
        if team_games.empty:
            return 0.5
        
        # Get opponents' Elo ratings
        opponent_elos = []
        for _, game in team_games.iterrows():
            if game['home_team'] == team:
                opponent_elo = game.get('away_elo', 1500.0)
            else:
                opponent_elo = game.get('home_elo', 1500.0)
            
            if not pd.isna(opponent_elo):
                opponent_elos.append(opponent_elo)
        
        if not opponent_elos:
            return 0.5
        
        # Average opponent Elo and normalize to 0-1 scale (1500 = 0.5, 2000 = 1.0, 1000 = 0.0)
        avg_opponent_elo = np.mean(opponent_elos)
        sos_rating = (avg_opponent_elo - 1000) / 1000  # Normalize to 0-1
        return max(0.0, min(1.0, sos_rating))

    def _estimate_injury_impact(self, team: str, data: Dict[str, Any]) -> float:
        """Return neutral 1.0 placeholder (no injury data available)"""
        return 1.0  # Neutral impact

    def _calculate_consistency_rating(self, team: str, data: Dict[str, Any]) -> float:
        """Calculate consistency rating from EPA variance"""
        # Try games first, then features as fallback
        enhanced_games = data.get('games', pd.DataFrame())
        features_data = data.get('features', pd.DataFrame())
        
        # Use features if games don't have the column
        if not enhanced_games.empty and 'home_adjusted_epa' in enhanced_games.columns:
            data_source = enhanced_games
        elif not features_data.empty and 'home_adjusted_epa' in features_data.columns:
            data_source = features_data
        else:
            return 0.75  # Default moderate consistency
        
        # Get team's EPA values across all games
        home_games = data_source[data_source['home_team'] == team]
        away_games = data_source[data_source['away_team'] == team]
        
        epa_values = []
        if not home_games.empty and 'home_adjusted_epa' in home_games.columns:
            epa_values.extend(home_games['home_adjusted_epa'].dropna().tolist())
        if not away_games.empty and 'away_adjusted_epa' in away_games.columns:
            epa_values.extend(away_games['away_adjusted_epa'].dropna().tolist())
        
        if len(epa_values) < 2:
            return 0.75
        
        # Lower variance = higher consistency
        epa_std = np.std(epa_values)
        # Normalize: std of 0.1 = 0.9 consistency, std of 0.3 = 0.5 consistency
        consistency = max(0.0, min(1.0, 1.0 - (epa_std * 2)))
        return consistency

    def _calculate_clutch_performance(self, team: str, data: Dict[str, Any]) -> float:
        """Calculate clutch performance (placeholder - would need close game data)"""
        # This would require analyzing performance in close games
        # For now, return a moderate value based on overall rating
        overall = self._calculate_overall_rating(team, data)
        # Scale overall rating (0-100) to clutch rating (0.7-0.95)
        return 0.7 + (overall / 100.0) * 0.25

    def _calculate_adjusted_rating(self, team: str, data: Dict[str, Any]) -> float:
        """Calculate adjusted rating considering strength of schedule"""
        overall = self._calculate_overall_rating(team, data)
        sos = self._calculate_strength_of_schedule(team, data)
        consistency = self._calculate_consistency_rating(team, data)
        
        # Adjust for SOS: higher SOS = slight boost, lower SOS = slight penalty
        sos_adjustment = (sos - 0.5) * 5.0  # ±2.5 points based on SOS
        consistency_adjustment = (consistency - 0.75) * 5.0  # ±1.25 points based on consistency
        
        adjusted = overall + sos_adjustment + consistency_adjustment
        return max(0.0, min(100.0, adjusted))

    def _identify_key_positional_matchups(self, home: str, away: str, metrics: Dict) -> List[str]:
        return ["QB vs Secondary", "OL vs DL", "WR vs CB", "LB vs RB"]

    def _compare_offenses(self, home: str, away: str, metrics: Dict) -> Dict[str, Any]:
        return {"advantage": home if random.random() > 0.5 else away, "margin": random.uniform(1, 10)}

    def _compare_defenses(self, home: str, away: str, metrics: Dict) -> Dict[str, Any]:
        return {"advantage": home if random.random() > 0.5 else away, "margin": random.uniform(1, 10)}

    def _compare_special_teams(self, home: str, away: str, metrics: Dict) -> Dict[str, Any]:
        return {"advantage": "Even", "margin": 0}

    def _analyze_coaching_matchup(self, home: str, away: str) -> Dict[str, Any]:
        return {"advantage": home if random.random() > 0.5 else away, "experience_edge": random.uniform(0.8, 1.2)}

    def _identify_x_factors(self, home: str, away: str, metrics: Dict) -> List[str]:
        return ["Turnover battle", "Special teams", "Weather conditions", "Injuries"]

    def _predict_game_flow(self, home: str, away: str, metrics: Dict) -> str:
        return random.choice(["High-scoring shootout", "Defensive struggle", "Balanced game"])

    def _analyze_critical_situations(self, home: str, away: str, metrics: Dict) -> List[str]:
        return ["Third down efficiency", "Red zone performance", "Two-minute drill"]

    def _analyze_weather_impact(self, game: Dict) -> Dict[str, Any]:
        return {"impact": random.uniform(0.8, 1.2), "conditions": "Clear"}

    def _analyze_travel_factors(self, home: str, away: str) -> Dict[str, Any]:
        return {"advantage": home, "distance_penalty": random.uniform(0.9, 1.0)}

    def _analyze_motivation_factors(self, game: Dict) -> Dict[str, Any]:
        return {"home_motivation": random.uniform(0.8, 1.2), "away_motivation": random.uniform(0.8, 1.2)}

    def _estimate_injury_situation(self, home: str, away: str) -> Dict[str, Any]:
        return {"home_impact": random.uniform(0.9, 1.0), "away_impact": random.uniform(0.9, 1.0)}

    def _analyze_playoff_implications(self, game: Dict) -> Dict[str, Any]:
        return {"implications": random.choice(["High", "Medium", "Low"])}

    def _analyze_rivalry_factors(self, home: str, away: str) -> Dict[str, Any]:
        return {"intensity": random.uniform(1.0, 1.5), "historical_significance": random.uniform(0.8, 1.2)}

    def _predict_game_pace(self, home: str, away: str) -> Dict[str, Any]:
        return {"plays_per_game": random.randint(140, 180), "tempo": random.choice(["Fast", "Medium", "Slow"])}

    def _calculate_scoring_probability(self, home: str, away: str) -> float:
        return random.uniform(0.4, 0.8)

    def _project_turnovers(self, home: str, away: str) -> Dict[str, Any]:
        return {"home_turnovers": random.randint(0, 3), "away_turnovers": random.randint(0, 3)}

    def _calculate_explosive_play_probability(self, home: str, away: str) -> float:
        return random.uniform(0.1, 0.3)

    def _project_third_down_efficiency(self, home: str, away: str) -> Dict[str, Any]:
        return {"home_rate": random.uniform(0.35, 0.5), "away_rate": random.uniform(0.35, 0.5)}

    def _project_red_zone_efficiency(self, home: str, away: str) -> Dict[str, Any]:
        return {"home_rate": random.uniform(0.7, 0.9), "away_rate": random.uniform(0.7, 0.9)}

    def _predict_time_of_possession(self, home: str, away: str) -> Dict[str, Any]:
        return {"home_minutes": random.randint(28, 35), "away_minutes": random.randint(25, 32)}

    def _project_penalties(self, home: str, away: str) -> Dict[str, Any]:
        return {"home_penalties": random.randint(5, 12), "away_penalties": random.randint(5, 12)}

    def _project_sacks(self, home: str, away: str) -> Dict[str, Any]:
        return {"home_sacks": random.randint(1, 6), "away_sacks": random.randint(1, 6)}

    def _project_big_plays(self, home: str, away: str) -> Dict[str, Any]:
        return {"home_big_plays": random.randint(3, 8), "away_big_plays": random.randint(3, 8)}

    def _predict_winner(self, home: str, away: str, metrics: Dict) -> str:
        return home if random.random() > 0.45 else away  # Slight home bias

    def _calculate_prediction_confidence(self, home: str, away: str, metrics: Dict) -> float:
        return random.uniform(0.6, 0.9)

    def _predict_score(self, home: str, away: str, metrics: Dict) -> Dict[str, int]:
        return {"home_score": random.randint(20, 45), "away_score": random.randint(15, 40)}

    def _analyze_spread(self, home: str, away: str, metrics: Dict) -> Dict[str, Any]:
        spread = random.uniform(-14, 14)
        return {"predicted_spread": spread, "recommendation": "Home" if spread < 0 else "Away"}

    def _analyze_over_under(self, home: str, away: str, metrics: Dict) -> Dict[str, Any]:
        total = random.uniform(40, 70)
        return {"predicted_total": total, "recommendation": "Over" if total > 55 else "Under"}

    def _generate_betting_recommendations(self, home: str, away: str, metrics: Dict) -> List[str]:
        return random.sample(["Home ATS", "Away ML", "Over Total", "Under Total", "Prop Bet"], 2)

    def _calculate_upset_probability(self, home: str, away: str, metrics: Dict) -> float:
        return random.uniform(0.1, 0.4)

    def _identify_key_factors(self, home: str, away: str, metrics: Dict, insight: Dict) -> List[str]:
        return random.sample(["Turnover margin", "Third downs", "Red zone", "Special teams"], 3)

    def _identify_strategic_advantages(self, home: str, away: str, metrics: Dict) -> Dict[str, List[str]]:
        return {
            "home": random.sample(["Run game", "Pass defense", "Home field"], 2),
            "away": random.sample(["Pass game", "Run defense", "Coaching"], 2)
        }

    def _predict_game_script(self, home: str, away: str, metrics: Dict) -> str:
        return random.choice(["High-scoring", "Defensive battle", "Close game", "Blowout"])

    def _generate_power_rankings(self, strength_metrics: Dict, enhanced_data: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Generate power rankings with real win-loss records from training data"""
        # Get training data from enhanced_data if available
        training_data = None
        if enhanced_data and 'training_data' in enhanced_data:
            training_data = enhanced_data['training_data']
        else:
            # Try to load training data directly
            training_data_path = "model_pack/updated_training_data.csv"
            if os.path.exists(training_data_path):
                training_data = pd.read_csv(training_data_path)
                # Filter to completed games (both teams must have scores)
                training_data = training_data[
                    training_data['home_points'].notna() & 
                    training_data['away_points'].notna() &
                    (training_data['home_points'] > 0) & (training_data['away_points'] > 0)
                ]
                # Optionally filter to current season for season-specific records
                if self.season and 'season' in training_data.columns:
                    training_data = training_data[training_data['season'] == self.season]
                    self.log_info(f"Filtered to {self.season} season: {len(training_data)} games")
        
        # Calculate win-loss records for each team
        team_records = {}
        if training_data is not None and not training_data.empty:
            for team in strength_metrics.keys():
                team_games = training_data[
                    (training_data['home_team'] == team) | (training_data['away_team'] == team)
                ]
                
                if not team_games.empty:
                    # Calculate wins
                    home_wins = len(team_games[
                        (team_games['home_team'] == team) & 
                        (team_games['home_points'] > team_games['away_points'])
                    ])
                    away_wins = len(team_games[
                        (team_games['away_team'] == team) & 
                        (team_games['away_points'] > team_games['home_points'])
                    ])
                    wins = home_wins + away_wins
                    losses = len(team_games) - wins
                    team_records[team] = {'wins': wins, 'losses': losses, 'games': len(team_games)}
                else:
                    team_records[team] = {'wins': 0, 'losses': 0, 'games': 0}
        else:
            # No training data available, use placeholder
            for team in strength_metrics.keys():
                team_records[team] = {'wins': 0, 'losses': 0, 'games': 0}
        
        # Sort teams by overall rating (from strength_metrics)
        sorted_teams = sorted(
            strength_metrics.items(),
            key=lambda x: x[1].get('overall_rating', 0),
            reverse=True
        )
        
        rankings = []
        for i, (team, metrics) in enumerate(sorted_teams[:25]):  # Top 25
            record = team_records.get(team, {'wins': 0, 'losses': 0, 'games': 0})
            rankings.append({
                "rank": i + 1,
                "team": team,
                "rating": metrics.get('overall_rating', 75.0),
                "record": f"{record['wins']}-{record['losses']}",
                "strength_of_schedule": metrics.get('strength_of_schedule', 0.5),
                "offensive_rating": metrics.get('offensive_rating', 75.0),
                "defensive_rating": metrics.get('defensive_rating', 75.0),
                "games_played": record['games']
            })
        
        return rankings

    def _identify_top_matchups(self, data: Dict, recommendations: List[Dict]) -> List[Dict[str, Any]]:
        # Return top 5 most interesting matchups
        return recommendations[:5]

    def _identify_upset_alerts(self, recommendations: List[Dict]) -> List[Dict[str, Any]]:
        # Return games with high upset probability
        upset_games = [rec for rec in recommendations if rec.get('upset_probability', 0) > 0.3]
        return upset_games[:3]

    def _analyze_playoff_picture(self, data: Dict, recommendations: List[Dict]) -> Dict[str, Any]:
        return {"teams_in_hunt": random.randint(8, 12), "bubble_teams": random.randint(4, 6)}

    def _analyze_conference_races(self, data: Dict, strength_metrics: Dict) -> Dict[str, Any]:
        return {"tight_races": random.randint(2, 4), "decided_races": random.randint(2, 5)}

    def _analyze_heisman_implications(self, data: Dict, strength_metrics: Dict) -> Dict[str, Any]:
        return {"candidates_affected": random.randint(3, 6), "boost_opportunities": random.randint(1, 3)}

    def _analyze_coaching_situations(self, data: Dict, strength_metrics: Dict) -> Dict[str, Any]:
        return {"hot_seat_games": random.randint(1, 3), "contract_extension_games": random.randint(2, 4)}

    def _project_bowl_implications(self, data: Dict, recommendations: List[Dict]) -> Dict[str, Any]:
        return {"teams_affected": random.randint(15, 25), "bowl_jumps": random.randint(3, 6)}


# Example usage
if __name__ == "__main__":
    agent = WeeklyMatchupAnalysisAgent(week=13, season=2025)

    task_data = {
        'operation': 'analyze_matchups',
        'target_week': 13,
        'season': 2025,
        'analysis_depth': 'comprehensive'
    }

    result = agent.execute_task(task_data)
    print(f"Matchup Analysis Result: {result}")

