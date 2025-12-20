#!/usr/bin/env python3
"""
Multi-Level Memory System for Script Ohio 2.0

Advanced hierarchical memory management with working, episodic, and semantic layers.
Provides intelligent caching, context management, and knowledge retention.

Memory Architecture:
- Working Memory: Current context and session state (transient)
- Episodic Memory: Experience storage and similarity search (session-based)
- Semantic Memory: Knowledge graphs and documentation (persistent)
- Meta-Memory: Orchestration and consolidation

Features:
- Vector-based similarity search
- Automatic consolidation and forgetting
- Context-aware memory retrieval
- Cross-layer memory transfer
- Performance optimization with caching
"""

import os
import sys
import json
import time
import hashlib
import pickle
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import numpy as np

# Vector storage and similarity
try:
    from sentence_transformers import SentenceTransformer
    import faiss

    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    print(
        "⚠️  Sentence transformers and FAISS not available. Memory will use basic similarity."
    )

# ChromaDB for persistent vector storage
try:
    import chromadb
    from chromadb.config import Settings

    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    print("⚠️  ChromaDB not available. Using file-based storage.")


class MemoryLevel(Enum):
    """Memory hierarchy levels"""

    WORKING = "working"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    META = "meta"


class MemoryType(Enum):
    """Types of memory entries"""

    CONTEXT = "context"
    EXPERIENCE = "experience"
    KNOWLEDGE = "knowledge"
    PROCEDURE = "procedure"
    REFLECTION = "reflection"


@dataclass
class MemoryEntry:
    """Universal memory entry structure"""

    id: str
    level: MemoryLevel
    memory_type: MemoryType
    content: Any
    metadata: Dict[str, Any]
    timestamp: datetime
    embedding: Optional[np.ndarray] = None
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    importance_score: float = 0.0
    expires_at: Optional[datetime] = None


@dataclass
class MemoryQuery:
    """Memory search query"""

    query_text: str
    memory_level: MemoryLevel
    memory_types: List[MemoryType]
    limit: int = 10
    min_similarity: float = 0.3
    filters: Dict[str, Any] = None


@dataclass
class MemoryStats:
    """Memory system statistics"""

    total_entries: int
    working_memory_entries: int
    episodic_memory_entries: int
    semantic_memory_entries: int
    cache_hit_rate: float
    average_query_time: float
    consolidation_cycles: int
    last_cleanup: datetime


