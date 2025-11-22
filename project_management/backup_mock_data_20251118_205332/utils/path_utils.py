#!/usr/bin/env python3
"""
Path Resolution Utilities for Script Ohio 2.0

Provides centralized path resolution, project root detection, and file existence checking.
"""

import os
import logging
from pathlib import Path
from typing import Optional, List, Tuple

logger = logging.getLogger(__name__)

# Cache for project root to avoid repeated lookups
_PROJECT_ROOT_CACHE: Optional[Path] = None


def find_project_root(start_path: Optional[Path] = None, marker_files: Optional[List[str]] = None) -> Path:
    """
    Find the project root directory by looking for marker files.
    
    Args:
        start_path: Starting directory for search (defaults to current file's directory)
        marker_files: List of marker files to look for (default: ['.git', 'AGENTS.md', 'README.md'])
    
    Returns:
        Path to project root directory
    
    Raises:
        RuntimeError: If project root cannot be found
    """
    global _PROJECT_ROOT_CACHE
    
    # Return cached value if available
    if _PROJECT_ROOT_CACHE is not None:
        return _PROJECT_ROOT_CACHE
    
    if marker_files is None:
        marker_files = ['.git', 'AGENTS.md', 'README.md', 'CLAUDE.md']
    
    if start_path is None:
        # Start from the directory containing this file
        start_path = Path(__file__).resolve().parent.parent.parent
    
    current = Path(start_path).resolve()
    
    # Search up the directory tree
    for parent in [current] + list(current.parents):
        # Check if any marker file exists
        for marker in marker_files:
            if (parent / marker).exists():
                _PROJECT_ROOT_CACHE = parent
                logger.debug(f"Found project root: {parent}")
                return parent
    
    # Fallback: use the directory containing this file's parent's parent
    # (assuming this file is in model_pack/utils/)
    fallback_root = Path(__file__).resolve().parent.parent.parent
    logger.warning(f"Could not find project root using markers, using fallback: {fallback_root}")
    _PROJECT_ROOT_CACHE = fallback_root
    return fallback_root


def resolve_path(relative_path: str, base_path: Optional[Path] = None) -> Path:
    """
    Resolve a relative path relative to project root or specified base path.
    
    Args:
        relative_path: Relative path string (e.g., "model_pack/data.csv")
        base_path: Base path for resolution (defaults to project root)
    
    Returns:
        Resolved absolute Path
    """
    if base_path is None:
        base_path = find_project_root()
    
    # Handle absolute paths
    if os.path.isabs(relative_path):
        return Path(relative_path)
    
    # Resolve relative to base path
    resolved = (base_path / relative_path).resolve()
    
    # Security: Ensure resolved path is within base path (prevent directory traversal)
    try:
        resolved.relative_to(base_path.resolve())
    except ValueError:
        raise ValueError(f"Path {relative_path} resolves outside project root: {resolved}")
    
    return resolved


def find_data_file(filename: str, search_dirs: Optional[List[str]] = None, 
                   base_path: Optional[Path] = None) -> Optional[Path]:
    """
    Find a data file by searching in common directories.
    
    Args:
        filename: Name of the file to find
        search_dirs: List of directories to search (defaults to common data directories)
        base_path: Base path for search (defaults to project root)
    
    Returns:
        Path to file if found, None otherwise
    """
    if base_path is None:
        base_path = find_project_root()
    
    if search_dirs is None:
        search_dirs = [
            "model_pack",
            "starter_pack/data",
            "model_pack/data",
            "data"
        ]
    
    for search_dir in search_dirs:
        search_path = base_path / search_dir / filename
        if search_path.exists():
            logger.debug(f"Found {filename} at {search_path}")
            return search_path
    
    logger.warning(f"Could not find {filename} in search directories: {search_dirs}")
    return None


def get_training_data_file(base_path: Optional[Path] = None) -> Path:
    """
    Get the training data file path, preferring updated_training_data.csv over training_data.csv.
    
    Args:
        base_path: Base path for search (defaults to project root)
    
    Returns:
        Path to training data file
    
    Raises:
        FileNotFoundError: If neither training data file is found
    """
    if base_path is None:
        base_path = find_project_root()
    
    # Try updated_training_data.csv first
    updated_path = base_path / "model_pack" / "updated_training_data.csv"
    if updated_path.exists():
        return updated_path
    
    # Fallback to training_data.csv
    training_path = base_path / "model_pack" / "training_data.csv"
    if training_path.exists():
        logger.info(f"Using fallback training_data.csv (updated_training_data.csv not found)")
        return training_path
    
    raise FileNotFoundError(
        f"Could not find training data file. Searched:\n"
        f"  - {updated_path}\n"
        f"  - {training_path}"
    )


def ensure_directory_exists(path: Path) -> Path:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Path to directory
    
    Returns:
        Path to directory (created if necessary)
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_output_directory(subdirectory: Optional[str] = None, 
                        base_path: Optional[Path] = None) -> Path:
    """
    Get the output directory path, creating it if necessary.
    
    Args:
        subdirectory: Optional subdirectory within model_pack
        base_path: Base path for resolution (defaults to project root)
    
    Returns:
        Path to output directory
    """
    if base_path is None:
        base_path = find_project_root()
    
    output_dir = base_path / "model_pack"
    if subdirectory:
        output_dir = output_dir / subdirectory
    
    return ensure_directory_exists(output_dir)


def validate_file_exists(file_path: Path, description: str = "File") -> Path:
    """
    Validate that a file exists, raising a helpful error if not.
    
    Args:
        file_path: Path to file
        description: Description of file for error message
    
    Returns:
        Path to file if it exists
    
    Raises:
        FileNotFoundError: If file does not exist
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(
            f"{description} not found: {file_path}\n"
            f"Current working directory: {os.getcwd()}\n"
            f"Project root: {find_project_root()}"
        )
    return file_path

