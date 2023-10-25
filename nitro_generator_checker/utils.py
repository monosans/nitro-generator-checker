from __future__ import annotations

import asyncio
from typing import Callable, Coroutine, Set

from typing_extensions import Any, TypeVar

T = TypeVar("T")

background_tasks: Set[asyncio.Task[Any]] = set()


def create_background_task(coro: Coroutine[Any, Any, Any]) -> None:
    task = asyncio.create_task(coro)
    background_tasks.add(task)
    task.add_done_callback(background_tasks.discard)


def sync_to_async(func: Callable[[], T]) -> asyncio.Future[T]:
    loop = asyncio.get_running_loop()
    return loop.run_in_executor(None, func)
