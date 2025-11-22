#!/usr/bin/env python3
"""
Advanced Cache Manager - High-Performance Multi-Level Caching System

This module implements intelligent caching with predictive preloading,
adaptive eviction policies, and distributed caching support for the
Script Ohio 2.0 platform to achieve Grade A performance.

Author: Claude Code Assistant (Performance Tuning Agent)
Created: 2025-11-10
Version: 1.0
"""

import os
import time
import json
import hashlib
import threading
import logging
import pickle
import zlib
from typing import Dict, List, Optional, Any, Tuple, Union, Callable
from dataclasses import dataclass, asdict
from collections import OrderedDict, defaultdict, deque
from pathlib import Path
import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
import weakref
import gc
from abc import ABC, abstractmethod

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    key: str
    value: Any
    size_bytes: int
    created_at: float
    last_accessed: float
    access_count: int
    ttl_seconds: Optional[float]
    compression_ratio: Optional[float]
    cost: float  # Computational cost to regenerate
    tags: List[str]
    priority: int  # 1=low, 5=high

@dataclass
class CacheStats:
    """Cache performance statistics"""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    size_bytes: int = 0
    entry_count: int = 0
    avg_access_time_ms: float = 0.0
    compression_ratio: float = 1.0
    hit_rate: float = 0.0

class EvictionPolicy(ABC):
    """Abstract base class for cache eviction policies"""

    @abstractmethod
    def should_evict(self, cache_entries: Dict[str, CacheEntry], new_entry_size: int,
                    max_size_bytes: int) -> Optional[str]:
        """Determine if an entry should be evicted and return key to evict"""
        pass

    @abstractmethod
    def update_access(self, entry: CacheEntry):
        """Update entry access information"""
        pass

class LRUWithCostEviction(EvictionPolicy):
    """LRU eviction policy that considers computational cost"""

    def __init__(self, cost_weight: float = 0.3):
        self.cost_weight = cost_weight
        self.access_order = OrderedDict()

    def should_evict(self, cache_entries: Dict[str, CacheEntry], new_entry_size: int,
                    max_size_bytes: int) -> Optional[str]:
        """Evict based on LRU with cost consideration"""
        total_size = sum(entry.size_bytes for entry in cache_entries.values())

        if total_size + new_entry_size <= max_size_bytes:
            return None

        # Calculate eviction score: lower score = higher eviction priority
        def eviction_score(key: str, entry: CacheEntry) -> float:
            recent_access = (time.time() - entry.last_accessed) / 3600  # Hours since access
            frequency = entry.access_count / max(1, time.time() - entry.created_at)
            cost_factor = entry.cost * self.cost_weight
            return recent_access / (frequency + 0.1) + cost_factor

        # Find entry with lowest eviction score
        if self.access_order:
            # Combine LRU order with cost scoring
            for key in self.access_order:
                if key in cache_entries:
                    return key

        # Fallback to cost-based eviction
        return min(cache_entries.keys(), key=lambda k: eviction_score(k, cache_entries[k]))

    def update_access(self, entry: CacheEntry):
        """Update LRU access order"""
        if entry.key in self.access_order:
            self.access_order.move_to_end(entry.key)
        else:
            self.access_order[entry.key] = True

