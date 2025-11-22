import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.append(str(REPO_ROOT))


@pytest.fixture(scope="session")
def orchestrator():
    from agents.analytics_orchestrator import AnalyticsOrchestrator

    return AnalyticsOrchestrator()
