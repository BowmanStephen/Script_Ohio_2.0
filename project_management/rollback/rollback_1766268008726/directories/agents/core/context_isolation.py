"""
Context Isolation Manager

Manages fresh context windows per subagent and context handoffs between agents.
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class IsolatedContext:
    """Isolated context for a subagent"""

    context_id: str
    subagent_id: str
    initial_context: Dict[str, Any] = field(default_factory=dict)
    isolated: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary"""
        return {
            "context_id": self.context_id,
            "subagent_id": self.subagent_id,
            "initial_context": self.initial_context,
            "isolated": self.isolated,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class ContextHandoff:
    """Context handoff between agents"""

    handoff_id: str
    from_agent: str
    to_agent: str
    context_data: Dict[str, Any]
    filtered_context: Dict[str, Any] = field(default_factory=dict)
    handoff_time: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ContextIsolationManager:
    """
    Manages context isolation for subagents.

    Features:
    - Fresh context windows per subagent
    - Context handoff between agents
    - Context archival for audit trails
    - Context compression for efficiency
    """

    def __init__(self):
        """Initialize the context isolation manager"""
        self.active_contexts: Dict[str, IsolatedContext] = {}
        self.handoff_history: List[ContextHandoff] = []
        self.archived_contexts: List[IsolatedContext] = []

    def create_isolated_context(
        self, subagent_id: str, initial_context: Optional[Dict[str, Any]] = None
    ) -> IsolatedContext:
        """
        Create a fresh, isolated context window for a subagent.

        Args:
            subagent_id: ID of the subagent
            initial_context: Optional initial context to load

        Returns:
            IsolatedContext with fresh context window
        """
        context_id = str(uuid.uuid4())

        # Create isolated context - no previous conversation noise
        # Only relevant context is loaded
        context = IsolatedContext(
            context_id=context_id,
            subagent_id=subagent_id,
            initial_context=initial_context or {},
            isolated=True,
        )

        self.active_contexts[context_id] = context
        logger.info(f"Created isolated context {context_id} for subagent {subagent_id}")

        return context

    def handoff_context(
        self,
        from_agent: str,
        to_agent: str,
        context_data: Dict[str, Any],
        filter_irrelevant: bool = True,
    ) -> IsolatedContext:
        """
        Transfer context from one agent to another.

        Args:
            from_agent: Source agent ID
            to_agent: Target agent ID
            context_data: Context data to transfer
            filter_irrelevant: Whether to filter irrelevant information

        Returns:
            New isolated context for target agent
        """
        handoff_id = str(uuid.uuid4())

        # Filter irrelevant information if requested
        filtered_context = context_data
        if filter_irrelevant:
            filtered_context = self._filter_context(context_data, to_agent)

        # Create handoff record
        handoff = ContextHandoff(
            handoff_id=handoff_id,
            from_agent=from_agent,
            to_agent=to_agent,
            context_data=context_data,
            filtered_context=filtered_context,
        )

        self.handoff_history.append(handoff)

        # Create new isolated context for target agent
        new_context = self.create_isolated_context(to_agent, filtered_context)

        logger.info(
            f"Handed off context from {from_agent} to {to_agent} "
            f"(handoff_id: {handoff_id})"
        )

        return new_context

    def _filter_context(
        self, context_data: Dict[str, Any], target_agent: str
    ) -> Dict[str, Any]:
        """
        Filter context to only include relevant information for target agent.

        Args:
            context_data: Full context data
            target_agent: Target agent ID

        Returns:
            Filtered context
        """
        # Simple filtering logic
        # In production, use more sophisticated filtering based on agent type

        filtered = {}

        # Keep essential fields
        for key in ["objective", "task", "requirements", "specifications"]:
            if key in context_data:
                filtered[key] = context_data[key]

        # Keep results if present
        if "result" in context_data:
            filtered["result"] = context_data["result"]

        # Keep errors if present
        if "error" in context_data:
            filtered["error"] = context_data["error"]

        # Add metadata about filtering
        filtered["_filtered_for"] = target_agent
        filtered["_filtered_at"] = datetime.now().isoformat()

        return filtered

    def archive_context(self, context_id: str, reason: str = "completed") -> bool:
        """
        Archive a context for audit trail.

        Args:
            context_id: Context ID to archive
            reason: Reason for archiving

        Returns:
            True if archived successfully
        """
        if context_id not in self.active_contexts:
            logger.warning(f"Context {context_id} not found for archiving")
            return False

        context = self.active_contexts.pop(context_id)
        context.metadata["archived_reason"] = reason
        context.metadata["archived_at"] = datetime.now().isoformat()

        self.archived_contexts.append(context)

        logger.info(f"Archived context {context_id} (reason: {reason})")
        return True

    def get_context(self, context_id: str) -> Optional[IsolatedContext]:
        """
        Get an active context by ID.

        Args:
            context_id: Context ID

        Returns:
            IsolatedContext or None if not found
        """
        return self.active_contexts.get(context_id)

    def get_handoff_history(
        self, from_agent: Optional[str] = None, to_agent: Optional[str] = None
    ) -> List[ContextHandoff]:
        """
        Get handoff history, optionally filtered by agents.

        Args:
            from_agent: Filter by source agent
            to_agent: Filter by target agent

        Returns:
            List of ContextHandoff records
        """
        history = self.handoff_history

        if from_agent:
            history = [h for h in history if h.from_agent == from_agent]

        if to_agent:
            history = [h for h in history if h.to_agent == to_agent]

        return history

    def compress_context(self, context: IsolatedContext) -> Dict[str, Any]:
        """
        Compress context for efficiency.

        Args:
            context: Context to compress

        Returns:
            Compressed context dictionary
        """
        # Simple compression - keep only essential data
        compressed = {
            "context_id": context.context_id,
            "subagent_id": context.subagent_id,
            "essential_data": {},
        }

        # Extract essential data from initial context
        initial = context.initial_context
        for key in ["objective", "task", "result", "error"]:
            if key in initial:
                compressed["essential_data"][key] = initial[key]

        return compressed
