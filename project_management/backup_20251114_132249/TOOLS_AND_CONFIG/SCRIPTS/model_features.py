"""Compatibility shim exposing feature definitions for tests.

The authoritative implementation lives in project_management/core_tools/
model_features.py. Some legacy scripts import `model_features` from the repo
root, so this module simply re-exports the public objects.
"""

from project_management.TOOLS_AND_CONFIG.model_features import *  # noqa: F401,F403
