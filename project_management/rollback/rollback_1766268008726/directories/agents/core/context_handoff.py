"""
Context Handoff - Context Transfer Between Agents

Handles context transfer and validation during agent handoffs.
"""

import logging
from typing import Any, Dict, Optional

from agents.core.context_isolation import ContextIsolationManager

logger = logging.getLogger(__name__)


class ContextHandoffManager:
    """
    Manages context handoffs between agents in sequential workflows.

    Features:
    - Context validation before handoff
    - Context transformation for target agent
    - Handoff monitoring and logging
    """

    def __init__(self, isolation_manager: ContextIsolationManager):
        """
        Initialize the context handoff manager.

        Args:
            isolation_manager: ContextIsolationManager instance
        """
        self.isolation_manager = isolation_manager

    def prepare_handoff(
        self,
        from_agent: str,
        to_agent: str,
        output_data: Dict[str, Any],
        validate: bool = True,
    ) -> Dict[str, Any]:
        """
        Prepare context for handoff between agents.

        Args:
            from_agent: Source agent ID
            to_agent: Target agent ID
            output_data: Output data from source agent
            validate: Whether to validate output data

        Returns:
            Prepared context for target agent
        """
        if validate:
            validation_result = self._validate_output(output_data)
            if not validation_result["valid"]:
                logger.warning(
                    f"Output validation failed for {from_agent}: "
                    f"{validation_result['errors']}"
                )

        # Transform output for target agent
        transformed = self._transform_for_target(output_data, to_agent)

        # Create handoff context
        handoff_context = self.isolation_manager.handoff_context(
            from_agent, to_agent, transformed, filter_irrelevant=True
        )

        return {
            "success": True,
            "handoff_context": handoff_context,
            "transformed_data": transformed,
        }

    def _validate_output(self, output_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate output data before handoff.

        Args:
            output_data: Output data to validate

        Returns:
            Validation result
        """
        errors = []

        # Check for required fields
        if "success" not in output_data:
            errors.append("Missing 'success' field")

        # Check for result or error
        if "result" not in output_data and "error" not in output_data:
            errors.append("Missing 'result' or 'error' field")

        return {"valid": len(errors) == 0, "errors": errors}

    def _transform_for_target(
        self, output_data: Dict[str, Any], target_agent: str
    ) -> Dict[str, Any]:
        """
        Transform output data for target agent.

        Args:
            output_data: Output data from source agent
            target_agent: Target agent ID

        Returns:
            Transformed data
        """
        # Simple transformation - extract relevant data
        # In production, use agent-specific transformation logic

        transformed = {
            "from_previous_agent": True,
            "previous_result": output_data.get("result"),
            "previous_error": output_data.get("error"),
            "previous_success": output_data.get("success", False),
        }

        # Add task-specific data if present
        if "task" in output_data:
            transformed["task"] = output_data["task"]

        if "objective" in output_data:
            transformed["objective"] = output_data["objective"]

        return transformed
