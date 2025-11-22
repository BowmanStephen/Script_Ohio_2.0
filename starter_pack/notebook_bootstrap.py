#!/usr/bin/env python3
"""
Backwards-compatible shim that re-exports the canonical bootstrap helper.

The full implementation now lives in `starter_pack.utils.bootstrap`. This file
remains so older notebooks that import `starter_pack.notebook_bootstrap`
continue to work without any edits.
"""

from starter_pack.utils.bootstrap import (  # noqa: F401
    BootstrapResult,
    ESSENTIAL_DEPENDENCIES,
    ensure_notebook_environment,
)

__all__ = [
    "BootstrapResult",
    "ESSENTIAL_DEPENDENCIES",
    "ensure_notebook_environment",
]


if __name__ == "__main__":
    ensure_notebook_environment()
