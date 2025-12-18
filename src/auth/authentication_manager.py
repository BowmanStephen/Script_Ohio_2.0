"""
Centralized Authentication Manager for CFBD API

This module provides standardized authentication handling for all CFBD clients
in the Script Ohio 2.0 system, ensuring consistent authentication patterns
across REST, GraphQL, and legacy clients.

Key Features:
- Automatic key format detection and normalization
- Support for both access_token and Bearer token patterns
- Environment variable management
- Tier-aware authentication configuration
- Comprehensive error handling and validation
"""

import os
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class AuthenticationPattern(Enum):
    """Supported authentication patterns"""
    ACCESS_TOKEN = "access_token"  # CFBD v5.13.2+ preferred
    BEARER_HEADER = "bearer_header"  # GraphQL and manual requests
    LEGACY_API_KEY = "legacy_api_key"  # Deprecated - migrate to access_token


@dataclass
class AuthenticationConfig:
    """Configuration for CFBD authentication"""
    api_key: str
    pattern: AuthenticationPattern
    host: Optional[str] = None
    tier_level: int = 3  # Default to Tier 3
    user_agent: Optional[str] = None

    def __post_init__(self):
        """Validate and normalize configuration after initialization"""
        self.api_key = self._normalize_api_key(self.api_key)

    def _normalize_api_key(self, key: str) -> str:
        """Normalize API key format based on pattern"""
        if not key:
            raise ValueError("API key cannot be empty")

        key = key.strip()

        # Remove "Bearer " prefix for patterns that expect raw key
        if self.pattern != AuthenticationPattern.BEARER_HEADER and key.startswith("Bearer "):
            key = key.replace("Bearer ", "").strip()
            logger.info("🔑 Stripped 'Bearer ' prefix from API key for non-header pattern")

        # Add "Bearer " prefix for header patterns if missing
        if self.pattern == AuthenticationPattern.BEARER_HEADER and not key.startswith("Bearer "):
            key = f"Bearer {key}"
            logger.info("🔑 Added 'Bearer ' prefix to API key for header pattern")

        return key


