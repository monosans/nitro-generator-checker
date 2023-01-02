from __future__ import annotations

import random
import string
from typing import Generator


class NitroGenerator:
    __slots__ = ("characters",)

    def __init__(self) -> None:
        self.characters = string.ascii_letters + string.digits

    def __iter__(self) -> Generator[str, None, None]:
        while True:
            yield "".join(random.choices(self.characters, k=16))
