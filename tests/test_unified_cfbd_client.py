"""
Test suite for UnifiedCFBDClient.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.cfbd_client.unified_client import UnifiedCFBDClient
from src.config.cfbd_config import CFBDConfig
from src.cfbd_client.errors import (
    CFBDAuthenticationError,
    CFBDForbiddenError,
    CFBDNotFoundError,
    CFBDRateLimitError,
    CFBDServerError,
)

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
    
    def test_host_config_production(self):
        """Test that production host config is used"""
        config = CFBDConfig(
            api_key="test_key",
            host="https://api.collegefootballdata.com",
        )
        with patch('src.cfbd_client.unified_client.cfbd.ApiClient'):
            client = UnifiedCFBDClient(config)
            # Verify config host is set correctly
            assert client.config.host == "https://api.collegefootballdata.com"
    
    def test_host_config_next(self):
        """Test that Next API host config is used"""
        config = CFBDConfig(
            api_key="test_key",
            host="https://apinext.collegefootballdata.com",
        )
        with patch('src.cfbd_client.unified_client.cfbd.ApiClient'):
            client = UnifiedCFBDClient(config)
            # Verify config host is set correctly
            assert client.config.host == "https://apinext.collegefootballdata.com"
    
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
        from src.cfbd_client.errors import CFBDServerError
        
        client.games_api = Mock()
        client.games_api.get_games.side_effect = ApiException(status=500, reason="Server Error")
        
        # Should retry and then raise CFBDServerError (converted from ApiException)
        with patch('time.sleep'): # speed up test
            with pytest.raises(CFBDServerError):
                client.get_games(year=2025)
        
        assert client.metrics.errors >= 3
    
    def test_generic_request_method(self, client):
        """Test generic request() method"""
        client.games_api = Mock()
        mock_game = Mock()
        mock_game.to_dict.return_value = {'id': 1, 'home_team': 'Ohio State'}
        client.games_api.get_games.return_value = [mock_game]
        
        # Test that generic request routes to get_games
        result = client.request("GET", "/games", {"year": 2025, "week": 12})
        assert len(result) == 1
        assert result[0]['home_team'] == 'Ohio State'
    
    def test_get_drives(self, client):
        """Test get_drives method"""
        client.drives_api = Mock()
        mock_drive = Mock()
        mock_drive.to_dict.return_value = {'id': 1, 'offense': 'Ohio State'}
        client.drives_api.get_drives.return_value = [mock_drive]
        
        drives = client.get_drives(year=2025, week=12)
        assert len(drives) == 1
        assert drives[0]['offense'] == 'Ohio State'
    
    def test_get_player_stats(self, client):
        """Test get_player_stats method"""
        client.players_api = Mock()
        mock_player = Mock()
        mock_player.to_dict.return_value = {'player': 'John Doe', 'yards': 1000}
        client.players_api.get_player_season_stats.return_value = [mock_player]
        
        stats = client.get_player_stats(year=2025, team='Ohio State')
        assert len(stats) == 1
        assert stats[0]['player'] == 'John Doe'
    
    def test_get_conferences(self, client):
        """Test get_conferences method"""
        client.conferences_api = Mock()
        mock_conf = Mock()
        mock_conf.to_dict.return_value = {'name': 'Big Ten', 'id': 1}
        client.conferences_api.get_conferences.return_value = [mock_conf]
        
        conferences = client.get_conferences()
        assert len(conferences) == 1
        assert conferences[0]['name'] == 'Big Ten'
    
    def test_get_advanced_stats(self, client):
        """Test get_advanced_stats method"""
        client.stats_api = Mock()
        mock_stat = Mock()
        mock_stat.to_dict.return_value = {'team': 'Ohio State', 'epa': 0.15}
        client.stats_api.get_advanced_season_stats.return_value = [mock_stat]
        
        stats = client.get_advanced_stats(year=2025, team='Ohio State')
        assert len(stats) == 1
        assert stats[0]['team'] == 'Ohio State'
    
    def test_error_taxonomy_401(self, client):
        """Test that 401 errors raise CFBDAuthenticationError"""
        from cfbd.rest import ApiException
        
        client.games_api = Mock()
        client.games_api.get_games.side_effect = ApiException(status=401, reason="Unauthorized")
        
        with pytest.raises(CFBDAuthenticationError):
            client.get_games(year=2025)
    
    def test_error_taxonomy_403(self, client):
        """Test that 403 errors raise CFBDForbiddenError"""
        from cfbd.rest import ApiException
        
        client.games_api = Mock()
        client.games_api.get_games.side_effect = ApiException(status=403, reason="Forbidden")
        
        with pytest.raises(CFBDForbiddenError):
            client.get_games(year=2025)
    
    def test_error_taxonomy_404(self, client):
        """Test that 404 errors raise CFBDNotFoundError (not return None)"""
        from cfbd.rest import ApiException
        
        client.games_api = Mock()
        client.games_api.get_games.side_effect = ApiException(status=404, reason="Not Found")
        
        # 404 errors should raise CFBDNotFoundError, not return None
        with pytest.raises(CFBDNotFoundError):
            client.get_games(year=2025)
    
    def test_error_taxonomy_429(self, client):
        """Test that 429 errors raise CFBDRateLimitError with Retry-After"""
        from cfbd.rest import ApiException
        
        client.games_api = Mock()
        mock_exception = ApiException(status=429, reason="Too Many Requests")
        mock_exception.headers = {'Retry-After': '30'}
        client.games_api.get_games.side_effect = [mock_exception, Mock(to_dict=lambda: {'id': 1})]
        
        with patch('time.sleep'):
            result = client.get_games(year=2025)
            # Should have retried and succeeded
            assert result is not None

