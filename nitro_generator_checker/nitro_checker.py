from __future__ import annotations

import asyncio
import logging
from configparser import ConfigParser
from types import MappingProxyType
from typing import Optional, Tuple

from aiohttp import ClientSession, ClientTimeout, DummyCookieJar
from aiohttp_socks import ProxyConnector
from rich.console import Console
from rich.live import Live

from . import result_handlers, validators
from .counter import Counter
from .nitro_generator import NitroGenerator
from .proxy_generator import ProxyGenerator
from .utils import create_background_task

logger = logging.getLogger(__name__)
HEADERS = MappingProxyType(
    {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; rv:120.0)"
            " Gecko/20100101 Firefox/120.0"
        )
    }
)


class NitroChecker:
    __slots__ = (
        "console",
        "counter",
        "max_connections",
        "nitro_generator",
        "proxy_generator",
        "session",
        "timeout",
        "result_handlers",
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
        webhook_url = webhook_url or None
        validators.webhook_url(webhook_url)

        self.console = console or Console()
        self.counter = Counter()
        self.max_connections = validators.max_connections(max_connections)
        self.nitro_generator = NitroGenerator()
        self.proxy_generator = ProxyGenerator(session)
        self.session = session
        self.timeout = ClientTimeout(total=timeout, sock_connect=float("inf"))

        file_handler = result_handlers.FileHandler(file_name)
        self.result_handlers: Tuple[result_handlers.ABCResultHandler, ...] = (
            (
                file_handler,
                result_handlers.DiscordWebhookHandler(session, webhook_url),
            )
            if webhook_url
            else (file_handler,)
        )

    @classmethod
    async def run_from_configparser(
        cls, config: ConfigParser, *, console: Optional[Console] = None
    ) -> None:
        cfg = config["DEFAULT"]
        async with ClientSession(
            headers=HEADERS, cookie_jar=DummyCookieJar()
        ) as session:
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
        await self.proxy_generator.ready_event.wait()
        for code in self.nitro_generator:
            url = (
                f"https://discord.com/api/v9/entitlements/gift-codes/{code}"
                "?with_application=false&with_subscription_plan=true"
            )
            proxy = self.proxy_generator.get_random_proxy()
            try:
                connector = ProxyConnector.from_url(proxy)
                async with ClientSession(
                    connector=connector,
                    headers=HEADERS,
                    cookie_jar=self.session.cookie_jar,
                    timeout=self.timeout,
                ) as session, session.get(url) as response:
                    pass
            except asyncio.TimeoutError:
                logger.info("%s proxy timed out", proxy)
            except OSError as e:
                # Too many open files
                if e.errno == 24:  # noqa: PLR2004
                    logger.error("Please, set MaxConnections to lower value.")
            except Exception:
                pass
            else:
                status = response.status
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
                    for handler in self.result_handlers:
                        create_background_task(handler.save(gift_url))
                    self.counter.add_valid()
                    self.counter.add_total()
                    live.update(self.counter.as_rich_table())

    async def run(self) -> None:
        with Live(self.counter.as_rich_table(), console=self.console) as live:
            await asyncio.gather(
                self.proxy_generator.run_inf_loop(),
                *(
                    result_handler.pre_run()
                    for result_handler in self.result_handlers
                ),
                *(self.checker(live) for _ in range(self.max_connections)),
            )
