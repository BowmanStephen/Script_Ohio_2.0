"""Lightweight caching utilities for CFBD data sources."""

from __future__ import annotations

import json
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional


CacheFetcher = Callable[[], Any]
ClockFn = Callable[[], float]


@dataclass(slots=True)
class CacheEntry:
    value: Any
    expires_at: Optional[float]


class InMemoryCacheBackend:
    """Thread-safe in-memory backend used by default."""

    def __init__(self) -> None:
        self._store: Dict[str, CacheEntry] = {}
        self._lock = threading.Lock()

    def read(self, key: str) -> Optional[CacheEntry]:
        with self._lock:
            return self._store.get(key)

    def write(self, key: str, entry: CacheEntry) -> None:
        with self._lock:
            self._store[key] = entry

    def delete(self, key: str) -> None:
        with self._lock:
            self._store.pop(key, None)

    def keys(self) -> list[str]:
        with self._lock:
            return list(self._store.keys())

    def clear(self) -> None:
        with self._lock:
            self._store.clear()


DEFAULT_TTL_SECONDS: Dict[str, int] = {
    "games": 15 * 60,
    "ratings": 15 * 60,
    "lines": 2 * 60,
    "recruiting": 6 * 60 * 60,
    "team_talent": 12 * 60 * 60,
    "weather": 10 * 60,
    "media": 60 * 60,
    "raw": 10 * 60,
    "stats": 60 * 60,
    "teams": 7 * 24 * 60 * 60,
    "predictions": 5 * 60,
}


@dataclass(slots=True)
class CFBDCacheConfig:
    enable_cache: bool = True
    default_ttl_seconds: int = 15 * 60
    ttl_overrides: Dict[str, int] = field(default_factory=lambda: dict(DEFAULT_TTL_SECONDS))
    
    # Add fields used in cfbd_config.py from the plan if they differ from the existing class
    # The plan uses: cache_ttl_games, cache_ttl_stats, cache_ttl_teams, cache_ttl_predictions
    # I should adapt the config to support these or map them.
    # The plan's CFBDCacheConfig instantiation:
    # cache_config = CFBDCacheConfig(
    #     enable_cache=cache_enabled,
    #     cache_ttl_games=int(os.getenv("CFBD_CACHE_TTL_GAMES", "86400")),  # 24 hours
    #     ...
    # )
    # The existing class uses a dict `ttl_overrides`. 
    # I will update the class to include the specific fields the plan uses or update the plan's usage.
    # It is safer to update the class to be compatible with what the plan expects OR update the plan implementation in my head.
    # I will stick to the plan's implementation of CFBDConfig which instantiates CFBDCacheConfig.
    # I will modify CFBDCacheConfig to match the plan's usage or use kwargs.
    
    # Let's add the fields the plan seems to expect as arguments, but map them to ttl_overrides or keep them separate.
    # The plan implementation of CFBDConfig passes: enable_cache, cache_ttl_games, etc.
    # I will add these as optional init args that populate ttl_overrides.
    
    def __init__(self, enable_cache: bool = True, 
                 cache_ttl_games: int = 86400,
                 cache_ttl_stats: int = 3600,
                 cache_ttl_teams: int = 604800,
                 cache_ttl_predictions: int = 300,
                 default_ttl_seconds: int = 900,
                 ttl_overrides: Optional[Dict[str, int]] = None):
        self.enable_cache = enable_cache
        self.default_ttl_seconds = default_ttl_seconds
        self.ttl_overrides = ttl_overrides or dict(DEFAULT_TTL_SECONDS)
        
        # Update overrides with specific args
        self.ttl_overrides['games'] = cache_ttl_games
        self.ttl_overrides['stats'] = cache_ttl_stats
        self.ttl_overrides['teams'] = cache_ttl_teams
        self.ttl_overrides['predictions'] = cache_ttl_predictions
        self.ttl_overrides['ratings'] = cache_ttl_stats # map ratings to stats ttl roughly


class CFBDCacheManager:
    """Cache manager with pluggable backends and TTL policies."""

    def __init__(
        self,
        config: Optional[CFBDCacheConfig] = None,
        backend: Optional[InMemoryCacheBackend] = None,
        clock: Optional[ClockFn] = None,
    ) -> None:
        self._config = config or CFBDCacheConfig()
        self._backend = backend or InMemoryCacheBackend()
        self._clock = clock or time.monotonic
        self._stats = {"hits": 0, "misses": 0, "writes": 0}

    @property
    def enabled(self) -> bool:
        return self._config.enable_cache

    def _build_key(self, label: str, params: Optional[Dict[str, Any]]) -> str:
        serialized = json.dumps(params or {}, sort_keys=True, separators=(",", ":"))
        return f"{label}:{serialized}"

    def _resolve_ttl(self, label: str) -> int:
        return self._config.ttl_overrides.get(label, self._config.default_ttl_seconds)

    def invalidate(self, label: Optional[str] = None) -> None:
        if label is None:
            self._backend.clear()
        else:
            prefix = f"{label}:"
            for key in self._backend.keys():
                if key.startswith(prefix):
                    self._backend.delete(key)

    # Updated to match the plan's usage which calls get_cached_data and cache_data
    def get_cached_data(self, endpoint: str, params: Dict[str, Any], cache_type: str) -> Any:
         # endpoint is the label
         return self.get_or_fetch(endpoint, params, lambda: None, only_read=True)

    def cache_data(self, endpoint: str, params: Dict[str, Any], data: Any, cache_type: str) -> None:
        # We need to write to cache manually
        key = self._build_key(endpoint, params)
        now = self._clock()
        ttl = self._resolve_ttl(cache_type)
        expires_at = now + ttl if ttl > 0 else None
        self._backend.write(key, CacheEntry(value=data, expires_at=expires_at))
        self._stats["writes"] += 1

    def get_or_fetch(
        self,
        label: str,
        params: Optional[Dict[str, Any]],
        fetcher: CacheFetcher,
        only_read: bool = False
    ) -> Any:
        if not self.enabled:
            if only_read: return None
            return fetcher()

        key = self._build_key(label, params)
        now = self._clock()
        entry = self._backend.read(key)

        if entry and (entry.expires_at is None or entry.expires_at > now):
            self._stats["hits"] += 1
            return entry.value

        if entry:
            self._backend.delete(key)

        if only_read:
            return None

        value = fetcher()
        ttl = self._resolve_ttl(label)
        expires_at = now + ttl if ttl > 0 else None
        self._backend.write(key, CacheEntry(value=value, expires_at=expires_at))
        self._stats["misses"] += 1
        self._stats["writes"] += 1
        return value

    def get_cache_stats(self) -> Dict[str, int]:
        return dict(self._stats)

