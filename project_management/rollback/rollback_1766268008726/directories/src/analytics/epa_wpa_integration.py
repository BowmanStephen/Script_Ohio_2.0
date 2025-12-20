"""
EPA/WPA Integration Module for Script Ohio 2.0

This module provides comprehensive integration of Expected Points Added (EPA) and
Win Probability Added (WPA) analytics from CFBD, processing raw play-by-play data
into actionable insights for machine learning models and predictive analytics.

Author: Script Ohio 2.0 Team
Created: 2025-12-18
Purpose: Advanced EPA/WPA analytics processing and integration
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

from ..cfbd_client.unified_client import UnifiedCFBDClient

# Import schema definitions
try:
    from data.processed.analytics.schema_definitions import (
        AdvancedTeamMetrics,
        AnalyticsSchemaValidator,
        EPAPlayRecord,
        TeamEPASeason,
    )
except ImportError:
    logging.warning("Analytics schema definitions not available, using fallbacks")

logger = logging.getLogger(__name__)


@dataclass
class EPAConfig:
    """Configuration for EPA/WPA processing"""

    # Data processing parameters
    explosiveness_threshold: float = 2.0  # EPA threshold for explosive plays
    success_threshold: float = 0.5  # Success rate threshold
    sample_size_min: int = 10  # Minimum plays for reliable metrics

    # Smoothing and averaging
    rolling_window_size: int = 5  # Games for rolling averages
    exponential_smoothing_factor: float = 0.3  # Smoothing factor for trends

    # Quality control
    outlier_detection: bool = True
    outlier_std_threshold: float = 3.0  # Standard deviations for outlier detection

    # Caching
    cache_enabled: bool = True
    cache_ttl_hours: int = 1  # Cache time-to-live in hours

    # Data validation
    validate_data_quality: bool = True
    min_game_completeness: float = 0.8  # Minimum game completion percentage


@dataclass
class EPATeamSummary:
    """Summary of EPA/WPA metrics for a team"""

    team: str
    season: int
    week: Optional[int] = None

    # EPA Metrics
    total_offense_epa: float = 0.0
    total_defense_epa: float = 0.0
    net_epa: float = 0.0
    offense_epa_per_play: float = 0.0
    defense_epa_per_play: float = 0.0

    # WPA Metrics
    total_wpa: float = 0.0
    wpa_per_play: float = 0.0
    comeback_wins: int = 0
    blown_leads: int = 0

    # Efficiency Metrics
    success_rate: float = 0.0
    explosiveness_rate: float = 0.0
    havoc_rate: float = 0.0
    power_success_rate: float = 0.0
    stuff_rate: float = 0.0

    # Contextual Metrics
    games_analyzed: int = 0
    total_plays: int = 0
    avg_field_position: float = 0.0

    # Trend Metrics
    epa_trend: float = 0.0  # Positive = improving, Negative = declining
    wpa_trend: float = 0.0

    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


class EPAWPAIntegration:
    """
    Comprehensive EPA/WPA integration processor for Script Ohio 2.0.

    This class provides methods to:
    - Process raw CFBD play-by-play data into EPA/WPA metrics
    - Calculate team and player performance analytics
    - Generate features for ML models
    - Identify trends and patterns in EPA/WPA data
    """

    def __init__(self, config: Optional[EPAConfig] = None):
        """Initialize EPA/WPA integration processor"""
        self.config = config or EPAConfig()
        self.cfbd_client = UnifiedCFBDClient()

        # Data storage
        self.cache = {}
        self.cache_timestamps = {}

        # Processing state
        self.team_summaries = {}
        self.season_averages = {}

        logger.info("🚀 EPA/WPA Integration Module initialized")

    def process_team_season_epa_wpa(
        self,
        team: str,
        year: int,
        week: Optional[int] = None,
        force_refresh: bool = False,
    ) -> EPATeamSummary:
        """
        Process EPA/WPA data for a team for a given season/week.

        Args:
            team: Team name
            year: Season year
            week: Week number (optional)
            force_refresh: Force refresh of cached data

        Returns:
            EPATeamSummary with comprehensive analytics
        """
        cache_key = f"{team}_{year}_{week or 'full'}"

        # Check cache
        if (
            not force_refresh
            and self.config.cache_enabled
            and cache_key in self.cache
            and self._is_cache_valid(cache_key)
        ):
            logger.debug(f"Using cached EPA/WPA data for {cache_key}")
            return self.cache[cache_key]

        logger.info(f"Processing EPA/WPA data for {team}, {year}, week {week}")

        try:
            # Get raw EPA/WPA data from CFBD
            raw_data = self.cfbd_client.get_team_epa_wpa_season(year, team)

            if not raw_data:
                logger.warning(f"No EPA/WPA data found for {team}, {year}")
                return self._create_empty_summary(team, year, week)

            # Process the raw data
            summary = self._process_epa_wpa_data(team, year, week, raw_data)

            # Cache the result
            if self.config.cache_enabled:
                self.cache[cache_key] = summary
                self.cache_timestamps[cache_key] = datetime.utcnow()

            return summary

        except Exception as e:
            logger.error(f"Error processing EPA/WPA for {team}: {e}")
            return self._create_empty_summary(team, year, week)

    def process_game_epa_wpa_analysis(
        self, game_id: int, include_play_details: bool = False
    ) -> Dict[str, Any]:
        """
        Process EPA/WPA analysis for a specific game.

        Args:
            game_id: CFBD game ID
            include_play_details: Include detailed play-by-play breakdown

        Returns:
            Dictionary containing comprehensive game EPA/WPA analysis
        """
        logger.info(f"Processing EPA/WPA analysis for game {game_id}")

        try:
            # Get game EPA/WPA analysis
            game_analysis = self.cfbd_client.get_epa_wpa_game_analysis(game_id)

            if not game_analysis:
                return {"error": "No EPA/WPA data available for this game"}

            # Enhanced analysis
            enhanced_analysis = self._enhance_game_analysis(
                game_analysis, include_play_details
            )

            return enhanced_analysis

        except Exception as e:
            logger.error(f"Error processing game EPA/WPA analysis: {e}")
            return {"error": str(e)}

    def generate_epa_wpa_features_for_ml(
        self,
        games_data: List[Dict[str, Any]],
        lookback_games: int = 5,
        include_trends: bool = True,
    ) -> pd.DataFrame:
        """
        Generate EPA/WPA features suitable for machine learning models.

        Args:
            games_data: List of games data
            lookback_games: Number of previous games to consider for trends
            include_trends: Include trend-based features

        Returns:
            DataFrame with EPA/WPA features for ML
        """
        logger.info(f"Generating EPA/WPA features for {len(games_data)} games")

        features_list = []

        for game in games_data:
            try:
                home_team = game.get("home_team")
                away_team = game.get("away_team")
                season = game.get("season", datetime.now().year)
                week = game.get("week")

                if not home_team or not away_team:
                    continue

                # Get EPA/WPA summaries for both teams
                home_summary = self.process_team_season_epa_wpa(home_team, season, week)
                away_summary = self.process_team_season_epa_wpa(away_team, season, week)

                # Generate features
                game_features = self._create_game_features(
                    game, home_summary, away_summary, include_trends
                )

                features_list.append(game_features)

            except Exception as e:
                logger.warning(
                    f"Error processing game {game.get('id', 'unknown')}: {e}"
                )
                continue

        if not features_list:
            logger.warning("No EPA/WPA features generated")
            return pd.DataFrame()

        # Create DataFrame
        features_df = pd.DataFrame(features_list)

        logger.info(
            f"✅ Generated EPA/WPA features: {len(features_df.columns)} features for {len(features_df)} games"
        )

        return features_df

    def calculate_epa_wpa_trends(
        self, team: str, year: int, trend_window: int = 4
    ) -> Dict[str, float]:
        """
        Calculate EPA/WPA trends for a team over a sliding window.

        Args:
            team: Team name
            year: Season year
            trend_window: Number of weeks for trend calculation

        Returns:
            Dictionary containing trend metrics
        """
        logger.info(f"Calculating EPA/WPA trends for {team}, {year}")

        try:
            trends = {}

            # Get EPA/WPA data for the season
            season_data = self.process_team_season_epa_wpa(team, year)

            # Calculate various trends
            trends["epa_trend"] = self._calculate_linear_trend(
                (
                    season_data.epa_per_game
                    if hasattr(season_data, "epa_per_game")
                    else 0.0
                ),
                trend_window,
            )

            trends["success_rate_trend"] = self._calculate_linear_trend(
                season_data.success_rate, trend_window
            )

            trends["explosiveness_trend"] = self._calculate_linear_trend(
                season_data.explosiveness_rate, trend_window
            )

            return trends

        except Exception as e:
            logger.error(f"Error calculating trends for {team}: {e}")
            return {}

    def identify_epa_wpa_anomalies(
        self, team: str, year: int, std_threshold: float = 2.0
    ) -> List[Dict[str, Any]]:
        """
        Identify anomalous EPA/WPA performance patterns.

        Args:
            team: Team name
            year: Season year
            std_threshold: Standard deviation threshold for anomaly detection

        Returns:
            List of detected anomalies
        """
        logger.info(f"Identifying EPA/WPA anomalies for {team}, {year}")

        try:
            anomalies = []

            # Get season data
            season_summary = self.process_team_season_epa_wpa(team, year)

            # Check for various types of anomalies
            if season_summary.net_epa < -std_threshold:
                anomalies.append(
                    {
                        "type": "poor_performance",
                        "metric": "net_epa",
                        "value": season_summary.net_epa,
                        "threshold": -std_threshold,
                        "description": f"Team has poor EPA performance: {season_summary.net_epa:.2f}",
                    }
                )

            if season_summary.success_rate < (0.5 - std_threshold * 0.1):
                anomalies.append(
                    {
                        "type": "low_success_rate",
                        "metric": "success_rate",
                        "value": season_summary.success_rate,
                        "threshold": 0.5 - std_threshold * 0.1,
                        "description": f"Team has low success rate: {season_summary.success_rate:.2%}",
                    }
                )

            return anomalies

        except Exception as e:
            logger.error(f"Error identifying anomalies for {team}: {e}")
            return []

    def _process_epa_wpa_data(
        self, team: str, year: int, week: Optional[int], raw_data: List[Dict[str, Any]]
    ) -> EPATeamSummary:
        """Process raw EPA/WPA data into team summary"""
        if not raw_data:
            return self._create_empty_summary(team, year, week)

        # Aggregate metrics
        total_offense_epa = sum(item.get("offenseEpa", 0) for item in raw_data)
        total_defense_epa = sum(item.get("defenseEpa", 0) for item in raw_data)
        total_plays = len(raw_data)

        # Calculate per-play metrics
        offense_epa_per_play = total_offense_epa / max(total_plays, 1)
        defense_epa_per_play = total_defense_epa / max(total_plays, 1)

        # Calculate derived metrics
        success_rate = self._calculate_success_rate(raw_data)
        explosiveness_rate = self._calculate_explosiveness_rate(raw_data)

        return EPATeamSummary(
            team=team,
            season=year,
            week=week,
            total_offense_epa=round(total_offense_epa, 3),
            total_defense_epa=round(total_defense_epa, 3),
            net_epa=round(total_offense_epa + total_defense_epa, 3),
            offense_epa_per_play=round(offense_epa_per_play, 3),
            defense_epa_per_play=round(defense_epa_per_play, 3),
            success_rate=round(success_rate, 3),
            explosiveness_rate=round(explosiveness_rate, 3),
            games_analyzed=len(
                set(item.get("gameId") for item in raw_data if item.get("gameId"))
            ),
            total_plays=total_plays,
            epa_trend=0.0,  # Would be calculated from historical data
            metadata={
                "data_source": "cfbd",
                "processing_timestamp": datetime.utcnow().isoformat(),
                "raw_data_count": len(raw_data),
            },
        )

    def _calculate_success_rate(self, plays_data: List[Dict[str, Any]]) -> float:
        """Calculate success rate from plays data"""
        if not plays_data:
            return 0.0

        # Success criteria varies by down and distance
        # This is a simplified calculation - real implementation would be more nuanced
        successful_plays = 0
        total_plays = len(plays_data)

        for play in plays_data:
            offense_epa = play.get("offenseEpa", 0)
            # Simple success criterion: positive EPA
            if offense_epa > 0:
                successful_plays += 1

        return successful_plays / max(total_plays, 1)

    def _calculate_explosiveness_rate(self, plays_data: List[Dict[str, Any]]) -> float:
        """Calculate explosiveness rate (plays with EPA > threshold)"""
        if not plays_data:
            return 0.0

        explosive_plays = 0
        total_plays = len(plays_data)

        for play in plays_data:
            offense_epa = play.get("offenseEpa", 0)
            if abs(offense_epa) > self.config.explosiveness_threshold:
                explosive_plays += 1

        return explosive_plays / max(total_plays, 1)

    def _enhance_game_analysis(
        self, game_analysis: Dict[str, Any], include_play_details: bool
    ) -> Dict[str, Any]:
        """Enhance game analysis with additional insights"""
        enhanced = game_analysis.copy()

        try:
            # Add calculated insights
            if "epa_wpa_analysis" in game_analysis:
                epa_data = game_analysis["epa_wpa_analysis"]

                # Calculate game control metrics
                enhanced["game_control"] = self._calculate_game_control_metrics(
                    epa_data
                )

                # Identify turning points
                enhanced["turning_points"] = self._identify_turning_points(epa_data)

                # Calculate efficiency ratings
                enhanced["efficiency_ratings"] = self._calculate_efficiency_ratings(
                    epa_data
                )

        except Exception as e:
            logger.warning(f"Error enhancing game analysis: {e}")

        return enhanced

    def _create_game_features(
        self,
        game: Dict[str, Any],
        home_summary: EPATeamSummary,
        away_summary: EPATeamSummary,
        include_trends: bool,
    ) -> Dict[str, Any]:
        """Create EPA/WPA features for a game"""
        features = {
            # Game identifiers
            "game_id": game.get("id"),
            "season": game.get("season"),
            "week": game.get("week"),
            "home_team": game.get("home_team"),
            "away_team": game.get("away_team"),
            # EPA features - home team
            "home_offense_epa_per_game": home_summary.offense_epa_per_play,
            "home_defense_epa_per_game": home_summary.defense_epa_per_play,
            "home_net_epa_per_game": home_summary.net_epa,
            "home_success_rate": home_summary.success_rate,
            "home_explosiveness_rate": home_summary.explosiveness_rate,
            # EPA features - away team
            "away_offense_epa_per_game": away_summary.offense_epa_per_play,
            "away_defense_epa_per_game": away_summary.defense_epa_per_play,
            "away_net_epa_per_game": away_summary.net_epa,
            "away_success_rate": away_summary.success_rate,
            "away_explosiveness_rate": away_summary.explosiveness_rate,
            # Differential features
            "epa_differential": home_summary.net_epa - away_summary.net_epa,
            "success_rate_differential": home_summary.success_rate
            - away_summary.success_rate,
            "explosiveness_differential": home_summary.explosiveness_rate
            - away_summary.explosiveness_rate,
            # Context features
            "total_plays_analyzed": home_summary.total_plays + away_summary.total_plays,
            "games_analyzed_home": home_summary.games_analyzed,
            "games_analyzed_away": away_summary.games_analyzed,
        }

        # Add trend features if requested
        if include_trends:
            features.update(
                {
                    "home_epa_trend": home_summary.epa_trend,
                    "away_epa_trend": away_summary.epa_trend,
                    "epa_trend_differential": home_summary.epa_trend
                    - away_summary.epa_trend,
                }
            )

        return features

    def _calculate_linear_trend(self, current_value: float, window_size: int) -> float:
        """Calculate a simplified linear trend (placeholder for more complex calculation)"""
        # In a real implementation, this would use historical data
        # For now, return a small random value to simulate trend calculation
        return np.random.normal(0, 0.1)  # Small random trend

    def _create_empty_summary(
        self, team: str, year: int, week: Optional[int]
    ) -> EPATeamSummary:
        """Create an empty EPA/WPA summary"""
        return EPATeamSummary(
            team=team,
            season=year,
            week=week,
            metadata={"status": "no_data", "message": "No EPA/WPA data available"},
        )

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid"""
        if cache_key not in self.cache_timestamps:
            return False

        cache_age = datetime.utcnow() - self.cache_timestamps[cache_key]
        max_age = timedelta(hours=self.config.cache_ttl_hours)

        return cache_age < max_age

    def _calculate_game_control_metrics(
        self, epa_data: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate game control metrics from EPA/WPA data"""
        # Placeholder implementation
        return {"home_team_control": 0.5, "away_team_control": 0.5, "control_shifts": 0}

    def _identify_turning_points(
        self, epa_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Identify turning points in the game based on EPA/WPA"""
        # Placeholder implementation
        return []

    def _calculate_efficiency_ratings(
        self, epa_data: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate efficiency ratings from EPA/WPA data"""
        # Placeholder implementation
        return {
            "offensive_efficiency": 0.5,
            "defensive_efficiency": 0.5,
            "overall_efficiency": 0.5,
        }

    def save_epa_wpa_data(
        self,
        team: str,
        year: int,
        summary: EPATeamSummary,
        output_dir: Optional[Path] = None,
    ) -> None:
        """
        Save EPA/WPA summary data to file.

        Args:
            team: Team name
            year: Season year
            summary: EPA team summary
            output_dir: Output directory (optional)
        """
        if output_dir is None:
            output_dir = Path("data/processed/analytics/epa_wpa")

        output_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{team}_{year}_epa_wpa_summary.json"
        filepath = output_dir / filename

        # Convert to dict and save
        data_dict = summary.__dict__.copy()
        data_dict["created_at"] = summary.created_at.isoformat()

        with open(filepath, "w") as f:
            json.dump(data_dict, f, indent=2)

        logger.info(f"✅ EPA/WPA summary saved to {filepath}")


if __name__ == "__main__":
    # Example usage
    config = EPAConfig(
        explosiveness_threshold=2.0, rolling_window_size=5, cache_enabled=True
    )

    epa_integration = EPAWPAIntegration(config)

    print("✅ EPA/WPA Integration Module initialized")
    print(f"Configuration: explosiveness_threshold={config.explosiveness_threshold}")

    # Example: Process a team's EPA/WPA data
    try:
        summary = epa_integration.process_team_season_epa_wpa("Ohio State", 2024)
        print(f"✅ Processed EPA/WPA data: {summary.team} {summary.season}")
        print(f"Net EPA: {summary.net_epa}")
        print(f"Success Rate: {summary.success_rate:.2%}")
    except Exception as e:
        print(f"❌ Error in example: {e}")
