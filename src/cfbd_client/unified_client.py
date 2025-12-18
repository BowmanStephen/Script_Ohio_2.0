"""
Unified CFBD API client consolidating best practices from all existing implementations.
This replaces: src/cfbd_client/client.py, src/data_sources/cfbd_client.py,
starter_pack/utils/cfbd_loader.py, and agents/core/enhanced_cfbd_integration.py
"""

import hashlib
import json
import logging
import os
import pickle
import random
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

import cfbd
from cfbd.rest import ApiException

from .cfbd_cache_manager import CFBDCacheConfig, CFBDCacheManager
from .errors import (
    CFBDAuthenticationError,
    CFBDClientError,
    CFBDForbiddenError,
    CFBDNotFoundError,
    CFBDRateLimitError,
    CFBDServerError,
)

try:
    from ..config.cfbd_config import CFBDConfig
except ImportError:
    # Fallback if config module not available
    from src.config.cfbd_config import CFBDConfig

# Import the new authentication manager
try:
    from ..auth.authentication_manager import get_auth_manager
except ImportError:
    # Fallback if auth module not available
    from src.auth.authentication_manager import get_auth_manager

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
            if self.successful_requests > 0
            else 0.0
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
        """Initialize CFBD API client with proper authentication using centralized auth manager"""
        try:
            # Use the centralized authentication manager for consistent auth
            auth_manager = get_auth_manager()

            # Configure CFBD client with the working authentication pattern
            configuration = cfbd.Configuration()
            configuration.host = self.config.host

            # Let the auth manager configure authentication properly
            auth_manager.configure_cfbd_client(configuration, "rest")

            # Create API client
            self.api_client = cfbd.ApiClient(configuration)

            # Initialize API endpoints
            self.games_api = cfbd.GamesApi(self.api_client)
            self.stats_api = cfbd.StatsApi(self.api_client)
            self.teams_api = cfbd.TeamsApi(self.api_client)
            self.ratings_api = cfbd.RatingsApi(self.api_client)
            self.betting_api = cfbd.BettingApi(self.api_client)
            self.plays_api = cfbd.PlaysApi(self.api_client)
            self.drives_api = cfbd.DrivesApi(self.api_client)
            self.players_api = cfbd.PlayersApi(self.api_client)
            self.conferences_api = cfbd.ConferencesApi(self.api_client)
            self.metrics_api = cfbd.MetricsApi(self.api_client)
            self.rankings_api = cfbd.RankingsApi(self.api_client)
            self.coaches_api = cfbd.CoachesApi(self.api_client)
            self.recruiting_api = cfbd.RecruitingApi(self.api_client)
            self.venues_api = cfbd.VenuesApi(self.api_client)

            # Initialize GraphQL client if available and enabled
            self.graphql_client = None
            try:
                from src.data_sources.cfbd_graphql import (
                    GQL_AVAILABLE,
                    CFBDGraphQLClient,
                )

                if GQL_AVAILABLE and not self.config.graphql_disabled:
                    # Determine host type from URL if not explicitly set
                    host_type = "production"
                    if "apinext" in self.config.host:
                        host_type = "next"

                    self.graphql_client = CFBDGraphQLClient(
                        api_key=self.config.api_key, host=host_type
                    )
                    logger.info("✅ Unified Client: GraphQL enabled")
            except ImportError:
                logger.debug("GraphQL dependencies not present")
            except Exception as e:
                logger.warning(f"Failed to initialize GraphQL client: {e}")

            self.rankings_api = cfbd.RankingsApi(self.api_client)

        except Exception as e:
            logger.error(f"❌ Failed to initialize CFBD client: {e}")
            raise

    def _rate_limit(self):
        """Implement rate limiting with burst protection"""
        current_time = time.time()

        # Remove requests older than 1 second
        self.request_history = [
            t for t in self.request_history if current_time - t < 1.0
        ]

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

    def _parse_retry_after(self, exception: ApiException, attempt: int) -> float:
        """
        Parse Retry-After header from API exception.

        Args:
            exception: ApiException with potential Retry-After header
            attempt: Current retry attempt number

        Returns:
            Wait time in seconds (uses Retry-After if present, otherwise exponential backoff)
        """
        # Try to get Retry-After header
        retry_after = None
        if hasattr(exception, "headers") and exception.headers:
            # Headers might be a dict or CaseInsensitiveDict
            headers = exception.headers
            if isinstance(headers, dict):
                # Try case-insensitive lookup
                for key, value in headers.items():
                    if key.lower() == "retry-after":
                        retry_after = value
                        break
            elif hasattr(headers, "get"):
                retry_after = headers.get("Retry-After") or headers.get("retry-after")

        if retry_after:
            try:
                # Retry-After can be seconds (integer) or HTTP date
                wait_time = float(retry_after)
                # Cap at reasonable maximum (5 minutes)
                wait_time = min(wait_time, 300)
                logger.info(f"📋 Using Retry-After header: {wait_time}s")
                return wait_time
            except (ValueError, TypeError):
                # If it's a date string, fall back to exponential backoff
                logger.warning(f"⚠️ Could not parse Retry-After header: {retry_after}")

        # Fall back to bounded exponential backoff
        wait_time = min(2**attempt + 1, 60)  # Cap at 60 seconds
        return wait_time

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
        # Only retry idempotent operations (GET/HEAD)
        # GraphQL queries are effectively idempotent, but mutations are not
        import random

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
                # Convert to CFBD error taxonomy
                from .errors import convert_api_exception

                cfbd_error = convert_api_exception(e)

                # Handle specific API errors
                self.metrics.errors += 1
                self.metrics.total_requests += 1

                if isinstance(
                    cfbd_error, CFBDRateLimitError
                ):  # Rate limit exceeded (429)
                    # Use Retry-After if available, otherwise exponential backoff
                    wait_time = (
                        cfbd_error.retry_after
                        if cfbd_error.retry_after
                        else self._parse_retry_after(e, attempt)
                    )
                    # Add jitter to prevent retry storms (random 0-20% of wait time)
                    jitter = random.uniform(0, wait_time * 0.2)
                    wait_time += jitter
                    self.metrics.rate_limit_hits += 1
                    logger.warning(
                        f"⏱️ Rate limit hit, waiting {wait_time:.2f}s (attempt {attempt + 1}, jitter={jitter:.2f}s)"
                    )
                    time.sleep(wait_time)
                    continue

                elif isinstance(
                    cfbd_error, CFBDAuthenticationError
                ):  # Authentication error (401)
                    logger.error("🔐 Authentication failed - check API key")
                    raise cfbd_error

                elif isinstance(cfbd_error, CFBDForbiddenError):  # Forbidden (403)
                    logger.error("🚫 Access forbidden - check API key permissions")
                    raise cfbd_error

                elif isinstance(cfbd_error, CFBDNotFoundError):  # Not found (404)
                    # Raise 404 errors at client layer - don't silently return None
                    # This helps catch bugs (wrong paths, API changes, client issues)
                    # If specific endpoints need "empty on 404", handle it in the endpoint wrapper
                    logger.warning(f"🔍 Resource not found: {cfbd_error.message}")
                    raise cfbd_error

                elif isinstance(cfbd_error, CFBDServerError):  # Server error (5xx)
                    if attempt < self.config.max_retries - 1:
                        # Bounded exponential backoff for 5xx errors with jitter
                        wait_time = min(2**attempt + 1, 60)  # Cap at 60 seconds
                        # Add jitter to prevent retry storms (random 0-20% of wait time)
                        jitter = random.uniform(0, wait_time * 0.2)
                        wait_time += jitter
                        logger.warning(
                            f"🔄 Server error, retrying in {wait_time:.2f}s (attempt {attempt + 1}, jitter={jitter:.2f}s)"
                        )
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error(
                            f"❌ Server error after {attempt + 1} attempts: {cfbd_error.message}"
                        )
                        raise cfbd_error

                else:
                    # Other errors
                    logger.error(f"❌ API error: {cfbd_error.message}")
                    raise cfbd_error

            except Exception as e:
                self.metrics.errors += 1
                self.metrics.total_requests += 1
                logger.error(f"❌ Unexpected error: {str(e)}")
                raise

        return None

    def request(
        self, method: str, path: str, params: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Generic request method for CFBD API endpoints.

        This method provides a unified interface for making API requests with
        automatic rate limiting, error handling, retries, and caching.

        Args:
            method: HTTP method (GET, POST, etc.) - currently only GET supported
            path: API endpoint path (e.g., "/games", "/drives", "/players")
            params: Query parameters as dictionary

        Returns:
            API response data (converted to list of dicts)

        Raises:
            CFBDClientError: For API errors (converted to error taxonomy)
            ValueError: For invalid method or path
        """
        if method.upper() != "GET":
            raise ValueError(
                f"Unsupported HTTP method: {method}. Only GET is currently supported."
            )

        if not path.startswith("/"):
            path = "/" + path

        params = params or {}

        # Map common endpoints to API methods
        # This allows using the generic request() method while leveraging
        # existing optimized methods when available
        endpoint_lower = path.lower().strip("/")

        if endpoint_lower == "games":
            return self.get_games(
                year=params.get("year", params.get("season", 2025)),
                week=params.get("week"),
                season_type=params.get(
                    "seasonType", params.get("season_type", "regular")
                ),
                team=params.get("team"),
            )
        elif endpoint_lower == "ratings":
            return self.get_ratings(
                year=params.get("year", params.get("season", 2025)),
                week=params.get("week"),
            )
        elif endpoint_lower == "lines":
            return self.get_lines(
                year=params.get("year", params.get("season", 2025)),
                week=params.get("week", params.get("week_number")),
            )
        elif endpoint_lower == "team_talent" or endpoint_lower == "teams/talent":
            return self.get_team_talent(
                year=params.get("year", params.get("season", 2025)),
            )
        elif endpoint_lower == "stats" or endpoint_lower == "team_season_stats":
            return self.get_stats(
                year=params.get("year", params.get("season", 2025)),
                team=params.get("team"),
                category=params.get("category"),
            )
        elif endpoint_lower == "drives":
            return self.get_drives(
                year=params.get("year", params.get("season", 2025)),
                week=params.get("week"),
                season_type=params.get(
                    "seasonType", params.get("season_type", "regular")
                ),
                team=params.get("team"),
                offense=params.get("offense"),
                defense=params.get("defense"),
                conference=params.get("conference"),
            )
        elif endpoint_lower == "players" or endpoint_lower == "player/season/stats":
            return self.get_player_stats(
                year=params.get("year", params.get("season", 2025)),
                team=params.get("team"),
                conference=params.get("conference"),
                category=params.get("category"),
            )
        elif endpoint_lower == "conferences":
            return self.get_conferences()
        elif (
            endpoint_lower == "advanced_season_stats"
            or endpoint_lower == "stats/advanced"
        ):
            return self.get_advanced_stats(
                year=params.get("year", params.get("season", 2025)),
                team=params.get("team"),
            )
        else:
            # For unmapped endpoints, use direct API client call
            # This is a fallback for endpoints not yet explicitly supported
            logger.warning(f"Using generic request for unmapped endpoint: {path}")
            # For now, raise an error - can be extended later
            raise ValueError(
                f"Endpoint {path} not yet supported. Use specific methods or request implementation."
            )

    def _get_cache_key(self, endpoint: str, params: Dict[str, Any]) -> str:
        """Generate cache key for API call"""
        key_data = f"{endpoint}_{json.dumps(params, sort_keys=True, default=str)}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def _cached_fetch(
        self,
        endpoint: str,
        params: Dict[str, Any],
        api_function,
        cache_type: str = "stats",
    ) -> Any:
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
            return [
                item.to_dict() if hasattr(item, "to_dict") else item for item in data
            ]
        return [data.to_dict() if hasattr(data, "to_dict") else data]

    def get_games(
        self,
        year: int,
        week: Optional[int] = None,
        season_type: str = "regular",
        team: Optional[str] = None,
    ) -> List[Dict]:
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
            lambda: self._to_dict_list(
                self.games_api.get_games(
                    year=year,
                    week=week,
                    season_type=season_type,
                    team=team,
                )
            ),
            "games",
        )

    def get_ratings(self, year: int, week: Optional[int] = None) -> List[Dict]:
        """Get ratings data with caching"""
        params = {"year": year, "week": week}
        return self._cached_fetch(
            "ratings",
            params,
            lambda: self._to_dict_list(self.ratings_api.get_elo(year=year, week=week)),
            "ratings",
        )

    def get_lines(self, year: int, week: int) -> List[Dict]:
        """Get betting lines with caching"""
        params = {"year": year, "week": week}
        return self._cached_fetch(
            "lines",
            params,
            lambda: self._to_dict_list(
                self.betting_api.get_lines(year=year, week=week)
            ),
            "lines",
        )

    def get_teams(self, conference: Optional[str] = None) -> List[Dict]:
        """Get teams data with caching"""
        params = {"conference": conference}
        return self._cached_fetch(
            "teams",
            params,
            lambda: self._to_dict_list(self.teams_api.get_teams(conference=conference)),
            "teams",
        )

    def get_team_talent(self, year: int) -> List[Dict]:
        """Get team talent ratings with caching"""
        params = {"year": year}
        return self._cached_fetch(
            "team_talent",
            params,
            lambda: self._to_dict_list(self.teams_api.get_team_talent(year=year)),
            "teams",
        )

    def get_stats(
        self, year: int, team: Optional[str] = None, category: Optional[str] = None
    ) -> List[Dict]:
        """Get team statistics with caching"""
        params = {"year": year, "team": team, "category": category}
        return self._cached_fetch(
            "stats",
            params,
            lambda: self._to_dict_list(
                self.stats_api.get_team_season_stats(
                    year=year, team=team, category=category
                )
            ),
            "stats",
        )

    def get_drives(
        self,
        year: int,
        week: Optional[int] = None,
        season_type: str = "regular",
        team: Optional[str] = None,
        offense: Optional[str] = None,
        defense: Optional[str] = None,
        conference: Optional[str] = None,
    ) -> List[Dict]:
        """Get drives data with caching"""
        params = {
            "year": year,
            "week": week,
            "seasonType": season_type,
            "team": team,
            "offense": offense,
            "defense": defense,
            "conference": conference,
        }
        return self._cached_fetch(
            "drives",
            params,
            lambda: self._to_dict_list(
                self.drives_api.get_drives(
                    year=year,
                    week=week,
                    season_type=season_type,
                    team=team,
                    offense=offense,
                    defense=defense,
                    conference=conference,
                )
            ),
            "stats",  # Drives are statistical data
        )

    def get_player_stats(
        self,
        year: int,
        team: Optional[str] = None,
        conference: Optional[str] = None,
        category: Optional[str] = None,
    ) -> List[Dict]:
        """Get player statistics with caching"""
        params = {
            "year": year,
            "team": team,
            "conference": conference,
            "category": category,
        }
        return self._cached_fetch(
            "player_stats",
            params,
            lambda: self._to_dict_list(
                self.players_api.get_player_season_stats(
                    year=year, team=team, conference=conference, category=category
                )
            ),
            "stats",
        )

    def get_conferences(self) -> List[Dict]:
        """Get conference information with caching"""
        params = {}
        return self._cached_fetch(
            "conferences",
            params,
            lambda: self._to_dict_list(self.conferences_api.get_conferences()),
            "teams",  # Conferences are relatively stable like team data
        )

    def get_advanced_stats(self, year: int, team: Optional[str] = None) -> List[Dict]:
        """Get advanced season statistics with caching"""
        params = {"year": year, "team": team}
        return self._cached_fetch(
            "advanced_stats",
            params,
            lambda: self._to_dict_list(
                self.stats_api.get_advanced_season_stats(year=year, team=team)
            ),
            "stats",
        )

    def get_plays(
        self,
        year: int,
        week: Optional[int] = None,
        season_type: str = "regular",
        team: Optional[str] = None,
    ) -> List[Dict]:
        """Get play-by-play data with caching"""
        params = {"year": year, "week": week, "seasonType": season_type, "team": team}
        return self._cached_fetch(
            "plays",
            params,
            lambda: self._to_dict_list(
                self.plays_api.get_plays(
                    year=year, week=week, season_type=season_type, team=team
                )
            ),
            "stats",  # Plays are statistical data
        )

    def get_recruiting(self, year: int, team: Optional[str] = None) -> List[Dict]:
        """Get recruiting information with caching"""
        params = {"year": year, "team": team}
        return self._cached_fetch(
            "recruiting",
            params,
            lambda: self._to_dict_list(
                self.recruiting_api.get_team_recruiting_rankings(year=year)
            ),
            "teams",  # Recruiting data is relatively stable
        )

    def get_venues(self) -> List[Dict]:
        """Get venue data with caching"""
        params = {}
        return self._cached_fetch(
            "venues",
            params,
            lambda: self._to_dict_list(self.venues_api.get_venues()),
            "teams",  # Venues are relatively stable
        )

    def get_coaches(
        self,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        team: Optional[str] = None,
        year: Optional[int] = None,
    ) -> List[Dict]:
        """Get coach information with caching"""
        params = {
            "first_name": first_name,
            "last_name": last_name,
            "team": team,
            "year": year,
        }
        return self._cached_fetch(
            "coaches",
            params,
            lambda: self._to_dict_list(
                self.coaches_api.get_coaches(
                    first_name=first_name, last_name=last_name, team=team, year=year
                )
            ),
            "teams",  # Coach data is relatively stable
        )

    def get_rankings(
        self, year: int, week: Optional[int] = None, season_type: str = "regular"
    ) -> List[Dict]:
        """Get poll rankings with caching"""
        params = {"year": year, "week": week, "seasonType": season_type}
        return self._cached_fetch(
            "rankings",
            params,
            lambda: self._to_dict_list(
                self.rankings_api.get_rankings(
                    year=year, week=week, season_type=season_type
                )
            ),
            "ratings",  # Rankings are similar to ratings data
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
            },
        }

    def get_game_media(
        self,
        year: int,
        week: Optional[int] = None,
        season_type: str = "regular",
        team: Optional[str] = None,
        conference: Optional[str] = None,
    ) -> List[Dict]:
        """Get game media information with caching"""
        params = {
            "year": year,
            "week": week,
            "seasonType": season_type,
            "team": team,
            "conference": conference,
        }
        return self._cached_fetch(
            "media",
            params,
            lambda: self._to_dict_list(
                self.games_api.get_game_media(
                    year=year,
                    week=week,
                    season_type=season_type,
                    team=team,
                    conference=conference,
                )
            ),
            "games",
        )

    def get_calendar(self, year: int) -> List[Dict]:
        """Get season calendar with caching"""
        params = {"year": year}
        return self._cached_fetch(
            "calendar",
            params,
            lambda: self._to_dict_list(self.games_api.get_calendar(year=year)),
            "games",
        )

    def get_box_score(self, game_id: int) -> Dict:
        """Get box score for a specific game"""
        params = {"gameId": game_id}
        # Box score returns a single object
        return self._cached_fetch(
            "box_score",
            params,
            lambda: self.games_api.get_game_box_score(game_id=game_id).to_dict(),
            "games",
        )

    def get_team_matchup(
        self,
        team1: str,
        team2: str,
        min_year: Optional[int] = None,
        max_year: Optional[int] = None,
    ) -> Dict:
        """Get matchup history between two teams"""
        params = {
            "team1": team1,
            "team2": team2,
            "minYear": min_year,
            "maxYear": max_year,
        }
        return self._cached_fetch(
            "matchup",
            params,
            lambda: self.teams_api.get_team_matchup(
                team1=team1, team2=team2, min_year=min_year, max_year=max_year
            ).to_dict(),
            "teams",
        )

    def get_roster(self, year: int, team: Optional[str] = None) -> List[Dict]:
        """Get team roster with caching"""
        params = {"year": year, "team": team}
        return self._cached_fetch(
            "roster",
            params,
            lambda: self._to_dict_list(self.teams_api.get_roster(year=year, team=team)),
            "teams",
        )

    def get_win_probabilities(
        self, year: int, week: Optional[int] = None, team: Optional[str] = None
    ) -> List[Dict]:
        """Get pregame win probabilities with caching"""
        params = {"year": year, "week": week, "team": team}
        return self._cached_fetch(
            "win_probs",
            params,
            lambda: self._to_dict_list(
                self.metrics_api.get_pregame_win_probabilities(
                    year=year, week=week, team=team
                )
            ),
            "metrics",
        )

    def get_scoreboard_graphql(
        self, year: int, week: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get scoreboard data via GraphQL (efficient batch fetch).
        Returns None if GraphQL is unavailable.
        """
        if not self.graphql_client:
            return None

        return self._cached_fetch(
            "gql_scoreboard",
            {"year": year, "week": week},
            lambda: self.graphql_client.get_scoreboard(season=year, week=week),
            "games",
        )

    def get_recruiting_graphql(
        self, year: int, team: Optional[str] = None, limit: int = 50
    ) -> Optional[Dict[str, Any]]:
        """
        Get recruiting data via GraphQL (richer data than REST).
        Returns None if GraphQL is unavailable.
        """
        if not self.graphql_client:
            return None

        return self._cached_fetch(
            "gql_recruiting",
            {"year": year, "team": team, "limit": limit},
            lambda: self.graphql_client.get_recruits(
                season=year, team=team, limit=limit
            ),
            "recruiting",
        )
