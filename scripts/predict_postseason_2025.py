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
import sys
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
from src.observability import (  # noqa: E402
    ObservabilityHub,
    configure_logging,
    get_logger,
)


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


def predict_postseason_2025(
    *, include_incomplete: bool = True, output_format: str = "csv"
) -> Path:
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

    # Feature engineering for XGBoost
    if "home_adjusted_epa" in df.columns and "away_adjusted_epa_allowed" in df.columns:
        df["epa_interaction"] = (
            df["home_adjusted_epa"] * df["away_adjusted_epa_allowed"]
        )
    else:
        df["epa_interaction"] = 0.0

    if "home_elo" in df.columns and "away_elo" in df.columns:
        df["elo_diff"] = df["home_elo"] - df["away_elo"]
    else:
        df["elo_diff"] = 0.0

    if "home_talent" in df.columns and "away_talent" in df.columns:
        df["talent_diff"] = df["home_talent"] - df["away_talent"]
    else:
        df["talent_diff"] = 0.0

    # Ensure robust interaction terms for inference
    for col in ["epa_interaction", "elo_diff", "talent_diff"]:
        if col not in df.columns:
            df[col] = 0.0

    margin_pred = ridge.predict(df[list(RIDGE_FEATURES)].fillna(0))

    # Add engineered features to XGB feature list for prediction
    xgb_inference_features = list(XGB_FEATURES) + [
        "epa_interaction",
        "elo_diff",
        "talent_diff",
    ]
    # Ensure all features exist
    for f in xgb_inference_features:
        if f not in df.columns:
            df[f] = 0.0

    win_prob = xgb.predict_proba(df[xgb_inference_features].fillna(0))[:, 1]

    out = df[
        [
            c
            for c in [
                "id",
                "start_date",
                "season",
                "week",
                "season_type",
                "home_team",
                "away_team",
            ]
            if c in df.columns
        ]
    ].copy()
    out["predicted_margin"] = margin_pred
    out["home_win_prob"] = win_prob

    output_dir = PROJECT_ROOT / "predictions" / "postseason_2025"
    output_dir.mkdir(parents=True, exist_ok=True)

    if output_format == "json":
        # JSON output format for MVP
        output_path = PROJECT_ROOT / "predictions" / "bowls_2025_predictions.json"

        games = []
        for _, row in out.iterrows():
            game = {
                "id": int(row["id"]) if pd.notna(row["id"]) else None,
                "date": (
                    str(row["start_date"])
                    if "start_date" in row and pd.notna(row["start_date"])
                    else None
                ),
                "home_team": (
                    str(row["home_team"]) if pd.notna(row["home_team"]) else None
                ),
                "away_team": (
                    str(row["away_team"]) if pd.notna(row["away_team"]) else None
                ),
                "home_win_prob": (
                    float(row["home_win_prob"])
                    if pd.notna(row["home_win_prob"])
                    else None
                ),
                "predicted_margin": (
                    float(row["predicted_margin"])
                    if pd.notna(row["predicted_margin"])
                    else None
                ),
                "home_talent": (
                    float(row["home_talent"])
                    if "home_talent" in row and pd.notna(row["home_talent"])
                    else None
                ),
                "away_talent": (
                    float(row["away_talent"])
                    if "away_talent" in row and pd.notna(row["away_talent"])
                    else None
                ),
                "home_elo": (
                    float(row["home_elo"])
                    if "home_elo" in row and pd.notna(row["home_elo"])
                    else None
                ),
                "away_elo": (
                    float(row["away_elo"])
                    if "away_elo" in row and pd.notna(row["away_elo"])
                    else None
                ),
                "spread": (
                    float(row["spread"])
                    if "spread" in row and pd.notna(row["spread"])
                    else None
                ),
            }
            games.append(game)

        output_data = {
            "generated_at": datetime.now().isoformat() + "Z",
            "season": 2025,
            "games": games,
        }

        with open(output_path, "w") as f:
            json.dump(output_data, f, indent=2)

        hub.emit_event(
            "predict.success",
            {"rows": int(len(out)), "output": str(output_path), "format": "json"},
        )
        logger.info(
            "Wrote postseason predictions (JSON)",
            extra={"output": str(output_path), "rows": int(len(out))},
        )
    else:
        # CSV output format (default)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = output_dir / f"postseason_predictions_2025_{ts}.csv"
        out.to_csv(output_path, index=False)

        hub.emit_event(
            "predict.success",
            {"rows": int(len(out)), "output": str(output_path), "format": "csv"},
        )
        logger.info(
            "Wrote postseason predictions (CSV)",
            extra={"output": str(output_path), "rows": int(len(out))},
        )

    return output_path


def _parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--postseason-only", action="store_true")
    parser.add_argument(
        "--use-snapshots",
        action="store_true",
        help="Validate that data snapshots exist before running (for offline/deterministic runs)",
    )
    parser.add_argument(
        "--format",
        choices=["csv", "json"],
        default="csv",
        help="Output format: csv (default) or json",
    )
    return parser.parse_args(argv)


def ensure_snapshots_exist(season: int) -> None:
    """
    Validate that required snapshot files exist in data/raw/cfbd/.
    """
    snapshot_dir = PROJECT_ROOT / "data" / "raw" / "cfbd"
    required_files = [
        f"games_regular_{season}.json",
        f"games_postseason_{season}.json",
    ]

    missing = []
    for filename in required_files:
        if not (snapshot_dir / filename).exists():
            missing.append(filename)

    if missing:
        print(f"Error: Snapshots missing ({', '.join(missing)}).")
        print(
            f"Run: python scripts/cfbd_refresh_snapshots.py --season {season} --refresh-all"
        )
        sys.exit(1)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parse_args(argv)

    if args.use_snapshots:
        ensure_snapshots_exist(2025)

    # Check for CFBD_API_KEY if needed (though this script reads from CSV, not API)
    # This is a safeguard per plan requirements
    if not os.getenv("CFBD_API_KEY") and args.format == "json":
        # Note: This script doesn't actually need CFBD_API_KEY since it reads from CSV
        # But we check it as a safeguard per MVP requirements
        print(
            "Warning: CFBD_API_KEY not set (this script reads from CSV, so it may not be needed)"
        )

    predict_postseason_2025(
        include_incomplete=not args.postseason_only, output_format=args.format
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
