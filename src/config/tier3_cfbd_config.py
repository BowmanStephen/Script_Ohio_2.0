"""
Tier 3 optimized CFBD configuration.

Tier 3 Benefits:
- 75,000 API calls/month
- ~2,500 calls/day average
- ~100 calls/hour average
- ~25 requests/second sustainable rate
- GraphQL API access with subscriptions
- All advanced metrics (EPA, PPA, Win Probability, etc.)
- Live scoreboard and play-by-play data
- Weather data
- Weekly model training data downloads
"""

import os
from dataclasses import dataclass, field
from typing import Optional

try:
    from ..cfbd_client.cfbd_cache_manager import CFBDCacheConfig
except ImportError:
    from src.cfbd_client.cfbd_cache_manager import CFBDCacheConfig


@dataclass
class Tier3CFBDConfig:
    """Tier 3 optimized configuration for CFBD API integration"""

    # API Configuration
    api_key: Optional[str] = None
    host: str = "https://api.collegefootballdata.com"

    # Tier 3 Rate Limiting - Optimized for 75k monthly requests
    # Conservative estimate: 75k/30 days = 2.5k/day = 104/hour = 25/sec
    max_requests_per_second: int = 25  # Tier 3 optimized rate
    rate_limit_delay: float = 0.04   # 1/25 = 0.04s for exactly 25 req/sec
    max_retries: int = 3

    # Tier 3 Enhanced Caching - More aggressive for premium features
    cache_config: CFBDCacheConfig = field(default_factory=lambda: CFBDCacheConfig(
        enable_cache=True,
        default_ttl_seconds=900,  # 15 minutes default
        ttl_overrides={
            "games": 43200,           # 12 hours for games (live data changes)
            "stats": 1800,            # 30 minutes for stats (premium data)
            "teams": 604800,          # 7 days for teams (stable)
            "predictions": 300,       # 5 minutes for predictions (live)
            "live_data": 60,          # 1 minute for live data (real-time)
            "premium_metrics": 900,   # 15 minutes for premium metrics
            "ppa_data": 1800,         # 30 minutes for PPA data
            "week_data": 3600,        # 1 hour for weekly data
        }
    ))

    # Feature Flags - All enabled for Tier 3
    enable_metrics: bool = True
    enable_logging: bool = True
    enable_graphql: bool = True
    enable_live_data: bool = True
    enable_premium_metrics: bool = True
    enable_weekly_training: bool = True

    # Tier 3 Transport Preference - GraphQL preferred for efficiency
    preferred_transport: str = "graphql"  # "graphql", "rest", "auto"
    graphql_fallback_to_rest: bool = True
    graphql_disabled: bool = False

    # Tier 3 specific settings
    batch_size: int = 50  # Larger batches for efficiency
    parallel_requests: int = 5  # Limited parallelism for rate limits
    subscription_timeout: int = 300  # GraphQL subscription timeout

    @classmethod
    def from_env(cls) -> "Tier3CFBDConfig":
        """Create Tier 3 configuration from environment variables"""
        api_key = os.getenv("CFBD_API_KEY") or os.getenv("CFBD_API_TOKEN")

        if not api_key:
            raise ValueError("CFBD_API_KEY or CFBD_API_TOKEN environment variable required")

        # Determine host
        host_env = os.getenv("CFBD_HOST", "production").lower()
        host_map = {
            "production": "https://api.collegefootballdata.com",
            "next": "https://apinext.collegefootballdata.com",
        }
        host = host_map.get(host_env, host_map["production"])

        # Tier 3 optimized rate limiting
        # Allow override but default to Tier 3 optimized values
        max_requests_per_second = int(os.getenv("CFBD_MAX_REQUESTS_PER_SECOND", "25"))
        if max_requests_per_second > 30:  # Safety cap
            max_requests_per_second = 25
        rate_limit_delay = 1.0 / max_requests_per_second
        max_retries = int(os.getenv("CFBD_MAX_RETRIES", "3"))

        # Enhanced caching for Tier 3
        cache_enabled = os.getenv("CFBD_CACHE_ENABLED", "true").lower() != "false"
        default_ttl = int(os.getenv("CFBD_CACHE_DEFAULT_TTL", "900"))  # 15 minutes default

        # TTL overrides for different data types (Tier 3 optimized)
        ttl_overrides = {
            "games": int(os.getenv("CFBD_CACHE_TTL_GAMES", "43200")),      # 12 hours
            "stats": int(os.getenv("CFBD_CACHE_TTL_STATS", "1800")),       # 30 minutes
            "teams": int(os.getenv("CFBD_CACHE_TTL_TEAMS", "604800")),     # 7 days
            "predictions": int(os.getenv("CFBD_CACHE_TTL_PREDICTIONS", "300")),  # 5 minutes
            "live_data": int(os.getenv("CFBD_CACHE_TTL_LIVE", "60")),       # 1 minute
            "premium_metrics": int(os.getenv("CFBD_CACHE_TTL_PREMIUM", "900")),  # 15 minutes
            "ppa_data": int(os.getenv("CFBD_CACHE_TTL_PPA", "1800")),       # 30 minutes
            "week_data": int(os.getenv("CFBD_CACHE_TTL_WEEKLY", "3600")),    # 1 hour
        }

        cache_config = CFBDCacheConfig(
            enable_cache=cache_enabled,
            default_ttl_seconds=default_ttl,
            ttl_overrides=ttl_overrides
        )

        # Feature flags (all enabled by default for Tier 3)
        enable_metrics = os.getenv("CFBD_ENABLE_METRICS", "true").lower() != "false"
        enable_logging = os.getenv("CFBD_ENABLE_LOGGING", "true").lower() != "false"
        enable_graphql = os.getenv("CFBD_ENABLE_GRAPHQL", "true").lower() != "false"
        enable_live_data = os.getenv("CFBD_ENABLE_LIVE_DATA", "true").lower() != "false"
        enable_premium_metrics = os.getenv("CFBD_ENABLE_PREMIUM", "true").lower() != "false"
        enable_weekly_training = os.getenv("CFBD_ENABLE_WEEKLY_TRAINING", "true").lower() != "false"

        # Transport preference for Tier 3
        preferred_transport = os.getenv("CFBD_PREFERRED_TRANSPORT", "graphql").lower()
        if preferred_transport not in ["graphql", "rest", "auto"]:
            preferred_transport = "graphql"

        graphql_fallback_to_rest = os.getenv("CFBD_GRAPHQL_FALLBACK_TO_REST", "true").lower() != "false"
        graphql_disabled = os.getenv("CFBD_GRAPHQL_DISABLED", "false").lower() == "true"

        # Tier 3 performance settings
        batch_size = int(os.getenv("CFBD_BATCH_SIZE", "50"))
        parallel_requests = int(os.getenv("CFBD_PARALLEL_REQUESTS", "5"))
        subscription_timeout = int(os.getenv("CFBD_SUBSCRIPTION_TIMEOUT", "300"))

        return cls(
            api_key=api_key,
            host=host,
            max_requests_per_second=max_requests_per_second,
            rate_limit_delay=rate_limit_delay,
            max_retries=max_retries,
            cache_config=cache_config,
            enable_metrics=enable_metrics,
            enable_logging=enable_logging,
            enable_graphql=enable_graphql,
            enable_live_data=enable_live_data,
            enable_premium_metrics=enable_premium_metrics,
            enable_weekly_training=enable_weekly_training,
            preferred_transport=preferred_transport,
            graphql_fallback_to_rest=graphql_fallback_to_rest,
            graphql_disabled=graphql_disabled,
            batch_size=batch_size,
            parallel_requests=parallel_requests,
            subscription_timeout=subscription_timeout,
        )

    def get_monthly_quota_info(self) -> dict:
        """Get Tier 3 quota information"""
        return {
            "tier": "tier3",
            "monthly_quota": 75000,
            "daily_average": 2500,
            "hourly_average": 104,
            "max_sustainable_rps": 25,
            "features": [
                "GraphQL API with subscriptions",
                "All advanced metrics (EPA, PPA, Win Probability)",
                "Live scoreboard and play-by-play",
                "Weather data",
                "Weekly model training downloads",
                "Betting lines and historical data"
            ]
        }

    def validate(self) -> None:
        """Validate Tier 3 configuration"""
        if not self.api_key:
            raise ValueError("API key is required for Tier 3")

        if self.max_requests_per_second <= 0 or self.max_requests_per_second > 30:
            raise ValueError("max_requests_per_second must be between 1 and 30 for Tier 3")

        if self.rate_limit_delay <= 0:
            raise ValueError("rate_limit_delay must be positive")

        if self.max_retries < 0:
            raise ValueError("max_retries must be non-negative")

        if self.batch_size <= 0 or self.batch_size > 100:
            raise ValueError("batch_size must be between 1 and 100")

        if self.parallel_requests <= 0 or self.parallel_requests > 10:
            raise ValueError("parallel_requests must be between 1 and 10")