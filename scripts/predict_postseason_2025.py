#!/usr/bin/env python3
"""
Generate bowl/postseason projections for 2025 using the latest trained models.

Reads:
  data/training/weekly/training_data_2025_postseason.csv

Writes:
  predictions/postseason_2025/postseason_predictions_2025_<timestamp>.csv

Notes:
- This script does NOT require game outcomes.
- It uses ridge_model_2025.joblib for margin and xgb_home_win_model_2025.pkl for win prob.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Sequence

import joblib
import pandas as pd
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

from model_pack.utils.path_utils import get_postseason_training_file  # noqa: E402
from src.observability import ObservabilityHub, configure_logging, get_logger  # noqa: E402

def _load_feature_lists() -> tuple[list[str], list[str]]:
    """
    Load feature lists from `config/model_config.py` without importing `config.*`.

    Some environments add `src/` to `sys.path`, which can cause `import config`
    to resolve to `src/config` instead of the repo-root `config/` directory.
    """
    import importlib.util

    path = PROJECT_ROOT / "config" / "model_config.py"
    spec = importlib.util.spec_from_file_location("local_model_config", str(path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load feature config from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[assignment]
    return list(module.RIDGE_FEATURES), list(module.XGB_FEATURES)


RIDGE_FEATURES, XGB_FEATURES = _load_feature_lists()


def _ensure_features(df: pd.DataFrame, features: Sequence[str]) -> pd.DataFrame:
    missing = [f for f in features if f not in df.columns]
    if missing:
        for f in missing:
            df[f] = 0
    return df


def get_git_info() -> dict:
    """Get git information for tracking."""
    try:
        git_sha = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT
        ).stdout.strip()

        git_branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT
        ).stdout.strip()

        git_dirty = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT
        ).stdout.strip() != ""

        return {
            "sha": git_sha,
            "branch": git_branch,
            "dirty": git_dirty,
            "short_sha": git_sha[:8] if git_sha else "unknown"
        }
    except Exception:
        return {
            "sha": "unknown",
            "branch": "unknown",
            "dirty": False,
            "short_sha": "unknown"
        }


def backup_file_if_exists(file_path: Path) -> Optional[Path]:
    """Create backup of file if it exists."""
    if file_path.exists():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = file_path.parent / f"{file_path.stem}_backup_{timestamp}{file_path.suffix}"
        shutil.copy2(file_path, backup_path)
        print(f"⚠️ Backed up existing file to: {backup_path}")
        return backup_path
    return None


def analyze_margin_distribution(margins: list) -> dict:
    """Analyze prediction margin distribution."""
    import numpy as np
    margins = [m for m in margins if pd.notna(m)]

    if not margins:
        return {"error": "No valid margins found"}

    margins_array = np.array(margins)
    return {
        "count": len(margins),
        "min": float(np.min(margins_array)),
        "max": float(np.max(margins_array)),
        "mean": float(np.mean(margins_array)),
        "std": float(np.std(margins_array)),
        "range": float(np.max(margins_array) - np.min(margins_array))
    }


def predict_postseason_2025(*, include_incomplete: bool = True, output_format: str = "csv",
                           dry_run: bool = False, timestamp_output: bool = False) -> Path:
    configure_logging(service_name="predict_postseason_2025")
    logger = get_logger(__name__, component="predictions")
    hub = ObservabilityHub.instance()

    model_dir = PROJECT_ROOT / "model_pack"
    ridge = joblib.load(model_dir / "ridge_model_2025.joblib")
    xgb = joblib.load(model_dir / "xgb_home_win_model_2025.pkl")

    postseason_path = get_postseason_training_file(season=2025, base_path=PROJECT_ROOT)
    df = pd.read_csv(postseason_path, low_memory=False).dropna(how="all")
    if not include_incomplete and "season_type" in df.columns:
        df = df[df["season_type"] == "postseason"].copy()

    df = _ensure_features(df, sorted(set(RIDGE_FEATURES) | set(XGB_FEATURES)))

    margin_pred = ridge.predict(df[list(RIDGE_FEATURES)].fillna(0))
    win_prob = xgb.predict_proba(df[list(XGB_FEATURES)].fillna(0))[:, 1]

    out = df[
        [c for c in ["id", "start_date", "season", "week", "season_type", "home_team", "away_team"] if c in df.columns]
    ].copy()
    out["predicted_margin"] = margin_pred
    out["home_win_prob"] = win_prob

    output_dir = PROJECT_ROOT / "predictions" / "postseason_2025"
    output_dir.mkdir(parents=True, exist_ok=True)

    if output_format == "json":
        # JSON output format for MVP - ML specific filename
        base_filename = "bowls_2025_predictions_ml"
        if timestamp_output:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"{base_filename}_{timestamp}.json"
        else:
            output_filename = f"{base_filename}.json"

        output_path = PROJECT_ROOT / "predictions" / output_filename

        # Safety: Check if file exists and warn
        if output_path.exists() and not dry_run:
            response = input(f"⚠️ File {output_path} already exists. Overwrite? (y/N): ")
            if response.lower() != 'y':
                print("❌ Aborted - file would be overwritten")
                return output_path
            backup_file_if_exists(output_path)

        games = []
        for _, row in out.iterrows():
            game = {
                "id": int(row["id"]) if pd.notna(row["id"]) else None,
                "date": str(row["start_date"]) if "start_date" in row and pd.notna(row["start_date"]) else None,
                "home_team": str(row["home_team"]) if pd.notna(row["home_team"]) else None,
                "away_team": str(row["away_team"]) if pd.notna(row["away_team"]) else None,
                "home_win_prob": float(row["home_win_prob"]) if pd.notna(row["home_win_prob"]) else None,
                "predicted_margin": float(row["predicted_margin"]) if pd.notna(row["predicted_margin"]) else None,
            }
            games.append(game)

        # Get model info
        model_dir = PROJECT_ROOT / "model_pack"
        ridge_path = model_dir / "ridge_model_2025.joblib"
        xgb_path = model_dir / "xgb_home_win_model_2025.pkl"

        # Get model version/timestamp from file modification time
        ridge_mtime = datetime.fromtimestamp(ridge_path.stat().st_mtime).isoformat() if ridge_path.exists() else None
        xgb_mtime = datetime.fromtimestamp(xgb_path.stat().st_mtime).isoformat() if xgb_path.exists() else None

        # Get data version info
        data_path = postseason_path
        data_mtime = datetime.fromtimestamp(data_path.stat().st_mtime).isoformat() if data_path.exists() else None

        # Get git info
        git_info = get_git_info()

        # Analyze margins for diagnostics
        margins = out["predicted_margin"].tolist()
        margin_analysis = analyze_margin_distribution(margins)

        # Check margin distribution warning
        if margin_analysis.get("range", 0) < 5.0:
            print(f"⚠️ WARNING: Margin distribution range is only {margin_analysis.get('range', 0):.1f} points (< 5 points)")
            print("   This may indicate conservative predictions or data issues")

        output_data = {
            "generated_at": datetime.now().isoformat() + "Z",
            "season": 2025,
            "model_type": "ml_ensemble",
            "git": git_info,
            "model": {
                "name": "Ridge + XGBoost Ensemble (ML)",
                "ridge_model": "ridge_model_2025.joblib",
                "xgb_model": "xgb_home_win_model_2025.pkl",
                "ridge_version": ridge_mtime,
                "xgb_version": xgb_mtime,
            },
            "data": {
                "source": str(postseason_path.name),
                "version": data_mtime,
                "include_incomplete": include_incomplete
            },
            "diagnostics": {
                "margin_distribution": margin_analysis,
                "total_games": len(games),
                "predictions_generated": datetime.now().isoformat() + "Z"
            },
            "games": games,
        }

        if dry_run:
            print(f"🔍 DRY RUN - Would write {len(games)} predictions to: {output_path}")
            print(f"   Margin range: {margin_analysis.get('range', 0):.1f} points")
            print(f"   Git SHA: {git_info['short_sha']}")
            return output_path

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(output_data, f, indent=2)

        print(f"✅ Generated {len(games)} ML predictions")
        print(f"   Output: {output_path}")
        print(f"   Git: {git_info['short_sha']} ({git_info['branch']})")
        print(f"   Margin range: {margin_analysis.get('range', 0):.1f} points")

        hub.emit_event("predict.success", {"rows": int(len(out)), "output": str(output_path), "format": "json"})
        logger.info("Wrote postseason predictions (JSON)", extra={"output": str(output_path), "rows": int(len(out))})
    else:
        # CSV output format (default)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = output_dir / f"postseason_predictions_2025_{ts}.csv"
        out.to_csv(output_path, index=False)
        
        hub.emit_event("predict.success", {"rows": int(len(out)), "output": str(output_path), "format": "csv"})
        logger.info("Wrote postseason predictions (CSV)", extra={"output": str(output_path), "rows": int(len(out))})
    
    return output_path


def ensure_snapshots_exist(season: int, snapshot_dir: Path) -> None:
    """
    Validate that required snapshots exist.
    
    Args:
        season: Season year
        snapshot_dir: Directory containing snapshots
        
    Raises:
        SystemExit: If snapshots are missing
    """
    required_snapshot = snapshot_dir / f"games_{season}_postseason.json"
    if not required_snapshot.exists():
        error_msg = (
            f"❌ Snapshot not found: {required_snapshot}\n"
            f"   Run: python scripts/cfbd_refresh_snapshots.py --season {season} --refresh-all"
        )
        print(error_msg, file=sys.stderr)
        raise SystemExit(1)
    print(f"✅ Snapshot validated: {required_snapshot}")


def _parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--postseason-only", action="store_true")
    parser.add_argument(
        "--format",
        choices=["csv", "json"],
        default="csv",
        help="Output format: csv (default) or json",
    )
    parser.add_argument(
        "--use-snapshots",
        action="store_true",
        help="Validate that snapshots exist before running predictions. "
             "Ensures data pipeline used snapshots for data preparation.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and show what would be generated without writing files",
    )
    parser.add_argument(
        "--timestamp-output",
        action="store_true",
        help="Add timestamp to output filename to avoid overwriting",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parse_args(argv)

    # Validate snapshots if --use-snapshots is set
    if args.use_snapshots:
        snapshot_dir = PROJECT_ROOT / "data" / "raw" / "cfbd"
        ensure_snapshots_exist(season=2025, snapshot_dir=snapshot_dir)

    # Check for CFBD_API_KEY if needed (though this script reads from CSV, not API)
    # This is a safeguard per plan requirements
    if not os.getenv("CFBD_API_KEY") and args.format == "json":
        # Note: This script doesn't actually need CFBD_API_KEY since it reads from CSV
        # But we check it as a safeguard per MVP requirements
        print("Warning: CFBD_API_KEY not set (this script reads from CSV, so it may not be needed)")

    predict_postseason_2025(
        include_incomplete=not args.postseason_only,
        output_format=args.format,
        dry_run=args.dry_run,
        timestamp_output=args.timestamp_output
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
