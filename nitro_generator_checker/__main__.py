from __future__ import annotations

import asyncio
import logging
import sys
from typing import TYPE_CHECKING, Dict

import aiofiles
import rich.traceback
from aiohttp import ClientSession, DummyCookieJar, TCPConnector
from rich.console import Console
from rich.logging import RichHandler
from typing_extensions import Any

from . import http
from .nitro_checker import NitroChecker
from .utils import bytes_decode

if sys.version_info >= (3, 11):
    try:
        import tomllib
    except ImportError:
        # Help users on older alphas
        if not TYPE_CHECKING:
            import tomli as tomllib
else:
    import tomli as tomllib


def set_event_loop_policy() -> None:
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    elif sys.implementation.name == "cpython" and sys.platform in {
        "darwin",
        "linux",
    }:
        try:
            import uvloop  # noqa: PLC0415
        except ImportError:
            pass
        else:
            asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


async def read_config(file: str, /) -> Dict[str, Any]:
    async with aiofiles.open(file, "rb") as f:
        content = await f.read()
    return tomllib.loads(bytes_decode(content))


def configure_logging(*, console: Console) -> None:
    rich.traceback.install(
        console=console, width=None, extra_lines=0, word_wrap=True
    )
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        datefmt=logging.Formatter.default_time_format,
        handlers=(
            RichHandler(
                console=console,
                omit_repeated_times=False,
                show_path=False,
                rich_tracebacks=True,
                tracebacks_extra_lines=0,
            ),
        ),
    )


async def main() -> None:
    console = Console()
    configure_logging(console=console)
    cfg = await read_config("config.toml")
    async with ClientSession(
        connector=TCPConnector(ssl=http.SSL_CONTEXT),
        headers=http.HEADERS,
        cookie_jar=DummyCookieJar(),
        raise_for_status=True,
        fallback_charset_resolver=http.fallback_charset_resolver,
    ) as session:
        await NitroChecker.from_mapping(
            cfg, console=console, session=session
        ).run()


if __name__ == "__main__":
    set_event_loop_policy()
    asyncio.run(main())
