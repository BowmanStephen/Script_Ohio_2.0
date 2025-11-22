"""
Test suite for UnifiedCFBDClient.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.cfbd_client.unified_client import UnifiedCFBDClient
from src.config.cfbd_config import CFBDConfig

class TestUnifiedCFBDClient:
    """Test cases for UnifiedCFBDClient"""
    
    @pytest.fixture
    def config(self):
        return CFBDConfig(
            api_key="test_key",
            host="https://api.collegefootballdata.com",
            max_requests_per_second=6,
            rate_limit_delay=0.17,
            max_retries=3,
        )
    
    @pytest.fixture
    def client(self, config):
        with patch('src.cfbd_client.unified_client.cfbd.ApiClient'):
            client = UnifiedCFBDClient(config)
            # Mock cache manager to avoid filesystem/memory state issues
            client.cache_manager = Mock()
            client.cache_manager.get_cached_data.return_value = None
            return client
    
    def test_initialization(self, client):
        """Test client initialization"""
        assert client.config.api_key == "test_key"
        assert client.config.host == "https://api.collegefootballdata.com"
        assert client.config.max_requests_per_second == 6
        assert client.config.rate_limit_delay == 0.17
        assert client.config.max_retries == 3
    
    def test_get_games(self, client):
        """Test get_games method"""
        # Mock games API
        client.games_api = Mock()
        mock_game = Mock()
        mock_game.to_dict.return_value = {'id': 1, 'home_team': 'Ohio State'}
        client.games_api.get_games.return_value = [mock_game]
        
        # Call method
        games = client.get_games(year=2025, week=12)
        
        # Verify API was called
        client.games_api.get_games.assert_called_once_with(
            year=2025, week=12, season_type="regular", team=None
        )
        
        # Verify response
        assert len(games) == 1
        assert games[0]['home_team'] == 'Ohio State'
    
    def test_rate_limiting(self, client):
        """Test rate limiting functionality"""
        # Mock sleep
        with patch('time.sleep') as mock_sleep:
            # Simulate rapid requests
            for _ in range(7):
                client._rate_limit()
            
            # Should have slept at least once (after 6 requests)
            assert mock_sleep.call_count >= 1

    def test_caching(self, client):
        """Test caching functionality"""
        # Mock cache hit
        client.cache_manager.get_cached_data.return_value = [{'id': 1}]
        client.games_api = Mock()
        
        games = client.get_games(year=2025)
        
        # API should NOT be called
        client.games_api.get_games.assert_not_called()
        assert games == [{'id': 1}]
        assert client.metrics.cache_hits == 1

    def test_error_handling(self, client):
        """Test error handling"""
        from cfbd.rest import ApiException
        
        client.games_api = Mock()
        client.games_api.get_games.side_effect = ApiException(status=500, reason="Server Error")
        
        # Should retry and then raise
        with patch('time.sleep'): # speed up test
            with pytest.raises(ApiException):
                client.get_games(year=2025)
        
        assert client.metrics.errors >= 3

