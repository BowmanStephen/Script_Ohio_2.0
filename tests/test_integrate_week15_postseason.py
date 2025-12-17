#!/usr/bin/env python3
"""
Comprehensive unit tests for Week 15 + Postseason training data integration.

These tests operate on a synthetic mini project layout under tmp_path to avoid
modifying real datasets in the repository. Tests cover:
- File loading and path resolution
- Schema validation
- Deduplication logic
- Backup creation
- Rollback mechanism
- Error handling
- Observability integration
"""

from __future__ import annotations

import importlib.util
import shutil
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, List

import pandas as pd
import pytest


def _load_module(module_name: str, path: Path) -> ModuleType:
    """Load a Python module from a file path."""
    spec = importlib.util.spec_from_file_location(module_name, str(path))
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)  # type: ignore[assignment]
    return module


def _write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    """Write a CSV file from a list of dictionaries."""
    df = pd.DataFrame(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def _mini_project_root(tmp_path: Path) -> Path:
    """Create a minimal project structure for testing."""
    (tmp_path / "AGENTS.md").write_text("test", encoding="utf-8")
    (tmp_path / "README.md").write_text("test", encoding="utf-8")
    (tmp_path / "model_pack").mkdir(parents=True, exist_ok=True)
    (tmp_path / "data" / "training" / "weekly").mkdir(parents=True, exist_ok=True)
    return tmp_path


def _base_columns() -> List[str]:
    """Return base required columns for test data."""
    return [
        "id",
        "season",
        "week",
        "season_type",
        "home_team",
        "away_team",
        "margin",
    ]


def _create_full_schema_columns() -> List[str]:
    """Create a full schema with 88 columns (86 features + 2 metadata)."""
    base = _base_columns()
    # Add enough columns to meet minimum requirement
    feature_cols = [f"feature_{i:02d}" for i in range(1, 81)]
    return base + feature_cols


def test_file_loading_week15(tmp_path: Path) -> None:
    """Test that week 15 file is loaded correctly."""
    project_root = _mini_project_root(tmp_path)
    week15_path = (
        project_root / "data" / "training" / "weekly" / "training_data_2025_week15.csv"
    )
    _write_csv(
        week15_path,
        [
            {
                "id": 1,
                "season": 2025,
                "week": 15,
                "season_type": "regular",
                "home_team": "A",
                "away_team": "B",
                "margin": 7,
            }
        ],
    )

    from model_pack.utils.path_utils import get_weekly_training_file

    resolved = get_weekly_training_file(week=15, season=2025, base_path=project_root)
    assert resolved == week15_path
    assert resolved.exists()


def test_file_loading_postseason(tmp_path: Path) -> None:
    """Test that postseason file is loaded correctly."""
    project_root = _mini_project_root(tmp_path)
    postseason_path = (
        project_root
        / "data"
        / "training"
        / "weekly"
        / "training_data_2025_postseason.csv"
    )
    _write_csv(
        postseason_path,
        [
            {
                "id": 2,
                "season": 2025,
                "week": 16,
                "season_type": "postseason",
                "home_team": "C",
                "away_team": "D",
                "margin": 10,
            }
        ],
    )

    from model_pack.utils.path_utils import get_postseason_training_file

    resolved = get_postseason_training_file(season=2025, base_path=project_root)
    assert resolved == postseason_path
    assert resolved.exists()


def test_integration_creates_backup_and_writes_master(tmp_path: Path) -> None:
    """Test that integration creates backup and writes to master file."""
    project_root = _mini_project_root(tmp_path)

    master_path = project_root / "model_pack" / "updated_training_data.csv"
    week15_path = (
        project_root / "data" / "training" / "weekly" / "training_data_2025_week15.csv"
    )
    postseason_path = (
        project_root
        / "data"
        / "training"
        / "weekly"
        / "training_data_2025_postseason.csv"
    )

    _write_csv(
        master_path,
        [
            {
                "id": 10,
                "season": 2025,
                "week": 14,
                "season_type": "regular",
                "home_team": "X",
                "away_team": "Y",
                "margin": 3,
            }
        ],
    )
    _write_csv(
        week15_path,
        [
            {
                "id": 11,
                "season": 2025,
                "week": 15,
                "season_type": "regular",
                "home_team": "A",
                "away_team": "B",
                "margin": -7,
            }
        ],
    )
    _write_csv(
        postseason_path,
        [
            {
                "id": 12,
                "season": 2025,
                "week": 16,
                "season_type": "postseason",
                "home_team": "C",
                "away_team": "D",
                "margin": 10,
            }
        ],
    )

    module = _load_module(
        "integrate_week15_postseason", Path("scripts/integrate_week15_postseason.py")
    )

    result = module.integrate_week15_postseason(base_path=project_root)

    assert result["success"] is True
    assert result["original_game_count"] == 1
    assert result["week15_games"] == 1
    assert result["postseason_games"] == 1
    assert result["final_game_count"] == 3
    assert result["backup_path"] is not None
    assert Path(result["backup_path"]).exists()

    integrated = pd.read_csv(master_path)
    assert len(integrated) == 3
    assert set(integrated["id"].tolist()) == {10, 11, 12}


def test_integration_dedupes_on_id_keep_last(tmp_path: Path) -> None:
    """Test that integration deduplicates on game ID, keeping last occurrence."""
    project_root = _mini_project_root(tmp_path)

    master_path = project_root / "model_pack" / "updated_training_data.csv"
    week15_path = (
        project_root / "data" / "training" / "weekly" / "training_data_2025_week15.csv"
    )
    postseason_path = (
        project_root
        / "data"
        / "training"
        / "weekly"
        / "training_data_2025_postseason.csv"
    )

    _write_csv(
        master_path,
        [
            {
                "id": 10,
                "season": 2025,
                "week": 14,
                "season_type": "regular",
                "home_team": "X",
                "away_team": "Y",
                "margin": 3,
            }
        ],
    )
    _write_csv(
        week15_path,
        [
            {
                "id": 10,  # Duplicate ID
                "season": 2025,
                "week": 15,
                "season_type": "regular",
                "home_team": "X",
                "away_team": "Y",
                "margin": 21,  # Different margin
            }
        ],
    )
    _write_csv(
        postseason_path,
        [
            {
                "id": 12,
                "season": 2025,
                "week": 16,
                "season_type": "postseason",
                "home_team": "C",
                "away_team": "D",
                "margin": 10,
            }
        ],
    )

    module = _load_module(
        "integrate_week15_postseason", Path("scripts/integrate_week15_postseason.py")
    )
    result = module.integrate_week15_postseason(base_path=project_root)

    assert result["duplicates_removed"] == 1
    assert result["final_game_count"] == 2

    integrated = pd.read_csv(master_path)
    assert len(integrated) == 2
    # Should keep the last occurrence (from week15 with margin=21)
    assert int(integrated[integrated["id"] == 10]["margin"].iloc[0]) == 21


def test_schema_validation_catches_mismatches(tmp_path: Path) -> None:
    """Test that schema validation catches column mismatches."""
    project_root = _mini_project_root(tmp_path)

    master_path = project_root / "model_pack" / "updated_training_data.csv"
    week15_path = (
        project_root / "data" / "training" / "weekly" / "training_data_2025_week15.csv"
    )
    postseason_path = (
        project_root
        / "data"
        / "training"
        / "weekly"
        / "training_data_2025_postseason.csv"
    )

    # Create dataframes with different columns
    week15_df = pd.DataFrame(
        {
            "id": [1],
            "season": [2025],
            "week": [15],
            "season_type": ["regular"],
            "home_team": ["A"],
            "away_team": ["B"],
            "margin": [7],
            "extra_col": [999],  # Extra column
        }
    )
    week15_df.to_csv(week15_path, index=False)

    postseason_df = pd.DataFrame(
        {
            "id": [2],
            "season": [2025],
            "week": [16],
            "season_type": ["postseason"],
            "home_team": ["C"],
            "away_team": ["D"],
            "margin": [10],
            # Missing extra_col
        }
    )
    postseason_df.to_csv(postseason_path, index=False)

    master_df = pd.DataFrame(
        {
            "id": [10],
            "season": [2025],
            "week": [14],
            "season_type": ["regular"],
            "home_team": ["X"],
            "away_team": ["Y"],
            "margin": [3],
        }
    )
    master_df.to_csv(master_path, index=False)

    module = _load_module(
        "integrate_week15_postseason", Path("scripts/integrate_week15_postseason.py")
    )

    with pytest.raises(ValueError, match="Schema mismatch"):
        module.integrate_week15_postseason(base_path=project_root)


def test_required_columns_validation(tmp_path: Path) -> None:
    """Test that missing required columns are caught."""
    project_root = _mini_project_root(tmp_path)

    week15_path = (
        project_root / "data" / "training" / "weekly" / "training_data_2025_week15.csv"
    )
    postseason_path = (
        project_root
        / "data"
        / "training"
        / "weekly"
        / "training_data_2025_postseason.csv"
    )

    # Missing 'id' column
    week15_df = pd.DataFrame(
        {
            "season": [2025],
            "week": [15],
            "season_type": ["regular"],
            "home_team": ["A"],
            "away_team": ["B"],
        }
    )
    week15_df.to_csv(week15_path, index=False)

    postseason_df = pd.DataFrame(
        {
            "id": [2],
            "season": [2025],
            "week": [16],
            "season_type": ["postseason"],
            "home_team": ["C"],
            "away_team": ["D"],
        }
    )
    postseason_df.to_csv(postseason_path, index=False)

    module = _load_module(
        "integrate_week15_postseason", Path("scripts/integrate_week15_postseason.py")
    )

    with pytest.raises(ValueError, match="Missing required columns"):
        module.integrate_week15_postseason(base_path=project_root)


def test_dry_run_mode(tmp_path: Path) -> None:
    """Test that dry-run mode validates without writing files."""
    project_root = _mini_project_root(tmp_path)

    master_path = project_root / "model_pack" / "updated_training_data.csv"
    week15_path = (
        project_root / "data" / "training" / "weekly" / "training_data_2025_week15.csv"
    )
    postseason_path = (
        project_root
        / "data"
        / "training"
        / "weekly"
        / "training_data_2025_postseason.csv"
    )

    original_master = pd.DataFrame(
        {
            "id": [10],
            "season": [2025],
            "week": [14],
            "season_type": ["regular"],
            "home_team": ["X"],
            "away_team": ["Y"],
            "margin": [3],
        }
    )
    original_master.to_csv(master_path, index=False)
    original_bytes = master_path.read_bytes()

    _write_csv(
        week15_path,
        [
            {
                "id": 11,
                "season": 2025,
                "week": 15,
                "season_type": "regular",
                "home_team": "A",
                "away_team": "B",
                "margin": 7,
            }
        ],
    )
    _write_csv(
        postseason_path,
        [
            {
                "id": 12,
                "season": 2025,
                "week": 16,
                "season_type": "postseason",
                "home_team": "C",
                "away_team": "D",
                "margin": 10,
            }
        ],
    )

    module = _load_module(
        "integrate_week15_postseason", Path("scripts/integrate_week15_postseason.py")
    )
    result = module.integrate_week15_postseason(dry_run=True, base_path=project_root)

    assert result["dry_run"] is True
    assert result["success"] is True
    assert result["backup_path"] is None  # No backup in dry-run
    # Master file should be unchanged
    assert master_path.read_bytes() == original_bytes


def test_rollback_on_validation_failure(tmp_path: Path) -> None:
    """Test that rollback occurs when validation fails after backup."""
    project_root = _mini_project_root(tmp_path)

    master_path = project_root / "model_pack" / "updated_training_data.csv"
    week15_path = (
        project_root / "data" / "training" / "weekly" / "training_data_2025_week15.csv"
    )
    postseason_path = (
        project_root
        / "data"
        / "training"
        / "weekly"
        / "training_data_2025_postseason.csv"
    )

    original_master = pd.DataFrame(
        {
            "id": [10],
            "season": [2025],
            "week": [14],
            "season_type": ["regular"],
            "home_team": ["X"],
            "away_team": ["Y"],
            "margin": [3],
        }
    )
    original_master.to_csv(master_path, index=False)
    original_bytes = master_path.read_bytes()

    # Create week15 with invalid data (null in critical column)
    week15_df = pd.DataFrame(
        {
            "id": [None],  # Invalid: null in critical column
            "season": [2025],
            "week": [15],
            "season_type": ["regular"],
            "home_team": ["A"],
            "away_team": ["B"],
            "margin": [7],
        }
    )
    week15_df.to_csv(week15_path, index=False)

    _write_csv(
        postseason_path,
        [
            {
                "id": 12,
                "season": 2025,
                "week": 16,
                "season_type": "postseason",
                "home_team": "C",
                "away_team": "D",
                "margin": 10,
            }
        ],
    )

    module = _load_module(
        "integrate_week15_postseason", Path("scripts/integrate_week15_postseason.py")
    )

    # Should raise ValueError during validation
    with pytest.raises(ValueError, match="Null values in critical columns"):
        module.integrate_week15_postseason(base_path=project_root)

    # Master file should be unchanged (rollback should have occurred)
    # Note: In the current implementation, rollback only happens if error occurs after backup
    # Since validation happens before backup, file should remain unchanged
    assert master_path.read_bytes() == original_bytes


def test_observability_events_emitted(tmp_path: Path) -> None:
    """Test that observability events are emitted during integration."""
    project_root = _mini_project_root(tmp_path)

    master_path = project_root / "model_pack" / "updated_training_data.csv"
    week15_path = (
        project_root / "data" / "training" / "weekly" / "training_data_2025_week15.csv"
    )
    postseason_path = (
        project_root
        / "data"
        / "training"
        / "weekly"
        / "training_data_2025_postseason.csv"
    )

    _write_csv(
        master_path,
        [
            {
                "id": [10],
                "season": [2025],
                "week": [14],
                "season_type": ["regular"],
                "home_team": ["X"],
                "away_team": ["Y"],
                "margin": [3],
            }
        ],
    )
    _write_csv(
        week15_path,
        [
            {
                "id": 11,
                "season": 2025,
                "week": 15,
                "season_type": "regular",
                "home_team": "A",
                "away_team": "B",
                "margin": 7,
            }
        ],
    )
    _write_csv(
        postseason_path,
        [
            {
                "id": 12,
                "season": 2025,
                "week": 16,
                "season_type": "postseason",
                "home_team": "C",
                "away_team": "D",
                "margin": 10,
            }
        ],
    )

    module = _load_module(
        "integrate_week15_postseason", Path("scripts/integrate_week15_postseason.py")
    )

    # Get the hub instance to check events
    hub = module.ObservabilityHub.instance()
    initial_event_count = len(hub._events)

    result = module.integrate_week15_postseason(base_path=project_root)

    # Check that events were emitted
    assert len(hub._events) > initial_event_count
    # Check for specific event types
    event_types = [event.event_type for event in hub._events]
    assert "integration.start" in event_types
    assert "integration.file_loaded" in event_types
    assert "integration.success" in event_types


def test_missing_files_error(tmp_path: Path) -> None:
    """Test that missing files raise FileNotFoundError."""
    project_root = _mini_project_root(tmp_path)

    # Don't create the files
    module = _load_module(
        "integrate_week15_postseason", Path("scripts/integrate_week15_postseason.py")
    )

    with pytest.raises(FileNotFoundError):
        module.integrate_week15_postseason(base_path=project_root)
