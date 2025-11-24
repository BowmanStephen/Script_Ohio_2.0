"""
Unit tests for the talent prior blender.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.ratings.talent_prior_blender import (
    TalentPriorConfig,
    compute_talent_priors,
)


def _sample_games() -> pd.DataFrame:
    data = [
        {
            "season": 2025,
            "week": 5,
            "home_team": "Ohio State",
            "away_team": "Michigan",
            "home_points": 31,
            "away_points": 24,
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
            "home_points": 20,
            "away_points": 27,
            "home_talent": 916.0,
            "away_talent": 926.0,
            "neutral_site": False,
        },
    ]
    return pd.DataFrame(data)


def test_talent_priors_zero_centered():
    games = _sample_games()
    config = TalentPriorConfig(season=2025, week=6)
    priors = compute_talent_priors(config, games_df=games)

    assert not priors.empty
    assert np.isclose(priors["prior_rating"].mean(), 0.0, atol=1e-9)

    osu_prior = priors.loc[priors["team"] == "Ohio State", "prior_rating"].iloc[0]
    texas_prior = priors.loc[priors["team"] == "Texas", "prior_rating"].iloc[0]
    assert osu_prior > texas_prior


def test_missing_columns_raise_error():
    games = _sample_games().drop(columns=["home_talent"])
    config = TalentPriorConfig(season=2025, week=6)

    with pytest.raises(ValueError):
        compute_talent_priors(config, games_df=games)

