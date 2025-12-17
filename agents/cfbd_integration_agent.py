"""Agent that centralizes CFBD data access for other workflows.

This agent provides unified access to CFBD data through both REST and GraphQL APIs.
GraphQL capabilities are automatically registered when the gql library is installed
and CFBD_API_KEY is configured. REST capabilities are always available as fallback.

GraphQL Features (requires Patreon Tier 3+ subscription):
- graphql_scoreboard: Fetch scoreboard data via GraphQL API (<1.5s execution time)
- graphql_recruiting: Fetch recruiting data via GraphQL API (<2.0s execution time)

REST Features (always available):
- team_snapshot: Return normalized CFBD snapshot for a single team (<1.0s execution time)
- live_scoreboard: Return the latest live scoreboard events (<0.2s execution time)

Capabilities are automatically registered based on availability:
- REST capabilities: Always available
- GraphQL capabilities: Only available when gql library is installed and CFBD_API_KEY is set

Backward Compatibility:
- All existing REST workflows continue to work regardless of GraphQL availability
- GraphQL capabilities are additive and don't break existing functionality

Example Usage:
    >>> agent = CFBDIntegrationAgent(agent_id="cfbd_001")
    >>> # REST (always available)
    >>> result = agent._execute_action(
    ...     "team_snapshot",
    ...     {"team": "Ohio State", "season": 2025},
    ...     {"user_id": "user_001"}
    ... )
    >>> # GraphQL (if available)
    >>> result = agent._execute_action(
    ...     "graphql_scoreboard",
    ...     {"season": 2025, "week": 12},
    ...     {"user_id": "user_001"}
    ... )
"""
from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from agents.core.agent_framework import BaseAgent, AgentCapability, PermissionLevel
from src.cfbd_client.unified_client import UnifiedCFBDClient

# Try to import GraphQL client (requires Patreon Tier 3+ access)
try:
    from src.data_sources.cfbd_graphql import CFBDGraphQLClient
    GRAPHQL_AVAILABLE = True
except ImportError:
    GRAPHQL_AVAILABLE = False
    CFBDGraphQLClient = None  # type: ignore

logger = logging.getLogger(__name__)

