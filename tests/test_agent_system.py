#!/usr/bin/env python3
"""
Comprehensive Test Suite for Script Ohio 2.0 Agent System

This module provides unit tests, integration tests, and system validation
for the entire agent architecture.

Author: Claude Code Assistant
Created: 2025-11-07
Version: 1.0
"""

import unittest
import sys
import os
import time
import json
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Add agents directory to path for development
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import system components using absolute imports
from agents.core.context_manager import ContextManager, UserRole
from agents.core.agent_framework import AgentFactory, RequestRouter, BaseAgent, AgentRequest, PermissionLevel
from agents.core.tool_loader import ToolLoader, ToolCategory
from agents.analytics_orchestrator import AnalyticsOrchestrator, AnalyticsRequest
from src.models.execution.engine import ModelExecutionEngine

class TestContextManager(unittest.TestCase):
    """Test cases for Context Manager"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.context_manager = ContextManager(base_path=self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_role_detection_analyst(self):
        """Test analyst role detection"""
        user_context = {
            'notebooks': ['starter_pack/01_intro_to_data.ipynb'],
            'models': ['ridge_model_2025.joblib'],
            'query_type': 'learn about college football data'
        }

        detected_role = self.context_manager.detect_user_role(user_context)
        self.assertEqual(detected_role, UserRole.ANALYST)

    def test_role_detection_data_scientist(self):
        """Test data scientist role detection"""
        user_context = {
            'notebooks': ['model_pack/06_shap_interpretability.ipynb'],
            'models': ['xgb_home_win_model_2025.pkl'],
            'query_type': 'advanced feature engineering and model optimization'
        }

        detected_role = self.context_manager.detect_user_role(user_context)
        self.assertEqual(detected_role, UserRole.DATA_SCIENTIST)

    def test_role_detection_production(self):
        """Test production role detection"""
        user_context = {
            'models': ['ridge_model_2025.joblib'],
            'query_type': 'predict game outcomes for production use'
        }

        detected_role = self.context_manager.detect_user_role(user_context)
        self.assertEqual(detected_role, UserRole.PRODUCTION)

    def test_context_loading_for_analyst(self):
        """Test context loading for analyst role"""
        user_context = {
            'notebooks': ['starter_pack/01_intro_to_data.ipynb'],
            'query_type': 'learning'
        }

        context = self.context_manager.load_context_for_role(UserRole.ANALYST, user_context)

        self.assertIn('role', context)
        self.assertEqual(context['role'], 'analyst')
        self.assertIn('profile', context)
        self.assertIn('data', context)
        self.assertIn('notebooks', context)
        self.assertIn('optimization_applied', context)
        self.assertTrue(context['optimization_applied'])

    def test_token_optimization(self):
        """Test token optimization functionality"""
        # Create a large context to trigger optimization
        large_context = {
            'data': {f'key_{i}': f'value_{i}' * 100 for i in range(100)},
            'notebooks': [{'path': f'notebook_{i}'} for i in range(50)],
            'features': [{'name': f'feature_{i}'} for i in range(86)]
        }

        # Apply optimization with small budget
        optimized = self.context_manager._optimize_context(large_context, 1000)

        self.assertIn('optimization_metadata', optimized)
        self.assertLess(len(str(optimized)), len(str(large_context)))

    def test_caching_functionality(self):
        """Test context caching"""
        user_context = {'query_type': 'test_query'}
        role = UserRole.ANALYST

        # First call should miss cache
        context1 = self.context_manager.load_context_for_role(role, user_context)

        # Second call should hit cache
        context2 = self.context_manager.load_context_for_role(role, user_context)

        # Should be the same object (cached)
        self.assertEqual(context1, context2)

        # Check cache metrics
        metrics = self.context_manager.get_performance_metrics()
        self.assertGreater(metrics['cache_hit_rate'], 0)

class TestToolLoader(unittest.TestCase):
    """Test cases for Tool Loader"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.tool_loader = ToolLoader(tools_directory=self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_builtin_tools_loading(self):
        """Test that built-in tools are loaded"""
        tools = self.tool_loader.list_tools()
        self.assertGreater(len(tools), 0)

        tool_names = [tool['name'] for tool in tools]
        self.assertIn('load_notebook_metadata', tool_names)
        self.assertIn('predict_game_outcome', tool_names)
        self.assertIn('create_learning_path_chart', tool_names)

    def test_tool_execution_success(self):
        """Test successful tool execution"""
        result = self.tool_loader.execute_tool(
            'load_notebook_metadata',
            {
                'notebook_paths': ['starter_pack/01_intro_to_data.ipynb'],
                'include_content': False
            },
            {'role': 'analyst'}
        )

        self.assertTrue(result.success)
        self.assertIn('metadata', result.result)
        self.assertIn('summary', result.result)

    def test_tool_execution_not_found(self):
        """Test tool execution with non-existent tool"""
        result = self.tool_loader.execute_tool(
            'non_existent_tool',
            {},
            {'role': 'analyst'}
        )

        self.assertFalse(result.success)
        self.assertIn('Tool not found', result.error_message)

    def test_permission_filtering(self):
        """Test permission-based tool filtering"""
        # Test different permission levels
        read_only_tools = self.tool_loader.get_tools_for_permission_level(1)
        admin_tools = self.tool_loader.get_tools_for_permission_level(4)

        self.assertLessEqual(len(read_only_tools), len(admin_tools))

    def test_tool_status_report(self):
        """Test tool status report generation"""
        status = self.tool_loader.get_tool_status_report()

        self.assertIn('total_tools', status)
        self.assertIn('active_tools', status)
        self.assertIn('categories', status)
        self.assertGreater(status['total_tools'], 0)

