"""
Hierarchical Memory Manager for Super AI Agent Architecture

Implements 4-level memory hierarchy:
- Level 1: Meta Agent Memory (Persistent)
- Level 2: Orchestrator Memory (Session)
- Level 3: Agent Memory (Ephemeral)
- Level 4: Cache Memory (Temporary)
"""

import json
import time
import os
import sqlite3
import pickle
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from enum import Enum
import logging
import threading
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MemoryLevel(Enum):
    """Memory hierarchy levels"""
    META_AGENT = 1      # Persistent - system state, agent registry, performance metrics
    ORCHESTRATOR = 2    # Session - active plans, task queues, agent assignments
    AGENT = 3           # Ephemeral - task-specific context, intermediate results
    CACHE = 4           # Temporary - CFBD API responses, model predictions, TOON outputs

@dataclass
class MemoryEntry:
    """Represents a memory entry with metadata"""
    key: str
    value: Any
    level: MemoryLevel
    timestamp: datetime
    expires_at: Optional[datetime]
    access_count: int
    size_bytes: int
    tags: List[str]
    agent_id: Optional[str] = None

@dataclass
class MemoryStats:
    """Memory usage statistics"""
    total_entries: int
    total_size_mb: float
    level_stats: Dict[MemoryLevel, Dict[str, Any]]
    hit_rate: float
    eviction_count: int
    compression_ratio: float

