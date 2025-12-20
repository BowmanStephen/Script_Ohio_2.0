#!/usr/bin/env python3
"""
Bowl Games Specialist Agent - Tier 4 Security Level
Specialized agent for college football bowl games prediction and analysis

Implements advanced bowl games prediction with historical analysis, team matchup evaluation,
weather integration, and specialized ML models for postseason scenarios.
"""

import logging
import json
import time
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import re

from agents.core.enhanced_agent_framework import EnhancedBaseAgent
from agents.core.security_manager import security_manager, PermissionLevel


class BowlTier(Enum):
    """Bowl game tier classifications"""

    NEW_YORK_SIX = "new_york_six"  # Top tier bowl games
    COLLEGE_FOOTBALL_PLAYOFF = "cfp"  # CFP semifinals and championship
    MAJOR_BOWLS = "major_bowls"  # Rose, Sugar, Orange, Fiesta
    SECOND_TIER = "second_tier"  # Cotton, Peach, Outback, etc.
    CONFERENCE_TIER = "conference_tier"  # Conference-affiliated bowls
    REGIONAL = "regional"  # Geographic regional bowls
    INVITATIONAL = "invitational"  # Invitational bowls


class PredictionConfidence(Enum):
    """Prediction confidence levels"""

    VERY_HIGH = "very_high"  # 90%+ confidence
    HIGH = "high"  # 80-89% confidence
    MODERATE = "moderate"  # 65-79% confidence
    LOW = "low"  # 50-64% confidence
    VERY_LOW = "very_low"  # <50% confidence


class TeamRankingLevel(Enum):
    """Team ranking levels"""

    TOP_5 = "top_5"
    TOP_10 = "top_10"
    TOP_25 = "top_25"
    RANKED = "ranked"
    UNRANKED = "unranked"


@dataclass
class BowlGame:
    """Represents a bowl game matchup"""

    game_id: str
    bowl_name: str
    bowl_tier: BowlTier
    season: int
    date: datetime
    location: str
    home_team: str
    away_team: str
    conference_affiliation: Dict[str, str]  # team -> conference
    neutral_site: bool = True
    prestige_score: float = 0.0  # 0-100 bowl importance score
    weather_conditions: Dict[str, Any] = field(default_factory=dict)
    historical_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TeamMatchupAnalysis:
    """Analysis of team matchup for bowl game"""

    team1: str
    team2: str
    season: int
    head_to_head: Dict[str, Any]
    strength_comparison: Dict[str, Any]
    ranking_differential: int
    conference_strength_comparison: Dict[str, float]
    travel_distance_impact: Dict[str, float]
    momentum_analysis: Dict[str, Any]
    injury_impact: Dict[str, float]
    coaching_experience: Dict[str, Any]
    overall_advantage_score: float  # -100 to +100


@dataclass
class BowlPrediction:
    """Bowl game prediction with confidence"""

    game_id: str
    predicted_winner: str
    predicted_margin: float
    confidence_level: PredictionConfidence
    probability: float  # 0-1 probability of prediction being correct
    key_factors: List[Dict[str, Any]]
    risk_assessment: str
    similar_historical_games: List[Dict[str, Any]]
    prediction_rationale: str
    created_at: datetime = field(default_factory=datetime.utcnow)