class TestAgentFramework(unittest.TestCase):
    """Test cases for Agent Framework"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.agent_factory = AgentFactory(base_path=self.temp_dir)
        self.request_router = RequestRouter(self.agent_factory)

    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_agent_factory_initialization(self):
        """Test agent factory initialization"""
        self.assertIsNotNone(self.agent_factory.tool_loader)
        self.assertEqual(len(self.agent_factory.agent_registry), 0)
        self.assertEqual(len(self.agent_factory.agents), 0)

    def test_agent_registration_and_creation(self):
        """Test agent registration and creation"""
        from agents.core.agent_framework import LearningNavigatorAgent

        # Register agent class
        self.agent_factory.register_agent_class(LearningNavigatorAgent, 'test_agent')

        # Create agent instance
        agent = self.agent_factory.create_agent('test_agent', 'test_001')

        self.assertIsNotNone(agent)
        self.assertEqual(agent.agent_id, 'test_001')
        self.assertEqual(agent.name, 'Learning Navigator')

    def test_agent_request_validation(self):
        """Test agent request validation"""
        from agents.core.agent_framework import LearningNavigatorAgent

        # Create agent
        self.agent_factory.register_agent_class(LearningNavigatorAgent, 'learning_navigator')
        agent = self.agent_factory.create_agent('learning_navigator', 'nav_test')

        # Create valid request
        valid_request = AgentRequest(
            request_id='req_001',
            agent_type='learning_navigator',
            action='guide_learning_path',
            parameters={'current_notebook': 'start'},
            user_context={'role': 'analyst'},
            timestamp=time.time()
        )

        self.assertTrue(agent.can_handle_request(valid_request, PermissionLevel.READ_EXECUTE))

        # Create invalid request (wrong action)
        invalid_request = AgentRequest(
            request_id='req_002',
            agent_type='learning_navigator',
            action='invalid_action',
            parameters={},
            user_context={'role': 'analyst'},
            timestamp=time.time()
        )

        self.assertFalse(agent.can_handle_request(invalid_request, PermissionLevel.READ_EXECUTE))

    def test_request_routing(self):
        """Test request routing functionality"""
        from agents.core.agent_framework import LearningNavigatorAgent

        # Setup agent
        self.agent_factory.register_agent_class(LearningNavigatorAgent, 'learning_navigator')
        self.agent_factory.create_agent('learning_navigator', 'nav_test')

        # Submit request
        request = AgentRequest(
            request_id='route_test',
            agent_type='learning_navigator',
            action='guide_learning_path',
            parameters={'current_notebook': 'start'},
            user_context={'role': 'analyst'},
            timestamp=time.time()
        )

        request_id = self.request_router.submit_request(request, PermissionLevel.READ_EXECUTE)
        self.assertEqual(request_id, 'route_test')

        # Process request
        self.request_router.process_requests(PermissionLevel.READ_EXECUTE)

        # Check result
        status = self.request_router.get_request_status(request_id)
        self.assertIsNotNone(status)
        self.assertEqual(status['status'], 'completed')

class TestModelExecutionEngine(unittest.TestCase):
    """Test cases for Model Execution Engine"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.model_engine = ModelExecutionEngine(agent_id='test_model_engine')

    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_model_engine_initialization(self):
        """Test model engine initialization"""
        self.assertIsNotNone(self.model_engine.models)
        self.assertIsNotNone(self.model_engine.prediction_history)
        self.assertEqual(self.model_engine.name, 'Model Execution Engine')

    def test_game_prediction_structure(self):
        """Test game prediction structure"""
        # Mock the model loading to avoid dependency on actual models
        with patch.object(self.model_engine, '_load_available_models'):
            with patch.object(self.model_engine, 'models') as mock_models:
                # Mock model metadata
                mock_models.__contains__ = Mock(return_value=True)
                mock_models.__getitem__ = Mock(return_value=Mock(
                    model_type='regression',
                    features_required=['home_talent', 'away_talent'],
                    file_path='/mock/path/ridge_model_2025.joblib'
                ))

                result = self.model_engine._predict_game_outcome({
                    'home_team': 'Ohio State',
                    'away_team': 'Michigan',
                    'model_type': 'ridge_model_2025'
                }, {'role': 'data_scientist'})

                # The result should contain the expected structure
                self.assertIn('success', result)

    def test_batch_predictions(self):
        """Test batch prediction functionality"""
        # Mock single prediction method
        with patch.object(self.model_engine, '_predict_game_outcome') as mock_predict:
            mock_predict.return_value = {
                'success': True,
                'prediction': {'predicted_margin': 7.5}
            }

            games = [
                {'home_team': 'Ohio State', 'away_team': 'Michigan'},
                {'home_team': 'Alabama', 'away_team': 'Georgia'}
            ]

            result = self.model_engine._batch_predictions({
                'games': games,
                'model_type': 'ridge_model_2025'
            }, {'role': 'data_scientist'})

            self.assertTrue(result['success'])
            self.assertEqual(result['total_games'], 2)
            self.assertEqual(len(result['predictions']), 2)
            self.assertEqual(mock_predict.call_count, 2)

    def test_model_comparison(self):
        """Test model comparison functionality"""
        with patch.object(self.model_engine, '_predict_game_outcome') as mock_predict:
            mock_predict.return_value = {
                'success': True,
                'prediction': {'home_win_probability': 0.65}
            }

            result = self.model_engine._model_comparison({
                'home_team': 'Ohio State',
                'away_team': 'Michigan',
                'models': ['ridge_model_2025', 'xgb_home_win_model_2025']
            }, {'role': 'data_scientist'})

            self.assertTrue(result['success'])
            self.assertEqual(len(result['comparison']), 2)

    def test_model_status_reporting(self):
        """Test model status reporting"""
        status = self.model_engine.get_model_status()

        self.assertIn('total_models', status)
        self.assertIn('available_models', status)
        self.assertIn('total_predictions_made', status)

