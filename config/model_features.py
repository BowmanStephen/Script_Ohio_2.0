"""Compatibility shim exposing feature definitions for tests."""

from importlib import util as _import_util
from pathlib import Path as _Path

_ROOT = _Path(__file__).resolve().parents[1]
_MODEL_FEATURES_PATH = _ROOT / "project_management" / "TOOLS_AND_CONFIG" / "model_features.py"

_spec = _import_util.spec_from_file_location("project_model_features", _MODEL_FEATURES_PATH)
if _spec is None or _spec.loader is None:  # pragma: no cover - defensive
    raise ImportError(f"Unable to load model features from {_MODEL_FEATURES_PATH}")

_module = _import_util.module_from_spec(_spec)
_spec.loader.exec_module(_module)

RIDGE_FEATURES = _module.RIDGE_FEATURES  # noqa: F401
XGB_FEATURES = _module.XGB_FEATURES  # noqa: F401
SHARED_FEATURES = getattr(_module, "SHARED_FEATURES", ())  # noqa: F401
describe_features = getattr(_module, "describe_features", lambda: None)  # noqa: F401
get_model_features = getattr(_module, "get_model_features")  # noqa: F401
validate_features = getattr(_module, "validate_features")  # noqa: F401

__all__ = [
    "RIDGE_FEATURES",
    "XGB_FEATURES",
    "SHARED_FEATURES",
    "describe_features",
    "get_model_features",
    "validate_features",
]
