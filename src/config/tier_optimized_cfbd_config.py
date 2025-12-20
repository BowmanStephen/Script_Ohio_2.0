"""
Tier-Optimized CFBD Configuration for Enhanced Performance

This module provides optimized configurations for different CFBD API tiers,
allowing users to maximize performance based on their subscription level.

Tier Capabilities:
- Free/Tier 1: 5-6 req/sec, basic REST endpoints
- Tier 2: 10-15 req/sec, advanced player metrics, transfer portal
- Tier 3: 30 req/sec, GraphQL API, NFL draft data, WEPA analytics
- Tier 4+: 60+ req/sec, premium features, priority access
"""

import os
from dataclasses import dataclass
from typing import Any, Dict

from .cfbd_config import CFBDCacheConfig


@dataclass
class TierConfig:
    """Configuration for specific CFBD API tier"""

    # Tier identification
    tier_name: str
    tier_number: int

    # Rate limiting
    max_requests_per_second: int
    rate_limit_delay: float
    burst_capacity: int

    # Features available
    has_graphql: bool
    has_transfer_portal: bool
    has_nfl_draft: bool
    has_wepa_analytics: bool
    has_advanced_metrics: bool

    # Performance optimizations
    cache_ttl_multiplier: float
    enable_batch_requests: bool
    max_concurrent_requests: int

    # GraphQL specific
    graphql_complexity_limit: int
    enable_subscriptions: bool

    @classmethod
    def from_tier_number(cls, tier_number: int) -> "TierConfig":
        """Create tier config from tier number"""
        tier_configs = {
            1: cls(
                tier_name="Free/Tier 1",
                tier_number=1,
                max_requests_per_second=5,
                rate_limit_delay=0.2,
                burst_capacity=10,
                has_graphql=False,
                has_transfer_portal=False,
                has_nfl_draft=False,
                has_wepa_analytics=False,
                has_advanced_metrics=False,
                cache_ttl_multiplier=1.0,
                enable_batch_requests=False,
                max_concurrent_requests=1,
                graphql_complexity_limit=0,
                enable_subscriptions=False,
            ),
            2: cls(
                tier_name="Tier 2",
                tier_number=2,
                max_requests_per_second=15,
                rate_limit_delay=0.067,  # 1/15
                burst_capacity=25,
                has_graphql=False,
                has_transfer_portal=True,
                has_nfl_draft=False,
                has_wepa_analytics=False,
                has_advanced_metrics=True,
                cache_ttl_multiplier=1.2,
                enable_batch_requests=True,
                max_concurrent_requests=2,
                graphql_complexity_limit=0,
                enable_subscriptions=False,
            ),
            3: cls(
                tier_name="Tier 3",
                tier_number=3,
                max_requests_per_second=30,
                rate_limit_delay=0.033,  # 1/30
                burst_capacity=50,
                has_graphql=True,
                has_transfer_portal=True,
                has_nfl_draft=True,
                has_wepa_analytics=True,
                has_advanced_metrics=True,
                cache_ttl_multiplier=1.5,
                enable_batch_requests=True,
                max_concurrent_requests=3,
                graphql_complexity_limit=1000,
                enable_subscriptions=True,
            ),
            4: cls(
                tier_name="Tier 4",
                tier_number=4,
                max_requests_per_second=60,
                rate_limit_delay=0.017,  # 1/60
                burst_capacity=100,
                has_graphql=True,
                has_transfer_portal=True,
                has_nfl_draft=True,
                has_wepa_analytics=True,
                has_advanced_metrics=True,
                cache_ttl_multiplier=2.0,
                enable_batch_requests=True,
                max_concurrent_requests=5,
                graphql_complexity_limit=2000,
                enable_subscriptions=True,
            ),
            5: cls(
                tier_name="Tier 5",
                tier_number=5,
                max_requests_per_second=90,
                rate_limit_delay=0.011,  # 1/90
                burst_capacity=150,
                has_graphql=True,
                has_transfer_portal=True,
                has_nfl_draft=True,
                has_wepa_analytics=True,
                has_advanced_metrics=True,
                cache_ttl_multiplier=2.5,
                enable_batch_requests=True,
                max_concurrent_requests=7,
                graphql_complexity_limit=3000,
                enable_subscriptions=True,
            ),
            6: cls(
                tier_name="Tier 6",
                tier_number=6,
                max_requests_per_second=120,
                rate_limit_delay=0.008,  # 1/120
                burst_capacity=200,
                has_graphql=True,
                has_transfer_portal=True,
                has_nfl_draft=True,
                has_wepa_analytics=True,
                has_advanced_metrics=True,
                cache_ttl_multiplier=3.0,
                enable_batch_requests=True,
                max_concurrent_requests=10,
                graphql_complexity_limit=5000,
                enable_subscriptions=True,
            ),
        }

        return tier_configs.get(tier_number, tier_configs[1])


