"""
Test suite for CFBDDataValidator.
"""

import pytest
import pandas as pd
import numpy as np
from validation.cfbd_data_validator import CFBDDataValidator, ValidationResult

class TestCFBDDataValidator:
    """Test cases for CFBDDataValidator"""
    
    @pytest.fixture
    def validator(self):
        return CFBDDataValidator()
    
    def test_validate_valid_dataframe(self, validator):
        """Test validation of valid data"""
        df = pd.DataFrame([{
            'season': 2025,
            'week': 12,
            'home_team': 'Ohio State',
            'away_team': 'Michigan',
            'home_points': 42,
            'away_points': 27,
            'margin': 15,
            'spread': -14.5,
            'home_talent': 900,
            'away_talent': 850
        }])
        
        result = validator.validate_dataframe(df)
        assert result.is_valid
        assert not result.errors
    
    def test_validate_missing_features(self, validator):
        """Test detection of missing features"""
        df = pd.DataFrame([{
            'season': 2025,
            # Missing week, home_team etc
        }])
        
        result = validator.validate_dataframe(df)
        # Should have errors about missing features
        assert not result.is_valid
        assert any("Missing required features" in e for e in result.errors)
    
    def test_validate_invalid_ranges(self, validator):
        """Test detection of invalid ranges"""
        df = pd.DataFrame([{
            'season': 1900, # Invalid
            'week': 20, # Invalid
            'home_team': 'A', 'away_team': 'B',
            'home_points': 0, 'away_points': 0, 'margin': 0,
            'spread': 0, 'home_talent': 0, 'away_talent': 0
        }])
        
        result = validator.validate_dataframe(df)
        # Should have invalid range errors
        assert not result.is_valid
        assert any("season" in e for e in result.invalid_ranges)
        assert any("week" in e for e in result.invalid_ranges)

    def test_inconsistent_margin(self, validator):
        """Test detection of inconsistent margin"""
        df = pd.DataFrame([{
            'season': 2025, 'week': 1,
            'home_team': 'A', 'away_team': 'B',
            'home_points': 10,
            'away_points': 0,
            'margin': 5, # Wrong, should be 10
            'spread': 0, 'home_talent': 0, 'away_talent': 0
        }])
        
        result = validator.validate_dataframe(df)
        # Should warn
        assert any("inconsistent margin" in w for w in result.warnings)
        
    def test_fix_data_issues(self, validator):
        """Test fixing data issues"""
        df = pd.DataFrame([{
            'season': 2025, 'week': 1,
            'home_team': 'A', 'away_team': 'B',
            'home_points': 10,
            'away_points': 0,
            'margin': 5, # Wrong
            'spread': 0, 'home_talent': 0, 'away_talent': 0
        }])
        
        fixed_df, result = validator.fix_data_issues(df)
        
        assert fixed_df.iloc[0]['margin'] == 10
        assert result.is_valid

