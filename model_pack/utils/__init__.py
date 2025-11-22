"""
Utilities package for Script Ohio 2.0

Provides path resolution and other utility functions.
"""

from .path_utils import (
    find_project_root,
    resolve_path,
    find_data_file,
    get_training_data_file,
    ensure_directory_exists,
    get_output_directory,
    validate_file_exists,
)

__all__ = [
    'find_project_root',
    'resolve_path',
    'find_data_file',
    'get_training_data_file',
    'ensure_directory_exists',
    'get_output_directory',
    'validate_file_exists',
]

