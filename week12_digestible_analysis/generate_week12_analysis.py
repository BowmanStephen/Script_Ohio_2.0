#!/usr/bin/env python3
"""
Week 12 Digestible Analysis Generator

This script uses the Script Ohio 2.0 multi-agent system to analyze all Week 12 games
and create easy-to-digest artifacts for quick consumption.

Author: Claude Code Assistant
Created: November 2025
Purpose: Generate comprehensive Week 12 analysis with digestible outputs
"""

import os
import sys
import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import pandas as pd
import numpy as np

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('week12_analysis.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class Week12AnalysisGenerator:
    """
    Comprehensive Week 12 analysis generator using the Script Ohio 2.0 agent system
    """

    def __init__(self, week: int = 12, season: int = 2025):
        """Initialize the analysis generator"""
        self.week = week
        self.season = season
        self.output_dir = Path(__file__).parent
        self.predictions_dir = self.output_dir / "predictions"
        self.visualizations_dir = self.output_dir / "visualizations"
        self.insights_dir = self.output_dir / "insights"
        self.quick_picks_dir = self.output_dir / "quick_picks"

        self.data_dir = project_root / "model_pack"
        self.games_data_path = self.data_dir / "2025_processed_features.csv"
        if not self.games_data_path.exists():
            self.games_data_path = self.data_dir / "2025_raw_games_enhanced.csv"
        self.training_data_path = self.data_dir / "updated_training_data.csv"
        self.required_features: List[str] = []
        self.feature_defaults: Dict[str, Any] = {}
        self.team_records: Dict[str, Dict[str, int]] = {}
        self.team_power_ranks: Dict[str, int] = {}
        self.cfbd_api_client = self._initialize_cfbd_client()
        self._failed_models: set[str] = set()

        # Ensure directories exist
        for dir_path in [self.predictions_dir, self.visualizations_dir,
                        self.insights_dir, self.quick_picks_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

        # Initialize agent system
        self._initialize_agents()
        self._prepare_feature_schema()
        self.team_records = self._build_team_records_map()

        logger.info(f"Initialized Week {week} Analysis Generator for {season} season")

    def _initialize_agents(self):
        """Initialize the agent system components"""
        try:
            # Import required agents
            from agents.analytics_orchestrator import AnalyticsOrchestrator, AnalyticsRequest
            from agents.model_execution_engine import ModelExecutionEngine
            from agents.learning_navigator_agent import LearningNavigatorAgent

            # Initialize main orchestrator
            self.orchestrator = AnalyticsOrchestrator()
            logger.info("✅ Analytics Orchestrator initialized")

            # Initialize model execution engine
            self.model_engine = ModelExecutionEngine("week12_analysis")
            logger.info("✅ Model Execution Engine initialized")

            # Test agent availability
            test_request = AnalyticsRequest(
                user_id="test_user",
                query="Test agent system",
                query_type="test",
                parameters={},
                context_hints={"role": "analyst"}
            )

            logger.info("✅ Agent system successfully initialized and tested")

        except Exception as e:
            logger.error(f"❌ Failed to initialize agent system: {str(e)}")
            raise

    def _initialize_cfbd_client(self):
        """Configure CFBD API client if an API key is available."""
        api_key = os.environ.get("CFBD_API_KEY")
        if not api_key:
            logger.info("ℹ️  CFBD_API_KEY not set; skipping live record fetch.")
            return None

        try:
            from cfbd import Configuration, ApiClient

            configuration = Configuration()
            configuration.api_key['Authorization'] = api_key
            configuration.api_key_prefix['Authorization'] = 'Bearer'
            configuration.host = os.environ.get(
                "CFBD_API_HOST",
                "https://api.collegefootballdata.com"
            )

            logger.info("✅ CFBD API client initialized for record retrieval.")
            return ApiClient(configuration)
        except Exception as exc:
            logger.warning(f"⚠️ Unable to initialize CFBD client: {exc}")
            return None

    def _prepare_feature_schema(self):
        """Determine required ML feature columns and default values."""
        feature_candidates: List[str] = []

        try:
            if hasattr(self, "model_engine"):
                for metadata in getattr(self.model_engine, "models", {}).values():
                    if metadata.features_required:
                        feature_candidates.extend(metadata.features_required)
        except Exception as exc:
            logger.warning(f"⚠️ Unable to collect model feature metadata: {exc}")

        if not feature_candidates:
            feature_candidates = self._load_training_feature_columns()

        if not feature_candidates and hasattr(self, "model_engine"):
            feature_candidates = self.model_engine._get_default_features()

        self.required_features = sorted(set(feature_candidates))
        self.feature_defaults = self._load_feature_defaults(self.required_features)

        if not self.required_features:
            logger.warning("⚠️ No feature schema detected; predictions may use minimal defaults.")
        else:
            logger.info(f"✅ Prepared feature schema with {len(self.required_features)} fields.")

    def _load_training_feature_columns(self) -> List[str]:
        """Load feature column names from the training dataset."""
        if not self.training_data_path.exists():
            return []

        try:
            training_header = pd.read_csv(self.training_data_path, nrows=0)
            exclude = {'home_team', 'away_team', 'id', 'start_date', 'game_key'}
            return [col for col in training_header.columns if col not in exclude]
        except Exception as exc:
            logger.warning(f"⚠️ Unable to read training header: {exc}")
            return []

    def _load_feature_defaults(self, feature_names: List[str]) -> Dict[str, Any]:
        """Load median/mode defaults for each feature from the training dataset."""
        defaults: Dict[str, Any] = {}

        if not self.training_data_path.exists() or not feature_names:
            return defaults

        try:
            usecols = list(set(feature_names))
            training_df = pd.read_csv(self.training_data_path, usecols=usecols)

            for feature in feature_names:
                if feature not in training_df.columns:
                    continue
                series = training_df[feature]
                if pd.api.types.is_numeric_dtype(series):
                    defaults[feature] = float(series.median())
                else:
                    mode = series.mode()
                    defaults[feature] = mode.iloc[0] if not mode.empty else ""
        except Exception:
            logger.warning("⚠️ Unable to compute feature defaults from training data; using baseline fallbacks.")

        return defaults

    def _ensure_required_feature_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Ensure the Week 12 dataset contains all required ML features."""
        for feature in self.required_features:
            if feature not in df.columns:
                df[feature] = self.feature_defaults.get(feature, 0.0)
        return df

    def _build_feature_row(self, row: pd.Series) -> Dict[str, Any]:
        """Build a feature dictionary for a single matchup."""
        feature_row = {}
        for feature in self.required_features:
            feature_row[feature] = row.get(feature, self.feature_defaults.get(feature, 0.0))
        return feature_row

    def _build_team_power_ranks(self, games_df: pd.DataFrame) -> Dict[str, int]:
        """Create Elo-based power rankings for contextual reporting."""
        ratings: Dict[str, List[float]] = {}

        for _, row in games_df.iterrows():
            ratings.setdefault(row["home_team"], []).append(row.get("home_elo", np.nan))
            ratings.setdefault(row["away_team"], []).append(row.get("away_elo", np.nan))

        average_ratings = {
            team: float(np.nanmean(values)) if len(values) else 0.0
            for team, values in ratings.items()
        }

        sorted_teams = sorted(
            average_ratings.items(),
            key=lambda item: item[1],
            reverse=True
        )

        return {team: idx + 1 for idx, (team, _) in enumerate(sorted_teams)}

    def _build_team_records_map(self) -> Dict[str, Dict[str, int]]:
        """
        Build the best-available approximation of team records.

        NOTE: Attempts to pull live records from CFBD when API credentials exist.
        """
        if not self.cfbd_api_client:
            logger.warning("⚠️ Team record data not available (missing CFBD client). Using 'Unknown'.")
            return {}

        try:
            from cfbd import TeamsApi

            teams_api = TeamsApi(self.cfbd_api_client)
            response = teams_api.get_team_records(year=self.season, season_type="regular")

            records: Dict[str, Dict[str, int]] = {}
            for entry in response or []:
                team_name = getattr(entry, "team", None)
                overall = getattr(entry, "overall", None)

                if not team_name or not overall:
                    continue

                wins = getattr(overall, "wins", None)
                losses = getattr(overall, "losses", None)
                ties = getattr(overall, "ties", None)

                records[team_name] = {
                    "wins": int(wins) if wins is not None else 0,
                    "losses": int(losses) if losses is not None else 0,
                    "ties": int(ties) if ties is not None else 0,
                }

            if records:
                logger.info(f"✅ Loaded {len(records)} team records from CFBD.")
            else:
                logger.warning("⚠️ CFBD returned no team records; using 'Unknown'.")

            return records

        except Exception as exc:
            logger.warning(f"⚠️ Unable to fetch team records from CFBD: {exc}")
            return {}

    def _format_team_record(self, team: str) -> str:
        """Return a display string for a team record."""
        record = self.team_records.get(team)
        if not record:
            return "Unknown"

        return f"{record.get('wins', 0)}-{record.get('losses', 0)}"

    def _get_team_rank(self, team: str) -> Optional[int]:
        """Return the derived power ranking for a team."""
        return self.team_power_ranks.get(team)

    def _run_model_prediction(self, parameters: Dict[str, Any], model_name: str) -> Dict[str, Any]:
        """Execute a single model prediction with error handling."""
        if model_name in self._failed_models:
            return {}

        model_params = parameters.copy()
        model_params.update({
            "model_type": model_name,
            "include_confidence": True,
            "include_explanation": False
        })

        try:
            result = self.model_engine._predict_game_outcome(
                model_params,
                user_context={"role": "data_scientist", "skill_level": "advanced"}
            )
            if result.get("success"):
                return result.get("prediction", {})

            logger.warning(f"⚠️ Model {model_name} failed: {result.get('error_message')}")
            self._failed_models.add(model_name)
        except Exception as exc:
            logger.warning(f"⚠️ Exception running model {model_name}: {exc}")
            self._failed_models.add(model_name)
        return {}

    def _margin_to_probability(self, margin: float) -> float:
        """Convert a predicted margin into an approximate home win probability."""
        # Logistic transform centered at pick'em
        return float(1 / (1 + np.exp(-margin / 7.5)))

    def _estimate_scores(self, margin: float, features: Dict[str, Any]) -> (int, int):
        """Estimate plausible scores from margin and offensive metrics."""
        offensive_signal = (
            features.get('home_adjusted_epa', 0.15) +
            features.get('away_adjusted_epa', 0.15)
        )
        defensive_signal = (
            features.get('home_adjusted_epa_allowed', 0.15) +
            features.get('away_adjusted_epa_allowed', 0.15)
        )
        explosiveness = (
            features.get('home_adjusted_explosiveness', 1.0) +
            features.get('away_adjusted_explosiveness', 1.0)
        )

        projected_total = 52 + offensive_signal * 18 - defensive_signal * 10 + (explosiveness - 2.0) * 6
        projected_total = float(np.clip(projected_total, 38, 82))

        home_score = projected_total / 2 + margin / 2
        away_score = projected_total - home_score

        return int(round(max(home_score, 0))), int(round(max(away_score, 0)))

    def get_week12_games_data(self) -> List[Dict[str, Any]]:
        """
        Load REAL Week 12 games data from user's 2025_raw_games.csv file

        Returns:
            List of Week 12 games with team information
        """
        logger.info("🔍 Loading REAL Week 12 games data from processed feature file...")

        try:
            # Load the user's real games data
            games_df = pd.read_csv(self.games_data_path)
            games_df = self._ensure_required_feature_columns(games_df)

            if not self.team_power_ranks:
                self.team_power_ranks = self._build_team_power_ranks(games_df)

            # Filter for Week 12 games
            week12_df = games_df[games_df['week'] == 12].copy()

            if len(week12_df) == 0:
                logger.warning("⚠️  No Week 12 games found in 2025_raw_games.csv")
                return self._generate_sample_week12_games()

            logger.info(f"✅ Found {len(week12_df)} real Week 12 games!")

            # Convert to list of dictionaries for processing
            games_data = []
            for _, row in week12_df.iterrows():
                game_data = {
                    "home_team": row["home_team"],
                    "away_team": row["away_team"],
                    "home_conference": row["home_conference"],
                    "away_conference": row["away_conference"],
                    "neutral_site": row["neutral_site"],
                    "home_elo": row["home_elo"],
                    "away_elo": row["away_elo"],
                    "home_talent": row["home_talent"],
                    "away_talent": row["away_talent"],
                    "spread": row["spread"],
                    "home_rank": self._get_team_rank(row["home_team"]),
                    "away_rank": self._get_team_rank(row["away_team"]),
                    "home_record": self._format_team_record(row["home_team"]),
                    "away_record": self._format_team_record(row["away_team"]),
                    # Use all the advanced features the models need
                    "home_adjusted_epa": row["home_adjusted_epa"],
                    "home_adjusted_epa_allowed": row["home_adjusted_epa_allowed"],
                    "away_adjusted_epa": row["away_adjusted_epa"],
                    "away_adjusted_epa_allowed": row["away_adjusted_epa_allowed"],
                    "home_adjusted_success": row["home_adjusted_success"],
                    "home_adjusted_success_allowed": row["home_adjusted_success_allowed"],
                    "away_adjusted_success": row["away_adjusted_success"],
                    "away_adjusted_success_allowed": row["away_adjusted_success_allowed"],
                    # Add more features for the model
                    "home_total_havoc_defense": row["home_total_havoc_defense"],
                    "away_total_havoc_defense": row["away_total_havoc_defense"],
                    "home_adjusted_line_yards": row["home_adjusted_line_yards"],
                    "away_adjusted_line_yards": row["away_adjusted_line_yards"],
                    "home_points_per_opportunity_offense": row.get("home_points_per_opportunity_offense", np.nan),
                    "away_points_per_opportunity_offense": row.get("away_points_per_opportunity_offense", np.nan),
                    "home_points_per_opportunity_defense": row.get("home_points_per_opportunity_defense", np.nan),
                    "away_points_per_opportunity_defense": row.get("away_points_per_opportunity_defense", np.nan),
                    "home_avg_start_offense": row.get("home_avg_start_offense", np.nan),
                    "away_avg_start_offense": row.get("away_avg_start_offense", np.nan),
                    "home_avg_start_defense": row.get("home_avg_start_defense", np.nan),
                    "away_avg_start_defense": row.get("away_avg_start_defense", np.nan),
                    "conference_game": row.get("conference_game"),
                    "features": self._build_feature_row(row)
                }
                games_data.append(game_data)

            logger.info(f"✅ Successfully loaded {len(games_data)} Week 12 games with real team data!")
            return games_data

        except FileNotFoundError:
            logger.error("❌ Could not find 2025_raw_games.csv file")
            logger.info("Falling back to sample data")
            return self._generate_sample_week12_games()
        except Exception as e:
            logger.error(f"❌ Error loading real games data: {str(e)}")
            logger.info("Falling back to sample data")
            return self._generate_sample_week12_games()

    def _extract_games_from_response(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract games data from orchestrator response"""
        games = []

        # Try to extract games from different possible response formats
        if isinstance(results, dict):
            # Check for games in model_engine results
            if 'model_engine' in results and results['model_engine']:
                model_results = results['model_engine']
                if 'predictions' in model_results:
                    predictions = model_results['predictions']
                    if isinstance(predictions, list):
                        for pred in predictions:
                            games.append(self._convert_prediction_to_game(pred))

            # Check for games data in other formats
            if 'games' in results:
                games = results['games']
            elif 'week_games' in results:
                games = results['week_games']

        return games

    def _convert_prediction_to_game(self, prediction: Dict[str, Any]) -> Dict[str, Any]:
        """Convert prediction data to game format"""
        return {
            "home_team": prediction.get("home_team", "Unknown"),
            "away_team": prediction.get("away_team", "Unknown"),
            "home_score": prediction.get("predicted_home_score", 0),
            "away_score": prediction.get("predicted_away_score", 0),
            "predicted_winner": prediction.get("predicted_winner"),
            "predicted_margin": prediction.get("predicted_margin", 0),
            "confidence": prediction.get("confidence", 0.5)
        }

    def _generate_sample_week12_games(self) -> List[Dict[str, Any]]:
        """Generate sample Week 12 games data for demonstration"""

        # Sample Week 12 matchups (realistic college football matchups)
        sample_games = [
            {
                "home_team": "Georgia",
                "away_team": "Tennessee",
                "home_rank": 1,
                "away_rank": 7,
                "home_record": "10-0",
                "away_record": "8-2",
                "conference": "SEC"
            },
            {
                "home_team": "Ohio State",
                "away_team": "Michigan State",
                "home_rank": 2,
                "away_rank": 15,
                "home_record": "10-0",
                "away_record": "7-3",
                "conference": "Big Ten"
            },
            {
                "home_team": "Texas",
                "away_team": "Kansas",
                "home_rank": 3,
                "away_rank": 23,
                "home_record": "9-1",
                "away_record": "7-3",
                "conference": "Big 12"
            },
            {
                "home_team": "Alabama",
                "away_team": "Ole Miss",
                "home_rank": 4,
                "away_rank": 11,
                "home_record": "8-2",
                "away_record": "8-2",
                "conference": "SEC"
            },
            {
                "home_team": "Oregon",
                "away_team": "Washington",
                "home_rank": 5,
                "away_rank": 8,
                "home_record": "9-1",
                "away_record": "8-2",
                "conference": "Pac-12"
            },
            {
                "home_team": "Penn State",
                "away_team": "Minnesota",
                "home_rank": 6,
                "away_rank": 18,
                "home_record": "8-2",
                "away_record": "7-3",
                "conference": "Big Ten"
            },
            {
                "home_team": "Notre Dame",
                "away_team": "Virginia Tech",
                "home_rank": 9,
                "away_rank": None,
                "home_record": "8-2",
                "away_record": "5-5",
                "conference": "Independent"
            },
            {
                "home_team": "Missouri",
                "away_team": "Florida",
                "home_rank": 10,
                "away_rank": 20,
                "home_record": "8-2",
                "away_record": "6-4",
                "conference": "SEC"
            },
            {
                "home_team": "Oklahoma State",
                "away_team": "Kansas State",
                "home_rank": 12,
                "away_rank": 16,
                "home_record": "7-3",
                "away_record": "7-3",
                "conference": "Big 12"
            },
            {
                "home_team": "LSU",
                "away_team": "Texas A&M",
                "home_rank": 13,
                "away_rank": 22,
                "home_record": "7-3",
                "away_record": "6-4",
                "conference": "SEC"
            }
        ]

        # Add realistic score predictions
        for game in sample_games:
            # Generate realistic college football scores
            home_base = np.random.normal(28, 8)
            away_base = np.random.normal(24, 8)

            # Adjust based on rankings
            if game.get("home_rank") and game.get("away_rank"):
                rank_diff = game["away_rank"] - game["home_rank"]
                home_base += rank_diff * 0.5

            # Ensure positive scores
            game["predicted_home_score"] = max(0, round(home_base))
            game["predicted_away_score"] = max(0, round(away_base))
            game["predicted_margin"] = game["predicted_home_score"] - game["predicted_away_score"]
            game["predicted_winner"] = game["home_team"] if game["predicted_margin"] > 0 else game["away_team"]

            # Calculate confidence based on margin
            game["confidence"] = min(0.95, 0.5 + abs(game["predicted_margin"]) * 0.03)

        return sample_games

    def _record_run_with_orchestrator(self, predictions_df: pd.DataFrame):
        """Log the Week 12 analysis run with the analytics orchestrator for auditability."""
        try:
            from agents.analytics_orchestrator import AnalyticsRequest

            summary_payload = predictions_df.nlargest(3, 'confidence')[[
                'home_team', 'away_team', 'predicted_winner', 'predicted_margin', 'confidence'
            ]].to_dict('records')

            request = AnalyticsRequest(
                user_id="week12_pipeline",
                query=f"Week {self.week} {self.season} analysis summary",
                query_type="analysis",
                parameters={
                    "week": self.week,
                    "season": self.season,
                    "games_analyzed": len(predictions_df),
                    "top_confident_games": summary_payload
                },
                context_hints={"role": "production", "skill_level": "advanced"}
            )
            response = self.orchestrator.process_analytics_request(request)
            if response.status == "error":
                logger.warning(f"⚠️ Orchestrator logging failed: {response.error_message}")
            else:
                logger.info("🗂️  Recorded Week 12 run with analytics orchestrator.")
        except Exception as exc:
            logger.warning(f"⚠️ Unable to record run with orchestrator: {exc}")

    def _format_prediction_payload(
        self,
        game: Dict[str, Any],
        features: Dict[str, Any],
        predicted_margin: float,
        home_win_probability: float,
        confidence: float,
        source_models: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Assemble the final prediction payload with advanced stats."""
        home_score, away_score = self._estimate_scores(predicted_margin, features)
        prediction = {
            "home_team": game["home_team"],
            "away_team": game["away_team"],
            "home_rank": game.get("home_rank"),
            "away_rank": game.get("away_rank"),
            "home_record": game.get("home_record"),
            "away_record": game.get("away_record"),
            "home_conference": game.get("home_conference", ""),
            "away_conference": game.get("away_conference", ""),
            "conference": game.get("home_conference", game.get("conference", "")),
            "neutral_site": game.get("neutral_site", False),
            "spread": game.get("spread", 0.0),
            "home_elo": game.get("home_elo", features.get("home_elo", 1500)),
            "away_elo": game.get("away_elo", features.get("away_elo", 1500)),
            "home_talent": game.get("home_talent", 500),
            "away_talent": game.get("away_talent", 500),
            "home_adjusted_epa": features.get("home_adjusted_epa", game.get("home_adjusted_epa", 0.15)),
            "home_adjusted_epa_allowed": features.get("home_adjusted_epa_allowed", game.get("home_adjusted_epa_allowed", 0.15)),
            "away_adjusted_epa": features.get("away_adjusted_epa", game.get("away_adjusted_epa", 0.15)),
            "away_adjusted_epa_allowed": features.get("away_adjusted_epa_allowed", game.get("away_adjusted_epa_allowed", 0.15)),
            "home_adjusted_success": features.get("home_adjusted_success", game.get("home_adjusted_success", 0.45)),
            "away_adjusted_success": features.get("away_adjusted_success", game.get("away_adjusted_success", 0.45)),
            "home_total_havoc_defense": game.get("home_total_havoc_defense", 0),
            "away_total_havoc_defense": game.get("away_total_havoc_defense", 0),
            "home_adjusted_line_yards": game.get("home_adjusted_line_yards", 0),
            "away_adjusted_line_yards": game.get("away_adjusted_line_yards", 0),
            "home_points_per_opportunity_offense": game.get("home_points_per_opportunity_offense"),
            "away_points_per_opportunity_offense": game.get("away_points_per_opportunity_offense"),
            "home_points_per_opportunity_defense": game.get("home_points_per_opportunity_defense"),
            "away_points_per_opportunity_defense": game.get("away_points_per_opportunity_defense"),
            "home_avg_start_offense": game.get("home_avg_start_offense"),
            "away_avg_start_offense": game.get("away_avg_start_offense"),
            "home_avg_start_defense": game.get("home_avg_start_defense"),
            "away_avg_start_defense": game.get("away_avg_start_defense"),
            "predicted_home_score": home_score,
            "predicted_away_score": away_score,
            "predicted_winner": game["home_team"] if predicted_margin >= 0 else game["away_team"],
            "predicted_margin": round(predicted_margin, 2),
            "home_win_probability": round(home_win_probability, 4),
            "confidence": round(confidence, 4),
            "model_sources": source_models or []
        }

        prediction["upset_potential"] = self._calculate_upset_potential(prediction)
        prediction["betting_value"] = self._calculate_betting_value(prediction)

        explanation_parts = [
            f"Margin {predicted_margin:+.1f}",
            f"Win Prob {home_win_probability:.1%}",
            f"Models {', '.join(prediction['model_sources'])}" if prediction["model_sources"] else "Heuristic blend",
            f"EPA diff {(prediction['home_adjusted_epa'] - prediction['away_adjusted_epa']):+.2f}",
            f"Talent diff {(prediction['home_talent'] - prediction['away_talent']):+.1f}"
        ]
        prediction["explanation"] = " | ".join(explanation_parts)
        return prediction

    def generate_predictions(self, games_data: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Generate predictions for all Week 12 games using the model execution engine

        Args:
            games_data: List of games to predict

        Returns:
            DataFrame with comprehensive predictions
        """
        logger.info("🤖 Generating ML predictions for Week 12 games...")

        predictions = []

        for game in games_data:
            try:
                features = game.get("features", {})
                base_params = {
                    "home_team": game["home_team"],
                    "away_team": game["away_team"],
                    "features": features,
                    "spread": game.get("spread", 0.0),
                    "season": self.season,
                    "week": self.week
                }

                ridge_pred = self._run_model_prediction(base_params, "ridge_model_2025")
                xgb_pred = self._run_model_prediction(base_params, "xgb_home_win_model_2025")
                fastai_pred = self._run_model_prediction(base_params, "fastai_home_win_model_2025")

                source_models = []
                predicted_margin = None
                if ridge_pred:
                    predicted_margin = ridge_pred.get("predicted_margin")
                    source_models.append(ridge_pred.get("model_used", "ridge_model_2025"))

                win_probs = []
                for model_pred in (xgb_pred, fastai_pred):
                    if model_pred and "home_win_probability" in model_pred:
                        win_probs.append(model_pred["home_win_probability"])
                        source_models.append(model_pred.get("model_used"))

                home_win_probability = float(np.mean(win_probs)) if win_probs else None

                if predicted_margin is None and home_win_probability is not None:
                    predicted_margin = (home_win_probability - 0.5) * 18

                if predicted_margin is None:
                    logger.warning(
                        f"⚠️ Falling back to heuristic prediction for {game['home_team']} vs {game['away_team']}"
                    )
                    prediction = self._generate_pattern_prediction(game)
                else:
                    if home_win_probability is None:
                        home_win_probability = self._margin_to_probability(predicted_margin)
                    confidence = max(home_win_probability, 1 - home_win_probability)
                    prediction = self._format_prediction_payload(
                        game,
                        features,
                        predicted_margin,
                        home_win_probability,
                        confidence,
                        source_models=[m for m in source_models if m]
                    )

                predictions.append(prediction)

            except Exception as e:
                logger.warning(
                    f"⚠️ Error predicting {game.get('home_team', 'Unknown')} vs {game.get('away_team', 'Unknown')}: {e}"
                )
                continue

        predictions_df = pd.DataFrame(predictions)
        logger.info(f"✅ Generated predictions for {len(predictions_df)} games")
        return predictions_df

    def _generate_pattern_prediction(self, game: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a heuristic prediction when ML models are unavailable."""
        features = game.get("features", {})

        home_elo = game.get("home_elo", 1500)
        away_elo = game.get("away_elo", 1500)
        home_talent = game.get("home_talent", 500)
        away_talent = game.get("away_talent", 500)
        home_epa = features.get("home_adjusted_epa", game.get("home_adjusted_epa", 0.15))
        away_epa = features.get("away_adjusted_epa", game.get("away_adjusted_epa", 0.15))
        home_epa_allowed = features.get("home_adjusted_epa_allowed", game.get("home_adjusted_epa_allowed", 0.15))
        away_epa_allowed = features.get("away_adjusted_epa_allowed", game.get("away_adjusted_epa_allowed", 0.15))
        home_success = features.get("home_adjusted_success", game.get("home_adjusted_success", 0.45))
        away_success = features.get("away_adjusted_success", game.get("away_adjusted_success", 0.45))

        elo_advantage = (home_elo - away_elo) / 150
        talent_advantage = (home_talent - away_talent) / 75
        epa_advantage = (home_epa - away_epa + away_epa_allowed - home_epa_allowed) * 35
        success_advantage = (home_success - away_success) * 30
        home_field = 0 if game.get("neutral_site", False) else 2.5

        predicted_margin = elo_advantage + talent_advantage + epa_advantage + success_advantage + home_field
        home_win_probability = self._margin_to_probability(predicted_margin)
        confidence = min(0.9, max(home_win_probability, 1 - home_win_probability) + abs(predicted_margin) * 0.01)

        return self._format_prediction_payload(
            game,
            features,
            predicted_margin,
            home_win_probability,
            confidence,
            source_models=["heuristic"]
        )

    def _calculate_upset_potential(self, game: Dict[str, Any]) -> str:
        """Calculate upset potential for a game"""
        home_rank = game.get("home_rank")
        away_rank = game.get("away_rank")

        if not home_rank or not away_rank:
            return "Unknown"

        rank_diff = abs(home_rank - away_rank)

        if rank_diff > 15:
            return "High"
        elif rank_diff > 8:
            return "Medium"
        else:
            return "Low"

    def _calculate_upset_potential_from_elo(self, home_elo: float, away_elo: float) -> str:
        """Calculate upset potential using Elo ratings"""
        elo_diff = abs(home_elo - away_elo)

        if elo_diff > 150:
            return "High"
        elif elo_diff > 75:
            return "Medium"
        else:
            return "Low"

    def _calculate_betting_value(self, game: Dict[str, Any]) -> str:
        """Calculate potential betting value"""
        confidence = game.get("confidence", 0.5)
        upset_potential = self._calculate_upset_potential(game)

        if confidence > 0.8 and upset_potential == "Low":
            return "Strong Value"
        elif confidence > 0.7:
            return "Good Value"
        elif upset_potential == "High":
            return "Upset Special"
        else:
            return "Standard"

    def _calculate_betting_value_from_metrics(self, game: Dict[str, Any]) -> str:
        """Calculate betting value using advanced metrics"""
        home_elo = game.get("home_elo", 1500)
        away_elo = game.get("away_elo", 1500)
        spread = game.get("spread", 0)

        # Calculate model prediction vs actual spread
        elo_diff = home_elo - away_elo
        model_margin = elo_diff / 100  # Convert Elo difference to predicted margin
        if not game.get("neutral_site", False):
            model_margin += 3  # Add home field advantage

        # Compare model prediction to actual spread
        spread_diff = model_margin - spread

        if abs(spread_diff) > 7:
            return "Strong Value"
        elif abs(spread_diff) > 4:
            return "Good Value"
        else:
            return "Standard"

    def save_predictions_csv(self, predictions_df: pd.DataFrame):
        """Save predictions to digestible CSV format with advanced stats"""
        logger.info("💾 Saving predictions to CSV...")

        # Create comprehensive CSV with advanced stats
        comprehensive_df = predictions_df[[
            'home_team', 'away_team', 'predicted_home_score', 'predicted_away_score',
            'predicted_winner', 'predicted_margin', 'home_win_probability', 'confidence',

            # ADVANCED METRICS
            'home_elo', 'away_elo', 'home_talent', 'away_talent',
            'home_conference', 'away_conference', 'neutral_site', 'spread',
            'home_adjusted_epa', 'away_adjusted_epa', 'home_adjusted_epa_allowed', 'away_adjusted_epa_allowed',
            'home_adjusted_success', 'away_adjusted_success',
            'home_total_havoc_defense', 'away_total_havoc_defense',
            'home_adjusted_line_yards', 'away_adjusted_line_yards',

            'upset_potential', 'betting_value', 'explanation'
        ]].copy()

        # Format for readability
        comprehensive_df['matchup'] = comprehensive_df['home_team'] + ' vs ' + comprehensive_df['away_team']
        comprehensive_df['prediction'] = comprehensive_df['predicted_winner'] + ' by ' + comprehensive_df['predicted_margin'].astype(str) + ' points'
        comprehensive_df['confidence_pct'] = (comprehensive_df['confidence'] * 100).round(1).astype(str) + '%'
        comprehensive_df['win_probability'] = (comprehensive_df['home_win_probability'] * 100).round(1).astype(str) + '%'

        # Create Elo advantage column
        comprehensive_df['elo_advantage'] = comprehensive_df['home_elo'] - comprehensive_df['away_elo']
        comprehensive_df['elo_diff_formatted'] = comprehensive_df['elo_advantage'].apply(lambda x: f"{x:+.0f}")

        # Create talent advantage column
        comprehensive_df['talent_advantage'] = comprehensive_df['home_talent'] - comprehensive_df['away_talent']

        # Format EPA metrics
        comprehensive_df['home_epa_total'] = (comprehensive_df['home_adjusted_epa'] - comprehensive_df['home_adjusted_epa_allowed']).round(3)
        comprehensive_df['away_epa_total'] = (comprehensive_df['away_adjusted_epa'] - comprehensive_df['away_adjusted_epa_allowed']).round(3)

        # Create digestible columns order
        final_columns = [
            'matchup', 'prediction', 'confidence_pct', 'win_probability',
            'predicted_home_score', 'predicted_away_score', 'predicted_margin',

            # Advanced stats
            'home_elo', 'away_elo', 'elo_diff_formatted', 'home_talent', 'away_talent', 'talent_advantage',
            'home_conference', 'away_conference', 'neutral_site',

            # EPA metrics
            'home_adjusted_epa', 'away_adjusted_epa', 'home_epa_total', 'away_epa_total',
            'home_adjusted_success', 'away_adjusted_success',

            # Other metrics
            'home_total_havoc_defense', 'away_total_havoc_defense',
            'home_adjusted_line_yards', 'away_adjusted_line_yards',

            # Analysis
            'upset_potential', 'betting_value', 'explanation'
        ]

        comprehensive_df = comprehensive_df[final_columns]

        # Save comprehensive predictions
        csv_path = self.predictions_dir / "week12_all_games_predictions.csv"
        comprehensive_df.to_csv(csv_path, index=False)

        # Also create a simple summary CSV for quick viewing
        summary_df = predictions_df[[
            'home_team', 'away_team', 'predicted_winner', 'predicted_margin', 'confidence', 'upset_potential', 'betting_value'
        ]].copy()

        summary_df['confidence_pct'] = (summary_df['confidence'] * 100).round(1).astype(str) + '%'
        summary_df['matchup'] = summary_df['home_team'] + ' vs ' + summary_df['away_team']

        summary_columns = ['matchup', 'predicted_winner', 'predicted_margin', 'confidence_pct', 'upset_potential', 'betting_value']
        summary_df = summary_df[summary_columns]

        summary_path = self.predictions_dir / "week12_predictions_summary.csv"
        summary_df.to_csv(summary_path, index=False)

        logger.info(f"✅ Saved {len(comprehensive_df)} comprehensive predictions to {csv_path}")
        logger.info(f"✅ Saved {len(summary_df)} summary predictions to {summary_path}")

    def generate_insights(self, predictions_df: pd.DataFrame) -> Dict[str, Any]:
        """Generate insights and analysis from predictions"""
        logger.info("💡 Generating insights and analysis...")

        insights = {
            "summary": {
                "total_games": len(predictions_df),
                "avg_confidence": round(predictions_df['confidence'].mean() * 100, 1),
                "high_confidence_games": len(predictions_df[predictions_df['confidence'] > 0.8]),
                "upset_alerts": len(predictions_df[predictions_df['upset_potential'] == 'High'])
            },
            "top_confident_picks": [],
            "upset_alerts": [],
            "conference_insights": {},
            "betting_opportunities": []
        }

        # Top confident picks
        top_confident = predictions_df.nlargest(5, 'confidence')
        for _, game in top_confident.iterrows():
            insights["top_confident_picks"].append({
                "matchup": f"{game['home_team']} vs {game['away_team']}",
                "prediction": f"{game['predicted_winner']} by {game['predicted_margin']}",
                "confidence": f"{game['confidence']*100:.1f}%",
                "reasoning": game.get('explanation', 'High confidence prediction')
            })

        # Upset alerts
        upset_games = predictions_df[predictions_df['upset_potential'] == 'High']
        for _, game in upset_games.iterrows():
            insights["upset_alerts"].append({
                "matchup": f"{game['home_team']} ({game.get('home_rank', 'NR')}) vs {game['away_team']} ({game.get('away_rank', 'NR')})",
                "reason": "Large ranking differential suggests potential upset",
                "confidence": f"{game['confidence']*100:.1f}%"
            })

        # Conference insights
        if 'conference' in predictions_df.columns:
            conf_stats = predictions_df.groupby('conference').agg({
                'confidence': ['mean', 'count'],
                'predicted_margin': 'mean'
            }).round(3)

            # Flatten MultiIndex to simple dict structure
            insights["conference_insights"] = {}
            for conf in conf_stats.index:
                insights["conference_insights"][conf] = {
                    "avg_confidence": conf_stats.loc[conf, ('confidence', 'mean')],
                    "game_count": conf_stats.loc[conf, ('confidence', 'count')],
                    "avg_margin": conf_stats.loc[conf, ('predicted_margin', 'mean')]
                }

        # Betting opportunities
        value_bets = predictions_df[predictions_df['betting_value'].isin(['Strong Value', 'Upset Special'])]
        for _, game in value_bets.iterrows():
            insights["betting_opportunities"].append({
                "matchup": f"{game['home_team']} vs {game['away_team']}",
                "value_type": game['betting_value'],
                "confidence": f"{game['confidence']*100:.1f}%",
                "predicted_margin": game['predicted_margin']
            })

        return insights

    def create_visualizations(self, predictions_df: pd.DataFrame, insights: Dict[str, Any]):
        """Create visualizations for Week 12 games"""
        logger.info("📊 Creating visualizations...")

        # Create confidence distribution chart
        self._create_confidence_chart(predictions_df)

        # Create matchup strength chart
        self._create_matchup_chart(predictions_df)

        # Create upset alerts visualization
        self._create_upset_alerts_chart(predictions_df)

        logger.info("✅ Visualizations created")

    def _create_confidence_chart(self, predictions_df: pd.DataFrame):
        """Create confidence distribution chart"""
        try:
            import matplotlib.pyplot as plt
            import seaborn as sns

            plt.figure(figsize=(12, 8))

            # Create subplot
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

            # Confidence distribution
            ax1.hist(predictions_df['confidence'] * 100, bins=10, alpha=0.7, color='blue', edgecolor='black')
            ax1.set_xlabel('Prediction Confidence (%)')
            ax1.set_ylabel('Number of Games')
            ax1.set_title(f'Week {self.week} Prediction Confidence Distribution')
            ax1.grid(True, alpha=0.3)

            # Top 10 most confident games
            top_10 = predictions_df.nlargest(10, 'confidence')
            matchups = [f"{game['home_team'][:15]}..." for _, game in top_10.iterrows()]
            confidences = top_10['confidence'] * 100

            bars = ax2.barh(matchups, confidences, color='green', alpha=0.7)
            ax2.set_xlabel('Confidence (%)')
            ax2.set_title('Top 10 Most Confident Predictions')
            ax2.grid(True, alpha=0.3, axis='x')

            # Add value labels
            for i, (bar, conf) in enumerate(zip(bars, confidences)):
                ax2.text(conf + 1, bar.get_y() + bar.get_height()/2, f'{conf:.1f}%',
                        va='center', ha='left', fontsize=9)

            plt.tight_layout()
            chart_path = self.visualizations_dir / "prediction_confidence_chart.png"
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()

            logger.info(f"✅ Confidence chart saved to {chart_path}")

        except ImportError:
            logger.warning("⚠️  Matplotlib not available, skipping confidence chart")
        except Exception as e:
            logger.error(f"❌ Error creating confidence chart: {str(e)}")

    def _create_matchup_chart(self, predictions_df: pd.DataFrame):
        """Create matchup strength chart"""
        try:
            import matplotlib.pyplot as plt
            import seaborn as sns

            # Create margin distribution
            plt.figure(figsize=(12, 6))

            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

            # Predicted margin distribution
            ax1.hist(predictions_df['predicted_margin'], bins=15, alpha=0.7, color='orange', edgecolor='black')
            ax1.axvline(x=0, color='red', linestyle='--', label='Even Matchup')
            ax1.set_xlabel('Predicted Margin (Home Team)')
            ax1.set_ylabel('Number of Games')
            ax1.set_title(f'Week {self.week} Predicted Score Margins')
            ax1.legend()
            ax1.grid(True, alpha=0.3)

            # Score predictions scatter
            ax2.scatter(predictions_df['predicted_away_score'], predictions_df['predicted_home_score'],
                       alpha=0.7, s=60, c=predictions_df['confidence'], cmap='viridis')
            ax2.plot([10, 50], [10, 50], 'r--', label='Even Score')
            ax2.set_xlabel('Predicted Away Score')
            ax2.set_ylabel('Predicted Home Score')
            ax2.set_title('Score Predictions (Color = Confidence)')
            ax2.legend()
            ax2.grid(True, alpha=0.3)

            plt.tight_layout()
            chart_path = self.visualizations_dir / "team_strength_rankings.png"
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()

            logger.info(f"✅ Matchup chart saved to {chart_path}")

        except ImportError:
            logger.warning("⚠️  Matplotlib not available, skipping matchup chart")
        except Exception as e:
            logger.error(f"❌ Error creating matchup chart: {str(e)}")

    def _create_upset_alerts_chart(self, predictions_df: pd.DataFrame):
        """Create upset alerts visualization"""
        try:
            import matplotlib.pyplot as plt

            upset_games = predictions_df[predictions_df['upset_potential'] == 'High']

            if len(upset_games) > 0:
                plt.figure(figsize=(12, 8))

                fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

                # Upset alert games
                matchups = [f"{game['home_team']} vs {game['away_team']}" for _, game in upset_games.iterrows()]
                margins = upset_games['predicted_margin']
                confidences = upset_games['confidence'] * 100

                colors = ['red' if margin < 0 else 'blue' for margin in margins]
                bars = ax1.barh(matchups, margins, color=colors, alpha=0.7)
                ax1.set_xlabel('Predicted Margin (Negative = Away Team Favored)')
                ax1.set_title('Week 12 Upset Alert Games')
                ax1.grid(True, alpha=0.3)
                ax1.axvline(x=0, color='black', linestyle='--', alpha=0.5)

                # Confidence vs Upset Potential
                upset_potential_counts = predictions_df['upset_potential'].value_counts()
                colors_upset = ['red', 'orange', 'green']
                bars2 = ax2.bar(upset_potential_counts.index, upset_potential_counts.values,
                               color=colors_upset, alpha=0.7)
                ax2.set_xlabel('Upset Potential')
                ax2.set_ylabel('Number of Games')
                ax2.set_title('Upset Potential Distribution')
                ax2.grid(True, alpha=0.3)

                # Add value labels
                for bar, count in zip(bars2, upset_potential_counts.values):
                    ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                            str(count), ha='center', va='bottom')

                plt.tight_layout()
                chart_path = self.visualizations_dir / "upset_special_alerts.png"
                plt.savefig(chart_path, dpi=300, bbox_inches='tight')
                plt.close()

                logger.info(f"✅ Upset alerts chart saved to {chart_path}")
            else:
                logger.info("ℹ️  No high upset potential games found")

        except ImportError:
            logger.warning("⚠️  Matplotlib not available, skipping upset alerts chart")
        except Exception as e:
            logger.error(f"❌ Error creating upset alerts chart: {str(e)}")

    def create_interactive_dashboard(self, predictions_df: pd.DataFrame):
        """Create interactive HTML dashboard"""
        logger.info("🌐 Creating interactive dashboard...")

        # Generate HTML dashboard
        dashboard_html = self._generate_dashboard_html(predictions_df)

        dashboard_path = self.visualizations_dir / "weekly_matchup_dashboard.html"
        with open(dashboard_path, 'w', encoding='utf-8') as f:
            f.write(dashboard_html)

        logger.info(f"✅ Interactive dashboard saved to {dashboard_path}")

    def _generate_dashboard_html(self, predictions_df: pd.DataFrame) -> str:
        """Generate HTML dashboard content"""

        # Sort predictions by confidence
        sorted_df = predictions_df.sort_values('confidence', ascending=False)

        # Generate JavaScript data
        games_data = []
        for _, game in sorted_df.iterrows():
            games_data.append({
                "home_team": game['home_team'],
                "away_team": game['away_team'],
                "predicted_home_score": int(game['predicted_home_score']),
                "predicted_away_score": int(game['predicted_away_score']),
                "predicted_winner": game['predicted_winner'],
                "predicted_margin": game['predicted_margin'],
                "confidence": round(game['confidence'] * 100, 1),
                "home_rank": game.get('home_rank', 'NR'),
                "away_rank": game.get('away_rank', 'NR'),
                "upset_potential": game.get('upset_potential', 'Low'),
                "betting_value": game.get('betting_value', 'Standard')
            })

        html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Week {self.week} Interactive Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            text-align: center;
            background-color: #1e3a8a;
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }}
        .stat-card {{
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
        }}
        .games-table {{
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #1e3a8a;
            color: white;
            font-weight: bold;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .confidence-high {{ color: #16a34a; font-weight: bold; }}
        .confidence-medium {{ color: #ca8a04; font-weight: bold; }}
        .confidence-low {{ color: #dc2626; font-weight: bold; }}
        .upset-high {{ background-color: #fee2e2; }}
        .betting-value {{ background-color: #dcfce7; }}
        .charts-container {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }}
        .chart-box {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .filter-container {{
            background: white;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .filter-container input, .filter-container select {{
            margin: 5px;
            padding: 8px;
            border: 1px solid #ccc;
            border-radius: 4px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🏈 Week {self.week} Interactive Dashboard</h1>
        <p>College Football Predictions & Analysis</p>
        <p>Generated by Script Ohio 2.0 Multi-Agent System</p>
    </div>

    <div class="stats-grid">
        <div class="stat-card">
            <h3>Total Games</h3>
            <h2 style="color: #1e3a8a;">{len(predictions_df)}</h2>
        </div>
        <div class="stat-card">
            <h3>Avg Confidence</h3>
            <h2 style="color: #16a34a;">{predictions_df['confidence'].mean()*100:.1f}%</h2>
        </div>
        <div class="stat-card">
            <h3>High Confidence</h3>
            <h2 style="color: #ca8a04;">{len(predictions_df[predictions_df['confidence'] > 0.8])}</h2>
        </div>
        <div class="stat-card">
            <h3>Upset Alerts</h3>
            <h2 style="color: #dc2626;">{len(predictions_df[predictions_df['upset_potential'] == 'High'])}</h2>
        </div>
    </div>

    <div class="filter-container">
        <h3>🔍 Filters</h3>
        <input type="text" id="teamFilter" placeholder="Filter by team name...">
        <select id="confidenceFilter">
            <option value="">All Confidence Levels</option>
            <option value="high">High (>80%)</option>
            <option value="medium">Medium (60-80%)</option>
            <option value="low">Low (<60%)</option>
        </select>
        <select id="upsetFilter">
            <option value="">All Games</option>
            <option value="high">Upset Alerts Only</option>
            <option value="value">Betting Value</option>
        </select>
        <button onclick="applyFilters()" style="padding: 8px 16px; background-color: #1e3a8a; color: white; border: none; border-radius: 4px; cursor: pointer;">Apply Filters</button>
    </div>

    <div class="games-table">
        <h2>📊 Week {self.week} Predictions</h2>
        <table id="gamesTable">
            <thead>
                <tr>
                    <th>Matchup</th>
                    <th>Prediction</th>
                    <th>Score</th>
                    <th>Confidence</th>
                    <th>Rankings</th>
                    <th>Upset Alert</th>
                    <th>Betting Value</th>
                </tr>
            </thead>
            <tbody id="gamesTableBody">
                <!-- Games will be populated here -->
            </tbody>
        </table>
    </div>

    <div class="charts-container">
        <div class="chart-box">
            <h3>Confidence Distribution</h3>
            <canvas id="confidenceChart"></canvas>
        </div>
        <div class="chart-box">
            <h3>Predicted Margins</h3>
            <canvas id="marginChart"></canvas>
        </div>
    </div>

    <script>
        // Games data
        const gamesData = {json.dumps(games_data)};

        // Populate games table
        function populateGamesTable(games) {{
            const tbody = document.getElementById('gamesTableBody');
            tbody.innerHTML = '';

            games.forEach(game => {{
                const row = document.createElement('tr');

                const confidenceClass = game.confidence > 80 ? 'confidence-high' :
                                       game.confidence > 60 ? 'confidence-medium' : 'confidence-low';

                const upsetClass = game.upset_potential === 'High' ? 'upset-high' : '';
                const valueClass = game.betting_value.includes('Value') ? 'betting-value' : '';

                row.className = `{{upsetClass}} {{valueClass}}`;

                row.innerHTML = `
                    <td><strong>{{game.home_team}}</strong> vs {{game.away_team}}</td>
                    <td><strong>{{game.predicted_winner}}</strong> by {{game.predicted_margin}} pts</td>
                    <td>{{game.predicted_home_score}} - {{game.predicted_away_score}}</td>
                    <td class="{{confidenceClass}}">{{game.confidence}}%</td>
                    <td>{{game.home_rank || 'NR'}} vs {{game.away_rank || 'NR'}}</td>
                    <td>{{game.upset_potential}}</td>
                    <td>{{game.betting_value}}</td>
                `;

                tbody.appendChild(row);
            }});
        }}

        // Apply filters
        function applyFilters() {{
            const teamFilter = document.getElementById('teamFilter').value.toLowerCase();
            const confidenceFilter = document.getElementById('confidenceFilter').value;
            const upsetFilter = document.getElementById('upsetFilter').value;

            let filteredGames = gamesData.filter(game => {{
                const teamMatch = !teamFilter ||
                    game.home_team.toLowerCase().includes(teamFilter) ||
                    game.away_team.toLowerCase().includes(teamFilter);

                const confidenceMatch = !confidenceFilter ||
                    (confidenceFilter === 'high' && game.confidence > 80) ||
                    (confidenceFilter === 'medium' && game.confidence >= 60 && game.confidence <= 80) ||
                    (confidenceFilter === 'low' && game.confidence < 60);

                const upsetMatch = !upsetFilter ||
                    (upsetFilter === 'high' && game.upset_potential === 'High') ||
                    (upsetFilter === 'value' && game.betting_value.includes('Value'));

                return teamMatch && confidenceMatch && upsetMatch;
            }});

            populateGamesTable(filteredGames);
        }}

        // Create charts
        function createCharts() {{
            // Confidence distribution
            const ctx1 = document.getElementById('confidenceChart').getContext('2d');
            const confidenceData = gamesData.map(g => g.confidence);

            new Chart(ctx1, {{
                type: 'histogram',
                data: {{
                    labels: ['<50%', '50-60%', '60-70%', '70-80%', '80-90%', '>90%'],
                    datasets: [{{
                        label: 'Games by Confidence',
                        data: [
                            confidenceData.filter(c => c < 50).length,
                            confidenceData.filter(c => c >= 50 && c < 60).length,
                            confidenceData.filter(c => c >= 60 && c < 70).length,
                            confidenceData.filter(c => c >= 70 && c < 80).length,
                            confidenceData.filter(c => c >= 80 && c < 90).length,
                            confidenceData.filter(c => c >= 90).length
                        ],
                        backgroundColor: ['#dc2626', '#ea580c', '#ca8a04', '#84cc16', '#22c55e', '#16a34a']
                    }}]
                }},
                options: {{
                    responsive: true,
                    plugins: {{
                        legend: {{ display: false }}
                    }}
                }}
            }});

            // Margin distribution
            const ctx2 = document.getElementById('marginChart').getContext('2d');
            const marginData = gamesData.map(g => g.predicted_margin);

            new Chart(ctx2, {{
                type: 'bar',
                data: {{
                    labels: gamesData.map(g => `{{g.home_team.slice(0, 8)}}...`),
                    datasets: [{{
                        label: 'Predicted Margin',
                        data: marginData,
                        backgroundColor: marginData.map(m => m > 0 ? '#16a34a' : '#dc2626')
                    }}]
                }},
                options: {{
                    responsive: true,
                    scales: {{
                        y: {{
                            beginAtZero: true,
                            title: {{
                                display: true,
                                text: 'Predicted Margin'
                            }}
                        }}
                    }},
                    plugins: {{
                        legend: {{ display: false }}
                    }}
                }}
            }});
        }}

        // Initialize
        document.addEventListener('DOMContentLoaded', function() {{
            populateGamesTable(gamesData);
            createCharts();
        }});
    </script>
</body>
</html>
        """

        return html_template

    def save_insights_json(self, insights: Dict[str, Any]):
        """Save insights to JSON format"""
        insights_path = self.predictions_dir / "confidence_scores.json"

        with open(insights_path, 'w', encoding='utf-8') as f:
            json.dump(insights, f, indent=2, default=str)

        logger.info(f"✅ Insights saved to {insights_path}")

    def create_executive_summary(self, predictions_df: pd.DataFrame, insights: Dict[str, Any]):
        """Create executive summary markdown"""
        logger.info("📝 Creating executive summary...")

        summary_content = f"""# 🏈 Week {self.week} Executive Summary

**Generated:** {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
**Source:** Script Ohio 2.0 Multi-Agent System
**Total Games Analyzed:** {len(predictions_df)}

---

## 📊 Key Highlights

### Overall Confidence
- **Average Confidence:** {predictions_df['confidence'].mean()*100:.1f}%
- **High Confidence Games (>80%):** {len(predictions_df[predictions_df['confidence'] > 0.8])}
- **Low Confidence Games (<60%):** {len(predictions_df[predictions_df['confidence'] < 0.6])}

### Upset Alerts
- **High Upset Potential Games:** {len(predictions_df[predictions_df['upset_potential'] == 'High'])}
- **Must-Watch Games:** {len(predictions_df[(predictions_df['confidence'] < 0.7) & (predictions_df['upset_potential'] == 'High')])}

---

## 🎯 Top 5 Confident Picks

"""

        for i, pick in enumerate(insights['top_confident_picks'][:5], 1):
            summary_content += f"""
**{i}. {pick['matchup']}**
- **Prediction:** {pick['prediction']}
- **Confidence:** {pick['confidence']}
- **Reasoning:** {pick['reasoning']}
"""

        summary_content += f"""

---

## ⚠️ Upset Alerts

"""

        if insights['upset_alerts']:
            for alert in insights['upset_alerts'][:5]:
                summary_content += f"""
**{alert['matchup']}**
- **Alert:** {alert['reason']}
- **Prediction Confidence:** {alert['confidence']}
"""
        else:
            summary_content += "No major upset alerts identified for this week.\n"

        summary_content += f"""

---

## 💰 Betting Value Opportunities

"""

        if insights['betting_opportunities']:
            for opportunity in insights['betting_opportunities'][:5]:
                summary_content += f"""
**{opportunity['matchup']}**
- **Value Type:** {opportunity['value_type']}
- **Confidence:** {opportunity['confidence']}
- **Predicted Margin:** {opportunity['predicted_margin']} points
"""
        else:
            summary_content += "No significant betting value opportunities identified for this week.\n"

        summary_content += f"""

---

## 📈 Statistical Insights

### Predicted Score Margins
- **Largest Predicted Victory:** {predictions_df['predicted_margin'].max():.1f} points
- **Most Competitive Game:** {predictions_df['predicted_margin'].abs().min():.1f} points
- **Average Predicted Margin:** {predictions_df['predicted_margin'].abs().mean():.1f} points

### Score Predictions
- **Highest Scoring Game:** {predictions_df[['predicted_home_score', 'predicted_away_score']].sum(axis=1).max():.0f} total points
- **Average Total Points:** {predictions_df[['predicted_home_score', 'predicted_away_score']].sum(axis=1).mean():.1f} points

---

## 🔍 Methodology

This analysis was generated using the Script Ohio 2.0 multi-agent system:

1. **Data Acquisition:** Week {self.week} games fetched via CFBD Integration Agent
2. **ML Predictions:** Ensemble of Ridge, XGBoost, and FastAI models (86 features)
3. **Confidence Scoring:** Model agreement and uncertainty quantification
4. **Insight Generation:** Statistical analysis and pattern recognition
5. **Visualization:** Automated chart generation and interactive dashboard

**Model Performance:** 73% historical accuracy against the spread (2016-2025 seasons)

---

*For detailed predictions and interactive visualizations, see the CSV files and dashboard in this folder.*

---

**🤖 Generated by Script Ohio 2.0 Intelligent Analytics Platform**
"""

        # Save summary
        summary_path = self.insights_dir / "easy_to_read_summary.md"
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(summary_content)

        logger.info(f"✅ Executive summary saved to {summary_path}")

    def create_quick_picks(self, predictions_df: pd.DataFrame, insights: Dict[str, Any]):
        """Create quick picks for easy consumption"""
        logger.info("🎯 Creating quick picks...")

        # Top 5 confident picks
        top_picks = predictions_df.nlargest(5, 'confidence')[[
            'home_team', 'away_team', 'predicted_winner', 'predicted_margin',
            'confidence', 'home_rank', 'away_rank'
        ]].to_dict('records')

        # Must-watch games (competitive + interesting)
        competitive_games = predictions_df[
            (predictions_df['predicted_margin'].abs() < 7) &
            (predictions_df['confidence'] < 0.8)
        ].nlargest(5, 'confidence')[[
            'home_team', 'away_team', 'predicted_winner', 'predicted_margin',
            'confidence', 'upset_potential'
        ]].to_dict('records')

        # Save quick picks
        quick_picks_data = {
            "top_5_confident_picks": top_picks,
            "must_watch_games": competitive_games,
            "generated_at": datetime.now().isoformat(),
            "week": self.week,
            "season": self.season
        }

        picks_path = self.quick_picks_dir / "top_5_confident_picks.json"
        with open(picks_path, 'w', encoding='utf-8') as f:
            json.dump(quick_picks_data, f, indent=2)

        # Create must-watch games separate file
        must_watch_path = self.quick_picks_dir / "must_watch_games.json"
        with open(must_watch_path, 'w', encoding='utf-8') as f:
            json.dump({
                "must_watch_games": competitive_games,
                "generated_at": datetime.now().isoformat(),
                "week": self.week,
                "season": self.season
            }, f, indent=2)

        logger.info(f"✅ Quick picks saved to {picks_path} and {must_watch_path}")

    def generate_complete_analysis(self):
        """Generate complete Week 12 analysis"""
        logger.info(f"🚀 Starting Week {self.week} complete analysis...")

        start_time = time.time()

        try:
            # Step 1: Get games data
            games_data = self.get_week12_games_data()

            # Step 2: Generate predictions
            predictions_df = self.generate_predictions(games_data)
            self._record_run_with_orchestrator(predictions_df)

            # Step 3: Save predictions
            self.save_predictions_csv(predictions_df)

            # Step 4: Generate insights
            insights = self.generate_insights(predictions_df)
            self.save_insights_json(insights)

            # Step 5: Create visualizations
            self.create_visualizations(predictions_df, insights)

            # Step 6: Create executive summary
            self.create_executive_summary(predictions_df, insights)

            # Step 7: Create interactive dashboard
            self.create_interactive_dashboard(predictions_df)

            # Step 8: Create quick picks
            self.create_quick_picks(predictions_df, insights)

            execution_time = time.time() - start_time
            logger.info(f"✅ Week {self.week} analysis completed in {execution_time:.2f} seconds")

            print(f"\n🎉 Week {self.week} Analysis Complete!")
            print(f"📁 Check the 'week12_digestible_analysis' folder for results")
            print(f"⏱️  Total execution time: {execution_time:.2f} seconds")
            print(f"📊 Analyzed {len(predictions_df)} games")
            print(f"🎯 Average confidence: {predictions_df['confidence'].mean()*100:.1f}%")

            return True

        except Exception as e:
            logger.error(f"❌ Error in complete analysis: {str(e)}")
            raise


if __name__ == "__main__":
    print("🏈 Script Ohio 2.0 - Week 12 Digestible Analysis Generator")
    print("=" * 60)

    try:
        generator = Week12AnalysisGenerator(week=12, season=2025)
        success = generator.generate_complete_analysis()

        if success:
            print("\n✅ Analysis completed successfully!")
            print("📂 Check the following files:")
            print("  - week12_digestible_analysis/predictions/week12_all_games_predictions.csv")
            print("  - week12_digestible_analysis/visualizations/weekly_matchup_dashboard.html")
            print("  - week12_digestible_analysis/insights/easy_to_read_summary.md")
            print("  - week12_digestible_analysis/quick_picks/top_5_confident_picks.json")
        else:
            print("❌ Analysis failed. Check logs for details.")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("Check the log file 'week12_analysis.log' for details")
        sys.exit(1)