#!/usr/bin/env python3
"""
Advanced State Management and Persistence System

Implements OpenAI best practices for state management:
- Persistent state storage across sessions
- State versioning and rollback capabilities
- Atomic state operations and consistency
- State synchronization across agents
- Recovery and resilience mechanisms
"""

import json
import sqlite3
import time
import uuid
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
import logging
from pathlib import Path
import pickle
import hashlib
from contextlib import contextmanager

logger = logging.getLogger("state_manager")

class StateType(Enum):
    """Types of state that can be managed"""
    SESSION_STATE = "session_state"           # User session state
    AGENT_STATE = "agent_state"              # Individual agent state
    WORKFLOW_STATE = "workflow_state"        # Multi-step workflow state
    SYSTEM_STATE = "system_state"            # System configuration state
    COLLABORATION_STATE = "collaboration_state"  # Agent collaboration state
    MEMORY_STATE = "memory_state"            # Conversation memory state

class StateStatus(Enum):
    """Status of state entries"""
    ACTIVE = "active"                       # Currently in use
    COMPLETED = "completed"                 # Successfully completed
    FAILED = "failed"                      # Failed during execution
    SUSPENDED = "suspended"                 # Paused for later resumption
    ARCHIVED = "archived"                   # Stored for long-term reference

@dataclass
class StateSnapshot:
    """Represents a snapshot of system state"""
    snapshot_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    state_type: StateType = StateType.SESSION_STATE
    entity_id: str = ""                     # session_id, agent_id, workflow_id, etc.
    state_data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    version: int = 1
    parent_snapshot_id: Optional[str] = None
    checksum: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    status: StateStatus = StateStatus.ACTIVE

    def __post_init__(self):
        """Calculate checksum after data is set"""
        self.checksum = self._calculate_checksum()

    def _calculate_checksum(self) -> str:
        """Calculate checksum for data integrity verification"""
        data_str = json.dumps(self.state_data, sort_keys=True, default=str)
        return hashlib.sha256(data_str.encode()).hexdigest()

    def verify_integrity(self) -> bool:
        """Verify state data integrity using checksum"""
        current_checksum = self._calculate_checksum()
        return self.checksum == current_checksum

@dataclass
class StateTransition:
    """Represents a transition between state snapshots"""
    transition_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    from_snapshot_id: Optional[str] = None
    to_snapshot_id: str = ""
    transition_type: str = ""                # "create", "update", "rollback", "restore"
    actor: str = ""                          # Which agent/system initiated the transition
    reason: str = ""                         # Reason for the transition
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

class DatabaseManager:
    """Handles database operations for state persistence"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.lock = threading.Lock()
        self._initialize_database()

    def _initialize_database(self):
        """Initialize SQLite database with required tables"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            try:
                # Create snapshots table
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS state_snapshots (
                        snapshot_id TEXT PRIMARY KEY,
                        state_type TEXT NOT NULL,
                        entity_id TEXT NOT NULL,
                        state_data TEXT NOT NULL,
                        metadata TEXT,
                        version INTEGER DEFAULT 1,
                        parent_snapshot_id TEXT,
                        checksum TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        expires_at TEXT,
                        status TEXT DEFAULT 'active'
                    )
                ''')

                # Create transitions table
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS state_transitions (
                        transition_id TEXT PRIMARY KEY,
                        from_snapshot_id TEXT,
                        to_snapshot_id TEXT NOT NULL,
                        transition_type TEXT NOT NULL,
                        actor TEXT NOT NULL,
                        reason TEXT,
                        timestamp TEXT NOT NULL,
                        metadata TEXT
                    )
                ''')

                # Create indexes for performance
                conn.execute('''
                    CREATE INDEX IF NOT EXISTS idx_snapshots_entity_type
                    ON state_snapshots(entity_id, state_type)
                ''')

                conn.execute('''
                    CREATE INDEX IF NOT EXISTS idx_snapshots_status
                    ON state_snapshots(status, created_at)
                ''')

                conn.execute('''
                    CREATE INDEX IF NOT EXISTS idx_transitions_to_snapshot
                    ON state_transitions(to_snapshot_id)
                ''')

                conn.commit()
                logger.info(f"State database initialized: {self.db_path}")

            except Exception as e:
                logger.error(f"Failed to initialize database: {e}")
                raise
            finally:
                conn.close()

    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

