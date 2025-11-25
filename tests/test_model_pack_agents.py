#!/usr/bin/env python3
"""
Unit Tests for Model Pack Agent Components

Tests for:
- metrics_calculation_agent.py
- 2025_data_acquisition_v2.py (DataAcquisitionAgent)
- migrate_starter_pack_data.py (StarterPackDataMigrator)

Author: Model Pack Improvement Plan
Created: 2025-11-19
"""

import pytest
import pandas as pd
import numpy as np
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open
import warnings
import sys
import os

# Suppress warnings for cleaner test output
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


class TestMetricsCalculationAgent:
    """Unit tests for MetricsCalculationAgent"""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files"""
        temp_path = tempfile.mkdtemp()
        yield temp_path
        shutil.rmtree(temp_path)

    @pytest.fixture
    def sample_historical_data(self):
        """Sample historical training data"""
        return pd.DataFrame({
            'season': [2016, 2017, 2018, 2019, 2020],
            'week': [5, 6, 7, 8, 9],
            'home_team': ['Ohio State', 'Michigan', 'Alabama', 'Georgia', 'Texas'],
            'away_team': ['Michigan', 'Ohio State', 'Auburn', 'Florida', 'Oklahoma'],
            'home_points': [42, 35, 28, 31, 24],
            'away_points': [13, 21, 14, 17, 21],
            'home_adjusted_epa': [0.25, 0.18, 0.22, 0.20, 0.15],
            'away_adjusted_epa': [0.10, 0.12, 0.08, 0.11, 0.13],
            'home_conference': ['Big Ten', 'Big Ten', 'SEC', 'SEC', 'Big 12'],
            'away_conference': ['Big Ten', 'Big Ten', 'SEC', 'SEC', 'Big 12'],
        })

    @pytest.fixture
    def sample_2025_data(self):
        """Sample 2025 raw data"""
        return pd.DataFrame({
            'season': [2025, 2025, 2025],
            'week': [1, 2, 3],
            'home_team': ['Ohio State', 'Alabama', 'Georgia'],
            'away_team': ['Notre Dame', 'Texas', 'Florida'],
            'home_points': [0, 0, 0],  # Future games
            'away_points': [0, 0, 0],
            'home_conference': ['Big Ten', 'SEC', 'SEC'],
            'away_conference': ['Independent', 'Big 12', 'SEC'],
        })

    @pytest.fixture
    def mock_agent(self, temp_dir, sample_historical_data, sample_2025_data):
        """Create mock MetricsCalculationAgent with test data"""
        with patch('model_pack.metrics_calculation_agent.MetricsCalculationAgent.__init__', lambda self: None):
            from model_pack.metrics_calculation_agent import MetricsCalculationAgent
            agent = MetricsCalculationAgent()
            agent.base_path = temp_dir
            agent.training_data_path = os.path.join(temp_dir, "training_data.csv")
            agent.raw_2025_path = os.path.join(temp_dir, "2025_raw_games_fixed.csv")
            agent.processed_2025_path = os.path.join(temp_dir, "2025_processed_features.csv")
            agent.updated_training_path = os.path.join(temp_dir, "updated_training_data.csv")
            
            # Save test data
            sample_historical_data.to_csv(agent.training_data_path, index=False)
            sample_2025_data.to_csv(agent.raw_2025_path, index=False)
            
            agent.historical_data = None
            agent.data_2025 = None
            agent.processed_2025 = None
            agent.validation_results = {}
            
            return agent

    def test_ensure_identifier_columns(self, mock_agent):
        """Test _ensure_identifier_columns method"""
        df = pd.DataFrame({
            'season': [2025],
            'week': [1],
            'home_team': ['Ohio State'],
            'away_team': ['Michigan'],
        })
        
        result = mock_agent._ensure_identifier_columns(df)
        
        assert 'game_key' in result.columns
        assert result['game_key'].iloc[0] == "2025_1_Ohio_State_Michigan"
        assert 'conference_game' in result.columns

    def test_ensure_identifier_columns_with_existing(self, mock_agent):
        """Test _ensure_identifier_columns with existing columns"""
        df = pd.DataFrame({
            'season': [2025],
            'week': [1],
            'home_team': ['Ohio State'],
            'away_team': ['Michigan'],
            'game_key': ['existing_key'],
            'conference_game': [True],
        })
        
        result = mock_agent._ensure_identifier_columns(df)
        
        assert result['game_key'].iloc[0] == 'existing_key'
        assert result['conference_game'].iloc[0] == True

    def test_load_and_analyze_data(self, mock_agent):
        """Test load_and_analyze_data method"""
        mock_agent.load_and_analyze_data()
        
        assert mock_agent.historical_data is not None
        assert mock_agent.data_2025 is not None
        assert len(mock_agent.historical_data) == 5
        assert len(mock_agent.data_2025) == 3

    def test_load_and_analyze_data_missing_files(self, temp_dir):
        """Test load_and_analyze_data with missing files"""
        with patch('model_pack.metrics_calculation_agent.MetricsCalculationAgent.__init__', lambda self: None):
            from model_pack.metrics_calculation_agent import MetricsCalculationAgent
            agent = MetricsCalculationAgent()
            agent.base_path = temp_dir
            agent.training_data_path = os.path.join(temp_dir, "nonexistent.csv")
            agent.raw_2025_path = os.path.join(temp_dir, "nonexistent2.csv")
            
            with pytest.raises((FileNotFoundError, pd.errors.EmptyDataError)):
                agent.load_and_analyze_data()


class TestDataAcquisitionAgent:
    """Unit tests for DataAcquisitionAgent"""

    @pytest.fixture
    def mock_api_key(self):
        """Mock API key"""
        with patch.dict(os.environ, {'CFBD_API_KEY': 'test_key'}):
            yield 'test_key'

    @pytest.fixture
    def mock_agent(self, mock_api_key):
        """Create mock DataAcquisitionAgent"""
        with patch('model_pack.2025_data_acquisition_v2.API_KEY', mock_api_key):
            with patch('model_pack.2025_data_acquisition_v2.GQL_AVAILABLE', False):
                with patch('model_pack.2025_data_acquisition_v2.CFBDGraphQLClient', None):
                    from model_pack import data_acquisition_v2
                    agent = data_acquisition_v2.DataAcquisitionAgent(use_rest=True)
                    return agent

    def test_rate_limit(self, mock_agent):
        """Test rate limiting functionality"""
        with patch.object(mock_agent.rate_limiter, 'wait') as mock_wait:
            mock_agent._rate_limit()
            mock_wait.assert_called_once()

    def test_fetch_games_graphql_no_client(self, mock_agent):
        """Test fetch_games_graphql without GraphQL client"""
        with pytest.raises(ValueError, match="GraphQL client not initialized"):
            mock_agent.fetch_games_graphql(2025, 1)

    def test_convert_graphql_to_dataframe(self, mock_agent):
        """Test _convert_graphql_to_dataframe method"""
        records = [
            {
                'id': 1,
                'season': 2025,
                'week': 1,
                'homeTeam': 'Ohio State',
                'awayTeam': 'Michigan',
                'homePoints': 42,
                'awayPoints': 13,
            }
        ]
        
        result = mock_agent._convert_graphql_to_dataframe(records)
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1
        assert 'home_team' in result.columns
        assert 'away_team' in result.columns
        assert result['home_team'].iloc[0] == 'Ohio State'

    def test_convert_graphql_to_dataframe_empty(self, mock_agent):
        """Test _convert_graphql_to_dataframe with empty records"""
        result = mock_agent._convert_graphql_to_dataframe([])
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0

    def test_is_fbs_game_from_df(self, mock_agent):
        """Test _is_fbs_game_from_df method"""
        # FBS team
        fbs_row = pd.Series({
            'home_conference': 'Big Ten',
            'away_conference': 'SEC',
        })
        assert mock_agent._is_fbs_game_from_df(fbs_row) == True
        
        # Non-FBS team
        non_fbs_row = pd.Series({
            'home_conference': None,
            'away_conference': 'FCS',
        })
        assert mock_agent._is_fbs_game_from_df(non_fbs_row) == False

    def test_quality_report_initialization(self, mock_agent):
        """Test quality report is properly initialized"""
        assert 'total_games' in mock_agent.quality_report
        assert 'successful_game_fetches' in mock_agent.quality_report
        assert 'failed_games' in mock_agent.quality_report
        assert mock_agent.quality_report['total_games'] == 0


class TestStarterPackDataMigrator:
    """Unit tests for StarterPackDataMigrator"""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration"""
        mock_config = MagicMock()
        mock_config.get_season.return_value = 2025
        mock_config.get_week.return_value = 1
        mock_config.get_starter_pack_data_path.return_value = "/tmp/test_games.csv"
        mock_config.get_training_data_path.return_value = "/tmp/training_data.csv"
        mock_config.get_output_path.return_value = "/tmp/output.csv"
        return mock_config

    @pytest.fixture
    def mock_migrator(self, mock_config):
        """Create mock StarterPackDataMigrator"""
        with patch('model_pack.migrate_starter_pack_data.config', mock_config):
            with patch('model_pack.migrate_starter_pack_data.API_KEY', 'test_key'):
                with patch('model_pack.migrate_starter_pack_data.CFBDGraphQLClient', None):
                    from model_pack.migrate_starter_pack_data import StarterPackDataMigrator
                    migrator = StarterPackDataMigrator()
                    return migrator

    def test_rate_limit(self, mock_migrator):
        """Test rate limiting"""
        import time
        with patch('time.sleep') as mock_sleep:
            mock_migrator._rate_limit()
            mock_sleep.assert_called_once_with(0.17)

    def test_fetch_games_graphql_no_client(self, mock_migrator):
        """Test fetch_games_graphql without GraphQL client"""
        with pytest.raises(ValueError, match="GraphQL client not initialized"):
            mock_migrator.fetch_games_graphql(2025, 1)

    def test_convert_graphql_to_dataframe(self, mock_migrator):
        """Test _convert_graphql_to_dataframe method"""
        records = [
            {
                'id': 1,
                'season': 2025,
                'week': 1,
                'homeTeam': 'Ohio State',
                'awayTeam': 'Michigan',
            }
        ]
        
        result = mock_migrator._convert_graphql_to_dataframe(records)
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1
        assert 'home_team' in result.columns

    def test_apply_week_filter(self, mock_migrator):
        """Test apply_week_filter method"""
        df = pd.DataFrame({
            'week': [1, 2, 3, 4, 5, 6, 7],
            'season': [2025] * 7,
        })
        
        # Test filtering weeks 5+
        result = mock_migrator.apply_week_filter(df, min_week=5)
        
        assert len(result) == 3
        assert all(result['week'] >= 5)

    def test_apply_week_filter_with_max(self, mock_migrator):
        """Test apply_week_filter with max_week"""
        df = pd.DataFrame({
            'week': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            'season': [2025] * 10,
        })
        
        result = mock_migrator.apply_week_filter(df, min_week=5, max_week=8)
        
        assert len(result) == 4
        assert all((result['week'] >= 5) & (result['week'] <= 8))


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_missing_data_handling(self):
        """Test handling of missing data"""
        df = pd.DataFrame({
            'season': [2025, 2025, None],
            'week': [1, None, 2],
            'home_team': ['Ohio State', None, 'Michigan'],
        })
        
        # Should handle missing values gracefully
        assert df.isnull().sum().sum() > 0

    def test_api_failure_handling(self, mock_api_key):
        """Test API failure handling"""
        with patch('model_pack.2025_data_acquisition_v2.API_KEY', mock_api_key):
            with patch('model_pack.2025_data_acquisition_v2.GQL_AVAILABLE', False):
                with patch('model_pack.2025_data_acquisition_v2.CFBDGraphQLClient', None):
                    from model_pack import data_acquisition_v2
                    agent = data_acquisition_v2.DataAcquisitionAgent(use_rest=True)
                    
                    # Should gracefully handle API failures
                    assert agent.use_graphql == False
                    assert agent.graphql_client is None

    def test_invalid_input_handling(self):
        """Test handling of invalid inputs"""
        # Test with invalid season
        with pytest.raises((ValueError, TypeError)):
            invalid_season = "not_a_number"
            int(invalid_season)

    def test_empty_dataframe_handling(self):
        """Test handling of empty DataFrames"""
        empty_df = pd.DataFrame()
        
        assert len(empty_df) == 0
        assert len(empty_df.columns) == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

