#!/usr/bin/env python3
"""
MCP Health Check Module for Agent System Integration

This module provides lightweight health check functions that can be imported
by the agent orchestrator and context management system to monitor MCP server
status without running full diagnostics.

Features:
- Quick health summary for checkpoint reports
- Detailed health dashboard for system status
- Critical server verification
- Available tool listing for dynamic selection
- Result caching to avoid repeated diagnostics
"""

import json
import time
from dataclasses import asdict
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

# Import diagnostic functions from the main script
try:
    from mcp_servers.diagnose_mcp_setup import (
        load_configs,
        diagnose_all,
        get_project_root,
        MCPServerResult,
        DiagnosticContext,
    )
except ImportError:
    # Fallback if import fails
    load_configs = None
    diagnose_all = None
    get_project_root = None
    MCPServerResult = None
    DiagnosticContext = None

# Cache configuration
_CACHE_TTL = 300  # 5 minutes
_cache: Optional[Dict[str, Any]] = None
_cache_timestamp: float = 0.0

# Critical servers that must be working for core functionality
CRITICAL_SERVERS = [
    "agent_orchestrator",
    "filesystem",
    "database_sqlite",
]


def _get_cached_results() -> Optional[Tuple[List[MCPServerResult], DiagnosticContext]]:
    """Get cached diagnostic results if still valid."""
    global _cache, _cache_timestamp
    
    if _cache is None:
        return None
    
    current_time = time.time()
    if current_time - _cache_timestamp > _CACHE_TTL:
        _cache = None
        return None
    
    # Reconstruct results from cache
    if load_configs is None or diagnose_all is None or get_project_root is None:
        return None
    
    project_root = get_project_root()
    ctx = load_configs(project_root)
    
    # Re-run diagnostics if cache expired or invalid
    results = diagnose_all(ctx, project_root)
    return results, ctx


def _cache_results(results: List[MCPServerResult], ctx: DiagnosticContext) -> None:
    """Cache diagnostic results with timestamp."""
    global _cache, _cache_timestamp
    
    _cache = {
        "results": [asdict(r) for r in results],
        "context": {
            "desktop_config_path": str(ctx.desktop_config_path) if ctx.desktop_config_path else None,
            "project_config_path": str(ctx.project_config_path) if ctx.project_config_path else None,
            "prereqs": ctx.prereqs,
        }
    }
    _cache_timestamp = time.time()


def _run_diagnostics(use_cache: bool = True) -> Tuple[List[MCPServerResult], DiagnosticContext]:
    """Run diagnostics, using cache if available and valid."""
    if use_cache:
        cached = _get_cached_results()
        if cached is not None:
            return cached
    
    if load_configs is None or diagnose_all is None or get_project_root is None:
        raise ImportError(
            "Cannot import diagnostic functions. Ensure diagnose_mcp_setup.py is available."
        )
    
    project_root = get_project_root()
    ctx = load_configs(project_root)
    results = diagnose_all(ctx, project_root)
    
    # Cache the results
    _cache_results(results, ctx)
    
    return results, ctx


def get_mcp_health_summary(use_cache: bool = True) -> Dict[str, Any]:
    """
    Get a lightweight health summary for checkpoint reports.
    
    Returns only non-WORKING servers to keep summaries concise.
    Perfect for inclusion in 75% context window checkpoint reports.
    
    Args:
        use_cache: Whether to use cached results (default: True)
    
    Returns:
        Dictionary with:
        - status: Overall status (healthy / degraded / critical)
        - total_servers: Total number of configured servers
        - working: Number of working servers
        - needs_setup: Number of servers needing setup
        - not_installed: Number of servers not installed
        - errors: Number of servers with errors
        - critical_status: Status of critical servers
        - issues: List of non-working servers with their top issue
        - timestamp: When this summary was generated
    """
    try:
        results, ctx = _run_diagnostics(use_cache=use_cache)
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": time.time(),
        }
    
    # Count statuses
    counts = {"WORKING": 0, "NEEDS_SETUP": 0, "NOT_INSTALLED": 0, "ERROR": 0}
    for r in results:
        counts[r.status] = counts.get(r.status, 0) + 1
    
    # Check critical servers
    critical_status = {}
    critical_issues = []
    for server_name in CRITICAL_SERVERS:
        server_result = next((r for r in results if r.name == server_name), None)
        if server_result:
            critical_status[server_name] = server_result.status
            if server_result.status != "WORKING":
                critical_issues.append({
                    "name": server_name,
                    "status": server_result.status,
                    "top_issue": server_result.issues[0] if server_result.issues else "Unknown issue",
                })
    
    # Determine overall status
    if counts["ERROR"] > 0 or any(s["status"] == "ERROR" for s in critical_issues):
        overall_status = "critical"
    elif counts["NOT_INSTALLED"] > 0 or critical_issues:
        overall_status = "degraded"
    elif counts["NEEDS_SETUP"] > 0:
        overall_status = "degraded"
    else:
        overall_status = "healthy"
    
    # Collect non-working servers (for checkpoint reports, we only show issues)
    issues = []
    for r in results:
        if r.status != "WORKING":
            issues.append({
                "name": r.name,
                "status": r.status,
                "category": r.category,
                "top_issue": r.issues[0] if r.issues else "No specific issue reported",
            })
    
    return {
        "status": overall_status,
        "total_servers": len(results),
        "working": counts["WORKING"],
        "needs_setup": counts["NEEDS_SETUP"],
        "not_installed": counts["NOT_INSTALLED"],
        "errors": counts["ERROR"],
        "critical_status": critical_status,
        "critical_issues": critical_issues,
        "issues": issues,
        "timestamp": time.time(),
    }


