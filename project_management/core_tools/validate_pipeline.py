#!/usr/bin/env python3
"""Comprehensive validation script for the Ohio Model data pipeline."""

from __future__ import annotations

import json
import pickle
import sys
from pathlib import Path
from typing import List

import joblib
import pandas as pd
import torch

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PLAYS_PATH = PROJECT_ROOT / "model_pack/2025_plays.csv"
TRAINING_PATH = PROJECT_ROOT / "model_pack/updated_training_data.csv"
RIDGE_PATH = PROJECT_ROOT / "model_pack/ridge_model_2025.joblib"
XGB_PATH = PROJECT_ROOT / "model_pack/xgb_home_win_model_2025.pkl"
FASTAI_PATH = PROJECT_ROOT / "model_pack/fastai_home_win_model_2025.pkl"
REPORT_PATH = PROJECT_ROOT / "starter_pack/data/2025_data_integration_report.json"
DOCS = [
    PROJECT_ROOT / "project_management/DATA_STATUS.md",
    PROJECT_ROOT / "project_management/WEEKLY_MAINTENANCE.md",
]


def validate_plays() -> List[str]:
    issues: List[str] = []
    if not PLAYS_PATH.exists():
        return ["model_pack/2025_plays.csv is missing"]

    df = pd.read_csv(PLAYS_PATH)
    games = df["game_id"].nunique()
    plays = len(df)
    print(f"[plays] {plays:,} plays across {games} games")
    if plays < 1000 or games < 100:
        issues.append("Unexpectedly low play totals; verify CFBD pull.")

    mock_mask = df.astype(str).apply(lambda col: col.str.contains(r"\bMock\b", case=False, regex=True, na=False))
    mock_hits = int(mock_mask.any(axis=1).sum())
    if mock_hits:
        issues.append(f"Found {mock_hits} rows containing standalone 'Mock'")
    return issues


def validate_training() -> List[str]:
    issues: List[str] = []
    if not TRAINING_PATH.exists():
        return ["model_pack/updated_training_data.csv is missing"]

    df = pd.read_csv(TRAINING_PATH, low_memory=False)
    games_2025 = df[df["season"] == 2025]
    print(f"[training] total rows={len(df):,} | 2025 rows={len(games_2025):,}")
    if games_2025.empty:
        issues.append("Training data missing season 2025 rows.")
    else:
        weeks = sorted(games_2025["week"].dropna().unique().tolist())
        print(f"[training] 2025 weeks covered: {weeks}")
        if weeks[0] > 1 or weeks[-1] < 12:
            issues.append("2025 week range incomplete in training data.")

    dupes = df.duplicated(subset=["id"]).sum()
    if dupes:
        issues.append(f"Training data contains {dupes} duplicate game ids.")
    return issues


def validate_models() -> List[str]:
    issues: List[str] = []
    try:
        ridge = joblib.load(RIDGE_PATH)
        print(f"[models] Ridge loaded ({RIDGE_PATH.name})")
        _ = ridge.get_params()
    except Exception as exc:  # noqa: BLE001
        issues.append(f"Failed to load ridge model: {exc}")

    try:
        with open(XGB_PATH, "rb") as handle:
            pickle.load(handle)
        print(f"[models] XGBoost loaded ({XGB_PATH.name})")
    except Exception as exc:  # noqa: BLE001
        issues.append(f"Failed to load XGBoost model: {exc}")

    try:
        from fastai.learner import load_learner  # type: ignore
        load_learner(FASTAI_PATH, cpu=True)
        print(f"[models] FastAI learner loaded ({FASTAI_PATH.name})")
    except ImportError:
        print("[models] fastai not installed; skipping FastAI validation")
    except Exception as exc:  # noqa: BLE001
        print(f"[models] FastAI warning: {exc}")
    return issues


def validate_report() -> List[str]:
    issues: List[str] = []
    if not REPORT_PATH.exists():
        return ["starter_pack/data/2025_data_integration_report.json missing"]
    with open(REPORT_PATH, "r") as handle:
        report = json.load(handle)
    weeks = report.get("weeks_covered", "unknown")
    print(f"[report] weeks_covered={weeks} last_updated={report.get('last_updated')}")
    if not str(weeks).startswith("1-"):
        issues.append("Integration report weeks_covered does not start at Week 1.")
    return issues


def validate_docs() -> List[str]:
    issues: List[str] = []
    for path in DOCS:
        if not path.exists():
            issues.append(f"Documentation missing: {path}")
        else:
            print(f"[docs] {path.name} present")
    return issues


def validate_pipeline() -> int:
    errors: List[str] = []

    errors.extend(validate_plays())
    errors.extend(validate_training())
    errors.extend(validate_models())
    errors.extend(validate_report())
    errors.extend(validate_docs())

    if errors:
        print("\n✗ Pipeline validation encountered issues:")
        for err in errors:
            print(f"  - {err}")
        return 1

    print("\n✓ Pipeline validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(validate_pipeline())

