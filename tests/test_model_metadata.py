"""
Unit tests for model metadata registry.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from src.models.metadata import MetadataRegistry, get_registry


def test_register_model():
    """Test registering a new model."""
    with tempfile.TemporaryDirectory() as tmpdir:
        registry_path = Path(tmpdir) / "test_registry.json"
        registry = MetadataRegistry(registry_path)

        metadata = registry.register_model(
            model_id="test_ridge_2025",
            model_type="ridge",
            version="2025.1.0",
            feature_set=["home_talent", "away_talent", "home_adjusted_epa"],
            training_params={"alpha": 1.0},
            performance_metrics={"mae": 12.5, "rmse": 15.2},
        )

        assert metadata.model_id == "test_ridge_2025"
        assert metadata.model_type == "ridge"
        assert len(metadata.feature_set) == 3
        assert registry_path.exists()


def test_get_model():
    """Test retrieving model metadata."""
    with tempfile.TemporaryDirectory() as tmpdir:
        registry_path = Path(tmpdir) / "test_registry.json"
        registry = MetadataRegistry(registry_path)

        registry.register_model(
            model_id="test_model",
            model_type="xgb",
            version="2025.1.0",
            feature_set=["feature1", "feature2"],
        )

        retrieved = registry.get_model("test_model")
        assert retrieved is not None
        assert retrieved.model_type == "xgb"


def test_list_models():
    """Test listing models with filters."""
    with tempfile.TemporaryDirectory() as tmpdir:
        registry_path = Path(tmpdir) / "test_registry.json"
        registry = MetadataRegistry(registry_path)

        registry.register_model(
            model_id="ridge_1",
            model_type="ridge",
            version="2025.1.0",
            feature_set=["f1"],
        )
        registry.register_model(
            model_id="xgb_1",
            model_type="xgb",
            version="2025.1.0",
            feature_set=["f1"],
        )

        ridge_models = registry.list_models(model_type="ridge")
        assert len(ridge_models) == 1
        assert ridge_models[0].model_type == "ridge"


def test_update_performance():
    """Test updating performance metrics."""
    with tempfile.TemporaryDirectory() as tmpdir:
        registry_path = Path(tmpdir) / "test_registry.json"
        registry = MetadataRegistry(registry_path)

        registry.register_model(
            model_id="test_model",
            model_type="ridge",
            version="2025.1.0",
            feature_set=["f1"],
        )

        updated = registry.update_performance("test_model", {"mae": 10.5, "rmse": 13.2})
        assert updated is not None
        assert updated.performance_metrics["mae"] == 10.5

