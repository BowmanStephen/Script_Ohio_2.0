"""
Context Compression Rules for Super AI Agent Architecture

Implements smart context management for Claude Code + Z.AI integration.
Provides phase-based clearing, dynamic loading, and TOON format integration.
"""

import json
import time
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from pathlib import Path
import logging

from src.toon_format import encode, decode

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ContextState:
    """Represents the current state of agent context"""
    agent_id: str
    context_tokens: int
    last_updated: datetime
    priority_score: float
    compression_applied: bool
    archive_path: Optional[str] = None

@dataclass
class ContextRule:
    """Represents a context management rule"""
    rule_id: str
    name: str
    condition: str
    action: str
    priority: int
    enabled: bool = True

class ContextCompressionEngine:
    """
    Advanced context compression and management system.

    Features:
    - Phase-based context clearing
    - Dynamic context loading with priority scoring
    - TOON format integration for 50-70% token reduction
    - Intelligent context archival and retrieval
    - Agent isolation and context inheritance
    """

    def __init__(self, config_path: str = "config/claude_code_optimization.json"):
        """Initialize the context compression engine"""
        self.config = self._load_config(config_path)
        self.context_states: Dict[str, ContextState] = {}
        self.archived_contexts: Dict[str, str] = {}
        self.current_phase = "initialization"

        # Context management rules
        self.rules = self._initialize_rules()

        # Performance metrics
        self.metrics = {
            "contexts_compressed": 0,
            "tokens_saved": 0,
            "contexts_archived": 0,
            "contexts_restored": 0,
            "compression_ratio": 0.0
        }

        logger.info("ContextCompressionEngine initialized successfully")

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Config file {config_path} not found, using defaults")
            return self._get_default_config()
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing config file: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration if config file is missing"""
        return {
            "context_management": {
                "phase_based_clearing": {
                    "enabled": True,
                    "max_context_tokens": 8000,
                    "compression_threshold": 6000
                },
                "toon_format": {
                    "enabled": True,
                    "compression_ratio_target": 0.65
                }
            }
        }

    def _initialize_rules(self) -> List[ContextRule]:
        """Initialize context management rules"""
        rules = [
            ContextRule(
                rule_id="PHASE_BASED_CLEARING",
                name="Phase-based Context Clearing",
                condition="phase_changed",
                action="clear_preserve_meta",
                priority=1
            ),
            ContextRule(
                rule_id="TOKEN_THRESHOLD_COMPRESSION",
                name="Token Threshold Compression",
                condition="context_tokens > compression_threshold",
                action="apply_toon_compression",
                priority=2
            ),
            ContextRule(
                rule_id="AGENT_ISOLATION",
                name="Agent Context Isolation",
                condition="agent_context_bubble_exceeded",
                action="isolate_agent_context",
                priority=3
            ),
            ContextRule(
                rule_id="DYNAMIC_LOADING",
                name="Dynamic Context Loading",
                condition="task_relevance_high",
                action="load_relevant_context",
                priority=4
            ),
            ContextRule(
                rule_id="CONTEXT_ARCHIVAL",
                name="Context Archival",
                condition="context_age > retention_period",
                action="archive_context",
                priority=5
            )
        ]
        return rules

    def update_phase(self, new_phase: str, preserve_context: List[str] = None):
        """
        Update the current phase and apply phase-based context clearing

        Args:
            new_phase: New phase identifier (e.g., "analysis", "prediction", "reporting")
            preserve_context: List of context types to preserve during clearing
        """
        old_phase = self.current_phase
        self.current_phase = new_phase

        logger.info(f"Phase changed from {old_phase} to {new_phase}")

        if self.config["context_management"]["phase_based_clearing"]["enabled"]:
            preserve_context = preserve_context or self.config["context_management"]["phase_based_clearing"]["preserve_on_clear"]
            self._apply_phase_based_clearing(preserve_context)

        # Apply relevant rules
        self._apply_rules({"phase_changed": True})

    def compress_context(self, agent_id: str, context_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compress context data using TOON format and other optimization techniques

        Args:
            agent_id: ID of the agent requesting compression
            context_data: Raw context data to compress

        Returns:
            Compressed context data
        """
        if not self.config["context_management"]["toon_format"]["enabled"]:
            return context_data

        try:
            # Apply TOON format compression
            compressed_data = encode(context_data)

            # Calculate compression ratio
            original_size = len(json.dumps(context_data))
            compressed_size = len(compressed_data)
            compression_ratio = compressed_size / original_size

            # Update metrics
            self.metrics["contexts_compressed"] += 1
            self.metrics["tokens_saved"] += (original_size - compressed_size)
            self.metrics["compression_ratio"] = (
                self.metrics["tokens_saved"] /
                max(1, self.metrics["contexts_compressed"] * original_size)
            )

            # Update context state
            self.context_states[agent_id] = ContextState(
                agent_id=agent_id,
                context_tokens=compressed_size,
                last_updated=datetime.now(),
                priority_score=self._calculate_priority_score(context_data),
                compression_applied=True
            )

            logger.info(f"Context compressed for agent {agent_id}: {compression_ratio:.2%} ratio")

            # Check if compression target is met
            target_ratio = self.config["context_management"]["toon_format"]["compression_ratio_target"]
            if compression_ratio > target_ratio:
                logger.warning(f"Compression ratio {compression_ratio:.2%} exceeds target {target_ratio:.2%}")

            return {"compressed_data": compressed_data, "original_format": "toon"}

        except Exception as e:
            logger.error(f"Error compressing context for agent {agent_id}: {e}")
            return context_data

    def load_relevant_context(self, agent_id: str, task_type: str, max_tokens: int = 2000) -> Dict[str, Any]:
        """
        Dynamically load relevant context based on task type and agent capabilities

        Args:
            agent_id: ID of the agent requesting context
            task_type: Type of task being performed
            max_tokens: Maximum tokens to load for context

        Returns:
            Relevant context data
        """
        relevant_context = {}
        loaded_tokens = 0

        # Priority-based context loading
        context_sources = self._get_context_priorities(agent_id, task_type)

        for source_name, source_data, priority in context_sources:
            if loaded_tokens >= max_tokens:
                break

            # Compress source if needed
            if self.config["context_management"]["toon_format"]["enabled"]:
                compressed_source = encode(source_data)
                source_size = len(compressed_source)
            else:
                source_size = len(json.dumps(source_data))

            if loaded_tokens + source_size <= max_tokens:
                relevant_context[source_name] = source_data
                loaded_tokens += source_size
            else:
                # Partial loading for large sources
                remaining_tokens = max_tokens - loaded_tokens
                partial_context = self._get_partial_context(source_data, remaining_tokens)
                if partial_context:
                    relevant_context[f"{source_name}_partial"] = partial_context
                break

        logger.info(f"Loaded {loaded_tokens} tokens of relevant context for agent {agent_id}")
        return relevant_context

    def archive_context(self, agent_id: str, context_data: Dict[str, Any], metadata: Dict[str, Any] = None):
        """
        Archive context data for future reference

        Args:
            agent_id: ID of the agent archiving context
            context_data: Context data to archive
            metadata: Additional metadata for the archive
        """
        try:
            # Create archive directory if it doesn't exist
            archive_dir = Path(self.config["context_management"]["phase_based_clearing"]["archive_path"])
            archive_dir.mkdir(parents=True, exist_ok=True)

            # Generate archive filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{agent_id}_context_{timestamp}.json"
            archive_path = archive_dir / filename

            # Prepare archive data
            archive_data = {
                "agent_id": agent_id,
                "timestamp": timestamp,
                "metadata": metadata or {},
                "context_data": context_data,
                "phase": self.current_phase,
                "compression_applied": self.context_states.get(agent_id, ContextState("", 0, datetime.now(), 0.0, False)).compression_applied
            }

            # Write archive
            with open(archive_path, 'w') as f:
                json.dump(archive_data, f, indent=2, default=str)

            # Update tracking
            self.archived_contexts[agent_id] = str(archive_path)
            self.metrics["contexts_archived"] += 1

            logger.info(f"Context archived for agent {agent_id}: {archive_path}")

        except Exception as e:
            logger.error(f"Error archiving context for agent {agent_id}: {e}")

    def restore_context(self, agent_id: str, archive_path: str = None) -> Optional[Dict[str, Any]]:
        """
        Restore archived context data

        Args:
            agent_id: ID of the agent requesting context restoration
            archive_path: Specific archive path to restore from

        Returns:
            Restored context data or None if not found
        """
        try:
            if archive_path is None:
                archive_path = self.archived_contexts.get(agent_id)

            if archive_path is None or not os.path.exists(archive_path):
                logger.warning(f"No archive found for agent {agent_id}")
                return None

            with open(archive_path, 'r') as f:
                archive_data = json.load(f)

            self.metrics["contexts_restored"] += 1
            logger.info(f"Context restored for agent {agent_id} from {archive_path}")

            return archive_data["context_data"]

        except Exception as e:
            logger.error(f"Error restoring context for agent {agent_id}: {e}")
            return None

    def get_context_state(self, agent_id: str) -> Optional[ContextState]:
        """Get current context state for an agent"""
        return self.context_states.get(agent_id)

    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        return self.metrics.copy()

    def _apply_phase_based_clearing(self, preserve_context: List[str]):
        """Apply phase-based context clearing rules"""
        logger.info(f"Applying phase-based clearing for phase: {self.current_phase}")

        # Archive contexts that don't need to be preserved
        for agent_id, state in list(self.context_states.items()):
            if state.agent_id not in preserve_context:
                self.archive_context(agent_id, {"state": state}, {"phase": self.current_phase})
                del self.context_states[agent_id]

    def _apply_rules(self, conditions: Dict[str, bool]):
        """Apply context management rules based on conditions"""
        for rule in self.rules:
            if not rule.enabled:
                continue

            if self._evaluate_rule_condition(rule, conditions):
                logger.info(f"Applying rule: {rule.name}")
                self._execute_rule_action(rule)

    def _evaluate_rule_condition(self, rule: ContextRule, conditions: Dict[str, bool]) -> bool:
        """Evaluate if a rule condition is met"""
        # Simplified condition evaluation - in production, this would be more sophisticated
        condition_mapping = {
            "phase_changed": "phase_changed" in conditions,
            "context_tokens > compression_threshold": any(
                state.context_tokens > self.config["context_management"]["phase_based_clearing"]["compression_threshold"]
                for state in self.context_states.values()
            ),
            # Add more condition evaluations as needed
        }
        return condition_mapping.get(rule.condition, False)

    def _execute_rule_action(self, rule: ContextRule):
        """Execute a rule action"""
        action_mapping = {
            "clear_preserve_meta": self._action_clear_preserve_meta,
            "apply_toon_compression": self._action_apply_toon_compression,
            "isolate_agent_context": self._action_isolate_agent_context,
            "load_relevant_context": self._action_load_relevant_context,
            "archive_context": self._action_archive_context
        }

        action_func = action_mapping.get(rule.action)
        if action_func:
            action_func()
        else:
            logger.warning(f"Unknown rule action: {rule.action}")

    def _action_clear_preserve_meta(self):
        """Clear context preserving meta agent state"""
        preserve_list = self.config["context_management"]["phase_based_clearing"]["preserve_on_clear"]
        self._apply_phase_based_clearing(preserve_list)

    def _action_apply_toon_compression(self):
        """Apply TOON compression to contexts exceeding threshold"""
        threshold = self.config["context_management"]["phase_based_clearing"]["compression_threshold"]
        for agent_id, state in self.context_states.items():
            if state.context_tokens > threshold and not state.compression_applied:
                logger.info(f"Applying compression to agent {agent_id} context")
                # In a real implementation, this would trigger compression

    def _action_isolate_agent_context(self):
        """Isolate agent contexts to prevent interference"""
        for agent_id in self.context_states.keys():
            logger.info(f"Isolating context for agent {agent_id}")
            # In a real implementation, this would create isolated context bubbles

    def _action_load_relevant_context(self):
        """Load relevant context for current phase"""
        logger.info("Loading relevant context for current phase")
        # In a real implementation, this would load phase-specific context

    def _action_archive_context(self):
        """Archive old contexts"""
        retention_hours = self.config["memory_hierarchy"]["level_3_agents"]["retention_minutes"] / 60
        cutoff_time = datetime.now() - timedelta(hours=retention_hours)

        for agent_id, state in list(self.context_states.items()):
            if state.last_updated < cutoff_time:
                self.archive_context(agent_id, {"state": state}, {"reason": "retention_expired"})
                del self.context_states[agent_id]

    def _calculate_priority_score(self, context_data: Dict[str, Any]) -> float:
        """Calculate priority score for context data"""
        # Simplified scoring - in production, this would be more sophisticated
        base_score = 0.5
        size_factor = min(1.0, len(json.dumps(context_data)) / 1000)
        recency_factor = 1.0  # Would factor in timestamps

        return base_score + size_factor * 0.3 + recency_factor * 0.2

    def _get_context_priorities(self, agent_id: str, task_type: str) -> List[Tuple[str, Dict, int]]:
        """Get prioritized list of context sources for an agent"""
        # This would return a list of (source_name, source_data, priority) tuples
        # For now, return empty list - would be implemented with actual context sources
        return []

    def _get_partial_context(self, source_data: Dict[str, Any], max_tokens: int) -> Dict[str, Any]:
        """Get partial context data within token limit"""
        # Simplified implementation - would be more sophisticated in production
        data_str = json.dumps(source_data)
        if len(data_str) <= max_tokens:
            return source_data

        # Truncate to fit within limit
        truncated = data_str[:max_tokens-10] + "..."
        return {"truncated_data": truncated}

# Global context compression engine instance
context_compression_engine = ContextCompressionEngine()