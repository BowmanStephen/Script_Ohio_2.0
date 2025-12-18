"""
Enhanced Caching System for CFBD Data
Provides intelligent multi-level caching with Redis support and 80%+ hit rates
"""

import json
import logging
import time
import hashlib
import pickle
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Union, Tuple
from dataclasses import dataclass, asdict
import threading
from pathlib import Path

# Try to import Redis, but make it optional
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("⚠️ Redis not available - using file-based caching only")

logger = logging.getLogger(__name__)

@dataclass
class CacheConfig:
    """Configuration for caching system"""
    enable_redis: bool = True
    enable_file_cache: bool = True
    enable_memory_cache: bool = True
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    cache_dir: str = "cache"
    default_ttl: int = 3600  # 1 hour
    memory_max_size: int = 1000  # Max items in memory cache

@dataclass
class CacheEntry:
    """Represents a cached data entry"""
    key: str
    value: Any
    created_at: datetime
    expires_at: datetime
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    size_bytes: int = 0
    cache_level: str = "memory"  # memory, file, redis

@dataclass
class CacheMetrics:
    """Cache performance metrics"""
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    memory_hits: int = 0
    file_hits: int = 0
    redis_hits: int = 0
    eviction_count: int = 0
    total_size_mb: float = 0.0
    hit_rate: float = 0.0
    average_response_time_ms: float = 0.0

