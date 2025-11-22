"""
Legacy agent system package (DEPRECATED).

The modern Script Ohio 2.0 stack uses `agents.analytics_orchestrator.AnalyticsOrchestrator`
as the single entry point. This package is retained only for historical reference and
will be removed in a future release.
"""

from warnings import warn

warn(
    "The `agents.system` package is deprecated. Use "
    "`agents.analytics_orchestrator.AnalyticsOrchestrator` instead.",
    DeprecationWarning,
    stacklevel=2,
)

