"""
Unified CFBD API client consolidating best practices from all existing implementations.
This replaces: src/cfbd_client/client.py, src/data_sources/cfbd_client.py, 
starter_pack/utils/cfbd_loader.py, and agents/core/enhanced_cfbd_integration.py
"""

import os
import time
import json
import logging
import hashlib
import pickle
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Callable

import cfbd
from cfbd.rest import ApiException

from .cfbd_cache_manager import CFBDCacheManager, CFBDCacheConfig
try:
    from ..config.cfbd_config import CFBDConfig
except ImportError:
    # Fallback if config module not available
    from src.config.cfbd_config import CFBDConfig

logger = logging.getLogger(__name__)

@dataclass
class CFBDClientMetrics:
    """Metrics for monitoring CFBD API usage"""
    total_requests: int = 0
    successful_requests: int = 0
    rate_limit_hits: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    errors: int = 0
    total_latency_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        avg_latency = (
            self.total_latency_ms / self.successful_requests
            if self.successful_requests > 0 else 0.0
        )
        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "rate_limit_hits": self.rate_limit_hits,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "errors": self.errors,
            "average_latency_ms": round(avg_latency, 2),
        }

class UnifiedCFBDClient:
    """
    Unified CFBD API client with production-grade features.
    
    Features:
    - Consistent rate limiting (6 req/sec)
    - Intelligent caching with TTL by data type
    - Comprehensive error handling with exponential backoff
    - Performance metrics and monitoring
    - Support for both production and Next API
    - REST-only (GraphQL removed)
    """
    
    def __init__(self, config: Optional[CFBDConfig] = None):
        """Initialize client with configuration"""
        self.config = config or CFBDConfig.from_env()
        
        # Initialize metrics
        self.metrics = CFBDClientMetrics()
        
        # Rate limiting state
        self.request_history = []
        self.last_request_time = 0
        
        # Initialize CFBD client
        self._init_cfbd_client()
        
        # Initialize cache manager
        self.cache_manager = CFBDCacheManager(self.config.cache_config)
        
        logger.info(f"✅ Unified CFBD Client initialized: {self.config.host}")
    
    def _init_cfbd_client(self):
        """Initialize CFBD API client with proper authentication"""
        try:
            # Configure CFBD client
            configuration = cfbd.Configuration()
            configuration.access_token = self.config.api_key
            configuration.host = self.config.host
            
            # Create API client
            self.api_client = cfbd.ApiClient(configuration)
            
            # Initialize API endpoints
            self.games_api = cfbd.GamesApi(self.api_client)
            self.stats_api = cfbd.StatsApi(self.api_client)
            self.teams_api = cfbd.TeamsApi(self.api_client)
            self.ratings_api = cfbd.RatingsApi(self.api_client)
            self.betting_api = cfbd.BettingApi(self.api_client)
            self.plays_api = cfbd.PlaysApi(self.api_client)
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize CFBD client: {e}")
            raise
    
    def _rate_limit(self):
        """Implement rate limiting with burst protection"""
        current_time = time.time()
        
        # Remove requests older than 1 second
        self.request_history = [t for t in self.request_history if current_time - t < 1.0]
        
        # If we've hit the limit, calculate precise delay
        if len(self.request_history) >= self.config.max_requests_per_second:
            sleep_time = 1.0 - (current_time - self.request_history[0])
            if sleep_time > 0:
                time.sleep(sleep_time)
                self.metrics.rate_limit_hits += 1
                current_time = time.time()
        
        # Record this request
        self.request_history.append(current_time)
        
        # Simple fallback for first request
        if len(self.request_history) == 1:
            time_since_last = current_time - self.last_request_time
            if time_since_last < self.config.rate_limit_delay:
                time.sleep(self.config.rate_limit_delay - time_since_last)
        
        self.last_request_time = time.time()
    
    def _safe_api_call(self, api_function, *args, **kwargs):
        """
        Make API call with comprehensive error handling and retry logic.
        
        Args:
            api_function: CFBD API method to call
            *args, **kwargs: Arguments to pass to the API function
            
        Returns:
            API response or None if all retries fail
        """
        start_time = time.time()
        
        # Implement rate limiting
        self._rate_limit()
        
        # Retry logic with exponential backoff
        for attempt in range(self.config.max_retries):
            try:
                # Make API call
                result = api_function(*args, **kwargs)
                
                # Track success
                self.metrics.successful_requests += 1
                self.metrics.total_requests += 1
                latency_ms = (time.time() - start_time) * 1000
                self.metrics.total_latency_ms += latency_ms
                
                return result
                
            except ApiException as e:
                # Handle specific API errors
                self.metrics.errors += 1
                self.metrics.total_requests += 1
                
                if e.status == 429:  # Rate limit exceeded
                    wait_time = 2 ** attempt + 1  # Exponential backoff
                    logger.warning(f"⏱️ Rate limit hit, waiting {wait_time}s (attempt {attempt + 1})")
                    time.sleep(wait_time)
                    continue
                    
                elif e.status == 401:  # Authentication error
                    logger.error("🔐 Authentication failed - check API key")
                    raise ValueError("Invalid CFBD API key")
                    
                elif e.status == 404:  # Not found
                    logger.warning(f"🔍 Resource not found: {str(e)}")
                    return None
                    
                elif e.status >= 500:  # Server error
                    if attempt < self.config.max_retries - 1:
                        wait_time = 2 ** attempt + 1
                        logger.warning(f"🔄 Server error, retrying in {wait_time}s (attempt {attempt + 1})")
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"❌ Server error after {attempt + 1} attempts: {str(e)}")
                        raise
                        
                else:
                    logger.error(f"❌ API error: {str(e)}")
                    raise
                    
            except Exception as e:
                self.metrics.errors += 1
                self.metrics.total_requests += 1
                logger.error(f"❌ Unexpected error: {str(e)}")
                raise
        
        return None
    
    def _get_cache_key(self, endpoint: str, params: Dict[str, Any]) -> str:
        """Generate cache key for API call"""
        key_data = f"{endpoint}_{json.dumps(params, sort_keys=True, default=str)}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _cached_fetch(self, endpoint: str, params: Dict[str, Any], 
                     api_function, cache_type: str = 'stats') -> Any:
        """
        Fetch data with caching support.
        
        Args:
            endpoint: API endpoint name
            params: Parameters for the API call
            api_function: Function to call if cache miss
            cache_type: Type of cache (games, stats, teams, etc.)
            
        Returns:
            API response data
        """
        # Check cache first
        # Note: I updated CFBDCacheManager to accept endpoint, params, cache_type
        # The plan code used self.cache_manager.get_cached_data(endpoint, params, cache_type)
        # which matches my update to the manager.
        
        cached_data = self.cache_manager.get_cached_data(endpoint, params, cache_type)
        
        if cached_data:
            self.metrics.cache_hits += 1
            logger.debug(f"🎯 Cache hit: {endpoint}")
            return cached_data
        
        # Cache miss - fetch from API
        self.metrics.cache_misses += 1
        logger.debug(f"🌐 API fetch: {endpoint}")
        
        data = self._safe_api_call(api_function)
        
        # Cache the result
        if data:
            self.cache_manager.cache_data(endpoint, params, data, cache_type)
        
        return data
    
    # API Methods
    def _to_dict_list(self, data: Any) -> List[Dict]:
        """Convert API response objects to list of dicts"""
        if not data:
            return []
        if isinstance(data, list):
            return [item.to_dict() if hasattr(item, "to_dict") else item for item in data]
        return [data.to_dict() if hasattr(data, "to_dict") else data]

    def get_games(self, year: int, week: Optional[int] = None, 
                 season_type: str = "regular", team: Optional[str] = None) -> List[Dict]:
        """Get games data with caching"""
        params = {
            "year": year,
            "week": week,
            "seasonType": season_type,
            "team": team,
        }
        return self._cached_fetch(
            "games",
            params,
            lambda: self._to_dict_list(self.games_api.get_games(
                year=year,
                week=week,
                season_type=season_type,
                team=team,
            )),
            "games"
        )
    
    def get_ratings(self, year: int, week: Optional[int] = None) -> List[Dict]:
        """Get ratings data with caching"""
        params = {"year": year, "week": week}
        return self._cached_fetch(
            "ratings",
            params,
            lambda: self._to_dict_list(self.ratings_api.get_elo(year=year, week=week)),
            "ratings"
        )
    
    def get_lines(self, year: int, week: int) -> List[Dict]:
        """Get betting lines with caching"""
        params = {"year": year, "week": week}
        return self._cached_fetch(
            "lines",
            params,
            lambda: self._to_dict_list(self.betting_api.get_lines(year=year, week=week)),
            "lines"
        )
    
    def get_team_talent(self, year: int) -> List[Dict]:
        """Get team talent ratings with caching"""
        params = {"year": year}
        return self._cached_fetch(
            "team_talent",
            params,
            lambda: self._to_dict_list(self.teams_api.get_team_talent(year=year)),
            "teams"
        )
    
    def get_stats(self, year: int, team: Optional[str] = None, 
                category: Optional[str] = None) -> List[Dict]:
        """Get team statistics with caching"""
        params = {"year": year, "team": team, "category": category}
        return self._cached_fetch(
            "stats",
            params,
            lambda: self._to_dict_list(self.stats_api.get_team_season_stats(
                year=year, team=team, category=category
            )),
            "stats"
        )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        cache_stats = self.cache_manager.get_cache_stats()
        return {
            "client_metrics": self.metrics.to_dict(),
            "cache_stats": cache_stats,
            "config": {
                "host": self.config.host,
                "max_requests_per_second": self.config.max_requests_per_second,
                "rate_limit_delay": self.config.rate_limit_delay,
                "cache_enabled": self.config.cache_config.enable_cache,
            }
        }

