"""Shared data-source utilities for Script Ohio 2.0."""

from .cfbd_client import CFBDClientConfig, CFBDRESTDataSource, build_cfbd_rest_client
from .cfbd_cache_manager import CFBDCacheManager, CFBDCacheConfig

try:
    from .cfbd_graphql import CFBDGraphQLClient
    GRAPHQL_AVAILABLE = True
except ImportError:
    CFBDGraphQLClient = None  # type: ignore
    GRAPHQL_AVAILABLE = False

__all__ = [
    "CFBDClientConfig",
    "CFBDRESTDataSource",
    "build_cfbd_rest_client",
    "CFBDCacheManager",
    "CFBDCacheConfig",
]

if GRAPHQL_AVAILABLE:
    __all__.append("CFBDGraphQLClient")

