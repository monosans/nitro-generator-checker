from __future__ import annotations

import random
import string
import sys
from typing import Iterator

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override


class NitroGenerator(Iterator[str]):
    __slots__ = ("_characters",)

    def __init__(self) -> None:
        self._characters = string.ascii_letters + string.digits

    @override
    def __next__(self) -> str:
        return "".join(random.choices(self._characters, k=16))