class BowlGamesSpecialistAgent(EnhancedBaseAgent):
    """
    Bowl Games Specialist Agent - Specialized bowl games prediction and analysis

    Capabilities:
    - Bowl game matchup analysis with historical context
    - Specialized ML models for postseason predictions
    - Weather impact assessment on game outcomes
    - Team momentum and performance trend analysis
    - Conference strength and scheduling advantages
    - Travel distance and neutral site effects
    - Injury and coaching impact analysis
    - Confidence scoring and risk assessment
    """

    def __init__(self, agent_id: str = "bowl_games_specialist"):
        super().__init__(
            agent_id=agent_id,
            agent_name="Bowl Games Specialist Agent",
            permission_level=PermissionLevel.READ_EXECUTE,
        )

        self.logger = logging.getLogger(f"{__name__}.{agent_id}")

        # Bowl game configuration
        self.bowl_data_directory = Path("/app/data/bowl-games")
        self.bowl_data_directory.mkdir(parents=True, exist_ok=True)
        self.predictions_directory = Path("/app/data/predictions")
        self.predictions_directory.mkdir(parents=True, exist_ok=True)

        # Bowl tier prestige scores
        self.bowl_tier_scores = {
            BowlTier.NEW_YORK_SIX: 100.0,
            BowlTier.COLLEGE_FOOTBALL_PLAYOFF: 95.0,
            BowlTier.MAJOR_BOWLS: 85.0,
            BowlTier.SECOND_TIER: 75.0,
            BowlTier.CONFERENCE_TIER: 65.0,
            BowlTier.REGIONAL: 55.0,
            BowlTier.INVITATIONAL: 45.0,
        }

        # Conference strength scores (0-100)
        self.conference_strength_2025 = {
            "SEC": 95.0,
            "Big Ten": 93.0,
            "Big 12": 88.0,
            "ACC": 85.0,
            "Pac-12": 82.0,
            "Big Ten": 90.0,
            "American": 75.0,
            "Mountain West": 70.0,
            "Conference USA": 65.0,
            "Sun Belt": 60.0,
            "MAC": 58.0,
        }

        # Weather impact factors
        self.weather_impact_factors = {
            "extreme_cold": -0.15,  # Below 32°F
            "heavy_rain": -0.10,  # >0.5 inches
            "strong_wind": -0.08,  # >15 mph
            "snow": -0.12,  # Any snow accumulation
            "extreme_heat": -0.05,  # Above 90°F
        }

        # Performance metrics
        self.metrics = {
            "bowl_predictions_made": 0,
            "bowl_predictions_correct": 0,
            "average_confidence": 0.0,
            "accuracy_by_tier": {},
            "predictions_by_confidence": {},
            "historical_analysis_count": 0,
            "weather_adjustments_made": 0,
        }

        # Load historical bowl data
        self.historical_bowl_data = self._load_historical_bowl_data()

    def _define_capabilities(self) -> List:
        """Define bowl games specialist capabilities"""
        return [
            {
                "name": "analyze_bowl_matchup",
                "description": "Comprehensive analysis of bowl game matchup",
                "execution_time_estimate": 20.0,
                "required_permissions": [PermissionLevel.READ_EXECUTE],
                "parameters": ["bowl_game", "analysis_depth", "include_historical"],
                "returns": {
                    "matchup_analysis": "object",
                    "key_factors": "list",
                    "advantage_score": "float",
                },
            },
            {
                "name": "predict_bowl_game",
                "description": "Generate specialized bowl game predictions with confidence",
                "execution_time_estimate": 15.0,
                "required_permissions": [PermissionLevel.READ_EXECUTE],
                "parameters": [
                    "bowl_game",
                    "prediction_method",
                    "confidence_threshold",
                ],
                "returns": {
                    "prediction": "object",
                    "confidence": "float",
                    "key_factors": "list",
                },
            },
            {
                "name": "analyze_bowl_season",
                "description": "Complete analysis of entire bowl season",
                "execution_time_estimate": 45.0,
                "required_permissions": [PermissionLevel.READ_EXECUTE],
                "parameters": ["season", "include_playoff", "analysis_completeness"],
                "returns": {
                    "season_analysis": "object",
                    "bowl_predictions": "list",
                    "season_outlook": "dict",
                },
            },
            {
                "name": "weather_impact_analysis",
                "description": "Analyze weather conditions impact on bowl game outcomes",
                "execution_time_estimate": 8.0,
                "required_permissions": [PermissionLevel.READ_EXECUTE],
                "parameters": ["bowl_game", "weather_forecast", "sensitivity_analysis"],
                "returns": {
                    "weather_impact": "dict",
                    "adjusted_predictions": "object",
                    "risk_factors": "list",
                },
            },
            {
                "name": "historical_comparison",
                "description": "Find similar historical bowl games for prediction reference",
                "execution_time_estimate": 12.0,
                "required_permissions": [PermissionLevel.READ_EXECUTE],
                "parameters": [
                    "bowl_game",
                    "comparison_criteria",
                    "similarity_threshold",
                ],
                "returns": {
                    "similar_games": "list",
                    "historical_patterns": "dict",
                    "prediction_insights": "list",
                },
            },
        ]

    def _execute_action(
        self, action: str, parameters: Dict, user_context: Dict
    ) -> Dict:
        """Execute bowl games specialist actions"""
        try:
            # Create security context
            context = security_manager.create_security_context(
                user_id=user_context.get("user_id", "bowl_specialist_system"),
                permissions=[
                    "bowl_games_specialization",
                    "prediction_generation",
                    "historical_analysis",
                ],
            )

            if action == "analyze_bowl_matchup":
                return self._analyze_bowl_matchup(parameters, context)
            elif action == "predict_bowl_game":
                return self._predict_bowl_game(parameters, context)
            elif action == "analyze_bowl_season":
                return self._analyze_bowl_season(parameters, context)
            elif action == "weather_impact_analysis":
                return self._weather_impact_analysis(parameters, context)
            elif action == "historical_comparison":
                return self._historical_comparison(parameters, context)
            else:
                raise ValueError(f"Unknown action: {action}")

        except Exception as e:
            self.logger.error(f"Bowl games action {action} failed: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__,
                "agent_id": self.agent_id,
                "timestamp": datetime.utcnow().isoformat(),
            }

    def _analyze_bowl_matchup(self, parameters: Dict, context) -> Dict:
        """Comprehensive analysis of bowl game matchup"""
        self.logger.info("Starting bowl matchup analysis")

        bowl_game_data = parameters.get("bowl_game", {})
        analysis_depth = parameters.get("analysis_depth", "comprehensive")
        include_historical = parameters.get("include_historical", True)

        # Create BowlGame object
        bowl_game = BowlGame(
            game_id=bowl_game_data.get("game_id", f"bowl_{int(time.time())}"),
            bowl_name=bowl_game_data.get("bowl_name", ""),
            bowl_tier=BowlTier(bowl_game_data.get("bowl_tier", "regional")),
            season=bowl_game_data.get("season", 2025),
            date=datetime.fromisoformat(
                bowl_game_data.get("date", datetime.utcnow().isoformat())
            ),
            location=bowl_game_data.get("location", ""),
            home_team=bowl_game_data.get("home_team", ""),
            away_team=bowl_game_data.get("away_team", ""),
            conference_affiliation=bowl_game_data.get("conference_affiliation", {}),
            neutral_site=bowl_game_data.get("neutral_site", True),
            prestige_score=self._calculate_bowl_prestige(
                BowlTier(bowl_game_data.get("bowl_tier", "regional"))
            ),
        )

        start_time = time.time()

        try:
            # Analyze team matchup
            matchup_analysis = self._analyze_team_matchup(
                bowl_game, analysis_depth, include_historical
            )

            # Calculate overall advantage score
            overall_advantage = self._calculate_overall_advantage(matchup_analysis)

            # Identify key factors
            key_factors = self._identify_key_matchup_factors(matchup_analysis)

            # Generate matchup insights
            insights = self._generate_matchup_insights(matchup_analysis, bowl_game)

            execution_time = time.time() - start_time

            # Update metrics
            self.metrics["historical_analysis_count"] += 1

            return {
                "status": "success",
                "data": {
                    "matchup_analysis": {
                        "teams": {
                            "team1": matchup_analysis.team1,
                            "team2": matchup_analysis.team2,
                        },
                        "strength_comparison": matchup_analysis.strength_comparison,
                        "head_to_head": matchup_analysis.head_to_head,
                        "ranking_differential": matchup_analysis.ranking_differential,
                        "conference_strength": matchup_analysis.conference_strength_comparison,
                        "momentum_analysis": matchup_analysis.momentum_analysis,
                        "travel_impact": matchup_analysis.travel_distance_impact,
                    },
                    "key_factors": key_factors,
                    "advantage_score": overall_advantage,
                    "insights": insights,
                    "bowl_game": {
                        "game_id": bowl_game.game_id,
                        "bowl_name": bowl_game.bowl_name,
                        "bowl_tier": bowl_game.bowl_tier.value,
                        "prestige_score": bowl_game.prestige_score,
                    },
                },
                "execution_time": execution_time,
                "agent_id": self.agent_id,
            }

        except Exception as e:
            return {
                "status": "error",
                "error": f"Bowl matchup analysis failed: {str(e)}",
                "execution_time": time.time() - start_time,
                "agent_id": self.agent_id,
            }

    def _predict_bowl_game(self, parameters: Dict, context) -> Dict:
        """Generate specialized bowl game predictions with confidence"""
        self.logger.info("Generating bowl game prediction")

        bowl_game_data = parameters.get("bowl_game", {})
        prediction_method = parameters.get("prediction_method", "ensemble")
        confidence_threshold = parameters.get("confidence_threshold", 0.65)

        # Create BowlGame object
        bowl_game = BowlGame(
            game_id=bowl_game_data.get("game_id", f"prediction_{int(time.time())}"),
            bowl_name=bowl_game_data.get("bowl_name", ""),
            bowl_tier=BowlTier(bowl_game_data.get("bowl_tier", "regional")),
            season=bowl_game_data.get("season", 2025),
            date=datetime.fromisoformat(
                bowl_game_data.get("date", datetime.utcnow().isoformat())
            ),
            location=bowl_game_data.get("location", ""),
            home_team=bowl_game_data.get("home_team", ""),
            away_team=bowl_game_data.get("away_team", ""),
            conference_affiliation=bowl_game_data.get("conference_affiliation", {}),
        )

        start_time = time.time()

        try:
            # Perform matchup analysis first
            matchup_analysis = self._analyze_team_matchup(
                bowl_game, "comprehensive", True
            )

            # Generate prediction using specified method
            prediction = self._generate_prediction(
                bowl_game, matchup_analysis, prediction_method
            )

            # Apply confidence filtering
            if prediction.probability < confidence_threshold:
                prediction.confidence_level = PredictionConfidence.LOW
                prediction.risk_assessment = (
                    "High uncertainty - below confidence threshold"
                )

            # Get similar historical games
            similar_games = self._find_similar_bowl_games(bowl_game, matchup_analysis)

            # Generate prediction rationale
            rationale = self._generate_prediction_rationale(
                prediction, matchup_analysis, similar_games
            )

            # Update metrics
            self.metrics["bowl_predictions_made"] += 1
            self._update_confidence_metrics(prediction)

            execution_time = time.time() - start_time

            return {
                "status": "success",
                "data": {
                    "prediction": {
                        "game_id": prediction.game_id,
                        "predicted_winner": prediction.predicted_winner,
                        "predicted_margin": prediction.predicted_margin,
                        "confidence_level": prediction.confidence_level.value,
                        "probability": prediction.probability,
                        "risk_assessment": prediction.risk_assessment,
                        "prediction_rationale": rationale,
                    },
                    "confidence": prediction.probability,
                    "key_factors": prediction.key_factors,
                    "similar_historical_games": similar_games,
                    "matchup_advantage": matchup_analysis.overall_advantage_score,
                    "bowl_prestige": bowl_game.prestige_score,
                },
                "execution_time": execution_time,
                "agent_id": self.agent_id,
            }

        except Exception as e:
            return {
                "status": "error",
                "error": f"Bowl prediction failed: {str(e)}",
                "execution_time": time.time() - start_time,
                "agent_id": self.agent_id,
            }

    def _analyze_bowl_season(self, parameters: Dict, context) -> Dict:
        """Complete analysis of entire bowl season"""
        self.logger.info("Starting bowl season analysis")

        season = parameters.get("season", 2025)
        include_playoff = parameters.get("include_playoff", True)
        analysis_completeness = parameters.get("analysis_completeness", "full")

        start_time = time.time()

        try:
            # Get all bowl games for season
            bowl_games = self._get_season_bowl_games(season, include_playoff)

            if not bowl_games:
                return {
                    "status": "error",
                    "error": f"No bowl games found for season {season}",
                }

            # Analyze each bowl game
            bowl_predictions = []
            season_analysis = {
                "total_bowls": len(bowl_games),
                "bowls_by_tier": {},
                "conference_representations": {},
                "geographic_distribution": {},
                "prestige_distribution": {},
                "average_prestige_score": 0.0,
            }

            for bowl_game in bowl_games:
                # Analyze matchup
                matchup_analysis = self._analyze_team_matchup(
                    bowl_game, "standard", False
                )

                # Generate prediction
                prediction = self._generate_prediction(
                    bowl_game, matchup_analysis, "ensemble"
                )

                bowl_predictions.append(
                    {
                        "game_id": bowl_game.game_id,
                        "bowl_name": bowl_game.bowl_name,
                        "teams": {"home": bowl_game.home_team, "away": bowl_game.away},
                        "prediction": {
                            "winner": prediction.predicted_winner,
                            "margin": prediction.predicted_margin,
                            "confidence": prediction.confidence_level.value,
                        },
                        "prestige_score": bowl_game.prestige_score,
                        "advantage_score": matchup_analysis.overall_advantage_score,
                    }
                )

                # Update season analysis
                self._update_season_analysis(
                    season_analysis, bowl_game, matchup_analysis
                )

            # Generate season outlook
            season_outlook = self._generate_season_outlook(
                bowl_predictions, season_analysis
            )

            execution_time = time.time() - start_time

            return {
                "status": "success",
                "data": {
                    "season_analysis": season_analysis,
                    "bowl_predictions": bowl_predictions,
                    "season_outlook": season_outlook,
                    "summary": {
                        "total_games_analyzed": len(bowl_predictions),
                        "average_confidence": np.mean(
                            [
                                self._confidence_to_float(p["prediction"]["confidence"])
                                for p in bowl_predictions
                            ]
                        ),
                        "high_confidence_games": len(
                            [
                                p
                                for p in bowl_predictions
                                if p["prediction"]["confidence"]
                                in ["very_high", "high"]
                            ]
                        ),
                        "playoff_games_included": include_playoff,
                        "analysis_completeness": analysis_completeness,
                    },
                },
                "execution_time": execution_time,
                "agent_id": self.agent_id,
            }

        except Exception as e:
            return {
                "status": "error",
                "error": f"Bowl season analysis failed: {str(e)}",
                "execution_time": time.time() - start_time,
                "agent_id": self.agent_id,
            }

    def _weather_impact_analysis(self, parameters: Dict, context) -> Dict:
        """Analyze weather conditions impact on bowl game outcomes"""
        self.logger.info("Starting weather impact analysis")

        bowl_game_data = parameters.get("bowl_game", {})
        weather_forecast = parameters.get("weather_forecast", {})
        sensitivity_analysis = parameters.get("sensitivity_analysis", True)

        # Create BowlGame object
        bowl_game = BowlGame(
            game_id=bowl_game_data.get("game_id", f"weather_{int(time.time())}"),
            bowl_name=bowl_game_data.get("bowl_name", ""),
            season=bowl_game_data.get("season", 2025),
            home_team=bowl_game_data.get("home_team", ""),
            away_team=bowl_game_data.get("away_team", ""),
            location=bowl_game_data.get("location", ""),
            weather_conditions=weather_forecast,
        )

        start_time = time.time()

        try:
            # Analyze weather impact
            weather_impact = self._analyze_weather_effects(bowl_game, weather_forecast)

            # Adjust predictions based on weather
            adjusted_predictions = self._adjust_predictions_for_weather(
                bowl_game, weather_impact
            )

            # Identify weather risk factors
            risk_factors = self._identify_weather_risk_factors(weather_forecast)

            # Generate weather insights
            insights = self._generate_weather_insights(weather_impact, bowl_game)

            if sensitivity_analysis:
                # Perform sensitivity analysis
                sensitivity_results = self._perform_weather_sensitivity_analysis(
                    bowl_game, weather_impact
                )
            else:
                sensitivity_results = {}

            # Update metrics
            self.metrics["weather_adjustments_made"] += 1

            execution_time = time.time() - start_time

            return {
                "status": "success",
                "data": {
                    "weather_impact": {
                        "impact_score": weather_impact.get("impact_score", 0),
                        "affected_team": weather_impact.get("affected_team"),
                        "impact_magnitude": weather_impact.get(
                            "impact_magnitude", "moderate"
                        ),
                        "temperature_effect": weather_impact.get("temperature_effect"),
                        "precipitation_effect": weather_impact.get(
                            "precipitation_effect"
                        ),
                        "wind_effect": weather_impact.get("wind_effect"),
                    },
                    "adjusted_predictions": adjusted_predictions,
                    "risk_factors": risk_factors,
                    "insights": insights,
                    "sensitivity_analysis": sensitivity_results,
                    "weather_forecast": weather_forecast,
                },
                "execution_time": execution_time,
                "agent_id": self.agent_id,
            }

        except Exception as e:
            return {
                "status": "error",
                "error": f"Weather impact analysis failed: {str(e)}",
                "execution_time": time.time() - start_time,
                "agent_id": self.agent_id,
            }

    def _historical_comparison(self, parameters: Dict, context) -> Dict:
        """Find similar historical bowl games for prediction reference"""
        self.logger.info("Starting historical comparison analysis")

        bowl_game_data = parameters.get("bowl_game", {})
        comparison_criteria = parameters.get(
            "comparison_criteria", ["bowl_tier", "ranking_differential", "conference"]
        )
        similarity_threshold = parameters.get("similarity_threshold", 0.7)

        # Create BowlGame object
        bowl_game = BowlGame(
            game_id=bowl_game_data.get("game_id", f"historical_{int(time.time())}"),
            bowl_name=bowl_game_data.get("bowl_name", ""),
            bowl_tier=BowlTier(bowl_game_data.get("bowl_tier", "regional")),
            season=bowl_game_data.get("season", 2025),
            home_team=bowl_game_data.get("home_team", ""),
            away_team=bowl_game_data.get("away_team", ""),
            conference_affiliation=bowl_game_data.get("conference_affiliation", {}),
        )

        start_time = time.time()

        try:
            # Find similar games
            similar_games = self._find_similar_bowl_games(
                bowl_game, comparison_criteria, similarity_threshold
            )

            # Analyze historical patterns
            historical_patterns = self._analyze_historical_patterns(similar_games)

            # Generate prediction insights
            prediction_insights = self._generate_historical_prediction_insights(
                similar_games, historical_patterns
            )

            # Calculate statistical significance
            statistical_analysis = self._calculate_historical_statistics(similar_games)

            execution_time = time.time() - start_time

            return {
                "status": "success",
                "data": {
                    "similar_games": similar_games,
                    "historical_patterns": historical_patterns,
                    "prediction_insights": prediction_insights,
                    "statistical_analysis": statistical_analysis,
                    "comparison_summary": {
                        "total_similar_games": len(similar_games),
                        "average_similarity": (
                            np.mean(
                                [game["similarity_score"] for game in similar_games]
                            )
                            if similar_games
                            else 0
                        ),
                        "criteria_used": comparison_criteria,
                        "similarity_threshold": similarity_threshold,
                    },
                },
                "execution_time": execution_time,
                "agent_id": self.agent_id,
            }

        except Exception as e:
            return {
                "status": "error",
                "error": f"Historical comparison failed: {str(e)}",
                "execution_time": time.time() - start_time,
                "agent_id": self.agent_id,
            }

    # Helper methods
    def _load_historical_bowl_data(self) -> pd.DataFrame:
        """Load historical bowl game data"""
        try:
            # Look for historical data files
            data_files = list(self.bowl_data_directory.glob("*.csv")) + list(
                self.bowl_data_directory.glob("*.json")
            )

            if data_files:
                # Load first available file
                data_file = data_files[0]
                if data_file.suffix == ".csv":
                    return pd.read_csv(data_file)
                elif data_file.suffix == ".json":
                    with open(data_file, "r") as f:
                        data = json.load(f)
                    return pd.DataFrame(data)
            else:
                # Create empty DataFrame with expected columns
                return pd.DataFrame(
                    columns=[
                        "season",
                        "bowl_name",
                        "bowl_tier",
                        "home_team",
                        "away_team",
                        "home_score",
                        "away_score",
                        "home_conference",
                        "away_conference",
                        "date",
                        "location",
                        "winner",
                    ]
                )
        except Exception as e:
            self.logger.warning(f"Failed to load historical bowl data: {e}")
            return pd.DataFrame()

    def _calculate_bowl_prestige(self, bowl_tier: BowlTier) -> float:
        """Calculate prestige score for bowl tier"""
        return self.bowl_tier_scores.get(bowl_tier, 50.0)

    def _analyze_team_matchup(
        self, bowl_game: BowlGame, analysis_depth: str, include_historical: bool
    ) -> TeamMatchupAnalysis:
        """Analyze team matchup for bowl game"""
        # Head to head analysis
        head_to_head = self._get_head_to_head_record(
            bowl_game.home_team, bowl_game.away_team, bowl_game.season
        )

        # Strength comparison
        strength_comparison = self._compare_team_strengths(
            bowl_game.home_team, bowl_game.away_team, bowl_game.season
        )

        # Ranking differential
        ranking_differential = self._calculate_ranking_differential(
            bowl_game.home_team, bowl_game.away_team, bowl_game.season
        )

        # Conference strength comparison
        home_conf_strength = self.conference_strength_2025.get(
            bowl_game.conference_affiliation.get(bowl_game.home_team, ""), 50.0
        )
        away_conf_strength = self.conference_strength_2025.get(
            bowl_game.conference_affiliation.get(bowl_game.away_team, ""), 50.0
        )
        conference_strength_comparison = {
            "home_team": home_conf_strength,
            "away_team": away_conf_strength,
            "differential": home_conf_strength - away_conf_strength,
        }

        # Travel distance impact
        travel_impact = self._calculate_travel_impact(bowl_game)

        # Momentum analysis
        momentum_analysis = self._analyze_team_momentum(
            bowl_game.home_team, bowl_game.away_team, bowl_game.season
        )

        # Injury impact
        injury_impact = self._calculate_injury_impact(
            bowl_game.home_team, bowl_game.away_team
        )

        # Coaching experience
        coaching_experience = self._analyze_coaching_experience(
            bowl_game.home_team, bowl_game.away_team
        )

        # Calculate overall advantage score
        overall_advantage = self._calculate_matchup_advantage_score(
            head_to_head,
            strength_comparison,
            ranking_differential,
            conference_strength_comparison["differential"],
            travel_impact,
            momentum_analysis,
            injury_impact,
            coaching_experience,
        )

        return TeamMatchupAnalysis(
            team1=bowl_game.home_team,
            team2=bowl_game.away_team,
            season=bowl_game.season,
            head_to_head=head_to_head,
            strength_comparison=strength_comparison,
            ranking_differential=ranking_differential,
            conference_strength_comparison=conference_strength_comparison,
            travel_distance_impact=travel_impact,
            momentum_analysis=momentum_analysis,
            injury_impact=injury_impact,
            coaching_experience=coaching_experience,
            overall_advantage_score=overall_advantage,
        )

    def _generate_prediction(
        self,
        bowl_game: BowlGame,
        matchup_analysis: TeamMatchupAnalysis,
        prediction_method: str,
    ) -> BowlPrediction:
        """Generate prediction using specified method"""
        try:
            if prediction_method == "ensemble":
                prediction = self._ensemble_prediction_method(
                    bowl_game, matchup_analysis
                )
            elif prediction_method == "statistical":
                prediction = self._statistical_prediction_method(
                    bowl_game, matchup_analysis
                )
            elif prediction_method == "momentum":
                prediction = self._momentum_prediction_method(
                    bowl_game, matchup_analysis
                )
            else:
                # Default to ensemble
                prediction = self._ensemble_prediction_method(
                    bowl_game, matchup_analysis
                )

            # Set key factors
            prediction.key_factors = self._extract_key_prediction_factors(
                matchup_analysis
            )

            # Set similar historical games
            prediction.similar_historical_games = self._find_similar_bowl_games(
                bowl_game, matchup_analysis
            )[:5]

            return prediction

        except Exception as e:
            self.logger.error(f"Prediction generation failed: {str(e)}")
            # Return fallback prediction
            return BowlPrediction(
                game_id=bowl_game.game_id,
                predicted_winner=(
                    bowl_game.home_team
                    if matchup_analysis.overall_advantage_score >= 0
                    else bowl_game.away_team
                ),
                predicted_margin=abs(matchup_analysis.overall_advantage_score) / 10,
                confidence_level=PredictionConfidence.LOW,
                probability=0.5,
                key_factors=[{"factor": "fallback_prediction", "impact": "minimal"}],
                risk_assessment="Prediction generation failed, using fallback method",
            )

    # Specific prediction methods would be implemented here
    def _ensemble_prediction_method(
        self, bowl_game: BowlGame, matchup_analysis: TeamMatchupAnalysis
    ) -> BowlPrediction:
        """Ensemble prediction method combining multiple factors"""
        # Base prediction on overall advantage
        advantage_score = matchup_analysis.overall_advantage_score

        predicted_winner = (
            bowl_game.home_team if advantage_score >= 0 else bowl_game.away_team
        )
        predicted_margin = abs(advantage_score) / 5  # Scale down to realistic margin

        # Calculate confidence based on multiple factors
        confidence_factors = []

        # Head to head confidence
        if matchup_analysis.head_to_head.get("games_played", 0) >= 3:
            h2h_winner_margin = abs(
                matchup_analysis.head_to_head.get("win_percentage", 0.5) - 0.5
            )
            confidence_factors.append(min(h2h_winner_margin * 2, 1.0))

        # Ranking confidence
        if matchup_analysis.ranking_differential != 0:
            ranking_confidence = min(
                abs(matchup_analysis.ranking_differential) / 25, 1.0
            )
            confidence_factors.append(ranking_confidence)

        # Conference strength confidence
        conf_diff = abs(matchup_analysis.conference_strength_comparison["differential"])
        if conf_diff > 0:
            confidence_factors.append(min(conf_diff / 50, 1.0))

        # Bowl prestige confidence
        prestige_confidence = bowl_game.prestige_score / 100
        confidence_factors.append(prestige_confidence)

        # Calculate overall confidence
        if confidence_factors:
            avg_confidence = np.mean(confidence_factors)
            probability = 0.5 + (avg_confidence - 0.5) * 0.4  # Scale to 0.3-0.7 range
            probability = max(0.3, min(0.9, probability))
        else:
            probability = 0.65

        # Determine confidence level
        if probability >= 0.8:
            confidence_level = PredictionConfidence.VERY_HIGH
        elif probability >= 0.7:
            confidence_level = PredictionConfidence.HIGH
        elif probability >= 0.65:
            confidence_level = PredictionConfidence.MODERATE
        elif probability >= 0.5:
            confidence_level = PredictionConfidence.LOW
        else:
            confidence_level = PredictionConfidence.VERY_LOW

        return BowlPrediction(
            game_id=bowl_game.game_id,
            predicted_winner=predicted_winner,
            predicted_margin=predicted_margin,
            confidence_level=confidence_level,
            probability=probability,
            risk_assessment=self._assess_prediction_risk(
                advantage_score, confidence_factors
            ),
        )

    def _statistical_prediction_method(
        self, bowl_game: BowlGame, matchup_analysis: TeamMatchupAnalysis
    ) -> BowlPrediction:
        """Statistical prediction method based on historical patterns"""
        # Implement statistical prediction logic
        # For now, simplified version
        return self._ensemble_prediction_method(bowl_game, matchup_analysis)

    def _momentum_prediction_method(
        self, bowl_game: BowlGame, matchup_analysis: TeamMatchupAnalysis
    ) -> BowlPrediction:
        """Momentum-based prediction method"""
        # Implement momentum prediction logic
        # For now, simplified version
        return self._ensemble_prediction_method(bowl_game, matchup_analysis)

    # Additional helper methods for analysis and calculations
    def _get_head_to_head_record(self, team1: str, team2: str, season: int) -> Dict:
        """Get head-to-head record between two teams"""
        # Simplified implementation - would query historical data
        return {
            "games_played": 0,
            "team1_wins": 0,
            "team2_wins": 0,
            "win_percentage": 0.5,
            "average_margin": 0,
        }

    def _compare_team_strengths(self, team1: str, team2: str, season: int) -> Dict:
        """Compare team strengths"""
        # Simplified implementation
        return {
            "team1_strength": 75.0,
            "team2_strength": 70.0,
            "differential": 5.0,
            "strength_categories": ["offense", "defense", "special_teams"],
        }

    def _calculate_ranking_differential(
        self, team1: str, team2: str, season: int
    ) -> int:
        """Calculate ranking differential between teams"""
        # Simplified implementation
        return 5  # team1 ranked 5 spots higher

    def _calculate_travel_impact(self, bowl_game: BowlGame) -> Dict:
        """Calculate travel distance impact"""
        # Simplified implementation
        return {
            "home_team_distance": 500,
            "away_team_distance": 800,
            "distance_differential": 300,
            "impact_factor": 0.1,
        }

    def _analyze_team_momentum(self, team1: str, team2: str, season: int) -> Dict:
        """Analyze team momentum going into bowl game"""
        return {
            "team1_momentum": 0.7,
            "team2_momentum": 0.6,
            "momentum_differential": 0.1,
            "recent_performance": ["strong", "moderate"],
        }

    def _calculate_injury_impact(self, team1: str, team2: str) -> Dict:
        """Calculate injury impact on both teams"""
        return {
            "team1_impact": 0.05,
            "team2_impact": 0.1,
            "key_players_out": [],
            "overall_impact": 0.15,
        }

    def _analyze_coaching_experience(self, team1: str, team2: str) -> Dict:
        """Analyze coaching experience in bowl games"""
        return {
            "team1_coach_bowl_record": {"wins": 3, "losses": 2},
            "team2_coach_bowl_record": {"wins": 2, "losses": 3},
            "experience_differential": 0.1,
        }

    def _calculate_matchup_advantage_score(
        self,
        head_to_head: Dict,
        strength_comparison: Dict,
        ranking_diff: int,
        conf_diff: float,
        travel_impact: Dict,
        momentum: Dict,
        injury: Dict,
        coaching: Dict,
    ) -> float:
        """Calculate overall matchup advantage score"""
        # Combine all factors into single score (-100 to +100)
        score = 0.0

        # Head to head
        if head_to_head.get("games_played", 0) > 0:
            h2h_advantage = (
                head_to_head.get("team1_wins", 0) - head_to_head.get("team2_wins", 0)
            ) * 5
            score += h2h_advantage

        # Strength comparison
        score += strength_comparison.get("differential", 0) * 2

        # Ranking
        score += ranking_diff * 3

        # Conference strength
        score += conf_diff * 0.5

        # Travel impact
        score += travel_impact.get("distance_differential", 0) * 0.01

        # Momentum
        score += (
            momentum.get("team1_momentum", 0) - momentum.get("team2_momentum", 0)
        ) * 20

        # Injuries
        score += (injury.get("team2_impact", 0) - injury.get("team1_impact", 0)) * 10

        # Coaching
        score += coaching.get("experience_differential", 0) * 5

        return np.clip(score, -100, 100)

    def _assess_prediction_risk(
        self, advantage_score: float, confidence_factors: List[float]
    ) -> str:
        """Assess prediction risk level"""
        if advantage_score < -20 or advantage_score > 20:
            return "High advantage detected - consider risk factors"
        elif not confidence_factors or np.mean(confidence_factors) < 0.6:
            return "Low confidence - high uncertainty in prediction"
        elif abs(advantage_score) < 10:
            return "Close matchup - prediction could go either way"
        else:
            return "Moderate confidence - reasonable prediction confidence"

    def _extract_key_prediction_factors(
        self, matchup_analysis: TeamMatchupAnalysis
    ) -> List[Dict]:
        """Extract key factors influencing prediction"""
        factors = []

        if abs(matchup_analysis.ranking_differential) > 0:
            factors.append(
                {
                    "factor": "ranking_differential",
                    "impact": abs(matchup_analysis.ranking_differential) / 25,
                    "description": f"Ranking difference of {matchup_analysis.ranking_differential} spots",
                }
            )

        if abs(matchup_analysis.conference_strength_comparison["differential"]) > 10:
            factors.append(
                {
                    "factor": "conference_strength",
                    "impact": abs(
                        matchup_analysis.conference_strength_comparison["differential"]
                    )
                    / 50,
                    "description": "Conference strength difference",
                }
            )

        return factors

    def _find_similar_bowl_games(
        self,
        bowl_game: BowlGame,
        matchup_analysis: TeamMatchupAnalysis,
        criteria: List[str] = None,
        threshold: float = 0.7,
    ) -> List[Dict]:
        """Find similar historical bowl games"""
        similar_games = []

        # Search through historical data
        for _, historical_game in self.historical_bowl_data.iterrows():
            similarity_score = 0.0

            # Bowl tier similarity
            if criteria is None or "bowl_tier" in criteria:
                if historical_game.get("bowl_tier") == bowl_game.bowl_tier.value:
                    similarity_score += 0.3

            # Ranking differential similarity
            if criteria is None or "ranking_differential" in criteria:
                hist_rank_diff = self._calculate_historical_ranking_diff(
                    historical_game
                )
                current_rank_diff = abs(matchup_analysis.ranking_differential)
                if hist_rank_diff and current_rank_diff:
                    rank_similarity = 1 - abs(hist_rank_diff - current_rank_diff) / max(
                        hist_rank_diff, current_rank_diff, 1
                    )
                    similarity_score += rank_similarity * 0.4

            # Conference matchup similarity
            if criteria is None or "conference" in criteria:
                if self._has_conference_match(historical_game, bowl_game):
                    similarity_score += 0.3

            if similarity_score >= threshold:
                similar_games.append(
                    {
                        "season": historical_game.get("season"),
                        "bowl_name": historical_game.get("bowl_name"),
                        "teams": {
                            "home": historical_game.get("home_team"),
                            "away": historical_game.get("away_team"),
                        },
                        "result": historical_game.get("winner"),
                        "margin": abs(
                            historical_game.get("home_score", 0)
                            - historical_game.get("away_score", 0)
                        ),
                        "similarity_score": similarity_score,
                    }
                )

        return sorted(similar_games, key=lambda x: x["similarity_score"], reverse=True)

    def _generate_prediction_rationale(
        self,
        prediction: BowlPrediction,
        matchup_analysis: TeamMatchupAnalysis,
        similar_games: List[Dict],
    ) -> str:
        """Generate prediction rationale"""
        rationale_parts = []

        # Add winner prediction
        rationale_parts.append(
            f"Predicted {prediction.predicted_winner} to win by {prediction.predicted_margin:.1f} points"
        )

        # Add confidence assessment
        rationale_parts.append(
            f"Confidence level: {prediction.confidence_level.value} ({prediction.probability:.1%} probability)"
        )

        # Add key factors
        if matchup_analysis.ranking_differential != 0:
            rationale_parts.append(
                f"Ranking advantage: {abs(matchup_analysis.ranking_differential)} spots"
            )

        # Add historical context
        if similar_games:
            similar_wins = sum(
                1
                for game in similar_games
                if game["result"] == prediction.predicted_winner
            )
            rationale_parts.append(
                f"Historical pattern: {similar_wins}/{len(similar_games)} similar games favored {prediction.predicted_winner}"
            )

        return " | ".join(rationale_parts)

    def _confidence_to_float(self, confidence_str: str) -> float:
        """Convert confidence string to float"""
        confidence_map = {
            "very_high": 0.9,
            "high": 0.75,
            "moderate": 0.65,
            "low": 0.55,
            "very_low": 0.45,
        }
        return confidence_map.get(confidence_str, 0.65)

    def _update_confidence_metrics(self, prediction: BowlPrediction) -> None:
        """Update confidence metrics"""
        confidence_float = prediction.probability
        confidence_str = prediction.confidence_level.value

        if confidence_str not in self.metrics["predictions_by_confidence"]:
            self.metrics["predictions_by_confidence"][confidence_str] = 0

        self.metrics["predictions_by_confidence"][confidence_str] += 1

        # Update average confidence
        current_avg = self.metrics.get("average_confidence", 0)
        total_predictions = self.metrics.get("bowl_predictions_made", 1)
        self.metrics["average_confidence"] = (
            current_avg * (total_predictions - 1) + confidence_float
        ) / total_predictions

    # Additional helper methods for season analysis, weather, etc.
    def _get_season_bowl_games(self, season: int, include_playoff: bool) -> List[Dict]:
        """Get all bowl games for a season"""
        # Simplified implementation - would query actual bowl game data
        sample_bowls = [
            {
                "game_id": f"cfp_semifinal_1_{season}",
                "bowl_name": "CFP Semifinal",
                "bowl_tier": "college_football_playoff",
                "home_team": "Georgia",
                "away_team": "Michigan",
                "date": f"{season}-12-31T19:00:00Z",
                "location": "Atlanta, GA",
            },
            {
                "game_id": f"rose_bowl_{season}",
                "bowl_name": "Rose Bowl",
                "bowl_tier": "major_bowls",
                "home_team": "Ohio State",
                "away_team": "Oregon",
                "date": f"{season}-01-01T17:00:00Z",
                "location": "Pasadena, CA",
            },
        ]

        return sample_bowls

    def _update_season_analysis(
        self,
        season_analysis: Dict,
        bowl_game: BowlGame,
        matchup_analysis: TeamMatchupAnalysis,
    ) -> None:
        """Update season analysis with bowl game data"""
        # Update tier counts
        tier = bowl_game.bowl_tier.value
        if tier not in season_analysis["bowls_by_tier"]:
            season_analysis["bowls_by_tier"][tier] = 0
        season_analysis["bowls_by_tier"][tier] += 1

        # Update conference representations
        home_conf = bowl_game.conference_affiliation.get(bowl_game.home_team, "")
        away_conf = bowl_game.conference_affiliation.get(bowl_game.away_team, "")

        for conf in [home_conf, away_conf]:
            if conf:
                if conf not in season_analysis["conference_representations"]:
                    season_analysis["conference_representations"][conf] = 0
                season_analysis["conference_representations"][conf] += 1

        # Update prestige score
        season_analysis["prestige_scores"] = season_analysis.get("prestige_scores", [])
        season_analysis["prestige_scores"].append(bowl_game.prestige_score)

    def _generate_season_outlook(
        self, bowl_predictions: List[Dict], season_analysis: Dict
    ) -> Dict:
        """Generate season outlook summary"""
        return {
            "most_prestigious_bowl": (
                max(bowl_predictions, key=lambda x: x.get("prestige_score", 0))[
                    "bowl_name"
                ]
                if bowl_predictions
                else ""
            ),
            "conference_champion_predictions": self._predict_conference_champions(
                bowl_predictions, season_analysis
            ),
            "close_matchups": len(
                [p for p in bowl_predictions if abs(p.get("advantage_score", 0)) < 10]
            ),
            "high_confidence_games": len(
                [
                    p
                    for p in bowl_predictions
                    if p["prediction"]["confidence"] in ["very_high", "high"]
                ]
            ),
        }

    def _predict_conference_champions(
        self, bowl_predictions: List[Dict], season_analysis: Dict
    ) -> Dict:
        """Predict conference champions based on bowl performances"""
        # Simplified implementation
        return {
            "SEC": "Alabama",
            "Big Ten": "Ohio State",
            "Big 12": "Texas",
            "ACC": "Florida State",
        }

    def _analyze_weather_effects(
        self, bowl_game: BowlGame, weather_forecast: Dict
    ) -> Dict:
        """Analyze weather effects on game outcome"""
        impact_score = 0.0
        affected_team = None
        impact_magnitude = "moderate"

        # Check temperature
        temperature = weather_forecast.get("temperature", 70)
        if temperature < 32:
            impact_score += self.weather_impact_factors["extreme_cold"]
            affected_team = "cold_weather_teams"
        elif temperature > 90:
            impact_score += self.weather_impact_factors["extreme_heat"]

        # Check precipitation
        precipitation = weather_forecast.get("precipitation", 0)
        if precipitation > 0.5:
            impact_score += self.weather_impact_factors["heavy_rain"]

        # Check wind
        wind_speed = weather_forecast.get("wind_speed", 0)
        if wind_speed > 15:
            impact_score += self.weather_impact_factors["strong_wind"]

        # Check for snow
        if weather_forecast.get("snow", False):
            impact_score += self.weather_impact_factors["snow"]

        # Determine impact magnitude
        if abs(impact_score) > 0.15:
            impact_magnitude = "severe"
        elif abs(impact_score) > 0.08:
            impact_magnitude = "moderate"
        else:
            impact_magnitude = "minor"

        return {
            "impact_score": impact_score,
            "affected_team": affected_team,
            "impact_magnitude": impact_magnitude,
            "temperature_effect": self._get_temperature_effect(temperature),
            "precipitation_effect": self._get_precipitation_effect(precipitation),
            "wind_effect": self._get_wind_effect(wind_speed),
        }

    def _adjust_predictions_for_weather(
        self, bowl_game: BowlGame, weather_impact: Dict
    ) -> Dict:
        """Adjust predictions based on weather impact"""
        return {
            "adjusted_winner": bowl_game.home_team,  # Would apply logic here
            "adjusted_margin": 3.0,
            "confidence_adjustment": -0.1,
            "weather_factor": weather_impact.get("impact_score", 0),
        }

    def _identify_weather_risk_factors(self, weather_forecast: Dict) -> List[Dict]:
        """Identify weather risk factors"""
        risks = []

        if weather_forecast.get("temperature", 70) < 20:
            risks.append(
                {
                    "risk": "extreme_cold",
                    "severity": "high",
                    "impact": "Affects passing game and player comfort",
                }
            )

        if weather_forecast.get("precipitation", 0) > 1.0:
            risks.append(
                {
                    "risk": "heavy_precipitation",
                    "severity": "medium",
                    "impact": "Could lead to fumbles and reduced field position",
                }
            )

        return risks

    def _generate_weather_insights(
        self, weather_impact: Dict, bowl_game: BowlGame
    ) -> List[str]:
        """Generate weather insights"""
        insights = []

        if weather_impact.get("impact_score", 0) != 0:
            insights.append(
                f"Weather conditions may favor {weather_impact.get('affected_team', 'adjustments')}"
            )

        if weather_impact.get("impact_magnitude") == "severe":
            insights.append(
                "Severe weather expected - game could be significantly affected"
            )

        return insights

    def _perform_weather_sensitivity_analysis(
        self, bowl_game: BowlGame, weather_impact: Dict
    ) -> Dict:
        """Perform sensitivity analysis for weather conditions"""
        return {
            "temperature_sensitivity": self._test_temperature_sensitivity(bowl_game),
            "precipitation_sensitivity": self._test_precipitation_sensitivity(
                bowl_game
            ),
            "wind_sensitivity": self._test_wind_sensitivity(bowl_game),
        }

    # Temperature and precipitation effect analysis methods
    def _get_temperature_effect(self, temperature: float) -> Dict:
        """Get temperature effect on game"""
        if temperature < 32:
            return {
                "effect": "negative",
                "impact": "cold_weather_favors_defense",
                "severity": "high",
            }
        elif temperature > 90:
            return {
                "effect": "negative",
                "impact": "heat_affects_conditioning",
                "severity": "medium",
            }
        else:
            return {
                "effect": "neutral",
                "impact": "ideal_conditions",
                "severity": "low",
            }

    def _get_precipitation_effect(self, precipitation: float) -> Dict:
        """Get precipitation effect on game"""
        if precipitation > 1.0:
            return {
                "effect": "negative",
                "impact": "reduces_passing_effectiveness",
                "severity": "high",
            }
        elif precipitation > 0.1:
            return {
                "effect": "slightly_negative",
                "impact": "minor_passing_impact",
                "severity": "low",
            }
        else:
            return {
                "effect": "neutral",
                "impact": "no_precipitation",
                "severity": "none",
            }

    def _get_wind_effect(self, wind_speed: float) -> Dict:
        """Get wind effect on game"""
        if wind_speed > 20:
            return {
                "effect": "negative",
                "impact": "affects_kicking_and_passing",
                "severity": "high",
            }
        elif wind_speed > 10:
            return {
                "effect": "slightly_negative",
                "impact": "minor_kicking_impact",
                "severity": "low",
            }
        else:
            return {
                "effect": "neutral",
                "impact": "minimal_wind_impact",
                "severity": "none",
            }

    # Additional test methods for sensitivity analysis
    def _test_temperature_sensitivity(self, bowl_game: BowlGame) -> Dict:
        """Test temperature sensitivity"""
        return {"sensitivity_score": 0.3, "optimal_range": "60-80°F"}

    def _test_precipitation_sensitivity(self, bowl_game: BowlGame) -> Dict:
        """Test precipitation sensitivity"""
        return {"sensitivity_score": 0.4, "optimal_conditions": "no_precipitation"}

    def _test_wind_sensitivity(self, bowl_game: BowlGame) -> Dict:
        """Test wind sensitivity"""
        return {"sensitivity_score": 0.2, "optimal_conditions": "<10mph"}

    # Historical analysis methods
    def _analyze_historical_patterns(self, similar_games: List[Dict]) -> Dict:
        """Analyze patterns from similar historical games"""
        if not similar_games:
            return {"patterns": [], "trends": []}

        # Calculate win percentages
        home_wins = sum(
            1
            for game in similar_games
            if game.get("result") == game.get("teams", {}).get("home")
        )
        total_games = len(similar_games)

        return {
            "patterns": [
                {
                    "pattern": "home_team_advantage",
                    "frequency": home_wins / total_games,
                    "significance": (
                        "high" if home_wins / total_games > 0.6 else "medium"
                    ),
                }
            ],
            "trends": [
                {
                    "trend": "average_margin",
                    "value": np.mean([game.get("margin", 0) for game in similar_games]),
                }
            ],
        }

    def _generate_historical_prediction_insights(
        self, similar_games: List[Dict], patterns: Dict
    ) -> List[str]:
        """Generate prediction insights from historical analysis"""
        insights = []

        if similar_games:
            home_win_rate = sum(
                1
                for game in similar_games
                if game.get("result") == game.get("teams", {}).get("home")
            ) / len(similar_games)

            if home_win_rate > 0.6:
                insights.append("Historical pattern favors home team")
            elif home_win_rate < 0.4:
                insights.append("Historical pattern favors away team")
            else:
                insights.append("Historical pattern shows no clear advantage")

        return insights

    def _calculate_historical_statistics(self, similar_games: List[Dict]) -> Dict:
        """Calculate statistical measures from historical games"""
        if not similar_games:
            return {}

        margins = [game.get("margin", 0) for game in similar_games]

        return {
            "sample_size": len(similar_games),
            "average_margin": np.mean(margins),
            "median_margin": np.median(margins),
            "margin_std": np.std(margins),
            "margin_range": {"min": min(margins), "max": max(margins)},
        }

    # Additional helper methods
    def _calculate_historical_ranking_diff(
        self, historical_game: Dict
    ) -> Optional[int]:
        """Calculate ranking differential from historical game"""
        # Implementation would extract ranking data from historical game
        return 5  # Placeholder

    def _has_conference_match(self, historical_game: Dict, bowl_game: BowlGame) -> bool:
        """Check if historical game has conference match"""
        # Implementation would compare conference affiliations
        return True  # Placeholder

    def _calculate_overall_advantage(
        self, matchup_analysis: TeamMatchupAnalysis
    ) -> float:
        """Calculate overall advantage from matchup analysis"""
        return matchup_analysis.overall_advantage_score

    def _identify_key_matchup_factors(
        self, matchup_analysis: TeamMatchupAnalysis
    ) -> List[Dict]:
        """Identify key factors influencing matchup"""
        factors = []

        if abs(matchup_analysis.ranking_differential) > 0:
            factors.append(
                {
                    "factor": "ranking_differential",
                    "impact": "high",
                    "value": matchup_analysis.ranking_differential,
                }
            )

        return factors

    def _generate_matchup_insights(
        self, matchup_analysis: TeamMatchupAnalysis, bowl_game: BowlGame
    ) -> List[str]:
        """Generate insights from matchup analysis"""
        insights = []

        if abs(matchup_analysis.overall_advantage_score) > 20:
            insights.append("Clear advantage detected in matchup")
        elif abs(matchup_analysis.overall_advantage_score) < 5:
            insights.append("Very close matchup expected")

        return insights


