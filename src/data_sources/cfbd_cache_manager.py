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
}


@dataclass(slots=True)
class CFBDCacheConfig:
    enabled: bool = True
    default_ttl_seconds: int = 15 * 60
    ttl_overrides: Dict[str, int] = field(default_factory=lambda: dict(DEFAULT_TTL_SECONDS))


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
        return self._config.enabled

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

    def get_or_fetch(
        self,
        label: str,
        params: Optional[Dict[str, Any]],
        fetcher: CacheFetcher,
    ) -> Any:
        if not self.enabled:
            return fetcher()

        key = self._build_key(label, params)
        now = self._clock()
        entry = self._backend.read(key)

        if entry and (entry.expires_at is None or entry.expires_at > now):
            self._stats["hits"] += 1
            return entry.value

        if entry:
            self._backend.delete(key)

        value = fetcher()
        ttl = self._resolve_ttl(label)
        expires_at = now + ttl if ttl > 0 else None
        self._backend.write(key, CacheEntry(value=value, expires_at=expires_at))
        self._stats["misses"] += 1
        self._stats["writes"] += 1
        return value

    def stats(self) -> Dict[str, int]:
        return dict(self._stats)

