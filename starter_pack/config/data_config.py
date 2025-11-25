#!/usr/bin/env python3
"""
Starter Pack Data Configuration for Script Ohio 2.0

Configuration for starter pack notebooks including data directory resolution
and dynamic year detection for examples.
"""

import os
import logging
from datetime import date
from dataclasses import dataclass
from typing import Optional
from pathlib import Path
import sys

# Import model pack config for shared functionality
_model_pack_config_dir = Path(__file__).parent.parent.parent / "model_pack" / "config"
if str(_model_pack_config_dir.parent) not in sys.path:
    sys.path.insert(0, str(_model_pack_config_dir.parent))

# Import path utilities for weekly training files
_model_pack_utils_dir = Path(__file__).parent.parent.parent / "model_pack" / "utils"
if str(_model_pack_utils_dir.parent) not in sys.path:
    sys.path.insert(0, str(_model_pack_utils_dir.parent))

try:
    from model_pack.config.data_config import get_data_config as get_model_pack_config
    _model_pack_config = get_model_pack_config()
except ImportError:
    # Fallback if model pack config not available
    _model_pack_config = None

try:
    from model_pack.utils.path_utils import get_weekly_training_file
except ImportError:
    # Fallback if path utils not available
    get_weekly_training_file = None

logger = logging.getLogger(__name__)


@dataclass
class StarterPackDataConfig:
    """Configuration for starter pack notebooks"""
    
    # Data directory
    data_dir: Optional[Path] = None
    
    # Current year for examples (defaults to current season from model pack config)
    current_year: Optional[int] = None
    
    # Project root
    project_root: Optional[Path] = None
    
    def __post_init__(self):
        """Initialize configuration"""
        # Get project root
        if self.project_root is None:
            # Try to find project root by looking for marker files
            current = Path(__file__).resolve().parent.parent.parent
            for parent in [current] + list(current.parents):
                if (parent / "AGENTS.md").exists() or (parent / "README.md").exists():
                    self.project_root = parent
                    break
            
            if self.project_root is None:
                self.project_root = current
        
        # Set data directory
        if self.data_dir is None:
            self.data_dir = self.project_root / "starter_pack" / "data"
        
        # Get current year from model pack config or auto-detect
        if self.current_year is None:
            if _model_pack_config:
                self.current_year = _model_pack_config.get_season()
            else:
                # Fallback: detect from current date
                today = date.today()
                if today.month < 8:
                    self.current_year = today.year - 1
                else:
                    self.current_year = today.year
        
        # Allow environment variable override
        if os.environ.get("STARTER_PACK_CURRENT_YEAR"):
            self.current_year = int(os.environ["STARTER_PACK_CURRENT_YEAR"])
    
    def get_data_path(self, filename: str) -> Path:
        """Get path to a data file in the starter pack data directory"""
        return self.data_dir / filename
    
    def get_plays_path(self, year: Optional[int] = None, season_type: str = "regular", week: Optional[int] = None) -> Path:
        """
        Get path to plays data file.
        
        Args:
            year: Year (defaults to current year)
            season_type: 'regular' or 'postseason'
            week: Week number (for regular season)
        
        Returns:
            Path to plays file
        """
        if year is None:
            year = self.current_year
        
        if season_type == "regular" and week is not None:
            return self.data_dir / "plays" / str(year) / f"week_{week}_plays.csv"
        elif season_type == "postseason":
            return self.data_dir / "plays" / str(year) / f"postseason_1_plays.csv"
        else:
            # Fallback to general plays directory
            return self.data_dir / "plays" / str(year)
    
    def get_drives_path(self, year: Optional[int] = None) -> Path:
        """Get path to drives data file"""
        if year is None:
            year = self.current_year
        return self.data_dir / "drives" / f"drives_{year}.csv"
    
    def get_advanced_stats_path(self, year: Optional[int] = None) -> Path:
        """Get path to advanced season stats file"""
        if year is None:
            year = self.current_year
        return self.data_dir / "advanced_season_stats" / f"{year}.csv"
    
    def get_weekly_training_file(self, week: int, season: int = 2025) -> Path:
        """
        Get weekly training data file path using path utility.
        
        This method provides access to weekly training files with automatic
        fallback support for multiple file locations (canonical, legacy, root).
        
        Args:
            week: Week number (1-16)
            season: Season year (default: 2025)
        
        Returns:
            Path to weekly training file
        
        Raises:
            FileNotFoundError: If file not found in any location
            ImportError: If path utility is not available
        
        Example:
            >>> config = get_starter_pack_config()
            >>> weekly_path = config.get_weekly_training_file(week=1, season=2025)
            >>> df = pd.read_csv(weekly_path)
        """
        if get_weekly_training_file is None:
            raise ImportError(
                "get_weekly_training_file utility not available. "
                "Ensure model_pack.utils.path_utils is accessible."
            )
        return get_weekly_training_file(week=week, season=season, base_path=self.project_root)


# Global config instance
_starter_pack_config: Optional[StarterPackDataConfig] = None


def get_starter_pack_config() -> StarterPackDataConfig:
    """Get the global starter pack configuration instance"""
    global _starter_pack_config
    if _starter_pack_config is None:
        _starter_pack_config = StarterPackDataConfig()
    return _starter_pack_config


def reset_starter_pack_config():
    """Reset the global starter pack configuration (useful for testing)"""
    global _starter_pack_config
    _starter_pack_config = None

