#!/usr/bin/env python3
"""
Fallback Value Configuration for Script Ohio 2.0

Centralized management of fallback values used when real data is unavailable.
"""

import os
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class FallbackConfig:
    """Configuration for fallback values when real data is unavailable"""
    
    # Default ratings
    default_talent_rating: float = 500.0
    default_elo_rating: float = 1500.0
    default_spread: float = 0.0
    
    # Default advanced metrics (will be filled from historical data if available)
    default_epa: float = 0.0
    default_success_rate: float = 0.5
    default_explosiveness: float = 1.0
    default_havoc_rate: float = 0.0
    default_points_per_opportunity: float = 0.0
    default_avg_start_field_position: float = 70.0  # Yards from goal
    
    # Fallback strategies
    use_historical_averages: bool = True  # Use historical data averages when available
    use_team_specific_fallbacks: bool = True  # Use team-specific historical data when available
    warn_on_fallback: bool = True  # Log warnings when fallbacks are used
    
    # Historical data source
    historical_data_path: Optional[Path] = None
    
    def __post_init__(self):
        """Initialize fallback config with environment variable overrides"""
        # Allow environment variable overrides
        self.default_talent_rating = float(
            os.environ.get("FALLBACK_TALENT_RATING", self.default_talent_rating)
        )
        self.default_elo_rating = float(
            os.environ.get("FALLBACK_ELO_RATING", self.default_elo_rating)
        )
        self.default_spread = float(
            os.environ.get("FALLBACK_SPREAD", self.default_spread)
        )
        self.use_historical_averages = (
            os.environ.get("USE_HISTORICAL_FALLBACKS", "true").lower() == "true"
        )
        self.warn_on_fallback = (
            os.environ.get("WARN_ON_FALLBACK", "true").lower() == "true"
        )
    
    def get_fallback_value(self, metric_name: str, team: Optional[str] = None,
                          historical_data: Optional[Any] = None) -> float:
        """
        Get fallback value for a metric, using historical data if available.
        
        Args:
            metric_name: Name of the metric (e.g., 'talent', 'elo', 'epa')
            team: Optional team name for team-specific fallbacks
            historical_data: Optional pandas DataFrame with historical data
        
        Returns:
            Fallback value for the metric
        """
        # Try historical data first if enabled
        if self.use_historical_averages and historical_data is not None:
            try:
                # Map metric names to column names
                column_mapping = {
                    'talent': ['home_talent', 'away_talent'],
                    'elo': ['home_elo', 'away_elo'],
                    'epa': ['home_adjusted_epa', 'away_adjusted_epa'],
                    'success': ['home_adjusted_success', 'away_adjusted_success'],
                }
                
                # Try to get historical average
                if metric_name in column_mapping:
                    for col in column_mapping[metric_name]:
                        if col in historical_data.columns:
                            if team and self.use_team_specific_fallbacks:
                                # Try team-specific average
                                team_data = historical_data[
                                    (historical_data['home_team'] == team) |
                                    (historical_data['away_team'] == team)
                                ]
                                if len(team_data) > 0 and col in team_data.columns:
                                    value = float(team_data[col].mean())
                                    if self.warn_on_fallback:
                                        logger.debug(
                                            f"Using team-specific historical average for {team} {metric_name}: {value}"
                                        )
                                    return value
                            
                            # Use overall average
                            value = float(historical_data[col].mean())
                            if self.warn_on_fallback:
                                logger.debug(
                                    f"Using historical average for {metric_name}: {value}"
                                )
                            return value
            except Exception as e:
                logger.warning(f"Error getting historical fallback for {metric_name}: {e}")
        
        # Use default values
        default_values = {
            'talent': self.default_talent_rating,
            'elo': self.default_elo_rating,
            'spread': self.default_spread,
            'epa': self.default_epa,
            'success': self.default_success_rate,
            'explosiveness': self.default_explosiveness,
            'havoc': self.default_havoc_rate,
            'points_per_opportunity': self.default_points_per_opportunity,
            'avg_start': self.default_avg_start_field_position,
        }
        
        value = default_values.get(metric_name.lower(), 0.0)
        
        if self.warn_on_fallback:
            logger.warning(
                f"Using default fallback value for {metric_name}: {value} "
                f"(team: {team if team else 'N/A'})"
            )
        
        return value
    
    def log_fallback_usage(self, metric_name: str, value: float, 
                          reason: str = "Data not available"):
        """Log when a fallback value is used"""
        if self.warn_on_fallback:
            logger.warning(
                f"Fallback used for {metric_name}: {value} (reason: {reason})"
            )


# Global fallback config instance
_fallback_config: Optional[FallbackConfig] = None


def get_fallback_config() -> FallbackConfig:
    """Get the global fallback configuration instance"""
    global _fallback_config
    if _fallback_config is None:
        _fallback_config = FallbackConfig()
    return _fallback_config


def reset_fallback_config():
    """Reset the global fallback configuration (useful for testing)"""
    global _fallback_config
    _fallback_config = None

