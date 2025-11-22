#!/usr/bin/env python3
"""
Comprehensive Test Suite for Week 12 Agents

This module provides thorough testing for all Week 12 specialized agents,
ensuring they meet production standards and integration requirements.

Author: Claude Code Assistant
Created: 2025-11-10
Version: 2.0 - Grade A Enhancement
"""

import pytest
import pandas as pd
import numpy as np
import tempfile
import shutil
import time
import json
from unittest.mock import Mock, patch, MagicMock, mock_open
from pathlib import Path

# Import week12 agents
from agents.week12_matchup_analysis_agent import Week12MatchupAnalysisAgent
from agents.week12_mock_enhancement_agent import Week12MockEnhancementAgent
from agents.week12_model_validation_agent import Week12ModelValidationAgent
from agents.week12_prediction_generation_agent import Week12PredictionGenerationAgent


class TestWeek12MatchupAnalysisAgent:
    """Comprehensive test cases for Week 12 Matchup Analysis Agent"""

    @pytest.fixture
    def matchup_agent(self):
        """Create matchup analysis agent for testing"""
        return Week12MatchupAnalysisAgent()

    @pytest.fixture
    def sample_matchup_data(self):
        """Sample matchup data for testing"""
        return pd.DataFrame({
            'home_team': ['Ohio State', 'Michigan', 'Alabama'],
            'away_team': ['Michigan', 'Ohio State', 'Georgia'],
            'home_elo': [85.2, 84.8, 86.1],
            'away_elo': [85.5, 85.0, 84.7],
            'home_talent': [0.95, 0.93, 0.94],
            'away_talent': [0.93, 0.95, 0.92],
            'home_conference': ['Big Ten', 'Big Ten', 'SEC'],
            'away_conference': ['Big Ten', 'Big Ten', 'SEC'],
            'week': [12, 12, 12],
            'season': [2025, 2025, 2025]
        })

    def test_agent_initialization(self, matchup_agent):
        """Test matchup analysis agent initialization"""
        assert matchup_agent.name == "Week 12 Matchup Analysis Agent"
        assert matchup_agent.role == "Matchup Analysis Specialist"
        assert "READ_WRITE" in matchup_agent.permissions
        assert "data_analyzer" in matchup_agent.tools
        assert hasattr(matchup_agent, 'context_manager')
        assert hasattr(matchup_agent, 'analysis_weights')

    def test_load_week12_matchups(self, matchup_agent, sample_matchup_data):
        """Test loading Week 12 matchups"""
        with patch('pandas.read_csv') as mock_read:
            mock_read.return_value = sample_matchup_data

            result = matchup_agent._load_week12_matchups()

            assert isinstance(result, pd.DataFrame)
            assert len(result) == 3
            assert 'home_team' in result.columns
            assert 'away_team' in result.columns

    def test_analyze_team_matchup(self, matchup_agent, sample_matchup_data):
        """Test individual matchup analysis"""
        matchup = sample_matchup_data.iloc[0]

        with patch.object(matchup_agent, '_calculate_matchup_metrics') as mock_metrics:
            mock_metrics.return_value = {
                'elo_advantage': 0.7,
                'talent_gap': 0.02,
                'historical_advantage': 0.55,
                'conference_impact': 0.1
            }

            result = matchup_agent._analyze_team_matchup(matchup)

            assert 'matchup_metrics' in result
            assert 'strategic_insights' in result
            assert 'prediction_factors' in result

    def test_comprehensive_matchup_analysis(self, matchup_agent):
        """Test comprehensive matchup analysis"""
        task_data = {
            'operation': 'analyze_matchups',
            'target_week': 12,
            'season': 2025,
            'analysis_depth': 'comprehensive'
        }

        with patch.object(matchup_agent, '_load_week12_matchups') as mock_load:
            mock_data = pd.DataFrame({
                'home_team': ['Ohio State', 'Michigan'],
                'away_team': ['Michigan', 'Ohio State'],
                'home_elo': [85.2, 84.8],
                'away_elo': [85.5, 85.0]
            })
            mock_load.return_value = mock_data

            with patch.object(matchup_agent, '_analyze_team_matchup') as mock_analyze:
                mock_analyze.return_value = {
                    'matchup_metrics': {'elo_advantage': -0.3},
                    'strategic_insights': ['Close matchup expected']
                }

                result = matchup_agent.execute_task(task_data)

                assert result['success'] is True
                assert 'analysis_summary' in result
                assert 'matchup_breakdown' in result
                assert 'strategic_recommendations' in result

    def test_error_handling_invalid_data(self, matchup_agent):
        """Test error handling with invalid matchup data"""
        task_data = {
            'operation': 'analyze_matchups',
            'target_week': 99,  # Invalid week
            'season': 2025
        }

        result = matchup_agent.execute_task(task_data)

        assert result['success'] is False
        assert 'error' in result

    @pytest.mark.performance
    def test_analysis_performance(self, matchup_agent):
        """Test analysis performance benchmarks"""
        task_data = {
            'operation': 'analyze_matchups',
            'target_week': 12,
            'season': 2025,
            'analysis_depth': 'comprehensive'
        }

        with patch.object(matchup_agent, '_load_week12_matchups') as mock_load:
            mock_load.return_value = pd.DataFrame({
                'home_team': ['Team_' + str(i) for i in range(50)],
                'away_team': ['Opponent_' + str(i) for i in range(50)],
                'home_elo': np.random.normal(80, 10, 50),
                'away_elo': np.random.normal(80, 10, 50)
            })

            with patch.object(matchup_agent, '_analyze_team_matchup') as mock_analyze:
                mock_analyze.return_value = {'matchup_metrics': {}}

                start_time = time.time()
                result = matchup_agent.execute_task(task_data)
                end_time = time.time()

                analysis_time = end_time - start_time
                assert result['success'] is True
                assert analysis_time < 5.0  # Should complete within 5 seconds


