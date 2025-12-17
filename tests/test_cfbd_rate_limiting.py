"""
Test suite for CFBD rate limiting and retry logic.
"""
import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from cfbd.rest import ApiException

from src.cfbd_client.unified_client import UnifiedCFBDClient
from src.config.cfbd_config import CFBDConfig


class TestCFBDRateLimiting:
    """Test rate limiting and retry logic"""
    
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
            client.cache_manager = Mock()
            client.cache_manager.get_cached_data.return_value = None
            return client
    
    def test_retry_after_header_parsing(self, client):
        """Test that Retry-After header is parsed and used"""
        # Create mock exception with Retry-After header
        mock_exception = ApiException(status=429, reason="Rate limit exceeded")
        mock_exception.headers = {'Retry-After': '30'}
        
        wait_time = client._parse_retry_after(mock_exception, 0)
        assert wait_time == 30.0
    
    def test_retry_after_header_capped(self, client):
        """Test that Retry-After header is capped at 300 seconds"""
        mock_exception = ApiException(status=429, reason="Rate limit exceeded")
        mock_exception.headers = {'Retry-After': '600'}  # 10 minutes
        
        wait_time = client._parse_retry_after(mock_exception, 0)
        assert wait_time == 300.0  # Capped at 5 minutes
    
    def test_retry_after_fallback_to_exponential(self, client):
        """Test that exponential backoff is used when Retry-After is missing"""
        mock_exception = ApiException(status=429, reason="Rate limit exceeded")
        mock_exception.headers = {}  # No Retry-After header
        
        wait_time = client._parse_retry_after(mock_exception, 0)
        assert wait_time == 2.0  # 2^0 + 1 = 2
        
        wait_time = client._parse_retry_after(mock_exception, 1)
        assert wait_time == 3.0  # 2^1 + 1 = 3
        
        wait_time = client._parse_retry_after(mock_exception, 2)
        assert wait_time == 5.0  # 2^2 + 1 = 5
    
    def test_retry_after_exponential_capped(self, client):
        """Test that exponential backoff is capped at 60 seconds"""
        mock_exception = ApiException(status=429, reason="Rate limit exceeded")
        mock_exception.headers = {}
        
        # High attempt number should be capped
        wait_time = client._parse_retry_after(mock_exception, 10)
        assert wait_time == 60.0  # Capped at 60 seconds
    
    def test_429_respects_retry_after(self, client):
        """Test that 429 errors respect Retry-After header"""
        client.games_api = Mock()
        mock_exception = ApiException(status=429, reason="Rate limit exceeded")
        mock_exception.headers = {'Retry-After': '15'}
        client.games_api.get_games.side_effect = [mock_exception, Mock(to_dict=lambda: {'id': 1})]
        
        with patch('time.sleep') as mock_sleep:
            result = client.get_games(year=2025, week=12)
            # Should have slept for ~15 seconds (from Retry-After, plus jitter)
            mock_sleep.assert_called()
            # Check that sleep was called with value close to 15 (accounting for jitter 0-20%)
            sleep_calls = [call[0][0] for call in mock_sleep.call_args_list]
            # Jitter adds 0-20% (0-3s), so range is 15-18 seconds
            assert any(15.0 <= s <= 18.0 for s in sleep_calls), f"Expected sleep time 15-18s, got {sleep_calls}"
    
    def test_5xx_bounded_exponential_backoff(self, client):
        """Test that 5xx errors use bounded exponential backoff"""
        client.games_api = Mock()
        mock_exception = ApiException(status=500, reason="Server Error")
        client.games_api.get_games.side_effect = [mock_exception, mock_exception, Mock(to_dict=lambda: {'id': 1})]
        
        with patch('time.sleep') as mock_sleep:
            result = client.get_games(year=2025, week=12)
            # Should have retried with exponential backoff
            assert mock_sleep.call_count >= 2
            # Check that backoff is bounded (capped at 60)
            sleep_calls = [call[0][0] for call in mock_sleep.call_args_list]
            assert all(s <= 60 for s in sleep_calls)
    
    def test_rate_limit_metrics_tracking(self, client):
        """Test that 429 errors increment rate_limit_hits metric"""
        client.games_api = Mock()
        mock_exception = ApiException(status=429, reason="Rate limit exceeded")
        mock_exception.headers = {'Retry-After': '1'}
        client.games_api.get_games.side_effect = [mock_exception, Mock(to_dict=lambda: {'id': 1})]
        
        initial_hits = client.metrics.rate_limit_hits
        with patch('time.sleep'):
            client.get_games(year=2025, week=12)
        assert client.metrics.rate_limit_hits > initial_hits
    
    def test_rate_limit_configurable(self):
        """Test that rate limit is configurable via environment"""
        config = CFBDConfig(
            api_key="test_key",
            max_requests_per_second=10,  # Custom rate limit
            rate_limit_delay=0.1,  # 1/10 = 0.1s
        )
        assert config.max_requests_per_second == 10
        assert config.rate_limit_delay == 0.1  # 1/10 = 0.1s
        
        # Test that from_env calculates rate_limit_delay correctly
        import os
        os.environ['CFBD_MAX_REQUESTS_PER_SECOND'] = '10'
        env_config = CFBDConfig.from_env()
        assert env_config.max_requests_per_second == 10
        assert env_config.rate_limit_delay == 0.1  # Should be calculated as 1/10
