#!/usr/bin/env python3
"""
Fetch 2025 Week 12 CFBD datasets for the starter_pack snapshots.

This script refreshes all starter_pack CSVs that need Week 12 data for
the 2025 season:

- advanced_game_stats/2025.csv
- advanced_season_stats/2025.csv
- season_stats/2025.csv
- drives/drives_2025.csv
- game_stats/2025.csv
- plays/2025/regular_<week>_plays.csv (weeks 1-12)

Usage:
    CFBD_API_KEY=... python project_management/TOOLS_AND_CONFIG/fetch_2025_week12_data.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Dict, List

import pandas as pd
import cfbd

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from starter_pack.utils.cfbd_loader import (
    RateLimiter,
    live_cfbd_session,
    DEFAULT_HOST,
)

YEAR = 2025
SEASON_TYPE = "regular"
START_WEEK = 1
END_WEEK = 12
DATA_DIR = Path("starter_pack/data")
CFBD_HOST = os.environ.get("CFBD_API_HOST", DEFAULT_HOST)
_RATE_LIMITER = RateLimiter()


def rate_limit() -> None:
    _RATE_LIMITER.wait()


def flatten(prefix: str, data: Dict) -> Dict[str, object]:
    flat: Dict[str, object] = {}
    for key, value in data.items():
        name = f"{prefix}_{key}"
        if isinstance(value, dict):
            flat.update(flatten(name, value))
        else:
            flat[name] = value
    return flat


def reorder_columns(df: pd.DataFrame, sample_path: Path) -> pd.DataFrame:
    if not sample_path.exists():
        return df
    sample_cols = pd.read_csv(sample_path, nrows=0).columns.tolist()
    new_cols = df.columns.tolist()
    ordered = [col for col in sample_cols if col in new_cols]
    extras = [col for col in new_cols if col not in ordered]
    return df[ordered + extras]


def fetch_advanced_game_stats(stats_api: cfbd.StatsApi) -> pd.DataFrame:
    records: List[Dict[str, object]] = []
    for week in range(START_WEEK, END_WEEK + 1):
        rate_limit()
        stats = stats_api.get_advanced_game_stats(
            year=YEAR,
            week=week,
            season_type=SEASON_TYPE,
        )
        for stat in stats:
            base = {
                "gameId": stat.game_id,
                "season": stat.season,
                "week": stat.week,
                "team": stat.team,
                "opponent": stat.opponent,
            }
            base.update(flatten("offense", stat.offense.to_dict()))
            base.update(flatten("defense", stat.defense.to_dict()))
            records.append(base)
    return pd.DataFrame(records)


def fetch_advanced_season_stats(stats_api: cfbd.StatsApi) -> pd.DataFrame:
    rate_limit()
    stats = stats_api.get_advanced_season_stats(
        year=YEAR,
        start_week=START_WEEK,
        end_week=END_WEEK,
    )
    rows: List[Dict[str, object]] = []
    for stat in stats:
        base = {
            "season": stat.season,
            "team": stat.team,
            "conference": stat.conference,
        }
        base.update(flatten("offense", stat.offense.to_dict()))
        base.update(flatten("defense", stat.defense.to_dict()))
        rows.append(base)
    return pd.DataFrame(rows)


def fetch_season_stats(stats_api: cfbd.StatsApi) -> pd.DataFrame:
    rate_limit()
    stats = stats_api.get_team_stats(
        year=YEAR,
        start_week=START_WEEK,
        end_week=END_WEEK,
    )
    rows: Dict[tuple, Dict[str, object]] = {}
    for stat in stats:
        key = (stat.team, stat.conference)
        row = rows.setdefault(
            key,
            {
                "season": stat.season,
                "team": stat.team,
                "conference": stat.conference,
            },
        )
        row[stat.stat_name] = stat.stat_value.actual_instance
    return pd.DataFrame(rows.values())


def fetch_drives(drives_api: cfbd.DrivesApi) -> pd.DataFrame:
    records: List[Dict[str, object]] = []
    for week in range(START_WEEK, END_WEEK + 1):
        rate_limit()
        drives = drives_api.get_drives(year=YEAR, week=week, season_type=SEASON_TYPE)
        for drive in drives:
            data = drive.to_dict()
            for key in ("startTime", "endTime", "elapsed"):
                if key in data and data[key] is not None:
                    data[key] = json.dumps(data[key])
            records.append(data)
    df = pd.DataFrame(records)
    # Drop elapsed to match historical schema
    if "elapsed" in df.columns:
        df = df.drop(columns=["elapsed"])
    return df


def fetch_game_stats(games_api: cfbd.GamesApi) -> pd.DataFrame:
    rows: List[Dict[str, object]] = []
    for week in range(START_WEEK, END_WEEK + 1):
        rate_limit()
        games = games_api.get_game_team_stats(
            year=YEAR,
            week=week,
            season_type=SEASON_TYPE,
        )
        for game in games:
            teams = game.teams or []
            for idx, team in enumerate(teams):
                opponent = next((t for j, t in enumerate(teams) if j != idx), None)
                row: Dict[str, object] = {
                    "game_id": game.id,
                    "season": YEAR,
                    "week": week,
                    "season_type": SEASON_TYPE,
                    "home_away": team.home_away,
                    "team_id": team.team_id,
                    "team": team.team,
                    "conference": team.conference,
                    "opponent_id": opponent.team_id if opponent else None,
                    "opponent": opponent.team if opponent else None,
                    "opponent_conference": opponent.conference if opponent else None,
                }
                if team.points is not None:
                    row["points"] = team.points
                for stat in team.stats or []:
                    row[stat.category] = stat.stat
                rows.append(row)
    return pd.DataFrame(rows)


def fetch_plays(plays_api: cfbd.PlaysApi) -> Dict[int, pd.DataFrame]:
    weekly_frames: Dict[int, pd.DataFrame] = {}
    for week in range(START_WEEK, END_WEEK + 1):
        rate_limit()
        plays = plays_api.get_plays(
            year=YEAR,
            week=week,
            season_type=SEASON_TYPE,
        )
        records: List[Dict[str, object]] = []
        for play in plays:
            data = play.to_dict()
            if data.get("clock") is not None:
                data["clock"] = json.dumps(data["clock"])
            records.append(data)
        weekly_frames[week] = pd.DataFrame(records)
    return weekly_frames


def ensure_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def write_csv(df: pd.DataFrame, path: Path, sample_path: Path) -> None:
    ensure_dir(path)
    ordered = reorder_columns(df, sample_path)
    ordered.to_csv(path, index=False)


def main() -> None:
    api_key = os.environ.get("CFBD_API_KEY") or os.environ.get("CFBD_API_TOKEN")
    if not api_key:
        raise SystemExit("CFBD_API_KEY environment variable is required.")

    with live_cfbd_session(api_key=api_key, host=CFBD_HOST) as session:
        stats_api = session.stats_api
        games_api = session.games_api
        drives_api = session.drives_api
        plays_api = session.plays_api

        print("Fetching advanced game stats...")
        adv_game_df = fetch_advanced_game_stats(stats_api)
        write_csv(
            adv_game_df,
            DATA_DIR / "advanced_game_stats" / f"{YEAR}.csv",
            DATA_DIR / "advanced_game_stats" / "2024.csv",
        )

        print("Fetching advanced season stats...")
        adv_season_df = fetch_advanced_season_stats(stats_api)
        write_csv(
            adv_season_df,
            DATA_DIR / "advanced_season_stats" / f"{YEAR}.csv",
            DATA_DIR / "advanced_season_stats" / "2024.csv",
        )

        print("Fetching traditional season stats...")
        season_df = fetch_season_stats(stats_api)
        write_csv(
            season_df,
            DATA_DIR / "season_stats" / f"{YEAR}.csv",
            DATA_DIR / "season_stats" / "2024.csv",
        )

        print("Fetching drives...")
        drives_df = fetch_drives(drives_api)
        write_csv(
            drives_df,
            DATA_DIR / "drives" / f"drives_{YEAR}.csv",
            DATA_DIR / "drives" / "drives_2024.csv",
        )

        print("Fetching game stats...")
        game_stats_df = fetch_game_stats(games_api)
        write_csv(
            game_stats_df,
            DATA_DIR / "game_stats" / f"{YEAR}.csv",
            DATA_DIR / "game_stats" / "2024.csv",
        )

        print("Fetching plays per week...")
        plays_frames = fetch_plays(plays_api)
        plays_sample = DATA_DIR / "plays" / "2024" / "regular_1_plays.csv"
        for week, frame in plays_frames.items():
            path = DATA_DIR / "plays" / str(YEAR) / f"regular_{week}_plays.csv"
            write_csv(frame, path, plays_sample)

    print("✅ Completed 2025 Week 12 data refresh.")


if __name__ == "__main__":
    main()

