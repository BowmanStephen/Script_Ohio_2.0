#!/usr/bin/env python3
"""
Refresh starter-pack CSV snapshots directly from the CFBD API.

This fills the “manual data refresh” gap by wiring the official cfbd-python
client into a single CLI. It:

* Pulls the latest games, drives, team season stats, and advanced season stats
  for one or more seasons.
* Writes/overwrites the normalized CSVs stored under `starter_pack/data/`.
* Respects the documented 6 req/sec rate limit (0.17s delay between calls).

Example usage:

    python project_management/core_tools/update_data.py \\
        --datasets games season_stats advanced_season_stats \\
        --seasons 2025 2024
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from project_management.data_workflows import StarterDataUpdater
from starter_pack.config.data_config import get_starter_pack_config
from starter_pack.utils.cfbd_loader import (
    CFBDLoaderError,
    CFBDSession,
    RateLimiter,
    _records_to_frame,
)

DEFAULT_DATASETS = ("games", "season_stats", "advanced_season_stats", "drives")


class StarterDataRefreshWorkflow:
    """Coordinates dataset refreshes and file writes."""

    def __init__(
        self,
        *,
        datasets: Sequence[str],
        seasons: Sequence[int],
        season_type: str,
        api_key: Optional[str],
        host: str,
        dry_run: bool,
    ) -> None:
        self.datasets = datasets or DEFAULT_DATASETS
        self.seasons = seasons
        self.season_type = season_type
        self.api_key = api_key or os.environ.get("CFBD_API_KEY") or os.environ.get("CFBD_API_TOKEN")
        if not self.api_key:
            raise RuntimeError("CFBD API key missing. Set CFBD_API_KEY or pass --api-key.")
        self.host = host
        self.dry_run = dry_run

        self.config = get_starter_pack_config()
        self.data_dir = self.config.data_dir
        self.rate_limiter = RateLimiter()
        self.games_updater = StarterDataUpdater()

    def run(self) -> Dict[str, List[Dict[str, object]]]:
        summaries: Dict[str, List[Dict[str, object]]] = {dataset: [] for dataset in self.datasets}
        with CFBDSession(api_key=self.api_key, host=self.host) as session:
            for dataset in self.datasets:
                for season in self.seasons:
                    handler = getattr(self, f"_update_{dataset}", None)
                    if handler is None:
                        raise ValueError(f"Unsupported dataset '{dataset}'. Options: {', '.join(DEFAULT_DATASETS)}")
                    summary = handler(session=session, season=season)
                    summaries[dataset].append(summary)
        return summaries

    # ------------------------------------------------------------------ #
    # Dataset handlers
    # ------------------------------------------------------------------ #
    def _update_games(self, *, session: CFBDSession, season: int) -> Dict[str, object]:
        summary = self.games_updater.run(
            season=season,
            week=None,
            season_type=self.season_type,
            api_key=self.api_key,
            dry_run=self.dry_run,
        )
        summary["dataset"] = "games"
        summary["season"] = season
        return summary

    def _update_season_stats(self, *, session: CFBDSession, season: int) -> Dict[str, object]:
        self.rate_limiter.wait()
        records = session.stats_api.get_team_season_stats(year=season)
        frame = _records_to_frame(records)
        return self._write_year_scoped_csv(frame, subdir="season_stats", filename=f"{season}.csv", dataset="season_stats")

    def _update_advanced_season_stats(self, *, session: CFBDSession, season: int) -> Dict[str, object]:
        self.rate_limiter.wait()
        records = session.stats_api.get_advanced_season_stats(year=season)
        frame = _records_to_frame(records)
        return self._write_year_scoped_csv(
            frame,
            subdir="advanced_season_stats",
            filename=f"{season}.csv",
            dataset="advanced_season_stats",
        )

    def _update_drives(self, *, session: CFBDSession, season: int) -> Dict[str, object]:
        self.rate_limiter.wait()
        records = session.drives_api.get_drives(year=season)
        frame = _records_to_frame(records)
        return self._write_year_scoped_csv(
            frame,
            subdir="drives",
            filename=f"drives_{season}.csv",
            dataset="drives",
        )

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _write_year_scoped_csv(
        self,
        frame: pd.DataFrame,
        *,
        subdir: str,
        filename: str,
        dataset: str,
    ) -> Dict[str, object]:
        target_dir = self.data_dir / subdir
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / filename

        if frame.empty:
            raise RuntimeError(f"No records returned for {dataset} {filename}")

        if not self.dry_run:
            frame.to_csv(target_path, index=False)

        return {
            "dataset": dataset,
            "file": str(target_path),
            "rows": len(frame),
            "dry_run": self.dry_run,
        }


def _parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Refresh starter-pack CSVs from CFBD")
    parser.add_argument(
        "--datasets",
        nargs="+",
        default=DEFAULT_DATASETS,
        help=f"Datasets to refresh (choices: {', '.join(DEFAULT_DATASETS)})",
    )
    parser.add_argument(
        "--seasons",
        nargs="+",
        type=int,
        required=False,
        help="One or more seasons to refresh (defaults to StarterPackDataConfig.current_year)",
    )
    parser.add_argument("--season-type", default="regular", choices=["regular", "postseason"])
    parser.add_argument("--api-key", default=None, help="CFBD API key (otherwise uses env vars)")
    parser.add_argument("--host", default="https://api.collegefootballdata.com")
    parser.add_argument("--dry-run", action="store_true", help="Fetch data but skip writing files")
    return parser.parse_args(argv)


def main(argv: Optional[Iterable[str]] = None) -> None:
    args = _parse_args(argv)
    config = get_starter_pack_config()
    seasons = args.seasons or [config.current_year]
    workflow = StarterDataRefreshWorkflow(
        datasets=args.datasets,
        seasons=seasons,
        season_type=args.season_type,
        api_key=args.api_key,
        host=args.host,
        dry_run=args.dry_run,
    )
    try:
        summary = workflow.run()
    except CFBDLoaderError as exc:
        raise SystemExit(f"CFBD loader error: {exc}") from exc
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main(sys.argv[1:])

