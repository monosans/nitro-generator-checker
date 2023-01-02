from __future__ import annotations

import random
import string
from typing import Iterator


class NitroGenerator(Iterator[str]):
    __slots__ = ("characters",)

    def __init__(self) -> None:
        self.characters = string.ascii_letters + string.digits

    def __next__(self) -> str:
        return "".join(random.choices(self.characters, k=16))
