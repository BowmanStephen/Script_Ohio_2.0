#!/usr/bin/env python3
"""
Script Ohio 2.0 Agent System Package

This package contains the intelligent agent system for college football analytics.
It provides modular, role-based agents with context optimization and orchestration.

Core Components:
- Analytics Orchestrator: Main coordination system
- Context Manager: Role-based context optimization
- Agent Framework: Base infrastructure for agent development
- Model Execution Engine: ML model integration and predictions
- Tool Loader: Dynamic tool loading and management

Author: Claude Code Assistant
Created: 2025-11-07
Version: 1.0
"""

import sys
from pathlib import Path

_SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

__version__ = "1.0.0"
__author__ = "Claude Code Assistant"

# Import core classes for easy access (lazily, to avoid optional deps)
try:
    from .analytics_orchestrator import AnalyticsOrchestrator, AnalyticsRequest
except Exception as exc:  # pylint: disable=broad-except
    AnalyticsOrchestrator = None  # type: ignore
    AnalyticsRequest = None  # type: ignore
    _INIT_ERROR = exc
else:
    _INIT_ERROR = None

from .core.context_manager import ContextManager, UserRole
from .core.agent_framework import AgentFactory, RequestRouter, BaseAgent, AgentRequest
from .core.tool_loader import ToolLoader, ToolCategory

__all__ = [
    'AnalyticsOrchestrator',
    'AnalyticsRequest',
    'ContextManager',
    'UserRole',
    'AgentFactory',
    'RequestRouter',
    'BaseAgent',
    'AgentRequest',
    'ToolLoader',
    'ToolCategory'
]

if _INIT_ERROR:
    import warnings

    warnings.warn(
        f"AnalyticsOrchestrator could not be imported at package init: {_INIT_ERROR}",
        ImportWarning,
        stacklevel=2,
    )