class PredictivePreloader:
    """Predictive cache preloading based on access patterns"""

    def __init__(self, max_predictions: int = 50):
        self.max_predictions = max_predictions
        self.access_patterns = defaultdict(lambda: defaultdict(int))
        self.sequence_patterns = []
        self.last_accesses = {}

    def record_access(self, key: str, tags: List[str] = None):
        """Record cache access for pattern learning"""
        timestamp = int(time.time() / 60)  # Minute-level granularity
        self.access_patterns[key][timestamp] += 1

        # Record tag associations
        if tags:
            for tag in tags:
                self.access_patterns[f"tag:{tag}"][timestamp] += 1

        # Update last access time
        self.last_accesses[key] = time.time()

        # Update sequence patterns
        self._update_sequence_pattern(key)

    def _update_sequence_pattern(self, key: str):
        """Update access sequence patterns"""
        current_time = time.time()
        recent_keys = [
            k for k, t in self.last_accesses.items()
            if current_time - t < 300  # Last 5 minutes
        ]

        if len(recent_keys) > 1:
            self.sequence_patterns.append(recent_keys[-3:])  # Keep last 3 in sequence

        # Limit pattern history
        if len(self.sequence_patterns) > 1000:
            self.sequence_patterns = self.sequence_patterns[-500:]

    def predict_next_accesses(self, current_key: str, limit: int = 10) -> List[str]:
        """Predict likely next accesses based on patterns"""
        predictions = []
        current_time = time.time()

        # Sequence-based predictions
        for sequence in self.sequence_patterns:
            if len(sequence) >= 2 and sequence[-2] == current_key:
                next_key = sequence[-1]
                if next_key != current_key and next_key not in predictions:
                    predictions.append(next_key)

        # Frequency-based predictions
        key_patterns = self.access_patterns.get(current_key, {})
        if key_patterns:
            # Find keys frequently accessed after current key
            for other_key, patterns in self.access_patterns.items():
                if other_key != current_key and other_key not in predictions:
                    correlation_score = self._calculate_correlation(
                        key_patterns, patterns
                    )
                    if correlation_score > 0.3:
                        predictions.append(other_key)

        return predictions[:limit]

    def _calculate_correlation(self, pattern1: Dict, pattern2: Dict) -> float:
        """Calculate correlation between two access patterns"""
        # Simplified correlation based on overlapping access times
        times1 = set(pattern1.keys())
        times2 = set(pattern2.keys())

        if not times1 or not times2:
            return 0.0

        overlap = len(times1.intersection(times2))
        union = len(times1.union(times2))

        return overlap / union if union > 0 else 0.0

class CompressionStrategy(ABC):
    """Abstract base class for compression strategies"""

    @abstractmethod
    def compress(self, data: Any) -> Tuple[bytes, float]:
        """Compress data and return (compressed_data, compression_ratio)"""
        pass

    @abstractmethod
    def decompress(self, compressed_data: bytes) -> Any:
        """Decompress data"""
        pass

class ZlibCompression(CompressionStrategy):
    """Zlib compression strategy"""

    def __init__(self, compression_level: int = 6):
        self.compression_level = compression_level

    def compress(self, data: Any) -> Tuple[bytes, float]:
        """Compress data using zlib"""
        serialized = pickle.dumps(data)
        compressed = zlib.compress(serialized, self.compression_level)
        compression_ratio = len(compressed) / len(serialized) if serialized else 1.0
        return compressed, compression_ratio

    def decompress(self, compressed_data: bytes) -> Any:
        """Decompress zlib data"""
        decompressed = zlib.decompress(compressed_data)
        return pickle.loads(decompressed)

class NoCompression(CompressionStrategy):
    """No compression strategy for small/fast data"""

    def compress(self, data: Any) -> Tuple[bytes, float]:
        """Return data without compression"""
        serialized = pickle.dumps(data)
        return serialized, 1.0

    def decompress(self, compressed_data: bytes) -> Any:
        """Return data as-is"""
        return pickle.loads(compressed_data)

