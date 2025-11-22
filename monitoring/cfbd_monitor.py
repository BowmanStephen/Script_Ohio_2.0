"""
Monitoring and alerting for CFBD API integration.
"""

import logging
from typing import Dict, Any
from src.cfbd_client.unified_client import UnifiedCFBDClient

logger = logging.getLogger(__name__)

class CFBDMonitor:
    """Monitor CFBD API usage and performance"""
    
    def __init__(self, client: UnifiedCFBDClient):
        self.client = client
    
    def check_health(self) -> Dict[str, Any]:
        """Check CFBD API health"""
        try:
            # Test API connectivity
            # Use a lightweight call, e.g. current year games or just verify config/connectivity
            # get_games(year=2025, week=1) is standard test
            games = self.client.get_games(year=2025, week=1)
            
            # Get metrics
            metrics = self.client.get_metrics()
            client_metrics = metrics.get("client_metrics", {})
            
            # Determine health status
            total_requests = client_metrics.get("total_requests", 0)
            errors = client_metrics.get("errors", 0)
            
            error_rate = (
                errors / max(total_requests, 1)
            )
            
            cache_hits = client_metrics.get("cache_hits", 0)
            cache_misses = client_metrics.get("cache_misses", 0)
            
            cache_hit_rate = (
                cache_hits / max(cache_hits + cache_misses, 1)
            )
            
            health_status = {
                "status": "healthy" if error_rate < 0.05 else "degraded",
                "error_rate": error_rate,
                "cache_hit_rate": cache_hit_rate,
                "total_requests": total_requests,
                "average_latency_ms": client_metrics.get("average_latency_ms", 0.0),
            }
            
            # Log warnings for degraded performance
            if error_rate > 0.05:
                logger.warning(f"⚠️ High error rate: {error_rate:.2%}")
            
            if cache_hit_rate < 0.5 and total_requests > 10:
                logger.warning(f"⚠️ Low cache hit rate: {cache_hit_rate:.2%}")
            
            return health_status
            
        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }

