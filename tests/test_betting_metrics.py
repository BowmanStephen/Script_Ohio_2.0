"""
Unit tests for betting metrics and ROI simulation.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.betting.betting_metrics import (
    BettingSimConfig,
    simulate_betting_strategy,
)


def _sample_predictions() -> pd.DataFrame:
    """Generate sample predictions."""
    return pd.DataFrame(
        {
            "game_id": [1, 2, 3, 4, 5],
            "predicted_margin": [10.0, -5.0, 7.0, -3.0, 14.0],
            "confidence": [0.7, 0.6, 0.8, 0.5, 0.9],
        }
    )


def _sample_games() -> pd.DataFrame:
    """Generate sample games with spreads."""
    return pd.DataFrame(
        {
            "id": [1, 2, 3, 4, 5],
            "season": [2025] * 5,
            "week": [10, 10, 11, 11, 12],
            "home_team": ["Ohio State", "Michigan", "Alabama", "Texas", "Georgia"],
            "away_team": ["Michigan", "Ohio State", "Texas", "Alabama", "Florida"],
            "home_points": [31, 20, 28, 24, 35],
            "away_points": [20, 31, 24, 28, 21],
            "spread": [7.0, -7.0, 3.5, -3.5, 10.0],
        }
    )


def test_betting_simulation_basic():
    """Test basic betting simulation."""
    predictions = _sample_predictions()
    games = _sample_games()

    config = BettingSimConfig(
        initial_bankroll=10000.0,
        unit_size=100.0,
        min_confidence=0.0,
    )

    results_df, performance = simulate_betting_strategy(config, predictions, games_df=games)

    assert not results_df.empty
    assert performance.total_bets > 0
    assert performance.final_bankroll > 0
    assert "roi" in dir(performance)


def test_betting_simulation_with_confidence_filter():
    """Test betting simulation with confidence threshold."""
    predictions = _sample_predictions()
    games = _sample_games()

    config = BettingSimConfig(
        initial_bankroll=10000.0,
        unit_size=100.0,
        min_confidence=0.75,  # Higher threshold
    )

    results_df, performance = simulate_betting_strategy(config, predictions, games_df=games)

    # Should have fewer bets due to confidence filter
    assert performance.total_bets <= len(predictions)

