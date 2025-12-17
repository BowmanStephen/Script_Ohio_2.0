#!/usr/bin/env python3
"""
Rollback master training data to a previous backup.

By default this restores `model_pack/updated_training_data.csv` from the most
recent backup found in `model_pack/backups/` (preferred) or `model_pack/`.

Usage:
  python3 scripts/rollback_integration.py
  python3 scripts/rollback_integration.py --backup model_pack/backups/updated_training_data_backup_YYYYMMDD_HHMMSS.csv
"""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import sys
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from model_pack.utils.path_utils import (  # noqa: E402
    find_project_root,
    get_master_training_data_path,
)
from src.observability import (  # noqa: E402
    ErrorCategory,
    ErrorReport,
    ErrorSeverity,
    ObservabilityHub,
    configure_logging,
    get_logger,
)


@dataclass(frozen=True)
class RollbackResult:
    master_path: Path
    backup_path: Path
    backup_sha256: str
    restored_master_sha256: str


def _sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _find_latest_backup(project_root: Path) -> Path:
    backups_dir = project_root / "model_pack" / "backups"
    candidates = []

    if backups_dir.exists():
        candidates.extend(backups_dir.glob("updated_training_data_backup_*.csv"))
    candidates.extend(
        (project_root / "model_pack").glob("updated_training_data.csv.backup_*")
    )

    if not candidates:
        raise FileNotFoundError("No backups found for updated_training_data.csv")

    return max(candidates, key=lambda p: p.stat().st_mtime)


def rollback_master_training_data(
    *, project_root: Optional[Path] = None, backup_path: Optional[Path] = None
) -> RollbackResult:
    """
    Restore the master training data from a backup.

    Args:
        project_root: Project root override (defaults to auto-detect).
        backup_path: Explicit backup file to restore from (defaults to latest).

    Returns:
        RollbackResult containing paths and checksum.
    """
    configure_logging(service_name="rollback_integration")
    logger = get_logger(__name__, component="data_integration")
    hub = ObservabilityHub.instance()

    project_root = project_root or find_project_root(PROJECT_ROOT)
    master_path = get_master_training_data_path(project_root)
    backup_path = backup_path or _find_latest_backup(project_root)

    hub.emit_event(
        "rollback.start",
        {"master_path": str(master_path), "backup_path": str(backup_path)},
        severity=ErrorSeverity.WARNING.value,
    )

    if not backup_path.exists():
        raise FileNotFoundError(f"Backup file not found: {backup_path}")

    backup_sha256 = _sha256_file(backup_path)
    tmp_path = master_path.with_suffix(master_path.suffix + ".rollback_tmp")
    shutil.copy2(backup_path, tmp_path)
    os.replace(tmp_path, master_path)
    restored_sha256 = _sha256_file(master_path)

    result = RollbackResult(
        master_path=master_path,
        backup_path=backup_path,
        backup_sha256=backup_sha256,
        restored_master_sha256=restored_sha256,
    )
    hub.emit_event(
        "rollback.success",
        {"master_path": str(master_path), "backup_path": str(backup_path)},
        severity=ErrorSeverity.WARNING.value,
    )
    logger.warning("Rollback completed", extra={"rollback": result})
    return result


def _parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backup", type=str, default=None)
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parse_args(argv)
    backup_path = Path(args.backup) if args.backup else None
    try:
        rollback_master_training_data(backup_path=backup_path)
        return 0
    except Exception as exc:
        hub = ObservabilityHub.instance()
        hub.emit_error(
            ErrorReport(
                error_type=type(exc).__name__,
                error_message=str(exc),
                category=ErrorCategory.IO,
                severity=ErrorSeverity.HIGH,
                context={"backup": str(backup_path) if backup_path else None},
                stack_trace=traceback.format_exc(),
            )
        )
        raise


if __name__ == "__main__":
    raise SystemExit(main())
