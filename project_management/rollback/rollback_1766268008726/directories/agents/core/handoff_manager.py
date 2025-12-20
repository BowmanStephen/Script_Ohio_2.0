"""
Handoff Manager - Sequential Handoff Coordination

Manages sequential handoff patterns between agents (assembly-line pattern).
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from agents.core.context_handoff import ContextHandoffManager
from agents.core.context_isolation import ContextIsolationManager

logger = logging.getLogger(__name__)


@dataclass
class HandoffChain:
    """Represents a sequential handoff chain"""

    chain_id: str
    agents: List[str]
    validation_gates: Dict[str, List[str]] = field(default_factory=dict)
    retry_config: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class HandoffResult:
    """Result of a handoff execution"""

    handoff_id: str
    from_agent: str
    to_agent: str
    success: bool
    output: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0
    retry_count: int = 0


class HandoffManager:
    """
    Manages sequential handoff patterns between agents.

    Features:
    - Assembly-line pattern (PM → Engineer → Reviewer)
    - Handoff validation gates
    - Retry logic for failed handoffs
    - Handoff monitoring and metrics
    """

    def __init__(self, isolation_manager: Optional[ContextIsolationManager] = None):
        """
        Initialize the handoff manager.

        Args:
            isolation_manager: Optional ContextIsolationManager instance
        """
        if isolation_manager is None:
            isolation_manager = ContextIsolationManager()

        self.isolation_manager = isolation_manager
        self.handoff_manager = ContextHandoffManager(isolation_manager)
        self.active_chains: Dict[str, HandoffChain] = {}
        self.handoff_results: List[HandoffResult] = []
        self.metrics: Dict[str, Any] = {
            "total_handoffs": 0,
            "successful_handoffs": 0,
            "failed_handoffs": 0,
            "retry_count": 0,
        }

    def create_handoff_chain(
        self,
        agents: List[str],
        validation_gates: Optional[Dict[str, List[str]]] = None,
        retry_config: Optional[Dict[str, Any]] = None,
    ) -> HandoffChain:
        """
        Create a sequential handoff chain.

        Args:
            agents: List of agent IDs in execution order
            validation_gates: Optional validation criteria per agent
            retry_config: Optional retry configuration

        Returns:
            HandoffChain
        """
        chain_id = str(uuid.uuid4())

        chain = HandoffChain(
            chain_id=chain_id,
            agents=agents,
            validation_gates=validation_gates or {},
            retry_config=retry_config or {"max_retries": 3, "retry_delay": 1.0},
        )

        self.active_chains[chain_id] = chain
        logger.info(f"Created handoff chain {chain_id} with {len(agents)} agents")

        return chain

    def execute_handoff(
        self,
        from_agent: str,
        to_agent: str,
        output: Any,
        validate: bool = True,
    ) -> HandoffResult:
        """
        Execute a handoff between two agents.

        Args:
            from_agent: Source agent ID
            to_agent: Target agent ID
            output: Output from source agent
            validate: Whether to validate output

        Returns:
            HandoffResult
        """
        import time

        start_time = time.time()
        handoff_id = str(uuid.uuid4())

        self.metrics["total_handoffs"] += 1

        try:
            # Validate output if requested
            if validate:
                validation_result = self._validate_output_quality(output, to_agent)
                if not validation_result["valid"]:
                    return HandoffResult(
                        handoff_id=handoff_id,
                        from_agent=from_agent,
                        to_agent=to_agent,
                        success=False,
                        error=f"Output validation failed: {validation_result['errors']}",
                        execution_time=time.time() - start_time,
                    )

            # Prepare handoff context
            if isinstance(output, dict):
                handoff_prep = self.handoff_manager.prepare_handoff(
                    from_agent, to_agent, output, validate=validate
                )
            else:
                # Convert output to dict if needed
                handoff_prep = self.handoff_manager.prepare_handoff(
                    from_agent, to_agent, {"result": output}, validate=validate
                )

            if not handoff_prep.get("success"):
                return HandoffResult(
                    handoff_id=handoff_id,
                    from_agent=from_agent,
                    to_agent=to_agent,
                    success=False,
                    error="Handoff preparation failed",
                    execution_time=time.time() - start_time,
                )

            # In production, would execute target agent here
            # For now, return success
            result = HandoffResult(
                handoff_id=handoff_id,
                from_agent=from_agent,
                to_agent=to_agent,
                success=True,
                output=handoff_prep.get("transformed_data"),
                execution_time=time.time() - start_time,
            )

            self.metrics["successful_handoffs"] += 1

        except Exception as e:
            result = HandoffResult(
                handoff_id=handoff_id,
                from_agent=from_agent,
                to_agent=to_agent,
                success=False,
                error=str(e),
                execution_time=time.time() - start_time,
            )

            self.metrics["failed_handoffs"] += 1

        self.handoff_results.append(result)
        logger.info(
            f"Handoff {handoff_id} from {from_agent} to {to_agent}: "
            f"{'success' if result.success else 'failed'}"
        )

        return result

    def execute_chain(
        self,
        chain: HandoffChain,
        initial_input: Any,
        retry_on_failure: bool = True,
    ) -> List[HandoffResult]:
        """
        Execute a complete handoff chain.

        Args:
            chain: HandoffChain to execute
            initial_input: Initial input for first agent
            retry_on_failure: Whether to retry on failure

        Returns:
            List of HandoffResult for each handoff
        """
        results = []
        current_output = initial_input

        for i in range(len(chain.agents) - 1):
            from_agent = chain.agents[i]
            to_agent = chain.agents[i + 1]

            # Get validation gates for this handoff
            validation_gates = chain.validation_gates.get(to_agent, [])

            # Execute handoff
            result = self.execute_handoff(
                from_agent, to_agent, current_output, validate=len(validation_gates) > 0
            )

            # Retry logic
            if not result.success and retry_on_failure:
                max_retries = chain.retry_config.get("max_retries", 3)
                retry_delay = chain.retry_config.get("retry_delay", 1.0)

                for retry in range(max_retries):
                    import time

                    time.sleep(retry_delay)
                    result.retry_count = retry + 1
                    self.metrics["retry_count"] += 1

                    result = self.execute_handoff(
                        from_agent,
                        to_agent,
                        current_output,
                        validate=len(validation_gates) > 0,
                    )

                    if result.success:
                        break

            results.append(result)

            if not result.success:
                logger.error(
                    f"Handoff chain {chain.chain_id} failed at {from_agent} → {to_agent}"
                )
                break

            # Update current output for next handoff
            current_output = result.output if result.output else current_output

        return results

    def _validate_output_quality(
        self, output: Any, target_agent: str
    ) -> Dict[str, Any]:
        """
        Validate output quality before handoff.

        Args:
            output: Output to validate
            target_agent: Target agent ID

        Returns:
            Validation result
        """
        errors = []

        # Basic validation
        if output is None:
            errors.append("Output is None")

        if isinstance(output, dict):
            if "success" in output and not output["success"]:
                errors.append("Output indicates failure")

            if "error" in output and not output.get("result"):
                errors.append("Output contains error but no result")

        return {"valid": len(errors) == 0, "errors": errors}

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get handoff metrics.

        Returns:
            Metrics dictionary
        """
        total = self.metrics["total_handoffs"]
        success_rate = self.metrics["successful_handoffs"] / total if total > 0 else 0.0

        return {
            **self.metrics,
            "success_rate": success_rate,
        }
