"""
Advanced Caching and Performance Optimization Layer
Provides intelligent caching, performance monitoring, and optimization
"""

import time
import threading
import hashlib
import json
import pickle
import sqlite3
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
from concurrent.futures import ThreadPoolExecutor
import asyncio
# import aioredis  # Optional distributed cache - requires pip install aioredis
try:
    import psutil
except ImportError:
    psutil = None
    logger = logging.getLogger(__name__)
    logger.warning("psutil not available. Some monitoring features will be limited.")

class CacheLevel(Enum):
    MEMORY = "memory"
    DISK = "disk"
    DISTRIBUTED = "distributed"

class CachePolicy(Enum):
    LRU = "lru"
    LFU = "lfu"
    FIFO = "fifo"
    TTL = "ttl"

@dataclass
class CacheConfig:
    """Configuration for cache settings"""
    max_memory_size: int = 100 * 1024 * 1024  # 100MB
    max_disk_size: int = 1024 * 1024 * 1024  # 1GB
    default_ttl: int = 3600  # 1 hour
    cleanup_interval: int = 300  # 5 minutes
    compression_threshold: int = 1024  # 1KB
    enable_persistence: bool = True
    enable_compression: bool = True
    enable_metrics: bool = True

@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    key: str
    value: Any
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    ttl: Optional[int] = None
    access_count: int = 0
    size_bytes: int = 0
    compression_ratio: float = 1.0
    hit_count: int = 0
    miss_count: int = 0
    level: CacheLevel = CacheLevel.MEMORY

    def is_expired(self) -> bool:
        """Check if cache entry is expired"""
        if self.ttl is None:
            return False
        return (datetime.now() - self.created_at).total_seconds() > self.ttl

    def update_access(self):
        """Update access statistics"""
        self.last_accessed = datetime.now()
        self.access_count += 1
        self.hit_count += 1

