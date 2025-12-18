"""
Authentication module for Script Ohio 2.0

This module provides centralized authentication management for all CFBD API clients,
ensuring consistent authentication patterns across REST, GraphQL, and legacy clients.
"""

from .authentication_manager import (
    AuthenticationManager,
    AuthenticationConfig,
    AuthenticationPattern,
    get_auth_manager,
    configure_cfbd_client,
    get_bearer_headers,
    validate_api_key,
    auth_manager
)

__all__ = [
    'AuthenticationManager',
    'AuthenticationConfig',
    'AuthenticationPattern',
    'get_auth_manager',
    'configure_cfbd_client',
    'get_bearer_headers',
    'validate_api_key',
    'auth_manager'
]