class TestAnalyticsOrchestrator(unittest.TestCase):
    """Test cases for Analytics Orchestrator"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.orchestrator = AnalyticsOrchestrator(base_path=self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_orchestrator_initialization(self):
        """Test orchestrator initialization"""
        # self.assertIsNotNone(self.orchestrator.context_manager) # Deprecated
        self.assertIsNotNone(self.orchestrator.agent_factory)
        self.assertIsNotNone(self.orchestrator.request_router)

    def test_request_analysis(self):
        """Test request analysis functionality"""
        request = AnalyticsRequest(
            user_id='test_user',
            query='I want to learn about college football data',
            query_type='learning',
            parameters={},
            context_hints={'skill_level': 'beginner'}
        )

        requirements = self.orchestrator._analyze_request_requirements(request, {'role': 'analyst'})

        self.assertGreater(len(requirements), 0)
        self.assertEqual(requirements[0]['agent_type'], 'learning_navigator')

    def test_session_management(self):
        """Test session management"""
        # Start session
        session_id = self.orchestrator.start_session('test_user', {'role': 'analyst'})
        self.assertIsNotNone(session_id)

        # Check active sessions
        self.assertIn(session_id, self.orchestrator.active_sessions)

        # End session
        session_summary = self.orchestrator.end_session(session_id)
        self.assertEqual(session_summary['user_id'], 'test_user')
        self.assertNotIn(session_id, self.orchestrator.active_sessions)

    def test_system_status(self):
        """Test system status reporting"""
        status = self.orchestrator.get_system_status()

        self.assertIn('orchestrator', status)
        # self.assertIn('context_manager', status) # Deprecated
        self.assertIn('agent_factory', status)
        self.assertIn('request_router', status)

class TestIntegration(unittest.TestCase):
    """Integration tests for the complete system"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.orchestrator = AnalyticsOrchestrator(base_path=self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_end_to_end_learning_request(self):
        """Test complete learning request flow"""
        request = AnalyticsRequest(
            user_id='integration_test_user',
            query='I want to learn about college football analytics',
            query_type='learning',
            parameters={'current_notebook': 'start'},
            context_hints={'skill_level': 'beginner'},
            priority=2
        )

        response = self.orchestrator.process_analytics_request(request)

        self.assertIsNotNone(response)
        self.assertIn(response.status, ['success', 'partial_success'])
        self.assertGreater(len(response.insights), 0)

    @unittest.skip("Context optimization logic has changed/deprecated")
    def test_context_optimization_integration(self):
        """Test context optimization in full workflow"""
        # Create a large context
        large_context_hints = {
            'notebooks': ['starter_pack/01_intro_to_data.ipynb'] * 50,
            'models': ['ridge_model_2025.joblib'] * 20,
            'query_type': 'complex analysis with many parameters'
        }

        request = AnalyticsRequest(
            user_id='test_user',
            query='Complex analysis request',
            query_type='analysis',
            parameters={},
            context_hints=large_context_hints
        )

        response = self.orchestrator.process_analytics_request(request)

        self.assertIsNotNone(response)
        if hasattr(response, 'metadata'):
            self.assertIn('context_optimized', response.metadata)

    def test_performance_metrics_tracking(self):
        """Test performance metrics are properly tracked"""
        # Make multiple requests
        for i in range(3):
            request = AnalyticsRequest(
                user_id=f'perf_test_user_{i}',
                query=f'Test request {i}',
                query_type='learning',
                parameters={},
                context_hints={'skill_level': 'beginner'}
            )
            self.orchestrator.process_analytics_request(request)

        # Check metrics
        metrics = self.orchestrator.performance_metrics
        self.assertEqual(metrics['total_requests'], 3)
        self.assertGreater(metrics['average_response_time'], 0)

