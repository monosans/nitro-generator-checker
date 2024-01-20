from __future__ import annotations

import asyncio
from abc import ABCMeta, abstractmethod

import aiofiles
import aiofiles.os
import aiofiles.ospath
from aiohttp import ClientSession
from typing_extensions import override


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

    @override
    async def pre_run(self) -> None:
        if await aiofiles.ospath.isdir(self.file_path):
            msg = "FileName must be a file, not a directory"
            raise ValueError(msg)
        await aiofiles.os.makedirs(self.file_path, exist_ok=True)
        self._ready_event.set()

    @override
    async def save(self, gift_url: str) -> None:
        await self._ready_event.wait()
        async with aiofiles.open(self.file_path, "a", encoding="utf-8") as f:
            await f.write(f"\n{gift_url}")


class DiscordWebhookHandler(ABCResultHandler):
    __slots__ = ("session", "url")

    def __init__(self, session: ClientSession, url: str) -> None:
        self.session = session
        self.url = url

    @override
    async def save(self, gift_url: str) -> None:
        async with self.session.post(
            self.url, json={"content": f"@everyone {gift_url}"}
        ):
            pass
