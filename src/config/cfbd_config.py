"""
Centralized configuration for CFBD API integration.
This replaces scattered configuration across multiple files.
"""

import os
from dataclasses import dataclass, field
from typing import Optional

try:
    from ..cfbd_client.cfbd_cache_manager import CFBDCacheConfig
except ImportError:
    # Fallback if relative import fails
    from src.cfbd_client.cfbd_cache_manager import CFBDCacheConfig


@dataclass
class CFBDConfig:
    """Centralized configuration for CFBD API integration"""

    # API Configuration
    api_key: Optional[str] = None
    host: str = "https://api.collegefootballdata.com"

    # Rate Limiting
    max_requests_per_second: int = (
        5  # Default to 5 req/sec for free tier safety (300 req/min)
    )
    rate_limit_delay: float = 0.2  # 1/5 = 0.2s for exactly 5 req/sec
    max_retries: int = 3

    # Caching
    cache_config: CFBDCacheConfig = field(default_factory=CFBDCacheConfig)

    # Feature Flags
    enable_metrics: bool = True
    enable_logging: bool = True

    # Transport Preference
    preferred_transport: str = "auto"  # "auto", "graphql", "rest"
    graphql_fallback_to_rest: bool = (
        True  # If GraphQL fails (403/401), fallback to REST
    )
    graphql_disabled: bool = False  # If True, GraphQL features are disabled

    @classmethod
    def from_env(cls) -> "CFBDConfig":
        """Create configuration from environment variables"""
        api_key = os.getenv("CFBD_API_KEY") or os.getenv("CFBD_API_TOKEN")
        # Note: We don't raise here if missing, validation happens in validate() or client usage
        # But the plan says: if not api_key: raise ValueError.
        if not api_key:
            # Allow instantiation without key for testing/mocking if needed,
            # but plan says raise. I will follow plan logic but make it robust.
            # Actually, looking at the plan code:
            # if not api_key: raise ValueError("CFBD_API_KEY or CFBD_API_TOKEN environment variable required")
            pass

        # Determine host
        host_env = os.getenv("CFBD_HOST", "production").lower()
        host_map = {
            "production": "https://api.collegefootballdata.com",
            "next": "https://apinext.collegefootballdata.com",
        }
        host = host_map.get(host_env, host_map["production"])

        # Rate limiting (default 5 req/sec for free tier safety, ~300 req/min)
        max_requests_per_second = int(os.getenv("CFBD_MAX_REQUESTS_PER_SECOND", "5"))
        rate_limit_delay = 1.0 / max_requests_per_second
        max_retries = int(os.getenv("CFBD_MAX_RETRIES", "3"))

        # Caching
        cache_enabled = os.getenv("CFBD_CACHE_ENABLED", "true").lower() != "false"
        cache_config = CFBDCacheConfig(
            enable_cache=cache_enabled,
            cache_ttl_games=int(os.getenv("CFBD_CACHE_TTL_GAMES", "86400")),  # 24 hours
            cache_ttl_stats=int(os.getenv("CFBD_CACHE_TTL_STATS", "3600")),  # 1 hour
            cache_ttl_teams=int(os.getenv("CFBD_CACHE_TTL_TEAMS", "604800")),  # 7 days
            cache_ttl_predictions=int(
                os.getenv("CFBD_CACHE_TTL_PREDICTIONS", "300")
            ),  # 5 minutes
        )

        # Feature flags
        enable_metrics = os.getenv("CFBD_ENABLE_METRICS", "true").lower() != "false"
        enable_logging = os.getenv("CFBD_ENABLE_LOGGING", "true").lower() != "false"

        # Transport preference
        preferred_transport = os.getenv("CFBD_PREFERRED_TRANSPORT", "auto").lower()
        if preferred_transport not in ["auto", "graphql", "rest"]:
            preferred_transport = "auto"

        graphql_fallback_to_rest = (
            os.getenv("CFBD_GRAPHQL_FALLBACK_TO_REST", "true").lower() != "false"
        )

        # GraphQL disabled flag
        graphql_disabled = os.getenv("CFBD_GRAPHQL_DISABLED", "false").lower() == "true"

        if not api_key:
            # The plan says raise error here.
            raise ValueError(
                "CFBD_API_KEY or CFBD_API_TOKEN environment variable required"
            )

        return cls(
            api_key=api_key,
            host=host,
            max_requests_per_second=max_requests_per_second,
            rate_limit_delay=rate_limit_delay,
            max_retries=max_retries,
            cache_config=cache_config,
            enable_metrics=enable_metrics,
            enable_logging=enable_logging,
            preferred_transport=preferred_transport,
            graphql_fallback_to_rest=graphql_fallback_to_rest,
            graphql_disabled=graphql_disabled,
        )

    def validate(self) -> None:
        """Validate configuration"""
        if not self.api_key:
            raise ValueError("API key is required")

        if self.max_requests_per_second <= 0:
            raise ValueError("max_requests_per_second must be positive")

        if self.rate_limit_delay <= 0:
            raise ValueError("rate_limit_delay must be positive")

        if self.max_retries < 0:
            raise ValueError("max_retries must be non-negative")
