#!/usr/bin/env python3
"""Integrate weekly/postseason training CSVs into the master dataset.

This script is the general-purpose counterpart to
`scripts/integrate_week15_postseason.py`.

It:
1) Loads `model_pack/updated_training_data.csv`
2) Loads selected weekly files from `data/training/weekly/`
3) Optionally loads the postseason file
4) Aligns schemas to the master dataset
5) Deduplicates on `id` (keep='last')
6) Writes atomically and creates timestamped backups
7) Optionally fills missing outcomes via CFBD `/games` (requires API key)
8) Optionally runs the ValidationAgent integrity check

Inputs are discovered via `model_pack.utils.path_utils` so legacy paths still work.

Usage:
  # Integrate week 15 + postseason for 2025
  python3 scripts/integrate_weekly_files.py --season 2025 --weeks 15 --include-postseason

  # Integrate multiple weeks
  python3 scripts/integrate_weekly_files.py --season 2025 --weeks 14,15

  # Include incomplete rows (e.g., scheduled postseason games)
  python3 scripts/integrate_weekly_files.py --season 2025 --weeks 15 --include-postseason \\
    --allow-incomplete-new-rows
"""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import sys
import time
import traceback
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Sequence

import pandas as pd
import requests
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

from model_pack.utils.path_utils import (  # noqa: E402
    get_master_training_data_path,
    get_postseason_training_file,
    get_weekly_training_file,
)
from src.observability import (  # noqa: E402
    ErrorCategory,
    ErrorReport,
    ErrorSeverity,
    ObservabilityHub,
    configure_logging,
    get_logger,
)

REQUIRED_COLUMNS: tuple[str, ...] = (
    "id",
    "season",
    "week",
    "season_type",
    "home_team",
    "away_team",
)

OUTCOME_COLUMNS: tuple[str, ...] = ("home_points", "away_points", "margin")


@dataclass(frozen=True)
class BackupInfo:
    """Metadata about a created backup file."""

    backup_path: Path
    sha256: str
    created_at: str


def _sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _atomic_write_csv(df: pd.DataFrame, path: Path) -> None:
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    df.to_csv(tmp_path, index=False)
    tmp_path.replace(path)


def _create_backup(master_path: Path, backup_dir: Path) -> BackupInfo:
    backup_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"updated_training_data_backup_{ts}.csv"
    shutil.copy2(master_path, backup_path)
    return BackupInfo(
        backup_path=backup_path,
        sha256=_sha256_file(backup_path),
        created_at=datetime.now().isoformat(),
    )


def _load_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, low_memory=False)
    return df.dropna(how="all")


def _require_columns(df: pd.DataFrame, required: Sequence[str], *, label: str) -> None:
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"{label} missing required columns: {missing}")


def _align_to_master_schema(
    df: pd.DataFrame,
    *,
    master_columns: Sequence[str],
    label: str,
    allowed_missing: set[str],
) -> pd.DataFrame:
    master_set = set(master_columns)
    df_set = set(df.columns.astype(str).tolist())

    missing = master_set - df_set
    extra = df_set - master_set

    disallowed_missing = sorted([col for col in missing if col not in allowed_missing])
    if disallowed_missing:
        raise ValueError(f"{label} missing columns not allowed: {disallowed_missing}")
    if extra:
        raise ValueError(f"{label} has unexpected extra columns: {sorted(list(extra))}")

    aligned = df.copy()
    for col in missing:
        aligned[col] = pd.NA
    return aligned.loc[:, list(master_columns)]


def _fetch_scores_cfbd(game_ids: Sequence[int], *, season: int) -> Dict[int, Dict[str, Any]]:
    api_key = os.getenv("CFBD_API_KEY") or os.getenv("CFBD_API_TOKEN")
    if not api_key:
        raise RuntimeError("Missing CFBD_API_KEY/CFBD_API_TOKEN and outcomes are required.")

    headers = {"Authorization": f"Bearer {api_key}", "Accept": "application/json"}
    url = "https://api.collegefootballdata.com/games"
    response = requests.get(url, headers=headers, params={"year": season}, timeout=60)
    response.raise_for_status()
    games = response.json()

    lookup: Dict[int, Dict[str, Any]] = {}
    wanted = set(int(x) for x in game_ids)
    for game in games:
        game_id = game.get("id")
        if game_id in wanted:
            home_points = game.get("homePoints", game.get("home_points"))
            away_points = game.get("awayPoints", game.get("away_points"))
            lookup[int(game_id)] = {
                "home_points": home_points,
                "away_points": away_points,
            }
    return lookup


