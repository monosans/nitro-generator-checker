from __future__ import annotations

import asyncio
import logging
import sys
import urllib.parse
from typing import Optional

logger = logging.getLogger(__name__)


def max_connections(value: int, /) -> int:
    if value <= 0:
        msg = "max_connections must be positive"
        raise ValueError(msg)
    max_supported = _get_supported_max_connections()
    if not max_supported or value <= max_supported:
        return value
    logger.warning(
        "max_connections value is too high. "
        "Your OS supports a maximum of %d. "
        "The config value will be ignored and %d will be used.",
        max_supported,
        max_supported,
    )
    return max_supported


def _get_supported_max_connections() -> Optional[int]:
    if sys.platform == "win32":
        if isinstance(
            asyncio.get_event_loop_policy(),
            asyncio.WindowsSelectorEventLoopPolicy,
        ):
            return 512
        return None
    import resource  # noqa: PLC0415

    soft_limit, hard_limit = resource.getrlimit(resource.RLIMIT_NOFILE)
    logger.debug(
        "max_connections soft limit = %d, hard limit = %d, infinity = %d",
        soft_limit,
        hard_limit,
        resource.RLIM_INFINITY,
    )
    if soft_limit != hard_limit:
        try:
            resource.setrlimit(resource.RLIMIT_NOFILE, (hard_limit, hard_limit))
        except ValueError as e:
            logger.warning("Failed setting max_connection: %s", e)
        else:
            soft_limit = hard_limit
    if soft_limit == resource.RLIM_INFINITY:
        return None
    return soft_limit


def webhook_url(value: Optional[str], /) -> None:
    if value is None:
        return
    url = urllib.parse.urlparse(value)
    if not url.scheme or not url.netloc:
        msg = f"invalid webhook_url: {value}"
        raise ValueError(msg)


def timeout(value: float, /) -> None:
    if value <= 0:
        msg = "timeout must be positive"
        raise ValueError(msg)
