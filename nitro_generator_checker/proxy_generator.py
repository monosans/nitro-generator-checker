from __future__ import annotations

import asyncio
import logging
import random
from typing import List, NoReturn

from aiohttp import ClientSession

logger = logging.getLogger(__name__)


class ProxyGenerator:
    __slots__ = ("proxies", "ready_event", "session")

    def __init__(self, session: ClientSession) -> None:
        self.session = session
        self.ready_event = asyncio.Event()

    async def set_proxies(self) -> None:
        url = "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/{}.txt"
        protocols = ("http", "socks4", "socks5")
        coroutines = (self._fetch(url.format(proto)) for proto in protocols)
        prox: List[str] = await asyncio.gather(*coroutines)
        proxies = tuple(
            f"{proto}://{proxy}"
            for proto, proxies in zip(protocols, prox)
            for proxy in proxies.strip().splitlines()
        )
        if proxies:
            self.proxies = proxies
            self.ready_event.set()

    async def run_inf_loop(self) -> NoReturn:
        while True:
            await self.set_proxies()
            await asyncio.sleep(60)

    def get_random_proxy(self) -> str:
        return random.choice(self.proxies)

    async def _fetch(self, url: str) -> str:
        try:
            async with self.session.get(url, raise_for_status=True) as response:
                await response.read()
            return await response.text()
        except Exception as e:
            logger.error(
                "Couldn't download proxies | %s.%s | %s",
                e.__class__.__module__,
                e.__class__.__qualname__,
                e,
            )
        return ""
