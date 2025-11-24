"""Script Ohio core package."""

from .observability import configure_logging

# Ensure structured logging is configured for any `src.*` importers.
configure_logging()

__all__ = ["configure_logging"]