class CFBDIntegrationAgent(BaseAgent):
    """Provides normalized CFBD datasets and live scoreboard snapshots.
    
    This agent centralizes CFBD data access for the Script Ohio 2.0 platform,
    supporting both REST and GraphQL APIs. GraphQL capabilities are automatically
    registered when available, with graceful degradation to REST when not available.
    """

    def __init__(
        self,
        agent_id: str,
        cfbd_client: Optional[UnifiedCFBDClient] = None,
        live_feed_provider: Optional[Any] = None,
        cache_provider: Optional[Any] = None,
        graphql_client: Optional[Any] = None,
        tool_loader=None,
    ) -> None:
        # Initialize GraphQL client BEFORE super().__init__() because
        # _define_capabilities() is called during super().__init__() and needs _graphql_client
        self._graphql_client = graphql_client
        if GRAPHQL_AVAILABLE and self._graphql_client is None:
            # Check if GraphQL is explicitly disabled
            if os.getenv("CFBD_GRAPHQL_DISABLED", "false").lower() == "true":
                logger.info("GraphQL explicitly disabled via CFBD_GRAPHQL_DISABLED - skipping initialization")
                self._graphql_client = None
            else:
                try:
                    api_key = os.getenv("CFBD_API_KEY") or os.getenv("CFBD_API_TOKEN")
                    if api_key:
                        self._graphql_client = CFBDGraphQLClient(api_key=api_key)
                        logger.info("GraphQL client initialized successfully")
                    else:
                        logger.warning("CFBD_API_KEY or CFBD_API_TOKEN not set - GraphQL features disabled")
                        self._graphql_client = None
                except Exception as e:
                    logger.warning(f"Failed to initialize GraphQL client: {e}")
                    self._graphql_client = None
        elif not GRAPHQL_AVAILABLE:
            self._graphql_client = None
        
        super().__init__(
            agent_id=agent_id,
            name="CFBD Integration Agent",
            permission_level=PermissionLevel.READ_EXECUTE,
            tool_loader=tool_loader,
        )
        self.client = cfbd_client or UnifiedCFBDClient()
        self.live_feed_provider = live_feed_provider
        self.cache = cache_provider

    def _define_capabilities(self) -> List[AgentCapability]:
        capabilities = [
            AgentCapability(
                name="team_snapshot",
                description="Return normalized CFBD snapshot for a single team",
                permission_required=PermissionLevel.READ_EXECUTE,
                tools_required=["cfbd_client"],
                data_access=["CFBD REST"],
                execution_time_estimate=1.0,
            ),
            AgentCapability(
                name="live_scoreboard",
                description="Return the latest live scoreboard events (REST-based)",
                permission_required=PermissionLevel.READ_EXECUTE,
                tools_required=["cfbd_rest_client"],
                data_access=["CFBD REST"],
                execution_time_estimate=0.2,
            ),
        ]
        
        # Add GraphQL capabilities if available
        # Use getattr to safely access _graphql_client in case it wasn't set yet
        graphql_client = getattr(self, '_graphql_client', None)
        if GRAPHQL_AVAILABLE and graphql_client is not None:
            capabilities.extend([
                AgentCapability(
                    name="graphql_scoreboard",
                    description="Fetch scoreboard data via GraphQL API (requires Patreon Tier 3+ access). Falls back to REST if GraphQL unavailable.",
                    permission_required=PermissionLevel.READ_EXECUTE,
                    tools_required=["cfbd_graphql_client", "gql"],
                    data_access=["graphql.collegefootballdata.com"],
                    execution_time_estimate=1.5,
                ),
                AgentCapability(
                    name="graphql_recruiting",
                    description="Fetch recruiting data via GraphQL API (requires Patreon Tier 3+ access). Falls back to REST if GraphQL unavailable.",
                    permission_required=PermissionLevel.READ_EXECUTE,
                    tools_required=["cfbd_graphql_client", "gql"],
                    data_access=["graphql.collegefootballdata.com"],
                    execution_time_estimate=2.0,
                ),
                AgentCapability(
                    name="graphql_plays",
                    description="Fetch play-by-play data via GraphQL API (requires Patreon Tier 3+ access). Falls back to REST if GraphQL unavailable.",
                    permission_required=PermissionLevel.READ_EXECUTE,
                    tools_required=["cfbd_graphql_client", "gql"],
                    data_access=["graphql.collegefootballdata.com"],
                    execution_time_estimate=2.5,
                ),
                AgentCapability(
                    name="graphql_betting_lines",
                    description="Fetch betting lines via GraphQL API (requires Patreon Tier 3+ access). Falls back to REST if GraphQL unavailable.",
                    permission_required=PermissionLevel.READ_EXECUTE,
                    tools_required=["cfbd_graphql_client", "gql"],
                    data_access=["graphql.collegefootballdata.com"],
                    execution_time_estimate=1.5,
                ),
            ])
        
        return capabilities

    def _execute_action(
        self,
        action: str,
        parameters: Dict[str, Any],
        user_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        if action == "team_snapshot":
            return self._team_snapshot(parameters)
        if action == "live_scoreboard":
            return self._live_scoreboard(parameters)
        if action == "graphql_scoreboard":
            return self._handle_graphql_scoreboard(parameters)
        if action == "graphql_recruiting":
            return self._handle_graphql_recruiting(parameters)
        if action == "graphql_plays":
            return self._handle_graphql_plays(parameters)
        if action == "graphql_betting_lines":
            return self._handle_graphql_betting_lines(parameters)
        raise ValueError(f"Unknown action {action}")

    def _team_snapshot(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        team = parameters.get("team")
        if not team:
            raise ValueError("team parameter required")
            
        season = int(parameters.get("season", datetime.utcnow().year))
        week = parameters.get("week")
        
        cache_key = self._build_cache_key(
            "team_snapshot",
            team=team.replace(" ", "_").lower(),
            season=season,
            week=week or "latest",
        )

        if self.cache:
            cached_snapshot = self.cache.get(cache_key)
            if cached_snapshot:
                return {
                    "status": "success",
                    "team": team,
                    "season": season,
                    "week": week,
                    "snapshot": cached_snapshot,
                    "cached": True,
                }

        # Gather data using UnifiedCFBDClient
        # 1. Recent games
        games = self.client.get_games(year=season, week=week, team=team)
        games = sorted(games, key=lambda x: x.get('week', 0), reverse=True)[:3]

        # 2. Ratings
        all_ratings = self.client.get_ratings(year=season, week=week)
        ratings = [r for r in all_ratings if r.get('team') == team]

        # 3. Stats
        stats = self.client.get_stats(year=season, team=team)

        # 4. Talent
        talent = self.client.get_team_talent(year=season)
        team_talent = [t for t in talent if t.get('school') == team]

        snapshot = {
            "team": team,
            "season": season,
            "week": week,
            "recent_games": games,
            "ratings": ratings,
            "stats": stats,
            "talent": team_talent
        }

        if self.cache:
            self.cache.put(cache_key, snapshot, ttl_seconds=300, tags=["cfbd", team])

        return {
            "status": "success",
            "team": team,
            "season": season,
            "week": week,
            "snapshot": snapshot,
        }

    def _live_scoreboard(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        if not self.live_feed_provider:
            return {"status": "unavailable", "events": []}
        limit = int(parameters.get("limit", 5))
        cache_key = self._build_cache_key("live_scoreboard", limit=limit)

        if self.cache:
            cached_events = self.cache.get(cache_key)
            if cached_events:
                return {"status": "success", "events": cached_events, "cached": True}

        events = self.live_feed_provider.latest_events(limit=limit)
        if self.cache:
            self.cache.put(cache_key, events, ttl_seconds=30, tags=["cfbd", "live"])
        return {"status": "success", "events": events}

    def _handle_graphql_scoreboard(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle GraphQL scoreboard request.
        
        Args:
            parameters: Must contain 'season' (int) and optionally 'week' (int)
        
        Returns:
            Dictionary with games data from GraphQL API
        """
        if not GRAPHQL_AVAILABLE or self._graphql_client is None:
            return {
                "status": "error",
                "error": "GraphQL client not available. Ensure CFBD_API_KEY is set and gql library is installed.",
                "games": [],
            }
        
        # Validate required parameters
        season = parameters.get("season")
        if season is None:
            raise ValueError("Missing required parameter: season")
        
        # Validate types BEFORE conversion
        if not isinstance(season, int):
            raise ValueError("Invalid parameter type: season must be an integer")
        
        week = parameters.get("week")
        if week is not None and not isinstance(week, int):
            raise ValueError("Invalid parameter type: week must be an integer")
        
        # Convert to int (already validated as int)
        season = int(season)
        if week is not None:
            week = int(week)
        
        # Build cache key
        cache_key = self._build_cache_key(
            "graphql_scoreboard",
            season=season,
            week=week or "all",
        )
        
        # Check cache
        if self.cache:
            cached_data = self.cache.get(cache_key)
            if cached_data:
                logger.debug(f"Cache hit for GraphQL scoreboard: season={season}, week={week}")
                return {
                    "status": "success",
                    "season": season,
                    "week": week,
                    "games": cached_data.get("games", []),
                    "cached": True,
                    "data_source": "GraphQL API (cached)",
                }
        
        # Fetch from GraphQL API
        try:
            result = self._graphql_client.get_scoreboard(season=season, week=week)
            games = result.get("game", [])
            
            logger.info(f"Fetched {len(games)} games via GraphQL for season={season}, week={week}")
            
            # Cache the result
            if self.cache and games:
                self.cache.put(
                    cache_key,
                    {"games": games},
                    ttl_seconds=3600,  # 1 hour cache for scoreboard data
                    tags=["cfbd", "graphql", "scoreboard"],
                )
            
            return {
                "status": "success",
                "season": season,
                "week": week,
                "games": games,
                "cached": False,
                "data_source": "GraphQL API",
            }
            
        except Exception as e:
            error_msg = str(e).lower()
            is_auth_error = any(keyword in error_msg for keyword in ["401", "403", "unauthorized", "forbidden", "tier 3"])
            
            # Check if we should fallback to REST
            should_fallback = False
            if hasattr(self, 'client') and self.client:
                # Check config for fallback preference
                config = getattr(self.client, 'config', None)
                if config and hasattr(config, 'graphql_fallback_to_rest'):
                    should_fallback = config.graphql_fallback_to_rest
                else:
                    # Check environment variable
                    fallback_env = os.getenv("CFBD_GRAPHQL_FALLBACK_TO_REST", "true").lower()
                    should_fallback = fallback_env != "false"
            
            if is_auth_error:
                if should_fallback:
                    logger.warning(f"GraphQL access forbidden (Tier 3+ required), falling back to REST: {e}")
                    # Fallback to REST
                    try:
                        rest_games = self.client.get_games(year=season, week=week) if self.client else []
                        return {
                            "status": "success",
                            "season": season,
                            "week": week,
                            "games": rest_games or [],
                            "cached": False,
                            "data_source": "REST API (GraphQL fallback)",
                            "fallback_reason": "GraphQL requires Patreon Tier 3+",
                        }
                    except Exception as rest_error:
                        logger.error(f"REST fallback also failed: {rest_error}")
                        return {
                            "status": "error",
                            "error": f"GraphQL failed ({str(e)}) and REST fallback failed ({str(rest_error)})",
                            "games": [],
                        }
                else:
                    # Fallback disabled - fail loudly
                    logger.error(f"GraphQL access forbidden (Tier 3+ required) and fallback disabled: {e}")
                    return {
                        "status": "error",
                        "error": f"GraphQL requires Patreon Tier 3+ access. Set CFBD_GRAPHQL_FALLBACK_TO_REST=true to enable REST fallback.",
                        "games": [],
                        "requires_tier": "Patreon Tier 3+",
                    }
            else:
                logger.error(f"GraphQL scoreboard request failed: {e}")
                return {
                    "status": "error",
                    "error": f"GraphQL scoreboard request failed: {str(e)}",
                    "games": [],
                }

    def _handle_graphql_recruiting(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle GraphQL recruiting request.
        
        Args:
            parameters: Must contain 'year' (int) and optionally 'school' (str) and 'limit' (int)
        
        Returns:
            Dictionary with recruiting data from GraphQL API
        """
        if not GRAPHQL_AVAILABLE or self._graphql_client is None:
            return {
                "status": "error",
                "error": "GraphQL client not available. Ensure CFBD_API_KEY is set and gql library is installed.",
                "recruits": [],
            }
        
        # Validate required parameters
        year = parameters.get("year") or parameters.get("season")  # Support both 'year' and 'season'
        if year is None:
            raise ValueError("Missing required parameter: year (or season)")
        
        # Validate types BEFORE conversion
        if not isinstance(year, int):
            raise ValueError("Invalid parameter type: year must be an integer")
        
        limit = parameters.get("limit", 25)
        if limit is not None and not isinstance(limit, int):
            raise ValueError("Invalid parameter type: limit must be an integer")
        
        school = parameters.get("school") or parameters.get("team")  # Support both 'school' and 'team'
        
        # Convert to int (already validated as int)
        year = int(year)
        if limit is not None:
            limit = int(limit)
        else:
            limit = 25
        
        # Build cache key
        cache_key = self._build_cache_key(
            "graphql_recruiting",
            year=year,
            school=school or "all",
            limit=limit,
        )
        
        # Check cache
        if self.cache:
            cached_data = self.cache.get(cache_key)
            if cached_data:
                logger.debug(f"Cache hit for GraphQL recruiting: year={year}, school={school}")
                return {
                    "status": "success",
                    "year": year,
                    "school": school,
                    "recruits": cached_data.get("recruits", []),
                    "cached": True,
                    "data_source": "GraphQL API (cached)",
                }
        
        # Fetch from GraphQL API
        try:
            result = self._graphql_client.get_recruits(season=year, team=school, limit=limit)
            recruits = result.get("recruit", [])
            
            logger.info(f"Fetched {len(recruits)} recruits via GraphQL for year={year}, school={school}")
            
            # Cache the result
            if self.cache and recruits:
                self.cache.put(
                    cache_key,
                    {"recruits": recruits},
                    ttl_seconds=86400,  # 24 hour cache for recruiting data (relatively stable)
                    tags=["cfbd", "graphql", "recruiting"],
                )
            
            return {
                "status": "success",
                "year": year,
                "school": school,
                "recruits": recruits,
                "cached": False,
                "data_source": "GraphQL API",
            }
            
        except Exception as e:
            logger.error(f"GraphQL recruiting request failed: {e}")
            return {
                "status": "error",
                "error": f"GraphQL recruiting request failed: {str(e)}",
                "recruits": [],
            }
    
    def _handle_graphql_plays(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle GraphQL plays request.
        
        Args:
            parameters: Must contain 'season' (int) and optionally 'week' (int) and 'game_id' (int)
        
        Returns:
            Dictionary with play-by-play data from GraphQL API
        """
        if not GRAPHQL_AVAILABLE or self._graphql_client is None:
            # Fallback to REST
            if hasattr(self, 'client') and self.client:
                try:
                    season = int(parameters.get("season", parameters.get("year", datetime.utcnow().year)))
                    week = parameters.get("week")
                    team = parameters.get("team")
                    plays = self.client.get_plays(year=season, week=week, team=team)
                    return {
                        "status": "success",
                        "season": season,
                        "week": week,
                        "plays": plays,
                        "cached": False,
                        "data_source": "REST API (GraphQL unavailable)",
                    }
                except Exception as e:
                    logger.error(f"REST fallback for plays failed: {e}")
            
            return {
                "status": "error",
                "error": "GraphQL client not available. Falling back to REST.",
                "plays": [],
            }
        
        season = int(parameters.get("season", parameters.get("year", datetime.utcnow().year)))
        week = parameters.get("week")
        game_id = parameters.get("game_id")
        
        cache_key = self._build_cache_key(
            "graphql_plays",
            season=season,
            week=week or "all",
            game_id=game_id or "all",
        )
        
        if self.cache:
            cached_data = self.cache.get(cache_key)
            if cached_data:
                return {
                    "status": "success",
                    "season": season,
                    "week": week,
                    "plays": cached_data.get("plays", []),
                    "cached": True,
                    "data_source": "GraphQL API (cached)",
                }
        
        try:
            result = self._graphql_client.get_plays(season=season, week=week, game_id=game_id)
            plays = result.get("play", [])
            
            if self.cache and plays:
                self.cache.put(
                    cache_key,
                    {"plays": plays},
                    ttl_seconds=3600,
                    tags=["cfbd", "graphql", "plays"],
                )
            
            return {
                "status": "success",
                "season": season,
                "week": week,
                "plays": plays,
                "cached": False,
                "data_source": "GraphQL API",
            }
        except Exception as e:
            # Fallback to REST
            if hasattr(self, 'client') and self.client:
                try:
                    plays = self.client.get_plays(year=season, week=week)
                    return {
                        "status": "success",
                        "season": season,
                        "week": week,
                        "plays": plays,
                        "cached": False,
                        "data_source": "REST API (GraphQL fallback)",
                        "fallback_reason": str(e),
                    }
                except Exception as rest_error:
                    logger.error(f"REST fallback for plays failed: {rest_error}")
            
            return {
                "status": "error",
                "error": f"GraphQL plays request failed: {str(e)}",
                "plays": [],
            }
    
    def _handle_graphql_betting_lines(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle GraphQL betting lines request.
        
        Args:
            parameters: Must contain 'season' (int) and optionally 'week' (int)
        
        Returns:
            Dictionary with betting lines data from GraphQL API
        """
        if not GRAPHQL_AVAILABLE or self._graphql_client is None:
            # Fallback to REST
            if hasattr(self, 'client') and self.client:
                try:
                    season = int(parameters.get("season", parameters.get("year", datetime.utcnow().year)))
                    week = parameters.get("week")
                    if week:
                        lines = self.client.get_lines(year=season, week=week)
                    else:
                        lines = []
                    return {
                        "status": "success",
                        "season": season,
                        "week": week,
                        "lines": lines,
                        "cached": False,
                        "data_source": "REST API (GraphQL unavailable)",
                    }
                except Exception as e:
                    logger.error(f"REST fallback for betting lines failed: {e}")
            
            return {
                "status": "error",
                "error": "GraphQL client not available. Falling back to REST.",
                "lines": [],
            }
        
        season = int(parameters.get("season", parameters.get("year", datetime.utcnow().year)))
        week = parameters.get("week")
        
        cache_key = self._build_cache_key(
            "graphql_betting_lines",
            season=season,
            week=week or "all",
        )
        
        if self.cache:
            cached_data = self.cache.get(cache_key)
            if cached_data:
                return {
                    "status": "success",
                    "season": season,
                    "week": week,
                    "lines": cached_data.get("lines", []),
                    "cached": True,
                    "data_source": "GraphQL API (cached)",
                }
        
        try:
            result = self._graphql_client.get_betting_lines(season=season, week=week)
            lines = result.get("bettingLine", [])
            
            if self.cache and lines:
                self.cache.put(
                    cache_key,
                    {"lines": lines},
                    ttl_seconds=1800,  # 30 min cache for betting lines
                    tags=["cfbd", "graphql", "betting"],
                )
            
            return {
                "status": "success",
                "season": season,
                "week": week,
                "lines": lines,
                "cached": False,
                "data_source": "GraphQL API",
            }
        except Exception as e:
            # Fallback to REST
            if hasattr(self, 'client') and self.client and week:
                try:
                    lines = self.client.get_lines(year=season, week=week)
                    return {
                        "status": "success",
                        "season": season,
                        "week": week,
                        "lines": lines,
                        "cached": False,
                        "data_source": "REST API (GraphQL fallback)",
                        "fallback_reason": str(e),
                    }
                except Exception as rest_error:
                    logger.error(f"REST fallback for betting lines failed: {rest_error}")
            
            return {
                "status": "error",
                "error": f"GraphQL betting lines request failed: {str(e)}",
                "lines": [],
            }

    def _build_cache_key(self, prefix: str, **parts: Any) -> str:
        ordered = "_".join(f"{key}:{parts[key]}" for key in sorted(parts))
        return f"{prefix}:{ordered}"


__all__ = ["CFBDIntegrationAgent"]
