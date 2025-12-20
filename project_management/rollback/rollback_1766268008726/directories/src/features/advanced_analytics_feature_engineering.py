"""
Advanced Analytics Feature Engineering for Script Ohio 2.0

This module extends the existing CFBD feature engineering pipeline to support
EPA/WPA and other advanced analytics features, extending the schema from 86 to
100+ features while maintaining backward compatibility.

Author: Script Ohio 2.0 Team
Created: 2025-12-18
Purpose: Feature engineering for EPA/WPA and advanced CFBD analytics
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

from ..cfbd_client.unified_client import UnifiedCFBDClient
from .cfbd_feature_engineering import CFBDFeatureEngineer, FeatureEngineeringConfig

# Import schema definitions
try:
    from data.processed.analytics.schema_definitions import (
        CACHE_TTL_MAPPING,
        AdvancedTeamMetrics,
        AnalyticsSchemaValidator,
        TeamEPASeason,
    )
except ImportError:
    # Fallback for development
    logging.warning("Analytics schema definitions not available")

logger = logging.getLogger(__name__)


@dataclass
class AdvancedAnalyticsConfig(FeatureEngineeringConfig):
    """Extended configuration for advanced analytics feature engineering"""

    include_epa_features: bool = True
    include_wpa_features: bool = True
    include_advanced_efficiency: bool = True
    include_recruiting_features: bool = True
    include_roster_features: bool = True

    # EPA/WPA specific configurations
    epa_averaging_window: int = 5  # games
    wpa_weighting_factor: float = 1.0
    explosiveness_threshold: float = 2.0  # EPA threshold for explosive plays

    # Feature engineering parameters
    normalize_epa_features: bool = True
    calculate_epa_trends: bool = True
    include_epa_differentials: bool = True


class AdvancedAnalyticsFeatureEngineer(CFBDFeatureEngineer):
    """
    Extended feature engineer that incorporates EPA/WPA and advanced analytics
    into the existing 86-feature schema, creating a comprehensive 100+ feature set.
    """

    def __init__(self, config: Optional[AdvancedAnalyticsConfig] = None):
        """Initialize advanced analytics feature engineer"""
        super().__init__(config)
        self.config = config or AdvancedAnalyticsConfig()
        self.cfbd_client = UnifiedCFBDClient()

        # Advanced feature mappings
        self.epa_feature_mapping = self._build_epa_feature_mapping()
        self.advanced_feature_mapping = self._build_advanced_feature_mapping()

        logger.info("🚀 Advanced Analytics Feature Engineer initialized")

    def _build_epa_feature_mapping(self) -> Dict[str, str]:
        """Build mapping for EPA/WPA features to new feature names"""
        return {
            "offense_epa": "offense_epa_per_game",
            "defense_epa": "defense_epa_per_game",
            "net_epa": "net_epa_per_game",
            "offense_epa_per_play": "offense_epa_per_play",
            "defense_epa_per_play": "defense_epa_per_play",
            "success_rate": "success_rate",
            "explosiveness_rate": "explosiveness_rate",
            "havoc_rate": "havoc_rate",
            "power_success_rate": "power_success",
            "stuff_rate": "stuff_rate",
            "line_yards_per_game": "line_yards",
            "second_level_yards_per_game": "second_level_yards",
            "open_field_yards_per_game": "open_field_yards",
        }

    def _build_advanced_feature_mapping(self) -> Dict[str, str]:
        """Build mapping for advanced analytics features"""
        return {
            "total_commits": "recruiting_total_commits",
            "average_rating": "recruiting_avg_rating",
            "class_ranking": "recruiting_class_rank",
            "momentum_score": "recruiting_momentum",
            "talent_correlation": "recruiting_talent_correlation",
            "total_players": "roster_total_players",
            "position_depth_score": "roster_depth_quality",
            "returning_production_pct": "roster_returning_production",
            "average_experience": "roster_avg_experience",
        }

    def enhance_feature_frame_with_epa_wpa(
        self, feature_frame: pd.DataFrame, year: int, week: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Enhance the existing feature frame with EPA/WPA analytics.

        Args:
            feature_frame: Existing feature DataFrame with 86 features
            year: Season year
            week: Week number (optional)

        Returns:
            Enhanced DataFrame with EPA/WPA features (100+ total features)
        """
        logger.info(
            f"Enhancing feature frame with EPA/WPA analytics for {year}, week {week}"
        )

        enhanced_frame = feature_frame.copy()

        try:
            # Get EPA/WPA data for all teams in the feature frame
            teams = self._extract_unique_teams(enhanced_frame)

            for team in teams:
                epa_features = self._extract_team_epa_features(team, year, week)

                if epa_features:
                    # Add EPA/WPA features to the team's row(s)
                    team_mask = (enhanced_frame["home_team"] == team) | (
                        enhanced_frame["away_team"] == team
                    )

                    for feature_name, feature_value in epa_features.items():
                        if feature_name in self.epa_feature_mapping:
                            mapped_name = self.epa_feature_mapping[feature_name]
                            enhanced_frame.loc[team_mask, mapped_name] = feature_value

            logger.info(
                f"✅ Enhanced feature frame with {len(self.epa_feature_mapping)} EPA/WPA features"
            )

        except Exception as e:
            logger.error(f"❌ Error enhancing with EPA/WPA features: {e}")
            # Return original frame if enhancement fails
            return feature_frame

        return enhanced_frame

    def enhance_frame_with_advanced_analytics(
        self, feature_frame: pd.DataFrame, year: int, week: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Enhance feature frame with advanced analytics (recruiting, roster, etc.).

        Args:
            feature_frame: Existing feature DataFrame
            year: Season year
            week: Week number (optional)

        Returns:
            Enhanced DataFrame with advanced analytics features
        """
        logger.info(f"Adding advanced analytics features for {year}, week {week}")

        enhanced_frame = feature_frame.copy()

        try:
            teams = self._extract_unique_teams(enhanced_frame)

            for team in teams:
                # Add recruiting analytics
                if self.config.include_recruiting_features:
                    recruiting_features = self._extract_recruiting_features(team, year)
                    self._add_features_to_frame(
                        enhanced_frame, team, recruiting_features, "recruiting_"
                    )

                # Add roster analytics
                if self.config.include_roster_features:
                    roster_features = self._extract_roster_features(team, year)
                    self._add_features_to_frame(
                        enhanced_frame, team, roster_features, "roster_"
                    )

            logger.info("✅ Enhanced feature frame with advanced analytics")

        except Exception as e:
            logger.error(f"❌ Error enhancing with advanced analytics: {e}")
            return feature_frame

        return enhanced_frame

    def build_comprehensive_feature_frame(
        self, games_data: List[Dict[str, Any]], year: int, week: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Build comprehensive feature frame with all advanced analytics.

        This method extends the base build_feature_frame method with EPA/WPA
        and other advanced features, creating a 100+ feature dataset.

        Args:
            games_data: Raw games data from CFBD API
            year: Season year
            week: Week number (optional)

        Returns:
            Comprehensive feature DataFrame with 100+ features
        """
        logger.info(f"Building comprehensive feature frame with advanced analytics")

        # Build base feature frame using existing pipeline
        base_frame = super().build_feature_frame(games_data, year, week)

        # Enhance with EPA/WPA features
        if self.config.include_epa_features or self.config.include_wpa_features:
            enhanced_frame = self.enhance_feature_frame_with_epa_wpa(
                base_frame, year, week
            )
        else:
            enhanced_frame = base_frame

        # Enhance with other advanced analytics
        if (
            self.config.include_recruiting_features
            or self.config.include_roster_features
            or self.config.include_advanced_efficiency
        ):
            comprehensive_frame = self.enhance_frame_with_advanced_analytics(
                enhanced_frame, year, week
            )
        else:
            comprehensive_frame = enhanced_frame

        # Final validation and feature count report
        feature_count = len(comprehensive_frame.columns)
        logger.info(
            f"✅ Built comprehensive feature frame with {feature_count} features"
        )

        # Log new features added
        base_features = set(base_frame.columns)
        comprehensive_features = set(comprehensive_frame.columns)
        new_features = comprehensive_features - base_features

        if new_features:
            logger.info(
                f"🆕 Added {len(new_features)} new features: {sorted(list(new_features))}"
            )

        return comprehensive_frame

    def _extract_team_epa_features(
        self, team: str, year: int, week: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """Extract EPA/WPA features for a specific team"""
        try:
            # Get advanced team metrics from enhanced CFBD client
            metrics_data = self.cfbd_client.get_advanced_team_metrics(year, week, team)

            if metrics_data and "advanced_metrics" in metrics_data:
                return metrics_data["advanced_metrics"]

            return None

        except Exception as e:
            logger.warning(f"Failed to extract EPA features for {team}: {e}")
            return None

    def _extract_recruiting_features(
        self, team: str, year: int
    ) -> Optional[Dict[str, Any]]:
        """Extract recruiting analytics features for a team"""
        try:
            recruiting_data = self.cfbd_client.get_advanced_recruiting_analytics(
                year, team
            )

            if recruiting_data and "advanced_analytics" in recruiting_data:
                return recruiting_data["advanced_analytics"]

            return None

        except Exception as e:
            logger.warning(f"Failed to extract recruiting features for {team}: {e}")
            return None

    def _extract_roster_features(
        self, team: str, year: int
    ) -> Optional[Dict[str, Any]]:
        """Extract roster analytics features for a team"""
        try:
            roster_data = self.cfbd_client.get_advanced_roster_analytics(year, team)

            if roster_data and "advanced_analytics" in roster_data:
                return roster_data["advanced_analytics"]

            return None

        except Exception as e:
            logger.warning(f"Failed to extract roster features for {team}: {e}")
            return None

    def _extract_unique_teams(self, feature_frame: pd.DataFrame) -> List[str]:
        """Extract unique team names from feature frame"""
        if (
            "home_team" in feature_frame.columns
            and "away_team" in feature_frame.columns
        ):
            home_teams = feature_frame["home_team"].unique()
            away_teams = feature_frame["away_team"].unique()
            return list(set(list(home_teams) + list(away_teams)))
        elif "team" in feature_frame.columns:
            return feature_frame["team"].unique().tolist()
        else:
            logger.warning("Could not find team columns in feature frame")
            return []

    def _add_features_to_frame(
        self,
        feature_frame: pd.DataFrame,
        team: str,
        features: Dict[str, Any],
        prefix: str = "",
    ) -> None:
        """Add features to the appropriate team rows in the feature frame"""
        if not features:
            return

        # Find rows for this team (either home or away)
        team_mask = (feature_frame.get("home_team") == team) | (
            feature_frame.get("away_team") == team
        )

        if not team_mask.any():
            return

        # Add each feature to the team's rows
        for feature_name, feature_value in features.items():
            column_name = f"{prefix}{feature_name}"

            # Create column if it doesn't exist
            if column_name not in feature_frame.columns:
                feature_frame[column_name] = np.nan

            # Set value for team rows
            feature_frame.loc[team_mask, column_name] = feature_value

    def calculate_epa_differentials(self, feature_frame: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate EPA differentials between home and away teams.

        Args:
            feature_frame: Feature frame with EPA data

        Returns:
            Enhanced frame with EPA differential features
        """
        epa_columns = [
            "offense_epa_per_game",
            "defense_epa_per_game",
            "net_epa_per_game",
            "offense_epa_per_play",
            "defense_epa_per_play",
            "success_rate",
            "explosiveness_rate",
            "havoc_rate",
        ]

        enhanced_frame = feature_frame.copy()

        for col in epa_columns:
            if col in enhanced_frame.columns:
                # Create differential columns (home - away)
                home_col = f"{col}_home"
                away_col = f"{col}_away"
                diff_col = f"{col}_differential"

                enhanced_frame[home_col] = enhanced_frame.apply(
                    lambda row: (
                        row[col]
                        if row["home_team"] == row.get("team_focus")
                        else np.nan
                    ),
                    axis=1,
                )

                enhanced_frame[away_col] = enhanced_frame.apply(
                    lambda row: (
                        row[col]
                        if row["away_team"] == row.get("team_focus")
                        else np.nan
                    ),
                    axis=1,
                )

                enhanced_frame[diff_col] = (
                    enhanced_frame[home_col] - enhanced_frame[away_col]
                )

        return enhanced_frame

    def get_feature_importance_analysis(
        self, feature_frame: pd.DataFrame, target_column: str = "home_team_win"
    ) -> Dict[str, Any]:
        """
        Analyze feature importance for the enhanced feature set.

        Args:
            feature_frame: Enhanced feature frame
            target_column: Target variable for importance analysis

        Returns:
            Dictionary containing feature importance analysis
        """
        try:
            from sklearn.ensemble import RandomForestClassifier
            from sklearn.preprocessing import StandardScaler

            # Separate features from target
            feature_cols = [
                col
                for col in feature_frame.columns
                if col not in [target_column, "home_team", "away_team", "game_id"]
            ]

            X = feature_frame[feature_cols].fillna(0)
            y = feature_frame[target_column].fillna(0)

            # Scale features
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)

            # Train Random Forest for importance
            rf = RandomForestClassifier(n_estimators=100, random_state=42)
            rf.fit(X_scaled, y)

            # Get feature importance
            importance_scores = rf.feature_importances_
            feature_importance = dict(zip(feature_cols, importance_scores))

            # Sort by importance
            sorted_features = sorted(
                feature_importance.items(), key=lambda x: x[1], reverse=True
            )

            return {
                "feature_importance": dict(sorted_features),
                "top_features": sorted_features[:10],
                "total_features": len(feature_cols),
                "model_score": rf.score(X_scaled, y),
            }

        except Exception as e:
            logger.error(f"Error in feature importance analysis: {e}")
            return {"error": str(e)}

    def save_enhanced_feature_schema(
        self, feature_frame: pd.DataFrame, output_path: Path
    ) -> None:
        """
        Save the enhanced feature schema documentation.

        Args:
            feature_frame: Enhanced feature frame
            output_path: Path to save schema documentation
        """
        schema_info = {
            "total_features": len(feature_frame.columns),
            "feature_categories": {
                "base_features": 86,
                "epa_wpa_features": len(
                    [
                        col
                        for col in feature_frame.columns
                        if any(epa in col.lower() for epa in ["epa", "wpa"])
                    ]
                ),
                "recruiting_features": len(
                    [
                        col
                        for col in feature_frame.columns
                        if "recruiting" in col.lower()
                    ]
                ),
                "roster_features": len(
                    [col for col in feature_frame.columns if "roster" in col.lower()]
                ),
                "differential_features": len(
                    [
                        col
                        for col in feature_frame.columns
                        if "differential" in col.lower()
                    ]
                ),
            },
            "feature_list": list(feature_frame.columns),
            "created_at": datetime.utcnow().isoformat(),
            "config_used": {
                "include_epa_features": self.config.include_epa_features,
                "include_wpa_features": self.config.include_wpa_features,
                "include_recruiting_features": self.config.include_recruiting_features,
                "include_roster_features": self.config.include_roster_features,
            },
        }

        # Save schema information
        import json

        with open(output_path, "w") as f:
            json.dump(schema_info, f, indent=2)

        logger.info(f"✅ Enhanced feature schema saved to {output_path}")


if __name__ == "__main__":
    # Example usage
    config = AdvancedAnalyticsConfig(
        include_epa_features=True,
        include_wpa_features=True,
        include_recruiting_features=True,
        include_roster_features=True,
    )

    engineer = AdvancedAnalyticsFeatureEngineer(config)

    print("✅ Advanced Analytics Feature Engineer initialized")
    print(f"EPA/WPA features: {len(engineer.epa_feature_mapping)}")
    print(f"Advanced features: {len(engineer.advanced_feature_mapping)}")
