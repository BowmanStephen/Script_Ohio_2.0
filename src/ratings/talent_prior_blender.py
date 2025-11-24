"""
Talent prior blender utilities for the ridge rating solver.

This module aggregates Script Ohio 2.0 historical data into team-level priors
that anchor the ridge rating solver with talent information and light margin
context. The generated priors are centered on zero to avoid shifting the solver
baseline and can be cached for reuse.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pandas as pd

from .massey_ratings import MasseyConfig, load_game_data

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_PATH = PROJECT_ROOT / "model_pack" / "updated_training_data.csv"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "src" / "ratings"
TALENT_PRIOR_VERSION = "0.1.0"

PRIOR_REQUIRED_COLUMNS = {
    "season",
    "week",
    "home_team",
    "away_team",
    "home_points",
    "away_points",
    "home_talent",
    "away_talent",
}


@dataclass
class TalentPriorConfig:
    """Configuration for building ridge solver talent priors."""

    season: int = 2025
    week: Optional[int] = None
    data_path: Path = DEFAULT_DATA_PATH
    min_games: int = 2
    talent_weight: float = 1.0
    margin_weight: float = 0.2
    talent_scale: float = 25.0
    shrinkage_floor: float = 0.3
    enforce_zero_mean: bool = True
    cache_path: Optional[Path] = None
    max_games: Optional[int] = None

    def resolved_cache_path(self) -> Path:
        if self.cache_path:
            return self.cache_path
        DEFAULT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        return DEFAULT_OUTPUT_DIR / f"talent_priors_{self.season}.csv"


def _prepare_games_df(
    config: TalentPriorConfig, games_df: Optional[pd.DataFrame]
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

    missing = PRIOR_REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns for talent priors: {sorted(missing)}")

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
        raise ValueError("No games available for talent prior computation.")
    return df.reset_index(drop=True)


def _expand_team_games(df: pd.DataFrame) -> pd.DataFrame:
    records = []
    for row in df.itertuples(index=False):
        margin = float(row.home_points - row.away_points)
        records.append(
            {
                "team": row.home_team,
                "talent": float(row.home_talent),
                "margin": margin,
                "season": row.season,
                "week": row.week,
            }
        )
        records.append(
            {
                "team": row.away_team,
                "talent": float(row.away_talent),
                "margin": -margin,
                "season": row.season,
                "week": row.week,
            }
        )
    return pd.DataFrame.from_records(records)


def compute_talent_priors(
    config: TalentPriorConfig,
    games_df: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """Compute zero-centered talent priors for all teams."""
    df = _prepare_games_df(config, games_df)
    team_games = _expand_team_games(df)
    grouped = team_games.groupby("team")

    talent_scores = grouped["talent"].mean()
    margin_scores = grouped["margin"].mean()
    games_played = grouped.size()

    talent_centered = talent_scores - talent_scores.mean()
    talent_component = (talent_centered / config.talent_scale) * config.talent_weight
    margin_component = margin_scores * config.margin_weight

    prior = talent_component + margin_component

    if config.min_games > 0:
        divisor = max(config.min_games, 1)
        shrinkage = (games_played / divisor).clip(
            lower=config.shrinkage_floor, upper=1.0
        )
        prior = prior * shrinkage

    if config.enforce_zero_mean:
        prior -= prior.mean()

    priors_df = pd.DataFrame(
        {
            "team": talent_scores.index,
            "season": config.season,
            "week": config.week,
            "prior_rating": prior,
            "talent_score": talent_scores,
            "margin_score": margin_scores,
            "games_played": games_played.astype(int),
            "version": TALENT_PRIOR_VERSION,
        }
    ).sort_values("prior_rating", ascending=False)

    priors_df["last_updated"] = dt.datetime.now(dt.timezone.utc).isoformat()
    priors_df = priors_df.reset_index(drop=True)
    return priors_df


def save_talent_priors(priors_df: pd.DataFrame, path: Optional[Path] = None) -> Path:
    """Persist prior table to disk."""
    if path is None:
        season = int(priors_df["season"].iloc[0])
        path = DEFAULT_OUTPUT_DIR / f"talent_priors_{season}.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    priors_df.to_csv(path, index=False)
    return path


def generate_talent_priors(
    config: TalentPriorConfig,
    persist: bool = True,
    games_df: Optional[pd.DataFrame] = None,
) -> tuple[pd.DataFrame, Optional[Path]]:
    """Compute priors and optionally persist them."""
    priors_df = compute_talent_priors(config=config, games_df=games_df)
    output_path = config.resolved_cache_path() if persist else None
    if persist:
        save_talent_priors(priors_df, output_path)
    return priors_df, output_path


__all__ = [
    "TalentPriorConfig",
    "compute_talent_priors",
    "generate_talent_priors",
    "save_talent_priors",
]

