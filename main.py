#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
from configparser import ConfigParser
from random import choice, choices
from string import ascii_letters, digits
from typing import NoReturn, Optional

from aiofiles import open
from aiohttp import ClientSession
from aiohttp_socks import ProxyConnector
from rich.console import Console
from rich.live import Live
from rich.table import Table


class NitroGeneratorChecker:
    __slots__ = (
        "s",
        "c",
        "threads",
        "webhook_url",
        "timeout",
        "file_name",
        "symbols",
        "count",
        "valid_count",
        "proxies",
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
        self.s = session
        self.c = console or Console(highlight=False)
        self.threads = threads
        self.webhook_url = webhook_url or None
        self.timeout = timeout
        self.file_name = file_name
        self.symbols = ascii_letters + digits
        self.count = 0
        self.valid_count = 0

    async def fetch(self, url: str) -> str:
        try:
            async with self.s.get(url, raise_for_status=True) as r:
                return await r.text()
        except Exception:
            return ""

    async def set_proxies(self) -> None:
        url = "https://api.proxyscrape.com/v2/?request=getproxies&protocol="
        protocols = ("http", "socks4", "socks5")
        coroutines = (self.fetch(f"{url}{proto}") for proto in protocols)
        prox = await asyncio.gather(*coroutines)
        self.proxies = tuple(
            f"{proto}://{proxy}"
            for proto, proxies in zip(protocols, prox)
            for proxy in proxies.strip().splitlines()
        )

    async def grab_proxies(self) -> NoReturn:
        while True:
            await asyncio.sleep(10)
            await self.set_proxies()

    async def checker(self, live: Live) -> None:
        while True:
            code = "".join(choices(self.symbols, k=16))
            url = f"https://discord.com/api/v9/entitlements/gift-codes/{code}"
            proxy = choice(self.proxies)
            try:
                async with ClientSession(
                    connector=ProxyConnector.from_url(proxy)
                ) as session:
                    async with session.get(
                        url,
                        params={
                            "with_application": "false",
                            "with_subscription_plan": "true",
                        },
                        timeout=self.timeout,
                    ) as r:
                        status = r.status
            except Exception as e:
                # Too many open files
                if isinstance(e, OSError) and e.errno == 24:
                    self.c.print(
                        "[red]Please, set THREADS to lower value.[/red]"
                    )
                continue
            if status == 404:
                self.c.print(f"{code} | Invalid")
                self.count += 1
                live.update(self.table)
            elif status == 429:
                self.c.print(f"{code} | {proxy} is temporarily blocked")
            elif 400 <= status < 600:
                self.c.print(f"{code} | {status}")
            else:
                gift = f"https://discord.gift/{code}"
                async with open(self.file_name, "a") as f:
                    await f.write(f"\n{gift}")
                if self.webhook_url:
                    async with self.s.post(
                        self.webhook_url, json={"content": f"@everyone {gift}"}
                    ):
                        pass
                self.valid_count += 1
                self.count += 1
                live.update(self.table)

    @property
    def table(self) -> Table:
        table = Table("Total", "Valid")
        table.add_row(str(self.count), str(self.valid_count))
        return table

    async def main(self) -> None:
        await self.set_proxies()
        with Live(self.table, console=self.c) as live:
            coroutines = (self.checker(live) for _ in range(self.threads))
            await asyncio.gather(self.grab_proxies(), *coroutines)


async def main() -> None:
    config = ConfigParser()
    config.read("config.ini")
    cfg = config["DEFAULT"]
    async with ClientSession() as session:
        await NitroGeneratorChecker(
            session=session,
            threads=cfg.getint("Threads", 900),
            webhook_url=cfg.get("WebhookURL"),
            timeout=cfg.getfloat("Timeout", 10),
            file_name=cfg.get("FileName", "nitro_codes.txt"),
        ).main()


if __name__ == "__main__":
    asyncio.run(main())
