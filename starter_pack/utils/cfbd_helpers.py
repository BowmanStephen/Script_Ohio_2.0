"""Convenience helpers for accessing the CFBD API in diagnostics and QA scripts."""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Iterator, Optional

from starter_pack.utils.cfbd_loader import (
    CFBDLoader,
    CFBDLoaderError,
    CFBDSession,
    DEFAULT_HOST,
    live_cfbd_session,
)


def _resolve_api_key(explicit_key: Optional[str] = None) -> str:
    key = explicit_key or os.environ.get("CFBD_API_KEY") or os.environ.get("CFBD_API_TOKEN")
    if not key:
        raise CFBDLoaderError("CFBD API key missing. Set CFBD_API_KEY or pass api_key.")
    return key


def _resolve_host(explicit_host: Optional[str] = None) -> str:
    return explicit_host or os.environ.get("CFBD_API_HOST", DEFAULT_HOST)


def build_cfbd_loader(*, api_key: Optional[str] = None, host: Optional[str] = None) -> CFBDLoader:
    """
    Return a CFBDLoader instance that reuses the shared authentication +
    host selection logic. Diagnostics scripts can call this to fetch data
    without re-implementing rate limiting or auth.
    """

    return CFBDLoader(api_key=_resolve_api_key(api_key), host=_resolve_host(host))


@contextmanager
def cfbd_session(*, api_key: Optional[str] = None, host: Optional[str] = None) -> Iterator[CFBDSession]:
    """
    Context manager wrapping ``live_cfbd_session`` with the canonical auth +
    host configuration. This allows QA utilities to simply call::

        with cfbd_session() as session:
            games = session.games_api.get_games(year=2025)
    """

    with live_cfbd_session(api_key=_resolve_api_key(api_key), host=_resolve_host(host)) as session:
        yield session


__all__ = ["CFBDLoaderError", "CFBDSession", "DEFAULT_HOST", "build_cfbd_loader", "cfbd_session"]