class MemoryCache:
    """In-memory LRU cache implementation"""

    def __init__(self, max_size: int, policy: CachePolicy = CachePolicy.LRU):
        self.max_size = max_size
        self.policy = policy
        self.cache: Dict[str, CacheEntry] = {}
        self.access_order: List[str] = []
        self.lock = threading.RLock()
        self.current_size = 0

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        with self.lock:
            entry = self.cache.get(key)
            if entry is None:
                return None

            if entry.is_expired():
                self._remove_entry(key)
                return None

            entry.update_access()
            self._update_access_order(key)
            return entry.value

    def put(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Put value in cache"""
        with self.lock:
            # Check if key exists
            if key in self.cache:
                old_entry = self.cache[key]
                self.current_size -= old_entry.size_bytes
                del self.cache[key]
                if key in self.access_order:
                    self.access_order.remove(key)

            # Calculate size
            size_bytes = len(pickle.dumps(value))
            entry = CacheEntry(
                key=key,
                value=value,
                ttl=ttl,
                size_bytes=size_bytes,
                level=CacheLevel.MEMORY
            )

            # Evict if necessary
            while self.current_size + size_bytes > self.max_size and self.cache:
                self._evict_one()

            # Add new entry
            self.cache[key] = entry
            self.current_size += size_bytes
            self._update_access_order(key)

            return True

    def remove(self, key: str) -> bool:
        """Remove key from cache"""
        with self.lock:
            if key not in self.cache:
                return False

            entry = self.cache[key]
            self.current_size -= entry.size_bytes
            del self.cache[key]
            if key in self.access_order:
                self.access_order.remove(key)

            return True

    def clear(self):
        """Clear all cache entries"""
        with self.lock:
            self.cache.clear()
            self.access_order.clear()
            self.current_size = 0

    def _evict_one(self):
        """Evict one entry based on policy"""
        if not self.cache:
            return

        if self.policy == CachePolicy.LRU:
            # Remove least recently used
            if self.access_order:
                key_to_remove = self.access_order[0]
                self.remove(key_to_remove)

        elif self.policy == CachePolicy.LFU:
            # Remove least frequently used
            min_access_count = min(entry.access_count for entry in self.cache.values())
            candidates = [key for key, entry in self.cache.items() if entry.access_count == min_access_count]
            if candidates:
                self.remove(candidates[0])

        elif self.policy == CachePolicy.FIFO:
            # Remove oldest
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k].created_at)
            self.remove(oldest_key)

        elif self.policy == CachePolicy.TTL:
            # Remove expired first, then oldest
            expired_keys = [key for key, entry in self.cache.items() if entry.is_expired()]
            if expired_keys:
                self.remove(expired_keys[0])
            else:
                oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k].created_at)
                self.remove(oldest_key)

    def _update_access_order(self, key: str):
        """Update access order for LRU"""
        if self.policy == CachePolicy.LRU:
            if key in self.access_order:
                self.access_order.remove(key)
            self.access_order.append(key)

    def _remove_entry(self, key: str):
        """Remove entry and update size"""
        entry = self.cache[key]
        self.current_size -= entry.size_bytes
        del self.cache[key]
        if key in self.access_order:
            self.access_order.remove(key)

class DiskCache:
    """Persistent disk cache using SQLite"""

    def __init__(self, cache_dir: str, max_size: int):
        self.cache_dir = cache_dir
        self.max_size = max_size
        os.makedirs(cache_dir, exist_ok=True)

        # Initialize database
        self.db_path = os.path.join(cache_dir, "cache.db")
        self._init_database()

        self.lock = threading.RLock()

    def _init_database(self):
        """Initialize SQLite database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS cache_entries (
                    key TEXT PRIMARY KEY,
                    value BLOB,
                    created_at TIMESTAMP,
                    last_accessed TIMESTAMP,
                    ttl INTEGER,
                    access_count INTEGER,
                    size_bytes INTEGER
                )
            ''')

            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_last_accessed ON cache_entries(last_accessed)
            ''')

            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_created_at ON cache_entries(created_at)
            ''')

            conn.commit()

    def get(self, key: str) -> Optional[Any]:
        """Get value from disk cache"""
        with self.lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute('''
                        SELECT value, created_at, ttl, access_count, last_accessed
                        FROM cache_entries WHERE key = ?
                    ''', (key,))

                    row = cursor.fetchone()
                    if row is None:
                        return None

                    value_blob, created_at, ttl, access_count, last_accessed = row

                    # Check if expired
                    if ttl is not None:
                        created_time = datetime.fromisoformat(created_at)
                        if (datetime.now() - created_time).total_seconds() > ttl:
                            self._remove_entry_db(key)
                            return None

                    # Update access statistics
                    conn.execute('''
                        UPDATE cache_entries
                        SET last_accessed = ?, access_count = access_count + 1
                        WHERE key = ?
                    ''', (datetime.now().isoformat(), key))
                    conn.commit()

                    # Deserialize value
                    value = pickle.loads(value_blob)
                    return value

            except Exception as e:
                logging.error(f"Error getting from disk cache: {e}")
                return None

    def put(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Put value in disk cache"""
        with self.lock:
            try:
                # Serialize value
                value_blob = pickle.dumps(value)
                size_bytes = len(value_blob)

                # Check size limit
                if size_bytes > self.max_size:
                    return False

                # Evict if necessary
                while self._get_total_size() + size_bytes > self.max_size:
                    self._evict_one()

                # Store value
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute('''
                        INSERT OR REPLACE INTO cache_entries
                        (key, value, created_at, last_accessed, ttl, access_count, size_bytes)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        key,
                        value_blob,
                        datetime.now().isoformat(),
                        datetime.now().isoformat(),
                        ttl,
                        1,
                        size_bytes
                    ))
                    conn.commit()

                return True

            except Exception as e:
                logging.error(f"Error putting to disk cache: {e}")
                return False

    def remove(self, key: str) -> bool:
        """Remove key from disk cache"""
        with self.lock:
            try:
                return self._remove_entry_db(key)
            except Exception as e:
                logging.error(f"Error removing from disk cache: {e}")
                return False

    def clear(self):
        """Clear all disk cache entries"""
        with self.lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute('DELETE FROM cache_entries')
                    conn.commit()
            except Exception as e:
                logging.error(f"Error clearing disk cache: {e}")

    def _remove_entry_db(self, key: str) -> bool:
        """Remove entry from database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('DELETE FROM cache_entries WHERE key = ?', (key,))
            conn.commit()
            return cursor.rowcount > 0

    def _get_total_size(self) -> int:
        """Get total size of cache"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('SELECT COALESCE(SUM(size_bytes), 0) FROM cache_entries')
            return cursor.fetchone()[0]

    def _evict_one(self):
        """Evict one entry (oldest first)"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT key FROM cache_entries ORDER BY last_accessed ASC LIMIT 1
            ''')
            row = cursor.fetchone()
            if row:
                self._remove_entry_db(row[0])

class CachingLayer:
    """Multi-level intelligent caching system"""

    def __init__(self, config: CacheConfig = None):
        self.config = config or CacheConfig()

        # Initialize cache levels
        self.memory_cache = MemoryCache(self.config.max_memory_size, CachePolicy.LRU)

        cache_dir = os.path.join(os.getcwd(), "cache")
        self.disk_cache = DiskCache(cache_dir, self.config.max_disk_size)

        # Metrics
        self.metrics = {
            "memory_hits": 0,
            "memory_misses": 0,
            "disk_hits": 0,
            "disk_misses": 0,
            "total_requests": 0,
            "evictions": 0,
            "compression_savings": 0
        }

        # Background cleanup
        self.cleanup_thread = None
        self.running = False

        # Custom cache functions
        self.cache_functions: Dict[str, Callable] = {}

        self.logger = logging.getLogger("caching_layer")
        self.start_cleanup_thread()

    def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache (checks memory first, then disk)"""
        self.metrics["total_requests"] += 1

        # Try memory cache first
        value = self.memory_cache.get(key)
        if value is not None:
            self.metrics["memory_hits"] += 1
            return value

        self.metrics["memory_misses"] += 1

        # Try disk cache
        value = self.disk_cache.get(key)
        if value is not None:
            self.metrics["disk_hits"] += 1
            # Promote to memory cache
            self.memory_cache.put(key, value)
            return value

        self.metrics["disk_misses"] += 1
        return default

    def put(self, key: str, value: Any, ttl: Optional[int] = None, level: CacheLevel = CacheLevel.MEMORY) -> bool:
        """Put value in cache"""
        try:
            # Apply compression if enabled and value is large enough
            if self.config.enable_compression and self._should_compress(value):
                value = self._compress_value(value)

            if level == CacheLevel.MEMORY:
                return self.memory_cache.put(key, value, ttl)
            elif level == CacheLevel.DISK:
                return self.disk_cache.put(key, value, ttl)
            else:
                # Default to memory
                return self.memory_cache.put(key, value, ttl)

        except Exception as e:
            self.logger.error(f"Error putting to cache: {e}")
            return False

    def remove(self, key: str) -> bool:
        """Remove key from all cache levels"""
        memory_removed = self.memory_cache.remove(key)
        disk_removed = self.disk_cache.remove(key)
        return memory_removed or disk_removed

    def clear(self, level: CacheLevel = None):
        """Clear cache"""
        if level is None or level == CacheLevel.MEMORY:
            self.memory_cache.clear()
        if level is None or level == CacheLevel.DISK:
            self.disk_cache.clear()

    def cache_function(self, ttl: int = None, level: CacheLevel = CacheLevel.MEMORY):
        """Decorator to cache function results"""
        def decorator(func: Callable):
            def wrapper(*args, **kwargs):
                # Generate cache key
                cache_key = self._generate_function_key(func, args, kwargs)

                # Try to get from cache
                result = self.get(cache_key)
                if result is not None:
                    return result

                # Execute function and cache result
                result = func(*args, **kwargs)
                self.put(cache_key, result, ttl, level)
                return result

            return wrapper
        return decorator

    def cache_async_function(self, ttl: int = None, level: CacheLevel = CacheLevel.MEMORY):
        """Decorator to cache async function results"""
        def decorator(func: Callable):
            async def wrapper(*args, **kwargs):
                # Generate cache key
                cache_key = self._generate_function_key(func, args, kwargs)

                # Try to get from cache
                result = self.get(cache_key)
                if result is not None:
                    return result

                # Execute function and cache result
                result = await func(*args, **kwargs)
                self.put(cache_key, result, ttl, level)
                return result

            return wrapper
        return decorator

    def get_metrics(self) -> Dict[str, Any]:
        """Get cache performance metrics"""
        total_hits = self.metrics["memory_hits"] + self.metrics["disk_hits"]
        total_misses = self.metrics["memory_misses"] + self.metrics["disk_misses"]
        total_requests = total_hits + total_misses

        hit_rate = (total_hits / total_requests) if total_requests > 0 else 0
        memory_hit_rate = (self.metrics["memory_hits"] / (self.metrics["memory_hits"] + self.metrics["memory_misses"])) if (self.metrics["memory_hits"] + self.metrics["memory_misses"]) > 0 else 0
        disk_hit_rate = (self.metrics["disk_hits"] / (self.metrics["disk_hits"] + self.metrics["disk_misses"])) if (self.metrics["disk_hits"] + self.metrics["disk_misses"]) > 0 else 0

        # Memory usage
        if psutil:
            memory_usage = psutil.virtual_memory()
            process_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        else:
            memory_usage = type('obj', (object,), {'percent': 0.0})()
            process_memory = 0.0

        return {
            "hit_rate": hit_rate,
            "memory_hit_rate": memory_hit_rate,
            "disk_hit_rate": disk_hit_rate,
            "total_requests": total_requests,
            "total_hits": total_hits,
            "total_misses": total_misses,
            "memory_hits": self.metrics["memory_hits"],
            "disk_hits": self.metrics["disk_hits"],
            "evictions": self.metrics["evictions"],
            "compression_savings": self.metrics["compression_savings"],
            "memory_usage_mb": process_memory,
            "system_memory_usage_percent": memory_usage.percent,
            "memory_cache_size": self.memory_cache.current_size,
            "disk_cache_size": self.disk_cache._get_total_size(),
            "memory_cache_entries": len(self.memory_cache.cache)
        }

    def _generate_function_key(self, func: Callable, args: tuple, kwargs: dict) -> str:
        """Generate cache key for function call"""
        # Create a deterministic key from function name and arguments
        key_parts = [
            func.__name__,
            str(args),
            str(sorted(kwargs.items()))
        ]

        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()

    def _should_compress(self, value: Any) -> bool:
        """Check if value should be compressed"""
        if not self.config.enable_compression:
            return False

        try:
            size = len(pickle.dumps(value))
            return size >= self.config.compression_threshold
        except:
            return False

    def _compress_value(self, value: Any) -> Any:
        """Compress a value"""
        try:
            # Simple compression - convert to smaller representation if possible
            if isinstance(value, str) and len(value) > self.config.compression_threshold:
                # Store as bytes to save space
                compressed = value.encode('utf-8')
                self.metrics["compression_savings"] += len(value) - len(compressed)
                return compressed

            return value
        except:
            return value

    def start_cleanup_thread(self):
        """Start background cleanup thread"""
        if self.cleanup_thread is None or not self.cleanup_thread.is_alive():
            self.running = True
            self.cleanup_thread = threading.Thread(target=self._cleanup_worker, daemon=True)
            self.cleanup_thread.start()

    def stop_cleanup_thread(self):
        """Stop background cleanup thread"""
        self.running = False
        if self.cleanup_thread:
            self.cleanup_thread.join(timeout=5)

    def _cleanup_worker(self):
        """Background cleanup worker"""
        while self.running:
            try:
                # Cleanup expired entries
                self._cleanup_expired_entries()

                # Optimize memory usage
                self._optimize_memory_usage()

                # Sleep for cleanup interval
                time.sleep(self.config.cleanup_interval)

            except Exception as e:
                self.logger.error(f"Error in cleanup worker: {e}")
                time.sleep(60)

    def _cleanup_expired_entries(self):
        """Remove expired cache entries"""
        # Memory cache cleanup is handled automatically
        # Disk cache cleanup requires explicit handling
        try:
            with sqlite3.connect(self.disk_cache.db_path) as conn:
                # Find and remove expired entries
                cursor = conn.execute('''
                    SELECT key FROM cache_entries
                    WHERE ttl IS NOT NULL AND
                          (julianday('now') - julianday(created_at)) * 86400 > ttl
                ''')

                expired_keys = [row[0] for row in cursor.fetchall()]

                for key in expired_keys:
                    self.disk_cache.remove(key)

                if expired_keys:
                    self.logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")

        except Exception as e:
            self.logger.error(f"Error cleaning up expired entries: {e}")

    def _optimize_memory_usage(self):
        """Optimize memory usage"""
        try:
            if psutil:
                memory_usage = psutil.Process().memory_info().rss / 1024 / 1024  # MB
                threshold = self.config.max_memory_size / (1024 * 1024) * 0.8  # 80% threshold
            else:
                # Fallback when psutil is not available
                memory_usage = 50.0  # Assume 50MB
                threshold = 80.0

            # If memory usage is high, reduce memory cache size
            if memory_usage > threshold:
                # Clear least recently used entries from memory cache
                original_size = len(self.memory_cache.cache)

                # Remove a portion of entries
                entries_to_remove = max(1, original_size // 4)
                keys_to_remove = list(self.memory_cache.cache.keys())[:entries_to_remove]

                for key in keys_to_remove:
                    # Move to disk cache instead of just removing
                    entry = self.memory_cache.cache.get(key)
                    if entry:
                        self.disk_cache.put(key, entry.value, entry.ttl)
                    self.memory_cache.remove(key)

                self.logger.info(f"Optimized memory: moved {len(keys_to_remove)} entries to disk cache")

        except Exception as e:
            self.logger.error(f"Error optimizing memory usage: {e}")

# Global cache instance
cache = CachingLayer()

# Convenience functions
def cached(ttl: int = None, level: CacheLevel = CacheLevel.MEMORY):
    """Convenience decorator for caching functions"""
    return cache.cache_function(ttl, level)

def async_cached(ttl: int = None, level: CacheLevel = CacheLevel.MEMORY):
    """Convenience decorator for caching async functions"""
    return cache.cache_async_function(ttl, level)

def get_cache_metrics() -> Dict[str, Any]:
    """Get cache performance metrics"""
    return cache.get_metrics()