def _ensure_outcomes(
    df: pd.DataFrame,
    *,
    label: str,
    season: int,
    hub: ObservabilityHub,
    require_outcomes: bool,
) -> pd.DataFrame:
    if not require_outcomes or "id" not in df.columns:
        return df

    updated = df.copy()
    for col in OUTCOME_COLUMNS:
        if col not in updated.columns:
            updated[col] = pd.NA

    ids_needing = updated.loc[
        updated["home_points"].isna() | updated["away_points"].isna(), "id"
    ].dropna()

    if ids_needing.empty:
        return updated

    score_map = _fetch_scores_cfbd(ids_needing.astype(int).tolist(), season=season)
    filled = 0
    missing = 0
    for idx, game_id in ids_needing.astype(int).items():
        scores = score_map.get(int(game_id))
        if not scores:
            missing += 1
            continue
        updated.at[idx, "home_points"] = scores.get("home_points")
        updated.at[idx, "away_points"] = scores.get("away_points")
        if scores.get("home_points") is not None and scores.get("away_points") is not None:
            filled += 1

    updated["margin"] = updated["home_points"] - updated["away_points"]
    hub.emit_event(
        "integration.outcomes_filled",
        {
            "label": label,
            "filled": filled,
            "missing_ids": missing,
            "still_missing_points": int(
                (updated["home_points"].isna() | updated["away_points"].isna()).sum()
            ),
        },
        severity=ErrorSeverity.INFO.value,
    )
    return updated


def _parse_weeks(value: str) -> list[int]:
    weeks: set[int] = set()
    for part in value.split(","):
        token = part.strip()
        if not token:
            continue
        if "-" in token:
            start_str, end_str = token.split("-", 1)
            start = int(start_str)
            end = int(end_str)
            if start > end:
                start, end = end, start
            for wk in range(start, end + 1):
                weeks.add(int(wk))
        else:
            weeks.add(int(token))
    return sorted(weeks)