class TestSystemValidation(unittest.TestCase):
    """System validation tests"""

    def test_permission_levels_enforcement(self):
        """Test that permission levels are properly enforced"""
        temp_dir = tempfile.mkdtemp()
        try:
            from agents.core.agent_framework import LearningNavigatorAgent

            # Create agent with read-only permissions
            agent_factory = AgentFactory(base_path=temp_dir)
            agent_factory.register_agent_class(LearningNavigatorAgent, 'test_agent')
            agent = agent_factory.create_agent('test_agent', 'test_id')

            # Test that agent respects permissions
            request = AgentRequest(
                request_id='perm_test',
                agent_type='learning_navigator',
                action='guide_learning_path',
                parameters={},
                user_context={'role': 'analyst'},
                timestamp=time.time()
            )

            # Should work with read_execute permissions
            self.assertTrue(agent.can_handle_request(request, PermissionLevel.READ_EXECUTE))

            # Should fail with read_only permissions
            self.assertFalse(agent.can_handle_request(request, PermissionLevel.READ_ONLY))

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_error_handling_and_recovery(self):
        """Test system error handling and recovery"""
        temp_dir = tempfile.mkdtemp()
        try:
            orchestrator = AnalyticsOrchestrator(base_path=temp_dir)

            # Test with invalid request
            invalid_request = AnalyticsRequest(
                user_id='',
                query='',  # Empty query
                query_type='invalid_type',
                parameters={'invalid': 'data'},
                context_hints={'invalid': 'context'}
            )

            response = orchestrator.process_analytics_request(invalid_request)

            # Should handle gracefully
            self.assertIsNotNone(response)
            self.assertEqual(response.request_id, invalid_request.request_id)

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_resource_cleanup(self):
        """Test that resources are properly cleaned up"""
        temp_dir = tempfile.mkdtemp()
        try:
            orchestrator = AnalyticsOrchestrator(base_path=temp_dir)

            # Create multiple sessions
            session_ids = []
            for i in range(5):
                session_id = orchestrator.start_session(f'user_{i}')
                session_ids.append(session_id)

            # Verify sessions are active
            self.assertEqual(len(orchestrator.active_sessions), 5)

            # End all sessions
            for session_id in session_ids:
                orchestrator.end_session(session_id)

            # Verify cleanup
            self.assertEqual(len(orchestrator.active_sessions), 0)
            self.assertGreaterEqual(len(orchestrator.session_history), 5)

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == '__main__':
    # Configure test runner
    unittest.main(verbosity=2)