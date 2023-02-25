from __future__ import annotations

import asyncio
import logging
from configparser import ConfigParser
from typing import Optional

from aiofiles import open as aopen
from aiohttp import ClientSession, ClientTimeout, DummyCookieJar
from aiohttp_socks import ProxyConnector
from rich.console import Console
from rich.live import Live

from . import validators
from .counter import Counter
from .nitro_generator import NitroGenerator
from .proxy_generator import ProxyGenerator

logger = logging.getLogger(__name__)


class NitroChecker:
    __slots__ = (
        "console",
        "counter",
        "file_name",
        "max_connections",
        "nitro_generator",
        "proxy_generator",
        "session",
        "timeout",
        "webhook_url",
    )

    def __init__(
        self,
        *,
        session: ClientSession,
        max_connections: int,
        webhook_url: Optional[str],
        timeout: float,
        file_name: str,
        console: Optional[Console] = None,
    ) -> None:
        validators.timeout(timeout)
        validators.webhook_url(webhook_url)

        self.console = console or Console()
        self.counter = Counter()
        self.file_name = file_name
        self.max_connections = validators.max_connections(max_connections)
        self.nitro_generator = NitroGenerator()
        self.proxy_generator = ProxyGenerator(session)
        self.session = session
        self.timeout = ClientTimeout(total=timeout, sock_connect=float("inf"))
        self.webhook_url = webhook_url or None

    @classmethod
    async def run_from_configparser(
        cls, config: ConfigParser, *, console: Optional[Console] = None
    ) -> None:
        cfg = config["DEFAULT"]
        async with ClientSession(cookie_jar=DummyCookieJar()) as session:
            ngc = cls(
                session=session,
                max_connections=cfg.getint("MaxConnections", 512),
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
                "?with_application=false&with_subscription_plan=true"
            )
            proxy = self.proxy_generator.get_random_proxy()
            try:
                async with ProxyConnector.from_url(proxy) as connector:
                    async with ClientSession(
                        connector=connector,
                        cookie_jar=self.session.cookie_jar,
                        timeout=self.timeout,
                    ) as session:
                        async with session.get(url) as response:
                            status = response.status
            except asyncio.TimeoutError:
                logger.info("%s proxy timed out", proxy)
            except OSError as e:
                # Too many open files
                if e.errno == 24:  # noqa: PLR2004
                    logger.error("Please, set MaxConnections to lower value.")
            except Exception:
                pass
            else:
                if status == 404:  # noqa: PLR2004
                    logger.info("%s | Invalid", code)
                    self.counter.add_total()
                    live.update(self.counter.as_rich_table())
                elif status == 429:  # noqa: PLR2004
                    logger.info("%s proxy is temporarily blocked", proxy)
                elif status >= 400:  # noqa: PLR2004
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
        set_proxies_task = asyncio.create_task(self.proxy_generator.run_inf_loop())
        await self.proxy_generator.wait_for_proxies()
        with Live(self.counter.as_rich_table(), console=self.console) as live:
            coroutines = (self.checker(live) for _ in range(self.max_connections))
            await asyncio.gather(set_proxies_task, *coroutines)
