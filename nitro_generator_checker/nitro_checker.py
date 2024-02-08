from __future__ import annotations

import asyncio
import logging
from typing import Mapping, Optional, Tuple

from aiohttp import ClientSession, ClientTimeout
from aiohttp_socks import ProxyConnector
from rich.console import Console
from rich.live import Live
from typing_extensions import Any, Self

from . import result_handlers, validators
from .counter import Counter
from .http import HEADERS, SSL_CONTEXT, fallback_charset_resolver
from .nitro_generator import NitroGenerator
from .proxy_generator import ProxyGenerator
from .utils import create_background_task

logger = logging.getLogger(__name__)


class NitroChecker:
    __slots__ = (
        "_console",
        "_counter",
        "_max_connections",
        "_nitro_generator",
        "_proxy_generator",
        "_result_handlers",
        "_session",
        "_timeout",
    )

    def __init__(
        self,
        *,
        console: Console,
        file_name: str,
        max_connections: int,
        session: ClientSession,
        timeout: float,
        webhook_url: Optional[str],
    ) -> None:
        validators.timeout(timeout)
        webhook_url = webhook_url or None
        validators.webhook_url(webhook_url)

        self._console = console
        self._counter = Counter()
        self._max_connections = validators.max_connections(max_connections)
        self._nitro_generator = NitroGenerator()
        self._proxy_generator = ProxyGenerator(session=session)
        self._session = session
        self._timeout = ClientTimeout(total=timeout, sock_connect=float("inf"))

        file_handler = result_handlers.FileHandler(file_name)
        self._result_handlers: Tuple[result_handlers.ABCResultHandler, ...] = (
            (
                file_handler,
                result_handlers.DiscordWebhookHandler(
                    session=session, url=webhook_url
                ),
            )
            if webhook_url
            else (file_handler,)
        )

    @classmethod
    def from_mapping(
        cls,
        mapping: Mapping[str, Any],
        /,
        *,
        console: Console,
        session: ClientSession,
    ) -> Self:
        return cls(
            console=console,
            file_name=mapping["file_name"],
            max_connections=mapping["max_connections"],
            session=session,
            timeout=mapping["timeout"],
            webhook_url=mapping["webhook_url"],
        )

    async def checker(self, *, live: Live) -> None:
        await self._proxy_generator.ready_event.wait()
        for code in self._nitro_generator:
            url = (
                f"https://discord.com/api/v9/entitlements/gift-codes/{code}"
                "?with_application=false&with_subscription_plan=true"
            )
            proxy = self._proxy_generator.get_random_proxy()
            try:
                connector = ProxyConnector.from_url(proxy, ssl=SSL_CONTEXT)
                async with ClientSession(
                    connector=connector,
                    headers=HEADERS,
                    cookie_jar=self._session.cookie_jar,
                    timeout=self._timeout,
                    fallback_charset_resolver=fallback_charset_resolver,
                ) as session, session.get(url) as response:
                    pass
            except asyncio.TimeoutError:
                logger.info("%s proxy timed out", proxy)
            except OSError as e:
                # Too many open files
                if e.errno == 24:  # noqa: PLR2004
                    logger.error("Please, set max_connections to lower value.")
            except Exception:
                pass
            else:
                status = response.status
                if status == 404:  # noqa: PLR2004
                    logger.info("%s | Invalid", code)
                    self._counter.add_total()
                    live.update(self._counter.as_rich_table())
                elif status == 429:  # noqa: PLR2004
                    logger.info("%s | Rate limited", proxy)
                elif status >= 400:  # noqa: PLR2004
                    logger.info("%s | HTTP status code %d", code, status)
                else:
                    logger.info("%s | Valid", code)
                    gift_url = f"https://discord.gift/{code}"
                    for handler in self._result_handlers:
                        create_background_task(handler.save(gift_url=gift_url))
                    self._counter.add_total()
                    self._counter.add_valid()
                    live.update(self._counter.as_rich_table())

    async def run(self) -> None:
        with Live(self._counter.as_rich_table(), console=self._console) as live:
            await asyncio.gather(
                self._proxy_generator.run_inf_loop(),
                *(
                    result_handler.pre_run()
                    for result_handler in self._result_handlers
                ),
                *(
                    self.checker(live=live)
                    for _ in range(self._max_connections)
                ),
            )
