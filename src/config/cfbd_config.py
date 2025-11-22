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
    max_requests_per_second: int = 6
    rate_limit_delay: float = 0.17  # 1/6 = 0.17s for exactly 6 req/sec
    max_retries: int = 3
    
    # Caching
    cache_config: CFBDCacheConfig = field(default_factory=CFBDCacheConfig)
    
    # Feature Flags
    enable_metrics: bool = True
    enable_logging: bool = True
    
    @classmethod
    def from_env(cls) -> 'CFBDConfig':
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
        
        # Rate limiting
        max_requests_per_second = int(os.getenv("CFBD_MAX_REQUESTS_PER_SECOND", "6"))
        rate_limit_delay = 1.0 / max_requests_per_second
        max_retries = int(os.getenv("CFBD_MAX_RETRIES", "3"))
        
        # Caching
        cache_enabled = os.getenv("CFBD_CACHE_ENABLED", "true").lower() != "false"
        cache_config = CFBDCacheConfig(
            enable_cache=cache_enabled,
            cache_ttl_games=int(os.getenv("CFBD_CACHE_TTL_GAMES", "86400")),  # 24 hours
            cache_ttl_stats=int(os.getenv("CFBD_CACHE_TTL_STATS", "3600")),   # 1 hour
            cache_ttl_teams=int(os.getenv("CFBD_CACHE_TTL_TEAMS", "604800")),  # 7 days
            cache_ttl_predictions=int(os.getenv("CFBD_CACHE_TTL_PREDICTIONS", "300")),  # 5 minutes
        )
        
        # Feature flags
        enable_metrics = os.getenv("CFBD_ENABLE_METRICS", "true").lower() != "false"
        enable_logging = os.getenv("CFBD_ENABLE_LOGGING", "true").lower() != "false"
        
        if not api_key:
             # The plan says raise error here.
             raise ValueError("CFBD_API_KEY or CFBD_API_TOKEN environment variable required")

        return cls(
            api_key=api_key,
            host=host,
            max_requests_per_second=max_requests_per_second,
            rate_limit_delay=rate_limit_delay,
            max_retries=max_retries,
            cache_config=cache_config,
            enable_metrics=enable_metrics,
            enable_logging=enable_logging,
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

