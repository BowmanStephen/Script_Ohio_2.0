"""Shared rate-limiting helper for CFBD API calls."""
from __future__ import annotations

import logging
import time
from typing import Callable, Optional

DEFAULT_DELAY_SECONDS = 0.17  # 6 requests / second

logger = logging.getLogger(__name__)


def sleep_with_rate_limit(
    *,
    delay_seconds: float = DEFAULT_DELAY_SECONDS,
    after_request_hook: Optional[Callable[[float], None]] = None,
) -> None:
    """Sleep the configured amount between CFBD requests.

    Args:
        delay_seconds: Seconds to wait before the next request. Defaults to 0.17s.
        after_request_hook: Optional callback that receives the delay applied.
    """
    if delay_seconds <= 0:
        return

    logger.debug("Respecting CFBD rate limit, sleeping %.3fs", delay_seconds)
    time.sleep(delay_seconds)

    if after_request_hook:
        after_request_hook(delay_seconds)


__all__ = ["sleep_with_rate_limit", "DEFAULT_DELAY_SECONDS"]

