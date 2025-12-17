#!/usr/bin/env python3
"""
Audit completeness of local CFBD-derived datasets for a given season.

Reads existing CSVs under starter_pack/data/ and produces:
- data/cfbd/<season>/manifest.json
- reports/data_audit_<season>.md

It can optionally query CFBD online (postseason index) if a token is present.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

CANDIDATE_GAME_ID_COLS = [
    "gameId",
    "game_id",
    "id",
    "gameID",
]
CANDIDATE_WEEK_COLS = ["week", "Week", "weekNumber"]
CANDIDATE_SEASON_TYPE_COLS = ["seasonType", "season_type", "season_type_name"]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_csv_if_exists(path: Path) -> pd.DataFrame | None:
    if not path.exists():
        return None
    return pd.read_csv(path, low_memory=False)


def find_first_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    cols_lower = {c.lower(): c for c in df.columns}
    for cand in candidates:
        if cand in df.columns:
            return cand
        if cand.lower() in cols_lower:
            return cols_lower[cand.lower()]
    return None


def normalize_game_ids(
    df: pd.DataFrame, game_id_col: str, dropna: bool = True
) -> set[int]:
    s = df[game_id_col]
    if dropna:
        s = s.dropna()
    out: set[int] = set()
    for v in s.tolist():
        try:
            out.add(int(v))
        except Exception:
            continue
    return out


def normalize_weeks(df: pd.DataFrame, week_col: str) -> set[int]:
    s = df[week_col].dropna()
    out: set[int] = set()
    for v in s.tolist():
        try:
            out.add(int(v))
        except Exception:
            continue
    return out


def parse_week_from_filename(path: Path) -> int | None:
    """
    Tries to extract a week number from a filename like:
    - regular_week_12_plays.csv
    - regular_12_plays.csv
    - week12_plays.csv
    """
    name = path.name.lower()
    patterns = [
        r"week[_\- ](\d{1,2})",
        r"regular[_\- ](\d{1,2})",
        r"[_\- ](\d{1,2})[_\- ]plays",
    ]
    for pat in patterns:
        m = re.search(pat, name)
        if m:
            try:
                return int(m.group(1))
            except Exception:
                return None
    return None


@dataclass
class DatasetAudit:
    name: str
    path: str
    exists: bool
    present_game_ids: int
    expected_game_ids: int
    missing_game_ids: list[int]
    present_weeks: list[int]
    expected_weeks: list[int]
    missing_weeks: list[int]
    notes: list[str]


def compute_missing_weeks(
    expected_weeks: Iterable[int], present_weeks: Iterable[int]
) -> list[int]:
    exp = set(expected_weeks)
    pres = set(present_weeks)
    return sorted(exp - pres)


def maybe_get_cfbd_games_postseason_online(
    season: int, base_url: str | None = None
) -> list[dict[str, Any]] | None:
    """
    Optional online lookup for postseason games. Returns None if not configured.

    Uses env:
      - CFBD_API_KEY or CFBD_API_TOKEN
      - CFBD_HOST (production or next)
    """
    token = (
        os.getenv("CFBD_API_TOKEN")
        or os.getenv("CFBD_API_KEY")
        or os.getenv("CFBD_TOKEN")
    )
    if not token:
        return None

    # Try to use UnifiedCFBDClient if available
    try:
        from src.cfbd_client.unified_client import UnifiedCFBDClient

        client = UnifiedCFBDClient()
        # Use the get_games method directly
        try:
            games = client.get_games(year=season, season_type="postseason")
            if games and isinstance(games, list):
                return games
        except Exception as e:
            print(f"UnifiedCFBDClient.get_games failed: {e}")
            pass
    except ImportError:
        pass
    except Exception as e:
        print(f"UnifiedCFBDClient initialization failed: {e}")

    # Fallback to requests
    if base_url is None:
        host_env = os.getenv("CFBD_HOST", "production").lower()
        if host_env == "next":
            base_url = "https://apinext.collegefootballdata.com"
        else:
            base_url = "https://api.collegefootballdata.com"

    try:
        import requests

        url = base_url.rstrip("/") + "/games"
        headers = {"Authorization": f"Bearer {token}"}
        resp = requests.get(
            url,
            headers=headers,
            params={"year": season, "seasonType": "postseason"},
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, list):
            return data
        return None
    except Exception as e:
        print(f"Direct HTTP request failed: {e}")
        return None


def audit(season: int, starter_data_dir: Path, include_online: bool) -> dict[str, Any]:
    games_path = starter_data_dir / "games.csv"
    game_stats_path = starter_data_dir / "game_stats" / f"{season}.csv"
    adv_game_stats_path = starter_data_dir / "advanced_game_stats" / f"{season}.csv"
    drives_path = starter_data_dir / "drives" / f"drives_{season}.csv"
    season_stats_path = starter_data_dir / "season_stats" / f"{season}.csv"
    adv_season_stats_path = starter_data_dir / "advanced_season_stats" / f"{season}.csv"
    plays_dir = starter_data_dir / "plays" / str(season)

    notes: list[str] = []

    games_df = read_csv_if_exists(games_path)
    if games_df is None:
        raise FileNotFoundError(f"Missing required file: {games_path}")

    games_game_id_col = find_first_col(games_df, CANDIDATE_GAME_ID_COLS)
    if not games_game_id_col:
        raise ValueError(
            f"Could not find game id column in {games_path}. "
            f"Looked for: {CANDIDATE_GAME_ID_COLS}"
        )

    games_week_col = find_first_col(games_df, CANDIDATE_WEEK_COLS)
    if not games_week_col:
        notes.append(
            f"games.csv is missing a week column (expected one of {CANDIDATE_WEEK_COLS}); "
            "week completeness checks may be limited."
        )

    # Filter to season
    games_season_col = find_first_col(games_df, ["season", "Season", "year", "Year"])
    if games_season_col:
        games_df = games_df[games_df[games_season_col] == season].copy()

    expected_game_ids = normalize_game_ids(games_df, games_game_id_col)

    expected_weeks: list[int] = []
    if games_week_col:
        expected_weeks = sorted(normalize_weeks(games_df, games_week_col))

    def audit_csv_dataset(name: str, path: Path) -> DatasetAudit:
        df = read_csv_if_exists(path)
        if df is None:
            return DatasetAudit(
                name=name,
                path=str(path),
                exists=False,
                present_game_ids=0,
                expected_game_ids=len(expected_game_ids),
                missing_game_ids=sorted(expected_game_ids),
                present_weeks=[],
                expected_weeks=expected_weeks,
                missing_weeks=expected_weeks,
                notes=[f"{name} file missing."],
            )

        # Filter to season if season column exists
        season_col = find_first_col(df, ["season", "Season", "year", "Year"])
        if season_col:
            df = df[df[season_col] == season].copy()

        gid_col = find_first_col(df, CANDIDATE_GAME_ID_COLS)
        ds_notes: list[str] = []
        present_ids: set[int] = set()
        if gid_col:
            present_ids = normalize_game_ids(df, gid_col)
        else:
            ds_notes.append(
                f"Could not find a game id column in {path} "
                f"(looked for {CANDIDATE_GAME_ID_COLS}); gameId checks skipped."
            )

        wk_col = find_first_col(df, CANDIDATE_WEEK_COLS)
        present_weeks_set: set[int] = set()
        if wk_col:
            present_weeks_set = normalize_weeks(df, wk_col)
        else:
            # If stats files don't carry week, we infer weeks via join to games.csv by gameId.
            if gid_col and games_week_col:
                merged = df[[gid_col]].dropna().copy()
                merged[gid_col] = pd.to_numeric(merged[gid_col], errors="coerce")
                g = games_df[[games_game_id_col, games_week_col]].copy()
                g[games_game_id_col] = pd.to_numeric(
                    g[games_game_id_col], errors="coerce"
                )
                j = merged.merge(
                    g,
                    how="left",
                    left_on=gid_col,
                    right_on=games_game_id_col,
                )
                present_weeks_set = set(
                    pd.to_numeric(j[games_week_col], errors="coerce")
                    .dropna()
                    .astype(int)
                    .tolist()
                )
            else:
                ds_notes.append(
                    f"Could not find week in {path} and could not infer from games.csv."
                )

        missing_ids = sorted(expected_game_ids - present_ids) if present_ids else []
        missing_weeks = (
            compute_missing_weeks(expected_weeks, present_weeks_set)
            if expected_weeks
            else []
        )

        return DatasetAudit(
            name=name,
            path=str(path),
            exists=True,
            present_game_ids=len(present_ids),
            expected_game_ids=len(expected_game_ids),
            missing_game_ids=missing_ids,
            present_weeks=sorted(present_weeks_set),
            expected_weeks=expected_weeks,
            missing_weeks=missing_weeks,
            notes=ds_notes,
        )

    audits: list[DatasetAudit] = []
    audits.append(audit_csv_dataset("game_stats", game_stats_path))
    audits.append(audit_csv_dataset("advanced_game_stats", adv_game_stats_path))
    audits.append(audit_csv_dataset("drives", drives_path))
    audits.append(audit_csv_dataset("season_stats", season_stats_path))
    audits.append(audit_csv_dataset("advanced_season_stats", adv_season_stats_path))

    # Plays: expected weeks from games.csv; present from filenames + optional column inference
    plays_notes: list[str] = []
    plays_present_weeks: set[int] = set()
    plays_files: list[str] = []
    if plays_dir.exists():
        for p in sorted(plays_dir.glob("*plays*.csv")):
            plays_files.append(str(p))
            wk = parse_week_from_filename(p)
            if wk is not None:
                plays_present_weeks.add(wk)
            else:
                # fallback: read minimal to find week column
                try:
                    df = pd.read_csv(p)
                    wk_col = find_first_col(df, CANDIDATE_WEEK_COLS)
                    if wk_col:
                        plays_present_weeks |= normalize_weeks(df, wk_col)
                    else:
                        plays_notes.append(
                            f"Could not infer week for plays file {p.name}"
                        )
                except Exception as e:
                    plays_notes.append(f"Failed reading plays file {p.name}: {e}")
    else:
        plays_notes.append(f"Plays directory missing: {plays_dir}")

    plays_missing_weeks = (
        compute_missing_weeks(expected_weeks, plays_present_weeks)
        if expected_weeks
        else []
    )

    plays_audit = DatasetAudit(
        name="plays",
        path=str(plays_dir),
        exists=plays_dir.exists(),
        present_game_ids=0,
        expected_game_ids=len(expected_game_ids),
        missing_game_ids=[],
        present_weeks=sorted(plays_present_weeks),
        expected_weeks=expected_weeks,
        missing_weeks=plays_missing_weeks,
        notes=plays_notes + [f"Found {len(plays_files)} plays CSV files."],
    )

    # Optional online postseason index
    online_postseason: dict[str, Any] = {
        "enabled": include_online,
        "available": False,
        "expected_postseason_games": None,
        "notes": [],
    }
    if include_online:
        data = maybe_get_cfbd_games_postseason_online(season)
        if data is None:
            online_postseason["notes"].append(
                "Postseason online index not available (missing token, client mismatch, or request failed)."
            )
        else:
            online_postseason["available"] = True
            # Attempt to extract gameIds
            gids: set[int] = set()
            for item in data:
                for k in ["id", "gameId", "game_id"]:
                    if k in item:
                        try:
                            gids.add(int(item[k]))
                            break
                        except Exception:
                            continue
            online_postseason["expected_postseason_games"] = len(gids)
            missing_postseason_game_ids = sorted(gids - expected_game_ids)
            online_postseason["missing_from_games_csv"] = missing_postseason_game_ids
            if missing_postseason_game_ids:
                online_postseason["notes"].append(
                    f"games.csv appears to be missing {len(missing_postseason_game_ids)} postseason games."
                )

    audits.append(plays_audit)

    # Manifest
    manifest: dict[str, Any] = {
        "generated_at_utc": utc_now_iso(),
        "season": season,
        "starter_data_dir": str(starter_data_dir),
        "games_csv": {
            "path": str(games_path),
            "game_id_col": games_game_id_col,
            "week_col": games_week_col,
            "expected_game_ids": len(expected_game_ids),
            "expected_weeks": expected_weeks,
        },
        "datasets": [a.__dict__ for a in audits],
        "online_postseason_index": online_postseason,
        "notes": notes,
    }
    return manifest


def write_report(manifest: dict[str, Any], out_path: Path) -> None:
    season = manifest["season"]
    games = manifest["games_csv"]
    datasets = manifest["datasets"]
    online_post = manifest.get("online_postseason_index", {})

    lines: list[str] = []
    lines.append(f"# CFBD Data Audit Report — {season}")
    lines.append("")
    lines.append(f"- Generated (UTC): `{manifest['generated_at_utc']}`")
    lines.append(f"- Starter data dir: `{manifest['starter_data_dir']}`")
    lines.append("")
    lines.append("## Expected Index (from games.csv)")
    lines.append("")
    lines.append(f"- Expected games: **{games['expected_game_ids']}**")
    lines.append(f"- Expected weeks: `{games.get('expected_weeks', [])}`")
    lines.append("")

    lines.append("## Dataset Completeness")
    lines.append("")
    for ds in datasets:
        lines.append(f"### {ds['name']}")
        lines.append("")
        lines.append(f"- Path: `{ds['path']}`")
        lines.append(f"- Exists: **{ds['exists']}**")
        if ds["name"] not in ["plays"]:
            lines.append(
                f"- Game IDs present: **{ds['present_game_ids']} / {ds['expected_game_ids']}**"
            )
            if ds["missing_game_ids"]:
                preview = ds["missing_game_ids"][:20]
                lines.append(f"- Missing gameIds: **{len(ds['missing_game_ids'])}**")
                lines.append(f"  - First 20: `{preview}`")
        lines.append(f"- Weeks present: `{ds.get('present_weeks', [])}`")
        if ds.get("missing_weeks"):
            lines.append(
                f"- Missing weeks: **{len(ds['missing_weeks'])}** → `{ds['missing_weeks']}`"
            )
        if ds.get("notes"):
            lines.append("- Notes:")
            for n in ds["notes"]:
                lines.append(f"  - {n}")
        lines.append("")

    lines.append("## Postseason (online index)")
    lines.append("")
    lines.append(f"- Online enabled: **{bool(online_post.get('enabled'))}**")
    lines.append(f"- Online available: **{bool(online_post.get('available'))}**")
    if online_post.get("available"):
        lines.append(
            f"- Expected postseason games (CFBD): **{online_post.get('expected_postseason_games')}**"
        )
        missing = online_post.get("missing_from_games_csv", [])
        lines.append(f"- Missing from games.csv: **{len(missing)}**")
    if online_post.get("notes"):
        lines.append("- Notes:")
        for n in online_post["notes"]:
            lines.append(f"  - {n}")
    lines.append("")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--season", type=int, default=2025)
    parser.add_argument(
        "--starter-data-dir",
        type=Path,
        default=Path("starter_pack/data"),
    )
    parser.add_argument(
        "--out-manifest",
        type=Path,
        help="Output manifest path (default: data/cfbd/{season}/manifest.json)",
    )
    parser.add_argument(
        "--out-report",
        type=Path,
        help="Output report path (default: reports/data_audit_{season}.md)",
    )
    parser.add_argument(
        "--include-online-postseason",
        action="store_true",
        help="If set, attempts to query CFBD to estimate missing postseason games.",
    )
    args = parser.parse_args()

    # Set defaults based on season
    if args.out_manifest is None:
        args.out_manifest = Path(f"data/cfbd/{args.season}/manifest.json")
    if args.out_report is None:
        args.out_report = Path(f"reports/data_audit_{args.season}.md")

    manifest = audit(
        season=args.season,
        starter_data_dir=args.starter_data_dir,
        include_online=args.include_online_postseason,
    )

    args.out_manifest.parent.mkdir(parents=True, exist_ok=True)
    args.out_manifest.write_text(
        json.dumps(manifest, indent=2, sort_keys=False),
        encoding="utf-8",
    )

    write_report(manifest, args.out_report)
    print(f"✅ Wrote manifest: {args.out_manifest}")
    print(f"✅ Wrote report:   {args.out_report}")


if __name__ == "__main__":
    main()
