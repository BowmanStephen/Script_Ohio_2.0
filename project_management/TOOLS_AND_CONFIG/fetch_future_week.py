#!/usr/bin/env python3
"""
Fetch additional 2025 CFBD data for weeks 13+ and append to starter pack files.

Usage:
    CFBD_API_KEY=... python project_management/TOOLS_AND_CONFIG/fetch_future_week.py --week 13
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List

import pandas as pd
import cfbd

from starter_pack.utils.cfbd_loader import DEFAULT_HOST, RateLimiter, live_cfbd_session

DATA_DIR = Path("starter_pack/data")
GAMES_PATH = DATA_DIR / "2025_games.csv"
REPORT_PATH = DATA_DIR / "2025_data_integration_report.json"
CFBD_HOST = os.environ.get("CFBD_API_HOST", DEFAULT_HOST)
_RATE_LIMITER = RateLimiter()


def _load_games_frame() -> pd.DataFrame:
    if GAMES_PATH.exists():
        return pd.read_csv(GAMES_PATH, low_memory=False)
    return pd.DataFrame()


def _serialize_games(games: List[cfbd.models.game.Game]) -> pd.DataFrame:
    rows = []
    for game in games:
        data = game.to_dict()
        rows.append(data)
    return pd.DataFrame(rows)


def fetch_week_data(season: int, week: int, api_key: str) -> dict:
    print(f"Fetching season={season}, week={week} games...")
    with live_cfbd_session(api_key=api_key, host=CFBD_HOST) as session:
        _RATE_LIMITER.wait()
        games = session.games_api.get_games(year=season, week=week, season_type="regular")
        if not games:
            raise RuntimeError(f"No games returned for week {week}. CFBD may not be updated yet.")

        new_games = _serialize_games(games)
    new_games["fetched_at_utc"] = datetime.now(timezone.utc).isoformat()

    existing = _load_games_frame()
    combined = (
        pd.concat([existing, new_games], ignore_index=True, sort=False)
        .drop_duplicates(subset=["id"], keep="last")
        .sort_values(["season", "week", "start_date"], na_position="last")
        .reset_index(drop=True)
    )
    GAMES_PATH.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(GAMES_PATH, index=False)

    weeks = sorted(combined["week"].dropna().unique().tolist())
    _update_integration_report(weeks, week)

    return {
        "fetched_games": len(new_games),
        "total_games": len(combined),
        "weeks": weeks,
    }


def _update_integration_report(weeks: List[int], latest_week: int) -> None:
    if not REPORT_PATH.exists():
        return

    with open(REPORT_PATH, "r") as handle:
        report = json.load(handle)

    if "weeks_covered" in report:
        start = report["weeks_covered"].split("-")[0]
        report["weeks_covered"] = f"{start}-{latest_week}"
    else:
        report["weeks_covered"] = f"1-{latest_week}"

    report["last_updated"] = datetime.now(timezone.utc).isoformat()
    report["known_weeks"] = weeks

    with open(REPORT_PATH, "w") as handle:
        json.dump(report, handle, indent=2)
    print(f"Updated integration report: weeks={report['weeks_covered']}")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch and append week data for 2025 season.")
    parser.add_argument("--week", type=int, required=True, help="Week number to fetch (e.g., 13).")
    parser.add_argument("--season", type=int, default=2025, help="Season year (default: 2025).")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    api_key = os.environ.get("CFBD_API_KEY")
    if not api_key:
        raise SystemExit("CFBD_API_KEY environment variable is required.")

    summary = fetch_week_data(args.season, args.week, api_key)
    print(
        f"✓ Added {summary['fetched_games']} games for Week {args.week}. "
        f"Total games now: {summary['total_games']}."
    )
    print(f"Weeks tracked: {summary['weeks']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

