#!/usr/bin/env python3
"""
State Manager - Cleanup Operation State Tracking

Manages state tracking and persistence for cleanup operations including
operation progress, metrics collection, and checkpoint management.

Provides comprehensive visibility into autonomous cleanup operations
with persistent storage and recovery capabilities.

Author: Autonomous Code Orchestration System
Created: 2025-01-20
Version: 1.0
"""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.observability import (
    ErrorCategory,
    ErrorEvent,
    ErrorSeverity,
    configure_logging,
    get_logger,
)

configure_logging(service_name="agents")
logger = get_logger(__name__, component="state_manager", service_name="agents")


class CleanupState:
    """Represents the state of a cleanup operation"""

    def __init__(
        self,
        session_id: str,
        operation_type: str,
        scopes: List[str],
        initial_state: Optional[Dict[str, Any]] = None
    ):
        self.session_id = session_id
        self.operation_type = operation_type
        self.scopes = scopes
        self.status = "initialized"
        self.start_time = time.time()
        self.end_time: Optional[float] = None
        self.progress = {
            "total_scopes": len(scopes),
            "completed_scopes": [],
            "current_scope": None,
            "progress_percentage": 0.0
        }
        self.metrics = {
            "files_processed": 0,
            "space_freed_mb": 0.0,
            "directories_processed": 0,
            "errors": 0,
            "warnings": 0,
            "operations": {}
        }
        self.checkpoints = []
        self.errors = []
        self.warnings = []
        self.additional_data = initial_state or {}

    def update_progress(
        self,
        scope: Optional[str] = None,
        files_processed: int = 0,
        space_freed_mb: float = 0.0,
        status: Optional[str] = None
    ) -> None:
        """Update operation progress"""

        if scope:
            if scope not in self.progress["completed_scopes"]:
                self.progress["completed_scopes"].append(scope)

            self.progress["current_scope"] = scope

        self.progress["progress_percentage"] = (
            len(self.progress["completed_scopes"]) / self.progress["total_scopes"] * 100
        )

        self.metrics["files_processed"] += files_processed
        self.metrics["space_freed_mb"] += space_freed_mb

        if status:
            self.status = status

    def add_checkpoint(self, checkpoint_data: Dict[str, Any]) -> str:
        """Add a checkpoint to the state"""
        checkpoint_id = f"checkpoint_{int(time.time() * 1000)}"
        checkpoint = {
            "checkpoint_id": checkpoint_id,
            "timestamp": datetime.now().isoformat(),
            "session_time": time.time() - self.start_time,
            "state_snapshot": self.to_dict(),
            "checkpoint_data": checkpoint_data
        }
        self.checkpoints.append(checkpoint)
        return checkpoint_id

    def add_error(self, error_message: str, error_context: Optional[Dict[str, Any]] = None) -> None:
        """Add an error to the state"""
        error = {
            "timestamp": datetime.now().isoformat(),
            "session_time": time.time() - self.start_time,
            "message": error_message,
            "context": error_context or {}
        }
        self.errors.append(error)
        self.metrics["errors"] += 1

    def add_warning(self, warning_message: str, warning_context: Optional[Dict[str, Any]] = None) -> None:
        """Add a warning to the state"""
        warning = {
            "timestamp": datetime.now().isoformat(),
            "session_time": time.time() - self.start_time,
            "message": warning_message,
            "context": warning_context or {}
        }
        self.warnings.append(warning)
        self.metrics["warnings"] += 1

    def complete(self, success: bool = True) -> None:
        """Mark the operation as completed"""
        self.end_time = time.time()
        self.status = "completed" if success else "failed"
        self.progress["progress_percentage"] = 100.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary"""
        return {
            "session_id": self.session_id,
            "operation_type": self.operation_type,
            "scopes": self.scopes,
            "status": self.status,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_seconds": (self.end_time or time.time()) - self.start_time,
            "progress": self.progress,
            "metrics": self.metrics,
            "checkpoint_count": len(self.checkpoints),
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "additional_data": self.additional_data
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CleanupState":
        """Create state from dictionary"""
        state = cls(
            session_id=data["session_id"],
            operation_type=data["operation_type"],
            scopes=data["scopes"],
            initial_state=data.get("additional_data", {})
        )

        state.status = data["status"]
        state.start_time = data["start_time"]
        state.end_time = data.get("end_time")
        state.progress = data["progress"]
        state.metrics = data["metrics"]
        state.errors = data.get("errors", [])
        state.warnings = data.get("warnings", [])
        state.checkpoints = data.get("checkpoints", [])

        return state


class StateManager:
    """
    Manages state tracking and persistence for cleanup operations.

    Provides comprehensive state management with checkpoint creation,
    persistent storage, and recovery capabilities.
    """

    def __init__(self, state_dir: Optional[str] = None):
        self.state_dir = Path(state_dir or "project_management/cleanup_state")
        self.state_dir.mkdir(parents=True, exist_ok=True)

        self.active_states: Dict[str, CleanupState] = {}
        self.state_history: List[CleanupState] = []

        # Load existing state history
        self._load_state_history()

        logger.info(f"State Manager initialized with directory: {self.state_dir}")

    def create_state(
        self,
        session_id: str,
        operation_type: str,
        scopes: List[str],
        initial_state: Optional[Dict[str, Any]] = None
    ) -> CleanupState:
        """Create a new cleanup state"""

        state = CleanupState(session_id, operation_type, scopes, initial_state)
        self.active_states[session_id] = state

        logger.info(
            f"Created new cleanup state: {session_id}",
            extra={
                "event": "state_created",
                "session_id": session_id,
                "operation_type": operation_type,
                "scopes": scopes
            }
        )

        return state

    def get_state(self, session_id: str) -> Optional[CleanupState]:
        """Get active state by session ID"""
        return self.active_states.get(session_id)

    def update_state(
        self,
        session_id: str,
        scope: Optional[str] = None,
        files_processed: int = 0,
        space_freed_mb: float = 0.0,
        status: Optional[str] = None,
        checkpoint_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update an active state"""

        state = self.active_states.get(session_id)
        if not state:
            logger.warning(f"State not found for session: {session_id}")
            return False

        state.update_progress(scope, files_processed, space_freed_mb, status)

        if checkpoint_data:
            checkpoint_id = state.add_checkpoint(checkpoint_data)
            self._save_checkpoint(session_id, checkpoint_id, checkpoint_data)

        # Persist state updates
        self._save_state(state)

        return True

    def add_error(
        self,
        session_id: str,
        error_message: str,
        error_context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Add error to state"""

        state = self.active_states.get(session_id)
        if not state:
            return False

        state.add_error(error_message, error_context)
        self._save_state(state)
        return True

    def add_warning(
        self,
        session_id: str,
        warning_message: str,
        warning_context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Add warning to state"""

        state = self.active_states.get(session_id)
        if not state:
            return False

        state.add_warning(warning_message, warning_context)
        self._save_state(state)
        return True

    def complete_state(
        self,
        session_id: str,
        success: bool = True,
        final_summary: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Complete a state and move to history"""

        state = self.active_states.get(session_id)
        if not state:
            return False

        state.complete(success)

        if final_summary:
            state.additional_data["final_summary"] = final_summary

        # Move to history
        self.state_history.append(state)
        del self.active_states[session_id]

        # Save final state
        self._save_state_to_history(state)

        logger.info(
            f"Completed cleanup state: {session_id}",
            extra={
                "event": "state_completed",
                "session_id": session_id,
                "success": success,
                "duration": state.to_dict()["duration_seconds"]
            }
        )

        return True

    def create_checkpoint(
        self,
        session_id: str,
        checkpoint_data: Dict[str, Any]
    ) -> Optional[str]:
        """Create a checkpoint for a state"""

        state = self.active_states.get(session_id)
        if not state:
            return None

        checkpoint_id = state.add_checkpoint(checkpoint_data)
        self._save_checkpoint(session_id, checkpoint_id, checkpoint_data)

        return checkpoint_id

    def restore_from_checkpoint(
        self,
        session_id: str,
        checkpoint_id: str
    ) -> Optional[CleanupState]:
        """Restore state from checkpoint"""

        checkpoint_file = self.state_dir / f"{session_id}_checkpoint_{checkpoint_id}.json"
        if not checkpoint_file.exists():
            return None

        try:
            with open(checkpoint_file, 'r') as f:
                checkpoint_data = json.load(f)

            state_data = checkpoint_data["state_snapshot"]
            restored_state = CleanupState.from_dict(state_data)

            self.active_states[session_id] = restored_state

            logger.info(
                f"Restored state from checkpoint: {checkpoint_id}",
                extra={
                    "event": "state_restored",
                    "session_id": session_id,
                    "checkpoint_id": checkpoint_id
                }
            )

            return restored_state

        except Exception as e:
            logger.error(f"Failed to restore from checkpoint: {e}")
            return None

    def get_active_states(self) -> Dict[str, CleanupState]:
        """Get all active states"""
        return self.active_states.copy()

    def get_state_history(
        self,
        limit: Optional[int] = None,
        operation_type: Optional[str] = None
    ) -> List[CleanupState]:
        """Get state history with optional filtering"""

        history = self.state_history.copy()

        if operation_type:
            history = [s for s in history if s.operation_type == operation_type]

        # Sort by start time (newest first)
        history.sort(key=lambda s: s.start_time, reverse=True)

        if limit:
            history = history[:limit]

        return history

    def get_state_metrics(
        self,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get metrics for states"""

        if session_id:
            state = self.active_states.get(session_id)
            if not state:
                return {"error": "Session not found"}
            return state.metrics

        # Aggregate metrics for all active states
        total_metrics = {
            "active_sessions": len(self.active_states),
            "total_files_processed": 0,
            "total_space_freed_mb": 0.0,
            "total_errors": 0,
            "total_warnings": 0,
            "sessions": {}
        }

        for sid, state in self.active_states.items():
            total_metrics["total_files_processed"] += state.metrics["files_processed"]
            total_metrics["total_space_freed_mb"] += state.metrics["space_freed_mb"]
            total_metrics["total_errors"] += state.metrics["errors"]
            total_metrics["total_warnings"] += state.metrics["warnings"]

            total_metrics["sessions"][sid] = {
                "status": state.status,
                "progress": state.progress["progress_percentage"],
                "duration": time.time() - state.start_time
            }

        return total_metrics

    def cleanup_old_states(self, days_to_keep: int = 30) -> int:
        """Clean up old state history"""

        cutoff_time = time.time() - (days_to_keep * 24 * 60 * 60)

        old_states = [
            state for state in self.state_history
            if state.start_time < cutoff_time
        ]

        # Remove old state files
        removed_count = 0
        for state in old_states:
            state_file = self.state_dir / f"{state.session_id}_state.json"
            if state_file.exists():
                state_file.unlink()
                removed_count += 1

            # Remove checkpoint files
            for checkpoint in state.checkpoints:
                checkpoint_file = self.state_dir / f"{state.session_id}_checkpoint_{checkpoint['checkpoint_id']}.json"
                if checkpoint_file.exists():
                    checkpoint_file.unlink()

        # Remove from memory
        self.state_history = [
            state for state in self.state_history
            if state.start_time >= cutoff_time
        ]

        logger.info(
            f"Cleaned up {removed_count} old state files",
            extra={"event": "state_cleanup", "removed_count": removed_count}
        )

        return removed_count

    def _save_state(self, state: CleanupState) -> None:
        """Save state to file"""
        try:
            state_file = self.state_dir / f"{state.session_id}_state.json"
            with open(state_file, 'w') as f:
                json.dump(state.to_dict(), f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save state: {e}")

    def _save_checkpoint(self, session_id: str, checkpoint_id: str, checkpoint_data: Dict[str, Any]) -> None:
        """Save checkpoint to file"""
        try:
            checkpoint_file = self.state_dir / f"{session_id}_checkpoint_{checkpoint_id}.json"
            with open(checkpoint_file, 'w') as f:
                json.dump(checkpoint_data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")

    def _save_state_to_history(self, state: CleanupState) -> None:
        """Save completed state to history"""
        try:
            history_file = self.state_dir / f"{state.session_id}_completed.json"
            with open(history_file, 'w') as f:
                json.dump(state.to_dict(), f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save state to history: {e}")

    def _load_state_history(self) -> None:
        """Load existing state history from files"""
        try:
            for state_file in self.state_dir.glob("*_completed.json"):
                try:
                    with open(state_file, 'r') as f:
                        state_data = json.load(f)

                    state = CleanupState.from_dict(state_data)
                    self.state_history.append(state)

                except Exception as e:
                    logger.warning(f"Failed to load state from {state_file}: {e}")

            logger.info(f"Loaded {len(self.state_history)} states from history")

        except Exception as e:
            logger.error(f"Failed to load state history: {e}")

    def export_state_report(
        self,
        session_id: Optional[str] = None,
        format: str = "json"
    ) -> Optional[Dict[str, Any]]:
        """Export state report"""

        if session_id:
            state = self.active_states.get(session_id)
            if not state:
                return {"error": "Session not found"}
            return state.to_dict()

        # Export summary of all states
        report = {
            "generated_at": datetime.now().isoformat(),
            "active_states": {
                sid: state.to_dict() for sid, state in self.active_states.items()
            },
            "state_history_summary": {
                "total_completed": len(self.state_history),
                "recent_states": [
                    {
                        "session_id": state.session_id,
                        "operation_type": state.operation_type,
                        "status": state.status,
                        "completed_at": datetime.fromtimestamp(state.end_time or time.time()).isoformat(),
                        "duration": state.to_dict()["duration_seconds"],
                        "files_processed": state.metrics["files_processed"],
                        "space_freed_mb": state.metrics["space_freed_mb"]
                    }
                    for state in self.state_history[:10]  # Last 10 states
                ]
            },
            "aggregate_metrics": self.get_state_metrics()
        }

        return report

    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of state manager"""

        return {
            "status": "healthy",
            "active_states": len(self.active_states),
            "history_size": len(self.state_history),
            "state_dir_exists": self.state_dir.exists(),
            "disk_usage_mb": self._get_state_dir_size(),
            "last_cleanup": self._get_last_cleanup_time()
        }

    def _get_state_dir_size(self) -> float:
        """Get size of state directory in MB"""
        try:
            total_size = 0
            for file_path in self.state_dir.rglob("*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
            return total_size / (1024 * 1024)
        except Exception:
            return 0.0

    def _get_last_cleanup_time(self) -> Optional[str]:
        """Get last cleanup time"""
        # This could be stored in a metadata file
        # For now, return None
        return None