"""Feature definitions and validation helpers.

Historically, Script Ohio referenced `project_management/TOOLS_AND_CONFIG/model_features.py`.
That file may not be present in all deployments. This module provides a resilient
fallback so agents and scripts can continue to validate feature sets.
"""

from __future__ import annotations

from importlib import util as _import_util
from pathlib import Path as _Path
from typing import Any, Dict, Iterable, List, Sequence

_ROOT = _Path(__file__).resolve().parents[1]
_PROJECT_FEATURES_PATH = (
    _ROOT / "project_management" / "TOOLS_AND_CONFIG" / "model_features.py"
)

try:
    if not _PROJECT_FEATURES_PATH.exists():
        raise FileNotFoundError(str(_PROJECT_FEATURES_PATH))

    _spec = _import_util.spec_from_file_location(
        "project_model_features", _PROJECT_FEATURES_PATH
    )
    if _spec is None or _spec.loader is None:  # pragma: no cover - defensive
        raise ImportError(
            f"Unable to load model features from {_PROJECT_FEATURES_PATH}"
        )

    _module = _import_util.module_from_spec(_spec)
    _spec.loader.exec_module(_module)

    RIDGE_FEATURES = list(_module.RIDGE_FEATURES)
    XGB_FEATURES = list(_module.XGB_FEATURES)
    SHARED_FEATURES = list(getattr(_module, "SHARED_FEATURES", ()))

    describe_features = getattr(_module, "describe_features", lambda: None)
except Exception:
    from config.model_config import RIDGE_FEATURES, XGB_FEATURES

    SHARED_FEATURES: List[str] = sorted(list(set(RIDGE_FEATURES) & set(XGB_FEATURES)))

    def describe_features() -> None:
        """Print a lightweight feature summary."""

        print(f"RIDGE_FEATURES: {len(RIDGE_FEATURES)}")
        print(f"XGB_FEATURES: {len(XGB_FEATURES)}")


def get_model_features(model_name: str) -> List[str]:
    """Return expected feature list for a given model name."""

    key = (model_name or "").lower()
    if key in {"ridge", "margin"}:
        return list(RIDGE_FEATURES)
    if key in {"xgb", "xgboost", "home_win"}:
        return list(XGB_FEATURES)
    if key in {"fastai"}:
        return list(XGB_FEATURES)
    return []


def validate_features(
    available_features: Iterable[str], expected_features: Sequence[str]
) -> Dict[str, Any]:
    """Validate that expected features exist in the provided feature set."""

    available = set(available_features)
    missing = [f for f in expected_features if f not in available]
    return {
        "ok": len(missing) == 0,
        "missing": missing,
        "expected_count": len(expected_features),
        "available_count": len(available),
    }


__all__ = [
    "RIDGE_FEATURES",
    "XGB_FEATURES",
    "SHARED_FEATURES",
    "describe_features",
    "get_model_features",
    "validate_features",
]
