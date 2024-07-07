from __future__ import annotations

import ssl
from types import MappingProxyType

import certifi
import charset_normalizer
from aiohttp import ClientResponse, hdrs

from .utils import bytes_decode

SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())
HEADERS: MappingProxyType[str, str] = MappingProxyType({
    hdrs.USER_AGENT: (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"  # noqa: E501
    )
})


class NoCharsetHeaderError(Exception):
    pass


def fallback_charset_resolver(r: ClientResponse, b: bytes) -> str:  # noqa: ARG001
    return charset_normalizer.from_bytes(b)[0].encoding


def get_response_text(*, response: ClientResponse, content: bytes) -> str:
    try:
        return content.decode(response.get_encoding())
    except (NoCharsetHeaderError, UnicodeDecodeError):
        return bytes_decode(content)
