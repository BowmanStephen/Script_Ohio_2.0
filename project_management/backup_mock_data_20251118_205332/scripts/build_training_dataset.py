#!/usr/bin/env python3
"""
Orchestrate the end-to-end training dataset refresh workflow.

Steps:
1. Optionally run the starter-pack migration so the current season matches
   the 86-feature training schema.
2. Append/merge the migrated CSV into `model_pack/updated_training_data.csv`.
3. (Optional) Retrain the FastAI neural classifier to keep notebooks + agents current.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from model_pack.migrate_starter_pack_data import StarterPackDataMigrator
from project_management.data_workflows import FastAIModelTrainer, TrainingDataExtender


@dataclass
class TrainingDatasetBuilder:
    """Compose migration + extension + (optional) retraining steps."""

    max_week: Optional[int] = None
    migrated_file: Optional[Path] = None
    run_migration: bool = True
    extend_training: bool = True
    train_models: bool = False
    epochs: int = 300
    learning_rate: float = 1e-3

    def run(self) -> dict:
        summary: dict = {}
        path_to_use = self.migrated_file

        if self.run_migration:
            migrator = StarterPackDataMigrator()
            if not migrator.run_migration():
                raise RuntimeError("Starter pack migration failed. See console logs above.")
            path_to_use = Path(migrator.output_file)
        elif path_to_use is None:
            raise ValueError("Provide --migrated-file when skipping migration.")

        path_to_use = self._maybe_filter_week(path_to_use)
        summary["migrated_file"] = str(path_to_use)

        if self.extend_training:
            extender = TrainingDataExtender()
            extend_result = extender.extend(path_to_use)
            summary["extension"] = extend_result
        else:
            summary["extension"] = None

        if self.train_models:
            trainer = FastAIModelTrainer()
            train_result = trainer.train(epochs=self.epochs, learning_rate=self.learning_rate)
            summary["model_training"] = train_result
        else:
            summary["model_training"] = None

        return summary

    def _maybe_filter_week(self, migrated_file: Path) -> Path:
        if self.max_week is None:
            return migrated_file

        frame = pd.read_csv(migrated_file, low_memory=False)
        filtered = frame[frame["week"] <= self.max_week].copy()
        target = migrated_file.with_name(f"{migrated_file.stem}_week_{self.max_week}.csv")
        filtered.to_csv(target, index=False)
        return target


def _parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Rebuild/extend the model training dataset.")
    parser.add_argument("--max-week", type=int, default=None, help="Only include weeks up to this number.")
    parser.add_argument("--skip-migration", action="store_true", help="Skip starter-pack migration step.")
    parser.add_argument("--migrated-file", default=None, help="Existing migrated CSV to use when skipping migration.")
    parser.add_argument("--skip-extend", action="store_true", help="Skip appending to updated_training_data.csv.")
    parser.add_argument("--train-models", action="store_true", help="Retrain the FastAI neural model after extending data.")
    parser.add_argument("--epochs", type=int, default=300)
    parser.add_argument("--learning-rate", type=float, default=1e-3)
    return parser.parse_args(argv)


def run_build_training_pipeline(
    *,
    max_week: Optional[int],
    skip_migration: bool,
    migrated_file: Optional[str],
    skip_extend: bool,
    train_models: bool,
    epochs: int,
    learning_rate: float,
) -> dict:
    builder = TrainingDatasetBuilder(
        max_week=max_week,
        migrated_file=Path(migrated_file) if migrated_file else None,
        run_migration=not skip_migration,
        extend_training=not skip_extend,
        train_models=train_models,
        epochs=epochs,
        learning_rate=learning_rate,
    )
    return builder.run()


def main(argv: Optional[Iterable[str]] = None) -> None:
    args = _parse_args(argv)
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


if __name__ == "__main__":
    main(sys.argv[1:])