class HierarchicalMemoryManager:
    """
    Advanced hierarchical memory management system.

    Features:
    - 4-level memory hierarchy with different retention policies
    - Automatic eviction and compression
    - Thread-safe operations with concurrent access
    - Performance monitoring and statistics
    - Memory usage optimization and cleanup
    """

    def __init__(self, config_path: str = "config/claude_code_optimization.json"):
        """Initialize the hierarchical memory manager"""
        self.config = self._load_config(config_path)
        self.lock = threading.RLock()
        self.executor = ThreadPoolExecutor(max_workers=4)

        # Memory storage by level
        self.memory_stores = {
            MemoryLevel.META_AGENT: {},
            MemoryLevel.ORCHESTRATOR: {},
            MemoryLevel.AGENT: {},
            MemoryLevel.CACHE: {}
        }

        # Performance tracking
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "compressions": 0,
            "level_stats": {
                level: {"entries": 0, "size_bytes": 0, "accesses": 0}
                for level in MemoryLevel
            }
        }

        # Initialize storage directories
        self._initialize_storage()

        # Start background cleanup thread
        self._start_cleanup_thread()

        logger.info("HierarchicalMemoryManager initialized successfully")

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load memory configuration from JSON file"""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            return config.get("memory_hierarchy", {})
        except (FileNotFoundError, json.JSONDecodeError):
            logger.warning("Using default memory configuration")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default memory configuration"""
        return {
            "level_1_meta_agent": {
                "max_size_mb": 100,
                "retention_days": 365
            },
            "level_2_orchestrators": {
                "max_size_mb": 50,
                "retention_hours": 24
            },
            "level_3_agents": {
                "max_size_mb": 20,
                "retention_minutes": 60
            },
            "level_4_cache": {
                "max_size_mb": 200,
                "ttl_minutes": {
                    "cfbd_api_responses": 60,
                    "model_predictions": 1440,
                    "toon_outputs": 30
                }
            }
        }

    def _initialize_storage(self):
        """Initialize storage directories and database"""
        # Create storage directories
        for level_name, level_config in self.config.items():
            if "storage_path" in level_config:
                Path(level_config["storage_path"]).mkdir(parents=True, exist_ok=True)

        # Initialize SQLite database for metadata
        self.db_path = "project_management/memory/memory_metadata.db"
        self._init_database()

    def _init_database(self):
        """Initialize SQLite database for memory metadata"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memory_entries (
                    key TEXT PRIMARY KEY,
                    level INTEGER,
                    timestamp TEXT,
                    expires_at TEXT,
                    access_count INTEGER,
                    size_bytes INTEGER,
                    tags TEXT,
                    agent_id TEXT,
                    file_path TEXT
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS memory_stats (
                    level INTEGER,
                    entries INTEGER,
                    size_bytes INTEGER,
                    accesses INTEGER,
                    last_updated TEXT,
                    PRIMARY KEY (level)
                )
            """)

    def store(self, key: str, value: Any, level: MemoryLevel,
              expires_in: Optional[timedelta] = None,
              tags: List[str] = None, agent_id: str = None) -> bool:
        """
        Store a value in the specified memory level

        Args:
            key: Unique key for the memory entry
            value: Value to store
            level: Memory level to store in
            expires_in: Time until expiration (optional)
            tags: List of tags for categorization
            agent_id: ID of the agent storing the memory

        Returns:
            True if stored successfully, False otherwise
        """
        try:
            with self.lock:
                # Check if we need to evict entries
                self._check_storage_limits(level)

                # Create memory entry
                entry = MemoryEntry(
                    key=key,
                    value=value,
                    level=level,
                    timestamp=datetime.now(),
                    expires_at=datetime.now() + expires_in if expires_in else None,
                    access_count=0,
                    size_bytes=self._calculate_size(value),
                    tags=tags or [],
                    agent_id=agent_id
                )

                # Store in memory
                self.memory_stores[level][key] = entry

                # Update statistics
                self._update_stats(level, "store", entry.size_bytes)

                # Persist to disk if needed
                if self._should_persist(level):
                    self._persist_entry(entry)

                logger.debug(f"Stored {key} in {level.name} memory")
                return True

        except Exception as e:
            logger.error(f"Error storing {key} in {level.name}: {e}")
            return False

    def retrieve(self, key: str, level: Optional[MemoryLevel] = None) -> Optional[Any]:
        """
        Retrieve a value from memory

        Args:
            key: Key of the memory entry
            level: Specific level to search (optional, searches all levels if None)

        Returns:
            The stored value or None if not found
        """
        try:
            with self.lock:
                # Search in specified level or all levels
                search_levels = [level] if level else list(MemoryLevel)

                for search_level in search_levels:
                    if key in self.memory_stores[search_level]:
                        entry = self.memory_stores[search_level][key]

                        # Check if expired
                        if entry.expires_at and datetime.now() > entry.expires_at:
                            self._evict_entry(search_level, key)
                            continue

                        # Update access statistics
                        entry.access_count += 1
                        self.stats["hits"] += 1
                        self.stats["level_stats"][search_level]["accesses"] += 1

                        logger.debug(f"Retrieved {key} from {search_level.name} memory")
                        return entry.value

                # Try to load from disk if not in memory
                if not level:
                    return self._load_from_disk(key)

                self.stats["misses"] += 1
                return None

        except Exception as e:
            logger.error(f"Error retrieving {key}: {e}")
            self.stats["misses"] += 1
            return None

    def delete(self, key: str, level: Optional[MemoryLevel] = None) -> bool:
        """
        Delete a memory entry

        Args:
            key: Key of the memory entry
            level: Specific level to delete from (optional, searches all levels if None)

        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            with self.lock:
                deleted = False

                if level:
                    if key in self.memory_stores[level]:
                        entry = self.memory_stores[level].pop(key)
                        self._update_stats(level, "delete", entry.size_bytes)
                        deleted = True
                else:
                    # Search all levels
                    for search_level in MemoryLevel:
                        if key in self.memory_stores[search_level]:
                            entry = self.memory_stores[search_level].pop(key)
                            self._update_stats(search_level, "delete", entry.size_bytes)
                            deleted = True
                            break

                if deleted:
                    self._delete_from_disk(key)
                    logger.debug(f"Deleted {key} from memory")

                return deleted

        except Exception as e:
            logger.error(f"Error deleting {key}: {e}")
            return False

    def cleanup_expired(self) -> int:
        """Clean up expired memory entries"""
        expired_count = 0
        current_time = datetime.now()

        with self.lock:
            for level, store in self.memory_stores.items():
                expired_keys = [
                    key for key, entry in store.items()
                    if entry.expires_at and current_time > entry.expires_at
                ]

                for key in expired_keys:
                    self._evict_entry(level, key)
                    expired_count += 1

        logger.info(f"Cleaned up {expired_count} expired entries")
        return expired_count

    def get_stats(self) -> MemoryStats:
        """Get comprehensive memory statistics"""
        with self.lock:
            total_entries = sum(len(store) for store in self.memory_stores.values())
            total_size_mb = sum(
                sum(entry.size_bytes for entry in store.values())
                for store in self.memory_stores.values()
            ) / (1024 * 1024)

            level_stats = {}
            for level in MemoryLevel:
                store = self.memory_stores[level]
                level_stats[level] = {
                    "entries": len(store),
                    "size_mb": sum(entry.size_bytes for entry in store.values()) / (1024 * 1024),
                    "accesses": self.stats["level_stats"][level]["accesses"],
                    "avg_access_count": sum(entry.access_count for entry in store.values()) / max(1, len(store))
                }

            hit_rate = self.stats["hits"] / max(1, self.stats["hits"] + self.stats["misses"])

            return MemoryStats(
                total_entries=total_entries,
                total_size_mb=total_size_mb,
                level_stats=level_stats,
                hit_rate=hit_rate,
                eviction_count=self.stats["evictions"],
                compression_ratio=self.stats["compressions"] / max(1, total_entries)
            )

    def search_by_tags(self, tags: List[str], level: Optional[MemoryLevel] = None) -> List[MemoryEntry]:
        """
        Search memory entries by tags

        Args:
            tags: List of tags to search for
            level: Specific level to search (optional)

        Returns:
            List of matching memory entries
        """
        results = []
        search_levels = [level] if level else list(MemoryLevel)

        with self.lock:
            for search_level in search_levels:
                for entry in self.memory_stores[search_level].values():
                    if any(tag in entry.tags for tag in tags):
                        results.append(entry)

        return sorted(results, key=lambda x: x.access_count, reverse=True)

    def get_agent_memory(self, agent_id: str) -> Dict[str, Any]:
        """Get all memory entries for a specific agent"""
        agent_memory = {}

        with self.lock:
            for level, store in self.memory_stores.items():
                agent_memory[level.name] = {
                    key: entry.value for key, entry in store.items()
                    if entry.agent_id == agent_id
                }

        return agent_memory

    def compress_memory(self, level: MemoryLevel) -> int:
        """Compress memory entries in the specified level"""
        compressed_count = 0

        with self.lock:
            for key, entry in self.memory_stores[level].items():
                if self._should_compress(entry):
                    # Apply compression (simplified - would use actual compression)
                    compressed_value = self._compress_value(entry.value)
                    entry.value = compressed_value
                    entry.size_bytes = self._calculate_size(compressed_value)
                    compressed_count += 1
                    self.stats["compressions"] += 1

        logger.info(f"Compressed {compressed_count} entries in {level.name}")
        return compressed_count

    def _check_storage_limits(self, level: MemoryLevel):
        """Check and enforce storage limits for a level"""
        level_config = self._get_level_config(level)
        if not level_config:
            return

        current_size = sum(entry.size_bytes for entry in self.memory_stores[level].values())
        max_size_bytes = level_config.get("max_size_mb", 50) * 1024 * 1024

        if current_size > max_size_bytes:
            # Evict least recently used entries
            self._evict_lru(level, current_size - max_size_bytes)

    def _evict_lru(self, level: MemoryLevel, bytes_to_free: int):
        """Evict least recently used entries to free space"""
        entries = sorted(
            self.memory_stores[level].items(),
            key=lambda x: (x[1].access_count, x[1].timestamp)
        )

        bytes_freed = 0
        for key, entry in entries:
            if bytes_freed >= bytes_to_free:
                break

            self._evict_entry(level, key)
            bytes_freed += entry.size_bytes
            self.stats["evictions"] += 1

    def _evict_entry(self, level: MemoryLevel, key: str):
        """Evict a specific entry from memory"""
        if key in self.memory_stores[level]:
            entry = self.memory_stores[level].pop(key)
            self._update_stats(level, "delete", entry.size_bytes)
            self._delete_from_disk(key)

    def _should_persist(self, level: MemoryLevel) -> bool:
        """Check if entries in a level should be persisted to disk"""
        return level in [MemoryLevel.META_AGENT, MemoryLevel.ORCHESTRATOR]

    def _persist_entry(self, entry: MemoryEntry):
        """Persist a memory entry to disk"""
        try:
            level_config = self._get_level_config(entry.level)
            if not level_config or "storage_path" not in level_config:
                return

            storage_path = Path(level_config["storage_path"])
            filename = f"{entry.key}.pkl"
            file_path = storage_path / filename

            # Serialize and save
            with open(file_path, 'wb') as f:
                pickle.dump(entry.value, f)

            # Update database metadata
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO memory_entries
                    (key, level, timestamp, expires_at, access_count, size_bytes, tags, agent_id, file_path)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    entry.key,
                    entry.level.value,
                    entry.timestamp.isoformat(),
                    entry.expires_at.isoformat() if entry.expires_at else None,
                    entry.access_count,
                    entry.size_bytes,
                    json.dumps(entry.tags),
                    entry.agent_id,
                    str(file_path)
                ))

        except Exception as e:
            logger.error(f"Error persisting entry {entry.key}: {e}")

    def _load_from_disk(self, key: str) -> Optional[Any]:
        """Load a memory entry from disk"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT level, file_path FROM memory_entries WHERE key = ?
                """, (key,))

                row = cursor.fetchone()
                if row:
                    level_value, file_path = row
                    level = MemoryLevel(level_value)

                    if os.path.exists(file_path):
                        with open(file_path, 'rb') as f:
                            value = pickle.load(f)

                        # Load back into memory
                        self.memory_stores[level][key] = MemoryEntry(
                            key=key,
                            value=value,
                            level=level,
                            timestamp=datetime.now(),
                            expires_at=None,
                            access_count=1,
                            size_bytes=self._calculate_size(value),
                            tags=[],
                            agent_id=None
                        )

                        logger.debug(f"Loaded {key} from disk")
                        return value

        except Exception as e:
            logger.error(f"Error loading {key} from disk: {e}")

        return None

    def _delete_from_disk(self, key: str):
        """Delete a memory entry from disk"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT file_path FROM memory_entries WHERE key = ?
                """, (key,))

                row = cursor.fetchone()
                if row:
                    file_path = row[0]
                    if os.path.exists(file_path):
                        os.remove(file_path)

                conn.execute("DELETE FROM memory_entries WHERE key = ?", (key,))

        except Exception as e:
            logger.error(f"Error deleting {key} from disk: {e}")

    def _update_stats(self, level: MemoryLevel, operation: str, size_bytes: int):
        """Update memory statistics"""
        level_stats = self.stats["level_stats"][level]

        if operation == "store":
            level_stats["entries"] += 1
            level_stats["size_bytes"] += size_bytes
        elif operation == "delete":
            level_stats["entries"] = max(0, level_stats["entries"] - 1)
            level_stats["size_bytes"] = max(0, level_stats["size_bytes"] - size_bytes)

    def _get_level_config(self, level: MemoryLevel) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific memory level"""
        level_mapping = {
            MemoryLevel.META_AGENT: "level_1_meta_agent",
            MemoryLevel.ORCHESTRATOR: "level_2_orchestrators",
            MemoryLevel.AGENT: "level_3_agents",
            MemoryLevel.CACHE: "level_4_cache"
        }
        return self.config.get(level_mapping.get(level.name.lower()))

    def _calculate_size(self, value: Any) -> int:
        """Calculate the size of a value in bytes"""
        return len(pickle.dumps(value))

    def _should_compress(self, entry: MemoryEntry) -> bool:
        """Check if an entry should be compressed"""
        # Simple heuristic - compress entries larger than 1KB
        return entry.size_bytes > 1024

    def _compress_value(self, value: Any) -> Any:
        """Compress a value (simplified implementation)"""
        # In a real implementation, this would use actual compression algorithms
        return {"compressed": True, "data": value}

    def _start_cleanup_thread(self):
        """Start background cleanup thread"""
        def cleanup_worker():
            while True:
                try:
                    time.sleep(300)  # Run every 5 minutes
                    self.cleanup_expired()
                except Exception as e:
                    logger.error(f"Error in cleanup thread: {e}")

        cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        cleanup_thread.start()

# Global memory manager instance
memory_manager = HierarchicalMemoryManager()