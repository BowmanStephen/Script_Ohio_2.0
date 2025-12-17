"""
Live Scoreboard Polling Service
================================

Polls CFBD scoreboard data at regular intervals during live game windows
and caches results for fast access.
"""

import logging
import threading
import time
from datetime import datetime
from typing import Any, Dict, List, Optional
from collections import deque

from src.cfbd_client.unified_client import UnifiedCFBDClient
from src.cfbd_client.cfbd_cache_manager import CFBDCacheManager

logger = logging.getLogger(__name__)

# Global lock to ensure only one poller instance per process
_poller_lock = threading.Lock()
_active_pollers: Dict[str, 'LiveScoreboardPoller'] = {}


class LiveScoreboardPoller:
    """
    Polls live scoreboard data from CFBD API and caches results.
    
    Features:
    - Configurable polling interval (default: 30 seconds)
    - Automatic cache management
    - Graceful rate limiting
    - Thread-safe operation
    """
    
    def __init__(
        self,
        cfbd_client: UnifiedCFBDClient,
        cache_manager: CFBDCacheManager,
        polling_interval: int = 30,
        max_queue_size: int = 100,
        max_failures: int = 5,
    ):
        """
        Initialize live scoreboard poller.
        
        Args:
            cfbd_client: UnifiedCFBDClient instance
            cache_manager: CFBDCacheManager instance
            polling_interval: Polling interval in seconds (default: 30)
            max_queue_size: Maximum queue size for buffering (default: 100)
            max_failures: Maximum consecutive failures before backoff (default: 5)
        """
        self.client = cfbd_client
        self.cache = cache_manager
        self.polling_interval = polling_interval
        self.max_queue_size = max_queue_size
        self.max_failures = max_failures
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        self._event_queue: deque = deque(maxlen=max_queue_size)
        self._consecutive_failures = 0
        self._backoff_multiplier = 1.0
    
    def start_polling(self, season: int, week: Optional[int] = None) -> None:
        """
        Start background polling for live scoreboard.
        
        Args:
            season: Season year (e.g., 2025)
            week: Optional week number (if None, polls current week)
        
        Raises:
            RuntimeError: If another poller instance is already running for this season/week
        """
        # Check for existing poller instance
        poller_key = f"{season}_{week or 'current'}"
        with _poller_lock:
            if poller_key in _active_pollers:
                existing = _active_pollers[poller_key]
                if existing.is_running:
                    raise RuntimeError(
                        f"Poller already running for season={season}, week={week}. "
                        f"Stop existing poller before starting a new one."
                    )
                else:
                    # Clean up stale entry
                    del _active_pollers[poller_key]
            
            if self._running:
                logger.warning("Poller is already running")
                return
            
            _active_pollers[poller_key] = self
            self._running = True
            self._stop_event.clear()
        
        def poll_loop():
            while not self._stop_event.is_set():
                try:
                    self._poll_scoreboard(season, week)
                    # Reset failure count on success
                    self._consecutive_failures = 0
                    self._backoff_multiplier = 1.0
                except Exception as e:
                    self._consecutive_failures += 1
                    logger.error(f"Error in scoreboard polling (failure {self._consecutive_failures}): {e}")
                    
                    # Exponential backoff on repeated failures
                    if self._consecutive_failures >= self.max_failures:
                        self._backoff_multiplier = min(self._backoff_multiplier * 2, 8.0)  # Cap at 8x
                        logger.warning(
                            f"Backing off polling: {self.polling_interval * self._backoff_multiplier}s "
                            f"(failures: {self._consecutive_failures})"
                        )
                
                # Wait for polling interval (with backoff) or stop event
                wait_time = self.polling_interval * self._backoff_multiplier
                if self._stop_event.wait(wait_time):
                    break
        
        self._thread = threading.Thread(target=poll_loop, daemon=True)
        self._thread.start()
        logger.info(f"Started live scoreboard polling for season={season}, week={week}")
    
    def stop_polling(self) -> None:
        """Stop background polling and clean up."""
        if not self._running:
            return
        
        self._running = False
        self._stop_event.set()
        
        if self._thread:
            self._thread.join(timeout=5.0)
        
        # Remove from active pollers
        with _poller_lock:
            poller_key = None
            for key, poller in _active_pollers.items():
                if poller is self:
                    poller_key = key
                    break
            if poller_key:
                del _active_pollers[poller_key]
        
        logger.info("Stopped live scoreboard polling")
    
    def _poll_scoreboard(self, season: int, week: Optional[int] = None) -> None:
        """
        Poll scoreboard data and update cache.
        
        Args:
            season: Season year
            week: Optional week number
        """
        try:
            # Fetch scoreboard data
            games = self.client.get_games(year=season, week=week)
            
            # Build cache key
            cache_key = self._build_cache_key("live_scoreboard", season=season, week=week or "current")
            
            # Update cache with fresh data
            with self._lock:
                # Use cache manager's put method if available, otherwise direct cache
                if hasattr(self.cache, 'put'):
                    self.cache.put(
                        cache_key,
                        {
                            "games": games,
                            "last_updated": datetime.utcnow().isoformat(),
                            "season": season,
                            "week": week,
                        },
                        ttl_seconds=60,  # 1 minute TTL for live data
                        tags=["cfbd", "live", "scoreboard"],
                    )
                else:
                    # Fallback: use cache manager's internal cache
                    if hasattr(self.cache, '_cache'):
                        self.cache._cache[cache_key] = {
                            "games": games,
                            "last_updated": datetime.utcnow().isoformat(),
                        }
            
            logger.debug(f"Updated live scoreboard cache: {len(games)} games")
            
        except Exception as e:
            logger.error(f"Failed to poll scoreboard: {e}")
            # Don't raise - continue polling even if one request fails
    
    def get_cached_scoreboard(
        self,
        season: int,
        week: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get latest cached scoreboard data.
        
        Args:
            season: Season year
            week: Optional week number
        
        Returns:
            List of game dictionaries
        """
        cache_key = self._build_cache_key("live_scoreboard", season=season, week=week or "current")
        
        with self._lock:
            if hasattr(self.cache, 'get'):
                cached_data = self.cache.get(cache_key)
            elif hasattr(self.cache, '_cache'):
                cached_data = self.cache._cache.get(cache_key)
            else:
                cached_data = None
            
            if cached_data:
                if isinstance(cached_data, dict):
                    return cached_data.get("games", [])
                return cached_data if isinstance(cached_data, list) else []
        
        return []
    
    def _build_cache_key(self, prefix: str, **parts: Any) -> str:
        """Build cache key from prefix and parts."""
        ordered = "_".join(f"{key}:{parts[key]}" for key in sorted(parts))
        return f"{prefix}:{ordered}"
    
    @property
    def is_running(self) -> bool:
        """Check if poller is currently running."""
        return self._running