def get_mcp_health_dashboard(use_cache: bool = True) -> Dict[str, Any]:
    """
    Get detailed health dashboard with all server information.
    
    Returns comprehensive status for all MCP servers, suitable for
    detailed system status endpoints or debugging.
    
    Args:
        use_cache: Whether to use cached results (default: True)
    
    Returns:
        Dictionary with:
        - summary: Overall summary statistics
        - servers: Detailed information for each server
        - prerequisites: Prerequisite tool availability
        - timestamp: When this dashboard was generated
    """
    try:
        results, ctx = _run_diagnostics(use_cache=use_cache)
    except Exception as e:
        return {
            "error": str(e),
            "timestamp": time.time(),
        }
    
    # Build summary
    counts = {"WORKING": 0, "NEEDS_SETUP": 0, "NOT_INSTALLED": 0, "ERROR": 0}
    for r in results:
        counts[r.status] = counts.get(r.status, 0) + 1
    
    # Build server details
    servers = []
    for r in results:
        server_info = {
            "name": r.name,
            "status": r.status,
            "category": r.category,
            "command": r.command,
            "args": r.args,
            "origins": {
                "from_desktop": r.origins.from_desktop,
                "from_project": r.origins.from_project,
            },
            "issues": r.issues,
            "env_warnings": r.env_warnings,
            "setup_instructions": r.setup_instructions,
            "description": r.extra_info.get("description"),
            "troubleshooting": r.extra_info.get("troubleshooting", []),
        }
        servers.append(server_info)
    
    return {
        "summary": {
            "total_servers": len(results),
            "working": counts["WORKING"],
            "needs_setup": counts["NEEDS_SETUP"],
            "not_installed": counts["NOT_INSTALLED"],
            "errors": counts["ERROR"],
            "health_percentage": (counts["WORKING"] / len(results) * 100) if results else 0,
        },
        "servers": servers,
        "prerequisites": ctx.prereqs,
        "timestamp": time.time(),
    }


def check_critical_mcps(use_cache: bool = True) -> Tuple[bool, List[Dict[str, str]]]:
    """
    Quick check of critical MCP servers.
    
    Returns True if all critical servers are working, False otherwise.
    Also returns a list of failing critical servers with their status.
    
    Args:
        use_cache: Whether to use cached results (default: True)
    
    Returns:
        Tuple of (all_critical_working: bool, failing_servers: List[Dict])
    """
    try:
        results, _ = _run_diagnostics(use_cache=use_cache)
    except Exception as e:
        # If diagnostics fail, assume critical servers are not working
        return False, [{"name": "diagnostics", "status": "ERROR", "issue": str(e)}]
    
    failing = []
    for server_name in CRITICAL_SERVERS:
        server_result = next((r for r in results if r.name == server_name), None)
        if server_result and server_result.status != "WORKING":
            failing.append({
                "name": server_name,
                "status": server_result.status,
                "issue": server_result.issues[0] if server_result.issues else "Unknown issue",
            })
    
    return len(failing) == 0, failing


def get_available_mcp_tools(use_cache: bool = True) -> List[str]:
    """
    Get list of working MCP server names for dynamic tool selection.
    
    This can be used by the orchestrator to determine which MCP tools
    are available for use in agent workflows.
    
    Args:
        use_cache: Whether to use cached results (default: True)
    
    Returns:
        List of server names with WORKING status
    """
    try:
        results, _ = _run_diagnostics(use_cache=use_cache)
    except Exception:
        return []
    
    return [r.name for r in results if r.status == "WORKING"]


def clear_cache() -> None:
    """Clear the diagnostic result cache to force fresh diagnostics."""
    global _cache, _cache_timestamp
    _cache = None
    _cache_timestamp = 0.0


def get_cache_info() -> Dict[str, Any]:
    """Get information about the current cache state."""
    global _cache, _cache_timestamp
    
    if _cache is None:
        return {
            "cached": False,
            "age_seconds": None,
        }
    
    age = time.time() - _cache_timestamp
    return {
        "cached": True,
        "age_seconds": age,
        "ttl_seconds": _CACHE_TTL,
        "expires_in_seconds": max(0, _CACHE_TTL - age),
    }

