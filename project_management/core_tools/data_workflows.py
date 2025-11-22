#!/usr/bin/env python3
"""
High-level data workflow orchestration for Script Ohio 2.0.

This CLI fills multiple execution gaps:
1. Refresh starter-pack data from CFBD with a single command.
2. Append new seasons/weeks to the model-pack training dataset.
3. Train and serialize the FastAI neural win-probability model so notebooks
   and agents always have a real artifact to load.

Example usage:

    python project_management/data_workflows.py starter-data --season 2025 --week 13
    python project_management/data_workflows.py extend-training --migrated-file model_pack/2025_starter_pack_migrated.csv
    python project_management/data_workflows.py train-fastai --epochs 250
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import shutil
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

import pandas as pd
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

try:
    from fastai.losses import CrossEntropyLossFlat
    from fastai.tabular.all import (
        CategoryBlock,
        Categorify,
        FillMissing,
        Normalize,
        RandomSplitter,
        TabularPandas,
        RocAucBinary,
        accuracy,
        tabular_learner,
        F1Score,
    )

    FASTAI_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    FASTAI_AVAILABLE = False

# Ensure project root is importable when running as a module/script
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from starter_pack.config.data_config import get_starter_pack_config, StarterPackDataConfig
from starter_pack.utils.cfbd_loader import CFBDLoader, CFBDLoaderError, DEFAULT_HOST

try:
    from model_pack.config.data_config import get_data_config as get_model_pack_config
except ImportError:  # pragma: no cover - tests can inject stub path
    get_model_pack_config = None  # type: ignore


def _timestamp() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d_%H%M%S")


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Starter-pack live data refresh
# ---------------------------------------------------------------------------


@dataclass
class StarterDataUpdater:
    """Fetch new CFBD data and keep starter_pack/data/*.csv current."""

    config: StarterPackDataConfig = field(default_factory=get_starter_pack_config)

    def __post_init__(self) -> None:
        self.data_dir = self.config.data_dir
        self.snapshots_dir = self.data_dir / "live_snapshots"
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)
        self.cfbd_host = os.environ.get("CFBD_API_HOST", DEFAULT_HOST)

    def fetch_games(
        self,
        *,
        season: int,
        week: Optional[int],
        season_type: str,
        api_key: Optional[str],
    ) -> pd.DataFrame:
        """Fetch games via CFBD Python client."""
        token = api_key or os.environ.get("CFBD_API_KEY") or os.environ.get("CFBD_API_TOKEN")
        if not token:
            raise RuntimeError("CFBD API key missing. Set CFBD_API_KEY or pass --api-key.")

        loader = CFBDLoader(api_key=token, host=self.cfbd_host)
        try:
            frame = loader.fetch_games(
                season=season,
                season_type=season_type,
                week=week,
                use_cache=False,
                persist_cache=False,
            )
        except CFBDLoaderError as exc:
            raise RuntimeError(str(exc)) from exc

        if frame.empty:
            raise RuntimeError(f"No games returned for season={season}, week={week}, season_type={season_type}")

        df = frame.copy()
        df["fetched_at_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
        return df

    def persist_snapshot(self, frame: pd.DataFrame, *, season: int, week: Optional[int], season_type: str) -> Path:
        """Write a raw snapshot for reproducibility."""
        stamp = _timestamp()
        week_label = f"week_{week}" if week is not None else "full"
        snapshot_path = self.snapshots_dir / str(season) / f"{season_type}_{week_label}_{stamp}.csv"
        _ensure_parent(snapshot_path)
        frame.to_csv(snapshot_path, index=False)
        return snapshot_path

    def update_games_csv(self, frame: pd.DataFrame) -> Tuple[Path, int]:
        """Merge the latest frame into starter_pack/data/games.csv."""
        master_path = self.config.get_data_path("games.csv")
        if master_path.exists():
            existing = pd.read_csv(master_path, low_memory=False)
        else:
            existing = pd.DataFrame()

        combined = self._merge_games(existing, frame)
        _ensure_parent(master_path)
        combined.to_csv(master_path, index=False)
        return master_path, len(combined)

    @staticmethod
    def _merge_games(existing: pd.DataFrame, new_data: pd.DataFrame) -> pd.DataFrame:
        """Combine existing and new games while deduplicating on game id."""
        if existing.empty:
            return new_data.sort_values(["season", "week", "start_date"], na_position="last").reset_index(drop=True)

        merged = pd.concat([existing, new_data], ignore_index=True, sort=False)
        if "id" in merged.columns:
            merged = merged.drop_duplicates(subset=["id"], keep="last")
        merged = merged.sort_values(["season", "week", "start_date"], na_position="last")
        return merged.reset_index(drop=True)

    def run(
        self,
        *,
        season: int,
        week: Optional[int],
        season_type: str,
        api_key: Optional[str],
        dry_run: bool = False,
    ) -> dict:
        frame = self.fetch_games(season=season, week=week, season_type=season_type, api_key=api_key)
        snapshot_path = self.persist_snapshot(frame, season=season, week=week, season_type=season_type)
        summary = {"snapshot": str(snapshot_path), "rows": len(frame)}
        if not dry_run:
            master_path, total_rows = self.update_games_csv(frame)
            summary.update({"master": str(master_path), "total_rows": total_rows})
        return summary


# ---------------------------------------------------------------------------
# Training dataset extension
# ---------------------------------------------------------------------------


@dataclass
class TrainingDataExtender:
    """Append newly migrated data to the model training dataset."""

    training_data_path: Path = field(default_factory=lambda: get_model_pack_config().get_training_data_path())  # type: ignore

    def __post_init__(self) -> None:
        self.backup_dir = self.training_data_path.parent / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def extend(self, migrated_file: Path, output_path: Optional[Path] = None) -> dict:
        migrated_file = Path(migrated_file)
        if not migrated_file.exists():
            raise FileNotFoundError(f"Migrated file not found: {migrated_file}")

        base = pd.read_csv(self.training_data_path, low_memory=False)
        incoming = pd.read_csv(migrated_file, low_memory=False)
        combined = self._merge(base, incoming)

        backup_path = self._create_backup()
        target = Path(output_path) if output_path else self.training_data_path
        combined.to_csv(target, index=False)

        return {
            "backup": str(backup_path),
            "output": str(target),
            "rows_before": len(base),
            "rows_after": len(combined),
            "rows_added": len(combined) - len(base),
        }

    def _create_backup(self) -> Path:
        backup_path = self.backup_dir / f"{self.training_data_path.stem}_backup_{_timestamp()}.csv"
        shutil.copy2(self.training_data_path, backup_path)
        return backup_path

    @staticmethod
    def _merge(base: pd.DataFrame, incoming: pd.DataFrame) -> pd.DataFrame:
        merged = pd.concat([base, incoming], ignore_index=True, sort=False)
        dedupe_keys = [key for key in ("game_key", "id") if key in merged.columns]
        if dedupe_keys:
            merged = merged.drop_duplicates(subset=dedupe_keys, keep="last")
        return merged.reset_index(drop=True)


# ---------------------------------------------------------------------------
# FastAI neural classifier training
# ---------------------------------------------------------------------------


@dataclass
class FastAIModelTrainer:
    """Train the FastAI neural network win probability model."""

    training_data_path: Path = field(default_factory=lambda: get_model_pack_config().get_training_data_path())  # type: ignore
    output_path: Path = field(default_factory=lambda: Path("model_pack/fastai_home_win_model_2025.pkl"))
    random_state: int = 42
    valid_pct: float = 0.2
    batch_size: int = 128
    hidden_layers: Tuple[int, ...] = (256, 128, 64)

    TARGET_COLUMN = "home_win"
    CATEGORICAL_FEATURES = [
        "season_type",
        "neutral_site",
        "home_team",
        "home_conference",
        "away_team",
        "away_conference",
        "conference_game",
    ]
    EXCLUDED_COLUMNS = {
        "id",
        "start_date",
        "home_points",
        "away_points",
        "margin",
        "spread",
        "game_key",
        TARGET_COLUMN,
    }

    def train(
        self,
        *,
        epochs: int,
        learning_rate: float,
        learner_factory=None,
    ) -> dict:
        if not FASTAI_AVAILABLE:  # pragma: no cover - exercised in integration tests
            raise RuntimeError(
                "fastai is not installed. Install it via `pip install fastai` or "
                "`pip install -r requirements.txt` before training the neural model."
            )

        frame = pd.read_csv(self.training_data_path, low_memory=False)
        if "margin" not in frame.columns:
            raise RuntimeError("Training data must contain a 'margin' column to derive home_win labels.")

        if self.TARGET_COLUMN not in frame.columns:
            frame[self.TARGET_COLUMN] = (frame["margin"] > 0).astype(int)

        cat_names = [col for col in self.CATEGORICAL_FEATURES if col in frame.columns]
        cont_names = self._select_continuous_features(frame, set(cat_names))
        if not cont_names:
            raise RuntimeError("No continuous feature columns available for FastAI training.")

        splitter = RandomSplitter(valid_pct=self.valid_pct, seed=self.random_state)
        splits = splitter(list(range(len(frame))))
        to = TabularPandas(
            frame,
            procs=[Categorify, FillMissing, Normalize],
            cat_names=cat_names,
            cont_names=cont_names,
            y_names=self.TARGET_COLUMN,
            y_block=CategoryBlock(),
            splits=splits,
        )
        dls = to.dataloaders(bs=self.batch_size)

        learner_factory = learner_factory or self._default_learner_factory
        learner = learner_factory(dls)
        learner.fit_one_cycle(epochs, lr_max=learning_rate)

        _ensure_parent(self.output_path)
        learner.export(self.output_path)

        return {
            "output": str(self.output_path),
            "rows": len(frame),
            "cat_features": len(cat_names),
            "cont_features": len(cont_names),
            "target_positive_rate": float(frame[self.TARGET_COLUMN].mean()),
        }

    def _select_continuous_features(self, frame: pd.DataFrame, categorical: set) -> List[str]:
        allowed = []
        for col in frame.columns:
            if col in self.EXCLUDED_COLUMNS or col in categorical:
                continue
            if pd.api.types.is_numeric_dtype(frame[col]):
                allowed.append(col)
        return allowed

    def _default_learner_factory(self, dataloaders):
        return tabular_learner(
            dataloaders,
            layers=list(self.hidden_layers),
            metrics=[accuracy, RocAucBinary(), F1Score()],
            loss_func=CrossEntropyLossFlat(),
        )


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------


def _parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Data workflows for Script Ohio 2.0")
    subparsers = parser.add_subparsers(dest="command", required=True)

    starter_parser = subparsers.add_parser("starter-data", help="Refresh starter pack games via CFBD")
    starter_parser.add_argument("--season", type=int, required=True)
    starter_parser.add_argument("--week", type=int, default=None)
    starter_parser.add_argument("--season-type", default="regular", choices=["regular", "postseason"])
    starter_parser.add_argument("--api-key", default=None)
    starter_parser.add_argument("--dry-run", action="store_true")

    extend_parser = subparsers.add_parser("extend-training", help="Append migrated data into training dataset")
    extend_parser.add_argument("--migrated-file", required=True, help="CSV produced by migrate_starter_pack_data.py")
    extend_parser.add_argument("--output", default=None, help="Optional alternate output path")

    fastai_parser = subparsers.add_parser("train-fastai", help="Train the FastAI neural win probability model")
    fastai_parser.add_argument("--epochs", type=int, default=300)
    fastai_parser.add_argument("--learning-rate", type=float, default=1e-3)

    refresh_parser = subparsers.add_parser(
        "refresh-training",
        help="Run migration + training-data extension (+ optional retrain) in one shot",
    )
    refresh_parser.add_argument("--max-week", type=int, default=None)
    refresh_parser.add_argument("--skip-migration", action="store_true")
    refresh_parser.add_argument("--migrated-file", default=None)
    refresh_parser.add_argument("--skip-extend", action="store_true")
    refresh_parser.add_argument("--train-models", action="store_true")
    refresh_parser.add_argument("--epochs", type=int, default=300)
    refresh_parser.add_argument("--learning-rate", type=float, default=1e-3)

    return parser.parse_args(argv)


def _handle_starter_data(args: argparse.Namespace) -> None:
    updater = StarterDataUpdater()
    summary = updater.run(
        season=args.season,
        week=args.week,
        season_type=args.season_type,
        api_key=args.api_key,
        dry_run=args.dry_run,
    )
    print(json.dumps(summary, indent=2))


def _handle_extend_training(args: argparse.Namespace) -> None:
    extender = TrainingDataExtender()
    summary = extender.extend(Path(args.migrated_file), Path(args.output) if args.output else None)
    print(json.dumps(summary, indent=2))


def _handle_fastai(args: argparse.Namespace) -> None:
    trainer = FastAIModelTrainer()
    summary = trainer.train(epochs=args.epochs, learning_rate=args.learning_rate)
    print(json.dumps(summary, indent=2))


def _handle_refresh_training(args: argparse.Namespace) -> None:
    from model_pack.scripts.build_training_dataset import run_build_training_pipeline

    summary = run_build_training_pipeline(
        max_week=args.max_week,
        skip_migration=args.skip_migration,
        migrated_file=args.migrated_file,
        skip_extend=args.skip_extend,
        train_models=args.train_models,
        epochs=args.epochs,
        learning_rate=args.learning_rate,
    )
    print(json.dumps(summary, indent=2))


def main(argv: Optional[Iterable[str]] = None) -> None:
    args = _parse_args(argv)
    if args.command == "starter-data":
        _handle_starter_data(args)
    elif args.command == "extend-training":
        _handle_extend_training(args)
    elif args.command == "train-fastai":
        _handle_fastai(args)
    elif args.command == "refresh-training":
        _handle_refresh_training(args)
    else:  # pragma: no cover - defensive
        raise ValueError(f"Unknown command: {args.command}")


if __name__ == "__main__":
    main(sys.argv[1:])