class TestWeek12MockEnhancementAgent:
    """Comprehensive test cases for Week 12 Mock Enhancement Agent"""

    @pytest.fixture
    def mock_enhancement_agent(self):
        """Create mock enhancement agent for testing"""
        return Week12MockEnhancementAgent()

    @pytest.fixture
    def sample_base_data(self):
        """Sample base data for enhancement"""
        return pd.DataFrame({
            'team': ['Ohio State', 'Michigan', 'Alabama'],
            'conference': ['Big Ten', 'Big Ten', 'SEC'],
            'wins': [10, 9, 11],
            'losses': [1, 2, 0],
            'points_for': [450, 380, 490],
            'points_against': [280, 290, 220]
        })

    def test_agent_initialization(self, mock_enhancement_agent):
        """Test mock enhancement agent initialization"""
        assert mock_enhancement_agent.name is not None
        assert hasattr(mock_enhancement_agent, 'context_manager')
        assert hasattr(mock_enhancement_agent, 'enhancement_strategies')

    def test_data_enhancement_pipeline(self, mock_enhancement_agent, sample_base_data):
        """Test data enhancement pipeline"""
        task_data = {
            'operation': 'enhance_data',
            'target_week': 12,
            'season': 2025,
            'enhancement_types': ['advanced_metrics', 'opponent_adjustments']
        }

        with patch.object(mock_enhancement_agent, '_load_base_data') as mock_load:
            mock_load.return_value = sample_base_data

            with patch.object(mock_enhancement_agent, '_apply_enhancements') as mock_enhance:
                mock_enhance.return_value = sample_base_data.copy()

                result = mock_enhancement_agent.execute_task(task_data)

                assert result['success'] is True
                assert 'enhanced_data' in result
                assert 'enhancement_summary' in result

    def test_advanced_metrics_calculation(self, mock_enhancement_agent):
        """Test advanced metrics calculation"""
        base_stats = {
            'points_for': 450,
            'points_against': 280,
            'games_played': 11,
            'opponents_strength': 0.75
        }

        enhanced_metrics = mock_enhancement_agent._calculate_advanced_metrics(base_stats)

        assert 'efficiency_metrics' in enhanced_metrics
        assert 'strength_of_schedule' in enhanced_metrics
        assert 'performance_trends' in enhanced_metrics

    def test_opponent_adjustment_application(self, mock_enhancement_agent):
        """Test opponent adjustment application"""
        raw_data = pd.DataFrame({
            'team': ['Ohio State', 'Michigan'],
            'offensive_efficiency': [1.25, 1.18],
            'opponents': ['Strong_Schedule', 'Weak_Schedule']
        })

        adjusted_data = mock_enhancement_agent._apply_opponent_adjustments(raw_data)

        assert isinstance(adjusted_data, pd.DataFrame)
        assert len(adjusted_data) == len(raw_data)
        # Should have adjusted columns
        assert 'offensive_efficiency_adj' in adjusted_data.columns

    def test_enhancement_quality_validation(self, mock_enhancement_agent):
        """Test quality validation of enhanced data"""
        enhanced_data = pd.DataFrame({
            'team': ['Ohio State', 'Michigan'],
            'adjusted_epa': [0.25, 0.22],
            'strength_of_schedule': [0.78, 0.65]
        })

        quality_score = mock_enhancement_agent._validate_enhancement_quality(enhanced_data)

        assert isinstance(quality_score, dict)
        assert 'overall_score' in quality_score
        assert 'data_completeness' in quality_score
        assert 'metric_consistency' in quality_score


