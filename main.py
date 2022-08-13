#!/usr/bin/env python3
from __future__ import annotations

import asyncio
from configparser import ConfigParser
from random import choice, choices
from string import ascii_letters, digits
from typing import List, NoReturn, Optional

from aiofiles import open as aopen
from aiohttp import ClientSession
from aiohttp_socks import ProxyConnector
from rich.console import Console
from rich.live import Live
from rich.table import Table


class NitroGeneratorChecker:
    __slots__ = (
        "session",
        "console",
        "threads",
        "webhook_url",
        "timeout",
        "file_name",
        "characters",
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
        self.session = session
        self.console = console or Console(highlight=False)
        self.threads = threads
        self.webhook_url = webhook_url or None
        self.timeout = timeout
        self.file_name = file_name
        self.characters = ascii_letters + digits
        self.count = 0
        self.valid_count = 0

    async def fetch(self, url: str) -> str:
        try:
            async with self.session.get(
                url, raise_for_status=True
            ) as response:
                return await response.text()
        except Exception as e:
            self.console.print(f"[red]Couldn't download proxies: {e}")
        return ""

    async def set_proxies(self) -> None:
        url = "https://api.proxyscrape.com/v2/?request=getproxies&protocol="
        protocols = ("http", "socks4", "socks5")
        coroutines = (self.fetch(url + proto) for proto in protocols)
        prox: List[str] = await asyncio.gather(*coroutines)
        self.proxies = tuple(
            f"{proto}://{proxy}"
            for proto, proxies in zip(protocols, prox)
            for proxy in proxies.strip().splitlines()
        )

    async def grab_proxies(self) -> NoReturn:
        while True:
            await asyncio.sleep(60)
            await self.set_proxies()

    async def checker(self, live: Live) -> NoReturn:
        while True:
            if not self.proxies:
                continue
            code = "".join(choices(self.characters, k=16))
            url = (
                f"https://discord.com/api/v9/entitlements/gift-codes/{code}"
                + "?with_application=false&with_subscription_plan=true"
            )
            proxy = choice(self.proxies)
            connector = ProxyConnector.from_url(proxy)
            try:
                async with ClientSession(connector=connector) as session:
                    async with session.get(
                        url, timeout=self.timeout
                    ) as response:
                        status = response.status
            except Exception as e:
                # Too many open files
                if isinstance(e, OSError) and e.errno == 24:
                    self.console.print(
                        "[red]Please, set Threads to lower value."
                    )
                continue
            if status == 404:
                self.console.print(f"{code} | Invalid")
                self.count += 1
                live.update(self.table)
            elif status == 429:
                self.console.print(f"{code} | {proxy} is temporarily blocked")
            elif status >= 400:
                self.console.print(f"{code} | {status}")
            else:
                gift = f"https://discord.gift/{code}"
                async with aopen(self.file_name, "a", encoding="utf-8") as f:
                    await f.write(f"\n{gift}")
                if self.webhook_url:
                    async with self.session.post(
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
        with Live(self.table, console=self.console) as live:
            coroutines = (self.checker(live) for _ in range(self.threads))
            await asyncio.gather(self.grab_proxies(), *coroutines)


async def main() -> None:
    config = ConfigParser()
    config.read("config.ini", encoding="utf-8")
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
    try:
        import uvloop
    except ImportError:
        pass
    else:
        uvloop.install()
    asyncio.run(main())
