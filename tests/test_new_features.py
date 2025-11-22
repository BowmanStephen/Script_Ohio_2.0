"""
Test suite for new feature engineering modules.
"""
import pytest
import pandas as pd
import numpy as np
from src.features.similarity import TeamSimilarityModel, find_similar_teams
from src.features.cfbd_feature_engineering import calculate_points_per_drive, calculate_explosive_drive_rate
from src.features.offense_defense import OffenseDefenseComparison, generate_matchup_comparison

@pytest.fixture
def mock_stats_df():
    """Create mock advanced stats dataframe."""
    data = {
        'team': ['TeamA', 'TeamB', 'TeamC', 'TeamD', 'TeamE', 'TeamF'],
        'conference': ['Conf1'] * 6,
        'offense_ppa': [0.5, 0.4, 0.3, 0.2, 0.1, 0.0],
        'offense_successRate': [0.5, 0.45, 0.4, 0.35, 0.3, 0.25],
        'offense_explosiveness': [1.5, 1.4, 1.3, 1.2, 1.1, 1.0],
        'defense_ppa': [0.1, 0.2, 0.3, 0.4, 0.5, 0.6],
        'defense_successRate': [0.3, 0.35, 0.4, 0.45, 0.5, 0.55],
        'defense_explosiveness': [1.0, 1.1, 1.2, 1.3, 1.4, 1.5],
        # Extra columns to satisfy default metrics check if strict
        'offense_lineYards': [3.0]*6,
        'offense_secondLevelYards': [1.2]*6,
        'offense_pointsPerOpportunity': [4.0]*6,
        'defense_lineYards': [2.5]*6,
        'defense_secondLevelYards': [1.0]*6,
        'defense_pointsPerOpportunity': [3.5]*6,
    }
    return pd.DataFrame(data)

@pytest.fixture
def mock_drives_df():
    """Create mock drives dataframe."""
    data = {
        'start_offense_score': [0, 7, 14, 14, 21],
        'end_offense_score':   [7, 14, 14, 21, 24], # +7, +7, +0, +7, +3
        'yards': [80, 75, 10, 90, 50],
        'plays': [10, 8, 3, 5, 10]
    }
    # PPD: (7+7+0+7+3)/5 = 24/5 = 4.8
    # YPP: 8, 9.375, 3.33, 18, 5
    # Explosive (>10 ypp): 1 (90/5=18) -> 1/5 = 0.2
    return pd.DataFrame(data)

def test_team_similarity(mock_stats_df):
    """Test TeamSimilarityModel."""
    model = TeamSimilarityModel(mock_stats_df)
    
    # Test finding similar teams
    similar = model.find_similar_teams('TeamA', top_n=2)
    assert len(similar) == 2
    # TeamB should be closest
    assert similar[0][0] == 'TeamB'
    
    # Test functional interface
    similar_func = find_similar_teams(mock_stats_df, 'TeamA', top_n=2)
    assert similar_func == similar
    
    # Test matrix
    matrix = model.calculate_team_similarity_matrix()
    assert matrix.shape == (6, 6)
    assert matrix.loc['TeamA', 'TeamA'] == 0.0

def test_drive_efficiency(mock_drives_df):
    """Test drive efficiency calculations."""
    ppd = calculate_points_per_drive(mock_drives_df)
    # Total points gained: 7, 7, 0, 7, 3 = 24
    # Drives: 5
    # PPD = 4.8
    assert abs(ppd - 4.8) < 0.001
    
    explosive_rate = calculate_explosive_drive_rate(mock_drives_df, yards_threshold=10.0)
    # Drives with >= 10 ypp: 90/5=18 (index 3)
    # 1 out of 5
    assert abs(explosive_rate - 0.2) < 0.001

def test_offense_defense_comparison(mock_stats_df):
    """Test OffenseDefenseComparison."""
    model = OffenseDefenseComparison(mock_stats_df)
    
    comparison = model.generate_matchup_comparison('TeamA', 'TeamF')
    
    assert 'team1_off_vs_team2_def' in comparison
    assert 'team2_off_vs_team1_def' in comparison
    
    t1_stats = comparison['team1_off_vs_team2_def']
    # TeamA offense PPA is 0.5 (highest), TeamF defense PPA is 0.6 (highest/worst for defense)
    # TeamA off PPA z-score should be positive (high is good for offense)
    # TeamF def PPA z-score should be positive (high is bad for defense usually, but z-score just measures deviation)
    
    assert 'offense_ppa' in t1_stats
    assert 'defense_ppa' in t1_stats