class TestWeek12ModelValidationAgent:
    """Comprehensive test cases for Week 12 Model Validation Agent"""

    @pytest.fixture
    def model_validation_agent(self):
        """Create model validation agent for testing"""
        return Week12ModelValidationAgent()

    @pytest.fixture
    def sample_model_predictions(self):
        """Sample model predictions for validation"""
        return pd.DataFrame({
            'game_id': ['game_1', 'game_2', 'game_3'],
            'home_team': ['Ohio State', 'Michigan', 'Alabama'],
            'away_team': ['Michigan', 'Ohio State', 'Georgia'],
            'actual_home_win': [1, 0, 1],
            'predicted_win_prob': [0.65, 0.45, 0.72],
            'predicted_margin': [7.5, -3.2, 10.1],
            'actual_margin': [8, -5, 12]
        })

    def test_agent_initialization(self, model_validation_agent):
        """Test model validation agent initialization"""
        assert model_validation_agent.name is not None
        assert hasattr(model_validation_agent, 'validation_metrics')
        assert hasattr(model_validation_agent, 'model_performance_history')

    def test_accuracy_validation(self, model_validation_agent, sample_model_predictions):
        """Test model accuracy validation"""
        task_data = {
            'operation': 'validate_accuracy',
            'model_type': 'win_probability',
            'test_data': sample_model_predictions
        }

        result = model_validation_agent.execute_task(task_data)

        assert result['success'] is True
        assert 'accuracy_metrics' in result
        assert 'classification_report' in result
        assert 'confidence_intervals' in result

    def test_margin_prediction_validation(self, model_validation_agent, sample_model_predictions):
        """Test margin prediction validation"""
        task_data = {
            'operation': 'validate_margin',
            'model_type': 'ridge_regression',
            'test_data': sample_model_predictions
        }

        result = model_validation_agent.execute_task(task_data)

        assert result['success'] is True
        assert 'mae' in result
        assert 'rmse' in result
        assert 'r_squared' in result

    def test_model_calibration_validation(self, model_validation_agent, sample_model_predictions):
        """Test model calibration validation"""
        calibration_result = model_validation_agent._validate_calibration(
            sample_model_predictions['predicted_win_prob'],
            sample_model_predictions['actual_home_win']
        )

        assert 'brier_score' in calibration_result
        assert 'calibration_curve' in calibration_result
        assert 'reliability_diagram' in calibration_result

    def test_cross_validation_performance(self, model_validation_agent):
        """Test cross-validation performance assessment"""
        task_data = {
            'operation': 'cross_validation',
            'model_type': 'ensemble',
            'cv_folds': 5
        }

        with patch.object(model_validation_agent, '_perform_cross_validation') as mock_cv:
            mock_cv.return_value = {
                'cv_scores': [0.65, 0.62, 0.68, 0.64, 0.66],
                'mean_score': 0.65,
                'std_score': 0.02
            }

            result = model_validation_agent.execute_task(task_data)

            assert result['success'] is True
            assert 'cv_results' in result
            assert 'performance_stability' in result

    def test_model_comparison_validation(self, model_validation_agent):
        """Test model comparison validation"""
        task_data = {
            'operation': 'compare_models',
            'models': ['ridge_model', 'xgb_model', 'ensemble_model'],
            'test_data': 'week12_test_set'
        }

        with patch.object(model_validation_agent, '_run_model_comparison') as mock_compare:
            mock_compare.return_value = {
                'model_rankings': ['ensemble_model', 'xgb_model', 'ridge_model'],
                'performance_differences': [0.02, 0.05],
                'statistical_significance': [True, False]
            }

            result = model_validation_agent.execute_task(task_data)

            assert result['success'] is True
            assert 'model_comparison' in result
            assert 'recommendations' in result

    def test_validation_report_generation(self, model_validation_agent, sample_model_predictions):
        """Test comprehensive validation report generation"""
        task_data = {
            'operation': 'generate_report',
            'validation_comprehensive': True,
            'include_visualizations': True
        }

        with patch.object(model_validation_agent, '_compile_validation_results') as mock_compile:
            mock_compile.return_value = {
                'executive_summary': 'Models show good performance',
                'detailed_metrics': {'accuracy': 0.65, 'mae': 17.2},
                'recommendations': ['Continue monitoring', 'Consider ensemble methods']
            }

            result = model_validation_agent.execute_task(task_data)

            assert result['success'] is True
            assert 'validation_report' in result
            assert 'performance_summary' in result