class StateManager:
    """
    Advanced state management system following OpenAI best practices

    Features:
    - Atomic state operations with rollback capabilities
    - State versioning and branching
    - Automatic cleanup and archival
    - Performance optimization with caching
    - Integrity verification and recovery
    """

    def __init__(self, base_path: str = None):
        self.base_path = Path(base_path) if base_path else Path.cwd() / "state"
        self.base_path.mkdir(parents=True, exist_ok=True)

        # Initialize database
        db_path = self.base_path / "state_management.db"
        self.db_manager = DatabaseManager(str(db_path))

        # In-memory cache for frequently accessed states
        self.state_cache: Dict[str, StateSnapshot] = {}
        self.cache_lock = threading.Lock()
        self.cache_max_size = 100

        # State change observers
        self.state_observers: Dict[StateType, List[Callable]] = {
            state_type: [] for state_type in StateType
        }

        # Metrics tracking
        self.metrics = {
            'snapshots_created': 0,
            'snapshots_restored': 0,
            'rollbacks_performed': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'database_operations': 0
        }

        logger.info("State Manager initialized")

    def create_state_snapshot(self,
                            state_type: StateType,
                            entity_id: str,
                            state_data: Dict[str, Any],
                            metadata: Dict[str, Any] = None,
                            parent_snapshot_id: str = None,
                            expires_in_hours: int = None) -> str:
        """Create a new state snapshot with atomic operation"""

        snapshot = StateSnapshot(
            state_type=state_type,
            entity_id=entity_id,
            state_data=state_data,
            metadata=metadata or {},
            parent_snapshot_id=parent_snapshot_id
        )

        # Set expiration if specified
        if expires_in_hours:
            snapshot.expires_at = datetime.now() + timedelta(hours=expires_in_hours)

        # Store in database
        try:
            with self.db_manager.get_connection() as conn:
                conn.execute('''
                    INSERT INTO state_snapshots
                    (snapshot_id, state_type, entity_id, state_data, metadata,
                     version, parent_snapshot_id, checksum, created_at, expires_at, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    snapshot.snapshot_id,
                    snapshot.state_type.value,
                    snapshot.entity_id,
                    json.dumps(snapshot.state_data, default=str),
                    json.dumps(snapshot.metadata, default=str),
                    snapshot.version,
                    snapshot.parent_snapshot_id,
                    snapshot.checksum,
                    snapshot.created_at.isoformat(),
                    snapshot.expires_at.isoformat() if snapshot.expires_at else None,
                    snapshot.status.value
                ))

                conn.commit()

            # Cache the snapshot
            self._cache_snapshot(snapshot)

            # Record transition
            self._record_transition(
                transition_type="create",
                to_snapshot_id=snapshot.snapshot_id,
                actor="state_manager",
                reason="Initial state creation"
            )

            # Notify observers
            self._notify_observers(snapshot, "created")

            self.metrics['snapshots_created'] += 1
            logger.info(f"State snapshot created: {snapshot.snapshot_id} for {entity_id}")

            return snapshot.snapshot_id

        except Exception as e:
            logger.error(f"Failed to create state snapshot: {e}")
            raise

    def update_state_snapshot(self,
                            snapshot_id: str,
                            new_state_data: Dict[str, Any],
                            actor: str = "unknown",
                            reason: str = "State update") -> str:
        """Update an existing state snapshot with versioning"""

        # Get current snapshot
        current_snapshot = self._get_snapshot(snapshot_id)
        if not current_snapshot:
            raise ValueError(f"Snapshot not found: {snapshot_id}")

        # Create new version
        new_snapshot = StateSnapshot(
            state_type=current_snapshot.state_type,
            entity_id=current_snapshot.entity_id,
            state_data=new_state_data,
            metadata=current_snapshot.metadata.copy(),
            version=current_snapshot.version + 1,
            parent_snapshot_id=current_snapshot.parent_snapshot_id
        )

        # Store updated snapshot
        try:
            with self.db_manager.get_connection() as conn:
                # Mark old snapshot as completed
                conn.execute('''
                    UPDATE state_snapshots
                    SET status = 'completed'
                    WHERE snapshot_id = ?
                ''', (snapshot_id,))

                # Insert new snapshot
                conn.execute('''
                    INSERT INTO state_snapshots
                    (snapshot_id, state_type, entity_id, state_data, metadata,
                     version, parent_snapshot_id, checksum, created_at, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    new_snapshot.snapshot_id,
                    new_snapshot.state_type.value,
                    new_snapshot.entity_id,
                    json.dumps(new_snapshot.state_data, default=str),
                    json.dumps(new_snapshot.metadata, default=str),
                    new_snapshot.version,
                    new_snapshot.parent_snapshot_id,
                    new_snapshot.checksum,
                    new_snapshot.created_at.isoformat(),
                    new_snapshot.status.value
                ))

                conn.commit()

            # Update cache
            self._cache_snapshot(new_snapshot)

            # Record transition
            self._record_transition(
                from_snapshot_id=snapshot_id,
                to_snapshot_id=new_snapshot.snapshot_id,
                transition_type="update",
                actor=actor,
                reason=reason
            )

            # Notify observers
            self._notify_observers(new_snapshot, "updated")

            logger.info(f"State snapshot updated: {snapshot_id} -> {new_snapshot.snapshot_id}")
            return new_snapshot.snapshot_id

        except Exception as e:
            logger.error(f"Failed to update state snapshot: {e}")
            raise

    def restore_state_snapshot(self, snapshot_id: str, actor: str = "unknown") -> Dict[str, Any]:
        """Restore state from a snapshot with integrity verification"""

        # Get snapshot
        snapshot = self._get_snapshot(snapshot_id)
        if not snapshot:
            raise ValueError(f"Snapshot not found: {snapshot_id}")

        # Verify integrity
        if not snapshot.verify_integrity():
            raise ValueError(f"Snapshot integrity check failed: {snapshot_id}")

        # Check expiration
        if snapshot.expires_at and datetime.now() > snapshot.expires_at:
            raise ValueError(f"Snapshot has expired: {snapshot_id}")

        try:
            # Record transition
            self._record_transition(
                from_snapshot_id=snapshot_id,
                to_snapshot_id=snapshot_id,  # Restored to same snapshot
                transition_type="restore",
                actor=actor,
                reason="State restoration"
            )

            # Notify observers
            self._notify_observers(snapshot, "restored")

            self.metrics['snapshots_restored'] += 1
            logger.info(f"State snapshot restored: {snapshot_id}")

            return snapshot.state_data.copy()

        except Exception as e:
            logger.error(f"Failed to restore state snapshot: {e}")
            raise

    def rollback_to_snapshot(self, snapshot_id: str, actor: str = "unknown", reason: str = "Rollback") -> Dict[str, Any]:
        """Rollback to a previous snapshot"""

        # Get snapshot and its history
        snapshot = self._get_snapshot(snapshot_id)
        if not snapshot:
            raise ValueError(f"Snapshot not found: {snapshot_id}")

        # Mark current active snapshots as completed
        try:
            with self.db_manager.get_connection() as conn:
                conn.execute('''
                    UPDATE state_snapshots
                    SET status = 'completed'
                    WHERE entity_id = ? AND state_type = ? AND status = 'active'
                ''', (snapshot.entity_id, snapshot.state_type.value))

                # Reactivate the target snapshot
                conn.execute('''
                    UPDATE state_snapshots
                    SET status = 'active'
                    WHERE snapshot_id = ?
                ''', (snapshot_id,))

                conn.commit()

            # Record transition
            self._record_transition(
                to_snapshot_id=snapshot_id,
                transition_type="rollback",
                actor=actor,
                reason=reason
            )

            # Notify observers
            self._notify_observers(snapshot, "rollback")

            self.metrics['rollbacks_performed'] += 1
            logger.info(f"Rolled back to snapshot: {snapshot_id}")

            return snapshot.state_data.copy()

        except Exception as e:
            logger.error(f"Failed to rollback to snapshot: {e}")
            raise

    def get_latest_state(self, state_type: StateType, entity_id: str) -> Optional[Dict[str, Any]]:
        """Get the latest active state for an entity"""

        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute('''
                    SELECT snapshot_id FROM state_snapshots
                    WHERE entity_id = ? AND state_type = ? AND status = 'active'
                    ORDER BY created_at DESC
                    LIMIT 1
                ''', (entity_id, state_type.value))

                row = cursor.fetchone()
                if row:
                    return self.restore_state_snapshot(row['snapshot_id'])
                return None

        except Exception as e:
            logger.error(f"Failed to get latest state: {e}")
            return None

    def list_snapshots(self,
                      state_type: Optional[StateType] = None,
                      entity_id: Optional[str] = None,
                      status: Optional[StateStatus] = None,
                      limit: int = 50) -> List[Dict[str, Any]]:
        """List snapshots with optional filtering"""

        try:
            with self.db_manager.get_connection() as conn:
                query = "SELECT * FROM state_snapshots WHERE 1=1"
                params = []

                if state_type:
                    query += " AND state_type = ?"
                    params.append(state_type.value)

                if entity_id:
                    query += " AND entity_id = ?"
                    params.append(entity_id)

                if status:
                    query += " AND status = ?"
                    params.append(status.value)

                query += " ORDER BY created_at DESC LIMIT ?"
                params.append(limit)

                cursor = conn.execute(query, params)
                rows = cursor.fetchall()

                snapshots = []
                for row in rows:
                    snapshots.append({
                        'snapshot_id': row['snapshot_id'],
                        'state_type': row['state_type'],
                        'entity_id': row['entity_id'],
                        'version': row['version'],
                        'created_at': row['created_at'],
                        'status': row['status'],
                        'has_parent': bool(row['parent_snapshot_id'])
                    })

                return snapshots

        except Exception as e:
            logger.error(f"Failed to list snapshots: {e}")
            return []

    def cleanup_expired_snapshots(self) -> int:
        """Clean up expired snapshots"""

        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute('''
                    UPDATE state_snapshots
                    SET status = 'archived'
                    WHERE status = 'active'
                    AND expires_at IS NOT NULL
                    AND expires_at < datetime('now')
                ''')

                count = cursor.rowcount
                conn.commit()

                logger.info(f"Archived {count} expired snapshots")
                return count

        except Exception as e:
            logger.error(f"Failed to cleanup expired snapshots: {e}")
            return 0

    def register_observer(self, state_type: StateType, observer: Callable):
        """Register an observer for state changes"""

        self.state_observers[state_type].append(observer)
        logger.info(f"Registered observer for {state_type.value}")

    def get_metrics(self) -> Dict[str, Any]:
        """Get state manager metrics"""

        # Get database statistics
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) as total FROM state_snapshots")
            total_snapshots = cursor.fetchone()['total']

            cursor = conn.execute("SELECT COUNT(*) as active FROM state_snapshots WHERE status = 'active'")
            active_snapshots = cursor.fetchone()['active']

            cursor = conn.execute("SELECT COUNT(*) as total FROM state_transitions")
            total_transitions = cursor.fetchone()['total']

        cache_hit_rate = (self.metrics['cache_hits'] /
                         (self.metrics['cache_hits'] + self.metrics['cache_misses'])) \
                        if (self.metrics['cache_hits'] + self.metrics['cache_misses']) > 0 else 0

        return {
            **self.metrics,
            'total_snapshots': total_snapshots,
            'active_snapshots': active_snapshots,
            'total_transitions': total_transitions,
            'cache_hit_rate': round(cache_hit_rate, 3),
            'cache_size': len(self.state_cache)
        }

    # Private helper methods

    def _get_snapshot(self, snapshot_id: str) -> Optional[StateSnapshot]:
        """Get snapshot from cache or database"""

        # Try cache first
        with self.cache_lock:
            if snapshot_id in self.state_cache:
                self.metrics['cache_hits'] += 1
                return self.state_cache[snapshot_id]
            else:
                self.metrics['cache_misses'] += 1

        # Try database
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute('''
                    SELECT * FROM state_snapshots
                    WHERE snapshot_id = ?
                ''', (snapshot_id,))

                row = cursor.fetchone()
                if row:
                    snapshot = StateSnapshot(
                        snapshot_id=row['snapshot_id'],
                        state_type=StateType(row['state_type']),
                        entity_id=row['entity_id'],
                        state_data=json.loads(row['state_data']),
                        metadata=json.loads(row['metadata']),
                        version=row['version'],
                        parent_snapshot_id=row['parent_snapshot_id'],
                        checksum=row['checksum'],
                        created_at=datetime.fromisoformat(row['created_at']),
                        expires_at=datetime.fromisoformat(row['expires_at']) if row['expires_at'] else None,
                        status=StateStatus(row['status'])
                    )

                    # Cache it
                    self._cache_snapshot(snapshot)
                    return snapshot

            return None

        except Exception as e:
            logger.error(f"Failed to get snapshot {snapshot_id}: {e}")
            return None

    def _cache_snapshot(self, snapshot: StateSnapshot):
        """Cache a snapshot with size management"""

        with self.cache_lock:
            # Remove oldest entries if cache is full
            while len(self.state_cache) >= self.cache_max_size:
                oldest_key = next(iter(self.state_cache))
                del self.state_cache[oldest_key]

            # Add new snapshot
            self.state_cache[snapshot.snapshot_id] = snapshot

    def _record_transition(self,
                          from_snapshot_id: Optional[str] = None,
                          to_snapshot_id: str = None,
                          transition_type: str = None,
                          actor: str = None,
                          reason: str = None):
        """Record a state transition"""

        try:
            with self.db_manager.get_connection() as conn:
                conn.execute('''
                    INSERT INTO state_transitions
                    (transition_id, from_snapshot_id, to_snapshot_id,
                     transition_type, actor, reason, timestamp, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    str(uuid.uuid4()),
                    from_snapshot_id,
                    to_snapshot_id,
                    transition_type,
                    actor,
                    reason,
                    datetime.now().isoformat(),
                    json.dumps({})
                ))

                conn.commit()

        except Exception as e:
            logger.error(f"Failed to record transition: {e}")

    def _notify_observers(self, snapshot: StateSnapshot, action: str):
        """Notify observers of state changes"""

        observers = self.state_observers.get(snapshot.state_type, [])
        for observer in observers:
            try:
                observer(snapshot, action)
            except Exception as e:
                logger.error(f"Observer error: {e}")

# Global state manager instance
state_manager = StateManager()

# Utility functions
def save_session_state(session_id: str, state_data: Dict[str, Any], metadata: Dict[str, Any] = None) -> str:
    """Convenient function to save session state"""
    return state_manager.create_state_snapshot(
        state_type=StateType.SESSION_STATE,
        entity_id=session_id,
        state_data=state_data,
        metadata=metadata,
        expires_in_hours=24  # Sessions expire after 24 hours
    )

def restore_session_state(session_id: str) -> Optional[Dict[str, Any]]:
    """Convenient function to restore session state"""
    return state_manager.get_latest_state(StateType.SESSION_STATE, session_id)

def save_agent_state(agent_id: str, state_data: Dict[str, Any], metadata: Dict[str, Any] = None) -> str:
    """Convenient function to save agent state"""
    return state_manager.create_state_snapshot(
        state_type=StateType.AGENT_STATE,
        entity_id=agent_id,
        state_data=state_data,
        metadata=metadata
    )

def restore_agent_state(agent_id: str) -> Optional[Dict[str, Any]]:
    """Convenient function to restore agent state"""
    return state_manager.get_latest_state(StateType.AGENT_STATE, agent_id)

def save_workflow_state(workflow_id: str, state_data: Dict[str, Any], metadata: Dict[str, Any] = None) -> str:
    """Convenient function to save workflow state"""
    return state_manager.create_state_snapshot(
        state_type=StateType.WORKFLOW_STATE,
        entity_id=workflow_id,
        state_data=state_data,
        metadata=metadata,
        expires_in_hours=72  # Workflows expire after 72 hours
    )

def restore_workflow_state(workflow_id: str) -> Optional[Dict[str, Any]]:
    """Convenient function to restore workflow state"""
    return state_manager.get_latest_state(StateType.WORKFLOW_STATE, workflow_id)