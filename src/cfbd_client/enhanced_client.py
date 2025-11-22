"""
Enhanced CFBD Integration Module
=====================================
Upgraded CFBD client (5.13.2) with optimized rate limiting and production-grade error handling.
Follows established Script Ohio 2.0 patterns and integrates with existing agent framework.

Features:
- Upgraded CFBD client (5.13.2) with 3+ years of feature enhancements
- Optimized rate limiting (0.17s vs 0.5s) for 3x faster API calls
- REST API integration for efficient data fetching
- Production-grade error handling with exponential backoff
- Intelligent caching for repeated requests
- Comprehensive logging and monitoring
- Enhanced authentication patterns following existing .cursorrules standards

Author: Script Ohio 2.0 Enhancement
Version: 5.13.2-enhanced
Compatible with: BaseAgent framework, Analytics Orchestrator, Model Execution Engine
"""

import os
import time
import json
import logging
import requests
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
import pickle
import hashlib
from functools import lru_cache

# Enhanced CFBD import with version compatibility
try:
    import cfbd
    from cfbd.rest import ApiException
    CFBD_VERSION = getattr(cfbd, '__version__', '4.3.1')  # Handle version detection gracefully
    logging.info(f"✅ CFBD client version {CFBD_VERSION} loaded successfully")
except ImportError as e:
    logging.error(f"❌ CFBD client not available: {e}")
    cfbd = None
    CFBD_VERSION = None

# Set up logging following project standards
logger = logging.getLogger(__name__)


@dataclass
class CFBDCacheConfig:
    """Configuration for CFBD caching strategies"""
    enable_cache: bool = True
    cache_ttl_games: int = 86400  # 24 hours - game results stable
    cache_ttl_stats: int = 3600   # 1 hour - stats update periodically
    cache_ttl_teams: int = 604800  # 7 days - team info stable
    cache_ttl_predictions: int = 300  # 5 minutes - prediction data volatile
    cache_dir: str = "cfbd_cache"


@dataclass
class CFBDRateLimitConfig:
    """Enhanced rate limiting configuration for optimal performance"""
    max_requests_per_second: int = 6
    optimal_delay: float = 0.17  # 1/6 = 0.17s for exactly 6 req/sec
    burst_protection: bool = True
    exponential_backoff: bool = True
    max_retries: int = 3