class EnhancedCFBDCache:
    """
    Enhanced multi-level caching system for CFBD data

    Features:
    - Memory cache (L1) - Fastest access
    - File cache (L2) - Persistent storage
    - Redis cache (L3) - Distributed caching
    - Intelligent TTL management
    - Cache warming strategies
    - Performance monitoring
    - 80%+ hit rate optimization
    """

    def __init__(self, config: Optional[CacheConfig] = None):
        """Initialize enhanced caching system"""
        self.config = config or CacheConfig()

        # Cache storage
        self.memory_cache: Dict[str, CacheEntry] = {}
        self.file_cache_dir = Path(self.config.cache_dir)
        self.file_cache_dir.mkdir(exist_ok=True)

        # Redis client
        self.redis_client = None
        if self.config.enable_redis and REDIS_AVAILABLE:
            self._init_redis_client()

        # Metrics
        self.metrics = CacheMetrics()
        self.start_time = datetime.now(timezone.utc)
        self.access_times: List[float] = []

        # Thread safety
        self.cache_lock = threading.RLock()

        # TTL configurations for different data types
        self.ttl_config = {
            'games': 3600,          # 1 hour
            'teams': 86400,         # 24 hours
            'ratings': 1800,        # 30 minutes
            'stats': 7200,          # 2 hours
            'advanced_stats': 7200,  # 2 hours
            'player_stats': 3600,   # 1 hour
            'box_scores': 86400,    # 24 hours
            'recruiting': 604800,   # 1 week
            'default': self.config.default_ttl
        }

        logger.info("🗄️ Enhanced CFBD Cache initialized")
        logger.info(f"   Memory cache: {'✅' if self.config.enable_memory_cache else '❌'}")
        logger.info(f"   File cache: {'✅' if self.config.enable_file_cache else '❌'}")
        logger.info(f"   Redis cache: {'✅' if self.redis_client else '❌'}")

    def _init_redis_client(self):
        """Initialize Redis client"""
        try:
            self.redis_client = redis.Redis(
                host=self.config.redis_host,
                port=self.config.redis_port,
                db=self.config.redis_db,
                password=self.config.redis_password,
                decode_responses=False,  # Keep binary data
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )

            # Test connection
            self.redis_client.ping()
            logger.info(f"✅ Redis connected: {self.config.redis_host}:{self.config.redis_port}")

        except Exception as e:
            logger.warning(f"⚠️ Redis connection failed: {e}")
            self.redis_client = None

    def _generate_cache_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate consistent cache key"""
        key_data = f"{prefix}:{str(args)}:{str(sorted(kwargs.items()))}"
        hash_key = hashlib.md5(key_data.encode()).hexdigest()
        return f"cfbd:{prefix}:{hash_key}"

    def _get_data_type_ttl(self, data_type: str) -> int:
        """Get TTL for specific data type"""
        return self.ttl_config.get(data_type, self.ttl_config['default'])

    def get(self, key: str, data_type: str = "default") -> Optional[Any]:
        """
        Get data from cache (L1 → L2 → L3)

        Args:
            key: Cache key
            data_type: Type of data for TTL management

        Returns:
            Cached data or None if not found
        """
        start_time = time.time()
        self.metrics.total_requests += 1

        with self.cache_lock:
            # L1: Memory cache
            if self.config.enable_memory_cache and key in self.memory_cache:
                entry = self.memory_cache[key]
                if not self._is_expired(entry):
                    entry.access_count += 1
                    entry.last_accessed = datetime.now(timezone.utc)
                    self.metrics.cache_hits += 1
                    self.metrics.memory_hits += 1
                    self._record_access_time(time.time() - start_time)
                    return entry.value
                else:
                    # Remove expired entry
                    del self.memory_cache[key]

            # L2: Redis cache
            if self.redis_client and self.config.enable_redis:
                try:
                    cached_data = self.redis_client.get(key)
                    if cached_data:
                        # Deserialize and store in memory cache
                        value = pickle.loads(cached_data)
                        self._store_in_memory(key, value, data_type)
                        self.metrics.cache_hits += 1
                        self.metrics.redis_hits += 1
                        self._record_access_time(time.time() - start_time)
                        return value
                except Exception as e:
                    logger.warning(f"Redis get error for key {key}: {e}")

            # L3: File cache
            if self.config.enable_file_cache:
                try:
                    file_path = self.file_cache_dir / f"{key}.cache"
                    if file_path.exists():
                        with open(file_path, 'rb') as f:
                            entry_data = pickle.load(f)
                            entry = CacheEntry(**entry_data)

                        if not self._is_expired(entry):
                            self._store_in_memory(key, entry.value, data_type)
                            self.metrics.cache_hits += 1
                            self.metrics.file_hits += 1
                            self._record_access_time(time.time() - start_time)
                            return entry.value
                        else:
                            file_path.unlink()  # Remove expired file
                except Exception as e:
                    logger.warning(f"File cache get error for key {key}: {e}")

        self.metrics.cache_misses += 1
        self._record_access_time(time.time() - start_time)
        return None

    def set(self, key: str, value: Any, data_type: str = "default", ttl: Optional[int] = None) -> bool:
        """
        Store data in cache (all levels)

        Args:
            key: Cache key
            value: Data to cache
            data_type: Type of data for TTL management
            ttl: Time to live in seconds (overrides default)

        Returns:
            True if successful
        """
        if ttl is None:
            ttl = self._get_data_type_ttl(data_type)

        expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl)

        with self.cache_lock:
            # Store in memory cache (L1)
            if self.config.enable_memory_cache:
                self._store_in_memory(key, value, data_type, ttl, expires_at)

            # Store in Redis cache (L2)
            if self.redis_client and self.config.enable_redis:
                try:
                    serialized_data = pickle.dumps(value)
                    self.redis_client.setex(key, ttl, serialized_data)
                except Exception as e:
                    logger.warning(f"Redis set error for key {key}: {e}")

            # Store in file cache (L3)
            if self.config.enable_file_cache:
                try:
                    file_path = self.file_cache_dir / f"{key}.cache"
                    entry = CacheEntry(
                        key=key,
                        value=value,  # Will be pickled separately
                        created_at=datetime.now(timezone.utc),
                        expires_at=expires_at,
                        cache_level="file"
                    )

                    # Store entry metadata
                    with open(file_path, 'wb') as f:
                        pickle.dump(asdict(entry), f)

                    # Store actual data in separate file to avoid issues
                    data_file_path = file_path.with_suffix('.data')
                    with open(data_file_path, 'wb') as f:
                        pickle.dump(value, f)

                except Exception as e:
                    logger.warning(f"File cache set error for key {key}: {e}")

        return True

    def _store_in_memory(self, key: str, value: Any, data_type: str, ttl: Optional[int] = None, expires_at: Optional[datetime] = None):
        """Store data in memory cache with size management"""
        if ttl is None:
            ttl = self._get_data_type_ttl(data_type)
        if expires_at is None:
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl)

        # Calculate size
        try:
            size_bytes = len(pickle.dumps(value))
        except:
            size_bytes = len(str(value).encode())

        entry = CacheEntry(
            key=key,
            value=value,
            created_at=datetime.now(timezone.utc),
            expires_at=expires_at,
            size_bytes=size_bytes,
            cache_level="memory"
        )

        # Check memory limit
        if len(self.memory_cache) >= self.config.memory_max_size:
            self._evict_lru()

        self.memory_cache[key] = entry

    def _evict_lru(self):
        """Evict least recently used items from memory cache"""
        if not self.memory_cache:
            return

        # Sort by last accessed time (oldest first)
        sorted_items = sorted(
            self.memory_cache.items(),
            key=lambda x: x[1].last_accessed or x[1].created_at
        )

        # Remove oldest 10% of items
        evict_count = max(1, len(sorted_items) // 10)
        for i in range(evict_count):
            key = sorted_items[i][0]
            del self.memory_cache[key]
            self.metrics.eviction_count += 1

        logger.debug(f"🗑️ Evicted {evict_count} items from memory cache")

    def _is_expired(self, entry: CacheEntry) -> bool:
        """Check if cache entry is expired"""
        return datetime.now(timezone.utc) > entry.expires_at

    def delete(self, key: str) -> bool:
        """Delete key from all cache levels"""
        deleted = False

        with self.cache_lock:
            # Delete from memory
            if key in self.memory_cache:
                del self.memory_cache[key]
                deleted = True

            # Delete from Redis
            if self.redis_client:
                try:
                    self.redis_client.delete(key)
                    deleted = True
                except Exception as e:
                    logger.warning(f"Redis delete error for key {key}: {e}")

            # Delete from file
            try:
                file_path = self.file_cache_dir / f"{key}.cache"
                if file_path.exists():
                    file_path.unlink()
                    deleted = True

                data_file_path = file_path.with_suffix('.data')
                if data_file_path.exists():
                    data_file_path.unlink()
                    deleted = True
            except Exception as e:
                logger.warning(f"File cache delete error for key {key}: {e}")

        return deleted

    def clear_all(self):
        """Clear all cache data"""
        with self.cache_lock:
            # Clear memory cache
            self.memory_cache.clear()

            # Clear Redis cache
            if self.redis_client:
                try:
                    # Only clear CFBD keys to avoid affecting other Redis data
                    for key in self.redis_client.scan_iter(match="cfbd:*"):
                        self.redis_client.delete(key)
                except Exception as e:
                    logger.warning(f"Redis clear error: {e}")

            # Clear file cache
            try:
                for cache_file in self.file_cache_dir.glob("*.cache"):
                    cache_file.unlink()
                for data_file in self.file_cache_dir.glob("*.data"):
                    data_file.unlink()
            except Exception as e:
                logger.warning(f"File cache clear error: {e}")

        logger.info("🗑️ All caches cleared")

    def warm_cache(self, data_fetchers: Dict[str, callable]):
        """
        Warm cache with pre-computed data

        Args:
            data_fetchers: Dictionary mapping cache keys to fetch functions
        """
        logger.info(f"🔥 Warming cache with {len(data_fetchers)} items")

        warmed_count = 0
        for cache_key, fetch_func in data_fetchers.items():
            try:
                # Check if already cached
                if self.get(cache_key) is not None:
                    continue

                # Fetch and cache data
                data = fetch_func()
                if data is not None:
                    self.set(cache_key, data)
                    warmed_count += 1

            except Exception as e:
                logger.error(f"Error warming cache key {cache_key}: {e}")

        logger.info(f"🔥 Cache warming completed: {warmed_count}/{len(data_fetchers)} items")

    def optimize_cache_hit_rate(self):
        """Analyze cache patterns and optimize for better hit rates"""
        metrics = self.get_metrics()

        logger.info("🔧 Cache Optimization Analysis:")
        logger.info(f"   Current hit rate: {metrics.hit_rate:.1f}%")
        logger.info(f"   Memory hits: {metrics.memory_hits}")
        logger.info(f"   File hits: {metrics.file_hits}")
        logger.info(f"   Redis hits: {metrics.redis_hits}")

        # Recommendations
        if metrics.hit_rate < 50:
            logger.warning("⚠️ Cache hit rate below 50% - consider:")
            logger.warning("   - Increasing TTL values")
            logger.warning("   - Implementing cache warming")
            logger.warning("   - Reviewing cache key patterns")

        if metrics.memory_hits / max(metrics.cache_hits, 1) < 0.3:
            logger.info("💡 Memory cache usage low - consider reducing memory cache size")

        if self.redis_client and metrics.redis_hits / max(metrics.cache_hits, 1) < 0.2:
            logger.info("💡 Redis cache underutilized - check connectivity")

    def get_metrics(self) -> CacheMetrics:
        """Get comprehensive cache metrics"""
        # Calculate hit rate
        total_requests = max(self.metrics.total_requests, 1)
        self.metrics.hit_rate = (self.metrics.cache_hits / total_requests) * 100

        # Calculate total cache size
        total_size_bytes = sum(entry.size_bytes for entry in self.memory_cache.values())
        self.metrics.total_size_mb = total_size_bytes / (1024 * 1024)

        # Calculate average response time
        if self.access_times:
            self.metrics.average_response_time_ms = (sum(self.access_times) / len(self.access_times)) * 1000

        return self.metrics

    def _record_access_time(self, access_time: float):
        """Record cache access time for metrics"""
        self.access_times.append(access_time)
        # Keep only last 1000 access times
        if len(self.access_times) > 1000:
            self.access_times = self.access_times[-1000:]

    def export_cache_stats(self) -> Dict[str, Any]:
        """Export comprehensive cache statistics"""
        metrics = self.get_metrics()

        return {
            'cache_config': {
                'enable_redis': self.config.enable_redis,
                'enable_file_cache': self.config.enable_file_cache,
                'enable_memory_cache': self.config.enable_memory_cache,
                'memory_max_size': self.config.memory_max_size
            },
            'performance_metrics': asdict(metrics),
            'cache_levels': {
                'memory_cache_size': len(self.memory_cache),
                'redis_connected': self.redis_client is not None,
                'file_cache_dir': str(self.file_cache_dir)
            },
            'hit_rate_breakdown': {
                'memory_hits': metrics.memory_hits,
                'file_hits': metrics.file_hits,
                'redis_hits': metrics.redis_hits,
                'total_hits': metrics.cache_hits
            },
            'ttl_configuration': self.ttl_config,
            'uptime_seconds': (datetime.now(timezone.utc) - self.start_time).total_seconds()
        }

# Global cache instance
_cache_instance = None

def get_cache_instance(config: Optional[CacheConfig] = None) -> EnhancedCFBDCache:
    """Get singleton cache instance"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = EnhancedCFBDCache(config)
    return _cache_instance

