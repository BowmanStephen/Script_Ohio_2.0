"""
Unit tests for the ridge rating solver.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.ratings.ridge_rating_solver import (
    RidgeRatingConfig,
    compute_ridge_ratings,
)
from src.ratings.talent_prior_blender import (
    TalentPriorConfig,
    compute_talent_priors,
)


def _ridge_sample_games() -> pd.DataFrame:
    data = [
        {
            "season": 2025,
            "week": 5,
            "home_team": "Ohio State",
            "away_team": "Michigan",
            "home_points": 31,
            "away_points": 20,
            "home_talent": 930.0,
            "away_talent": 915.0,
            "neutral_site": False,
        },
        {
            "season": 2025,
            "week": 5,
            "home_team": "Alabama",
            "away_team": "Texas",
            "home_points": 24,
            "away_points": 21,
            "home_talent": 925.0,
            "away_talent": 905.0,
            "neutral_site": False,
        },
        {
            "season": 2025,
            "week": 6,
            "home_team": "Ohio State",
            "away_team": "Texas",
            "home_points": 28,
            "away_points": 24,
            "home_talent": 932.0,
            "away_talent": 907.0,
            "neutral_site": False,
        },
        {
            "season": 2025,
            "week": 6,
            "home_team": "Michigan",
            "away_team": "Alabama",
            "home_points": 17,
            "away_points": 27,
            "home_talent": 916.0,
            "away_talent": 926.0,
            "neutral_site": False,
        },
        {
            "season": 2025,
            "week": 7,
            "home_team": "Texas",
            "away_team": "Michigan",
            "home_points": 35,
            "away_points": 38,
            "home_talent": 908.0,
            "away_talent": 917.0,
            "neutral_site": False,
        },
        {
            "season": 2025,
            "week": 7,
            "home_team": "Alabama",
            "away_team": "Ohio State",
            "home_points": 21,
            "away_points": 30,
            "home_talent": 927.0,
            "away_talent": 933.0,
            "neutral_site": True,
        },
    ]
    return pd.DataFrame(data)


def test_ridge_solver_basic_rankings():
    games = _ridge_sample_games()
    prior_cfg = TalentPriorConfig(season=2025, week=7)
    priors = compute_talent_priors(prior_cfg, games_df=games)

    config = RidgeRatingConfig(
        season=2025,
        week=7,
        alpha=2.0,
        prior_strength=1.5,
    )

    ratings = compute_ridge_ratings(
        config=config,
        games_df=games,
        priors_df=priors,
    )

    assert not ratings.empty
    assert np.isclose(ratings["rating"].sum(), 0.0, atol=1e-6)
    assert ratings["hfa"].iloc[0] >= 0.5

    osu_rating = ratings.loc[ratings["team"] == "Ohio State", "rating"].iloc[0]
    texas_rating = ratings.loc[ratings["team"] == "Texas", "rating"].iloc[0]
    assert osu_rating > texas_rating


def test_ridge_solver_respects_priors():
    games = _ridge_sample_games()
    manual_priors = pd.DataFrame(
        {
            "team": ["Ohio State", "Texas", "Alabama", "Michigan"],
            "prior_rating": [0.0, 5.0, 0.0, -2.0],
        }
    )

    config = RidgeRatingConfig(
        season=2025,
        week=7,
        alpha=0.5,
        prior_strength=8.0,
    )

    ratings = compute_ridge_ratings(
        config=config,
        games_df=games,
        priors_df=manual_priors,
    )

    osu_rating = ratings.loc[ratings["team"] == "Ohio State", "rating"].iloc[0]
    texas_rating = ratings.loc[ratings["team"] == "Texas", "rating"].iloc[0]
    assert texas_rating > osu_rating

