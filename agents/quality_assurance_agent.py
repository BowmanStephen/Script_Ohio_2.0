"""Agent responsible for CFBD integration QA and telemetry inspection."""
from __future__ import annotations

from collections import Counter, deque
from statistics import mean
from typing import Any, Deque, Dict, List, Optional

from agents.core.agent_framework import BaseAgent, AgentCapability, PermissionLevel

try:
    from cfbd_client import CFBDDataProvider
except ImportError:  # pragma: no cover - optional dependency
    CFBDDataProvider = None  # type: ignore


class QualityAssuranceAgent(BaseAgent):
    """Surfaces telemetry summaries, schema diff alerts, and health checks."""

    def __init__(
        self,
        agent_id: str,
        telemetry_events: Optional[Deque[Dict[str, Any]]] = None,
        cfbd_data_provider: Optional["CFBDDataProvider"] = None,
        tool_loader=None,
    ) -> None:
        super().__init__(
            agent_id=agent_id,
            name="Quality Assurance Agent",
            permission_level=PermissionLevel.READ_EXECUTE,
            tool_loader=tool_loader,
        )
        self.telemetry_events = telemetry_events or deque(maxlen=200)
        self.cfbd_data_provider = cfbd_data_provider

    def _define_capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability(
                name="cfbd_health_check",
                description="Summarize CFBD client telemetry and error rates",
                permission_required=PermissionLevel.READ_EXECUTE,
                tools_required=["telemetry"],
                data_access=["cfbd_logs"],
                execution_time_estimate=0.5,
            ),
            AgentCapability(
                name="cfbd_recent_events",
                description="Return the latest telemetry events for inspection",
                permission_required=PermissionLevel.READ_EXECUTE,
                tools_required=["telemetry"],
                data_access=["cfbd_logs"],
                execution_time_estimate=0.2,
            ),
        ]

    def _execute_action(
        self,
        action: str,
        parameters: Dict[str, Any],
        user_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        if action == "cfbd_health_check":
            return self._health_check()
        if action == "cfbd_recent_events":
            return self._recent_events(parameters)
        raise ValueError(f"Unknown action {action}")

    def _health_check(self) -> Dict[str, Any]:
        events = list(self.telemetry_events)
        if not events:
            return {"status": "no_data", "message": "No telemetry events recorded yet"}

        status_counts = Counter(event.get("outcome", "unknown") for event in events)
        latencies = [event.get("latency_ms", 0.0) for event in events if event.get("latency_ms")]
        avg_latency = mean(latencies) if latencies else 0.0

        return {
            "status": "ok",
            "total_events": len(events),
            "status_counts": dict(status_counts),
            "average_latency_ms": round(avg_latency, 2),
            "latest_event": events[-1],
        }

    def _recent_events(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        limit = int(parameters.get("limit", 5))
        events = list(self.telemetry_events)[-limit:]
        return {"status": "ok", "events": events}


__all__ = ["QualityAssuranceAgent"]
