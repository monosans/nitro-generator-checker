from __future__ import annotations

import asyncio
import stat
from abc import ABCMeta, abstractmethod
from pathlib import Path

import aiofiles
from aiohttp import ClientConnectorError, ClientResponseError, ClientSession
from typing_extensions import override

from . import fs
from .utils import asyncify


class ABCResultHandler(metaclass=ABCMeta):
    __slots__ = ()

    async def pre_run(self) -> None:  # noqa: B027
        pass

    @abstractmethod
    async def save(self, *, gift_url: str) -> None:
        pass


class FileHandler(ABCResultHandler):
    __slots__ = ("_file_path", "_ready_event")

    def __init__(self, file_path: str, /) -> None:
        self._file_path = Path(file_path)
        self._ready_event = asyncio.Event()

    @override
    async def pre_run(self) -> None:
        if await asyncify(self._file_path.is_file)():
            await asyncify(fs.add_permission)(self._file_path, stat.S_IWUSR)
        elif await asyncify(self._file_path.exists)():
            msg = f"{self._file_path} must be a file"
            raise ValueError(msg)
        else:
            await asyncify(fs.create_or_fix_dir)(
                self._file_path.parent, permission=stat.S_IWUSR | stat.S_IXUSR
            )
        self._ready_event.set()

    @override
    async def save(self, *, gift_url: str) -> None:
        await self._ready_event.wait()
        async with aiofiles.open(self._file_path, "a", encoding="utf-8") as f:
            await f.write(f"\n{gift_url}")


class DiscordWebhookHandler(ABCResultHandler):
    __slots__ = ("_session", "_url")

    def __init__(self, *, session: ClientSession, url: str) -> None:
        self._session = session
        self._url = url

    @override
    async def save(self, *, gift_url: str) -> None:
        delay = 1
        while True:
            try:
                async with self._session.post(
                    self._url, json={"content": f"@everyone {gift_url}"}
                ):
                    pass
            except ClientConnectorError:
                continue
            except ClientResponseError as e:
                if e.status not in {500, 502}:
                    raise
                await asyncio.sleep(delay)
                delay *= 2
                continue
            break
