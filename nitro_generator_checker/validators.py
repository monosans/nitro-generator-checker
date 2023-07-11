from __future__ import annotations

import asyncio
import logging
import re
import sys
from typing import Optional

logger = logging.getLogger(__name__)


def max_connections(value: int) -> int:
    if value <= 0:
        msg = "MaxConnections must be positive"
        raise ValueError(msg)
    max_supported = _get_supported_max_connections()
    if not max_supported or value <= max_supported:
        return value
    logger.warning(
        "MaxConnections value is too high. "
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
    import resource

    soft_limit, hard_limit = resource.getrlimit(resource.RLIMIT_NOFILE)
    logger.debug(
        "MaxConnections soft limit = %d, hard limit = %d, infinity = %d",
        soft_limit,
        hard_limit,
        resource.RLIM_INFINITY,
    )
    if soft_limit != hard_limit:
        try:
            resource.setrlimit(resource.RLIMIT_NOFILE, (hard_limit, hard_limit))
        except ValueError as e:
            logger.warning("Failed setting MaxConnections: %s", e)
        else:
            soft_limit = hard_limit
    if soft_limit == resource.RLIM_INFINITY:
        return None
    return soft_limit


def webhook_url(value: Optional[str]) -> None:
    if value is not None and not re.match(
        r"https:\/\/discord\.com\/api\/webhooks\/[^\/]+\/[^\/]+", value
    ):
        msg = "WebhookURL does not match the pattern"
        raise ValueError(msg)


def timeout(value: float) -> None:
    if value <= 0:
        msg = "Timeout must be positive"
        raise ValueError(msg)
