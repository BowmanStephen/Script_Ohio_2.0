"""
Helper utilities for building and loading the shared rating library.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

import pandas as pd

from .cfbd_ratings import load_cfbd_ratings
from .coleman_metamodel import ColemanConfig, load_coleman_ratings
from .massey_ratings import MasseyConfig, generate_massey_ratings, save_ratings

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LIBRARY_DIR = PROJECT_ROOT / "src" / "ratings"


def get_library_path(season: int) -> Path:
    """Return the canonical rating library CSV path for a season."""
    DEFAULT_LIBRARY_DIR.mkdir(parents=True, exist_ok=True)
    return DEFAULT_LIBRARY_DIR / f"rating_library_{season}.csv"


def load_massey_ratings(
    config: Optional[MasseyConfig] = None,
    refresh: bool = False,
    persist: bool = True,
) -> pd.DataFrame:
    """Load cached Massey ratings, generating them if necessary."""
    config = config or MasseyConfig()
    cache_path = config.resolved_cache_path()

    if not refresh and cache_path.exists():
        return pd.read_csv(cache_path)

    ratings_df, _ = generate_massey_ratings(config=config, persist=persist)
    if persist and not cache_path.exists():
        save_ratings(ratings_df, cache_path)
    return ratings_df


def _format_system_frame(
    df: pd.DataFrame,
    system_name: str,
    rating_column: str,
    extra_columns: Optional[List[str]] = None,
) -> pd.DataFrame:
    cols = ["team", "season", rating_column]
    if extra_columns:
        cols.extend(extra_columns)
    subset = df[cols].copy()
    subset = subset.rename(columns={rating_column: "rating"})
    subset["system"] = system_name
    ordered_cols = ["team", "season", "system", "rating"]
    if extra_columns:
        ordered_cols.extend(extra_columns)
    return subset[ordered_cols]


def build_rating_library(
    season: int,
    refresh: bool = False,
    include_systems: Optional[List[str]] = None,
    library_path: Optional[Path] = None,
    massey_config: Optional[MasseyConfig] = None,
    massey_df: Optional[pd.DataFrame] = None,
    cfbd_df: Optional[pd.DataFrame] = None,
    coleman_config: Optional[ColemanConfig] = None,
    coleman_df: Optional[pd.DataFrame] = None,
    games_df: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """
    Assemble the rating library, aggregating multiple rating systems.
    """
    include_systems = include_systems or ["massey", "sp_plus", "fpi", "elo", "srs", "coleman"]
    frames: List[pd.DataFrame] = []

    config = massey_config or MasseyConfig(season=season)
    if massey_df is None:
        massey_df = load_massey_ratings(
            config=config,
            refresh=refresh,
            persist=True,
        )

    base_massey_df = massey_df.copy()

    if "massey" in include_systems:
        frames.append(_format_system_frame(base_massey_df, "massey", "rating", ["hfa", "solver_version"]))

    cfbd_systems = {"sp_plus": "sp_rating", "fpi": "fpi_rating", "elo": "elo_rating", "srs": "srs_rating"}
    requested_cfbd = [sys for sys in cfbd_systems if sys in include_systems]
    if requested_cfbd:
        if cfbd_df is None:
            cfbd_df = load_cfbd_ratings(season=season, refresh=refresh)
        for system_name, column in cfbd_systems.items():
            if system_name not in include_systems or column not in cfbd_df.columns:
                continue
            if cfbd_df[column].notna().sum() == 0:
                continue
            frames.append(_format_system_frame(cfbd_df, system_name, column, ["source"]))

    if "coleman" in include_systems:
        coleman_config = coleman_config or ColemanConfig(season=season)
        if coleman_df is None:
            coleman_df = load_coleman_ratings(
                config=coleman_config,
                refresh=refresh,
                massey_df=base_massey_df,
                cfbd_df=cfbd_df if cfbd_df is not None else pd.DataFrame(),
                games_df=games_df,
            )
        frames.append(_format_system_frame(coleman_df, "coleman", "rating", ["model_version"]))

    if not frames:
        raise ValueError("No rating systems selected for library build.")

    library_df = pd.concat(frames, ignore_index=True)
    path = library_path or get_library_path(season)
    path.parent.mkdir(parents=True, exist_ok=True)
    library_df.to_csv(path, index=False)
    return library_df


def load_rating_library(
    season: int = 2025,
    refresh: bool = False,
    include_systems: Optional[List[str]] = None,
    library_path: Optional[Path] = None,
    massey_config: Optional[MasseyConfig] = None,
    coleman_config: Optional[ColemanConfig] = None,
) -> pd.DataFrame:
    """Load the composite rating library, building it if needed."""
    path = library_path or get_library_path(season)
    if refresh or not path.exists():
        return build_rating_library(
            season=season,
            refresh=refresh,
            include_systems=include_systems,
            library_path=path,
            massey_config=massey_config,
            coleman_config=coleman_config,
        )
    return pd.read_csv(path)

