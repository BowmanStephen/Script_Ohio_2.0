"""
Unit tests for Massey solver and rating library integration.
"""

from pathlib import Path

import numpy as np
import pandas as pd

from src.ratings.massey_ratings import MasseyConfig, compute_massey_ratings
from src.ratings import rating_library

FIXTURE_PATH = (
    Path(__file__).parent / "fixtures" / "massey_sample_games.csv"
).resolve()


def test_compute_massey_ratings_basic():
    """Solver should produce zero-sum ratings with positive HFA."""
    config = MasseyConfig(season=2025, week=7, data_path=FIXTURE_PATH)
    ratings_df = compute_massey_ratings(config=config)

    assert not ratings_df.empty
    assert np.isclose(ratings_df["rating"].sum(), 0.0, atol=1e-6)
    assert ratings_df["hfa"].iloc[0] >= 0.5

    ohio_state = ratings_df.loc[ratings_df["team"] == "Ohio State", "rating"].iloc[0]
    texas = ratings_df.loc[ratings_df["team"] == "Texas", "rating"].iloc[0]
    assert ohio_state > texas


def test_rating_library_massey_only(tmp_path):
    """Rating library builder should persist massey cache and CSV."""
    cache_path = tmp_path / "massey_cache.csv"
    library_path = tmp_path / "rating_library.csv"
    config = MasseyConfig(
        season=2025,
        week=7,
        data_path=FIXTURE_PATH,
        cache_path=cache_path,
    )

    library_df = rating_library.build_rating_library(
        season=2025,
        refresh=True,
        library_path=library_path,
        massey_config=config,
        include_systems=["massey"],
    )

    assert not library_df.empty
    assert (library_df["system"] == "massey").all()
    assert cache_path.exists()
    assert library_path.exists()


def test_rating_library_with_multiple_systems(tmp_path):
    """Ensure rating library can merge CFBD and Coleman systems."""
    cache_path = tmp_path / "massey_cache.csv"
    library_path = tmp_path / "rating_library.csv"
    config = MasseyConfig(
        season=2025,
        week=7,
        data_path=FIXTURE_PATH,
        cache_path=cache_path,
    )
    massey_df = compute_massey_ratings(config=config)

    cfbd_df = pd.DataFrame(
        {
            "team": ["Ohio State", "Texas", "Alabama", "Michigan"],
            "season": [2025] * 4,
            "sp_rating": [25.0, 15.0, 27.0, 20.0],
            "fpi_rating": [24.0, 14.0, 26.0, 19.0],
            "elo_rating": [1750.0, 1680.0, 1785.0, 1725.0],
            "srs_rating": [23.0, 13.0, 24.0, 18.0],
            "source": ["test"] * 4,
        }
    )
    coleman_df = pd.DataFrame(
        {
            "team": ["Ohio State", "Texas", "Alabama", "Michigan"],
            "season": [2025] * 4,
            "rating": [28.0, 12.0, 30.0, 22.0],
            "model_version": ["test"] * 4,
        }
    )

    library_df = rating_library.build_rating_library(
        season=2025,
        refresh=True,
        library_path=library_path,
        massey_config=config,
        massey_df=massey_df,
        cfbd_df=cfbd_df,
        coleman_df=coleman_df,
        include_systems=["massey", "sp_plus", "fpi", "elo", "srs", "coleman"],
    )

    assert set(library_df["system"]) == {"massey", "sp_plus", "fpi", "elo", "srs", "coleman"}
    assert library_df.groupby("system")["team"].nunique().loc["coleman"] == 4
    assert library_path.exists()

