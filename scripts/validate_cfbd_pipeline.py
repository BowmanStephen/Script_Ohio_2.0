"""Run an end-to-end validation of the CFBD integrated orchestrator."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Use simplified orchestrator (backward compatible)
from agents.simplified_analytics_orchestrator import SimplifiedAnalyticsOrchestrator as AnalyticsOrchestrator, AnalyticsRequest


def main() -> int:
    orchestrator = AnalyticsOrchestrator()
    request = AnalyticsRequest(
        user_id="cfbd-validator",
        query="Generate team insight snapshot",
        query_type="analysis",
        parameters={
            "team": None,  # Use actual team from data
            "season": datetime.utcnow().year,
            "week": 12,
            "include_live_scoreboard": True,
        },
        context_hints={"role": "analyst"},  # Simplified: context_hints still accepted but not used for role filtering
    )
    response = orchestrator.process_analytics_request(request)
    payload = {
        "status": response.status,
        "execution_time": response.execution_time,
        "insights": response.insights[:3] if response.insights else [],
        "has_results": response.results is not None,
        "live_scoreboard_events": orchestrator.get_live_scoreboard_events(limit=3),
    }
    print(json.dumps(payload, indent=2, default=str))
    return 0 if response.status != "error" else 1


if __name__ == "__main__":
    raise SystemExit(main())
