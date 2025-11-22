"""
Test suite for CFBD Integration Agent GraphQL capabilities.
"""
from __future__ import annotations

import time
from unittest.mock import Mock, patch, MagicMock
from typing import Any, Dict

import pytest

from agents.cfbd_integration_agent import CFBDIntegrationAgent, GRAPHQL_AVAILABLE


class TestCFBDIntegrationAgentGraphQL:
    """Test GraphQL capabilities of CFBD Integration Agent"""

    @pytest.fixture
    def mock_graphql_client(self):
        """Mock GraphQL client"""
        mock_client = Mock()
        mock_client.get_scoreboard.return_value = {
            "game": [
                {
                    "id": 401485131,
                    "season": 2025,
                    "week": 12,
                    "homeTeam": "Ohio State",
                    "awayTeam": "Michigan",
                    "homePoints": 28,
                    "awayPoints": 24,
                    "startDate": "2025-11-22T12:00:00Z",
                }
            ]
        }
        mock_client.get_recruits.return_value = {
            "recruit": [
                {
                    "id": 12345,
                    "name": "John Doe",
                    "stars": 5,
                    "rating": 0.98,
                    "position": {"position": "QB", "positionGroup": "Offense"},
                    "college": {"school": "Ohio State", "conference": "Big Ten"},
                    "year": 2026,
                }
            ]
        }
        return mock_client

    @pytest.fixture
    def mock_cache(self):
        """Mock cache provider"""
        cache = Mock()
        cache.get.return_value = None
        return cache

    @pytest.fixture
    def agent_with_graphql(self, mock_graphql_client, mock_cache):
        """Agent with GraphQL client initialized"""
        with patch('agents.cfbd_integration_agent.CFBDGraphQLClient', return_value=mock_graphql_client):
            with patch('agents.cfbd_integration_agent.GRAPHQL_AVAILABLE', True):
                agent = CFBDIntegrationAgent(
                    "test_001",
                    graphql_client=mock_graphql_client,
                    cache_provider=mock_cache
                )
                return agent

    @pytest.fixture
    def agent_without_graphql(self):
        """Agent without GraphQL client"""
        with patch('agents.cfbd_integration_agent.GRAPHQL_AVAILABLE', False):
            agent = CFBDIntegrationAgent("test_002")
            return agent

    def test_graphql_capabilities_registered(self, agent_with_graphql):
        """Test that GraphQL capabilities are registered when available"""
        capabilities = agent_with_graphql._define_capabilities()
        capability_names = [cap.name for cap in capabilities]

        assert "graphql_scoreboard" in capability_names
        assert "graphql_recruiting" in capability_names

    def test_graphql_capabilities_not_registered_when_unavailable(self, agent_without_graphql):
        """Test that GraphQL capabilities are not registered when unavailable"""
        capabilities = agent_without_graphql._define_capabilities()
        capability_names = [cap.name for cap in capabilities]

        assert "graphql_scoreboard" not in capability_names
        assert "graphql_recruiting" not in capability_names

    def test_graphql_scoreboard_success(self, agent_with_graphql, mock_graphql_client):
        """Test successful GraphQL scoreboard request"""
        result = agent_with_graphql._execute_action(
            "graphql_scoreboard",
            {"season": 2025, "week": 12},
            {}
        )

        assert result["status"] == "success"
        assert result["season"] == 2025
        assert result["week"] == 12
        assert len(result["games"]) == 1
        assert result["games"][0]["homeTeam"] == "Ohio State"
        assert result["data_source"] == "GraphQL API"
        mock_graphql_client.get_scoreboard.assert_called_once_with(season=2025, week=12)

    def test_graphql_scoreboard_without_week(self, agent_with_graphql, mock_graphql_client):
        """Test GraphQL scoreboard request without week parameter"""
        result = agent_with_graphql._execute_action(
            "graphql_scoreboard",
            {"season": 2025},
            {}
        )

        assert result["status"] == "success"
        assert result["season"] == 2025
        assert result["week"] is None
        mock_graphql_client.get_scoreboard.assert_called_once_with(season=2025, week=None)

    def test_graphql_scoreboard_missing_season(self, agent_with_graphql):
        """Test GraphQL scoreboard with missing required parameter"""
        with pytest.raises(ValueError, match="Missing required parameter: season"):
            agent_with_graphql._execute_action(
                "graphql_scoreboard",
                {"week": 12},
                {}
            )

    def test_graphql_scoreboard_invalid_type(self, agent_with_graphql):
        """Test GraphQL scoreboard with invalid parameter type"""
        with pytest.raises(ValueError, match="Invalid parameter type"):
            agent_with_graphql._execute_action(
                "graphql_scoreboard",
                {"season": "2025", "week": 12},
                {}
            )

    def test_graphql_scoreboard_invalid_week_type(self, agent_with_graphql):
        """Test GraphQL scoreboard with invalid week type"""
        with pytest.raises(ValueError, match="Invalid parameter type"):
            agent_with_graphql._execute_action(
                "graphql_scoreboard",
                {"season": 2025, "week": "twelve"},
                {}
            )

    def test_graphql_recruiting_success(self, agent_with_graphql, mock_graphql_client):
        """Test successful GraphQL recruiting request"""
        result = agent_with_graphql._execute_action(
            "graphql_recruiting",
            {"year": 2026, "school": "Ohio State", "limit": 10},
            {}
        )

        assert result["status"] == "success"
        assert result["year"] == 2026
        assert result["school"] == "Ohio State"
        assert len(result["recruits"]) == 1
        assert result["recruits"][0]["name"] == "John Doe"
        assert result["data_source"] == "GraphQL API"
        mock_graphql_client.get_recruits.assert_called_once_with(
            season=2026, team="Ohio State", limit=10
        )

    def test_graphql_recruiting_flexible_parameters_year(self, agent_with_graphql, mock_graphql_client):
        """Test GraphQL recruiting with 'season' instead of 'year'"""
        result = agent_with_graphql._execute_action(
            "graphql_recruiting",
            {"season": 2026, "team": "Ohio State"},
            {}
        )

        assert result["status"] == "success"
        assert result["year"] == 2026
        mock_graphql_client.get_recruits.assert_called_once_with(
            season=2026, team="Ohio State", limit=25  # Default limit
        )

    def test_graphql_recruiting_flexible_parameters_school(self, agent_with_graphql, mock_graphql_client):
        """Test GraphQL recruiting with 'school' parameter"""
        result = agent_with_graphql._execute_action(
            "graphql_recruiting",
            {"year": 2026, "school": "Ohio State"},
            {}
        )

        assert result["status"] == "success"
        assert result["school"] == "Ohio State"
        mock_graphql_client.get_recruits.assert_called_once_with(
            season=2026, team="Ohio State", limit=25
        )

    def test_graphql_recruiting_missing_year(self, agent_with_graphql):
        """Test GraphQL recruiting with missing required parameter"""
        with pytest.raises(ValueError, match="Missing required parameter: year"):
            agent_with_graphql._execute_action(
                "graphql_recruiting",
                {"school": "Ohio State"},
                {}
            )

    def test_graphql_recruiting_invalid_year_type(self, agent_with_graphql):
        """Test GraphQL recruiting with invalid year type"""
        with pytest.raises(ValueError, match="Invalid parameter type"):
            agent_with_graphql._execute_action(
                "graphql_recruiting",
                {"year": "2026", "school": "Ohio State"},
                {}
            )

    def test_graphql_recruiting_invalid_limit_type(self, agent_with_graphql):
        """Test GraphQL recruiting with invalid limit type"""
        with pytest.raises(ValueError, match="Invalid parameter type"):
            agent_with_graphql._execute_action(
                "graphql_recruiting",
                {"year": 2026, "limit": "ten"},
                {}
            )

    def test_graphql_scoreboard_caching(self, agent_with_graphql, mock_graphql_client, mock_cache):
        """Test GraphQL scoreboard caching"""
        # Setup cache to return cached data
        cached_games = [{"id": 1, "cached": True, "homeTeam": "Cached Team"}]
        mock_cache.get.return_value = {"games": cached_games}

        result = agent_with_graphql._execute_action(
            "graphql_scoreboard",
            {"season": 2025, "week": 12},
            {}
        )

        assert result["cached"] is True
        assert result["data_source"] == "GraphQL API (cached)"
        assert result["games"] == cached_games
        # Should not call API if cached
        mock_graphql_client.get_scoreboard.assert_not_called()

    def test_graphql_scoreboard_cache_miss(self, agent_with_graphql, mock_graphql_client, mock_cache):
        """Test GraphQL scoreboard cache miss and subsequent caching"""
        # Cache returns None (miss)
        mock_cache.get.return_value = None

        result = agent_with_graphql._execute_action(
            "graphql_scoreboard",
            {"season": 2025, "week": 12},
            {}
        )

        assert result["status"] == "success"
        assert result["cached"] is not True  # Not from cache
        # Should call API
        mock_graphql_client.get_scoreboard.assert_called_once()
        # Should cache the result
        mock_cache.put.assert_called_once()
        call_args = mock_cache.put.call_args
        assert call_args[0][0] == "graphql_scoreboard:season:2025_week:12"
        assert call_args[1]["ttl_seconds"] == 3600
        assert "graphql" in call_args[1]["tags"]

    def test_graphql_recruiting_caching(self, agent_with_graphql, mock_graphql_client, mock_cache):
        """Test GraphQL recruiting caching"""
        cached_recruits = [{"name": "Cached Recruit", "stars": 5}]
        mock_cache.get.return_value = {"recruits": cached_recruits}

        result = agent_with_graphql._execute_action(
            "graphql_recruiting",
            {"year": 2026, "school": "Ohio State"},
            {}
        )

        assert result["cached"] is True
        assert result["data_source"] == "GraphQL API (cached)"
        assert result["recruits"] == cached_recruits
        mock_graphql_client.get_recruits.assert_not_called()

    def test_graphql_recruiting_cache_ttl(self, agent_with_graphql, mock_graphql_client, mock_cache):
        """Test GraphQL recruiting cache TTL is 24 hours"""
        mock_cache.get.return_value = None

        agent_with_graphql._execute_action(
            "graphql_recruiting",
            {"year": 2026, "school": "Ohio State"},
            {}
        )

        # Verify cache put was called with 24 hour TTL
        mock_cache.put.assert_called_once()
        call_args = mock_cache.put.call_args
        assert call_args[1]["ttl_seconds"] == 86400  # 24 hours

    def test_graphql_unavailable_graceful_degradation(self):
        """Test graceful degradation when GraphQL unavailable"""
        with patch('agents.cfbd_integration_agent.GRAPHQL_AVAILABLE', False):
            agent = CFBDIntegrationAgent("test_003")
            capabilities = agent._define_capabilities()
            capability_names = [cap.name for cap in capabilities]

            assert "graphql_scoreboard" not in capability_names
            assert "graphql_recruiting" not in capability_names

            # Should return error response, not raise exception
            result = agent._execute_action(
                "graphql_scoreboard",
                {"season": 2025, "week": 12},
                {}
            )
            assert result["status"] == "error"
            assert "not available" in result["error"].lower()
            assert result["games"] == []

    def test_graphql_scoreboard_error_handling(self, agent_with_graphql, mock_graphql_client):
        """Test error handling for GraphQL API failures"""
        mock_graphql_client.get_scoreboard.side_effect = Exception("API Error: Connection timeout")

        result = agent_with_graphql._execute_action(
            "graphql_scoreboard",
            {"season": 2025, "week": 12},
            {}
        )

        assert result["status"] == "error"
        assert "error" in result
        assert "API Error" in result["error"]
        assert result["games"] == []

    def test_graphql_recruiting_error_handling(self, agent_with_graphql, mock_graphql_client):
        """Test error handling for GraphQL recruiting API failures"""
        mock_graphql_client.get_recruits.side_effect = Exception("API Error: Rate limit exceeded")

        result = agent_with_graphql._execute_action(
            "graphql_recruiting",
            {"year": 2026, "school": "Ohio State"},
            {}
        )

        assert result["status"] == "error"
        assert "error" in result
        assert "API Error" in result["error"]
        assert result["recruits"] == []

    def test_graphql_scoreboard_empty_result(self, agent_with_graphql, mock_graphql_client, mock_cache):
        """Test handling of empty GraphQL scoreboard result"""
        mock_graphql_client.get_scoreboard.return_value = {"game": []}

        result = agent_with_graphql._execute_action(
            "graphql_scoreboard",
            {"season": 2025, "week": 12},
            {}
        )

        assert result["status"] == "success"
        assert result["games"] == []
        # Should not cache empty results
        mock_cache.put.assert_not_called()

    def test_graphql_recruiting_empty_result(self, agent_with_graphql, mock_graphql_client, mock_cache):
        """Test handling of empty GraphQL recruiting result"""
        mock_graphql_client.get_recruits.return_value = {"recruit": []}

        result = agent_with_graphql._execute_action(
            "graphql_recruiting",
            {"year": 2026, "school": "Ohio State"},
            {}
        )

        assert result["status"] == "success"
        assert result["recruits"] == []
        # Should not cache empty results
        mock_cache.put.assert_not_called()

    def test_graphql_recruiting_default_limit(self, agent_with_graphql, mock_graphql_client):
        """Test GraphQL recruiting uses default limit of 25"""
        agent_with_graphql._execute_action(
            "graphql_recruiting",
            {"year": 2026, "school": "Ohio State"},
            {}
        )

        mock_graphql_client.get_recruits.assert_called_once_with(
            season=2026, team="Ohio State", limit=25
        )