class HierarchicalMemoryManager:
    """
    Advanced hierarchical memory system

    Manages multiple memory layers with intelligent retrieval,
    consolidation, and optimization.
    """

    def __init__(
        self,
        storage_path: str = "./memory",
        max_working_size: int = 1000,
        max_episodic_size: int = 10000,
    ):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        self.max_working_size = max_working_size
        self.max_episodic_size = max_episodic_size

        self.logger = self._setup_logging()

        # Memory stores
        self.working_memory = {}  # Current session context
        self.episodic_memory = {}  # Experiences
        self.semantic_memory = {}  # Knowledge and documentation

        # Vector stores
        self._initialize_vector_stores()

        # Performance metrics
        self.stats = MemoryStats(
            total_entries=0,
            working_memory_entries=0,
            episodic_memory_entries=0,
            semantic_memory_entries=0,
            cache_hit_rate=0.0,
            average_query_time=0.0,
            consolidation_cycles=0,
            last_cleanup=datetime.utcnow(),
        )

        # Background processes
        self._consolidation_thread = None
        self._cleanup_thread = None
        self._running = True

        # Initialize background processes
        self._start_background_processes()

        self.logger.info("🧠 Hierarchical Memory System initialized")

    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger("memory_manager")

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)

        return logger

    def _initialize_vector_stores(self) -> None:
        """Initialize vector similarity stores"""
        try:
            if EMBEDDINGS_AVAILABLE:
                self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
                self.logger.info("✅ Sentence embeddings initialized")
            else:
                self.embedding_model = None
                self.logger.info("⚠️  Using text-based similarity")

            # Initialize FAISS indexes
            if EMBEDDINGS_AVAILABLE:
                self.working_index = faiss.IndexFlatL2(384)  # MiniLM dimension
                self.episodic_index = faiss.IndexFlatL2(384)
                self.semantic_index = faiss.IndexFlatL2(384)
                self.logger.info("✅ FAISS indexes initialized")
            else:
                self.working_index = None
                self.episodic_index = None
                self.semantic_index = None

            # Initialize ChromaDB if available
            if CHROMADB_AVAILABLE:
                self.chroma_client = chromadb.PersistentClient(
                    path=str(self.storage_path / "chroma")
                )
                self.logger.info("✅ ChromaDB initialized")
            else:
                self.chroma_client = None

        except Exception as e:
            self.logger.error(f"❌ Vector store initialization failed: {e}")
            self.embedding_model = None
            self.working_index = None
            self.episodic_index = None
            self.semantic_index = None
            self.chroma_client = None

    def store(
        self,
        content: Any,
        memory_level: MemoryLevel,
        memory_type: MemoryType,
        metadata: Optional[Dict[str, Any]] = None,
        expires_in: Optional[int] = None,
        tags: Optional[List[str]] = None,
    ) -> str:
        """
        Store content in specified memory level

        Args:
            content: Content to store
            memory_level: Target memory level
            memory_type: Type of memory entry
            metadata: Additional metadata
            expires_in: Time to expiration in seconds
            tags: Tags for organization

        Returns:
            Memory entry ID
        """
        try:
            # Generate unique ID
            entry_id = hashlib.md5(
                f"{memory_level.value}_{memory_type.value}_{time.time()}_{str(content)[:100]}".encode()
            ).hexdigest()[:16]

            # Create memory entry
            entry = MemoryEntry(
                id=entry_id,
                level=memory_level,
                memory_type=memory_type,
                content=content,
                metadata=metadata or {},
                timestamp=datetime.utcnow(),
                importance_score=self._calculate_importance(content, metadata),
                expires_at=(
                    datetime.utcnow() + timedelta(seconds=expires_in)
                    if expires_in
                    else None
                ),
            )

            # Generate embedding if content is text
            if self.embedding_model and isinstance(content, str):
                try:
                    entry.embedding = self.embedding_model.encode(content)
                except Exception as e:
                    self.logger.debug(f"Could not generate embedding: {e}")

            # Store in appropriate memory level
            if memory_level == MemoryLevel.WORKING:
                self._store_in_working_memory(entry)
            elif memory_level == MemoryLevel.EPISODIC:
                self._store_in_episodic_memory(entry)
            elif memory_level == MemoryLevel.SEMANTIC:
                self._store_in_semantic_memory(entry)

            # Update vector index
            self._update_vector_index(entry)

            # Update stats
            self._update_stats()

            self.logger.debug(
                f"📝 Stored {memory_type.value} in {memory_level.value} memory: {entry_id}"
            )
            return entry_id

        except Exception as e:
            self.logger.error(f"❌ Failed to store memory: {e}")
            return ""

    def retrieve(self, query: MemoryQuery) -> List[MemoryEntry]:
        """
        Retrieve memories based on query

        Args:
            query: Memory search query

        Returns:
            List of matching memory entries
        """
        start_time = time.time()

        try:
            results = []

            # Get entries from specified memory level
            if query.memory_level == MemoryLevel.WORKING:
                candidates = list(self.working_memory.values())
            elif query.memory_level == MemoryLevel.EPISODIC:
                candidates = list(self.episodic_memory.values())
            elif query.memory_level == MemoryLevel.SEMANTIC:
                candidates = list(self.semantic_memory.values())
            else:
                # Search all levels
                candidates = (
                    list(self.working_memory.values())
                    + list(self.episodic_memory.values())
                    + list(self.semantic_memory.values())
                )

            # Filter by memory types
            if query.memory_types:
                candidates = [
                    c for c in candidates if c.memory_type in query.memory_types
                ]

            # Apply additional filters
            if query.filters:
                candidates = self._apply_filters(candidates, query.filters)

            # Rank by similarity
            if query.query_text and self.embedding_model:
                results = self._rank_by_similarity(
                    candidates, query.query_text, query.min_similarity
                )
            else:
                # Sort by importance and recency
                results = sorted(
                    candidates,
                    key=lambda x: (x.importance_score, x.timestamp),
                    reverse=True,
                )

            # Limit results
            results = results[: query.limit]

            # Update access counts and times
            for entry in results:
                entry.access_count += 1
                entry.last_accessed = datetime.utcnow()

            # Update performance metrics
            query_time = time.time() - start_time
            self._update_query_performance(query_time)

            self.logger.debug(
                f"🔍 Retrieved {len(results)} entries in {query_time:.3f}s"
            )
            return results

        except Exception as e:
            self.logger.error(f"❌ Memory retrieval failed: {e}")
            return []

    def _store_in_working_memory(self, entry: MemoryEntry) -> None:
        """Store in working memory with size management"""
        # Check size limit
        if len(self.working_memory) >= self.max_working_size:
            self._evict_from_working_memory()

        self.working_memory[entry.id] = entry

    def _store_in_episodic_memory(self, entry: MemoryEntry) -> None:
        """Store in episodic memory"""
        # Check size limit
        if len(self.episodic_memory) >= self.max_episodic_size:
            self._evict_from_episodic_memory()

        self.episodic_memory[entry.id] = entry

        # Persist to disk
        self._persist_episodic_entry(entry)

    def _store_in_semantic_memory(self, entry: MemoryEntry) -> None:
        """Store in semantic memory"""
        self.semantic_memory[entry.id] = entry

        # Persist to disk
        self._persist_semantic_entry(entry)

    def _update_vector_index(self, entry: MemoryEntry) -> None:
        """Update vector similarity index"""
        if entry.embedding is None or not EMBEDDINGS_AVAILABLE:
            return

        try:
            if entry.level == MemoryLevel.WORKING and self.working_index:
                self.working_index.add(entry.embedding.reshape(1, -1))
            elif entry.level == MemoryLevel.EPISODIC and self.episodic_index:
                self.episodic_index.add(entry.embedding.reshape(1, -1))
            elif entry.level == MemoryLevel.SEMANTIC and self.semantic_index:
                self.semantic_index.add(entry.embedding.reshape(1, -1))

            # Also store in ChromaDB if available
            if self.chroma_client:
                self._store_in_chroma(entry)

        except Exception as e:
            self.logger.debug(f"Could not update vector index: {e}")

    def _rank_by_similarity(
        self, candidates: List[MemoryEntry], query_text: str, min_similarity: float
    ) -> List[MemoryEntry]:
        """Rank candidates by text similarity"""
        try:
            if self.embedding_model:
                # Generate query embedding
                query_embedding = self.embedding_model.encode(query_text)

                # Calculate similarities
                scored_entries = []
                for entry in candidates:
                    if entry.embedding is not None:
                        similarity = np.dot(entry.embedding, query_embedding) / (
                            np.linalg.norm(entry.embedding)
                            * np.linalg.norm(query_embedding)
                        )
                        if similarity >= min_similarity:
                            scored_entries.append((entry, similarity))

                # Sort by similarity
                scored_entries.sort(key=lambda x: x[1], reverse=True)
                return [entry for entry, _ in scored_entries]
            else:
                # Fallback to text similarity
                scored_entries = []
                for entry in candidates:
                    if isinstance(entry.content, str):
                        similarity = self._text_similarity(
                            query_text, str(entry.content)
                        )
                        if similarity >= min_similarity:
                            scored_entries.append((entry, similarity))

                scored_entries.sort(key=lambda x: x[1], reverse=True)
                return [entry for entry, _ in scored_entries]

        except Exception as e:
            self.logger.error(f"Similarity ranking failed: {e}")
            return candidates[:10]  # Fallback

    def _text_similarity(self, text1: str, text2: str) -> float:
        """Simple text similarity calculation"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        return len(intersection) / len(union) if union else 0.0

    def _calculate_importance(self, content: Any, metadata: Dict[str, Any]) -> float:
        """Calculate importance score for memory entry"""
        base_score = 0.5

        # Factor in metadata importance indicators
        if metadata:
            if metadata.get("importance") == "high":
                base_score += 0.3
            elif metadata.get("importance") == "critical":
                base_score += 0.5
            elif metadata.get("user_request"):
                base_score += 0.2
            elif metadata.get("error"):
                base_score += 0.1

        # Factor in content length (longer content often more important)
        if isinstance(content, str):
            length_score = min(len(content) / 1000, 0.3)  # Max 0.3 for length
            base_score += length_score

        return min(base_score, 1.0)

    def _evict_from_working_memory(self) -> None:
        """Evict least important entries from working memory"""
        if not self.working_memory:
            return

        # Sort by importance and last access
        entries = sorted(
            self.working_memory.items(),
            key=lambda x: (x[1].importance_score, x[1].last_accessed or x[1].timestamp),
        )

        # Remove least important 10%
        evict_count = max(1, len(self.working_memory) // 10)
        for i in range(evict_count):
            if i < len(entries):
                del self.working_memory[entries[i][0]]

    def _evict_from_episodic_memory(self) -> None:
        """Evict old entries from episodic memory"""
        if not self.episodic_memory:
            return

        cutoff_time = datetime.utcnow() - timedelta(days=30)  # 30 days

        to_remove = [
            entry_id
            for entry_id, entry in self.episodic_memory.items()
            if entry.timestamp < cutoff_time and entry.importance_score < 0.5
        ]

        for entry_id in to_remove:
            del self.episodic_memory[entry_id]

    def _apply_filters(
        self, candidates: List[MemoryEntry], filters: Dict[str, Any]
    ) -> List[MemoryEntry]:
        """Apply metadata filters to candidates"""
        filtered = candidates

        for key, value in filters.items():
            if key == "importance_min":
                filtered = [e for e in filtered if e.importance_score >= value]
            elif key == "importance_max":
                filtered = [e for e in filtered if e.importance_score <= value]
            elif key == "memory_type":
                if isinstance(value, list):
                    filtered = [e for e in filtered if e.memory_type in value]
                else:
                    filtered = [e for e in filtered if e.memory_type == value]
            elif key == "created_after":
                filtered = [e for e in filtered if e.timestamp >= value]
            elif key == "created_before":
                filtered = [e for e in filtered if e.timestamp <= value]

        return filtered

    def _start_background_processes(self) -> None:
        """Start background consolidation and cleanup processes"""
        self._consolidation_thread = threading.Thread(
            target=self._consolidation_worker, daemon=True
        )
        self._consolidation_thread.start()

        self._cleanup_thread = threading.Thread(
            target=self._cleanup_worker, daemon=True
        )
        self._cleanup_thread.start()

    def _consolidation_worker(self) -> None:
        """Background memory consolidation"""
        while self._running:
            try:
                time.sleep(3600)  # Run every hour

                # Consolidate working memory to episodic
                self._consolidate_working_to_episodic()

                # Consolidate episodic to semantic
                self._consolidate_episodic_to_semantic()

                self.stats.consolidation_cycles += 1
                self.logger.debug("🔄 Memory consolidation cycle completed")

            except Exception as e:
                self.logger.error(f"Consolidation error: {e}")

    def _cleanup_worker(self) -> None:
        """Background cleanup of expired entries"""
        while self._running:
            try:
                time.sleep(1800)  # Run every 30 minutes

                # Clean expired entries
                self._cleanup_expired_entries()

                # Optimize memory usage
                self._optimize_memory_usage()

                self.stats.last_cleanup = datetime.utcnow()
                self.logger.debug("🧹 Memory cleanup completed")

            except Exception as e:
                self.logger.error(f"Cleanup error: {e}")

    def _consolidate_working_to_episodic(self) -> None:
        """Move important working memory to episodic"""
        for entry in list(self.working_memory.values()):
            if (
                entry.importance_score >= 0.7
                and entry.access_count >= 3
                and (datetime.utcnow() - entry.timestamp).total_seconds() >= 3600
            ):  # 1 hour old

                # Move to episodic memory
                del self.working_memory[entry.id]
                entry.level = MemoryLevel.EPISODIC
                self._store_in_episodic_memory(entry)

    def _consolidate_episodic_to_semantic(self) -> None:
        """Move very important episodic memory to semantic"""
        for entry in list(self.episodic_memory.values()):
            if (
                entry.importance_score >= 0.9
                and entry.access_count >= 10
                and (datetime.utcnow() - entry.timestamp).total_seconds() >= 86400
            ):  # 1 day old

                # Move to semantic memory
                del self.episodic_memory[entry.id]
                entry.level = MemoryLevel.SEMANTIC
                self._store_in_semantic_memory(entry)

    def _cleanup_expired_entries(self) -> None:
        """Remove expired entries from all memory levels"""
        current_time = datetime.utcnow()

        # Clean working memory
        expired_working = [
            entry_id
            for entry_id, entry in self.working_memory.items()
            if entry.expires_at and entry.expires_at <= current_time
        ]
        for entry_id in expired_working:
            del self.working_memory[entry_id]

        # Clean episodic memory
        expired_episodic = [
            entry_id
            for entry_id, entry in self.episodic_memory.items()
            if entry.expires_at and entry.expires_at <= current_time
        ]
        for entry_id in expired_episodic:
            del self.episodic_memory[entry_id]

    def _optimize_memory_usage(self) -> None:
        """Optimize memory usage and performance"""
        # Clean up old entries
        self._evict_from_working_memory()
        self._evict_from_episodic_memory()

    def _update_stats(self) -> None:
        """Update memory statistics"""
        self.stats.total_entries = (
            len(self.working_memory)
            + len(self.episodic_memory)
            + len(self.semantic_memory)
        )
        self.stats.working_memory_entries = len(self.working_memory)
        self.stats.episodic_memory_entries = len(self.episodic_memory)
        self.stats.semantic_memory_entries = len(self.semantic_memory)

    def _update_query_performance(self, query_time: float) -> None:
        """Update query performance metrics"""
        # Simple moving average
        if self.stats.average_query_time == 0:
            self.stats.average_query_time = query_time
        else:
            self.stats.average_query_time = (
                self.stats.average_query_time * 0.9 + query_time * 0.1
            )

    def _persist_episodic_entry(self, entry: MemoryEntry) -> None:
        """Persist episodic entry to disk"""
        try:
            episodic_dir = self.storage_path / "episodic"
            episodic_dir.mkdir(exist_ok=True)

            file_path = episodic_dir / f"{entry.id}.json"
            with open(file_path, "w") as f:
                json.dump(
                    {
                        "id": entry.id,
                        "level": entry.level.value,
                        "memory_type": entry.memory_type.value,
                        "content": entry.content,
                        "metadata": entry.metadata,
                        "timestamp": entry.timestamp.isoformat(),
                        "importance_score": entry.importance_score,
                        "access_count": entry.access_count,
                        "expires_at": (
                            entry.expires_at.isoformat() if entry.expires_at else None
                        ),
                    },
                    f,
                    default=str,
                )

        except Exception as e:
            self.logger.debug(f"Could not persist episodic entry: {e}")

    def _persist_semantic_entry(self, entry: MemoryEntry) -> None:
        """Persist semantic entry to disk"""
        try:
            semantic_dir = self.storage_path / "semantic"
            semantic_dir.mkdir(exist_ok=True)

            file_path = semantic_dir / f"{entry.id}.json"
            with open(file_path, "w") as f:
                json.dump(
                    {
                        "id": entry.id,
                        "level": entry.level.value,
                        "memory_type": entry.memory_type.value,
                        "content": entry.content,
                        "metadata": entry.metadata,
                        "timestamp": entry.timestamp.isoformat(),
                        "importance_score": entry.importance_score,
                        "access_count": entry.access_count,
                    },
                    f,
                    default=str,
                )

        except Exception as e:
            self.logger.debug(f"Could not persist semantic entry: {e}")

    def _store_in_chroma(self, entry: MemoryEntry) -> None:
        """Store entry in ChromaDB"""
        if not self.chroma_client:
            return

        try:
            collection = self.chroma_client.get_or_create_collection(
                name=entry.level.value,
                metadata={"description": f"{entry.level.value} memory"},
            )

            collection.add(
                ids=[entry.id],
                documents=(
                    [str(entry.content)]
                    if isinstance(entry.content, str)
                    else [json.dumps(entry.content)]
                ),
                metadatas=[
                    {
                        "memory_type": entry.memory_type.value,
                        "importance_score": entry.importance_score,
                        "timestamp": entry.timestamp.isoformat(),
                        **entry.metadata,
                    }
                ],
            )

        except Exception as e:
            self.logger.debug(f"Could not store in ChromaDB: {e}")

    def get_stats(self) -> MemoryStats:
        """Get current memory statistics"""
        self._update_stats()
        return self.stats

    def clear_level(self, memory_level: MemoryLevel) -> None:
        """Clear all entries from specified memory level"""
        if memory_level == MemoryLevel.WORKING:
            self.working_memory.clear()
        elif memory_level == MemoryLevel.EPISODIC:
            self.episodic_memory.clear()
        elif memory_level == MemoryLevel.SEMANTIC:
            self.semantic_memory.clear()

        self._update_stats()
        self.logger.info(f"🧹 Cleared {memory_level.value} memory")

    def shutdown(self) -> None:
        """Shutdown memory system gracefully"""
        self.logger.info("🔄 Shutting down memory system...")

        self._running = False

        # Wait for background threads
        if self._consolidation_thread:
            self._consolidation_thread.join(timeout=5)
        if self._cleanup_thread:
            self._cleanup_thread.join(timeout=5)

        # Final cleanup
        self._cleanup_expired_entries()

        self.logger.info("✅ Memory system shutdown complete")


# Global memory manager instance
memory_manager = HierarchicalMemoryManager()

if __name__ == "__main__":
    # Test memory system
    print("🧠 Testing Hierarchical Memory System")

    # Store some test data
    test_content = "This is a test memory entry about college football analytics"
    entry_id = memory_manager.store(
        content=test_content,
        memory_level=MemoryLevel.WORKING,
        memory_type=MemoryType.CONTEXT,
        metadata={"importance": "high", "domain": "football"},
        tags=["test", "analytics"],
    )

    print(f"Stored entry: {entry_id}")

    # Retrieve with query
    query = MemoryQuery(
        query_text="college football",
        memory_level=MemoryLevel.WORKING,
        memory_types=[MemoryType.CONTEXT],
        limit=5,
    )

    results = memory_manager.retrieve(query)
    print(f"Retrieved {len(results)} entries")

    # Show stats
    stats = memory_manager.get_stats()
    print(f"Memory stats: {asdict(stats)}")

    # Cleanup
    memory_manager.shutdown()
