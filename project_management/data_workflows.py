#!/usr/bin/env python3
"""
Data workflow orchestration for Script Ohio 2.0.

This module provides a convenient import path for the data workflows
that are actually implemented in project_management/core_tools/data_workflows.py.
"""

import sys
from pathlib import Path

# Add project root to Python path for imports
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Import all the core classes and functions from the actual implementation
from project_management.core_tools.data_workflows import (
    # Core classes
    StarterDataUpdater,
    TrainingDataExtender,
    FastAIModelTrainer,

    # CLI functions
    main,
    _parse_args,
    _handle_starter_data,
    _handle_extend_training,
    _handle_fastai,
    _handle_refresh_training,

    # Utility functions
    _timestamp,
    _ensure_parent,
)

# Re-export for backward compatibility
__all__ = [
    'StarterDataUpdater',
    'TrainingDataExtender',
    'FastAIModelTrainer',
    'main',
    '_parse_args',
    '_handle_starter_data',
    '_handle_extend_training',
    '_handle_fastai',
    '_handle_refresh_training',
    '_timestamp',
    '_ensure_parent',
]

if __name__ == "__main__":
    main(sys.argv[1:])