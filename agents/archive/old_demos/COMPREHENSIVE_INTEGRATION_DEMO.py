#!/usr/bin/env python3
"""Comprehensive Integration Demonstration (Deprecated)

This script previously exercised the legacy `agents.system` stack. It now proxies to
`agents.demo_agent_system.run_demo`, which showcases the modern
`AnalyticsOrchestrator` and production agents. The legacy implementation has been
removed to prevent accidental usage.
"""

import sys
import warnings

from agents.demo_agent_system import run_demo

warnings.warn(
    "COMPREHENSIVE_INTEGRATION_DEMO is deprecated. Running the modern "
    "AnalyticsOrchestrator demo instead.",
    DeprecationWarning,
    stacklevel=2,
)


if __name__ == "__main__":
    success = run_demo()
    sys.exit(0 if success else 1)
