from __future__ import annotations

from rich.table import Table


class Counter:
    __slots__ = ("_total", "_valid")

    def __init__(self) -> None:
        self._total = 0
        self._valid = 0

    def add_total(self) -> None:
        self._total += 1

    def add_valid(self) -> None:
        self._valid += 1

    def as_rich_table(self) -> Table:
        table = Table("Total", "Valid")
        table.add_row(str(self._total), str(self._valid))
        return table
