#!/usr/bin/env python3
"""
Script Ohio 2.0 Agent System Core Package

This package contains the core infrastructure components for the intelligent agent system.
It provides base classes, context management, and tool loading functionality.

Core Components:
- Agent Framework: Base classes and factory patterns for agents
- Context Manager: Role-based context optimization and management
- Tool Loader: Dynamic tool loading and permission management

Author: Claude Code Assistant
Created: 2025-11-07
Version: 1.0
"""

__version__ = "1.0.0"
__author__ = "Claude Code Assistant"

# Import core classes for easy access
from .agent_framework import AgentFactory, RequestRouter, BaseAgent, AgentRequest, PermissionLevel
from .context_manager import ContextManager, UserRole
from .tool_loader import ToolLoader, ToolCategory

__all__ = [
    'AgentFactory',
    'RequestRouter',
    'BaseAgent',
    'AgentRequest',
    'PermissionLevel',
    'ContextManager',
    'UserRole',
    'ToolLoader',
    'ToolCategory'
]