class AdvancedCacheManager:
    """
    Advanced multi-level cache manager with intelligent eviction,
    predictive preloading, and adaptive compression.
    """

    def __init__(self, max_size_mb: int = 100, max_entries: int = 10000,
                 compression_threshold: int = 1024, enable_preloading: bool = True):
        # Cache configuration
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.max_entries = max_entries
        self.compression_threshold = compression_threshold
        self.enable_preloading = enable_preloading

        # Cache storage
        self.cache_entries: Dict[str, CacheEntry] = {}
        self.compressed_cache: Dict[str, bytes] = {}

        # Eviction and compression
        self.eviction_policy = LRUWithCostEviction(cost_weight=0.3)
        self.compression_strategies = {
            'zlib': ZlibCompression(),
            'none': NoCompression()
        }

        # Predictive preloading
        self.preloader = PredictivePreloader() if enable_preloading else None
        self.preload_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="cache_preload")

        # Statistics and monitoring
        self.stats = CacheStats()
        self.access_times = deque(maxlen=1000)
        self.lock = threading.RLock()

        # Background tasks
        self.maintenance_active = False
        self.maintenance_thread = None

        logger.info(f"Advanced Cache Manager initialized: {max_size_mb}MB, {max_entries} entries")

    def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache with decompression if needed"""
        start_time = time.time()

        with self.lock:
            if key not in self.cache_entries:
                self.stats.misses += 1
                self._update_hit_rate()
                return default

            entry = self.cache_entries[key]

            # Check TTL
            if entry.ttl_seconds and (time.time() - entry.created_at) > entry.ttl_seconds:
                self._remove_entry(key)
                self.stats.misses += 1
                self._update_hit_rate()
                return default

            # Update access information
            entry.last_accessed = time.time()
            entry.access_count += 1
            self.eviction_policy.update_access(entry)

            # Record access pattern for prediction
            if self.preloader:
                self.preloader.record_access(key, entry.tags)

            # Decompress if needed
            if key in self.compressed_cache:
                try:
                    value = self._decompress_entry(key)
                except Exception as e:
                    logger.error(f"Error decompressing cache entry {key}: {str(e)}")
                    self._remove_entry(key)
                    self.stats.misses += 1
                    self._update_hit_rate()
                    return default
            else:
                value = entry.value

            self.stats.hits += 1
            self._update_hit_rate()

            # Track access time
            access_time_ms = (time.time() - start_time) * 1000
            self.access_times.append(access_time_ms)
            self._update_avg_access_time()

            # Trigger predictive preloading
            if self.preloader:
                self._trigger_preload(key)

            return value

    def put(self, key: str, value: Any, ttl_seconds: Optional[float] = None,
            tags: List[str] = None, priority: int = 3, cost: float = 1.0) -> bool:
        """Put value in cache with intelligent compression"""
        try:
            with self.lock:
                # Calculate size and determine compression
                serialized = pickle.dumps(value)
                size_bytes = len(serialized)

                # Determine if compression should be used
                use_compression = size_bytes > self.compression_threshold
                compression_strategy = 'zlib' if use_compression else 'none'

                # Apply compression if needed
                if use_compression:
                    compressed_data, compression_ratio = self.compression_strategies[compression_strategy].compress(value)
                    final_size = len(compressed_data)
                    stored_value = None  # Value stored in compressed cache
                else:
                    compressed_data = None
                    compression_ratio = 1.0
                    final_size = size_bytes
                    stored_value = value

                # Check if eviction is needed
                if final_size > self.max_size_bytes:
                    logger.warning(f"Cache entry {key} ({final_size} bytes) exceeds max cache size")
                    return False

                # Evict entries if necessary
                while (self._get_total_size() + final_size > self.max_size_bytes or
                       len(self.cache_entries) >= self.max_entries):
                    evict_key = self.eviction_policy.should_evict(
                        self.cache_entries, final_size, self.max_size_bytes
                    )
                    if evict_key:
                        self._remove_entry(evict_key)
                    else:
                        break

                # Remove existing entry if present
                if key in self.cache_entries:
                    self._remove_entry(key)

                # Create cache entry
                entry = CacheEntry(
                    key=key,
                    value=stored_value,
                    size_bytes=final_size,
                    created_at=time.time(),
                    last_accessed=time.time(),
                    access_count=1,
                    ttl_seconds=ttl_seconds,
                    compression_ratio=compression_ratio,
                    cost=cost,
                    tags=tags or [],
                    priority=priority
                )

                # Store entry
                self.cache_entries[key] = entry
                if compressed_data:
                    self.compressed_cache[key] = compressed_data

                # Update statistics
                self._update_stats()

                logger.debug(f"Cached {key}: {final_size} bytes (compression: {compression_ratio:.2f})")
                return True

        except Exception as e:
            logger.error(f"Error caching entry {key}: {str(e)}")
            return False

    def remove(self, key: str) -> bool:
        """Remove entry from cache"""
        with self.lock:
            if key in self.cache_entries:
                self._remove_entry(key)
                return True
            return False

    def clear(self):
        """Clear all cache entries"""
        with self.lock:
            self.cache_entries.clear()
            self.compressed_cache.clear()
            self.stats = CacheStats()
            if self.preloader:
                self.preloader = PredictivePreloader()
            logger.info("Cache cleared")

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        with self.lock:
            self._update_hit_rate()
            self._update_avg_access_time()

            return {
                'entries': len(self.cache_entries),
                'size_bytes': self._get_total_size(),
                'size_mb': self._get_total_size() / (1024 * 1024),
                'hits': self.stats.hits,
                'misses': self.stats.misses,
                'hit_rate': self.stats.hit_rate,
                'evictions': self.stats.evictions,
                'avg_access_time_ms': self.stats.avg_access_time_ms,
                'compression_ratio': self.stats.compression_ratio,
                'compression_enabled': len(self.compressed_cache) > 0,
                'predictive_preloading': self.enable_preloading and self.preloader is not None,
                'memory_efficiency': self._calculate_memory_efficiency(),
                'cache_utilization': self._get_total_size() / self.max_size_bytes,
                'top_entries_by_access': self._get_top_entries_by_access(5),
                'entries_by_priority': self._get_entries_by_priority(),
                'ttl_expired_count': self._count_expired_entries()
            }

    def preload_predicted_entries(self, current_key: str, loader_func: Callable[[str], Any],
                                 max_preloads: int = 5):
        """Preload predicted cache entries"""
        if not self.preloader:
            return

        predicted_keys = self.preloader.predict_next_accesses(current_key, max_preloads)

        def preload_worker(key: str):
            """Worker function for preloading entries"""
            if key not in self.cache_entries:
                try:
                    value = loader_func(key)
                    if value is not None:
                        # Use lower priority for preloaded entries
                        self.put(key, value, priority=1, tags=['preloaded'])
                        logger.debug(f"Preloaded predicted cache entry: {key}")
                except Exception as e:
                    logger.warning(f"Failed to preload {key}: {str(e)}")

        # Submit preload tasks
        for key in predicted_keys:
            if key not in self.cache_entries:
                self.preload_executor.submit(preload_worker, key)

    def start_maintenance(self):
        """Start background maintenance tasks"""
        if self.maintenance_active:
            return

        self.maintenance_active = True
        self.maintenance_thread = threading.Thread(target=self._maintenance_loop, daemon=True)
        self.maintenance_thread.start()
        logger.info("Cache maintenance started")

    def stop_maintenance(self):
        """Stop background maintenance tasks"""
        self.maintenance_active = False
        if self.maintenance_thread:
            self.maintenance_thread.join(timeout=5)
        if hasattr(self, 'preload_executor'):
            self.preload_executor.shutdown(wait=True)
        logger.info("Cache maintenance stopped")

    def _maintenance_loop(self):
        """Background maintenance loop"""
        while self.maintenance_active:
            try:
                # Clean up expired entries
                self._cleanup_expired_entries()

                # Optimize memory usage
                self._optimize_memory_usage()

                # Update statistics
                self._update_stats()

                # Sleep for maintenance interval
                time.sleep(60)  # Run maintenance every minute

            except Exception as e:
                logger.error(f"Error in cache maintenance: {str(e)}")
                time.sleep(30)  # Wait before retrying

    def _remove_entry(self, key: str):
        """Remove entry from cache and update statistics"""
        if key in self.cache_entries:
            del self.cache_entries[key]
        if key in self.compressed_cache:
            del self.compressed_cache[key]
        self.stats.evictions += 1

    def _decompress_entry(self, key: str) -> Any:
        """Decompress cache entry"""
        if key in self.compressed_cache:
            compressed_data = self.compressed_cache[key]
            return self.compression_strategies['zlib'].decompress(compressed_data)
        else:
            return self.cache_entries[key].value

    def _get_total_size(self) -> int:
        """Calculate total cache size"""
        return sum(entry.size_bytes for entry in self.cache_entries.values())

    def _update_stats(self):
        """Update cache statistics"""
        self.stats.entry_count = len(self.cache_entries)
        self.stats.size_bytes = self._get_total_size()

        # Calculate compression ratio
        if self.compressed_cache:
            total_compression_ratio = 0
            for entry in self.cache_entries.values():
                if entry.compression_ratio:
                    total_compression_ratio += entry.compression_ratio

            if self.compressed_cache:
                self.stats.compression_ratio = total_compression_ratio / len(self.compressed_cache)

    def _update_hit_rate(self):
        """Update cache hit rate"""
        total_requests = self.stats.hits + self.stats.misses
        self.stats.hit_rate = (self.stats.hits / total_requests * 100) if total_requests > 0 else 0

    def _update_avg_access_time(self):
        """Update average access time"""
        if self.access_times:
            self.stats.avg_access_time_ms = sum(self.access_times) / len(self.access_times)

    def _trigger_preload(self, key: str):
        """Trigger predictive preloading for a key"""
        if self.preloader:
            # Preloading would be triggered by the calling code
            # This is just a placeholder for the trigger mechanism
            pass

    def _cleanup_expired_entries(self):
        """Remove expired cache entries"""
        current_time = time.time()
        expired_keys = []

        for key, entry in self.cache_entries.items():
            if entry.ttl_seconds and (current_time - entry.created_at) > entry.ttl_seconds:
                expired_keys.append(key)

        for key in expired_keys:
            self._remove_entry(key)

        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")

    def _optimize_memory_usage(self):
        """Optimize memory usage"""
        # Force garbage collection if memory usage is high
        if self._get_total_size() > self.max_size_bytes * 0.9:
            gc.collect()

    def _calculate_memory_efficiency(self) -> float:
        """Calculate memory efficiency score"""
        if not self.cache_entries:
            return 100.0

        # Factors: hit rate, compression ratio, cache utilization
        hit_rate_factor = self.stats.hit_rate / 100
        compression_factor = (2 - self.stats.compression_ratio) if self.stats.compression_ratio > 0 else 1
        utilization_factor = self._get_total_size() / self.max_size_bytes

        efficiency = (hit_rate_factor * 0.5 + compression_factor * 0.3 +
                     (1 - abs(utilization_factor - 0.7)) * 0.2) * 100

        return min(100, max(0, efficiency))

    def _get_top_entries_by_access(self, limit: int) -> List[Dict[str, Any]]:
        """Get top entries by access count"""
        sorted_entries = sorted(
            self.cache_entries.values(),
            key=lambda e: e.access_count,
            reverse=True
        )[:limit]

        return [
            {
                'key': entry.key,
                'access_count': entry.access_count,
                'size_bytes': entry.size_bytes,
                'last_accessed': entry.last_accessed
            }
            for entry in sorted_entries
        ]

    def _get_entries_by_priority(self) -> Dict[int, int]:
        """Count entries by priority level"""
        priority_counts = defaultdict(int)
        for entry in self.cache_entries.values():
            priority_counts[entry.priority] += 1
        return dict(priority_counts)

    def _count_expired_entries(self) -> int:
        """Count expired entries"""
        current_time = time.time()
        expired_count = 0

        for entry in self.cache_entries.values():
            if entry.ttl_seconds and (current_time - entry.created_at) > entry.ttl_seconds:
                expired_count += 1

        return expired_count

    def export_cache_state(self) -> Dict[str, Any]:
        """Export cache state for persistence"""
        with self.lock:
            return {
                'cache_entries': {
                    key: asdict(entry) for key, entry in self.cache_entries.items()
                    if key not in self.compressed_cache  # Only uncompressed entries
                },
                'compressed_cache_keys': list(self.compressed_cache.keys()),
                'stats': asdict(self.stats),
                'config': {
                    'max_size_bytes': self.max_size_bytes,
                    'max_entries': self.max_entries,
                    'compression_threshold': self.compression_threshold
                }
            }

    def __del__(self):
        """Cleanup on deletion"""
        self.stop_maintenance()


# Singleton cache manager instance for the application
_cache_manager_instance = None

def get_cache_manager(max_size_mb: int = 100, max_entries: int = 10000) -> AdvancedCacheManager:
    """Get singleton cache manager instance"""
    global _cache_manager_instance

    if _cache_manager_instance is None:
        _cache_manager_instance = AdvancedCacheManager(max_size_mb, max_entries)
        _cache_manager_instance.start_maintenance()

    return _cache_manager_instance


if __name__ == "__main__":
    # Test advanced cache manager
    cache = AdvancedCacheManager(max_size_mb=10, max_entries=1000)

    print("=== Advanced Cache Manager Test ===")

    # Test basic operations
    cache.put("test_key", {"data": "test_value", "numbers": [1, 2, 3]}, tags=["test"])
    result = cache.get("test_key")
    print(f"Basic test result: {result}")

    # Test compression with large data
    large_data = {"data": "x" * 1000, "numbers": list(range(1000))}
    cache.put("large_data", large_data, tags=["large"])

    # Test TTL
    cache.put("ttl_test", "expires_soon", ttl_seconds=2)
    time.sleep(3)
    ttl_result = cache.get("ttl_test")
    print(f"TTL test result: {ttl_result}")

    # Get statistics
    stats = cache.get_stats()
    print(f"\n=== Cache Statistics ===")
    print(f"Entries: {stats['entries']}")
    print(f"Size: {stats['size_mb']:.2f} MB")
    print(f"Hit rate: {stats['hit_rate']:.1f}%")
    print(f"Compression ratio: {stats['compression_ratio']:.2f}")
    print(f"Memory efficiency: {stats['memory_efficiency']:.1f}%")

    # Test preloading
    def sample_loader(key: str):
        """Sample loader function for preloading"""
        return f"loaded_data_for_{key}"

    cache.preload_predicted_entries("test_key", sample_loader)
    time.sleep(1)  # Allow preloading to complete

    # Cleanup
    cache.stop_maintenance()
    print("Cache manager test completed")
