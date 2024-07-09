from __future__ import annotations

import asyncio
import functools
from typing import TYPE_CHECKING

import charset_normalizer

if TYPE_CHECKING:
    from typing import Callable, Coroutine

    from typing_extensions import Any, ParamSpec, TypeVar

    T = TypeVar("T")
    P = ParamSpec("P")


background_tasks: set[asyncio.Task[Any]] = set()


def create_background_task(coro: Coroutine[Any, Any, Any], /) -> None:
    task = asyncio.create_task(coro)
    background_tasks.add(task)
    task.add_done_callback(background_tasks.discard)


def bytes_decode(b: bytes, /) -> str:
    return str(charset_normalizer.from_bytes(b)[0])


def asyncify(f: Callable[P, T], /) -> Callable[P, asyncio.Future[T]]:
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> asyncio.Future[T]:
        return asyncio.get_running_loop().run_in_executor(
            None, functools.partial(f, *args, **kwargs)
        )

    return functools.update_wrapper(wrapper, f)
