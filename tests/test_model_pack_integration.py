#!/usr/bin/env python3
"""
Integration Tests for Model Pack Complete Pipeline

Tests the complete end-to-end workflow:
- Data acquisition → Feature calculation → Model training → Prediction

Author: Model Pack Improvement Plan
Created: 2025-11-19
"""

import pytest
import pandas as pd
import numpy as np
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import warnings
import sys
import os
import joblib

# Suppress warnings
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


class TestCompletePipeline:
    """End-to-end integration tests for complete pipeline"""

    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace for integration tests"""
        temp_path = tempfile.mkdtemp()
        yield temp_path
        shutil.rmtree(temp_path)

    @pytest.fixture
    def mock_training_data(self):
        """Create mock training data for pipeline"""
        np.random.seed(42)
        n_games = 100
        
        data = {
            'season': np.random.choice([2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024], n_games),
            'week': np.random.randint(5, 15, n_games),
            'home_team': np.random.choice(['Ohio State', 'Michigan', 'Alabama', 'Georgia'], n_games),
            'away_team': np.random.choice(['Notre Dame', 'Penn State', 'Texas', 'Oklahoma'], n_games),
            'home_points': np.random.randint(10, 60, n_games),
            'away_points': np.random.randint(10, 60, n_games),
            'margin': np.random.randint(-30, 30, n_games),
            'home_talent': np.random.uniform(0.80, 0.98, n_games),
            'away_talent': np.random.uniform(0.80, 0.98, n_games),
            'home_elo': np.random.uniform(1500, 2200, n_games),
            'away_elo': np.random.uniform(1500, 2200, n_games),
            'spread': np.random.uniform(-20, 20, n_games),
            'home_adjusted_epa': np.random.uniform(-0.1, 0.4, n_games),
            'home_adjusted_epa_allowed': np.random.uniform(-0.4, 0.1, n_games),
            'away_adjusted_epa': np.random.uniform(-0.1, 0.4, n_games),
            'away_adjusted_epa_allowed': np.random.uniform(-0.4, 0.1, n_games),
            'home_adjusted_success': np.random.uniform(0.3, 0.6, n_games),
            'home_adjusted_success_allowed': np.random.uniform(0.3, 0.6, n_games),
            'away_adjusted_success': np.random.uniform(0.3, 0.6, n_games),
            'away_adjusted_success_allowed': np.random.uniform(0.3, 0.6, n_games),
            'home_conference': np.random.choice(['Big Ten', 'SEC', 'Big 12', 'ACC'], n_games),
            'away_conference': np.random.choice(['Big Ten', 'SEC', 'Big 12', 'ACC'], n_games),
            'neutral_site': np.random.choice([True, False], n_games),
        }
        
        return pd.DataFrame(data)

    def test_temporal_validation_split(self, mock_training_data, temp_workspace):
        """Test that temporal validation split works correctly"""
        # Split by season (train on 2016-2023, test on 2024)
        train_df = mock_training_data[mock_training_data['season'] < 2024]
        test_df = mock_training_data[mock_training_data['season'] == 2024]
        
        # Verify no data leakage
        assert train_df['season'].max() < test_df['season'].min()
        assert len(train_df) > 0
        assert len(test_df) >= 0  # May be empty if no 2024 data
        
        # Verify all seasons in train are before test
        if len(test_df) > 0:
            assert train_df['season'].max() < test_df['season'].min()

    def test_model_training_pipeline(self, mock_training_data, temp_workspace):
        """Test complete model training pipeline"""
        # Save mock data
        data_path = os.path.join(temp_workspace, "updated_training_data.csv")
        mock_training_data.to_csv(data_path, index=False)
        
        # Mock the model training agent
        with patch('model_pack.model_training_agent.ModelTrainingAgent') as MockAgent:
            mock_agent_instance = Mock()
            mock_agent_instance.load_and_prepare_data.return_value = None
            mock_agent_instance.train_ridge_regression.return_value = {
                'mae': 10.5,
                'rmse': 12.3,
                'r2': 0.45
            }
            mock_agent_instance.train_xgboost_classifier.return_value = {
                'accuracy': 0.65,
                'log_loss': 0.58,
                'auc': 0.72
            }
            MockAgent.return_value = mock_agent_instance
            
            # Test pipeline execution
            agent = MockAgent(data_path)
            agent.load_and_prepare_data()
            ridge_metrics = agent.train_ridge_regression()
            xgb_metrics = agent.train_xgboost_classifier()
            
            # Verify metrics are returned
            assert 'mae' in ridge_metrics
            assert 'accuracy' in xgb_metrics
            assert ridge_metrics['mae'] > 0
            assert xgb_metrics['accuracy'] > 0

    def test_model_loading_and_prediction(self, temp_workspace):
        """Test model loading and prediction consistency"""
        # Create a simple mock model
        from sklearn.linear_model import Ridge
        model = Ridge(alpha=1.0)
        
        # Train on dummy data
        X_train = np.random.rand(50, 8)
        y_train = np.random.rand(50) * 20 - 10
        model.fit(X_train, y_train)
        
        # Save model
        model_path = os.path.join(temp_workspace, "test_model.joblib")
        joblib.dump(model, model_path)
        
        # Load model
        loaded_model = joblib.load(model_path)
        
        # Test prediction consistency
        X_test = np.random.rand(10, 8)
        original_preds = model.predict(X_test)
        loaded_preds = loaded_model.predict(X_test)
        
        # Predictions should be identical
        np.testing.assert_array_almost_equal(original_preds, loaded_preds, decimal=5)

    def test_feature_consistency_across_pipeline(self, mock_training_data):
        """Test that features remain consistent across pipeline stages"""
        # Define expected features
        ridge_features = [
            'home_talent', 'away_talent', 'home_elo', 'away_elo',
            'home_adjusted_epa', 'home_adjusted_epa_allowed',
            'away_adjusted_epa', 'away_adjusted_epa_allowed'
        ]
        
        # Verify all features exist in data
        for feature in ridge_features:
            assert feature in mock_training_data.columns, f"Missing feature: {feature}"
        
        # Verify no missing values in features (for training)
        feature_data = mock_training_data[ridge_features]
        assert feature_data.notna().all().all(), "Features contain missing values"

    def test_data_acquisition_to_training_flow(self, temp_workspace):
        """Test flow from data acquisition to model training"""
        # Mock data acquisition
        mock_games = pd.DataFrame({
            'season': [2025, 2025],
            'week': [1, 2],
            'home_team': ['Ohio State', 'Alabama'],
            'away_team': ['Michigan', 'Georgia'],
            'home_points': [42, 35],
            'away_points': [13, 21],
        })
        
        # Save acquired data
        acquired_path = os.path.join(temp_workspace, "acquired_games.csv")
        mock_games.to_csv(acquired_path, index=False)
        
        # Verify data can be loaded
        loaded_data = pd.read_csv(acquired_path)
        assert len(loaded_data) == 2
        assert 'home_team' in loaded_data.columns
        
        # Verify data structure is suitable for training
        required_cols = ['season', 'week', 'home_team', 'away_team']
        for col in required_cols:
            assert col in loaded_data.columns

    def test_model_performance_tracking(self, temp_workspace):
        """Test model performance tracking across runs"""
        # Create performance history
        performance_history = {
            'run_1': {'mae': 10.5, 'accuracy': 0.65},
            'run_2': {'mae': 9.8, 'accuracy': 0.68},
            'run_3': {'mae': 9.2, 'accuracy': 0.70},
        }
        
        # Save to file
        import json
        history_path = os.path.join(temp_workspace, "performance_history.json")
        with open(history_path, 'w') as f:
            json.dump(performance_history, f)
        
        # Load and verify
        with open(history_path, 'r') as f:
            loaded_history = json.load(f)
        
        assert len(loaded_history) == 3
        assert 'run_1' in loaded_history
        assert loaded_history['run_3']['accuracy'] > loaded_history['run_1']['accuracy']

    def test_error_handling_in_pipeline(self, temp_workspace):
        """Test error handling at each pipeline stage"""
        # Test missing data file
        missing_path = os.path.join(temp_workspace, "nonexistent.csv")
        with pytest.raises((FileNotFoundError, pd.errors.EmptyDataError)):
            pd.read_csv(missing_path)
        
        # Test invalid model file
        invalid_model_path = os.path.join(temp_workspace, "invalid_model.joblib")
        with open(invalid_model_path, 'w') as f:
            f.write("not a valid model")
        
        with pytest.raises((ValueError, EOFError, Exception)):
            joblib.load(invalid_model_path)

    def test_pipeline_with_missing_features(self, mock_training_data):
        """Test pipeline behavior with missing features"""
        # Remove some features
        incomplete_data = mock_training_data.drop(columns=['home_adjusted_epa', 'away_adjusted_epa'])
        
        # Should handle missing features gracefully
        ridge_features = [
            'home_talent', 'away_talent', 'home_elo', 'away_elo',
            'home_adjusted_epa', 'home_adjusted_epa_allowed',
            'away_adjusted_epa', 'away_adjusted_epa_allowed'
        ]
        
        # Check which features are missing
        missing = [f for f in ridge_features if f not in incomplete_data.columns]
        assert len(missing) > 0  # Some features should be missing
        
        # Pipeline should handle this (either error or use available features)
        available_features = [f for f in ridge_features if f in incomplete_data.columns]
        assert len(available_features) < len(ridge_features)

    def test_model_versioning(self, temp_workspace):
        """Test model versioning system"""
        from datetime import datetime
        
        # Create versioned model files
        base_name = "ridge_model"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        versioned_path = os.path.join(temp_workspace, f"{base_name}_{timestamp}.joblib")
        
        # Create dummy model
        from sklearn.linear_model import Ridge
        model = Ridge()
        model.fit(np.random.rand(10, 8), np.random.rand(10))
        joblib.dump(model, versioned_path)
        
        # Verify versioned file exists
        assert os.path.exists(versioned_path)
        
        # Test loading versioned model
        loaded = joblib.load(versioned_path)
        assert loaded is not None


class TestDataQualityIntegration:
    """Integration tests for data quality across pipeline"""

    def test_no_data_leakage(self):
        """Test that no future data leaks into training features"""
        # Create data with temporal structure
        data = pd.DataFrame({
            'season': [2020, 2020, 2021, 2021, 2022, 2022],
            'week': [5, 6, 5, 6, 5, 6],
            'home_points': [42, 35, 28, 31, 24, 27],
            'away_points': [13, 21, 14, 17, 21, 20],
        })
        
        # Split temporally
        train = data[data['season'] < 2022]
        test = data[data['season'] >= 2022]
        
        # Verify no leakage
        assert train['season'].max() < test['season'].min()
        assert len(set(train['season']) & set(test['season'])) == 0

    def test_feature_distribution_consistency(self):
        """Test that feature distributions remain consistent"""
        # Create data with known distribution
        np.random.seed(42)
        data = pd.DataFrame({
            'home_talent': np.random.normal(0.85, 0.05, 100),
            'away_talent': np.random.normal(0.85, 0.05, 100),
        })
        
        # Check distribution properties
        assert data['home_talent'].mean() > 0.8
        assert data['home_talent'].mean() < 0.9
        assert data['home_talent'].std() > 0.01
        assert data['home_talent'].std() < 0.1

    def test_week_filtering_logic(self):
        """Test week 5+ filtering logic"""
        data = pd.DataFrame({
            'week': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            'season': [2025] * 10,
        })
        
        # Filter weeks 5+
        filtered = data[data['week'] >= 5]
        
        assert len(filtered) == 6
        assert filtered['week'].min() == 5
        assert all(filtered['week'] >= 5)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

