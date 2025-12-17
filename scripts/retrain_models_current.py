#!/usr/bin/env python3
"""
Retrain production models using the latest scored training data.

This script retrains:
- Ridge regression margin model (saved to model_pack/ridge_model_2025.joblib)
- XGBoost home win classifier (saved to model_pack/xgb_home_win_model_2025.pkl)
- FastAI home win model (saved to model_pack/fastai_home_win_model_2025.pkl) if available

Key behavior:
- Trains on *all* rows with outcomes (home_points/away_points present), including 2025.
- Creates timestamped backups of existing model files before overwriting.
- Uses feature lists from project_management/TOOLS_AND_CONFIG/model_features.py.

Usage:
  python3 scripts/retrain_models_current.py
  python3 scripts/retrain_models_current.py --skip-fastai
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Sequence

import joblib
import numpy as np
import pandas as pd
import xgboost as xgb
from dotenv import load_dotenv
from sklearn.linear_model import Ridge
from sklearn.metrics import accuracy_score, mean_absolute_error, roc_auc_score
from sklearn.model_selection import GridSearchCV, TimeSeriesSplit

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

from src.observability import (  # noqa: E402
    ErrorCategory,
    ErrorReport,
    ErrorSeverity,
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

try:
    from fastai.tabular.all import Categorify, FillMissing, Normalize, TabularDataLoaders, tabular_learner, accuracy  # type: ignore
    from fastai.metrics import RocAucBinary  # type: ignore

    FASTAI_AVAILABLE = True
except ImportError:
    FASTAI_AVAILABLE = False


@dataclass(frozen=True)
class ModelPaths:
    ridge_path: Path
    xgb_path: Path
    fastai_path: Path


def _load_training_data(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, low_memory=False).dropna(how="all")
    df = df.sort_values(["season", "week"]).reset_index(drop=True)
    # Keep only scored games (exclude future rows).
    return df[(df["home_points"].notna()) & (df["away_points"].notna())].copy()


def _ensure_features(df: pd.DataFrame, features: Sequence[str]) -> pd.DataFrame:
    missing = [f for f in features if f not in df.columns]
    if missing:
        for f in missing:
            df[f] = 0
    return df


def _backup_file(path: Path, backup_dir: Path) -> Optional[Path]:
    if not path.exists():
        return None
    backup_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"{path.name}.backup_{ts}"
    shutil.copy2(path, backup_path)
    return backup_path


def _train_ridge(df: pd.DataFrame, output_path: Path) -> Dict[str, Any]:
    df = _ensure_features(df, RIDGE_FEATURES)
    X = df[list(RIDGE_FEATURES)].fillna(0)
    y = (df["home_points"] - df["away_points"]).astype(float)

    tscv = TimeSeriesSplit(n_splits=5)
    grid = GridSearchCV(
        Ridge(),
        {"alpha": [0.01, 0.1, 1.0, 10.0, 100.0]},
        cv=tscv,
        scoring="neg_mean_absolute_error",
        n_jobs=-1,
    )
    grid.fit(X, y)
    model: Ridge = grid.best_estimator_

    # Simple in-sample diagnostics
    preds = model.predict(X)
    mae = float(mean_absolute_error(y, preds))

    joblib.dump(model, output_path)
    return {"alpha": float(model.alpha), "mae_in_sample": mae}


def _train_xgb(df: pd.DataFrame, output_path: Path) -> Dict[str, Any]:
    df = _ensure_features(df, XGB_FEATURES)
    X = df[list(XGB_FEATURES)].fillna(0)
    y = (df["home_points"] > df["away_points"]).astype(int)

    model = xgb.XGBClassifier(
        eval_metric="logloss",
        random_state=77,
        n_estimators=300,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.9,
        colsample_bytree=0.9,
    )
    model.fit(X, y)

    proba = model.predict_proba(X)[:, 1]
    pred = (proba >= 0.5).astype(int)
    acc = float(accuracy_score(y, pred))
    try:
        auc = float(roc_auc_score(y, proba))
    except ValueError:
        auc = 0.5

    joblib.dump(model, output_path)
    return {"accuracy_in_sample": acc, "auc_in_sample": auc}


def _train_fastai(df: pd.DataFrame, output_path: Path) -> Dict[str, Any]:
    if not FASTAI_AVAILABLE:
        raise RuntimeError("FastAI not available (install fastai to enable).")

    cont_names = sorted(list(set(RIDGE_FEATURES + XGB_FEATURES)))
    cat_names = ["week", "home_conference", "away_conference", "neutral_site"]

    df = df.copy()
    df = _ensure_features(df, cont_names)
    for col in cat_names:
        if col not in df.columns:
            df[col] = "Unknown"

    df["home_win"] = (df["home_points"] > df["away_points"]).astype(int)
    splits = (list(range(int(len(df) * 0.9))), list(range(int(len(df) * 0.9), len(df))))
    dls = TabularDataLoaders.from_df(
        df,
        procs=[Categorify, FillMissing, Normalize],
        cat_names=cat_names,
        cont_names=cont_names,
        y_names="home_win",
        splits=splits,
        bs=128,
    )

    learn = tabular_learner(dls, metrics=[accuracy, RocAucBinary()], layers=[200, 100])
    learn.fit_one_cycle(5, 1e-2)
    learn.export(output_path)
    return {"trained": True}


def retrain_models_current(*, skip_fastai: bool = False) -> Dict[str, Any]:
    configure_logging(service_name="retrain_models_current")
    logger = get_logger(__name__, component="model_training")
    hub = ObservabilityHub.instance()

    training_path = PROJECT_ROOT / "model_pack" / "updated_training_data.csv"
    output_dir = PROJECT_ROOT / "model_pack"
    backup_dir = output_dir / "backups" / "models"
    paths = ModelPaths(
        ridge_path=output_dir / "ridge_model_2025.joblib",
        xgb_path=output_dir / "xgb_home_win_model_2025.pkl",
        fastai_path=output_dir / "fastai_home_win_model_2025.pkl",
    )

    hub.emit_event("retrain.start", {"training_path": str(training_path)})
    df = _load_training_data(training_path)
    hub.emit_event(
        "retrain.data_loaded",
        {"rows": int(len(df)), "seasons": sorted(df["season"].unique().tolist())[-5:]},
    )

    backups = {
        "ridge": str(_backup_file(paths.ridge_path, backup_dir) or ""),
        "xgb": str(_backup_file(paths.xgb_path, backup_dir) or ""),
        "fastai": str(_backup_file(paths.fastai_path, backup_dir) or ""),
    }
    hub.emit_event("retrain.backups_created", {"backups": backups})

    ridge_metrics = _train_ridge(df, paths.ridge_path)
    hub.emit_event("retrain.ridge_trained", ridge_metrics)

    xgb_metrics = _train_xgb(df, paths.xgb_path)
    hub.emit_event("retrain.xgb_trained", xgb_metrics)

    fastai_metrics: Dict[str, Any] = {"skipped": True}
    if not skip_fastai:
        if FASTAI_AVAILABLE:
            fastai_metrics = _train_fastai(df, paths.fastai_path)
        else:
            fastai_metrics = {"skipped": True, "reason": "fastai not installed"}
    hub.emit_event("retrain.fastai_trained", fastai_metrics)

    result = {
        "rows_used": int(len(df)),
        "backups": backups,
        "ridge": ridge_metrics,
        "xgb": xgb_metrics,
        "fastai": fastai_metrics,
    }
    logger.info("Retraining complete", extra={"result": result})
    hub.emit_event("retrain.success", result)
    return result


def _parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-fastai", action="store_true")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parse_args(argv)
    try:
        retrain_models_current(skip_fastai=args.skip_fastai)
        return 0
    except Exception as exc:
        hub = ObservabilityHub.instance()
        hub.emit_error(
            ErrorReport(
                error_type=type(exc).__name__,
                error_message=str(exc),
                category=ErrorCategory.MODEL,
                severity=ErrorSeverity.HIGH,
                context={"script": "retrain_models_current"},
            )
        )
        raise


if __name__ == "__main__":
    raise SystemExit(main())
