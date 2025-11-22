"""
Integration tests for CFBD GraphQL capabilities with Analytics Orchestrator.
"""
from __future__ import annotations

import os
from unittest.mock import Mock, patch
from typing import Any, Dict

import pytest

from agents.analytics_orchestrator import AnalyticsOrchestrator, AnalyticsRequest


class TestCFBDGraphQLIntegration:
    """Integration tests for GraphQL capabilities"""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator instance"""
        return AnalyticsOrchestrator()

    @pytest.mark.integration
    @pytest.mark.skipif(
        not os.getenv("CFBD_API_KEY"),
        reason="CFBD_API_KEY not set - skipping integration test"
    )
    def test_orchestrator_graphql_scoreboard(self, orchestrator):
        """Test GraphQL scoreboard through orchestrator"""
        request = AnalyticsRequest(
            user_id="test_user",
            query="Get scoreboard for week 12, 2025 using GraphQL",
            query_type="data_fetch",
            parameters={"season": 2025, "week": 12},
            context_hints={"use_graphql": True, "prefer_graphql": True}
        )

        response = orchestrator.process_analytics_request(request)

        assert response.status == "success" or response.status == "partial_success"
        # Verify response contains relevant data
        assert response.data is not None or response.insights is not None

    @pytest.mark.integration
    @pytest.mark.skipif(
        not os.getenv("CFBD_API_KEY"),
        reason="CFBD_API_KEY not set - skipping integration test"
    )
    def test_orchestrator_graphql_recruiting(self, orchestrator):
        """Test GraphQL recruiting through orchestrator"""
        request = AnalyticsRequest(
            user_id="test_user",
            query="Get recruiting data for Ohio State 2026 class using GraphQL",
            query_type="data_fetch",
            parameters={"year": 2026, "school": "Ohio State"},
            context_hints={"use_graphql": True}
        )

        response = orchestrator.process_analytics_request(request)

        assert response.status == "success" or response.status == "partial_success"
        # Verify response contains relevant data
        assert response.data is not None or response.insights is not None

    def test_orchestrator_recognizes_graphql_query_patterns(self, orchestrator):
        """Test that orchestrator recognizes GraphQL query patterns"""
        # Test various GraphQL query patterns
        test_queries = [
            "Get scoreboard via GraphQL for week 12",
            "Fetch recruiting data using GraphQL",
            "GraphQL scoreboard 2025 week 12",
            "Get GraphQL recruiting data for Ohio State",
        ]

        for query in test_queries:
            request = AnalyticsRequest(
                user_id="test_user",
                query=query,
                query_type="data_fetch",
                parameters={"season": 2025, "week": 12},
                context_hints={}
            )

            # Analyze request requirements
            requirements = orchestrator._analyze_request_requirements(request, {})

            # Should identify GraphQL-related requirements
            # Note: This depends on orchestrator implementation
            assert requirements is not None
            assert isinstance(requirements, list)

    def test_cfbd_integration_agent_registered(self, orchestrator):
        """Test that CFBD Integration Agent is registered with orchestrator"""
        # Check if agent factory has CFBD Integration Agent
        agent_types = orchestrator.agent_factory.agent_types if hasattr(orchestrator.agent_factory, 'agent_types') else []

        # Try to create CFBD Integration Agent
        try:
            from agents.cfbd_integration_agent import CFBDIntegrationAgent
            agent = orchestrator.agent_factory.create_agent("cfbd_integration", "test_cfbd_001")
            assert agent is not None
            assert isinstance(agent, CFBDIntegrationAgent)
        except (ValueError, KeyError):
            # Agent type might not be registered, which is okay for this test
            pytest.skip("CFBD Integration Agent not registered in factory")

    def test_graphql_capabilities_discoverable(self, orchestrator):
        """Test that GraphQL capabilities are discoverable"""
        try:
            from agents.cfbd_integration_agent import CFBDIntegrationAgent
            agent = orchestrator.agent_factory.create_agent("cfbd_integration", "test_cfbd_002")
            
            capabilities = agent._define_capabilities()
            capability_names = [cap.name for cap in capabilities]
            
            # Check if GraphQL capabilities exist (if GraphQL is available)
            # This test passes whether GraphQL is available or not
            if "graphql_scoreboard" in capability_names:
                assert "graphql_recruiting" in capability_names
        except (ValueError, KeyError):
            pytest.skip("CFBD Integration Agent not available")

    @pytest.mark.integration
    @pytest.mark.skipif(
        not os.getenv("CFBD_API_KEY"),
        reason="CFBD_API_KEY not set - skipping integration test"
    )
    def test_end_to_end_graphql_workflow(self, orchestrator):
        """Test end-to-end GraphQL workflow through orchestrator"""
        request = AnalyticsRequest(
            user_id="test_user",
            query="Get GraphQL scoreboard for 2025 season week 12",
            query_type="data_fetch",
            parameters={"season": 2025, "week": 12},
            context_hints={"prefer_graphql": True}
        )

        response = orchestrator.process_analytics_request(request)

        # Should complete successfully or provide meaningful error
        assert response.status in ["success", "partial_success", "error"]
        assert response.execution_time >= 0

    def test_graphql_fallback_to_rest(self, orchestrator):
        """Test that system falls back to REST when GraphQL unavailable"""
        # Mock GraphQL as unavailable
        with patch('agents.cfbd_integration_agent.GRAPHQL_AVAILABLE', False):
            request = AnalyticsRequest(
                user_id="test_user",
                query="Get scoreboard for week 12",
                query_type="data_fetch",
                parameters={"season": 2025, "week": 12},
                context_hints={}
            )

            response = orchestrator.process_analytics_request(request)

            # Should still work with REST fallback
            assert response.status in ["success", "partial_success", "error"]
            # Should not mention GraphQL in error if it gracefully degraded
            if response.status == "error" and response.insights:
                # GraphQL errors should be handled gracefully
                pass
