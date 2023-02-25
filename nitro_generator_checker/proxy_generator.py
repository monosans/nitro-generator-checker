from __future__ import annotations

import asyncio
import logging
import random
from typing import List, NoReturn, Tuple

from aiohttp import ClientSession

logger = logging.getLogger(__name__)


class ProxyGenerator:
    __slots__ = ("proxies", "session")

    def __init__(self, session: ClientSession) -> None:
        self.session = session
        self.proxies: Tuple[str, ...] = ()

    async def set_proxies(self) -> None:
        url = (
            "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/{}.txt"
        )
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

    async def run_inf_loop(self) -> NoReturn:
        while True:
            await self.set_proxies()
            await asyncio.sleep(60)

    async def wait_for_proxies(self) -> None:
        while not self.proxies:
            await asyncio.sleep(0)

    def get_random_proxy(self) -> str:
        return random.choice(self.proxies)

    async def _fetch(self, url: str) -> str:
        try:
            async with self.session.get(url, raise_for_status=True) as response:
                return await response.text()
        except Exception as e:
            logger.error(
                "Couldn't download proxies | %s | %s", e.__class__.__qualname__, e
            )
        return ""
