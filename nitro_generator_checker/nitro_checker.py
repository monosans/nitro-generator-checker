from __future__ import annotations

import asyncio
import logging
from configparser import ConfigParser
from typing import Optional

from aiofiles import open as aopen
from aiohttp import ClientSession, DummyCookieJar
from aiohttp_socks import ProxyConnector
from rich.console import Console
from rich.live import Live

from .counter import Counter
from .nitro_generator import NitroGenerator
from .proxy_generator import ProxyGenerator

logger = logging.getLogger(__name__)


class NitroChecker:
    __slots__ = (
        "console",
        "counter",
        "file_name",
        "nitro_generator",
        "proxy_generator",
        "session",
        "threads",
        "timeout",
        "webhook_url",
    )

    def __init__(
        self,
        *,
        session: ClientSession,
        threads: int,
        webhook_url: Optional[str],
        timeout: float,
        file_name: str,
        console: Optional[Console] = None,
    ) -> None:
        self.nitro_generator = NitroGenerator()
        self.proxy_generator = ProxyGenerator(session)
        self.session = session
        self.console = console or Console()
        self.threads = threads
        self.webhook_url = webhook_url or None
        self.timeout = timeout
        self.file_name = file_name
        self.counter = Counter()

    @classmethod
    async def run_from_ini(
        cls, file_name: str, *, console: Optional[Console] = None
    ) -> None:
        config = ConfigParser()
        config.read(file_name, encoding="utf-8")
        cfg = config["DEFAULT"]
        async with ClientSession(cookie_jar=DummyCookieJar()) as session:
            ngc = cls(
                session=session,
                threads=cfg.getint("Threads", 900),
                webhook_url=cfg.get("WebhookURL"),
                timeout=cfg.getfloat("Timeout", 10),
                file_name=cfg.get("FileName", "nitro_codes.txt"),
                console=console,
            )
            await ngc.run()

    async def checker(self, live: Live) -> None:
        for code in self.nitro_generator:
            url = (
                f"https://discord.com/api/v9/entitlements/gift-codes/{code}"
                + "?with_application=false&with_subscription_plan=true"
            )
            proxy = self.proxy_generator.get_random_proxy()
            try:
                async with ProxyConnector.from_url(proxy) as connector:
                    async with ClientSession(
                        connector=connector, cookie_jar=self.session.cookie_jar
                    ) as session:
                        async with session.get(
                            url, timeout=self.timeout
                        ) as response:
                            status = response.status
            except Exception as e:
                # Too many open files
                if isinstance(e, OSError) and e.errno == 24:
                    logger.error("Please, set Threads to lower value.")
                continue
            if status == 404:
                logger.info("%s | Invalid", code)
                self.counter.add_total()
                live.update(self.counter.as_rich_table())
            elif status == 429:
                logger.info("%s proxy is temporarily blocked", proxy)
            elif status >= 400:
                logger.info("%s | HTTP status code %d", code, status)
            else:
                logger.info("%s | Valid", code)
                gift_url = f"https://discord.gift/{code}"
                await asyncio.gather(
                    self.save_gift(gift_url), self.send_webhook_msg(gift_url)
                )
                self.counter.add_valid()
                self.counter.add_total()
                live.update(self.counter.as_rich_table())

    async def save_gift(self, gift_url: str) -> None:
        async with aopen(self.file_name, "a", encoding="utf-8") as f:
            await f.write(f"\n{gift_url}")

    async def send_webhook_msg(self, gift_url: str) -> None:
        if not self.webhook_url:
            return
        async with self.session.post(
            self.webhook_url, json={"content": f"@everyone {gift_url}"}
        ):
            pass

    async def run(self) -> None:
        set_proxies_task = asyncio.create_task(
            self.proxy_generator.run_inf_loop()
        )
        await self.proxy_generator.wait_for_proxies()
        with Live(self.counter.as_rich_table(), console=self.console) as live:
            coroutines = (self.checker(live) for _ in range(self.threads))
            await asyncio.gather(set_proxies_task, *coroutines)