class TestCFBDGraphQLPerformance:
    """Performance tests for GraphQL capabilities"""

    @pytest.fixture
    def mock_graphql_client_fast(self):
        """Mock GraphQL client with fast response"""
        mock_client = Mock()
        mock_client.get_scoreboard.return_value = {"game": [{"id": 1}]}
        mock_client.get_recruits.return_value = {"recruit": [{"name": "Test"}]}
        return mock_client

    @pytest.fixture
    def agent_perf(self, mock_graphql_client_fast):
        """Agent for performance testing"""
        with patch('agents.cfbd_integration_agent.CFBDGraphQLClient', return_value=mock_graphql_client_fast):
            with patch('agents.cfbd_integration_agent.GRAPHQL_AVAILABLE', True):
                agent = CFBDIntegrationAgent("perf_test", graphql_client=mock_graphql_client_fast)
                return agent

    def test_graphql_scoreboard_response_time(self, agent_perf):
        """Test GraphQL scoreboard meets execution time estimate"""
        start_time = time.time()

        result = agent_perf._execute_action(
            "graphql_scoreboard",
            {"season": 2025, "week": 12},
            {}
        )

        execution_time = time.time() - start_time

        assert result["status"] == "success"
        assert execution_time < 2.0, f"Execution time {execution_time:.3f}s exceeded 2s limit"

    def test_graphql_recruiting_response_time(self, agent_perf):
        """Test GraphQL recruiting meets execution time estimate"""
        start_time = time.time()

        result = agent_perf._execute_action(
            "graphql_recruiting",
            {"year": 2026, "school": "Ohio State", "limit": 25},
            {}
        )

        execution_time = time.time() - start_time

        assert result["status"] == "success"
        assert execution_time < 3.0, f"Execution time {execution_time:.3f}s exceeded 3s limit"

    def test_graphql_scoreboard_cache_performance(self, agent_perf):
        """Test cache hit improves performance"""
        # Setup cache
        mock_cache = Mock()
        cached_data = {"games": [{"id": 1, "cached": True}]}
        mock_cache.get.return_value = cached_data
        agent_perf.cache = mock_cache

        start_time = time.time()

        result = agent_perf._execute_action(
            "graphql_scoreboard",
            {"season": 2025, "week": 12},
            {}
        )

        execution_time = time.time() - start_time

        assert result["status"] == "success"
        assert result["cached"] is True
        # Cached response should be very fast (< 0.1s)
        assert execution_time < 0.1, f"Cached response took {execution_time:.3f}s, expected < 0.1s"
