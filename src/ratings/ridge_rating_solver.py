"""
Ridge regression rating solver with talent priors and sample weighting.

This module complements the Massey solver by introducing Ridge regularization,
talent-anchor priors, and time-decay weighting on historical games. The solver
produces zero-centered team ratings plus an estimated home-field advantage that
feeds downstream rating libraries and validation tooling.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from .massey_ratings import MasseyConfig, load_game_data
from .talent_prior_blender import TalentPriorConfig, compute_talent_priors

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_PATH = PROJECT_ROOT / "model_pack" / "updated_training_data.csv"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "src" / "ratings"
RIDGE_SOLVER_VERSION = "0.1.0"

RIDGE_REQUIRED_COLUMNS = {
    "season",
    "week",
    "home_team",
    "away_team",
    "home_points",
    "away_points",
    "neutral_site",
}


@dataclass
class RidgeRatingConfig:
    """Configuration for the ridge rating solver."""

    season: int = 2025
    week: Optional[int] = None
    alpha: float = 4.0
    prior_strength: float = 2.0
    recency_halflife_weeks: float = 10.0
    min_sample_weight: float = 0.25
    zero_sum_weight: float = 5.0
    home_field_prior: float = 2.2
    home_field_floor: float = 0.5
    home_field_cap: float = 6.0
    regularize_hfa: bool = False
    enforce_zero_mean: bool = True
    neutral_site_hfa: float = 0.0
    data_path: Path = DEFAULT_DATA_PATH
    cache_path: Optional[Path] = None
    sample_weight_column: Optional[str] = None
    max_games: Optional[int] = None
    prior_config: Optional[TalentPriorConfig] = field(default=None)

    def resolved_cache_path(self) -> Path:
        if self.cache_path:
            return self.cache_path
        DEFAULT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        return DEFAULT_OUTPUT_DIR / f"ridge_ratings_{self.season}.csv"


def _prepare_games_df(
    config: RidgeRatingConfig, games_df: Optional[pd.DataFrame]
) -> pd.DataFrame:
    if games_df is not None:
        df = games_df.copy()
    else:
        loader_cfg = MasseyConfig(
            season=config.season,
            week=config.week,
            data_path=config.data_path,
            max_games=config.max_games,
        )
        df = load_game_data(loader_cfg)

    missing = RIDGE_REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns for ridge solver: {sorted(missing)}")

    df["week"] = df["week"].fillna(0).astype(int)
    df = df[df["season"] <= config.season]
    if config.week is not None:
        mask = (df["season"] < config.season) | (
            (df["season"] == config.season) & (df["week"] <= config.week)
        )
        df = df[mask]

    if config.max_games:
        df = df.tail(config.max_games)

    if df.empty:
        raise ValueError("No games available for ridge solver.")
    return df.reset_index(drop=True)


def _build_team_index(df: pd.DataFrame) -> Tuple[Dict[str, int], List[str]]:
    teams = sorted(set(df["home_team"]).union(df["away_team"]))
    if not teams:
        raise ValueError("No teams detected for ridge solver.")
    index = {team: idx for idx, team in enumerate(teams)}
    return index, teams


def _compute_sample_weights(df: pd.DataFrame, config: RidgeRatingConfig) -> np.ndarray:
    if config.sample_weight_column and config.sample_weight_column in df.columns:
        weights = (
            df[config.sample_weight_column].astype(float).clip(lower=config.min_sample_weight)
        )
        return weights.to_numpy()

    if config.recency_halflife_weeks <= 0:
        return np.ones(len(df))

    week_index = df["season"].astype(int) * 32 + df["week"].astype(int)
    anchor_week = config.season * 32 + (
        config.week if config.week is not None else int(df["week"].max())
    )
    delta = (anchor_week - week_index).clip(lower=0)
    decay = np.log(2) / max(config.recency_halflife_weeks, 1e-9)
    weights = np.exp(-decay * delta)
    weights = np.clip(weights, config.min_sample_weight, 1.0)
    return weights


def _build_design_matrix(
    df: pd.DataFrame,
    team_index: Dict[str, int],
    config: RidgeRatingConfig,
) -> Tuple[np.ndarray, np.ndarray]:
    num_games = len(df)
    num_vars = len(team_index) + 1  # teams + home-field term
    design = np.zeros((num_games, num_vars))
    targets = np.zeros(num_games)

    for row_idx, game in enumerate(
        df[["home_team", "away_team", "home_points", "away_points", "neutral_site"]].itertuples(
            index=False
        )
    ):
        home_idx = team_index[game.home_team]
        away_idx = team_index[game.away_team]
        design[row_idx, home_idx] = 1.0
        design[row_idx, away_idx] = -1.0
        if not bool(game.neutral_site):
            design[row_idx, -1] = 1.0
        else:
            design[row_idx, -1] = config.neutral_site_hfa
        targets[row_idx] = float(game.home_points - game.away_points)
    return design, targets


def _append_zero_sum_constraint(
    design: np.ndarray,
    targets: np.ndarray,
    weights: np.ndarray,
    config: RidgeRatingConfig,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    extra_row = np.zeros(design.shape[1])
    extra_row[: design.shape[1] - 1] = 1.0
    design = np.vstack([design, extra_row])
    targets = np.append(targets, 0.0)
    weights = np.append(weights, max(config.zero_sum_weight, 1e-6))
    return design, targets, weights


def _append_priors(
    design: np.ndarray,
    targets: np.ndarray,
    weights: np.ndarray,
    team_index: Dict[str, int],
    priors: pd.Series,
    config: RidgeRatingConfig,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    if config.prior_strength <= 0 or priors.empty:
        return design, targets, weights

    rows = []
    priors_targets = []
    priors_weights = []
    for team, prior in priors.items():
        col_idx = team_index.get(team)
        if col_idx is None:
            continue
        row = np.zeros(design.shape[1])
        row[col_idx] = 1.0
        rows.append(row)
        priors_targets.append(prior)
        priors_weights.append(config.prior_strength)

    if not rows:
        return design, targets, weights

    design = np.vstack([design, np.vstack(rows)])
    targets = np.append(targets, np.array(priors_targets))
    weights = np.append(weights, np.array(priors_weights))
    return design, targets, weights


def _solve_weighted_ridge(
    design: np.ndarray,
    targets: np.ndarray,
    weights: np.ndarray,
    config: RidgeRatingConfig,
) -> np.ndarray:
    sqrt_w = np.sqrt(weights)[:, None]
    weighted_design = design * sqrt_w
    weighted_targets = targets * np.sqrt(weights)

    lhs = weighted_design.T @ weighted_design
    rhs = weighted_design.T @ weighted_targets

    ridge = np.eye(design.shape[1]) * config.alpha
    if not config.regularize_hfa:
        ridge[-1, -1] = min(config.alpha * 1e-3, 1e-6)
    lhs += ridge

    try:
        solution = np.linalg.solve(lhs, rhs)
    except np.linalg.LinAlgError:
        solution, *_ = np.linalg.lstsq(lhs, rhs, rcond=None)
    return solution


def compute_ridge_ratings(
    config: RidgeRatingConfig,
    games_df: Optional[pd.DataFrame] = None,
    priors_df: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """Compute ridge ratings for the configured season/week."""
    df = _prepare_games_df(config, games_df)
    team_index, ordered_teams = _build_team_index(df)
    priors_df = priors_df
    if priors_df is None:
        prior_config = config.prior_config or TalentPriorConfig(
            season=config.season,
            week=config.week,
            data_path=config.data_path,
            max_games=config.max_games,
        )
        priors_df = compute_talent_priors(prior_config, games_df=df)

    prior_series = priors_df.set_index("team")["prior_rating"]
    design, targets = _build_design_matrix(df, team_index, config)
    weights = _compute_sample_weights(df, config)
    design, targets, weights = _append_zero_sum_constraint(design, targets, weights, config)
    design, targets, weights = _append_priors(
        design, targets, weights, team_index, prior_series, config
    )

    solution = _solve_weighted_ridge(design, targets, weights, config)
    ratings = solution[:-1]
    hfa = float(solution[-1])

    if np.isnan(hfa) or hfa <= 0.0:
        hfa = max(config.home_field_prior, config.home_field_floor)
    else:
        hfa = float(np.clip(hfa, config.home_field_floor, config.home_field_cap))

    if config.enforce_zero_mean:
        ratings -= ratings.mean()

    games_played = (
        df["home_team"].value_counts()
        .add(df["away_team"].value_counts(), fill_value=0)
        .astype(int)
    )

    prior_aligned = prior_series.reindex(ordered_teams).fillna(0.0)

    ratings_df = pd.DataFrame(
        {
            "team": ordered_teams,
            "season": config.season,
            "week": config.week,
            "rating": ratings,
            "games_played": [int(games_played.get(team, 0)) for team in ordered_teams],
            "talent_prior": prior_aligned.values,
            "solver_version": RIDGE_SOLVER_VERSION,
            "hfa": hfa,
        }
    ).sort_values("rating", ascending=False)

    ratings_df["last_updated"] = dt.datetime.now(dt.timezone.utc).isoformat()
    ratings_df["ratings_sum"] = ratings_df["rating"].sum()
    return ratings_df.reset_index(drop=True)


def save_ridge_ratings(ratings_df: pd.DataFrame, path: Optional[Path] = None) -> Path:
    """Persist solver output to disk."""
    if path is None:
        season = int(ratings_df["season"].iloc[0])
        path = DEFAULT_OUTPUT_DIR / f"ridge_ratings_{season}.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    ratings_df.to_csv(path, index=False)
    return path


def generate_ridge_ratings(
    config: RidgeRatingConfig,
    persist: bool = True,
    games_df: Optional[pd.DataFrame] = None,
    priors_df: Optional[pd.DataFrame] = None,
) -> tuple[pd.DataFrame, Optional[Path]]:
    """Convenience wrapper that runs the solver and optionally caches results."""
    ratings_df = compute_ridge_ratings(
        config=config,
        games_df=games_df,
        priors_df=priors_df,
    )
    output_path = config.resolved_cache_path() if persist else None
    if persist:
        save_ridge_ratings(ratings_df, output_path)
    return ratings_df, output_path


__all__ = [
    "RidgeRatingConfig",
    "compute_ridge_ratings",
    "generate_ridge_ratings",
    "save_ridge_ratings",
]

