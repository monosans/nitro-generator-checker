from __future__ import annotations

import asyncio
import logging
import sys
from configparser import ConfigParser

import aiofiles
import rich.traceback
from rich.console import Console
from rich.logging import RichHandler

from .nitro_checker import NitroChecker
from .utils import bytes_decode


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


def configure_logging(console: Console) -> None:
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


async def read_config(file: str) -> ConfigParser:
    async with aiofiles.open(file, "rb") as f:
        content = await f.read()
    cfg = ConfigParser(interpolation=None)
    cfg.read_string(bytes_decode(content))
    return cfg


async def main() -> None:
    console = Console()
    configure_logging(console)
    cfg = await read_config("config.ini")
    await NitroChecker.run_from_configparser(cfg, console=console)


if __name__ == "__main__":
    set_event_loop_policy()
    asyncio.run(main())
