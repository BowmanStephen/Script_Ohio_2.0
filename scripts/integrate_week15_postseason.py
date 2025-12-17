#!/usr/bin/env python3
"""
Integrate Week 15 + Postseason Training Data (A+ Standard)

Moves are handled separately; this script assumes the canonical inputs exist:
- data/training/weekly/training_data_2025_week15.csv
- data/training/weekly/training_data_2025_postseason.csv

This script:
- Loads week 15 + postseason CSVs
- Validates schema + required columns against the master training data
- Creates a timestamped backup before writing
- Deduplicates on `id` (keep='last')
- Writes atomically (tmp + replace)
- Emits structured observability events and basic metrics
- Optionally runs ValidationAgent.validate_import_integrity()

Usage:
  python3 scripts/integrate_week15_postseason.py
  python3 scripts/integrate_week15_postseason.py --dry-run
  python3 scripts/integrate_week15_postseason.py --no-rollback
  python3 scripts/integrate_week15_postseason.py --run-validation-agent
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
from typing import Any, Dict, Iterable, Optional, Sequence

import pandas as pd
import requests
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Load local dev environment variables (CFBD_API_KEY, etc.) if present.
load_dotenv(PROJECT_ROOT / ".env")

from model_pack.utils.path_utils import (  # noqa: E402
    find_project_root,
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


@dataclass(frozen=True)
class IntegrationResult:
    """Summary of a successful integration run."""

    master_path: Path
    week15_path: Path
    postseason_path: Path
    backup: Optional[BackupInfo]
    rows_before: int
    rows_week15: int
    rows_postseason: int
    rows_after: int
    duplicates_removed: int
    duration_s: float

    def to_dict(self) -> Dict[str, Any]:
        """Serialize result for logs/event payloads."""
        return {
            "master_path": str(self.master_path),
            "week15_path": str(self.week15_path),
            "postseason_path": str(self.postseason_path),
            "backup_path": str(self.backup.backup_path) if self.backup else None,
            "backup_sha256": self.backup.sha256 if self.backup else None,
            "rows_before": self.rows_before,
            "rows_week15": self.rows_week15,
            "rows_postseason": self.rows_postseason,
            "rows_after": self.rows_after,
            "duplicates_removed": self.duplicates_removed,
            "duration_s": self.duration_s,
        }


def _sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _load_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, low_memory=False)
    return df.dropna(how="all")


def _require_columns(df: pd.DataFrame, required: Sequence[str], *, label: str) -> None:
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"{label} missing required columns: {missing}")


def _validate_schema_equal(dfs: Iterable[pd.DataFrame], labels: Sequence[str]) -> None:
    columns_by_label: Dict[str, set[str]] = {}
    for df, label in zip(dfs, labels, strict=True):
        columns_by_label[label] = set(df.columns.astype(str).tolist())

    baseline_label = labels[0]
    baseline = columns_by_label[baseline_label]
    mismatches: Dict[str, Dict[str, list[str]]] = {}

    for label, cols in columns_by_label.items():
        if label == baseline_label:
            continue
        added = sorted(list(cols - baseline))
        missing = sorted(list(baseline - cols))
        if added or missing:
            mismatches[label] = {"added": added, "missing": missing}

    if mismatches:
        raise ValueError(
            "Schema mismatch against baseline "
            f"({baseline_label}): {mismatches}"
        )


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
        raise RuntimeError(
            "Missing CFBD_API_KEY/CFBD_API_TOKEN and outcomes are required to "
            "integrate these files."
        )

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


def _fill_master_missing_outcomes(
    df: pd.DataFrame,
    *,
    season: int,
    hub: ObservabilityHub,
) -> pd.DataFrame:
    if "id" not in df.columns:
        return df
    if not all(col in df.columns for col in OUTCOME_COLUMNS):
        return df

    updated = df.copy()
    missing_mask = (
        (updated["season"] == season)
        & (updated["home_points"].isna() | updated["away_points"].isna())
        & updated["id"].notna()
    )
    if not missing_mask.any():
        return updated

    ids = updated.loc[missing_mask, "id"].astype(int).tolist()
    score_map = _fetch_scores_cfbd(ids, season=season)

    filled = 0
    for idx, game_id in updated.loc[missing_mask, "id"].astype(int).items():
        scores = score_map.get(int(game_id))
        if not scores:
            continue
        updated.at[idx, "home_points"] = scores.get("home_points")
        updated.at[idx, "away_points"] = scores.get("away_points")
        if scores.get("home_points") is not None and scores.get("away_points") is not None:
            filled += 1

    updated["margin"] = updated["home_points"] - updated["away_points"]
    hub.emit_event(
        "integration.master_outcomes_filled",
        {
            "season": season,
            "attempted": len(ids),
            "filled": filled,
            "still_missing_points": int(
                (updated["home_points"].isna() | updated["away_points"].isna()).sum()
            ),
        },
        severity=ErrorSeverity.INFO.value,
    )
    return updated


def _create_backup(master_path: Path, backup_dir: Path) -> BackupInfo:
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"updated_training_data_backup_{timestamp}.csv"
    shutil.copy2(master_path, backup_path)
    return BackupInfo(
        backup_path=backup_path,
        sha256=_sha256_file(backup_path),
        created_at=datetime.now().isoformat(),
    )


def _atomic_write_csv(df: pd.DataFrame, dest_path: Path) -> None:
    tmp_path = dest_path.with_suffix(dest_path.suffix + ".tmp")
    df.to_csv(tmp_path, index=False)
    os.replace(tmp_path, dest_path)


def _dedupe_by_id(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    if "id" not in df.columns:
        return df, 0
    before = len(df)
    deduped = df.drop_duplicates(subset=["id"], keep="last")
    return deduped, before - len(deduped)


def integrate_week15_postseason(
    *,
    project_root: Optional[Path] = None,
    season: int = 2025,
    week: int = 15,
    dry_run: bool = False,
    rollback_on_failure: bool = True,
    run_validation_agent: bool = False,
    allow_incomplete_new_rows: bool = False,
    backup_dir: Optional[Path] = None,
) -> IntegrationResult:
    """
    Integrate week 15 + postseason training data into the master dataset.

    Args:
        project_root: Project root override (defaults to auto-detect).
        season: Season year (default: 2025).
        week: Regular season week to integrate (default: 15).
        dry_run: If True, perform all validations but do not write master file.
        rollback_on_failure: If True, restore from backup if a write fails.
        run_validation_agent: If True, run ValidationAgent import integrity check.
        backup_dir: Where to store backups (default: model_pack/backups).

    Returns:
        IntegrationResult describing the completed integration.
    """
    configure_logging(service_name="integrate_week15_postseason")
    logger = get_logger(__name__, component="data_integration")
    hub = ObservabilityHub.instance()

    project_root = project_root or find_project_root(PROJECT_ROOT)
    master_path = get_master_training_data_path(project_root)
    week15_path = get_weekly_training_file(week=week, season=season, base_path=project_root)
    postseason_path = get_postseason_training_file(season=season, base_path=project_root)
    backup_dir = backup_dir or (project_root / "model_pack" / "backups")

    start = time.monotonic()
    hub.emit_event(
        "integration.start",
        {
            "season": season,
            "week": week,
            "dry_run": dry_run,
            "rollback_on_failure": rollback_on_failure,
            "master_path": str(master_path),
            "week15_path": str(week15_path),
            "postseason_path": str(postseason_path),
        },
    )

    backup: Optional[BackupInfo] = None
    try:
        master_df = _load_csv(master_path)
        week15_df = _load_csv(week15_path)
        postseason_df = _load_csv(postseason_path)

        hub.emit_event(
            "integration.files_loaded",
            {
                "rows_master": len(master_df),
                "rows_week15": len(week15_df),
                "rows_postseason": len(postseason_df),
                "cols_master": len(master_df.columns),
                "cols_week15": len(week15_df.columns),
                "cols_postseason": len(postseason_df.columns),
            },
        )

        for df, label in (
            (master_df, "master"),
            (week15_df, "week15"),
            (postseason_df, "postseason"),
        ):
            _require_columns(df, REQUIRED_COLUMNS, label=label)

        allowed_missing = set(OUTCOME_COLUMNS)
        week15_df = _align_to_master_schema(
            week15_df,
            master_columns=master_df.columns.tolist(),
            label="week15",
            allowed_missing=allowed_missing,
        )
        postseason_df = _align_to_master_schema(
            postseason_df,
            master_columns=master_df.columns.tolist(),
            label="postseason",
            allowed_missing=allowed_missing,
        )

        require_outcomes = all(col in master_df.columns for col in OUTCOME_COLUMNS)
        if require_outcomes:
            master_df = _fill_master_missing_outcomes(master_df, season=season, hub=hub)
        week15_df = _ensure_outcomes(
            week15_df,
            label="week15",
            season=season,
            hub=hub,
            require_outcomes=require_outcomes,
        )
        postseason_df = _ensure_outcomes(
            postseason_df,
            label="postseason",
            season=season,
            hub=hub,
            require_outcomes=require_outcomes,
        )
        if require_outcomes and not allow_incomplete_new_rows:
            before_rows = len(postseason_df)
            postseason_df = postseason_df.dropna(subset=["home_points", "away_points"])
            skipped = before_rows - len(postseason_df)
            if skipped:
                hub.emit_event(
                    "integration.incomplete_rows_skipped",
                    {"label": "postseason", "skipped": skipped, "kept": len(postseason_df)},
                    severity=ErrorSeverity.WARNING.value,
                )

        _validate_schema_equal(
            (master_df, week15_df, postseason_df),
            ("master", "week15", "postseason"),
        )

        combined = pd.concat([master_df, week15_df, postseason_df], ignore_index=True)
        combined, duplicates_removed = _dedupe_by_id(combined)

        if "id" in combined.columns and combined["id"].duplicated().any():
            raise ValueError("Duplicate game IDs remain after deduplication.")

        null_required = {col: int(combined[col].isna().sum()) for col in REQUIRED_COLUMNS}
        if any(count > 0 for count in null_required.values()):
            raise ValueError(f"Nulls present in required columns: {null_required}")

        new_ids = set(week15_df["id"].dropna().astype(int).tolist()) | set(
            postseason_df["id"].dropna().astype(int).tolist()
        )
        if require_outcomes:
            new_rows = combined[combined["id"].astype(int).isin(new_ids)]
            null_new_outcomes = {col: int(new_rows[col].isna().sum()) for col in OUTCOME_COLUMNS}
            if any(count > 0 for count in null_new_outcomes.values()):
                raise ValueError(
                    "Missing outcomes in newly integrated rows: "
                    f"{null_new_outcomes}"
                )

        hub.emit_event(
            "integration.validation_passed",
            {
                "rows_after": len(combined),
                "duplicates_removed": duplicates_removed,
                "null_required_counts": null_required,
            },
        )

        if not dry_run:
            backup = _create_backup(master_path, backup_dir)
            hub.emit_event(
                "integration.backup_created",
                {
                    "backup_path": str(backup.backup_path),
                    "backup_sha256": backup.sha256,
                },
            )
            _atomic_write_csv(combined, master_path)
            hub.emit_event("integration.master_written", {"master_path": str(master_path)})

        if run_validation_agent:
            from agents.validation_agent import ValidationAgent  # noqa: WPS433

            agent = ValidationAgent("validation_agent")
            result = agent._execute_action("validate_import_integrity", {}, {})
            hub.emit_event("integration.validation_agent", {"result": result})

        duration_s = time.monotonic() - start
        hub.set_metric("integration.duration_s", duration_s)
        hub.set_metric("integration.rows_after", len(combined))
        hub.set_metric("integration.duplicates_removed", duplicates_removed)

        result = IntegrationResult(
            master_path=master_path,
            week15_path=week15_path,
            postseason_path=postseason_path,
            backup=backup,
            rows_before=len(master_df),
            rows_week15=len(week15_df),
            rows_postseason=len(postseason_df),
            rows_after=len(combined),
            duplicates_removed=duplicates_removed,
            duration_s=duration_s,
        )
        hub.emit_event("integration.success", result.to_dict())
        logger.info("Integration complete", extra={"integration": result.to_dict()})
        return result
    except Exception as exc:
        duration_s = time.monotonic() - start
        category = ErrorCategory.DATA
        if "CFBD_API_KEY" in str(exc):
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
                "week": week,
                "dry_run": dry_run,
                "rollback_on_failure": rollback_on_failure,
                "master_path": str(master_path),
                "week15_path": str(week15_path),
                "postseason_path": str(postseason_path),
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


def _parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--season", type=int, default=2025)
    parser.add_argument("--week", type=int, default=15)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-rollback", action="store_true")
    parser.add_argument("--run-validation-agent", action="store_true")
    parser.add_argument("--allow-incomplete-new-rows", action="store_true")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parse_args(argv)
    integrate_week15_postseason(
        season=args.season,
        week=args.week,
        dry_run=args.dry_run,
        rollback_on_failure=not args.no_rollback,
        run_validation_agent=args.run_validation_agent,
        allow_incomplete_new_rows=args.allow_incomplete_new_rows,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
