from __future__ import annotations

import asyncio
import logging
import random
from typing import TYPE_CHECKING

from aiohttp import hdrs

from .http import get_response_text

if TYPE_CHECKING:
    from typing import NoReturn

    from aiohttp import ClientSession

logger = logging.getLogger(__name__)


class ProxyGenerator:
    __slots__ = ("_etag", "_proxies", "_session", "ready_event")

    def __init__(self, *, session: ClientSession) -> None:
        self._etag: str | None = None
        self._session = session
        self.ready_event = asyncio.Event()

    async def set_proxies(self) -> None:
        headers = {hdrs.IF_NONE_MATCH: self._etag} if self._etag else None
        try:
            async with self._session.get(
                "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/all.txt",
                headers=headers,
            ) as response:
                if response.status == 304:  # noqa: PLR2004
                    return
                self._etag = response.headers.get(hdrs.ETAG)
                content = await response.read()
            r = get_response_text(response=response, content=content)
        except Exception as e:
            logger.error(
                "Failed downloading proxies | %s.%s | %s",
                e.__class__.__module__,
                e.__class__.__qualname__,
                e,
            )
        else:
            if r:
                self._proxies = tuple(r.splitlines())
                self.ready_event.set()

    async def run_inf_loop(self) -> NoReturn:
        while True:
            await self.set_proxies()
            await asyncio.sleep(10)

    def get_random_proxy(self) -> str:
        return random.choice(self._proxies)