# Agent registration function
def register_bowl_games_specialist_agent():
    """Register the bowl games specialist agent with the system"""
    agent = BowlGamesSpecialistAgent()

    registration_details = {
        "agent_id": agent.agent_id,
        "agent_name": agent.agent_name,
        "class_name": "BowlGamesSpecialistAgent",
        "file_path": __file__,
        "created_by": "system_architect",
        "capabilities": [
            "analyze_bowl_matchup",
            "predict_bowl_game",
            "analyze_bowl_season",
            "weather_impact_analysis",
            "historical_comparison",
        ],
        "dependencies": [
            "enhanced_agent_framework",
            "security_manager",
            "pandas",
            "numpy",
        ],
        "max_execution_time": 600,  # 10 minutes
        "memory_limit_mb": 1024,
        "security_tier": 4,
        "permission_level": "READ_EXECUTE",
        "specialization": "bowl_games_prediction",
    }

    return agent, registration_details


# Example usage and testing
if __name__ == "__main__":
    # Create agent
    agent = BowlGamesSpecialistAgent()

    # Test bowl matchup analysis
    test_bowl_game = {
        "game_id": "rose_bowl_2025",
        "bowl_name": "Rose Bowl",
        "bowl_tier": "major_bowls",
        "season": 2025,
        "date": "2025-01-01T17:00:00Z",
        "location": "Pasadena, CA",
        "home_team": "Ohio State",
        "away_team": "Oregon",
        "conference_affiliation": {"Ohio State": "Big Ten", "Oregon": "Big Ten"},
        "neutral_site": True,
    }

    result = agent.execute_action(
        "analyze_bowl_matchup",
        {
            "bowl_game": test_bowl_game,
            "analysis_depth": "comprehensive",
            "include_historical": True,
        },
    )
    print("Bowl Matchup Analysis Result:")
    print(json.dumps(result, indent=2))
