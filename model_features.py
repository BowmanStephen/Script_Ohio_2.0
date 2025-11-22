"""Compatibility shim for legacy imports."""

from config.model_features import (  # noqa: F401
    RIDGE_FEATURES,
    SHARED_FEATURES,
    XGB_FEATURES,
    describe_features,
    get_model_features,
    validate_features,
)

__all__ = [
    "RIDGE_FEATURES",
    "XGB_FEATURES",
    "SHARED_FEATURES",
    "describe_features",
    "get_model_features",
    "validate_features",
]
