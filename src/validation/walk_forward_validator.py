"""
Walk-forward validation for time-series model evaluation.

Implements walk-forward validation that respects temporal ordering by training
on historical data and testing on future weeks/seasons. Supports multiple
validation strategies (expanding window, rolling window, fixed-size window).
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_PATH = PROJECT_ROOT / "model_pack" / "updated_training_data.csv"
WALK_FORWARD_VERSION = "0.1.0"


@dataclass
class WalkForwardConfig:
    """Configuration for walk-forward validation."""

    season_start: int = 2016
    season_end: int = 2025
    week_start: int = 5
    min_train_games: int = 100
    min_test_games: int = 10
    validation_strategy: str = "expanding"  # expanding, rolling, fixed
    window_size_seasons: Optional[int] = None  # For rolling/fixed windows
    step_size_weeks: int = 1
    data_path: Path = DEFAULT_DATA_PATH
    output_dir: Optional[Path] = None

    def resolved_output_dir(self) -> Path:
        if self.output_dir:
            return self.output_dir
        return PROJECT_ROOT / "reports" / "walk_forward_validation"


@dataclass
class ValidationFold:
    """Represents a single train/test split in walk-forward validation."""

    fold_id: int
    train_season_start: int
    train_season_end: int
    train_week_start: int
    train_week_end: Optional[int]
    test_season_start: int
    test_season_end: int
    test_week_start: int
    test_week_end: Optional[int]
    train_games: int
    test_games: int


def _filter_games_by_window(
    df: pd.DataFrame,
    season_start: int,
    season_end: int,
    week_start: int,
    week_end: Optional[int],
) -> pd.DataFrame:
    """Filter games DataFrame to specified season/week window."""
    mask = (df["season"] >= season_start) & (df["season"] <= season_end)
    if week_end is None:
        mask = mask & (df["week"] >= week_start)
    else:
        season_mask = (df["season"] > season_start) & (df["season"] < season_end)
        week_mask = (
            ((df["season"] == season_start) & (df["week"] >= week_start))
            | season_mask
            | ((df["season"] == season_end) & (df["week"] <= week_end))
        )
        mask = mask & week_mask
    return df[mask].copy()


def _generate_folds(config: WalkForwardConfig, df: pd.DataFrame) -> List[ValidationFold]:
    """Generate validation folds based on configuration strategy."""
    folds = []
    fold_id = 0

    if config.validation_strategy == "expanding":
        # Expanding window: train on all data up to test period
        for test_season in range(config.season_start + 1, config.season_end + 1):
            for test_week in range(config.week_start, 16, config.step_size_weeks):
                train_end_season = test_season - 1
                train_end_week = None if test_season > config.season_start + 1 else test_week - 1

                train_df = _filter_games_by_window(
                    df,
                    config.season_start,
                    train_end_season,
                    config.week_start,
                    train_end_week,
                )
                test_df = _filter_games_by_window(
                    df, test_season, test_season, test_week, test_week
                )

                if len(train_df) >= config.min_train_games and len(test_df) >= config.min_test_games:
                    folds.append(
                        ValidationFold(
                            fold_id=fold_id,
                            train_season_start=config.season_start,
                            train_season_end=train_end_season,
                            train_week_start=config.week_start,
                            train_week_end=train_end_week,
                            test_season_start=test_season,
                            test_season_end=test_season,
                            test_week_start=test_week,
                            test_week_end=test_week,
                            train_games=len(train_df),
                            test_games=len(test_df),
                        )
                    )
                    fold_id += 1

    elif config.validation_strategy == "rolling":
        # Rolling window: fixed-size training window that moves forward
        if config.window_size_seasons is None:
            window_size = 2
        else:
            window_size = config.window_size_seasons

        for test_season in range(config.season_start + window_size, config.season_end + 1):
            for test_week in range(config.week_start, 16, config.step_size_weeks):
                train_start_season = test_season - window_size
                train_end_season = test_season - 1
                train_end_week = None

                train_df = _filter_games_by_window(
                    df,
                    train_start_season,
                    train_end_season,
                    config.week_start,
                    train_end_week,
                )
                test_df = _filter_games_by_window(
                    df, test_season, test_season, test_week, test_week
                )

                if len(train_df) >= config.min_train_games and len(test_df) >= config.min_test_games:
                    folds.append(
                        ValidationFold(
                            fold_id=fold_id,
                            train_season_start=train_start_season,
                            train_season_end=train_end_season,
                            train_week_start=config.week_start,
                            train_week_end=train_end_week,
                            test_season_start=test_season,
                            test_season_end=test_season,
                            test_week_start=test_week,
                            test_week_end=test_week,
                            train_games=len(train_df),
                            test_games=len(test_df),
                        )
                    )
                    fold_id += 1

    elif config.validation_strategy == "fixed":
        # Fixed window: same-size train and test windows
        if config.window_size_seasons is None:
            window_size = 1
        else:
            window_size = config.window_size_seasons

        for test_season in range(config.season_start + window_size, config.season_end + 1):
            for test_week in range(config.week_start, 16, config.step_size_weeks):
                train_start_season = test_season - window_size
                train_end_season = test_season - 1

                train_df = _filter_games_by_window(
                    df,
                    train_start_season,
                    train_end_season,
                    config.week_start,
                    None,
                )
                test_df = _filter_games_by_window(
                    df, test_season, test_season, test_week, test_week
                )

                if len(train_df) >= config.min_train_games and len(test_df) >= config.min_test_games:
                    folds.append(
                        ValidationFold(
                            fold_id=fold_id,
                            train_season_start=train_start_season,
                            train_season_end=train_end_season,
                            train_week_start=config.week_start,
                            train_week_end=None,
                            test_season_start=test_season,
                            test_season_end=test_season,
                            test_week_start=test_week,
                            test_week_end=test_week,
                            train_games=len(train_df),
                            test_games=len(test_df),
                        )
                    )
                    fold_id += 1

    return folds


def _calculate_fold_metrics(
    predictions: np.ndarray,
    actuals: np.ndarray,
    spreads: Optional[np.ndarray] = None,
) -> Dict[str, float]:
    """Calculate performance metrics for a validation fold."""
    valid_mask = ~(np.isnan(predictions) | np.isnan(actuals))
    if valid_mask.sum() == 0:
        return {
            "mae": np.nan,
            "rmse": np.nan,
            "bias": np.nan,
            "winner_accuracy": np.nan,
            "ats_accuracy": np.nan,
            "n_games": 0,
        }

    pred_valid = predictions[valid_mask]
    actual_valid = actuals[valid_mask]

    mae = float(np.mean(np.abs(pred_valid - actual_valid)))
    rmse = float(np.sqrt(np.mean((pred_valid - actual_valid) ** 2)))
    bias = float(np.mean(pred_valid - actual_valid))

    # Winner accuracy
    pred_winners = pred_valid > 0
    actual_winners = actual_valid > 0
    winner_accuracy = float((pred_winners == actual_winners).mean())

    # ATS accuracy (if spreads available)
    ats_accuracy = np.nan
    if spreads is not None:
        spread_valid = spreads[valid_mask]
        pred_cover = pred_valid > spread_valid
        actual_cover = actual_valid > spread_valid
        ats_accuracy = float((pred_cover == actual_cover).mean())

    return {
        "mae": mae,
        "rmse": rmse,
        "bias": bias,
        "winner_accuracy": winner_accuracy,
        "ats_accuracy": ats_accuracy,
        "n_games": int(valid_mask.sum()),
    }


def run_walk_forward_validation(
    config: WalkForwardConfig,
    model_predictor: callable,
    games_df: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """
    Execute walk-forward validation across multiple time periods.

    Args:
        config: Validation configuration.
        model_predictor: Callable that takes (train_df, test_df) and returns
            predictions array.
        games_df: Optional pre-loaded games DataFrame.

    Returns:
        DataFrame with metrics for each fold plus aggregate statistics.
    """
    if games_df is None:
        if not config.data_path.exists():
            raise FileNotFoundError(f"Data not found at {config.data_path}")
        games_df = pd.read_csv(config.data_path)

    required_cols = {"season", "week", "home_points", "away_points"}
    missing = required_cols - set(games_df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    games_df = games_df.copy()
    games_df["margin"] = games_df["home_points"] - games_df["away_points"]
    games_df["week"] = games_df["week"].fillna(0).astype(int)

    folds = _generate_folds(config, games_df)
    if not folds:
        raise ValueError("No validation folds generated. Check configuration.")

    fold_results = []

    for fold in folds:
        train_df = _filter_games_by_window(
            games_df,
            fold.train_season_start,
            fold.train_season_end,
            fold.train_week_start,
            fold.train_week_end,
        )
        test_df = _filter_games_by_window(
            games_df,
            fold.test_season_start,
            fold.test_season_end,
            fold.test_week_start,
            fold.test_week_end,
        )

        try:
            predictions = model_predictor(train_df, test_df)
            actuals = test_df["margin"].values
            spreads = test_df["spread"].values if "spread" in test_df.columns else None

            metrics = _calculate_fold_metrics(predictions, actuals, spreads)

            fold_results.append(
                {
                    "fold_id": fold.fold_id,
                    "train_season_start": fold.train_season_start,
                    "train_season_end": fold.train_season_end,
                    "test_season": fold.test_season_start,
                    "test_week": fold.test_week_start,
                    "train_games": fold.train_games,
                    "test_games": fold.test_games,
                    **metrics,
                }
            )
        except Exception as e:
            fold_results.append(
                {
                    "fold_id": fold.fold_id,
                    "train_season_start": fold.train_season_start,
                    "train_season_end": fold.train_season_end,
                    "test_season": fold.test_season_start,
                    "test_week": fold.test_week_start,
                    "train_games": fold.train_games,
                    "test_games": fold.test_games,
                    "error": str(e),
                }
            )

    results_df = pd.DataFrame(fold_results)

    # Aggregate statistics
    numeric_cols = ["mae", "rmse", "bias", "winner_accuracy", "ats_accuracy"]
    available_cols = [c for c in numeric_cols if c in results_df.columns]
    if available_cols:
        aggregate = results_df[available_cols].agg(["mean", "std", "min", "max"]).T
        aggregate["validation_strategy"] = config.validation_strategy
        aggregate["total_folds"] = len(folds)
        aggregate["version"] = WALK_FORWARD_VERSION

    results_df["validation_strategy"] = config.validation_strategy
    results_df["version"] = WALK_FORWARD_VERSION
    results_df["created_at"] = dt.datetime.now(dt.timezone.utc).isoformat()

    return results_df


__all__ = ["WalkForwardConfig", "ValidationFold", "run_walk_forward_validation"]