class AuthenticationManager:
    """
    Centralized authentication manager for all CFBD clients

    This manager provides consistent authentication handling across:
    - REST API clients (using access_token)
    - GraphQL clients (using Bearer headers)
    - Legacy clients (migration support)
    """

    _instance = None
    _config = None

    def __new__(cls):
        """Singleton pattern to ensure consistent authentication across the system"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize authentication manager with environment-based configuration"""
        if self._initialized:
            return

        self._config = self._load_configuration()
        self._initialized = True
        logger.info(f"🔐 AuthenticationManager initialized with {self._config.pattern.value} pattern")

    def _load_configuration(self) -> AuthenticationConfig:
        """Load authentication configuration from environment variables"""
        # Try primary API key
        api_key = os.environ.get("CFBD_API_KEY")
        if not api_key:
            # Fallback to alternative environment variable
            api_key = os.environ.get("CFBD_API_TOKEN")

        if not api_key:
            raise ValueError(
                "❌ No CFBD API key found in environment variables. "
                "Set CFBD_API_KEY or CFBD_API_TOKEN environment variable."
            )

        # Determine authentication pattern based on usage
        # Default to ACCESS_TOKEN for REST clients, BEARER_HEADER for GraphQL
        pattern = AuthenticationPattern.ACCESS_TOKEN  # CFBD preferred pattern

        # Load tier level (default to 3)
        tier_level = int(os.environ.get("CFBD_TIER_LEVEL", "3"))

        # Load optional host override
        host = os.environ.get("CFBD_API_HOST")  # Optional host override

        # Load user agent
        user_agent = os.environ.get("CFBD_USER_AGENT", "Script-Ohio-2.0/1.0")

        return AuthenticationConfig(
            api_key=api_key,
            pattern=pattern,
            host=host,
            tier_level=tier_level,
            user_agent=user_agent
        )

    def configure_cfbd_client(self, client, client_type: str = "rest") -> None:
        """
        Configure any CFBD client with standardized authentication

        Args:
            client: CFBD client instance to configure
            client_type: Type of client ("rest", "graphql", "legacy")
        """
        try:
            if client_type == "rest":
                self._configure_rest_client(client)
            elif client_type == "graphql":
                self._configure_graphql_client(client)
            elif client_type == "legacy":
                self._configure_legacy_client(client)
            else:
                raise ValueError(f"Unsupported client type: {client_type}")

            logger.info(f"✅ Configured {client_type} client with {self._config.pattern.value} pattern")

        except Exception as e:
            logger.error(f"❌ Failed to configure {client_type} client: {e}")
            raise

    def _configure_rest_client(self, client) -> None:
        """Configure REST API client with the working api_key + api_key_prefix pattern"""
        # Handle both configuration objects and client instances
        if hasattr(client, 'api_key'):  # It's a configuration object
            # This is the working pattern based on scripts/check_key.py
            raw_key = self.get_api_key("raw")  # Get key without Bearer prefix
            client.api_key["Authorization"] = raw_key
            client.api_key_prefix["Authorization"] = "Bearer"

            # Set host if specified
            if self._config.host and hasattr(client, 'host'):
                client.host = self._config.host

        elif hasattr(client, 'configuration'):  # It's a client instance
            # This is the working pattern based on scripts/check_key.py
            raw_key = self.get_api_key("raw")  # Get key without Bearer prefix
            client.configuration.api_key["Authorization"] = raw_key
            client.configuration.api_key_prefix["Authorization"] = "Bearer"

            # Set host if specified
            if self._config.host and hasattr(client.configuration, 'host'):
                client.configuration.host = self._config.host

        elif hasattr(client, 'api'):  # Fallback for older CFBD versions
            raw_key = self.get_api_key("raw")
            client.api.configuration.api_key["Authorization"] = raw_key
            client.api.configuration.api_key_prefix["Authorization"] = "Bearer"

            # Set host if specified
            if self._config.host and hasattr(client.api.configuration, 'host'):
                client.api.configuration.host = self._config.host
        else:
            raise ValueError(f"Unsupported client type: {type(client)}")

    def _configure_graphql_client(self, client) -> None:
        """Configure GraphQL client with Bearer token header"""
        if hasattr(client, 'headers'):
            client.headers['Authorization'] = self._config.api_key
        elif hasattr(client, '_headers'):
            client._headers['Authorization'] = self._config.api_key
        else:
            # For manual request clients
            if hasattr(client, 'set_default_header'):
                client.set_default_header('Authorization', self._config.api_key)

    def _configure_legacy_client(self, client) -> None:
        """Configure legacy client using api_key + api_key_prefix pattern"""
        if hasattr(client, 'configuration'):
            # Legacy approach - maintain for backward compatibility
            raw_key = self._config.api_key
            if raw_key.startswith("Bearer "):
                raw_key = raw_key.replace("Bearer ", "").strip()

            client.configuration.api_key["Authorization"] = raw_key
            client.configuration.api_key_prefix["Authorization"] = "Bearer"

        # Set host if specified
        if self._config.host and hasattr(client.configuration, 'host'):
            client.configuration.host = self._config.host

    def get_bearer_headers(self) -> Dict[str, str]:
        """Get Bearer token headers for manual requests"""
        return {
            "Authorization": self._config.api_key,
            "User-Agent": self._config.user_agent or "Script-Ohio-2.0/1.0"
        }

    def get_api_key(self, format_type: str = "raw") -> str:
        """
        Get API key in specified format

        Args:
            format_type: "raw" (no prefix), "bearer" (with "Bearer " prefix)

        Returns:
            API key in requested format
        """
        if format_type == "bearer":
            if not self._config.api_key.startswith("Bearer "):
                return f"Bearer {self._config.api_key}"
            return self._config.api_key
        elif format_type == "raw":
            if self._config.api_key.startswith("Bearer "):
                return self._config.api_key.replace("Bearer ", "").strip()
            return self._config.api_key
        else:
            raise ValueError(f"Unsupported format_type: {format_type}")

    def validate_api_key(self) -> Dict[str, Any]:
        """
        Validate API key by testing CFBD API access

        Returns:
            Dictionary with validation results
        """
        try:
            import cfbd

            # Test with CFBD API using the working authentication pattern
            configuration = cfbd.Configuration()
            # Use the working api_key + api_key_prefix pattern
            raw_key = self.get_api_key("raw")
            configuration.api_key["Authorization"] = raw_key
            configuration.api_key_prefix["Authorization"] = "Bearer"

            if self._config.host:
                configuration.host = self._config.host

            api_instance = cfbd.GamesApi(cfbd.ApiClient(configuration))

            # Try to fetch a small dataset to validate
            games = api_instance.get_games(year=2024, week=1)

            return {
                "status": "success",
                "message": "API key is valid and working",
                "tier_level": self._config.tier_level,
                "api_key_length": len(self._config.api_key),
                "test_data_count": len(games) if games else 0
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"API key validation failed: {str(e)}",
                "tier_level": self._config.tier_level,
                "api_key_length": len(self._config.api_key)
            }

    def get_configuration_info(self) -> Dict[str, Any]:
        """Get current configuration information for debugging"""
        return {
            "pattern": self._config.pattern.value,
            "tier_level": self._config.tier_level,
            "api_key_length": len(self._config.api_key),
            "api_key_preview": f"{self._config.api_key[:8]}...{self._config.api_key[-8:]}",
            "has_bearer_prefix": self._config.api_key.startswith("Bearer "),
            "host": self._config.host,
            "user_agent": self._config.user_agent
        }

    def reset_configuration(self) -> None:
        """Reset configuration and force reload from environment"""
        self._config = None
        self._initialized = False
        logger.info("🔄 AuthenticationManager configuration reset")


# Global instance for system-wide consistency
auth_manager = AuthenticationManager()


def get_auth_manager() -> AuthenticationManager:
    """Get the global authentication manager instance"""
    return auth_manager


def configure_cfbd_client(client, client_type: str = "rest") -> None:
    """
    Convenience function to configure any CFBD client with standardized authentication

    Args:
        client: CFBD client instance to configure
        client_type: Type of client ("rest", "graphql", "legacy")
    """
    auth_manager.configure_cfbd_client(client, client_type)


def get_bearer_headers() -> Dict[str, str]:
    """Convenience function to get Bearer token headers"""
    return auth_manager.get_bearer_headers()


def validate_api_key() -> Dict[str, Any]:
    """Convenience function to validate API key"""
    return auth_manager.validate_api_key()


if __name__ == "__main__":
    # Test authentication manager when run as script
    print("🔐 Testing AuthenticationManager")
    print("=" * 40)

    # Show configuration info
    config_info = auth_manager.get_configuration_info()
    print(f"Pattern: {config_info['pattern']}")
    print(f"Tier Level: {config_info['tier_level']}")
    print(f"API Key Length: {config_info['api_key_length']}")
    print(f"Has Bearer Prefix: {config_info['has_bearer_prefix']}")

    # Validate API key
    print("\n🔑 Validating API key...")
    validation = auth_manager.validate_api_key()

    if validation["status"] == "success":
        print("✅ API key is valid and working!")
        print(f"   Tier Level: {validation['tier_level']}")
        print(f"   Test Data Count: {validation.get('test_data_count', 'N/A')}")
    else:
        print(f"❌ API key validation failed: {validation['message']}")

    print("\n🏁 AuthenticationManager test complete")