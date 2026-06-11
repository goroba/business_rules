"""DateTime data type."""

from __future__ import annotations

from collections.abc import Collection
from datetime import datetime

from business_rules.data_types.base import DataType
from business_rules.data_types.pool import data_type
from business_rules.operators import implements

__all__ = ["DateTimeDataType"]


@data_type("datetime")
class DateTimeDataType(DataType[datetime]):
    def do_cast(self, value: str) -> datetime:
        return datetime.fromisoformat(value)

    def __str__(self, value: datetime) -> str:  # type: ignore[override]
        return value.isoformat()

    @implements("is_null")
    def is_null(self, value: datetime | None) -> bool:
        return value is None

    @implements("is_not_null")
    def is_not_null(self, value: datetime | None) -> bool:
        return value is not None

    @implements("eq")
    def eq(self, left: datetime, right: datetime) -> bool:
        return left == right

    @implements("ne")
    def ne(self, left: datetime, right: datetime) -> bool:
        return left != right

    @implements("lt")
    def lt(self, left: datetime, right: datetime) -> bool:
        return left < right

    @implements("lte")
    def lte(self, left: datetime, right: datetime) -> bool:
        return left <= right

    @implements("gt")
    def gt(self, left: datetime, right: datetime) -> bool:
        return left > right

    @implements("gte")
    def gte(self, left: datetime, right: datetime) -> bool:
        return left >= right

    @implements("is_in")
    def is_in(self, left: datetime, values: Collection[datetime]) -> bool:
        return left in values

    @implements("is_not_in")
    def is_not_in(self, left: datetime, values: Collection[datetime]) -> bool:
        return left not in values
