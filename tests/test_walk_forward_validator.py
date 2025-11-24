"""
Unit tests for walk-forward validation.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.validation.walk_forward_validator import (
    WalkForwardConfig,
    run_walk_forward_validation,
)


def _sample_games() -> pd.DataFrame:
    """Generate sample games for testing."""
    games = []
    for season in range(2020, 2024):
        for week in range(5, 11):
            games.append(
                {
                    "id": len(games) + 1,
                    "season": season,
                    "week": week,
                    "home_team": "Ohio State",
                    "away_team": "Michigan",
                    "home_points": 28 + np.random.randint(-7, 8),
                    "away_points": 21 + np.random.randint(-7, 8),
                    "spread": 7.0,
                }
            )
    return pd.DataFrame(games)


def _simple_predictor(train_df: pd.DataFrame, test_df: pd.DataFrame) -> np.ndarray:
    """Simple predictor that returns mean margin from training data."""
    mean_margin = train_df["margin"].mean() if not train_df.empty else 0.0
    return np.full(len(test_df), mean_margin)


def test_walk_forward_expanding_window():
    """Test expanding window validation strategy."""
    games = _sample_games()
    config = WalkForwardConfig(
        season_start=2020,
        season_end=2023,
        week_start=5,
        validation_strategy="expanding",
        min_train_games=5,
        min_test_games=1,
    )

    results = run_walk_forward_validation(config, _simple_predictor, games_df=games)

    assert not results.empty
    assert "mae" in results.columns
    assert "winner_accuracy" in results.columns
    assert results["test_season"].min() >= 2021


def test_walk_forward_rolling_window():
    """Test rolling window validation strategy."""
    games = _sample_games()
    config = WalkForwardConfig(
        season_start=2020,
        season_end=2023,
        week_start=5,
        validation_strategy="rolling",
        window_size_seasons=2,
        min_train_games=5,
        min_test_games=1,
    )

    results = run_walk_forward_validation(config, _simple_predictor, games_df=games)

    assert not results.empty
    assert all(results["train_season_start"] >= 2020)

