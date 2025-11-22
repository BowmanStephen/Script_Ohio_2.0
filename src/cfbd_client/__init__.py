"""
CFBD Client Module - Unified Implementation

This module provides the UnifiedCFBDClient, which is the canonical CFBD API client
for Script Ohio 2.0. All legacy clients have been deprecated.

For new code, always use:
    from src.cfbd_client.unified_client import UnifiedCFBDClient
"""

from .unified_client import UnifiedCFBDClient
from .cfbd_cache_manager import CFBDCacheManager, CFBDCacheConfig

__all__ = ["UnifiedCFBDClient", "CFBDCacheManager", "CFBDCacheConfig"]