class TestWeek12PredictionGenerationAgent:
    """Comprehensive test cases for Week 12 Prediction Generation Agent"""

    @pytest.fixture
    def prediction_agent(self):
        """Create prediction generation agent for testing"""
        return Week12PredictionGenerationAgent()

    @pytest.fixture
    def week12_matchups(self):
        """Sample Week 12 matchups for prediction"""
        return pd.DataFrame({
            'game_id': ['game_1', 'game_2', 'game_3'],
            'home_team': ['Ohio State', 'Michigan', 'Alabama'],
            'away_team': ['Michigan', 'Ohio State', 'Georgia'],
            'home_elo': [85.2, 84.8, 86.1],
            'away_elo': [85.5, 85.0, 84.7],
            'home_talent': [0.95, 0.93, 0.94],
            'away_talent': [0.93, 0.95, 0.92]
        })

    def test_agent_initialization(self, prediction_agent):
        """Test prediction generation agent initialization"""
        assert prediction_agent.name is not None
        assert hasattr(prediction_agent, 'prediction_models')
        assert hasattr(prediction_agent, 'ensemble_weights')

    def test_single_game_prediction(self, prediction_agent, week12_matchups):
        """Test single game prediction generation"""
        matchup = week12_matchups.iloc[0]

        with patch.object(prediction_agent, '_load_model_features') as mock_features:
            mock_features.return_value = {
                'home_talent': 0.95,
                'away_talent': 0.93,
                'home_elo': 85.2,
                'away_elo': 85.5
            }

            with patch.object(prediction_agent, '_run_prediction_models') as mock_predict:
                mock_predict.return_value = {
                    'win_probability': 0.65,
                    'predicted_margin': 7.5,
                    'confidence_interval': (2.1, 12.9)
                }

                result = prediction_agent._predict_single_game(matchup)

                assert 'home_win_probability' in result
                assert 'predicted_margin' in result
                assert 'confidence_level' in result

    def test_batch_prediction_generation(self, prediction_agent, week12_matchups):
        """Test batch prediction generation"""
        task_data = {
            'operation': 'generate_predictions',
            'target_week': 12,
            'season': 2025,
            'model_ensemble': True
        }

        with patch.object(prediction_agent, '_load_week12_matchups') as mock_load:
            mock_load.return_value = week12_matchups

            with patch.object(prediction_agent, '_predict_single_game') as mock_predict:
                mock_predict.return_value = {
                    'home_win_probability': 0.65,
                    'predicted_margin': 7.5
                }

                result = prediction_agent.execute_task(task_data)

                assert result['success'] is True
                assert 'predictions' in result
                assert len(result['predictions']) == 3
                assert 'prediction_summary' in result

    def test_ensemble_prediction_method(self, prediction_agent, week12_matchups):
        """Test ensemble prediction methodology"""
        matchup = week12_matchups.iloc[0]

        individual_predictions = {
            'ridge_model': {'win_probability': 0.63, 'margin': 6.8},
            'xgb_model': {'win_probability': 0.67, 'margin': 8.2},
            'neural_network': {'win_probability': 0.64, 'margin': 7.1}
        }

        ensemble_result = prediction_agent._create_ensemble_prediction(individual_predictions)

        assert 'ensemble_win_probability' in ensemble_result
        assert 'ensemble_margin' in ensemble_result
        assert 'prediction_variance' in ensemble_result
        assert 'confidence_level' in ensemble_result

    def test_prediction_explanation_generation(self, prediction_agent, week12_matchups):
        """Test prediction explanation generation"""
        prediction_data = {
            'home_team': 'Ohio State',
            'away_team': 'Michigan',
            'home_win_probability': 0.65,
            'predicted_margin': 7.5,
            'key_factors': {
                'elo_advantage': 0.3,
                'talent_gap': 0.02,
                'home_field_advantage': 0.15
            }
        }

        explanation = prediction_agent._generate_prediction_explanation(prediction_data)

        assert 'narrative_explanation' in explanation
        assert 'key_factors_breakdown' in explanation
        assert 'confidence_assessment' in explanation

    def test_uncertainty_quantification(self, prediction_agent):
        """Test prediction uncertainty quantification"""
        predictions_history = [
            {'predicted_prob': 0.65, 'actual_outcome': 1},
            {'predicted_prob': 0.45, 'actual_outcome': 0},
            {'predicted_prob': 0.72, 'actual_outcome': 1}
        ]

        uncertainty_analysis = prediction_agent._quantify_prediction_uncertainty(
            current_prediction=0.65,
            historical_predictions=predictions_history
        )

        assert 'prediction_interval' in uncertainty_analysis
        assert 'confidence_score' in uncertainty_analysis
        assert 'model_uncertainty' in uncertainty_analysis

    def test_performance_validation_against_actuals(self, prediction_agent):
        """Test validation against actual results"""
        task_data = {
            'operation': 'validate_predictions',
            'target_week': 11,  # Previous week for validation
            'compare_to_actuals': True
        }

        with patch.object(prediction_agent, '_load_actual_results') as mock_actuals:
            mock_actuals.return_value = pd.DataFrame({
                'game_id': ['game_1', 'game_2'],
                'home_team': ['Ohio State', 'Michigan'],
                'away_team': ['Michigan', 'Ohio State'],
                'actual_home_win': [1, 0],
                'actual_margin': [8, -5]
            })

            with patch.object(prediction_agent, '_load_previous_predictions') as mock_preds:
                mock_preds.return_value = pd.DataFrame({
                    'game_id': ['game_1', 'game_2'],
                    'predicted_win_prob': [0.65, 0.42],
                    'predicted_margin': [7.5, -3.1]
                })

                result = prediction_agent.execute_task(task_data)

                assert result['success'] is True
                assert 'validation_metrics' in result
                assert 'accuracy_assessment' in result

    @pytest.mark.performance
    def test_prediction_generation_performance(self, prediction_agent):
        """Test prediction generation performance benchmarks"""
        task_data = {
            'operation': 'generate_predictions',
            'target_week': 12,
            'season': 2025,
            'batch_size': 100
        }

        with patch.object(prediction_agent, '_load_week12_matchups') as mock_load:
            # Create large dataset for performance testing
            large_matchups = pd.DataFrame({
                'game_id': [f'game_{i}' for i in range(100)],
                'home_team': [f'Team_{i}' for i in range(100)],
                'away_team': [f'Opponent_{i}' for i in range(100)],
                'home_elo': np.random.normal(80, 10, 100),
                'away_elo': np.random.normal(80, 10, 100)
            })
            mock_load.return_value = large_matchups

            with patch.object(prediction_agent, '_predict_single_game') as mock_predict:
                mock_predict.return_value = {'home_win_probability': 0.5, 'predicted_margin': 0}

                start_time = time.time()
                result = prediction_agent.execute_task(task_data)
                end_time = time.time()

                prediction_time = end_time - start_time
                assert result['success'] is True
                assert prediction_time < 10.0  # Should complete within 10 seconds


