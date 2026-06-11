"""Date data type."""

from __future__ import annotations

from collections.abc import Collection
from datetime import date

from business_rules.data_types.base import DataType
from business_rules.data_types.pool import data_type
from business_rules.operators import implements

__all__ = ["DateDataType"]


@data_type("date")
class DateDataType(DataType[date]):
    def do_cast(self, value: str) -> date:
        return date.fromisoformat(value)

    def __str__(self, value: date) -> str:  # type: ignore[override]
        return value.isoformat()

    @implements("is_null")
    def is_null(self, value: date | None) -> bool:
        return value is None

    @implements("is_not_null")
    def is_not_null(self, value: date | None) -> bool:
        return value is not None

    @implements("eq")
    def eq(self, left: date, right: date) -> bool:
        return left == right

    @implements("ne")
    def ne(self, left: date, right: date) -> bool:
        return left != right

    @implements("lt")
    def lt(self, left: date, right: date) -> bool:
        return left < right

    @implements("lte")
    def lte(self, left: date, right: date) -> bool:
        return left <= right

    @implements("gt")
    def gt(self, left: date, right: date) -> bool:
        return left > right

    @implements("gte")
    def gte(self, left: date, right: date) -> bool:
        return left >= right

    @implements("is_in")
    def is_in(self, left: date, values: Collection[date]) -> bool:
        return left in values

    @implements("is_not_in")
    def is_not_in(self, left: date, values: Collection[date]) -> bool:
        return left not in values
