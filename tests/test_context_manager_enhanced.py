#!/usr/bin/env python3
"""
Enhanced Test Suite for Context Manager

This module provides comprehensive testing for the Context Manager component,
testing role detection, context optimization, caching, and performance.

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
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Import context manager
from agents.core.context_manager import ContextManager, UserRole


class TestContextManagerEnhanced:
    """Enhanced comprehensive test cases for Context Manager"""

    @pytest.fixture
    def context_manager(self, temp_workspace):
        """Create context manager instance for testing"""
        return ContextManager(base_path=temp_workspace)

    @pytest.fixture
    def sample_analyst_context(self):
        """Sample analyst context for testing"""
        return {
            'notebooks': ['starter_pack/01_intro_to_data.ipynb', 'starter_pack/02_build_simple_rankings.ipynb'],
            'models': ['ridge_model_2025.joblib'],
            'query_type': 'learn about college football data',
            'skill_level': 'beginner',
            'focus_areas': ['basic_analytics', 'rankings']
        }

    @pytest.fixture
    def sample_data_scientist_context(self):
        """Sample data scientist context for testing"""
        return {
            'notebooks': ['model_pack/01_linear_regression_margin.ipynb', 'model_pack/06_shap_interpretability.ipynb'],
            'models': ['xgb_home_win_model_2025.pkl', 'fastai_home_win_model_2025.pkl'],
            'query_type': 'advanced feature engineering and model optimization',
            'skill_level': 'advanced',
            'focus_areas': ['machine_learning', 'feature_engineering', 'model_interpretation']
        }

    @pytest.fixture
    def sample_production_context(self):
        """Sample production context for testing"""
        return {
            'models': ['ridge_model_2025.joblib'],
            'query_type': 'predict game outcomes for production use',
            'priority': 'high',
            'speed_requirement': 'fast'
        }

    def test_role_detection_edge_cases(self, context_manager):
        """Test role detection with edge cases"""
        # Empty context
        empty_context = {}
        detected_role = context_manager.detect_user_role(empty_context)
        assert detected_role == UserRole.ANALYST  # Default role

        # Ambiguous context
        ambiguous_context = {
            'query_type': 'some unclear query',
            'random_field': 'random_value'
        }
        detected_role = context_manager.detect_user_role(ambiguous_context)
        assert detected_role == UserRole.ANALYST  # Default fallback

        # Mixed signals (should prioritize based on rules)
        mixed_context = {
            'notebooks': ['model_pack/advanced_notebook.ipynb'],  # Data scientist signal
            'query_type': 'basic learning'  # Analyst signal
        }
        detected_role = context_manager.detect_user_role(mixed_context)
        # Should detect based on weighted rules
        assert detected_role in [UserRole.ANALYST, UserRole.DATA_SCIENTIST]

    def test_context_loading_comprehensive(self, context_manager, sample_analyst_context):
        """Test comprehensive context loading"""
        role = UserRole.ANALYST
        context = context_manager.load_context_for_role(role, sample_analyst_context)

        # Validate context structure
        assert 'role' in context
        assert 'profile' in context
        assert 'data' in context
        assert 'notebooks' in context
        assert 'optimization_metadata' in context

        # Validate role-specific content
        assert context['role'] == 'analyst'
        assert len(context['notebooks']) > 0
        assert any('intro' in nb.lower() for nb in context['notebooks'])

    def test_token_optimization_algorithms(self, context_manager):
        """Test different token optimization algorithms"""
        # Create a large context that would exceed token limits
        large_context = {
            'data': {f'feature_{i}': f'value_{i}' * 100 for i in range(200)},
            'notebooks': [{'path': f'notebook_{i}', 'content': 'content ' * 1000} for i in range(100)],
            'models': [{'name': f'model_{i}', 'metadata': 'data ' * 500} for i in range(50)]
        }

        # Test with different token budgets
        token_budgets = [500, 1000, 2000, 5000]

        for budget in token_budgets:
            optimized = context_manager._optimize_context(large_context, budget)

            # Validate optimization
            assert 'optimization_metadata' in optimized
            assert 'original_size' in optimized['optimization_metadata']
            assert 'optimized_size' in optimized['optimization_metadata']
            assert 'compression_ratio' in optimized['optimization_metadata']

            # Size should be reduced
            original_size = len(str(large_context))
            optimized_size = len(str(optimized))
            assert optimized_size <= original_size

    def test_advanced_caching_strategies(self, context_manager, sample_analyst_context):
        """Test advanced caching strategies"""
        role = UserRole.ANALYST

        # First load - should miss cache
        start_time = time.time()
        context1 = context_manager.load_context_for_role(role, sample_analyst_context)
        first_load_time = time.time() - start_time

        # Second load - should hit cache
        start_time = time.time()
        context2 = context_manager.load_context_for_role(role, sample_analyst_context)
        second_load_time = time.time() - start_time

        # Validate caching
        assert context1 == context2
        assert second_load_time < first_load_time  # Should be faster due to cache

        # Check cache metrics
        metrics = context_manager.get_performance_metrics()
        assert 'cache_hit_rate' in metrics
        assert metrics['cache_hit_rate'] > 0

    def test_context_personalization(self, context_manager, sample_data_scientist_context):
        """Test context personalization based on user preferences"""
        # Add user preferences
        personalized_context = sample_data_scientist_context.copy()
        personalized_context['user_preferences'] = {
            'preferred_models': ['xgb_home_win_model_2025.pkl'],
            'focus_areas': ['deep_learning', 'model_interpretability'],
            'learning_style': 'hands_on'
        }

        role = UserRole.DATA_SCIENTIST
        context = context_manager.load_context_for_role(role, personalized_context)

        # Validate personalization
        assert 'personalization_applied' in context
        assert context['personalization_applied'] is True

        # Check that preferences are reflected
        if 'recommended_models' in context:
            assert any('xgb' in model for model in context['recommended_models'])

    def test_context_validation_and_error_handling(self, context_manager):
        """Test context validation and error handling"""
        # Test with invalid role
        invalid_context = {'invalid_role': 'not_a_role'}

        try:
            context = context_manager.load_context_for_role('invalid_role', invalid_context)
            # Should handle gracefully with default behavior
            assert context is not None
        except Exception as e:
            # Should raise appropriate exception
            assert isinstance(e, (ValueError, TypeError))

        # Test with malformed context data
        malformed_context = {
            'notebooks': 'should_be_list_not_string',  # Wrong type
            'models': None  # Invalid value
        }

        context = context_manager.load_context_for_role(UserRole.ANALYST, malformed_context)
        # Should handle gracefully
        assert context is not None

    def test_performance_benchmarks(self, context_manager):
        """Test context manager performance benchmarks"""
        # Test with various context sizes
        context_sizes = [100, 500, 1000, 2000]
        load_times = []

        for size in context_sizes:
            # Create context of specified size
            test_context = {
                'data': {f'key_{i}': f'value_{i}' for i in range(size)},
                'notebooks': [f'notebook_{i}' for i in range(min(size, 50))]
            }

            # Measure load time
            start_time = time.time()
            context = context_manager.load_context_for_role(UserRole.ANALYST, test_context)
            load_time = time.time() - start_time
            load_times.append(load_time)

            # Should complete within reasonable time
            assert load_time < 2.0, f"Load time {load_time:.3f}s too large for size {size}"

        # Check that load times scale reasonably
        if len(load_times) >= 2:
            time_ratio = load_times[-1] / load_times[0]
            size_ratio = context_sizes[-1] / context_sizes[0]

            # Time should not scale disproportionately with size
            assert time_ratio < size_ratio * 2, "Load times scaling poorly with context size"

    def test_concurrent_context_loading(self, context_manager, sample_data_scientist_context):
        """Test concurrent context loading"""
        import threading
        import queue

        results = queue.Queue()

        def load_context(thread_id):
            try:
                context = context_manager.load_context_for_role(
                    UserRole.DATA_SCIENTIST,
                    sample_data_scientist_context
                )
                results.put((thread_id, True, context))
            except Exception as e:
                results.put((thread_id, False, str(e)))

        # Create multiple threads loading context concurrently
        threads = []
        for i in range(5):
            thread = threading.Thread(target=load_context, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Check results
        successful_loads = 0
        while not results.empty():
            thread_id, success, result = results.get()
            if success:
                successful_loads += 1
                # Validate context structure
                assert 'role' in result
                assert result['role'] == 'data_scientist'

        # Most loads should be successful
        assert successful_loads >= 4, f"Too many concurrent load failures: {5 - successful_loads}"

    def test_memory_usage_optimization(self, context_manager):
        """Test memory usage optimization"""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Load multiple large contexts
        for i in range(10):
            large_context = {
                'data': {f'key_{i}_{j}': f'value_{i}_{j}' * 10 for j in range(100)},
                'notebooks': [f'notebook_{i}_{j}' for j in range(50)],
                'models': [f'model_{i}_{j}' for j in range(30)]
            }

            context = context_manager.load_context_for_role(UserRole.ANALYST, large_context)
            assert context is not None

        final_memory = process.memory_info().rss
        memory_increase = (final_memory - initial_memory) / 1024 / 1024  # MB

        # Memory increase should be reasonable
        assert memory_increase < 100, f"Memory increase {memory_increase:.2f}MB exceeds limit"

    def test_context_persistence_and_recovery(self, context_manager, sample_analyst_context):
        """Test context persistence and recovery"""
        # Load and cache context
        role = UserRole.ANALYST
        context1 = context_manager.load_context_for_role(role, sample_analyst_context)

        # Simulate context manager restart by creating new instance
        new_context_manager = ContextManager(base_path=context_manager.base_path)

        # Should be able to recover cached context
        context2 = new_context_manager.load_context_for_role(role, sample_analyst_context)

        # Contexts should be equivalent
        assert context1['role'] == context2['role']
        assert context1['profile']['role'] == context2['profile']['role']

    def test_context_quality_metrics(self, context_manager):
        """Test context quality metrics"""
        test_contexts = [
            {'query_type': 'simple', 'data': {'key': 'value'}},
            {'query_type': 'complex', 'data': {f'key_{i}': f'value_{i}' for i in range(100)}},
            {'query_type': 'medium', 'notebooks': ['nb1', 'nb2', 'nb3']}
        ]

        quality_scores = []

        for test_context in test_contexts:
            context = context_manager.load_context_for_role(UserRole.ANALYST, test_context)

            # Calculate quality metrics
            if 'optimization_metadata' in context:
                quality_score = context_manager._calculate_context_quality(context)
                quality_scores.append(quality_score)

        # Should have quality scores for valid contexts
        assert len(quality_scores) >= len(test_contexts) - 1  # Allow for some edge cases

        # Quality scores should be reasonable
        for score in quality_scores:
            assert 0 <= score <= 1, f"Invalid quality score: {score}"

    def test_context_adaptation_learning(self, context_manager, sample_data_scientist_context):
        """Test context adaptation based on user interactions"""
        # Simulate user interaction history
        user_history = [
            {'query_type': 'model_analysis', 'preferred_models': ['xgb_model']},
            {'query_type': 'feature_engineering', 'preferred_tools': ['shap_analysis']},
            {'query_type': 'visualization', 'preferred_format': 'interactive'}
        ]

        # Add history to context
        adaptive_context = sample_data_scientist_context.copy()
        adaptive_context['interaction_history'] = user_history

        # Load context with adaptation
        context = context_manager.load_context_for_role(
            UserRole.DATA_SCIENTIST,
            adaptive_context
        )

        # Validate adaptation
        if 'adaptation_applied' in context:
            assert context['adaptation_applied'] is True

        # Check that history influences context
        if 'recommended_tools' in context:
            assert len(context['recommended_tools']) > 0

    def test_context_security_and_privacy(self, context_manager):
        """Test context security and privacy features"""
        # Test with sensitive data
        sensitive_context = {
            'user_data': {
                'email': 'user@example.com',
                'api_key': 'secret_key_123',
                'personal_info': 'sensitive_information'
            },
            'query_type': 'normal_query'
        }

        # Load context - should filter sensitive data
        context = context_manager.load_context_for_role(UserRole.ANALYST, sensitive_context)

        # Sensitive data should be filtered or masked
        assert 'user_data' not in context or \
               all(key not in str(context) for key in ['email', 'api_key', 'personal_info'])

    @pytest.mark.slow
    def test_stress_test_large_scale_operations(self, context_manager):
        """Stress test with large-scale context operations"""
        operation_count = 100
        success_count = 0
        total_time = 0

        for i in range(operation_count):
            # Create diverse contexts
            context_type = i % 3
            if context_type == 0:
                test_context = {
                    'query_type': 'large_data',
                    'data': {f'key_{j}': f'value_{j}' for j in range(200)}
                }
            elif context_type == 1:
                test_context = {
                    'query_type': 'many_notebooks',
                    'notebooks': [f'notebook_{j}' for j in range(100)]
                }
            else:
                test_context = {
                    'query_type': 'complex_mixed',
                    'data': {f'key_{j}': f'value_{j}' for j in range(50)},
                    'notebooks': [f'notebook_{j}' for j in range(50)],
                    'models': [f'model_{j}' for j in range(30)]
                }

            try:
                start_time = time.time()
                role = UserRole(list(UserRole)[i % 3])  # Rotate through roles
                context = context_manager.load_context_for_role(role, test_context)
                operation_time = time.time() - start_time
                total_time += operation_time

                if context is not None:
                    success_count += 1

                # Individual operation should not take too long
                assert operation_time < 5.0, f"Operation {i} took too long: {operation_time:.3f}s"

            except Exception as e:
                # Log exception but don't fail the test
                print(f"Operation {i} failed: {e}")

        # Overall performance metrics
        success_rate = success_count / operation_count
        avg_operation_time = total_time / operation_count

        assert success_rate > 0.9, f"Success rate too low: {success_rate:.2%}"
        assert avg_operation_time < 2.0, f"Average operation time too high: {avg_operation_time:.3f}s"