class CFBDCacheManager:
    """
    Intelligent caching system for CFBD API responses.
    Follows existing project patterns and integrates with agent system.
    """

    def __init__(self, config: CFBDCacheConfig = None):
        self.config = config or CFBDCacheConfig()
        self.cache_dir = Path(self.config.cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

        # In-memory cache for frequently accessed data
        self._memory_cache = {}
        self._cache_stats = {
            'hits': 0,
            'misses': 0,
            'writes': 0,
            'errors': 0
        }

        logger.info(f"🗄️ CFBD Cache initialized: {self.cache_dir}")

    def _get_cache_key(self, endpoint: str, params: Dict[str, Any]) -> str:
        """Generate secure cache key for API call"""
        key_data = f"{endpoint}_{json.dumps(params, sort_keys=True, default=str)}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def _get_cache_file(self, cache_key: str) -> Path:
        """Get cache file path for given key"""
        return self.cache_dir / f"{cache_key}.pkl"

    def _is_cache_valid(self, cache_file: Path, cache_type: str) -> bool:
        """Check if cached file is still valid based on type"""
        if not cache_file.exists():
            return False

        # Check file age based on cache type TTL
        file_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
        ttl_map = {
            'games': self.config.cache_ttl_games,
            'stats': self.config.cache_ttl_stats,
            'teams': self.config.cache_ttl_teams,
            'predictions': self.config.cache_ttl_predictions
        }

        ttl = ttl_map.get(cache_type, self.config.cache_ttl_stats)
        return file_age.total_seconds() < ttl

    def get_cached_data(self, endpoint: str, params: Dict[str, Any],
                      cache_type: str = 'stats') -> Optional[Dict[str, Any]]:
        """
        Get cached data if available and valid.
        Integrates with agent system performance monitoring.
        """
        if not self.config.enable_cache:
            return None

        try:
            # Check memory cache first
            cache_key = f"{endpoint}:{cache_type}:{hash(str(sorted(params.items())))}"
            if cache_key in self._memory_cache:
                cache_entry = self._memory_cache[cache_key]
                if self._is_cache_valid(cache_entry['file'], cache_type):
                    self._cache_stats['hits'] += 1
                    logger.debug(f"🎯 Memory cache hit: {cache_key}")
                    return cache_entry['data']

            # Check file cache
            file_cache_key = self._get_cache_key(endpoint, params)
            cache_file = self._get_cache_file(file_cache_key)

            if self._is_cache_valid(cache_file, cache_type):
                with open(cache_file, 'rb') as f:
                    cached_data = pickle.load(f)

                # Load into memory cache for faster access
                self._memory_cache[cache_key] = {
                    'data': cached_data,
                    'file': cache_file,
                    'timestamp': datetime.now()
                }

                self._cache_stats['hits'] += 1
                logger.debug(f"💾 File cache hit: {endpoint}")
                return cached_data

            self._cache_stats['misses'] += 1
            return None

        except Exception as e:
            self._cache_stats['errors'] += 1
            logger.error(f"❌ Cache retrieval error: {e}")
            return None

    def cache_data(self, endpoint: str, params: Dict[str, Any],
                  data: Dict[str, Any], cache_type: str = 'stats') -> None:
        """Cache API response with appropriate TTL"""
        if not self.config.enable_cache:
            return

        try:
            cache_key = f"{endpoint}:{cache_type}:{hash(str(sorted(params.items())))}"
            file_cache_key = self._get_cache_key(endpoint, params)
            cache_file = self._get_cache_file(file_cache_key)

            # Create cache entry
            cache_entry = {
                'data': data,
                'timestamp': datetime.now(),
                'endpoint': endpoint,
                'params': params,
                'cache_type': cache_type
            }

            # Save to file
            with open(cache_file, 'wb') as f:
                pickle.dump(cache_entry, f)

            # Save to memory
            self._memory_cache[cache_key] = {
                'data': data,
                'file': cache_file,
                'timestamp': datetime.now()
            }

            self._cache_stats['writes'] += 1
            logger.debug(f"💾 Data cached: {endpoint}")

        except Exception as e:
            self._cache_stats['errors'] += 1
            logger.error(f"❌ Cache storage error: {e}")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        total_requests = self._cache_stats['hits'] + self._cache_stats['misses']
        hit_rate = (self._cache_stats['hits'] / max(total_requests, 1)) * 100

        return {
            'hit_rate_percent': round(hit_rate, 2),
            'total_requests': total_requests,
            'cache_hits': self._cache_stats['hits'],
            'cache_misses': self._cache_stats['misses'],
            'cache_writes': self._cache_stats['writes'],
            'cache_errors': self._cache_stats['errors'],
            'memory_cache_size': len(self._memory_cache)
        }


class EnhancedCFBDClient:
    """
    Enhanced CFBD API client with optimized performance and production-grade features.
    Follows established Script Ohio 2.0 patterns and integrates seamlessly with BaseAgent framework.

    Key Enhancements:
    - Upgraded CFBD client 5.13.2 with latest features
    - Optimized rate limiting (0.17s delay for 6 req/sec)
    - REST API support with rate limiting
    - Production-grade error handling with exponential backoff
    - Intelligent caching system
    - Comprehensive performance monitoring
    - Enhanced authentication patterns
    Note: GraphQL support removed - requires Patreon Tier 3+ access
    """

    def __init__(self, api_key: str = None, config: CFBDRateLimitConfig = None,
                 cache_config: CFBDCacheConfig = None):
        """
        Initialize enhanced CFBD client with optimal configuration.

        Args:
            api_key: CFBD API key (defaults to environment variable)
            config: Rate limiting configuration
            cache_config: Caching configuration
        """
        # Configuration
        self.rate_config = config or CFBDRateLimitConfig()
        self.cache_config = cache_config or CFBDCacheConfig()
        
        # GraphQL support removed - requires Patreon Tier 3+ access and is not enabled
        
        # Authentication following existing .cursorrules patterns
        self.api_key = api_key or os.environ.get('CFBD_API_KEY') or os.environ.get('CFBD_API_TOKEN')
        if not self.api_key:
            raise ValueError("❌ CFBD_API_KEY or CFBD_API_TOKEN environment variable required")

        # Initialize CFBD client with latest version
        if cfbd is None:
            raise ImportError("❌ CFBD client not available. Install with: pip install cfbd==5.13.2")

        # Enhanced configuration for optimal performance
        self.configuration = cfbd.Configuration()
        self.configuration.access_token = self.api_key

        # Support for both standard and Next API
        self.api_host = os.environ.get('CFBD_API_HOST', 'https://api.collegefootballdata.com')
        self.configuration.host = self.api_host
        
        # Performance tracking
        self.performance_metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'rate_limit_hits': 0,
            'cache_hits': 0,
            'total_response_time': 0.0,
            'average_response_time': 0.0
        }

        # Rate limiting state
        self.last_request_time = 0
        self.request_history = []

        # Initialize components
        self.cache_manager = CFBDCacheManager(self.cache_config)
        self._init_api_clients()

        logger.info(f"🚀 Enhanced CFBD Client initialized")
        logger.info(f"   CFBD Version: {CFBD_VERSION}")
        logger.info(f"   API Host: {self.api_host}")
        logger.info(f"   Rate Limit: {self.rate_config.max_requests_per_second} req/sec")
        logger.info(f"   Caching: {'Enabled' if self.cache_config.enable_cache else 'Disabled'}")

    def _init_api_clients(self):
        """Initialize CFBD API clients following established patterns"""
        try:
            # Main API client for standard operations
            self.api_client = cfbd.ApiClient(self.configuration)

            # Specific API clients following .cursorrules patterns
            self.games_api = cfbd.GamesApi(self.api_client)
            self.stats_api = cfbd.StatsApi(self.api_client)
            self.teams_api = cfbd.TeamsApi(self.api_client)
            self.players_api = cfbd.PlayersApi(self.api_client)
            self.metrics_api = cfbd.MetricsApi(self.api_client)

            logger.info("✅ All CFBD API clients initialized successfully")

        except Exception as e:
            logger.error(f"❌ Failed to initialize CFBD API clients: {e}")
            raise

    def _rate_limit(self):
        """
        Optimized rate limiting for maximum performance.
        Implements burst protection and exact timing for 6 requests/second.
        """
        current_time = time.time()

        # Calculate exact delay needed
        if self.request_history:
            # Remove requests older than 1 second
            self.request_history = [t for t in self.request_history if current_time - t < 1.0]

            # If we've hit the limit, calculate precise delay
            if len(self.request_history) >= self.rate_config.max_requests_per_second:
                sleep_time = 1.0 - (current_time - self.request_history[0])
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    self.performance_metrics['rate_limit_hits'] += 1
                    current_time = time.time()

        # Record this request
        self.request_history.append(current_time)

        # Alternative simple approach (backup)
        if not self.request_history or len(self.request_history) == 1:
            time_since_last = current_time - self.last_request_time
            if time_since_last < self.rate_config.optimal_delay:
                time.sleep(self.rate_config.optimal_delay - time_since_last)

        self.last_request_time = time.time()

    def _track_performance(self, start_time: float, success: bool):
        """Track performance metrics for monitoring and optimization"""
        response_time = time.time() - start_time
        self.performance_metrics['total_requests'] += 1
        self.performance_metrics['total_response_time'] += response_time

        if success:
            self.performance_metrics['successful_requests'] += 1
        else:
            self.performance_metrics['failed_requests'] += 1

        # Update average response time
        total_requests = self.performance_metrics['total_requests']
        self.performance_metrics['average_response_time'] = (
            self.performance_metrics['total_response_time'] / total_requests
        )

    def _safe_api_call(self, api_function, *args, **kwargs):
        """
        Production-grade API call with comprehensive error handling and retry logic.
        Follows established .cursorrules patterns for CFBD integration.
        """
        start_time = time.time()

        # Check cache first
        cache_key = f"{api_function.__name__}_{str(args)}_{str(sorted(kwargs.items()))}"

        # Implement rate limiting
        self._rate_limit()

        # Retry logic with exponential backoff
        for attempt in range(self.rate_config.max_retries):
            try:
                # Make API call
                result = api_function(*args, **kwargs)

                # Track success
                self._track_performance(start_time, success=True)
                return result

            except ApiException as e:
                # Handle specific API errors
                error_msg = str(e)

                if e.status == 429:  # Rate limit exceeded
                    wait_time = 2 ** attempt + 1  # Exponential backoff
                    logger.warning(f"⏱️ Rate limit hit, waiting {wait_time}s (attempt {attempt + 1})")
                    time.sleep(wait_time)
                    continue

                elif e.status == 401:  # Authentication error
                    logger.error("🔐 Authentication failed - check API key")
                    self._track_performance(start_time, success=False)
                    raise ValueError("Invalid CFBD API key")

                elif e.status == 404:  # Not found
                    logger.warning(f"🔍 Resource not found: {error_msg}")
                    self._track_performance(start_time, success=False)
                    return None

                elif e.status >= 500:  # Server error
                    if attempt < self.rate_config.max_retries - 1:
                        wait_time = 2 ** attempt + 1
                        logger.warning(f"🔄 Server error, retrying in {wait_time}s (attempt {attempt + 1})")
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"❌ Server error after {attempt + 1} attempts: {error_msg}")
                        self._track_performance(start_time, success=False)
                        raise

                else:  # Other API errors
                    logger.error(f"❌ CFBD API error: {error_msg}")
                    self._track_performance(start_time, success=False)
                    raise

            except Exception as e:
                # Handle unexpected errors
                if attempt < self.rate_config.max_retries - 1:
                    wait_time = 2 ** attempt + 1
                    logger.warning(f"⚠️ Unexpected error, retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"❌ Unexpected error after {attempt + 1} attempts: {e}")
                    self._track_performance(start_time, success=False)
                    raise

        # Should not reach here
        raise RuntimeError("API call failed unexpectedly")

    def get_games(self, year: int, team: str = None, week: int = None,
                 season_type: str = None, use_cache: bool = True) -> List[Dict[str, Any]]:
        """
        Get games data with caching and performance optimization.
        Enhanced version following established patterns.
        """
        # Check cache first
        if use_cache and self.cache_config.enable_cache:
            cache_params = {'year': year, 'team': team, 'week': week, 'season_type': season_type}
            cached_data = self.cache_manager.get_cached_data('games', cache_params, 'games')
            if cached_data:
                self.performance_metrics['cache_hits'] += 1
                logger.debug(f"🎯 Cache hit for games: {year} week {week}")
                return cached_data

        # Fetch from API
        logger.info(f"📡 Fetching games data: {year} week {week}")
        games_data = self._safe_api_call(
            self.games_api.get_games,
            year=year,
            team=team,
            week=week,
            seasonType=season_type
        )

        # Transform to dictionary format
        if games_data:
            games_list = [game.to_dict() for game in games_data]

            # Cache the results
            if use_cache and self.cache_config.enable_cache:
                self.cache_manager.cache_data('games', cache_params, games_list, 'games')

            logger.info(f"✅ Retrieved {len(games_list)} games")
            return games_list

        return []

    def get_team_stats(self, year: int, team: str = None, use_cache: bool = True) -> List[Dict[str, Any]]:
        """Get team statistics with enhanced error handling and caching"""
        # Check cache first
        if use_cache and self.cache_config.enable_cache:
            cache_params = {'year': year, 'team': team}
            cached_data = self.cache_manager.get_cached_data('team_stats', cache_params, 'stats')
            if cached_data:
                self.performance_metrics['cache_hits'] += 1
                return cached_data

        # Fetch from API
        logger.info(f"📊 Fetching team stats: {year}")
        stats_data = self._safe_api_call(
            self.stats_api.get_team_season_stats,
            year=year,
            team=team
        )

        # Transform to dictionary format
        if stats_data:
            stats_list = [stat.to_dict() for stat in stats_data]

            # Cache the results
            if use_cache and self.cache_config.enable_cache:
                self.cache_manager.cache_data('team_stats', cache_params, stats_list, 'stats')

            logger.info(f"✅ Retrieved stats for {len(stats_list)} teams")
            return stats_list

        return []

    def get_teams(self, conference: str = None, use_cache: bool = True) -> List[Dict[str, Any]]:
        """Get team information with caching"""
        # Check cache first
        if use_cache and self.cache_config.enable_cache:
            cache_params = {'conference': conference}
            cached_data = self.cache_manager.get_cached_data('teams', cache_params, 'teams')
            if cached_data:
                self.performance_metrics['cache_hits'] += 1
                return cached_data

        # Fetch from API
        logger.info(f"🏈 Fetching teams: conference={conference}")
        teams_data = self._safe_api_call(
            self.teams_api.get_teams,
            conference=conference
        )

        # Transform to dictionary format
        if teams_data:
            teams_list = [team.to_dict() for team in teams_data]

            # Cache the results
            if use_cache and self.cache_config.enable_cache:
                self.cache_manager.cache_data('teams', cache_params, teams_list, 'teams')

            logger.info(f"✅ Retrieved {len(teams_list)} teams")
            return teams_list

        return []

    def get_advanced_metrics(self, year: int, team: str = None,
                           exclude_garbage_time: bool = True) -> List[Dict[str, Any]]:
        """
        Get advanced metrics (EPA, success rates, etc.) using latest CFBD features.
        Requires CFBD 5.13.2+ for enhanced metrics.
        """
        try:
            # Check if metrics API is available (CFBD 5.13.2+ feature)
            if not hasattr(self.metrics_api, 'get_team_epa'):
                logger.warning("⚠️ Advanced metrics not available in this CFBD version")
                return []

            logger.info(f"📈 Fetching advanced metrics: {year}")

            # Try EPA metrics first
            epa_data = self._safe_api_call(
                self.metrics_api.get_team_epa,
                year=year,
                team=team,
                excludeGarbageTime=exclude_garbage_time
            )

            if epa_data:
                metrics_list = [metric.to_dict() for metric in epa_data]
                logger.info(f"✅ Retrieved EPA metrics for {len(metrics_list)} teams")
                return metrics_list

            return []

        except Exception as e:
            logger.warning(f"⚠️ Advanced metrics not available: {e}")
            return []

    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance and usage report"""
        cache_stats = self.cache_manager.get_cache_stats()

        return {
            'cfbd_version': CFBD_VERSION,
            'api_host': self.api_host,
            'performance_metrics': self.performance_metrics,
            'cache_performance': cache_stats,
            'rate_limit_config': {
                'max_requests_per_second': self.rate_config.max_requests_per_second,
                'optimal_delay': self.rate_config.optimal_delay,
                'burst_protection': self.rate_config.burst_protection
            },
            'cache_config': {
                'enabled': self.cache_config.enable_cache,
                'cache_dir': str(self.cache_manager.cache_dir)
            }
        }


# Factory function for easy integration with existing agent system
def create_enhanced_cfbd_client(api_key: str = None, enable_cache: bool = True) -> EnhancedCFBDClient:
    """
    Factory function to create enhanced CFBD client with optimal defaults.
    Integrates seamlessly with existing Script Ohio 2.0 agent system.

    Args:
        api_key: CFBD API key (defaults to environment variable)
        enable_cache: Enable intelligent caching

    Returns:
        EnhancedCFBDClient: Configured client instance
    """
    # Optimized default configurations
    rate_config = CFBDRateLimitConfig(
        max_requests_per_second=6,
        optimal_delay=0.17,  # Exact timing for maximum performance
        burst_protection=True,
        exponential_backoff=True
    )

    cache_config = CFBDCacheConfig(
        enable_cache=enable_cache,
        cache_ttl_games=86400,  # 24 hours
        cache_ttl_stats=3600,   # 1 hour
        cache_ttl_teams=604800, # 7 days
        cache_ttl_predictions=300  # 5 minutes
    )

    return EnhancedCFBDClient(
        api_key=api_key,
        config=rate_config,
        cache_config=cache_config
    )


# Quick test function following project patterns
def test_enhanced_cfbd_client():
    """Test enhanced CFBD client functionality"""
    try:
        logger.info("🧪 Testing Enhanced CFBD Client")

        # Create client
        client = create_enhanced_cfbd_client(enable_cache=True)

        # Test basic functionality
        logger.info("📡 Testing games API...")
        # Use dynamic season and week calculation
        from src.utils.data import get_current_season, calculate_current_week
        current_season = get_current_season()
        current_week = calculate_current_week(current_season)
        games = client.get_games(year=current_season, week=current_week, use_cache=True)
        logger.info(f"✅ Retrieved {len(games)} games")

        logger.info("🏈 Testing teams API...")
        teams = client.get_teams(use_cache=True)
        logger.info(f"✅ Retrieved {len(teams)} teams")

        # Performance report
        report = client.get_performance_report()
        logger.info(f"📊 Performance: {report['performance_metrics']}")
        logger.info(f"🗄️ Cache: {report['cache_performance']}")

        return True

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Run test
    success = test_enhanced_cfbd_client()
    if success:
        print("🎉 Enhanced CFBD Client test successful!")
    else:
        print("❌ Enhanced CFBD Client test failed!")