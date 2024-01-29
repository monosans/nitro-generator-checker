from __future__ import annotations

import asyncio
from typing import Coroutine, Set

import charset_normalizer

from .typing_compat import Any

background_tasks: Set[asyncio.Task[Any]] = set()


def create_background_task(coro: Coroutine[Any, Any, Any]) -> None:
    task = asyncio.create_task(coro)
    background_tasks.add(task)
    task.add_done_callback(background_tasks.discard)


def bytes_decode(b: bytes) -> str:
    return str(charset_normalizer.from_bytes(b)[0])
