from __future__ import annotations

from rich.table import Table


class Counter:
    __slots__ = ("total", "valid")

    def __init__(self) -> None:
        self.total = 0
        self.valid = 0

    def add_total(self) -> None:
        self.total += 1

    def add_valid(self) -> None:
        self.valid += 1

    def as_rich_table(self) -> Table:
        table = Table("Total", "Valid")
        table.add_row(str(self.total), str(self.valid))
        return table
