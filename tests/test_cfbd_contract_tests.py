"""
Contract tests for CFBD integration to prevent regressions.

These tests ensure:
1. No API keys are exposed in responses
2. GraphQL fallback behavior is correct
3. Security requirements are maintained
"""

import json
from unittest.mock import MagicMock, Mock, patch

import pytest
from agents.cfbd_integration_agent import CFBDIntegrationAgent
from src.cfbd_client.unified_client import UnifiedCFBDClient
from src.config.cfbd_config import CFBDConfig


class TestCFBDSecurityContracts:
    """Contract tests to ensure security requirements are met"""

    @pytest.fixture
    def config(self):
        return CFBDConfig(
            api_key="test_key_12345",
            host="https://api.collegefootballdata.com",
        )

    @pytest.fixture
    def client(self, config):
        with patch("src.cfbd_client.unified_client.cfbd.ApiClient"):
            client = UnifiedCFBDClient(config)
            client.cache_manager = Mock()
            client.cache_manager.get_cached_data.return_value = None
            return client

    def test_no_api_key_in_response(self, client):
        """Contract: No endpoint response should contain CFBD_API_KEY or Authorization header"""
        client.games_api = Mock()
        mock_game = Mock()
        mock_game.to_dict.return_value = {"id": 1, "home_team": "Ohio State"}
        client.games_api.get_games.return_value = [mock_game]

        games = client.get_games(year=2025, week=12)

        # Serialize response to JSON string and check for API key
        response_json = json.dumps(games)

        # Should not contain API key
        assert "test_key_12345" not in response_json
        assert "CFBD_API_KEY" not in response_json
        assert "Authorization" not in response_json
        assert "Bearer" not in response_json.lower()

    def test_no_api_key_in_error_messages(self, client):
        """Contract: Error messages should not expose API keys"""
        from cfbd.rest import ApiException

        client.games_api = Mock()
        client.games_api.get_games.side_effect = ApiException(
            status=500, reason="Server Error"
        )

        with patch("time.sleep"):  # Speed up test
            try:
                client.get_games(year=2025)
                pytest.fail("Should have raised an exception")
            except Exception as e:
                error_str = str(e)
                # Error should not contain API key
                assert "test_key_12345" not in error_str
                assert "CFBD_API_KEY" not in error_str


class TestGraphQLFallbackContracts:
    """Contract tests for GraphQL fallback behavior"""

    @pytest.fixture
    def agent_with_fallback_enabled(self):
        """Agent with GraphQL fallback enabled (default)"""
        config = CFBDConfig(
            api_key="test_key",
            graphql_fallback_to_rest=True,
        )
        with patch("src.cfbd_client.unified_client.cfbd.ApiClient"):
            client = UnifiedCFBDClient(config)
            client.cache_manager = Mock()
            client.cache_manager.get_cached_data.return_value = None

            # Mock GraphQL client that raises 403
            mock_graphql_client = Mock()
            mock_graphql_error = Exception(
                "Authentication hook unauthorized this request (403)"
            )
            mock_graphql_client.get_scoreboard.side_effect = mock_graphql_error

            agent = CFBDIntegrationAgent(
                agent_id="test",
                cfbd_client=client,
                graphql_client=mock_graphql_client,
            )
            return agent

    @pytest.fixture
    def agent_with_fallback_disabled(self):
        """Agent with GraphQL fallback disabled"""
        config = CFBDConfig(
            api_key="test_key",
            graphql_fallback_to_rest=False,
        )
        with patch("src.cfbd_client.unified_client.cfbd.ApiClient"):
            client = UnifiedCFBDClient(config)
            client.cache_manager = Mock()
            client.cache_manager.get_cached_data.return_value = None

            # Mock GraphQL client that raises 403
            mock_graphql_client = Mock()
            mock_graphql_error = Exception(
                "Authentication hook unauthorized this request (403)"
            )
            mock_graphql_client.get_scoreboard.side_effect = mock_graphql_error

            agent = CFBDIntegrationAgent(
                agent_id="test",
                cfbd_client=client,
                graphql_client=mock_graphql_client,
            )
            return agent

    def test_graphql_fallback_on_403_when_enabled(self, agent_with_fallback_enabled):
        """Contract: GraphQL should fallback to REST on 403 when fallback is enabled"""
        # Mock REST client to return games
        agent_with_fallback_enabled.client.games_api = Mock()
        mock_game = Mock()
        mock_game.to_dict.return_value = {"id": 1, "home_team": "Ohio State"}
        agent_with_fallback_enabled.client.games_api.get_games.return_value = [
            mock_game
        ]

        result = agent_with_fallback_enabled._execute_action(
            "graphql_scoreboard", {"season": 2025, "week": 12}, {"user_id": "test"}
        )

        # Should have fallen back to REST
        assert result["status"] == "success"
        assert result["data_source"] == "REST API (GraphQL fallback)"
        assert "fallback_reason" in result
        assert len(result["games"]) == 1

    def test_graphql_no_fallback_on_403_when_disabled(
        self, agent_with_fallback_disabled
    ):
        """Contract: GraphQL should NOT fallback when fallback is disabled"""
        result = agent_with_fallback_disabled._execute_action(
            "graphql_scoreboard", {"season": 2025, "week": 12}, {"user_id": "test"}
        )

        # Should fail with error, not fallback
        assert result["status"] == "error"
        assert "requires_tier" in result or "Patreon Tier 3+" in result["error"]
        assert "REST API" not in result.get("data_source", "")

    def test_graphql_fallback_respects_env_var(self):
        """Contract: GraphQL fallback should respect CFBD_GRAPHQL_FALLBACK_TO_REST env var"""
        import os

        # Test with env var set to false
        with patch.dict(
            os.environ, {"CFBD_GRAPHQL_FALLBACK_TO_REST": "false"}, clear=False
        ):
            config = CFBDConfig(
                api_key="test_key",
                graphql_fallback_to_rest=False,  # Explicitly set to False to match env var
            )

            with patch("src.cfbd_client.unified_client.cfbd.ApiClient"):
                client = UnifiedCFBDClient(config)
                client.cache_manager = Mock()
                client.games_api = Mock()  # Mock REST API

                mock_graphql_client = Mock()
                mock_graphql_error = Exception("Authentication hook unauthorized (403)")
                mock_graphql_client.get_scoreboard.side_effect = mock_graphql_error

                agent = CFBDIntegrationAgent(
                    agent_id="test",
                    cfbd_client=client,
                    graphql_client=mock_graphql_client,
                )

                result = agent._execute_action(
                    "graphql_scoreboard",
                    {"season": 2025, "week": 12},
                    {"user_id": "test"},
                )

                # Should fail (no fallback) because config says false
                assert result["status"] == "error"
                assert "requires_tier" in result or "Patreon Tier 3+" in result.get(
                    "error", ""
                )
