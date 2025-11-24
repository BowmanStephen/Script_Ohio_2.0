"""
Model metadata registry for tracking model versions, features, and performance.

Provides a centralized registry for model metadata including feature sets,
training parameters, performance metrics, and versioning information.
"""

from __future__ import annotations

import datetime as dt
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REGISTRY_PATH = PROJECT_ROOT / "models" / "metadata_registry.json"
METADATA_VERSION = "0.1.0"


@dataclass
class ModelMetadata:
    """Metadata for a single model version."""

    model_id: str
    model_type: str  # "ridge", "xgb", "fastai", "ensemble", etc.
    version: str
    created_at: str
    feature_set: List[str]
    training_params: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    data_snapshot: Dict[str, Any] = field(default_factory=dict)
    file_path: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class ModelRegistry:
    """Registry of all model metadata."""

    registry_version: str = METADATA_VERSION
    created_at: str = field(default_factory=lambda: dt.datetime.now(dt.timezone.utc).isoformat())
    last_updated: str = field(default_factory=lambda: dt.datetime.now(dt.timezone.utc).isoformat())
    models: Dict[str, ModelMetadata] = field(default_factory=dict)


class MetadataRegistry:
    """Manages model metadata registry persistence and queries."""

    def __init__(self, registry_path: Path = DEFAULT_REGISTRY_PATH):
        self.registry_path = registry_path
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        self._registry = self._load_registry()

    def _load_registry(self) -> ModelRegistry:
        """Load registry from disk or create new one."""
        if self.registry_path.exists():
            try:
                with open(self.registry_path, "r") as f:
                    data = json.load(f)
                models = {
                    k: ModelMetadata(**v) for k, v in data.get("models", {}).items()
                }
                return ModelRegistry(
                    registry_version=data.get("registry_version", METADATA_VERSION),
                    created_at=data.get("created_at", dt.datetime.now(dt.timezone.utc).isoformat()),
                    last_updated=data.get("last_updated", dt.datetime.now(dt.timezone.utc).isoformat()),
                    models=models,
                )
            except Exception as e:
                # If loading fails, create new registry
                return ModelRegistry()
        return ModelRegistry()

    def _save_registry(self) -> None:
        """Persist registry to disk."""
        self._registry.last_updated = dt.datetime.now(dt.timezone.utc).isoformat()
        data = {
            "registry_version": self._registry.registry_version,
            "created_at": self._registry.created_at,
            "last_updated": self._registry.last_updated,
            "models": {k: asdict(v) for k, v in self._registry.models.items()},
        }
        with open(self.registry_path, "w") as f:
            json.dump(data, f, indent=2)

    def register_model(
        self,
        model_id: str,
        model_type: str,
        version: str,
        feature_set: List[str],
        training_params: Optional[Dict[str, Any]] = None,
        performance_metrics: Optional[Dict[str, float]] = None,
        data_snapshot: Optional[Dict[str, Any]] = None,
        file_path: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> ModelMetadata:
        """
        Register a new model or update existing model metadata.

        Args:
            model_id: Unique identifier for the model.
            model_type: Type of model (e.g., "ridge", "xgb").
            version: Version string (e.g., "2025.1.0").
            feature_set: List of feature names used by the model.
            training_params: Optional training hyperparameters.
            performance_metrics: Optional performance metrics (MAE, RMSE, etc.).
            data_snapshot: Optional snapshot of training data metadata.
            file_path: Optional path to model file.
            notes: Optional notes about the model.

        Returns:
            Registered ModelMetadata object.
        """
        metadata = ModelMetadata(
            model_id=model_id,
            model_type=model_type,
            version=version,
            created_at=dt.datetime.now(dt.timezone.utc).isoformat(),
            feature_set=feature_set,
            training_params=training_params or {},
            performance_metrics=performance_metrics or {},
            data_snapshot=data_snapshot or {},
            file_path=file_path,
            notes=notes,
        )

        self._registry.models[model_id] = metadata
        self._save_registry()
        return metadata

    def get_model(self, model_id: str) -> Optional[ModelMetadata]:
        """Retrieve metadata for a specific model."""
        return self._registry.models.get(model_id)

    def list_models(
        self,
        model_type: Optional[str] = None,
        min_version: Optional[str] = None,
    ) -> List[ModelMetadata]:
        """
        List all models matching optional filters.

        Args:
            model_type: Filter by model type.
            min_version: Filter by minimum version (string comparison).

        Returns:
            List of matching ModelMetadata objects.
        """
        models = list(self._registry.models.values())

        if model_type:
            models = [m for m in models if m.model_type == model_type]

        if min_version:
            models = [m for m in models if m.version >= min_version]

        return sorted(models, key=lambda m: m.created_at, reverse=True)

    def update_performance(
        self,
        model_id: str,
        performance_metrics: Dict[str, float],
    ) -> Optional[ModelMetadata]:
        """Update performance metrics for an existing model."""
        if model_id not in self._registry.models:
            return None

        self._registry.models[model_id].performance_metrics.update(performance_metrics)
        self._save_registry()
        return self._registry.models[model_id]

    def get_feature_usage(self) -> pd.DataFrame:
        """Get DataFrame showing feature usage across all models."""
        records = []
        for model_id, metadata in self._registry.models.items():
            for feature in metadata.feature_set:
                records.append(
                    {
                        "model_id": model_id,
                        "model_type": metadata.model_type,
                        "version": metadata.version,
                        "feature": feature,
                    }
                )
        return pd.DataFrame(records)

    def export_registry(self, output_path: Optional[Path] = None) -> Path:
        """Export registry to CSV for analysis."""
        if output_path is None:
            output_path = self.registry_path.parent / "metadata_registry_export.csv"

        records = []
        for model_id, metadata in self._registry.models.items():
            records.append(
                {
                    "model_id": model_id,
                    "model_type": metadata.model_type,
                    "version": metadata.version,
                    "created_at": metadata.created_at,
                    "num_features": len(metadata.feature_set),
                    "file_path": metadata.file_path,
                    "notes": metadata.notes,
                    **metadata.performance_metrics,
                }
            )

        df = pd.DataFrame(records)
        df.to_csv(output_path, index=False)
        return output_path


# Global registry instance
_default_registry: Optional[MetadataRegistry] = None


def get_registry(registry_path: Optional[Path] = None) -> MetadataRegistry:
    """Get or create the default metadata registry."""
    global _default_registry
    if _default_registry is None:
        _default_registry = MetadataRegistry(registry_path or DEFAULT_REGISTRY_PATH)
    return _default_registry


__all__ = [
    "ModelMetadata",
    "ModelRegistry",
    "MetadataRegistry",
    "get_registry",
]