def _parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--season", type=int, default=2025)
    parser.add_argument(
        "--weeks",
        type=str,
        required=True,
        help="Comma-separated weeks and/or ranges, e.g. '14,15' or '1-15'.",
    )
    parser.add_argument("--include-postseason", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-rollback", action="store_true")
    parser.add_argument("--run-validation-agent", action="store_true")
    parser.add_argument("--allow-incomplete-new-rows", action="store_true")
    return parser.parse_args(argv)


def integrate_weekly_files(
    *,
    season: int,
    weeks: Sequence[int],
    include_postseason: bool,
    dry_run: bool,
    rollback_on_failure: bool,
    run_validation_agent: bool,
    allow_incomplete_new_rows: bool,
) -> None:
    """Integrate selected weekly/postseason files into the master dataset.

    Args:
        season: Season year.
        weeks: Regular-season weeks to integrate.
        include_postseason: Whether to also integrate postseason file.
        dry_run: Whether to avoid writing the master dataset.
        rollback_on_failure: Whether to restore from backup if integration fails.
        run_validation_agent: Run ValidationAgent.validate_import_integrity after write.
        allow_incomplete_new_rows: Allow rows with missing outcomes to be kept.
    """
    configure_logging(service_name="integrate_weekly_files")
    logger = get_logger(__name__, component="data_integration")
    hub = ObservabilityHub.instance()

    start = time.monotonic()
    master_path = get_master_training_data_path(base_path=PROJECT_ROOT)
    backup_dir = PROJECT_ROOT / "model_pack" / "backups"

    backup: Optional[BackupInfo] = None
    try:
        master_df = _load_csv(master_path)
        _require_columns(master_df, REQUIRED_COLUMNS, label="master")
        master_columns = master_df.columns.astype(str).tolist()

        inputs: list[tuple[str, Path]] = []
        for wk in weeks:
            inputs.append(
                (f"week{int(wk):02d}", get_weekly_training_file(week=int(wk), season=season))
            )
        if include_postseason:
            inputs.append(("postseason", get_postseason_training_file(season=season)))

        allowed_missing = set(OUTCOME_COLUMNS)
        require_outcomes = not allow_incomplete_new_rows

        aligned: list[pd.DataFrame] = []
        for label, path in inputs:
            df = _load_csv(path)
            _require_columns(df, REQUIRED_COLUMNS, label=label)
            df = _ensure_outcomes(
                df, label=label, season=season, hub=hub, require_outcomes=require_outcomes
            )
            df = _align_to_master_schema(
                df,
                master_columns=master_columns,
                label=label,
                allowed_missing=allowed_missing,
            )
            aligned.append(df)

        combined = pd.concat([master_df, *aligned], ignore_index=True)
        rows_before = len(combined)
        combined = combined.drop_duplicates(subset=["id"], keep="last")
        duplicates_removed = rows_before - len(combined)

        if require_outcomes:
            combined = combined.dropna(subset=["home_points", "away_points"], how="any")

        combined = combined.sort_values(["season", "week"]).reset_index(drop=True)

        hub.emit_event(
            "integration.preview",
            {
                "master_path": str(master_path),
                "season": season,
                "weeks": list(int(x) for x in weeks),
                "include_postseason": include_postseason,
                "rows_master": int(len(master_df)),
                "rows_after": int(len(combined)),
                "duplicates_removed": int(duplicates_removed),
                "dry_run": dry_run,
            },
            severity=ErrorSeverity.INFO.value,
        )

        if not dry_run:
            backup = _create_backup(master_path, backup_dir)
            hub.emit_event(
                "integration.backup_created",
                {
                    "backup_path": str(backup.backup_path),
                    "backup_sha256": backup.sha256,
                },
                severity=ErrorSeverity.INFO.value,
            )
            _atomic_write_csv(combined, master_path)
            hub.emit_event(
                "integration.master_written",
                {"master_path": str(master_path)},
                severity=ErrorSeverity.INFO.value,
            )

        if run_validation_agent:
            from agents.validation_agent import ValidationAgent  # noqa: WPS433

            agent = ValidationAgent("validation_agent")
            result = agent._execute_action("validate_import_integrity", {}, {})
            hub.emit_event("integration.validation_agent", {"result": result})

        duration_s = time.monotonic() - start
        hub.set_metric("integration.duration_s", duration_s)
        logger.info(
            "Integration complete",
            extra={
                "master_path": str(master_path),
                "duration_s": duration_s,
                "dry_run": dry_run,
                "duplicates_removed": duplicates_removed,
            },
        )
    except Exception as exc:
        duration_s = time.monotonic() - start
        category = ErrorCategory.DATA
        if "CFBD_API_KEY" in str(exc) or "CFBD_API_TOKEN" in str(exc):
            category = ErrorCategory.CONFIGURATION
        elif isinstance(exc, requests.HTTPError):
            category = ErrorCategory.EXTERNAL_API

        error_report = ErrorReport(
            error_type=type(exc).__name__,
            error_message=str(exc),
            category=category,
            severity=ErrorSeverity.HIGH,
            context={
                "season": season,
                "weeks": list(int(x) for x in weeks),
                "include_postseason": include_postseason,
                "dry_run": dry_run,
                "rollback_on_failure": rollback_on_failure,
                "master_path": str(master_path),
                "duration_s": duration_s,
            },
            stack_trace=traceback.format_exc(),
            recovery_attempted=bool(backup) and rollback_on_failure,
        )

        if backup and rollback_on_failure and not dry_run:
            try:
                shutil.copy2(backup.backup_path, master_path)
                error_report.recovery_successful = True
                hub.emit_event(
                    "integration.rollback_success",
                    {
                        "restored_from": str(backup.backup_path),
                        "master_path": str(master_path),
                    },
                    severity=ErrorSeverity.WARNING.value,
                )
            except Exception as rollback_exc:
                hub.emit_event(
                    "integration.rollback_failed",
                    {"error": str(rollback_exc)},
                    severity=ErrorSeverity.CRITICAL.value,
                )

        hub.emit_error(error_report)
        raise


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parse_args(argv)
    integrate_weekly_files(
        season=int(args.season),
        weeks=_parse_weeks(str(args.weeks)),
        include_postseason=bool(args.include_postseason),
        dry_run=bool(args.dry_run),
        rollback_on_failure=not bool(args.no_rollback),
        run_validation_agent=bool(args.run_validation_agent),
        allow_incomplete_new_rows=bool(args.allow_incomplete_new_rows),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