class TierOptimizedCFBDConfig:
    """
    Tier-optimized CFBD configuration that maximizes performance based on subscription tier.

    Automatically detects optimal settings and provides tier-specific optimizations.
    """

    def __init__(self, tier_number: int = None, api_key: str = None):
        """
        Initialize tier-optimized configuration.

        Args:
            tier_number: CFBD API tier number (1-6). If None, will attempt to auto-detect.
            api_key: CFBD API key. If None, will use environment variable.
        """
        self.api_key = api_key or os.getenv("CFBD_API_KEY")

        if tier_number:
            self.tier = TierConfig.from_tier_number(tier_number)
        else:
            self.tier = self._detect_optimal_tier()

        # Create optimized cache config
        self.cache_config = self._create_optimized_cache_config()

        # Performance settings
        self.request_timeout = 30
        self.enable_compression = True
        self.enable_metrics = True

    def _detect_optimal_tier(self) -> TierConfig:
        """
        Auto-detect optimal tier by testing API capabilities.

        This is a conservative approach that starts with Tier 1 and escalates
        as capabilities are confirmed.
        """
        import requests

        if not self.api_key:
            raise ValueError("API key required for tier detection")

        headers = {"Authorization": f"Bearer {self.api_key}"}

        # Test for basic access (all tiers)
        try:
            response = requests.get(
                "https://api.collegefootballdata.com/games",
                params={"year": 2025, "week": 1},
                headers=headers,
                timeout=10,
            )
            if response.status_code == 200:
                base_tier = 1
            else:
                raise ValueError("Basic API access failed")
        except Exception:
            raise ValueError("Unable to test API access")

        # Test for Tier 2+ features (transfer portal, player usage)
        try:
            response = requests.get(
                "https://api.collegefootballdata.com/player/usage",
                params={"year": 2025},
                headers=headers,
                timeout=10,
            )
            if response.status_code == 200:
                base_tier = max(base_tier, 2)
        except:
            pass

        # Test for Tier 3+ features (NFL draft, WEPA)
        try:
            response = requests.get(
                "https://api.collegefootballdata.com/draft/picks",
                params={"year": 2024},
                headers=headers,
                timeout=10,
            )
            if response.status_code == 200:
                base_tier = max(base_tier, 3)
        except:
            pass

        # Test for GraphQL (Tier 3+)
        try:
            # Simple GraphQL test
            graphql_query = """
            query {
                games(year: 2025, week: 1) {
                    id
                    homeTeam
                    awayTeam
                }
            }
            """
            response = requests.post(
                "https://api.collegefootballdata.com/graphql",
                json={"query": graphql_query},
                headers=headers,
                timeout=10,
            )
            if response.status_code == 200:
                base_tier = max(base_tier, 3)
        except:
            pass

        # Use conservative tier selection
        detected_tier = min(base_tier, 3)  # Cap at Tier 3 for safety

        print(f"🔍 Detected CFBD Tier: {detected_tier}")
        return TierConfig.from_tier_number(detected_tier)

    def _create_optimized_cache_config(self) -> CFBDCacheConfig:
        """Create cache configuration optimized for the tier"""
        base_ttl = {
            "games": 86400,  # 24 hours
            "stats": 3600,  # 1 hour
            "teams": 604800,  # 7 days
            "predictions": 300,  # 5 minutes
        }

        # Apply tier multiplier
        optimized_ttl = {
            key: int(value * self.tier.cache_ttl_multiplier)
            for key, value in base_ttl.items()
        }

        return CFBDCacheConfig(
            enable_cache=True,
            cache_ttl_games=optimized_ttl["games"],
            cache_ttl_stats=optimized_ttl["stats"],
            cache_ttl_teams=optimized_ttl["teams"],
            cache_ttl_predictions=optimized_ttl["predictions"],
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            "tier": {
                "name": self.tier.tier_name,
                "number": self.tier.tier_number,
                "max_requests_per_second": self.tier.max_requests_per_second,
                "rate_limit_delay": self.tier.rate_limit_delay,
                "burst_capacity": self.tier.burst_capacity,
            },
            "features": {
                "graphql": self.tier.has_graphql,
                "transfer_portal": self.tier.has_transfer_portal,
                "nfl_draft": self.tier.has_nfl_draft,
                "wepa_analytics": self.tier.has_wepa_analytics,
                "advanced_metrics": self.tier.has_advanced_metrics,
            },
            "performance": {
                "cache_ttl_multiplier": self.tier.cache_ttl_multiplier,
                "enable_batch_requests": self.tier.enable_batch_requests,
                "max_concurrent_requests": self.tier.max_concurrent_requests,
                "enable_compression": self.enable_compression,
                "request_timeout": self.request_timeout,
            },
            "graphql": {
                "complexity_limit": self.tier.graphql_complexity_limit,
                "enable_subscriptions": self.tier.enable_subscriptions,
            },
        }

    def get_feature_summary(self) -> str:
        """Get human-readable summary of available features"""
        features = []
        if self.tier.has_graphql:
            features.append("GraphQL API")
        if self.tier.has_transfer_portal:
            features.append("Transfer Portal")
        if self.tier.has_nfl_draft:
            features.append("NFL Draft Data")
        if self.tier.has_wepa_analytics:
            features.append("WEPA Analytics")
        if self.tier.has_advanced_metrics:
            features.append("Advanced Metrics")

        return f"{self.tier.tier_name}: {', '.join(features)} ({self.tier.max_requests_per_second} req/sec)"


# Pre-configured instances for common use cases
FREE_TIER_CONFIG = TierOptimizedCFBDConfig(tier_number=1)
TIER_2_CONFIG = TierOptimizedCFBDConfig(tier_number=2)
TIER_3_CONFIG = TierOptimizedCFBDConfig(tier_number=3)
TIER_4_CONFIG = TierOptimizedCFBDConfig(tier_number=4)


def get_optimized_config() -> TierOptimizedCFBDConfig:
    """
    Get automatically optimized configuration based on current API key.

    This is the recommended way to create CFBD configurations for production use.
    """
    return TierOptimizedCFBDConfig()


def create_tier_config(
    tier_number: int, api_key: str = None
) -> TierOptimizedCFBDConfig:
    """
    Create configuration for specific tier.

    Args:
        tier_number: Target tier number (1-6)
        api_key: CFBD API key (optional, uses env var if not provided)

    Returns:
        TierOptimizedCFBDConfig instance
    """
    return TierOptimizedCFBDConfig(tier_number=tier_number, api_key=api_key)