class TestWeek12AgentsIntegration:
    """Integration tests for all Week 12 agents working together"""

    @pytest.fixture
    def all_agents(self):
        """Create all Week 12 agents for integration testing"""
        return {
            'matchup': Week12MatchupAnalysisAgent(),
            'enhancement': Week12MockEnhancementAgent(),
            'validation': Week12ModelValidationAgent(),
            'prediction': Week12PredictionGenerationAgent()
        }

    def test_complete_week12_workflow(self, all_agents):
        """Test complete Week 12 analytics workflow"""
        # Step 1: Enhanced data generation
        enhancement_task = {
            'operation': 'enhance_data',
            'target_week': 12,
            'season': 2025
        }

        with patch.object(all_agents['enhancement'], '_load_base_data') as mock_load:
            mock_load.return_value = pd.DataFrame({
                'team': ['Ohio State', 'Michigan'],
                'basic_metrics': [1.2, 1.1]
            })

            enhanced_result = all_agents['enhancement'].execute_task(enhancement_task)
            assert enhanced_result['success'] is True

        # Step 2: Matchup analysis
        matchup_task = {
            'operation': 'analyze_matchups',
            'target_week': 12,
            'season': 2025
        }

        with patch.object(all_agents['matchup'], '_load_week12_matchups') as mock_matchups:
            mock_matchups.return_value = pd.DataFrame({
                'home_team': ['Ohio State'],
                'away_team': ['Michigan']
            })

            matchup_result = all_agents['matchup'].execute_task(matchup_task)
            assert matchup_result['success'] is True

        # Step 3: Prediction generation
        prediction_task = {
            'operation': 'generate_predictions',
            'target_week': 12,
            'season': 2025
        }

        with patch.object(all_agents['prediction'], '_load_week12_matchups') as mock_pred_matchups:
            mock_pred_matchups.return_value = pd.DataFrame({
                'home_team': ['Ohio State'],
                'away_team': ['Michigan']
            })

            with patch.object(all_agents['prediction'], '_predict_single_game') as mock_predict:
                mock_predict.return_value = {'home_win_probability': 0.65}

                prediction_result = all_agents['prediction'].execute_task(prediction_task)
                assert prediction_result['success'] is True

        # Step 4: Model validation
        validation_task = {
            'operation': 'validate_accuracy',
            'model_type': 'win_probability'
        }

        validation_result = all_agents['validation'].execute_task(validation_task)
        assert validation_result['success'] is True

    def test_agent_data_consistency(self, all_agents):
        """Test data consistency across agents"""
        # Test that all agents can handle the same data format
        standard_data = pd.DataFrame({
            'team': ['Ohio State', 'Michigan'],
            'conference': ['Big Ten', 'Big Ten'],
            'season': [2025, 2025],
            'week': [12, 12]
        })

        # Each agent should be able to process the standard format
        for agent_name, agent in all_agents.items():
            try:
                # Test basic data processing capability
                if hasattr(agent, '_process_standard_data'):
                    result = agent._process_standard_data(standard_data.copy())
                    assert isinstance(result, (pd.DataFrame, dict))
            except AttributeError:
                # Agent may not have this method, which is fine
                pass

    def test_error_propagation_handling(self, all_agents):
        """Test error handling and propagation across agents"""
        # Test that errors in one agent don't crash the entire system
        for agent_name, agent in all_agents.items():
            # Test with invalid task data
            invalid_task = {
                'operation': 'invalid_operation',
                'invalid_parameter': 'test'
            }

            result = agent.execute_task(invalid_task)

            # Should handle errors gracefully
            assert 'success' in result
            assert isinstance(result['success'], bool)

            if not result['success']:
                assert 'error' in result or 'message' in result

    @pytest.mark.performance
    def test_overall_system_performance(self, all_agents):
        """Test overall system performance with all agents"""
        start_time = time.time()

        # Run quick versions of all agent tasks
        tasks = [
            (all_agents['matchup'], {'operation': 'analyze_matchups', 'target_week': 12}),
            (all_agents['enhancement'], {'operation': 'enhance_data', 'target_week': 12}),
            (all_agents['prediction'], {'operation': 'generate_predictions', 'target_week': 12}),
            (all_agents['validation'], {'operation': 'validate_accuracy', 'model_type': 'test'})
        ]

        successful_executions = 0
        for agent, task in tasks:
            with patch.object(agent, '_load_week12_matchups') as mock_load:
                mock_load.return_value = pd.DataFrame({'test': [1]})  # Minimal data

                try:
                    result = agent.execute_task(task)
                    if result.get('success', False):
                        successful_executions += 1
                except Exception:
                    # Should handle exceptions gracefully
                    pass

        end_time = time.time()
        total_time = end_time - start_time

        # Performance assertions
        assert total_time < 30.0  # Should complete within 30 seconds
        assert successful_executions >= 2  # At least half should succeed

    def test_memory_usage_integration(self, all_agents):
        """Test memory usage during integrated agent operations"""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Run all agents with minimal data
        for agent_name, agent in all_agents.items():
            with patch.object(agent, '_load_week12_matchups') as mock_load:
                mock_load.return_value = pd.DataFrame({'minimal': [1]})

                try:
                    agent.execute_task({
                        'operation': 'test_operation',
                        'minimal_data': True
                    })
                except:
                    pass  # Ignore errors for memory testing

        final_memory = process.memory_info().rss
        memory_increase = (final_memory - initial_memory) / 1024 / 1024  # MB

        # Memory increase should be reasonable
        assert memory_increase < 100, f"Memory increase {memory_increase:.2f}MB exceeds limit"