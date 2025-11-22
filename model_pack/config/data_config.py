#!/usr/bin/env python3
"""
Data Configuration for Script Ohio 2.0

Centralized configuration for data-related settings including dynamic season/week
detection, file path resolution, and data source configuration.
"""

import os
import logging
from datetime import date, datetime
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from pathlib import Path

# Import utilities
import sys
from pathlib import Path as PathLib
_config_dir = PathLib(__file__).parent
_model_pack_dir = _config_dir.parent
_project_root = _model_pack_dir.parent

# Add to path for imports
if str(_model_pack_dir) not in sys.path:
    sys.path.insert(0, str(_model_pack_dir))
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from model_pack.utils.path_utils import find_project_root, resolve_path, get_training_data_file
from model_pack.config.fallback_config import get_fallback_config

# Import week calculation function
try:
    from agents.simplified.game_data_loader import calculate_current_week
except ImportError:
    # Fallback implementation if import fails
    def calculate_current_week(season: Optional[int] = None) -> int:
        """Calculate current week of college football season"""
        if season is None:
            season = date.today().year
        today = date.today()
        season_start = date(season, 8, 24)
        season_end = date(season, 12, 7)
        
        if today < season_start:
            return 1
        if today > season_end:
            return 16
        
        days_since_start = (today - season_start).days
        weeks_since_start = (days_since_start // 7) + 1
        return max(1, min(weeks_since_start, 16))

logger = logging.getLogger(__name__)


@dataclass
class DataConfig:
    """Configuration for data loading and processing"""
    
    # Season configuration
    current_season: Optional[int] = None
    historical_start_year: int = 2016
    
    # Week configuration
    current_week: Optional[int] = None
    max_week: int = 16
    
    # File paths (will be resolved dynamically)
    project_root: Optional[Path] = None
    model_pack_dir: Optional[Path] = None
    starter_pack_dir: Optional[Path] = None
    training_data_file: Optional[Path] = None
    
    # Data source configuration
    data_source: str = "csv"  # Options: "csv", "api", "hybrid"
    prefer_updated_training_data: bool = True
    
    # FBS conferences
    fbs_conferences: List[str] = field(default_factory=lambda: [
        'ACC', 'Big 12', 'Big Ten', 'SEC', 'Pac-12',
        'American', 'C-USA', 'MAC', 'Mountain West', 'Sun Belt'
    ])
    
    # Output configuration
    output_dir: Optional[Path] = None
    
    # Fallback configuration
    fallback_config: Any = field(default_factory=get_fallback_config)
    
    # Caching
    _season_cache: Optional[int] = None
    _week_cache: Optional[int] = None
    
    def __post_init__(self):
        """Initialize configuration with environment variable overrides"""
        # Get project root
        if self.project_root is None:
            self.project_root = find_project_root()
        
        # Resolve directories
        self.model_pack_dir = self.project_root / "model_pack"
        self.starter_pack_dir = self.project_root / "starter_pack"
        
        # Get current season from environment or auto-detect
        if self.current_season is None:
            self.current_season = self._detect_current_season()
        
        # Get current week from environment or auto-calculate
        if self.current_week is None:
            self.current_week = self._calculate_current_week()
        
        # Resolve training data file
        if self.training_data_file is None:
            try:
                self.training_data_file = get_training_data_file(self.project_root)
            except FileNotFoundError:
                logger.warning("Training data file not found, will need to be set manually")
                self.training_data_file = self.model_pack_dir / "updated_training_data.csv"
        
        # Set output directory
        if self.output_dir is None:
            self.output_dir = self.model_pack_dir
        
        # Allow environment variable overrides
        if os.environ.get("CFBD_CURRENT_SEASON"):
            self.current_season = int(os.environ["CFBD_CURRENT_SEASON"])
        if os.environ.get("CFBD_CURRENT_WEEK"):
            self.current_week = int(os.environ["CFBD_CURRENT_WEEK"])
        if os.environ.get("CFBD_DATA_SOURCE"):
            self.data_source = os.environ["CFBD_DATA_SOURCE"]
    
    def _detect_current_season(self) -> int:
        """
        Detect the current college football season.
        
        College football seasons span calendar years (e.g., 2025 season runs Aug 2025 - Jan 2026).
        We consider the "current season" to be the year we're in if it's after August,
        otherwise the previous year.
        """
        today = date.today()
        current_year = today.year
        
        # If we're before August, we're still in the previous season
        if today.month < 8:
            return current_year - 1
        
        return current_year
    
    def _calculate_current_week(self) -> int:
        """Calculate the current week of the season"""
        if self._week_cache is not None:
            return self._week_cache
        
        week = calculate_current_week(self.current_season)
        self._week_cache = week
        return week
    
    def get_season(self) -> int:
        """Get the current season"""
        if self._season_cache is not None:
            return self._season_cache
        
        season = self.current_season
        self._season_cache = season
        return season
    
    def get_week(self) -> int:
        """Get the current week"""
        return self._calculate_current_week()
    
    def get_training_data_path(self) -> Path:
        """Get the path to the training data file"""
        return self.training_data_file
    
    def get_output_path(self, filename: str) -> Path:
        """Get output path for a file"""
        return self.output_dir / filename
    
    def get_starter_pack_data_path(self, relative_path: str) -> Path:
        """Get path to starter pack data file"""
        return self.starter_pack_dir / relative_path
    
    def is_fbs_conference(self, conference: Optional[str]) -> bool:
        """Check if a conference is an FBS conference"""
        if conference is None:
            return False
        return conference in self.fbs_conferences
    
    def get_data_file_path(self, filename: str, year: Optional[int] = None) -> Path:
        """
        Get path to a data file, optionally with year in filename.
        
        Args:
            filename: Base filename (e.g., "games.csv" or "games_{year}.csv")
            year: Optional year to insert into filename
        
        Returns:
            Path to data file
        """
        if year is None:
            year = self.get_season()
        
        # Replace {year} placeholder if present
        if "{year}" in filename:
            filename = filename.format(year=year)
        elif year and filename.endswith(".csv"):
            # Insert year before extension if not already present
            base = filename[:-4]
            if str(year) not in base:
                filename = f"{base}_{year}.csv"
        
        return self.model_pack_dir / filename
    
    def reset_cache(self):
        """Reset cached values (useful for testing or when date changes)"""
        self._season_cache = None
        self._week_cache = None


# Global config instance
_data_config: Optional[DataConfig] = None


def get_data_config() -> DataConfig:
    """Get the global data configuration instance"""
    global _data_config
    if _data_config is None:
        _data_config = DataConfig()
    return _data_config


def reset_data_config():
    """Reset the global data configuration (useful for testing)"""
    global _data_config
    _data_config = None

