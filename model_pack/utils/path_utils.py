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


def get_weekly_training_file(week: int, season: int = 2025, base_path: Optional[Path] = None) -> Path:
    """
    Get weekly training data file path with fallback search.
    
    This function searches for weekly training files in multiple locations
    to support migration from root-level files to organized directory structure.
    It searches in order of preference:
    1. data/training/weekly/ (canonical location)
    2. data/weekly_training/ (legacy location)
    3. Root level (temporary, during migration)
    
    Args:
        week: Week number (1-16)
        season: Season year (default: 2025)
        base_path: Base path for search (defaults to project root)
    
    Returns:
        Path to weekly training file
    
    Raises:
        FileNotFoundError: If file not found in any location
    
    Example:
        >>> path = get_weekly_training_file(week=12, season=2025)
        >>> df = pd.read_csv(path)
    """
    if base_path is None:
        base_path = find_project_root()
    
    filename = f"training_data_{season}_week{week:02d}.csv"
    
    # Search order: canonical location first
    locations = [
        ("data/training/weekly", "canonical"),  # Canonical location
        ("data/weekly_training", "legacy"),      # Legacy location
        ("", "root")                             # Root level (temporary)
    ]
    
    for rel_dir, location_type in locations:
        if rel_dir:
            search_path = base_path / rel_dir / filename
        else:
            search_path = base_path / filename
        
        if search_path.exists():
            if location_type == "canonical":
                logger.debug(f"Found weekly training file (canonical): {search_path}")
            else:
                logger.warning(
                    f"Using {location_type} location for weekly training file: {search_path}. "
                    f"Consider migrating to data/training/weekly/ for better organization."
                )
            return search_path
    
    # File not found in any location
    searched_paths = [
        str(base_path / "data" / "training" / "weekly" / filename),
        str(base_path / "data" / "weekly_training" / filename),
        str(base_path / filename)
    ]
    
    raise FileNotFoundError(
        f"Weekly training file for week {week} (season {season}) not found. "
        f"Searched locations:\n" + "\n".join(f"  - {path}" for path in searched_paths)
    )


def get_weekly_enhanced_dir(week: int, season: int = 2025, base_path: Optional[Path] = None) -> Path:
    """
    Get weekly enhanced data directory path with fallback support.
    
    This function returns the canonical directory path for weekly enhanced data,
    supporting fallback to legacy locations during migration.
    Canonical location: data/weekly/week{XX:02d}/enhanced/
    Legacy location: data/week{XX}/enhanced/
    
    Args:
        week: Week number (1-16)
        season: Season year (default: 2025)
        base_path: Base path for resolution (defaults to project root)
    
    Returns:
        Path to weekly enhanced data directory
    
    Example:
        >>> dir_path = get_weekly_enhanced_dir(week=13, season=2025)
        >>> # Returns: Path("data/weekly/week13/enhanced")
    """
    if base_path is None:
        base_path = find_project_root()
    
    # Canonical location
    canonical_dir = base_path / "data" / "weekly" / f"week{week:02d}" / "enhanced"
    return canonical_dir


def get_weekly_enhanced_file(week: int, file_type: str, season: int = 2025, 
                             base_path: Optional[Path] = None) -> Path:
    """
    Get weekly enhanced data file path with fallback search.
    
    This function searches for weekly enhanced files in multiple locations
    to support migration from legacy paths to canonical directory structure.
    It searches in order of preference:
    1. data/weekly/week{XX:02d}/enhanced/ (canonical location)
    2. data/week{XX}/enhanced/ (legacy location)
    
    Args:
        week: Week number (1-16)
        file_type: Type of file - 'features', 'games', or 'metadata'
        season: Season year (default: 2025)
        base_path: Base path for search (defaults to project root)
    
    Returns:
        Path to weekly enhanced file
    
    Raises:
        FileNotFoundError: If file not found in any location
        ValueError: If file_type is not recognized
    
    Example:
        >>> path = get_weekly_enhanced_file(week=13, file_type='features')
        >>> # Returns: Path("data/weekly/week13/enhanced/week13_features_86.csv")
        >>> df = pd.read_csv(path)
    """
    if base_path is None:
        base_path = find_project_root()
    
    # Map file types to filenames
    filename_map = {
        'features': f"week{week}_features_86.csv",
        'games': f"week{week}_enhanced_games.csv",
        'metadata': "enhancement_metadata.json"
    }
    
    if file_type not in filename_map:
        raise ValueError(
            f"Invalid file_type: {file_type}. Must be one of: {list(filename_map.keys())}"
        )
    
    filename = filename_map[file_type]
    
    # Search order: canonical location first
    locations = [
        ("data/weekly", f"week{week:02d}/enhanced", "canonical"),  # Canonical location
        ("data", f"week{week}/enhanced", "legacy"),                # Legacy location
    ]
    
    for base_dir, subdir, location_type in locations:
        search_path = base_path / base_dir / subdir / filename
        if search_path.exists():
            if location_type == "canonical":
                logger.debug(f"Found weekly enhanced file (canonical): {search_path}")
            else:
                logger.warning(
                    f"Using {location_type} location for weekly enhanced file: {search_path}. "
                    f"Consider migrating to data/weekly/week{week:02d}/enhanced/ for better organization."
                )
            return search_path
    
    # File not found in any location
    searched_paths = [
        str(base_path / "data" / "weekly" / f"week{week:02d}" / "enhanced" / filename),
        str(base_path / "data" / f"week{week}" / "enhanced" / filename),
    ]
    
    raise FileNotFoundError(
        f"Weekly enhanced {file_type} file for week {week} (season {season}) not found. "
        f"Searched locations:\n" + "\n".join(f"  - {path}" for path in searched_paths)
    )


def get_master_training_data_path(base_path: Optional[Path] = None) -> Path:
    """
    Get master training data file path with fallback support.
    
    This function returns the canonical path for master training data,
    supporting fallback to legacy filename during migration.
    Canonical location: model_pack/updated_training_data.csv
    Legacy location: model_pack/training_data.csv
    
    Args:
        base_path: Base path for search (defaults to project root)
    
    Returns:
        Path to master training data file
    
    Raises:
        FileNotFoundError: If neither training data file is found
    
    Note:
        This is an alias for get_training_data_file() for consistency.
        Both functions can be used interchangeably.
    
    Example:
        >>> path = get_master_training_data_path()
        >>> df = pd.read_csv(path)
    """
    return get_training_data_file(base_path)


def get_model_file_path(model_name: str, base_path: Optional[Path] = None) -> Path:
    """
    Get model file path.
    
    This function returns the canonical path for model files in model_pack/.
    
    Args:
        model_name: Name of model file (e.g., 'ridge_model_2025.joblib')
        base_path: Base path for resolution (defaults to project root)
    
    Returns:
        Path to model file
    
    Raises:
        FileNotFoundError: If model file does not exist
    
    Example:
        >>> path = get_model_file_path('ridge_model_2025.joblib')
        >>> model = joblib.load(path)
    """
    if base_path is None:
        base_path = find_project_root()
    
    model_path = base_path / "model_pack" / model_name
    
    if not model_path.exists():
        raise FileNotFoundError(
            f"Model file not found: {model_path}\n"
            f"Current working directory: {os.getcwd()}\n"
            f"Project root: {base_path}"
        )
    
    logger.debug(f"Found model file: {model_path}")
    return model_path

