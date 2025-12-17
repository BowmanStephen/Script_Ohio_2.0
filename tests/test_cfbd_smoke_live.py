"""
Live HTTP smoke test for CFBD integration.

This test makes real API calls to verify:
- Authentication works
- Base URLs are correct
- Response formats match expectations
- GraphQL schema is accessible (if tier 3+)

SKIPPED unless CFBD_API_KEY is set.
"""
import os
import pytest
from typing import Dict, Any, List

from src.cfbd_client.unified_client import UnifiedCFBDClient
from src.config.cfbd_config import CFBDConfig


@pytest.mark.integration
@pytest.mark.skipif(
    not (os.getenv("CFBD_API_KEY") and os.getenv("CFBD_LIVE_TESTS") == "1"),
    reason="Requires CFBD_API_KEY and CFBD_LIVE_TESTS=1"
)
class TestCFBDSmokeLive:
    """Live HTTP smoke tests for CFBD API
    
    Behavior:
    - Skips if CFBD_API_KEY not set (local/dev ergonomics)
    - If CFBD_LIVE_STRICT_AUTH=1: Fails on 401 (CI/production safety)
    - Otherwise: Skips on 401 (local/dev ergonomics)
    """
    
    @pytest.fixture
    def client(self):
        """Create client with live API key"""
        try:
            config = CFBDConfig.from_env()
            return UnifiedCFBDClient(config)
        except ValueError as e:
            pytest.skip(f"CFBD_API_KEY not available: {e}")
    
    def test_get_conferences_live(self, client):
        """Test that conferences endpoint returns valid data"""
        from src.cfbd_client.errors import CFBDAuthenticationError
        
        strict_auth = os.getenv("CFBD_LIVE_STRICT_AUTH", "0") == "1"
        
        try:
            conferences = client.get_conferences()
        except CFBDAuthenticationError as e:
            if strict_auth:
                # In CI/strict mode: fail loudly on invalid key
                pytest.fail(f"CFBD API key invalid or expired (strict mode): {e}")
            else:
                # In local/dev: skip gracefully
                pytest.skip(f"CFBD API key invalid or expired: {e}. Update CFBD_API_KEY to run this test.")
        
        # Basic shape checks
        assert isinstance(conferences, list)
        assert len(conferences) > 0
        
        # Check structure of first conference
        conf = conferences[0]
        assert isinstance(conf, dict)
        # Conferences should have name or abbreviation
        assert "name" in conf or "abbreviation" in conf or "short_name" in conf
    
    def test_get_games_live(self, client):
        """Test that games endpoint returns valid data for recent season"""
        from src.cfbd_client.errors import CFBDAuthenticationError
        
        strict_auth = os.getenv("CFBD_LIVE_STRICT_AUTH", "0") == "1"
        
        try:
            # Use 2024 season (recent, should have data)
            games = client.get_games(year=2024, week=1)
        except CFBDAuthenticationError as e:
            if strict_auth:
                pytest.fail(f"CFBD API key invalid or expired (strict mode): {e}")
            else:
                pytest.skip(f"CFBD API key invalid or expired: {e}. Update CFBD_API_KEY to run this test.")
        
        # Basic shape checks
        assert isinstance(games, list)
        # Week 1 should have games
        assert len(games) > 0
        
        # Check structure of first game
        game = games[0]
        assert isinstance(game, dict)
        # Games should have teams and season info
        assert "season" in game or "year" in game
        assert "week" in game
    
    def test_host_config_live(self):
        """Test that host configuration actually affects API calls"""
        from src.cfbd_client.errors import CFBDAuthenticationError
        
        api_key = os.getenv("CFBD_API_KEY")
        if not api_key:
            pytest.skip("CFBD_API_KEY not set")
        
        strict_auth = os.getenv("CFBD_LIVE_STRICT_AUTH", "0") == "1"
        
        # Test production host
        config_prod = CFBDConfig(
            api_key=api_key,
            host="https://api.collegefootballdata.com"
        )
        client_prod = UnifiedCFBDClient(config_prod)
        
        try:
            # Should work with production host
            conferences_prod = client_prod.get_conferences()
        except CFBDAuthenticationError as e:
            if strict_auth:
                pytest.fail(f"CFBD API key invalid or expired (strict mode): {e}")
            else:
                pytest.skip(f"CFBD API key invalid or expired: {e}. Update CFBD_API_KEY to run this test.")
        
        assert len(conferences_prod) > 0
        
        # Test Next API host (if different)
        config_next = CFBDConfig(
            api_key=api_key,
            host="https://apinext.collegefootballdata.com"
        )
        client_next = UnifiedCFBDClient(config_next)
        
        try:
            # Should also work with Next host
            conferences_next = client_next.get_conferences()
        except CFBDAuthenticationError as e:
            if strict_auth:
                pytest.fail(f"CFBD API key invalid or expired (strict mode): {e}")
            else:
                pytest.skip(f"CFBD API key invalid or expired: {e}. Update CFBD_API_KEY to run this test.")
        
        assert len(conferences_next) > 0
        
        # Both should return similar data (same API, different host)
        assert len(conferences_prod) == len(conferences_next)
    
    def test_error_handling_live(self, client):
        """Test that 404 errors are raised (not silently ignored)"""
        from src.cfbd_client.errors import CFBDAuthenticationError, CFBDNotFoundError
        
        strict_auth = os.getenv("CFBD_LIVE_STRICT_AUTH", "0") == "1"
        
        try:
            # Request a game that doesn't exist (future season/week)
            # This should raise CFBDNotFoundError, not return empty
            games = client.get_games(year=2099, week=1)
        except CFBDAuthenticationError as e:
            if strict_auth:
                pytest.fail(f"CFBD API key invalid or expired (strict mode): {e}")
            else:
                pytest.skip(f"CFBD API key invalid or expired: {e}. Update CFBD_API_KEY to run this test.")
        except CFBDNotFoundError:
            # Expected: 404 should raise, not return empty
            pass
        else:
            # If we get here, 404 didn't raise - that's a bug
            pytest.fail("Expected CFBDNotFoundError for non-existent resource, but got result or no exception")
    
    @pytest.mark.skipif(
        not os.getenv("CFBD_GRAPHQL_TIER3"),
        reason="GraphQL requires Patreon Tier 3+ - set CFBD_GRAPHQL_TIER3=1 to test"
    )
    def test_graphql_scoreboard_live(self):
        """Test GraphQL scoreboard endpoint (requires Tier 3+)"""
        from agents.cfbd_integration_agent import CFBDIntegrationAgent
        
        agent = CFBDIntegrationAgent("test_smoke")
        result = agent._execute_action(
            "graphql_scoreboard",
            {"season": 2024, "week": 1},
            {}
        )
        
        assert result["status"] == "success"
        assert "games" in result
        assert isinstance(result["games"], list)