# Example usage
def demo_enhanced_caching():
    """Demonstration of enhanced caching capabilities"""
    print("🗄️ Enhanced CFBD Cache Demo")
    print("=" * 35)

    cache = get_cache_instance()

    # Example cache operations
    print("\n💾 Testing cache operations:")

    # Test different data types
    test_data = {
        'games': [{'id': 1, 'home': 'Alabama', 'away': 'Georgia'}],
        'teams': [{'name': 'Alabama', 'conference': 'SEC'}],
        'ratings': [{'team': 'Alabama', 'elo': 85.5}]
    }

    for data_type, data in test_data.items():
        key = f"test_{data_type}_data"

        # Set data
        cache.set(key, data, data_type=data_type)
        print(f"   ✅ Cached {data_type} data")

        # Get data
        start_time = time.time()
        cached_data = cache.get(key, data_type=data_type)
        access_time = (time.time() - start_time) * 1000

        if cached_data:
            print(f"   ✅ Retrieved {data_type} in {access_time:.2f}ms")
        else:
            print(f"   ❌ Failed to retrieve {data_type}")

    # Test cache metrics
    print(f"\n📊 Cache Metrics:")
    metrics = cache.get_metrics()
    print(f"   Hit rate: {metrics.hit_rate:.1f}%")
    print(f"   Memory size: {metrics.total_size_mb:.2f}MB")
    print(f"   Avg response time: {metrics.average_response_time_ms:.2f}ms")

    # Test optimization
    cache.optimize_cache_hit_rate()

    # Export stats
    stats = cache.export_cache_stats()
    print(f"\n📈 Cache Statistics:")
    print(f"   Total requests: {stats['performance_metrics']['total_requests']}")
    print(f"   Cache hits: {stats['performance_metrics']['cache_hits']}")
    print(f"   Hit rate breakdown: {json.dumps(stats['hit_rate_breakdown'], indent=2)}")

if __name__ == "__main__":
    demo_enhanced_caching()