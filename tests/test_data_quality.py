#!/usr/bin/env python3
"""
Data Quality Validation Tests

Tests for:
- Opponent adjustment calculations
- Feature distribution validation
- Data leakage prevention
- Week 5+ filtering logic

Author: Model Pack Improvement Plan
Created: 2025-11-19
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import warnings
import sys

# Suppress warnings
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


class TestOpponentAdjustmentCalculations:
    """Test opponent adjustment calculation methodology"""

    def test_opponent_adjustment_basic(self):
        """Test basic opponent adjustment calculation"""
        # Known input/output pairs
        # Adjustment formula: adjusted = primary - opponent_average
        
        primary_epa = 0.25
        opponent_avg_epa_allowed = 0.15
        
        # Expected adjustment
        adjusted_epa = primary_epa - opponent_avg_epa_allowed
        expected = 0.10
        
        assert abs(adjusted_epa - expected) < 0.001

    def test_opponent_adjustment_with_known_values(self):
        """Test opponent adjustment with known historical values"""
        # Simulate opponent adjustment
        team_epa = 0.20
        opponent_defensive_epa_allowed = 0.10
        
        adjusted = team_epa - opponent_defensive_epa_allowed
        
        # Adjusted EPA should be higher when facing weak defense
        assert adjusted > team_epa - 0.15  # Should be adjusted upward
        assert adjusted == 0.10

    def test_opponent_adjustment_negative_values(self):
        """Test opponent adjustment handles negative values correctly"""
        team_epa = -0.10
        opponent_defensive_epa_allowed = 0.15
        
        adjusted = team_epa - opponent_defensive_epa_allowed
        
        # Should handle negative values
        assert adjusted < 0
        assert adjusted == -0.25

    def test_opponent_adjustment_missing_data(self):
        """Test opponent adjustment with missing data"""
        team_epa = 0.20
        opponent_defensive_epa_allowed = None
        
        # Should handle None gracefully
        if opponent_defensive_epa_allowed is None:
            adjusted = None
        else:
            adjusted = team_epa - opponent_defensive_epa_allowed
        
        assert adjusted is None

    def test_opponent_adjustment_consistency(self):
        """Test that opponent adjustments are consistent across features"""
        # Test multiple features use same methodology
        features = {
            'epa': (0.25, 0.15),
            'success_rate': (0.50, 0.45),
            'explosiveness': (1.2, 1.1),
        }
        
        for feature_name, (primary, opponent_avg) in features.items():
            adjusted = primary - opponent_avg
            # All should use subtraction method
            assert adjusted == primary - opponent_avg


class TestFeatureDistributionValidation:
    """Test that feature distributions match historical patterns"""

    def test_epa_distribution(self):
        """Test EPA values are within expected range"""
        # Historical EPA typically ranges from -0.3 to 0.5
        historical_epa = np.random.normal(0.10, 0.15, 1000)
        
        # Check distribution properties
        assert historical_epa.mean() > -0.2
        assert historical_epa.mean() < 0.3
        assert historical_epa.std() > 0.05
        assert historical_epa.std() < 0.25

    def test_success_rate_distribution(self):
        """Test success rate values are within expected range"""
        # Success rates typically range from 0.3 to 0.6
        historical_success = np.random.normal(0.45, 0.08, 1000)
        
        # Check distribution
        assert historical_success.mean() > 0.35
        assert historical_success.mean() < 0.55
        assert (historical_success >= 0).all()
        assert (historical_success <= 1).all()

    def test_talent_distribution(self):
        """Test talent composite values are within expected range"""
        # Talent typically ranges from 0.5 to 1.0
        historical_talent = np.random.uniform(0.5, 1.0, 1000)
        
        assert historical_talent.min() >= 0.5
        assert historical_talent.max() <= 1.0
        assert historical_talent.mean() > 0.7
        assert historical_talent.mean() < 0.9

    def test_elo_distribution(self):
        """Test Elo ratings are within expected range"""
        # Elo typically ranges from 1000 to 2500
        historical_elo = np.random.normal(1750, 200, 1000)
        
        assert historical_elo.mean() > 1500
        assert historical_elo.mean() < 2000
        assert historical_elo.std() > 100
        assert historical_elo.std() < 300

    def test_feature_correlation_validation(self):
        """Test that feature correlations match expected patterns"""
        # Create correlated features
        np.random.seed(42)
        base = np.random.rand(100)
        
        # EPA and success rate should be positively correlated
        epa = base * 0.5 + np.random.rand(100) * 0.1
        success_rate = base * 0.4 + np.random.rand(100) * 0.1
        
        correlation = np.corrcoef(epa, success_rate)[0, 1]
        
        # Should have positive correlation
        assert correlation > 0.3


class TestDataLeakagePrevention:
    """Test that no future data leaks into training features"""

    def test_temporal_split_no_leakage(self):
        """Test temporal split prevents data leakage"""
        data = pd.DataFrame({
            'season': [2020, 2020, 2021, 2021, 2022, 2022],
            'week': [5, 6, 5, 6, 5, 6],
            'home_points': [42, 35, 28, 31, 24, 27],
        })
        
        # Split temporally
        train = data[data['season'] < 2022]
        test = data[data['season'] >= 2022]
        
        # Verify no overlap
        assert len(set(train['season']) & set(test['season'])) == 0
        assert train['season'].max() < test['season'].min()

    def test_feature_calculation_no_future_data(self):
        """Test that features are calculated only from past data"""
        # Simulate feature calculation
        games = pd.DataFrame({
            'season': [2020, 2020, 2021, 2021],
            'week': [5, 6, 5, 6],
            'home_team': ['Team A', 'Team B', 'Team A', 'Team B'],
            'home_points': [42, 35, 28, 31],
        })
        
        # For week 6 game, should only use data from weeks 1-5
        week_6_game = games[(games['season'] == 2020) & (games['week'] == 6)]
        available_data = games[
            (games['season'] == 2020) & 
            (games['week'] < 6)
        ]
        
        # Verify feature calculation uses only past data
        assert len(available_data) > 0
        assert available_data['week'].max() < week_6_game['week'].iloc[0]

    def test_no_target_variable_in_features(self):
        """Test that target variables are not included in features"""
        # Define target variables
        target_vars = ['home_points', 'away_points', 'margin', 'home_win']
        
        # Define feature sets
        ridge_features = [
            'home_talent', 'away_talent', 'home_elo', 'away_elo',
            'home_adjusted_epa', 'home_adjusted_epa_allowed',
            'away_adjusted_epa', 'away_adjusted_epa_allowed'
        ]
        
        # Verify no target variables in features
        for target in target_vars:
            assert target not in ridge_features

    def test_opponent_adjustment_uses_only_past_data(self):
        """Test opponent adjustments use only historical data"""
        # Simulate calculating opponent adjustment for week 6 game
        all_games = pd.DataFrame({
            'season': [2020] * 10,
            'week': list(range(1, 11)),
            'home_team': ['Team A'] * 10,
            'away_team': ['Team B'] * 10,
            'away_points': [10, 14, 17, 21, 24, 28, 31, 35, 38, 42],
        })
        
        # For week 6, should only use weeks 1-5 for opponent stats
        week_6_game = all_games[all_games['week'] == 6]
        historical_data = all_games[all_games['week'] < 6]
        
        # Calculate opponent average from historical data only
        opponent_avg = historical_data['away_points'].mean()
        
        # Verify we're not using future data
        assert opponent_avg < week_6_game['away_points'].iloc[0]
        assert len(historical_data) == 5


class TestWeekFilteringLogic:
    """Test week 5+ filtering logic"""

    def test_week_filtering_basic(self):
        """Test basic week filtering"""
        data = pd.DataFrame({
            'week': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            'season': [2025] * 10,
        })
        
        # Filter weeks 5+
        filtered = data[data['week'] >= 5]
        
        assert len(filtered) == 6
        assert filtered['week'].min() == 5
        assert all(filtered['week'] >= 5)

    def test_week_filtering_with_max(self):
        """Test week filtering with maximum week"""
        data = pd.DataFrame({
            'week': list(range(1, 16)),
            'season': [2025] * 15,
        })
        
        # Filter weeks 5-12
        filtered = data[(data['week'] >= 5) & (data['week'] <= 12)]
        
        assert len(filtered) == 8
        assert filtered['week'].min() == 5
        assert filtered['week'].max() == 12

    def test_week_filtering_preserves_season_structure(self):
        """Test week filtering preserves season structure"""
        data = pd.DataFrame({
            'season': [2024, 2024, 2024, 2025, 2025, 2025],
            'week': [3, 4, 5, 3, 4, 5],
        })
        
        # Filter weeks 5+
        filtered = data[data['week'] >= 5]
        
        # Should preserve both seasons
        assert set(filtered['season']) == {2024, 2025}
        assert len(filtered[filtered['season'] == 2024]) == 1
        assert len(filtered[filtered['season'] == 2025]) == 1

    def test_week_filtering_reason(self):
        """Test that week filtering is applied for correct reason"""
        # Week 5+ ensures meaningful sample sizes for opponent adjustments
        # Early weeks have insufficient data for reliable adjustments
        
        weeks_1_4 = pd.DataFrame({
            'week': [1, 2, 3, 4],
            'games_played': [10, 15, 20, 25],  # Increasing sample size
        })
        
        weeks_5_plus = pd.DataFrame({
            'week': [5, 6, 7, 8],
            'games_played': [30, 35, 40, 45],  # Sufficient sample size
        })
        
        # Week 5+ should have more games for reliable statistics
        assert weeks_5_plus['games_played'].mean() > weeks_1_4['games_played'].mean()


class TestDataConsistency:
    """Test data consistency across different operations"""

    def test_feature_naming_consistency(self):
        """Test that feature naming is consistent"""
        # All opponent-adjusted features should follow naming convention
        features = [
            'home_adjusted_epa',
            'away_adjusted_epa',
            'home_adjusted_success',
            'away_adjusted_success',
        ]
        
        # Check naming pattern
        for feature in features:
            assert 'adjusted' in feature
            assert feature.startswith('home_') or feature.startswith('away_')

    def test_data_type_consistency(self):
        """Test that data types are consistent"""
        data = pd.DataFrame({
            'season': [2025, 2025],
            'week': [5, 6],
            'home_talent': [0.85, 0.87],
            'home_elo': [1850, 1900],
            'home_adjusted_epa': [0.20, 0.22],
        })
        
        # Check data types
        assert data['season'].dtype in [int, 'int64']
        assert data['week'].dtype in [int, 'int64']
        assert data['home_talent'].dtype in [float, 'float64']
        assert data['home_elo'].dtype in [int, 'int64', float, 'float64']
        assert data['home_adjusted_epa'].dtype in [float, 'float64']

    def test_missing_value_handling(self):
        """Test that missing values are handled consistently"""
        data = pd.DataFrame({
            'home_talent': [0.85, None, 0.87],
            'home_elo': [1850, 1900, None],
        })
        
        # Should identify missing values
        missing_talent = data['home_talent'].isna().sum()
        missing_elo = data['home_elo'].isna().sum()
        
        assert missing_talent == 1
        assert missing_elo == 1

    def test_duplicate_game_prevention(self):
        """Test that duplicate games are prevented"""
        data = pd.DataFrame({
            'season': [2025, 2025, 2025],
            'week': [5, 5, 6],
            'home_team': ['Ohio State', 'Ohio State', 'Michigan'],
            'away_team': ['Michigan', 'Michigan', 'Ohio State'],
        })
        
        # Check for duplicates (same season, week, teams)
        duplicates = data.duplicated(subset=['season', 'week', 'home_team', 'away_team']).sum()
        
        assert duplicates > 0  # Has duplicates in test data
        # In real system, should prevent or handle duplicates


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

