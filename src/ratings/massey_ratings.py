"""
Massey ratings solver utilities.

Implements a regularized least-squares solver that estimates team ratings and a
global home-field advantage term directly from Script Ohio 2.0 historical data.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_PATH = PROJECT_ROOT / "model_pack" / "updated_training_data.csv"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "src" / "ratings"
MASSEY_SOLVER_VERSION = "1.0.0"
REQUIRED_COLUMNS = {
    "season",
    "week",
    "home_team",
    "away_team",
    "home_points",
    "away_points",
}


@dataclass
class MasseyConfig:
    """Configuration object for Massey solver execution."""

    season: int = 2025
    week: Optional[int] = None
    regularization: float = 0.001
    home_field_prior: float = 2.3
    home_field_override: Optional[float] = None
    data_path: Path = DEFAULT_DATA_PATH
    cache_path: Optional[Path] = None
    max_games: Optional[int] = None

    def resolved_cache_path(self) -> Path:
        """Return the cache path for the computed ratings."""
        if self.cache_path:
            return self.cache_path
        DEFAULT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        return DEFAULT_OUTPUT_DIR / f"massey_ratings_{self.season}.csv"


def load_game_data(config: MasseyConfig) -> pd.DataFrame:
    """Load and filter historical games for the solver.

    Args:
        config: Solver configuration.

    Returns:
        Filtered DataFrame containing the required columns.
    """
    if not config.data_path.exists():
        raise FileNotFoundError(f"Game data not found at {config.data_path}")

    df = pd.read_csv(config.data_path)
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in data: {sorted(missing)}")

    df = df.copy()
    df = df.dropna(subset=["home_points", "away_points"])
    df["week"] = df["week"].fillna(0).astype(int)

    if "neutral_site" not in df.columns:
        df["neutral_site"] = False
    df["neutral_site"] = df["neutral_site"].fillna(False).astype(bool)

    df = df[df["season"] <= config.season]
    if config.week is not None:
        mask_current = (df["season"] == config.season) & (df["week"] <= config.week)
        mask_past = df["season"] < config.season
        df = df[mask_current | mask_past]

    df = df.sort_values(["season", "week"]).reset_index(drop=True)

    if config.max_games:
        df = df.tail(config.max_games)

    if df.empty:
        raise ValueError("Filtered game dataset is empty; check configuration.")

    df["point_diff"] = df["home_points"] - df["away_points"]
    return df


def _build_team_index(df: pd.DataFrame) -> Tuple[Dict[str, int], List[str]]:
    teams = sorted(set(df["home_team"]).union(df["away_team"]))
    if not teams:
        raise ValueError("No teams detected in dataset.")
    team_index = {team: idx for idx, team in enumerate(teams)}
    return team_index, teams


def _assemble_linear_system(
    df: pd.DataFrame,
    team_index: Dict[str, int],
) -> Tuple[np.ndarray, np.ndarray]:
    num_games = len(df)
    num_teams = len(team_index)
    design = np.zeros((num_games + 1, num_teams + 1))
    targets = np.zeros(num_games + 1)

    for row_idx, game in enumerate(
        df[["home_team", "away_team", "point_diff", "neutral_site"]].itertuples(
            index=False
        )
    ):
        home_idx = team_index[game.home_team]
        away_idx = team_index[game.away_team]
        design[row_idx, home_idx] = 1.0
        design[row_idx, away_idx] = -1.0
        if not bool(game.neutral_site):
            design[row_idx, -1] = 1.0
        targets[row_idx] = float(game.point_diff)

    # Normalization constraint to keep ratings centered on zero
    design[-1, :num_teams] = 1.0
    targets[-1] = 0.0

    return design, targets


def _solve_massey_system(
    design: np.ndarray,
    targets: np.ndarray,
    regularization: float,
) -> np.ndarray:
    num_vars = design.shape[1]
    lhs = design.T @ design
    rhs = design.T @ targets
    lhs += regularization * np.eye(num_vars)

    try:
        solution = np.linalg.solve(lhs, rhs)
    except np.linalg.LinAlgError:
        solution, *_ = np.linalg.lstsq(lhs, rhs, rcond=None)
    return solution


def compute_massey_ratings(
    config: MasseyConfig,
    games_df: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """Compute Massey ratings for the provided configuration.

    Args:
        config: Solver configuration.
        games_df: Optional pre-filtered dataframe (used for testing).

    Returns:
        DataFrame containing ratings, games played, and metadata.
    """
    df = games_df.copy() if games_df is not None else load_game_data(config)
    team_index, ordered_teams = _build_team_index(df)
    design, targets = _assemble_linear_system(df, team_index)
    solution = _solve_massey_system(design, targets, config.regularization)

    ratings = solution[:-1]
    hfa = solution[-1]

    if config.home_field_override is not None:
        hfa = config.home_field_override
    else:
        hfa = float(np.clip(hfa, 0.0, 7.0))
        if np.isclose(hfa, 0.0) and config.home_field_prior > 0:
            hfa = config.home_field_prior

    games_played = (
        df["home_team"].value_counts()
        .add(df["away_team"].value_counts(), fill_value=0)
        .astype(int)
    )

    ratings_df = pd.DataFrame(
        {
            "team": ordered_teams,
            "season": config.season,
            "week": config.week,
            "rating": ratings,
            "games_played": [int(games_played.get(team, 0)) for team in ordered_teams],
        }
    )
    ratings_df["hfa"] = hfa
    ratings_df["solver_version"] = MASSEY_SOLVER_VERSION
    ratings_df["last_updated"] = dt.datetime.now(dt.timezone.utc).isoformat()
    ratings_df["ratings_sum"] = ratings_df["rating"].sum()

    ratings_df = ratings_df.sort_values("rating", ascending=False).reset_index(
        drop=True
    )
    return ratings_df


def save_ratings(ratings_df: pd.DataFrame, path: Optional[Path] = None) -> Path:
    """Persist ratings to disk."""
    if path is None:
        season = int(ratings_df["season"].iloc[0])
        path = DEFAULT_OUTPUT_DIR / f"massey_ratings_{season}.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    ratings_df.to_csv(path, index=False)
    return path


def generate_massey_ratings(
    config: MasseyConfig,
    persist: bool = True,
    games_df: Optional[pd.DataFrame] = None,
) -> Tuple[pd.DataFrame, Optional[Path]]:
    """Execute solver and optionally persist results."""
    ratings_df = compute_massey_ratings(config=config, games_df=games_df)
    output_path = config.resolved_cache_path() if persist else None
    if persist:
        save_ratings(ratings_df, output_path)
    return ratings_df, output_path

