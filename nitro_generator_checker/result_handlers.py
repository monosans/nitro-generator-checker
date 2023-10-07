from __future__ import annotations

import asyncio
from abc import ABCMeta, abstractmethod
from pathlib import Path

from aiofile import async_open
from aiohttp import ClientSession

from .utils import sync_to_async


class ABCResultHandler(metaclass=ABCMeta):
    __slots__ = ()

    async def pre_run(self) -> None:  # noqa: B027
        pass

    @abstractmethod
    async def save(self, gift_url: str) -> None:
        pass


class FileHandler(ABCResultHandler):
    __slots__ = ("file_path", "_ready_event")

    def __init__(self, file_path: str) -> None:
        self.file_path = file_path
        self._ready_event = asyncio.Event()

    async def pre_run(self) -> None:
        def inner() -> None:
            path = Path(self.file_path)
            if path.is_dir():
                msg = "FileName must be a file, not a directory"
                raise ValueError(msg)
            path.parent.mkdir(parents=True, exist_ok=True)

        await sync_to_async(inner)
        self._ready_event.set()

    async def save(self, gift_url: str) -> None:
        await self._ready_event.wait()
        async with async_open(self.file_path, "a", encoding="utf-8") as f:
            await f.write(f"\n{gift_url}")


class DiscordWebhookHandler(ABCResultHandler):
    __slots__ = ("session", "url")

    def __init__(self, session: ClientSession, url: str) -> None:
        self.session = session
        self.url = url

    async def save(self, gift_url: str) -> None:
        async with self.session.post(
            self.url, json={"content": f"@everyone {gift_url}"}
        ):
            pass
