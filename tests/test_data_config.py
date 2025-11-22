#!/usr/bin/env python3
"""
Test suite for data configuration system

Validates that the configuration system correctly:
- Detects current season
- Calculates current week
- Resolves file paths
- Provides fallback values
"""

import sys
import os
from pathlib import Path
from datetime import date
import pytest

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "model_pack"))

from config.data_config import get_data_config, reset_data_config, DataConfig
from config.fallback_config import get_fallback_config, reset_fallback_config
from utils.path_utils import find_project_root, get_training_data_file


class TestDataConfig:
    """Test data configuration system"""
    
    def setup_method(self):
        """Reset config before each test"""
        reset_data_config()
        reset_fallback_config()
    
    def test_config_initialization(self):
        """Test that config initializes correctly"""
        config = get_data_config()
        assert config is not None
        assert config.current_season is not None
        assert config.current_week is not None
        assert config.project_root is not None
    
    def test_season_detection(self):
        """Test season detection logic"""
        config = get_data_config()
        current_season = config.get_season()
        
        # Season should be current year if after August, otherwise previous year
        today = date.today()
        expected_season = today.year if today.month >= 8 else today.year - 1
        
        assert current_season == expected_season
    
    def test_week_calculation(self):
        """Test week calculation"""
        config = get_data_config()
        current_week = config.get_week()
        
        # Week should be between 1 and 16
        assert 1 <= current_week <= 16
    
    def test_training_data_path(self):
        """Test training data path resolution"""
        config = get_data_config()
        training_path = config.get_training_data_path()
        
        assert training_path is not None
        assert isinstance(training_path, Path)
        # Path should exist or be in expected location
        assert training_path.parent.exists()
    
    def test_output_path(self):
        """Test output path generation"""
        config = get_data_config()
        output_path = config.get_output_path("test_file.csv")
        
        assert output_path is not None
        assert output_path.name == "test_file.csv"
        assert output_path.parent == config.output_dir
    
    def test_fbs_conference_check(self):
        """Test FBS conference checking"""
        config = get_data_config()
        
        assert config.is_fbs_conference("SEC") == True
        assert config.is_fbs_conference("Big Ten") == True
        assert config.is_fbs_conference("Invalid Conference") == False
        assert config.is_fbs_conference(None) == False


class TestFallbackConfig:
    """Test fallback configuration system"""
    
    def setup_method(self):
        """Reset config before each test"""
        reset_fallback_config()
    
    def test_fallback_initialization(self):
        """Test fallback config initializes"""
        fallback = get_fallback_config()
        assert fallback is not None
        assert fallback.default_elo_rating == 1500.0
        assert fallback.default_talent_rating == 500.0
    
    def test_fallback_values(self):
        """Test fallback value retrieval"""
        fallback = get_fallback_config()
        
        elo = fallback.get_fallback_value('elo')
        talent = fallback.get_fallback_value('talent')
        
        assert elo == 1500.0
        assert talent == 500.0


class TestPathUtils:
    """Test path utility functions"""
    
    def test_project_root_detection(self):
        """Test project root is found"""
        root = find_project_root()
        assert root is not None
        assert root.exists()
        # Should contain key project files
        assert (root / "AGENTS.md").exists() or (root / "README.md").exists()
    
    def test_training_data_file(self):
        """Test training data file resolution"""
        try:
            training_file = get_training_data_file()
            assert training_file is not None
            assert training_file.suffix == ".csv"
        except FileNotFoundError:
            # This is OK if training data doesn't exist yet
            pass


class TestEnvironmentOverrides:
    """Test environment variable overrides"""
    
    def setup_method(self):
        """Reset config before each test"""
        reset_data_config()
        reset_fallback_config()
    
    def test_season_override(self):
        """Test season can be overridden via environment"""
        os.environ["CFBD_CURRENT_SEASON"] = "2024"
        reset_data_config()
        
        config = get_data_config()
        assert config.get_season() == 2024
        
        # Cleanup
        del os.environ["CFBD_CURRENT_SEASON"]
        reset_data_config()
    
    def test_week_override(self):
        """Test week can be overridden via environment"""
        os.environ["CFBD_CURRENT_WEEK"] = "10"
        reset_data_config()
        
        config = get_data_config()
        assert config.get_week() == 10
        
        # Cleanup
        del os.environ["CFBD_CURRENT_WEEK"]
        reset_data_config()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

