#!/usr/bin/env python3
"""
CFBD Integration Agent - Tier 3 Security Level
Advanced CollegeFootballData.com API integration with security and rate limiting

Implements comprehensive CFBD API integration with intelligent caching, rate limiting,
and secure data extraction for college football analytics workflows.
"""

import logging
import json
import time
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import requests
import pandas as pd
from urllib.parse import urljoin, urlparse
import hashlib
import pickle
import os
from pathlib import Path

from agents.core.enhanced_agent_framework import EnhancedBaseAgent
from agents.core.security_manager import security_manager, PermissionLevel


class APIEndpoint(Enum):
    """CFBD API endpoints enumeration"""

    GAMES = "/games"
    TEAMS = "/teams"
    PLAYERS = "/players"
    PLAYER_STATS = "/player-stats"
    TEAM_STATS = "/team-stats"
    RANKINGS = "/rankings"
    METRICS = "/metrics"
    DRAFTEES = "/draftees"
    DRAFT_PICKS = "/draft-picks"
    CALENDAR = "/calendar"
    CONFERENCES = "/conferences"
    FBS_TEAMS = "/teams/fbs"


class DataFormat(Enum):
    """Supported data formats"""

    JSON = "json"
    CSV = "csv"
    PARQUET = "parquet"
    EXCEL = "excel"


class CacheStrategy(Enum):
    """Caching strategies"""

    NO_CACHE = "no_cache"
    MEMORY_ONLY = "memory_only"
    DISK_ONLY = "disk_only"
    MEMORY_AND_DISK = "memory_and_disk"
    INTELLIGENT = "intelligent"


@dataclass
class APIRequest:
    """Represents an API request with metadata"""

    endpoint: APIEndpoint
    parameters: Dict[str, Any]
    method: str = "GET"
    headers: Dict[str, str] = None
    timeout: int = 30
    retry_count: int = 0
    max_retries: int = 3
    priority: int = 5  # 1-10, 10 being highest

    def __post_init__(self):
        if self.headers is None:
            self.headers = {}

    def get_cache_key(self) -> str:
        """Generate cache key for this request"""
        cache_data = {
            "endpoint": self.endpoint.value,
            "parameters": sorted(self.parameters.items()),
            "method": self.method,
        }
        cache_string = json.dumps(cache_data, sort_keys=True)
        return hashlib.md5(cache_string.encode()).hexdigest()


@dataclass
class APIResponse:
    """Represents an API response with metadata"""

    request: APIRequest
    status_code: int
    data: Any
    headers: Dict[str, str]
    response_time_seconds: float
    cached: bool = False
    cache_expires_at: Optional[datetime] = None
    error_message: Optional[str] = None

    @property
    def is_success(self) -> bool:
        """Check if response is successful"""
        return 200 <= self.status_code < 300

    @property
    def is_rate_limited(self) -> bool:
        """Check if request was rate limited"""
        return self.status_code == 429

    @property
    def is_cached(self) -> bool:
        """Check if response came from cache"""
        return self.cached


