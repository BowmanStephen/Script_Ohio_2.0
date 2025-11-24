"""
Coleman metamodel implementation that blends multiple rating systems.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from joblib import dump
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from .massey_ratings import MasseyConfig, load_game_data

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LIBRARY_DIR = PROJECT_ROOT / "src" / "ratings"
DEFAULT_DATA_PATH = PROJECT_ROOT / "model_pack" / "updated_training_data.csv"
COLEMAN_MODEL_VERSION = "0.1.0"

logger = logging.getLogger(__name__)


@dataclass
class ColemanConfig:
    """Configuration for the Coleman metamodel solver."""

    season: int = 2025
    week: Optional[int] = None
    regularization: float = 1.0
    data_path: Path = DEFAULT_DATA_PATH
    ratings_path: Optional[Path] = None
    model_path: Optional[Path] = None
    metrics_path: Optional[Path] = None
    early_week_threshold: int = 5

    def resolved_ratings_path(self) -> Path:
        if self.ratings_path:
            return self.ratings_path
        DEFAULT_LIBRARY_DIR.mkdir(parents=True, exist_ok=True)
        return DEFAULT_LIBRARY_DIR / f"coleman_metamodel_{self.season}.csv"

    def resolved_model_path(self) -> Path:
        if self.model_path:
            return self.model_path
        DEFAULT_LIBRARY_DIR.mkdir(parents=True, exist_ok=True)
        return DEFAULT_LIBRARY_DIR / f"coleman_metamodel_{self.season}.joblib"

    def resolved_metrics_path(self) -> Path:
        if self.metrics_path:
            return self.metrics_path
        DEFAULT_LIBRARY_DIR.mkdir(parents=True, exist_ok=True)
        return DEFAULT_LIBRARY_DIR / f"coleman_metamodel_{self.season}_metrics.json"


def _build_team_game_records(games_df: pd.DataFrame) -> pd.DataFrame:
    records: List[Dict] = []
    for row in games_df.itertuples():
        diff = float(row.home_points - row.away_points)
        records.append(
            {
                "team": row.home_team,
                "opponent": row.away_team,
                "margin": diff,
                "is_home": True,
                "week": row.week,
                "season": row.season,
            }
        )
        records.append(
            {
                "team": row.away_team,
                "opponent": row.home_team,
                "margin": -diff,
                "is_home": False,
                "week": row.week,
                "season": row.season,
            }
        )
    return pd.DataFrame.from_records(records)


def _compute_team_features(team_games: pd.DataFrame, config: ColemanConfig) -> pd.DataFrame:
    grouped = team_games.groupby("team")
    team_stats = grouped["margin"].agg(
        avg_margin="mean",
        games_played="size",
    )

    home_margin = team_games[team_games["is_home"]].groupby("team")["margin"].mean()
    away_margin = team_games[~team_games["is_home"]].groupby("team")["margin"].mean()
    early_games = team_games[team_games["week"] <= config.early_week_threshold].groupby("team")["margin"].count()

    team_stats["home_margin"] = home_margin
    team_stats["away_margin"] = away_margin
    team_stats["home_road_split"] = team_stats["home_margin"].fillna(0) - team_stats["away_margin"].fillna(0)
    team_stats["early_games"] = early_games.reindex(team_stats.index).fillna(0)

    team_stats = team_stats.reset_index()
    team_stats["season"] = config.season
    return team_stats


def _merge_rating_sources(
    team_stats: pd.DataFrame,
    massey_df: pd.DataFrame,
    cfbd_df: pd.DataFrame,
) -> pd.DataFrame:
    massey_subset = massey_df[["team", "rating"]].rename(columns={"rating": "massey_rating"})
    merged = team_stats.merge(massey_subset, on="team", how="left")

    if not cfbd_df.empty:
        cfbd_cols = ["team", "sp_rating", "fpi_rating", "elo_rating", "srs_rating"]
        cfbd_subset = cfbd_df[cfbd_cols].copy()
        merged = merged.merge(cfbd_subset, on="team", how="left")
    else:
        for col in ["sp_rating", "fpi_rating", "elo_rating", "srs_rating"]:
            merged[col] = np.nan

    merged["disagreement_sp_massey"] = merged["massey_rating"] - merged["sp_rating"]
    merged["disagreement_fpi_massey"] = merged["massey_rating"] - merged["fpi_rating"]
    rating_cols = ["massey_rating", "sp_rating", "fpi_rating", "elo_rating", "srs_rating"]
    merged["rating_disagreement_std"] = merged[rating_cols].std(axis=1)
    return merged


def _fit_pipeline(X: pd.DataFrame, y: pd.Series, alpha: float) -> Pipeline:
    pipeline = Pipeline(
        steps=[
            ("scaler", StandardScaler(with_mean=True, with_std=True)),
            ("model", Ridge(alpha=alpha)),
        ]
    )
    pipeline.fit(X, y)
    return pipeline


def train_coleman_metamodel(
    config: ColemanConfig,
    massey_df: pd.DataFrame,
    cfbd_df: pd.DataFrame,
    games_df: Optional[pd.DataFrame] = None,
) -> Tuple[pd.DataFrame, Dict[str, float], Pipeline]:
    """Train the Coleman metamodel and return ratings + metrics."""
    if games_df is None:
        massey_config = MasseyConfig(
            season=config.season,
            week=config.week,
            data_path=config.data_path,
        )
        games_df = load_game_data(massey_config)

    team_games = _build_team_game_records(games_df)
    team_stats = _compute_team_features(team_games, config)
    merged = _merge_rating_sources(team_stats, massey_df, cfbd_df)

    feature_cols = [
        "massey_rating",
        "sp_rating",
        "fpi_rating",
        "elo_rating",
        "srs_rating",
        "home_road_split",
        "early_games",
        "games_played",
        "disagreement_sp_massey",
        "disagreement_fpi_massey",
        "rating_disagreement_std",
    ]

    for col in feature_cols:
        if col not in merged:
            merged[col] = 0.0

    feature_frame = merged[feature_cols].fillna(merged[feature_cols].mean())
    feature_frame = feature_frame.fillna(0.0)
    target = merged["avg_margin"].fillna(0.0)

    pipeline = _fit_pipeline(feature_frame, target, config.regularization)
    predictions = pipeline.predict(feature_frame)

    mae = float(mean_absolute_error(target, predictions))
    bias = float(np.mean(predictions - target))
    r2 = float(r2_score(target, predictions))
    sign_accuracy = float(np.mean(np.sign(predictions) == np.sign(target)))

    ratings_df = pd.DataFrame(
        {
            "team": merged["team"],
            "season": config.season,
            "rating": predictions,
            "games_played": merged["games_played"],
            "avg_margin": merged["avg_margin"],
            "home_road_split": merged["home_road_split"],
            "model_version": COLEMAN_MODEL_VERSION,
        }
    ).sort_values("rating", ascending=False)

    metrics = {
        "mae": mae,
        "bias": bias,
        "r2": r2,
        "sign_accuracy": sign_accuracy,
        "samples": int(len(ratings_df)),
    }
    return ratings_df, metrics, pipeline


def load_coleman_ratings(
    config: Optional[ColemanConfig] = None,
    refresh: bool = False,
    massey_df: Optional[pd.DataFrame] = None,
    cfbd_df: Optional[pd.DataFrame] = None,
    games_df: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """Load or train the Coleman metamodel ratings."""
    config = config or ColemanConfig()
    ratings_path = config.resolved_ratings_path()

    if not refresh and ratings_path.exists():
        return pd.read_csv(ratings_path)

    if massey_df is None or massey_df.empty:
        raise ValueError("massey_df is required to train Coleman metamodel.")
    if cfbd_df is None:
        cfbd_df = pd.DataFrame()

    ratings_df, metrics, pipeline = train_coleman_metamodel(
        config=config,
        massey_df=massey_df,
        cfbd_df=cfbd_df,
        games_df=games_df,
    )

    ratings_path.parent.mkdir(parents=True, exist_ok=True)
    ratings_df.to_csv(ratings_path, index=False)
    dump(pipeline, config.resolved_model_path())
    config.resolved_metrics_path().write_text(json.dumps(metrics, indent=2))

    logger.info(
        "Coleman metamodel trained for season %s (MAE=%.2f, bias=%.2f, r2=%.2f)",
        config.season,
        metrics["mae"],
        metrics["bias"],
        metrics["r2"],
    )
    return ratings_df


__all__ = ["ColemanConfig", "load_coleman_ratings", "train_coleman_metamodel"]

