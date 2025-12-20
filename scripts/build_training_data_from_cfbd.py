#!/usr/bin/env python3
"""Build canonical weekly/postseason training CSVs from the CFBD API.

This script fetches games from CollegeFootballData.com (via the `cfbd-python`
client), transforms them into the project's 86-feature schema, and writes the
result into the canonical training file locations:

- Weekly: `data/training/weekly/training_data_{season}_week{NN}.csv`
- Postseason: `data/training/weekly/training_data_{season}_postseason.csv`

It is intentionally focused on producing *inputs* for the integration step.
To merge these files into `data/processed/training/master_training_data_v2.csv`, run:

  `python3 scripts/integrate_weekly_files.py --season 2025 --weeks 15 --include-postseason`

Environment:
  - `CFBD_API_KEY` or `CFBD_API_TOKEN` (required)
  - `CFBD_HOST=production|next` (optional; defaults to production)

Usage:
  python3 scripts/build_training_data_from_cfbd.py --season 2025 --week 15
  python3 scripts/build_training_data_from_cfbd.py --season 2025 --season-type postseason
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence

import pandas as pd
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

from model_pack.utils.path_utils import ensure_directory_exists  # noqa: E402
from src.cfbd_client.unified_client import UnifiedCFBDClient  # noqa: E402
from src.features.cfbd_feature_engineering import (  # noqa: E402
    CFBDFeatureEngineer,
    FeatureEngineeringConfig,
)


@dataclass(frozen=True)
class BuildTargets:
    """Resolved output targets for a build run."""

    output_path: Path
    season: int
    week: Optional[int]
    season_type: str


def _parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--season", type=int, required=True)
    parser.add_argument(
        "--season-type",
        choices=("regular", "postseason"),
        default="regular",
        help="CFBD seasonType filter (default: regular).",
    )
    parser.add_argument(
        "--week",
        type=int,
        default=None,
        help="Week number for regular-season pulls (required for regular).",
    )
    parser.add_argument(
        "--with-plays",
        action="store_true",
        help="Fetch play-by-play to compute advanced metrics (slow).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional override output path (defaults to canonical location).",
    )
    return parser.parse_args(argv)


def _require_api_key() -> None:
    if os.getenv("CFBD_API_KEY") or os.getenv("CFBD_API_TOKEN"):
        return
    raise RuntimeError("CFBD_API_KEY or CFBD_API_TOKEN is required.")


def _resolve_targets(args: argparse.Namespace) -> BuildTargets:
    season = int(args.season)
    season_type = str(args.season_type)
    week = int(args.week) if args.week is not None else None

    if season_type == "regular" and week is None:
        raise ValueError("--week is required when --season-type=regular")
    if season_type == "postseason" and week is not None:
        raise ValueError("--week must not be set when --season-type=postseason")

    if args.output:
        output_path = Path(args.output).resolve()
    else:
        weekly_dir = PROJECT_ROOT / "data" / "training" / "weekly"
        if season_type == "postseason":
            output_path = weekly_dir / f"training_data_{season}_postseason.csv"
        else:
            output_path = weekly_dir / f"training_data_{season}_week{int(week):02d}.csv"

    ensure_directory_exists(output_path.parent)
    return BuildTargets(
        output_path=output_path,
        season=season,
        week=week,
        season_type=season_type,
    )


def _fetch_advanced_metrics(
    *,
    client: UnifiedCFBDClient,
    games_df: pd.DataFrame,
    include_plays: bool,
) -> dict[int, dict]:
    if games_df.empty:
        return {}

    try:
        from model_pack.utils.cfbd_advanced_metrics import AdvancedMetricsBuilder
    except ImportError:
        return {}

    builder = AdvancedMetricsBuilder(
        api_client=client.api_client,
        season=int(games_df["season"].iloc[0]),
    )

    plays_df = None
    if include_plays:
        records: list[dict] = []
        for game_id in games_df["id"].dropna().unique().tolist():
            plays = client.plays_api.get_plays(game_id=int(game_id)) or []
            for play in plays:
                records.append(play.to_dict() if hasattr(play, "to_dict") else play)
        plays_df = pd.DataFrame(records) if records else None

    metrics = builder.build_metrics_for_games(games_df, plays_df)
    coerced: dict[int, dict] = {}
    for key, value in metrics.items():
        try:
            coerced[int(key)] = dict(value)
        except Exception:
            continue
    return coerced


def build_training_data(
    *,
    season: int,
    week: Optional[int],
    season_type: str,
    output_path: Path,
    with_plays: bool,
) -> Path:
    """Build a canonical training CSV for a season/week/season_type.

    Args:
        season: Season year (e.g., 2025).
        week: Week number for regular season builds. Must be None for postseason.
        season_type: CFBD season type ("regular" or "postseason").
        output_path: Destination CSV path.
        with_plays: Whether to include play-by-play derived metrics.

    Returns:
        Path to the written CSV file.
    """
    _require_api_key()
    client = UnifiedCFBDClient()
    engineer = CFBDFeatureEngineer(
        FeatureEngineeringConfig(season=season, enforce_reference_schema=True)
    )

    raw_games = client.get_games(year=season, week=week, season_type=season_type) or []
    games_df = engineer.prepare_games_frame(raw_games, source="rest")
    if games_df.empty:
        raise RuntimeError("CFBD returned 0 games for the requested filters.")

    weeks_to_fetch = sorted(games_df["week"].dropna().unique().astype(int).tolist())
    lines_payload: list[dict] = []
    for wk in weeks_to_fetch:
        try:
            lines_payload.extend(client.get_lines(year=season, week=int(wk)) or [])
        except Exception:
            continue
    games_df = engineer.merge_spreads(games_df, lines_payload)

    metrics_by_game = _fetch_advanced_metrics(
        client=client, games_df=games_df, include_plays=with_plays
    )
    features_df = engineer.build_feature_frame(games_df, metrics_by_game)
    features_df.to_csv(output_path, index=False)
    return output_path


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parse_args(argv)
    targets = _resolve_targets(args)
    build_training_data(
        season=targets.season,
        week=targets.week,
        season_type=targets.season_type,
        output_path=targets.output_path,
        with_plays=bool(args.with_plays),
    )
    print(f"✅ Wrote {targets.output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