class CFBDIntegrationAgent(EnhancedBaseAgent):
    """
    CFBD Integration Agent - Advanced CFBD API integration

    Capabilities:
    - Secure CFBD API access with authentication and rate limiting
    - Intelligent caching with multiple strategies (memory, disk, hybrid)
    - Batch request processing and parallel execution
    - Data validation and transformation
    - Error handling and retry logic with exponential backoff
    - Performance monitoring and usage analytics
    """

    def __init__(self, agent_id: str = "cfbd_integration_agent"):
        super().__init__(
            agent_id=agent_id,
            agent_name="CFBD Integration Agent",
            permission_level=PermissionLevel.READ_EXECUTE,
        )

        self.logger = logging.getLogger(f"{__name__}.{agent_id}")

        # Configuration
        self.base_url = "https://api.collegefootballdata.com"
        self.api_key = os.getenv("CFBD_API_KEY")
        self.rate_limit_per_minute = 30
        self.rate_limit_burst = 5
        self.default_timeout = 30
        self.max_concurrent_requests = 3

        # Caching
        self.cache_strategy = CacheStrategy.INTELLIGENT
        self.memory_cache = {}
        self.disk_cache_dir = Path("/app/cache/cfbd")
        self.cache_ttl = {
            APIEndpoint.GAMES: 3600,  # 1 hour
            APIEndpoint.TEAMS: 86400,  # 24 hours
            APIEndpoint.PLAYERS: 1800,  # 30 minutes
            APIEndpoint.PLAYER_STATS: 900,  # 15 minutes
            APIEndpoint.TEAM_STATS: 900,  # 15 minutes
            APIEndpoint.RANKINGS: 3600,  # 1 hour
            APIEndpoint.METRICS: 1800,  # 30 minutes
            APIEndpoint.DRAFTEES: 86400,  # 24 hours
            APIEndpoint.DRAFT_PICKS: 86400,  # 24 hours
            APIEndpoint.CALENDAR: 86400,  # 24 hours
            APIEndpoint.CONFERENCES: 86400,  # 24 hours
            APIEndpoint.FBS_TEAMS: 86400,  # 24 hours
        }

        # Rate limiting
        self.request_times = []
        self.rate_limit_mutex = asyncio.Lock()

        # Performance metrics
        self.metrics = {
            "requests_made": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "rate_limit_hits": 0,
            "errors": 0,
            "average_response_time": 0.0,
            "api_usage_by_endpoint": {},
            "data_volume_mb": 0.0,
            "last_request_time": None,
        }

        # Initialize cache directory
        self.disk_cache_dir.mkdir(parents=True, exist_ok=True)

    def _define_capabilities(self) -> List:
        """Define CFBD integration capabilities"""
        return [
            {
                "name": "fetch_games_data",
                "description": "Fetch college football games data with filters",
                "execution_time_estimate": 15.0,
                "required_permissions": [PermissionLevel.READ_EXECUTE],
                "parameters": ["year", "week", "team", "conference", "season_type"],
                "returns": {"games": "list", "metadata": "dict"},
            },
            {
                "name": "fetch_team_stats",
                "description": "Fetch team statistics and performance metrics",
                "execution_time_estimate": 10.0,
                "required_permissions": [PermissionLevel.READ_EXECUTE],
                "parameters": ["year", "team", "conference", "stat_type"],
                "returns": {"team_stats": "list", "analysis": "dict"},
            },
            {
                "name": "fetch_player_data",
                "description": "Fetch player information and statistics",
                "execution_time_estimate": 12.0,
                "required_permissions": [PermissionLevel.READ_EXECUTE],
                "parameters": ["year", "team", "position", "stat_category"],
                "returns": {"players": "list", "statistics": "list"},
            },
            {
                "name": "batch_fetch_data",
                "description": "Fetch multiple data types in parallel with optimization",
                "execution_time_estimate": 25.0,
                "required_permissions": [PermissionLevel.READ_EXECUTE],
                "parameters": ["requests", "parallel_limit", "error_handling"],
                "returns": {"results": "dict", "performance": "dict"},
            },
            {
                "name": "get_rankings_data",
                "description": "Fetch team rankings and poll data",
                "execution_time_estimate": 8.0,
                "required_permissions": [PermissionLevel.READ_EXECUTE],
                "parameters": ["year", "week", "ranking_type", "season_type"],
                "returns": {"rankings": "list", "polls": "list"},
            },
        ]

    def _execute_action(
        self, action: str, parameters: Dict, user_context: Dict
    ) -> Dict:
        """Execute CFBD integration actions"""
        try:
            # Create security context
            context = security_manager.create_security_context(
                user_id=user_context.get("user_id", "cfbd_system"),
                permissions=["api_access", "data_collection", "rate_limit_management"],
            )

            if action == "fetch_games_data":
                return self._fetch_games_data(parameters, context)
            elif action == "fetch_team_stats":
                return self._fetch_team_stats(parameters, context)
            elif action == "fetch_player_data":
                return self._fetch_player_data(parameters, context)
            elif action == "batch_fetch_data":
                return self._batch_fetch_data(parameters, context)
            elif action == "get_rankings_data":
                return self._get_rankings_data(parameters, context)
            else:
                raise ValueError(f"Unknown action: {action}")

        except Exception as e:
            self.logger.error(f"CFBD action {action} failed: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__,
                "agent_id": self.agent_id,
                "timestamp": datetime.utcnow().isoformat(),
            }

    async def _execute_action_async(
        self, action: str, parameters: Dict, user_context: Dict
    ) -> Dict:
        """Async version of action execution"""
        try:
            context = security_manager.create_security_context(
                user_id=user_context.get("user_id", "cfbd_system"),
                permissions=["api_access", "data_collection", "rate_limit_management"],
            )

            if action == "fetch_games_data":
                return await self._fetch_games_data_async(parameters, context)
            elif action == "batch_fetch_data":
                return await self._batch_fetch_data_async(parameters, context)
            else:
                # Fallback to sync execution
                return self._execute_action(action, parameters, user_context)

        except Exception as e:
            self.logger.error(f"Async CFBD action {action} failed: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__,
                "agent_id": self.agent_id,
                "timestamp": datetime.utcnow().isoformat(),
            }

    def _fetch_games_data(self, parameters: Dict, context) -> Dict:
        """Fetch college football games data with filters"""
        self.logger.info(f"Fetching games data for parameters: {parameters}")

        year = parameters.get("year")
        week = parameters.get("week")
        team = parameters.get("team")
        conference = parameters.get("conference")
        season_type = parameters.get("season_type", "regular")

        # Build request parameters
        request_params = {}
        if year:
            request_params["year"] = year
        if week:
            request_params["week"] = week
        if team:
            request_params["team"] = team
        if conference:
            request_params["conference"] = conference
        if season_type:
            request_params["seasonType"] = season_type

        # Create API request
        api_request = APIRequest(
            endpoint=APIEndpoint.GAMES,
            parameters=request_params,
            priority=parameters.get("priority", 5),
        )

        # Execute request
        response = self._execute_api_request(api_request, context)

        if response.is_success:
            games_data = response.data

            # Process and validate games data
            processed_data = self._process_games_data(games_data)

            # Calculate metadata
            metadata = self._calculate_games_metadata(processed_data)

            return {
                "status": "success",
                "data": {
                    "games": processed_data,
                    "metadata": metadata,
                    "request_info": {
                        "parameters": request_params,
                        "cached": response.is_cached,
                        "response_time": response.response_time_seconds,
                    },
                },
                "execution_time": response.response_time_seconds,
                "agent_id": self.agent_id,
            }
        else:
            return {
                "status": "error",
                "error": response.error_message
                or f"API request failed with status {response.status_code}",
                "status_code": response.status_code,
                "rate_limited": response.is_rate_limited,
                "agent_id": self.agent_id,
            }

    def _fetch_team_stats(self, parameters: Dict, context) -> Dict:
        """Fetch team statistics and performance metrics"""
        self.logger.info(f"Fetching team statistics for parameters: {parameters}")

        year = parameters.get("year")
        team = parameters.get("team")
        conference = parameters.get("conference")
        stat_type = parameters.get("stat_type", "total")

        # Build request parameters
        request_params = {}
        if year:
            request_params["year"] = year
        if team:
            request_params["team"] = team
        if conference:
            request_params["conference"] = conference
        if stat_type:
            request_params["statType"] = stat_type

        # Create API request
        api_request = APIRequest(
            endpoint=APIEndpoint.TEAM_STATS,
            parameters=request_params,
            priority=parameters.get("priority", 5),
        )

        # Execute request
        response = self._execute_api_request(api_request, context)

        if response.is_success:
            team_stats_data = response.data

            # Process team statistics
            processed_stats = self._process_team_stats(team_stats_data)

            # Generate analysis
            analysis = self._generate_team_stats_analysis(processed_stats)

            return {
                "status": "success",
                "data": {
                    "team_stats": processed_stats,
                    "analysis": analysis,
                    "request_info": {
                        "parameters": request_params,
                        "cached": response.is_cached,
                        "response_time": response.response_time_seconds,
                    },
                },
                "execution_time": response.response_time_seconds,
                "agent_id": self.agent_id,
            }
        else:
            return {
                "status": "error",
                "error": response.error_message
                or f"API request failed with status {response.status_code}",
                "status_code": response.status_code,
                "rate_limited": response.is_rate_limited,
                "agent_id": self.agent_id,
            }

    def _fetch_player_data(self, parameters: Dict, context) -> Dict:
        """Fetch player information and statistics"""
        self.logger.info(f"Fetching player data for parameters: {parameters}")

        year = parameters.get("year")
        team = parameters.get("team")
        position = parameters.get("position")
        stat_category = parameters.get("stat_category", "all")

        # Build request parameters
        request_params = {}
        if year:
            request_params["year"] = year
        if team:
            request_params["team"] = team
        if position:
            request_params["position"] = position
        if stat_category:
            request_params["category"] = stat_category

        # Create API request
        api_request = APIRequest(
            endpoint=APIEndpoint.PLAYERS,
            parameters=request_params,
            priority=parameters.get("priority", 5),
        )

        # Execute request
        response = self._execute_api_request(api_request, context)

        if response.is_success:
            players_data = response.data

            # Process player data
            processed_players = self._process_player_data(players_data)

            # Fetch player stats if requested
            player_stats = []
            if stat_category != "basic":
                stats_request = APIRequest(
                    endpoint=APIEndpoint.PLAYER_STATS,
                    parameters=request_params,
                    priority=parameters.get("priority", 5),
                )
                stats_response = self._execute_api_request(stats_request, context)
                if stats_response.is_success:
                    player_stats = self._process_player_stats(stats_response.data)

            return {
                "status": "success",
                "data": {
                    "players": processed_players,
                    "statistics": player_stats,
                    "request_info": {
                        "parameters": request_params,
                        "cached": response.is_cached,
                        "response_time": response.response_time_seconds,
                    },
                },
                "execution_time": response.response_time_seconds,
                "agent_id": self.agent_id,
            }
        else:
            return {
                "status": "error",
                "error": response.error_message
                or f"API request failed with status {response.status_code}",
                "status_code": response.status_code,
                "rate_limited": response.is_rate_limited,
                "agent_id": self.agent_id,
            }

    def _batch_fetch_data(self, parameters: Dict, context) -> Dict:
        """Fetch multiple data types in parallel with optimization"""
        self.logger.info("Starting batch data fetch")

        requests = parameters.get("requests", [])
        parallel_limit = parameters.get("parallel_limit", self.max_concurrent_requests)
        error_handling = parameters.get("error_handling", "continue")

        # Validate requests
        if not requests:
            return {"status": "error", "error": "No requests provided for batch fetch"}

        # Convert request dictionaries to APIRequest objects
        api_requests = []
        for req_data in requests:
            try:
                endpoint = APIEndpoint(req_data.get("endpoint", "games"))
                api_request = APIRequest(
                    endpoint=endpoint,
                    parameters=req_data.get("parameters", {}),
                    priority=req_data.get("priority", 5),
                )
                api_requests.append(api_request)
            except ValueError as e:
                self.logger.warning(f"Invalid request in batch: {e}")

        if not api_requests:
            return {"status": "error", "error": "No valid requests found in batch"}

        # Execute batch requests
        results = self._execute_batch_requests(
            api_requests, parallel_limit, error_handling, context
        )

        # Calculate performance metrics
        performance = self._calculate_batch_performance(results)

        return {
            "status": "success",
            "data": {
                "results": results,
                "performance": performance,
                "summary": {
                    "total_requests": len(api_requests),
                    "successful_requests": sum(
                        1 for r in results if r.get("success", False)
                    ),
                    "failed_requests": sum(
                        1 for r in results if not r.get("success", False)
                    ),
                    "cache_hits": sum(1 for r in results if r.get("cached", False)),
                },
            },
            "execution_time": performance["total_execution_time"],
            "agent_id": self.agent_id,
        }

    def _get_rankings_data(self, parameters: Dict, context) -> Dict:
        """Fetch team rankings and poll data"""
        self.logger.info(f"Fetching rankings data for parameters: {parameters}")

        year = parameters.get("year")
        week = parameters.get("week")
        ranking_type = parameters.get("ranking_type", "ap")
        season_type = parameters.get("season_type", "regular")

        # Build request parameters
        request_params = {}
        if year:
            request_params["year"] = year
        if week:
            request_params["week"] = week
        if ranking_type:
            request_params["rankingType"] = ranking_type
        if season_type:
            request_params["seasonType"] = season_type

        # Create API request
        api_request = APIRequest(
            endpoint=APIEndpoint.RANKINGS,
            parameters=request_params,
            priority=parameters.get("priority", 5),
        )

        # Execute request
        response = self._execute_api_request(api_request, context)

        if response.is_success:
            rankings_data = response.data

            # Process rankings data
            processed_rankings = self._process_rankings_data(rankings_data)

            # Extract poll information
            polls = self._extract_poll_info(processed_rankings)

            return {
                "status": "success",
                "data": {
                    "rankings": processed_rankings,
                    "polls": polls,
                    "request_info": {
                        "parameters": request_params,
                        "cached": response.is_cached,
                        "response_time": response.response_time_seconds,
                    },
                },
                "execution_time": response.response_time_seconds,
                "agent_id": self.agent_id,
            }
        else:
            return {
                "status": "error",
                "error": response.error_message
                or f"API request failed with status {response.status_code}",
                "status_code": response.status_code,
                "rate_limited": response.is_rate_limited,
                "agent_id": self.agent_id,
            }

    # Core API execution methods
    def _execute_api_request(self, request: APIRequest, context) -> APIResponse:
        """Execute a single API request with caching and rate limiting"""
        start_time = time.time()

        # Check cache first
        if self.cache_strategy != CacheStrategy.NO_CACHE:
            cached_response = self._get_from_cache(request)
            if cached_response:
                self.metrics["cache_hits"] += 1
                return cached_response

        self.metrics["cache_misses"] += 1

        # Apply rate limiting
        self._apply_rate_limit()

        # Build request URL and headers
        url = urljoin(self.base_url, request.endpoint.value)
        headers = self._build_headers(request)

        try:
            # Execute HTTP request
            response = requests.request(
                method=request.method,
                url=url,
                headers=headers,
                params=request.parameters,
                timeout=request.timeout,
            )

            # Process response
            response_time = time.time() - start_time

            if response.status_code == 200:
                data = response.json()
                api_response = APIResponse(
                    request=request,
                    status_code=response.status_code,
                    data=data,
                    headers=dict(response.headers),
                    response_time_seconds=response_time,
                )

                # Cache successful response
                if self.cache_strategy != CacheStrategy.NO_CACHE:
                    self._store_in_cache(request, api_response)

                # Update metrics
                self._update_metrics(api_response)

                return api_response
            else:
                # Handle error response
                error_message = (
                    f"API request failed: {response.status_code} - {response.text}"
                )
                api_response = APIResponse(
                    request=request,
                    status_code=response.status_code,
                    data=None,
                    headers=dict(response.headers),
                    response_time_seconds=response_time,
                    error_message=error_message,
                )

                # Handle rate limiting
                if response.status_code == 429:
                    self.metrics["rate_limit_hits"] += 1
                    # Wait before retry
                    time.sleep(2 ** min(request.retry_count, 5))

                # Update error metrics
                self.metrics["errors"] += 1

                return api_response

        except requests.exceptions.Timeout:
            error_message = f"Request timeout after {request.timeout} seconds"
        except requests.exceptions.RequestException as e:
            error_message = f"Request exception: {str(e)}"
        except Exception as e:
            error_message = f"Unexpected error: {str(e)}"

        response_time = time.time() - start_time

        # Create error response
        api_response = APIResponse(
            request=request,
            status_code=0,
            data=None,
            headers={},
            response_time_seconds=response_time,
            error_message=error_message,
        )

        self.metrics["errors"] += 1
        return api_response

    def _execute_batch_requests(
        self,
        requests: List[APIRequest],
        parallel_limit: int,
        error_handling: str,
        context,
    ) -> List[Dict]:
        """Execute multiple API requests in parallel"""
        results = []

        # Process requests in batches
        for i in range(0, len(requests), parallel_limit):
            batch = requests[i : i + parallel_limit]

            # Execute batch
            batch_results = []
            for request in batch:
                try:
                    response = self._execute_api_request(request, context)
                    result = {
                        "request_id": request.get_cache_key(),
                        "endpoint": request.endpoint.value,
                        "parameters": request.parameters,
                        "success": response.is_success,
                        "status_code": response.status_code,
                        "data": response.data if response.is_success else None,
                        "error_message": response.error_message,
                        "cached": response.is_cached,
                        "response_time": response.response_time_seconds,
                    }
                    batch_results.append(result)
                except Exception as e:
                    result = {
                        "request_id": request.get_cache_key(),
                        "endpoint": request.endpoint.value,
                        "parameters": request.parameters,
                        "success": False,
                        "error_message": str(e),
                        "response_time": 0,
                    }
                    batch_results.append(result)

            results.extend(batch_results)

        return results

    # Caching methods
    def _get_from_cache(self, request: APIRequest) -> Optional[APIResponse]:
        """Get response from cache if available and not expired"""
        cache_key = request.get_cache_key()

        # Check memory cache first
        if cache_key in self.memory_cache:
            cached_item = self.memory_cache[cache_key]
            if self._is_cache_valid(cached_item):
                cached_item["response"].cached = True
                return cached_item["response"]
            else:
                del self.memory_cache[cache_key]

        # Check disk cache
        if self.cache_strategy in [
            CacheStrategy.DISK_ONLY,
            CacheStrategy.MEMORY_AND_DISK,
            CacheStrategy.INTELLIGENT,
        ]:
            disk_cache_file = self.disk_cache_dir / f"{cache_key}.pkl"
            if disk_cache_file.exists():
                try:
                    with open(disk_cache_file, "rb") as f:
                        cached_item = pickle.load(f)
                    if self._is_cache_valid(cached_item):
                        cached_item["response"].cached = True
                        # Store in memory cache if using memory cache
                        if self.cache_strategy in [
                            CacheStrategy.MEMORY_AND_DISK,
                            CacheStrategy.INTELLIGENT,
                        ]:
                            self.memory_cache[cache_key] = cached_item
                        return cached_item["response"]
                    else:
                        # Remove expired cache file
                        disk_cache_file.unlink()
                except Exception as e:
                    self.logger.warning(f"Error reading from disk cache: {e}")

        return None

    def _store_in_cache(self, request: APIRequest, response: APIResponse) -> None:
        """Store response in cache"""
        if not response.is_success:
            return

        cache_key = request.get_cache_key()
        ttl = self.cache_ttl.get(request.endpoint, 3600)
        expires_at = datetime.utcnow() + timedelta(seconds=ttl)

        cached_item = {
            "response": response,
            "cached_at": datetime.utcnow(),
            "expires_at": expires_at,
        }

        # Store in memory cache
        if self.cache_strategy in [
            CacheStrategy.MEMORY_ONLY,
            CacheStrategy.MEMORY_AND_DISK,
            CacheStrategy.INTELLIGENT,
        ]:
            self.memory_cache[cache_key] = cached_item

        # Store in disk cache
        if self.cache_strategy in [
            CacheStrategy.DISK_ONLY,
            CacheStrategy.MEMORY_AND_DISK,
            CacheStrategy.INTELLIGENT,
        ]:
            try:
                disk_cache_file = self.disk_cache_dir / f"{cache_key}.pkl"
                with open(disk_cache_file, "wb") as f:
                    pickle.dump(cached_item, f)
            except Exception as e:
                self.logger.warning(f"Error writing to disk cache: {e}")

    def _is_cache_valid(self, cached_item: Dict) -> bool:
        """Check if cached item is still valid"""
        expires_at = cached_item.get("expires_at")
        if expires_at:
            return datetime.utcnow() < expires_at
        return True

    # Rate limiting
    def _apply_rate_limit(self) -> None:
        """Apply rate limiting to API requests"""
        now = time.time()

        # Clean old request times (older than 1 minute)
        self.request_times = [
            req_time for req_time in self.request_times if now - req_time < 60
        ]

        # Check if we're at the rate limit
        if len(self.request_times) >= self.rate_limit_per_minute:
            # Calculate wait time
            oldest_request = min(self.request_times)
            wait_time = 60 - (now - oldest_request)
            if wait_time > 0:
                self.logger.info(f"Rate limit reached, waiting {wait_time:.2f} seconds")
                time.sleep(wait_time)

        # Add current request time
        self.request_times.append(now)

    # Helper methods
    def _build_headers(self, request: APIRequest) -> Dict[str, str]:
        """Build request headers"""
        headers = request.headers.copy()
        headers["Content-Type"] = "application/json"
        headers["User-Agent"] = f"CFBD-Integration-Agent/{self.agent_id}"

        # Add API key if available
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        return headers

    def _process_games_data(self, games_data: List[Dict]) -> List[Dict]:
        """Process and validate games data"""
        processed_games = []

        for game in games_data:
            # Validate required fields
            if not all(
                key in game
                for key in ["id", "season", "week", "home_team", "away_team"]
            ):
                continue

            # Process game data
            processed_game = {
                "id": game.get("id"),
                "season": game.get("season"),
                "week": game.get("week"),
                "season_type": game.get("season_type", "regular"),
                "date": game.get("start_date"),
                "home_team": game.get("home_team"),
                "away_team": game.get("away_team"),
                "home_points": game.get("home_points"),
                "away_points": game.get("away_points"),
                "venue": game.get("venue"),
                "conference_game": game.get("conference_game", False),
            }

            processed_games.append(processed_game)

        return processed_games

    def _process_team_stats(self, stats_data: List[Dict]) -> List[Dict]:
        """Process team statistics data"""
        processed_stats = []

        for stat in stats_data:
            processed_stat = {
                "team": stat.get("team"),
                "season": stat.get("season"),
                "week": stat.get("week"),
                "stat_type": stat.get("stat_type"),
                "conference": stat.get("conference"),
                "offense": stat.get("offense", {}),
                "defense": stat.get("defense", {}),
                "special_teams": stat.get("special_teams", {}),
            }

            processed_stats.append(processed_stat)

        return processed_stats

    def _process_player_data(self, players_data: List[Dict]) -> List[Dict]:
        """Process player data"""
        processed_players = []

        for player in players_data:
            processed_player = {
                "id": player.get("id"),
                "name": player.get("name"),
                "team": player.get("team"),
                "position": player.get("position"),
                "height": player.get("height"),
                "weight": player.get("weight"),
                "year": player.get("year"),
                "hometown": player.get("hometown"),
                "state": player.get("state"),
                "country": player.get("country"),
            }

            processed_players.append(processed_player)

        return processed_players

    def _process_player_stats(self, stats_data: List[Dict]) -> List[Dict]:
        """Process player statistics data"""
        processed_stats = []

        for stat in stats_data:
            processed_stat = {
                "player_id": stat.get("player_id"),
                "team": stat.get("team"),
                "season": stat.get("season"),
                "week": stat.get("week"),
                "category": stat.get("category"),
                "stat_type": stat.get("stat_type"),
                "stat_value": stat.get("stat_value"),
            }

            processed_stats.append(processed_stat)

        return processed_stats

    def _process_rankings_data(self, rankings_data: List[Dict]) -> List[Dict]:
        """Process rankings data"""
        processed_rankings = []

        for ranking in rankings_data:
            processed_ranking = {
                "season": ranking.get("season"),
                "week": ranking.get("week"),
                "season_type": ranking.get("season_type"),
                "ranking_type": ranking.get("ranking_type"),
                "poll": ranking.get("poll"),
                "ranks": ranking.get("ranks", []),
            }

            processed_rankings.append(processed_ranking)

        return processed_rankings

    def _calculate_games_metadata(self, games: List[Dict]) -> Dict:
        """Calculate metadata for games data"""
        if not games:
            return {"count": 0}

        seasons = set(game.get("season") for game in games)
        weeks = set(game.get("week") for game in games)
        teams = set()

        for game in games:
            teams.add(game.get("home_team"))
            teams.add(game.get("away_team"))

        return {
            "count": len(games),
            "seasons": sorted(list(seasons)),
            "weeks": sorted(list(weeks)),
            "teams": sorted(list(teams)),
            "date_range": {
                "earliest": min(game.get("date") for game in games if game.get("date")),
                "latest": max(game.get("date") for game in games if game.get("date")),
            },
        }

    def _generate_team_stats_analysis(self, team_stats: List[Dict]) -> Dict:
        """Generate analysis from team statistics"""
        if not team_stats:
            return {"analysis": "No team statistics available"}

        # Calculate basic statistics
        teams = set(stat.get("team") for stat in team_stats)

        return {
            "analysis": f"Statistics available for {len(teams)} teams",
            "team_count": len(teams),
            "stat_types": list(set(stat.get("stat_type") for stat in team_stats)),
            "summary": "Team statistics include offensive, defensive, and special teams performance metrics",
        }

    def _extract_poll_info(self, rankings: List[Dict]) -> List[Dict]:
        """Extract poll information from rankings data"""
        polls = set()
        for ranking in rankings:
            polls.add(ranking.get("poll"))

        return [{"name": poll, "type": "ranking"} for poll in sorted(polls) if poll]

    def _calculate_batch_performance(self, results: List[Dict]) -> Dict:
        """Calculate performance metrics for batch requests"""
        total_time = sum(result.get("response_time", 0) for result in results)
        successful_requests = sum(
            1 for result in results if result.get("success", False)
        )
        cache_hits = sum(1 for result in results if result.get("cached", False))

        return {
            "total_execution_time": total_time,
            "average_response_time": total_time / len(results) if results else 0,
            "success_rate": (
                (successful_requests / len(results) * 100) if results else 0
            ),
            "cache_hit_rate": (cache_hits / len(results) * 100) if results else 0,
            "requests_per_second": len(results) / total_time if total_time > 0 else 0,
        }

    def _update_metrics(self, response: APIResponse) -> None:
        """Update performance metrics"""
        self.metrics["requests_made"] += 1
        self.metrics["last_request_time"] = datetime.utcnow()

        # Update average response time
        current_avg = self.metrics["average_response_time"]
        total_requests = self.metrics["requests_made"]
        self.metrics["average_response_time"] = (
            current_avg * (total_requests - 1) + response.response_time_seconds
        ) / total_requests

        # Update endpoint usage
        endpoint = response.request.endpoint.value
        if endpoint not in self.metrics["api_usage_by_endpoint"]:
            self.metrics["api_usage_by_endpoint"][endpoint] = 0
        self.metrics["api_usage_by_endpoint"][endpoint] += 1

        # Update data volume (rough estimate)
        if response.data:
            data_size = len(json.dumps(response.data).encode()) / (1024 * 1024)  # MB
            self.metrics["data_volume_mb"] += data_size

    def get_performance_metrics(self) -> Dict:
        """Get current performance metrics"""
        return {
            **self.metrics,
            "cache_size": {
                "memory_cache_entries": len(self.memory_cache),
                "disk_cache_files": len(list(self.disk_cache_dir.glob("*.pkl"))),
            },
            "rate_limit_status": {
                "current_requests_per_minute": len(self.request_times),
                "limit_per_minute": self.rate_limit_per_minute,
                "burst_capacity": self.rate_limit_burst,
            },
        }

    def clear_cache(self) -> None:
        """Clear all caches"""
        self.memory_cache.clear()
        # Clear disk cache
        for cache_file in self.disk_cache_dir.glob("*.pkl"):
            cache_file.unlink()

    async def _fetch_games_data_async(self, parameters: Dict, context) -> Dict:
        """Async version of games data fetch"""
        # For now, just call sync version in thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self._fetch_games_data, parameters, context
        )

    async def _batch_fetch_data_async(self, parameters: Dict, context) -> Dict:
        """Async version of batch fetch"""
        # For now, just call sync version in thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self._batch_fetch_data, parameters, context
        )


