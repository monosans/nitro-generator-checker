#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
from random import choice, choices
from string import ascii_letters, digits
from typing import NoReturn, Optional

from aiofiles import open
from aiohttp import ClientSession
from aiohttp_socks import ProxyConnector
from rich.console import Console
from rich.live import Live
from rich.table import Table

import config


class NitroGeneratorChecker:
    def __init__(
        self,
        *,
        session: ClientSession,
        threads: int = 950,
        webhook_url: Optional[str] = None,
        timeout: float = 10,
        file_name: str = "nitro_codes.txt",
        console: Optional[Console] = None,
    ) -> None:
        self.s = session
        self.c = console or Console(highlight=False)
        self.THREADS = threads
        self.WEBHOOK_URL = webhook_url or None
        self.TIMEOUT = timeout
        self.FILE_NAME = file_name
        self.SYMBOLS = ascii_letters + digits
        self.count = 0
        self.valid_count = 0

    async def fetch(self, url: str) -> str:
        async with self.s.get(url) as r:
            return await r.text()

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
            code = "".join(choices(self.SYMBOLS, k=16))
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
                        timeout=self.TIMEOUT,
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
                live.update(self.get_table())
            elif status == 429:
                self.c.print(f"{code} | {proxy} is temporarily blocked")
            elif 400 <= status < 600:
                self.c.print(f"{code} | {status}")
            else:
                gift = f"https://discord.gift/{code}"
                async with open(self.FILE_NAME, "a") as f:
                    await f.write(f"\n{gift}")
                if self.WEBHOOK_URL:
                    async with self.s.post(
                        self.WEBHOOK_URL, json={"content": f"@everyone {gift}"}
                    ):
                        pass
                self.valid_count += 1
                self.count += 1
                live.update(self.get_table())

    def get_table(self) -> Table:
        table = Table()
        table.add_column("Total")
        table.add_column("Valid")
        table.add_row(str(self.count), str(self.valid_count))
        return table

    async def main(self) -> None:
        await self.set_proxies()
        with Live(self.get_table(), console=self.c) as live:
            coroutines = (self.checker(live) for _ in range(self.THREADS))
            await asyncio.gather(self.grab_proxies(), *coroutines)


async def main() -> None:
    async with ClientSession() as session:
        await NitroGeneratorChecker(
            session=session,
            threads=config.THREADS,
            webhook_url=config.WEBHOOK_URL,
            timeout=config.TIMEOUT,
            file_name=config.FILE_NAME,
        ).main()


if __name__ == "__main__":
    asyncio.run(main())
