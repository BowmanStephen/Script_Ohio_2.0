"""Utilities to convert starter-pack games into the training dataset format."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Callable, Iterable, List, Optional

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from model_pack.migrate_starter_pack_data import StarterPackDataMigrator

DEFAULT_OUTPUT = Path("model_pack/2025_weeks1-12_migrated.csv")


def create_2025_migration_file(
    *,
    max_week: int = 12,
    min_week: int = 1,
    output_path: Path | str = DEFAULT_OUTPUT,
) -> dict:
    """
    Convert current-season starter-pack games into the model-pack training schema.

    The heavy lifting is delegated to `StarterPackDataMigrator`, but we override the
    week filter so weeks 1-12 are preserved. The resulting CSV matches the 86-feature
    training dataset layout so it can be appended directly via `extend-training`.
    """

    migrator = StarterPackDataMigrator()
    steps: List[Callable[[], bool]] = [
        migrator.load_starter_pack_data,
        migrator.load_historical_structure,
        migrator.filter_fbs_teams,
        migrator.map_to_training_format,
    ]
    for step in steps:
        ok = step()
        if ok is False:
            raise RuntimeError(f"Migration step {step.__name__} failed")

    migrator.min_processed_week = min_week
    migrator.max_processed_week = max_week
    has_games = migrator.apply_week_filter(min_week=min_week, max_week=max_week)
    if not has_games:
        raise RuntimeError(f"No games found between weeks {min_week} and {max_week}.")

    metrics_populated = migrator.populate_advanced_features()
    merged_metrics = migrator.merge_precalculated_metrics()
    if not (metrics_populated or merged_metrics):
        migrator.add_placeholder_features(allow_placeholders=True)

    frame = migrator.processed_current_season
    if frame is None or frame.empty:
        raise RuntimeError("No processed games available after migration steps.")

    frame = frame.sort_values(["week", "start_date"]).reset_index(drop=True)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output, index=False)

    return {
        "output": str(output),
        "rows": len(frame),
        "weeks": f"{frame['week'].min()}-{frame['week'].max()}",
        "games": int(frame["game_key"].nunique()) if "game_key" in frame.columns else len(frame),
        "metrics_populated": metrics_populated or merged_metrics,
    }


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create a migrated CSV for the 2025 season (Weeks 1-12 by default)."
    )
    parser.add_argument("--min-week", type=int, default=1, help="Starting week to include (default: 1).")
    parser.add_argument("--max-week", type=int, default=12, help="Final week to include (default: 12).")
    parser.add_argument(
        "--output-path",
        default=str(DEFAULT_OUTPUT),
        help=f"Destination for the migrated CSV (default: {DEFAULT_OUTPUT}).",
    )
    return parser


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        summary = create_2025_migration_file(
            min_week=args.min_week,
            max_week=args.max_week,
            output_path=args.output_path,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}")
        return 1
    print(
        f"✓ Created {summary['output']} "
        f"({summary['rows']} rows, weeks {summary['weeks']}, metrics={'yes' if summary['metrics_populated'] else 'no'})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