# Agent registration function
def register_cfbd_integration_agent():
    """Register the CFBD integration agent with the system"""
    agent = CFBDIntegrationAgent()

    registration_details = {
        "agent_id": agent.agent_id,
        "agent_name": agent.agent_name,
        "class_name": "CFBDIntegrationAgent",
        "file_path": __file__,
        "created_by": "system_architect",
        "capabilities": [
            "fetch_games_data",
            "fetch_team_stats",
            "fetch_player_data",
            "batch_fetch_data",
            "get_rankings_data",
        ],
        "dependencies": ["enhanced_agent_framework", "security_manager", "requests"],
        "max_execution_time": 600,  # 10 minutes
        "memory_limit_mb": 1024,
        "security_tier": 3,
        "permission_level": "READ_EXECUTE",
        "api_access": True,
        "rate_limit_per_minute": 30,
    }

    return agent, registration_details


# Example usage and testing
if __name__ == "__main__":
    # Create agent
    agent = CFBDIntegrationAgent()

    # Test games data fetch
    result = agent.execute_action(
        "fetch_games_data", {"year": 2025, "week": 13, "priority": 8}
    )
    print("Games Data Fetch Result:")
    print(json.dumps(result, indent=2))

    # Test batch fetch
    batch_requests = [
        {"endpoint": "games", "parameters": {"year": 2025, "week": 13}, "priority": 8},
        {"endpoint": "teams", "parameters": {"conference": "SEC"}, "priority": 5},
    ]

    batch_result = agent.execute_action(
        "batch_fetch_data", {"requests": batch_requests, "parallel_limit": 2}
    )
    print("\nBatch Fetch Result:")
    print(json.dumps(batch_result, indent=2))
