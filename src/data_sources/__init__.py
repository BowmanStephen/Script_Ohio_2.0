"""Shared data-source utilities for Script Ohio 2.0."""

from .cfbd_cache_manager import CFBDCacheConfig, CFBDCacheManager

try:
    from .cfbd_graphql import CFBDGraphQLClient

    GRAPHQL_AVAILABLE = True
except ImportError:
    CFBDGraphQLClient = None  # type: ignore
    GRAPHQL_AVAILABLE = False

__all__ = [
    "CFBDCacheManager",
    "CFBDCacheConfig",
]

if GRAPHQL_AVAILABLE:
    __all__.append("CFBDGraphQLClient")
