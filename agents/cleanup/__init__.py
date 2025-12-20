#!/usr/bin/env python3
"""
Cleanup Sub-Agents Package

Specialized cleanup agents for autonomous codebase maintenance.
Each agent handles a specific cleanup domain with comprehensive safety validation.

Components:
- validation_manager: Pre/post-cleanup system validation
- state_manager: Cleanup operation state tracking
- rollback_manager: Emergency rollback and restore capabilities
- backup_cleanup_agent: Intelligent backup file management
- cache_cleanup_agent: Python cache directory optimization
- legacy_code_cleanup_agent: Post-migration cleanup
- test_file_organizer_agent: Test file organization
- documentation_streamliner_agent: Documentation consolidation

Author: Autonomous Code Orchestration System
Created: 2025-01-20
Version: 1.0
"""

__version__ = "1.0.0"
__author__ = "Autonomous Code Orchestration System"

# Import all cleanup components
from .validation_manager import ValidationManager
from .state_manager import StateManager
from .rollback_manager import RollbackManager

__all__ = [
    "ValidationManager",
    "StateManager",
    "RollbackManager"
]