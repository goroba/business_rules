"""Integer data type."""

from __future__ import annotations

from collections.abc import Collection

from business_rules.data_types.base import DataType
from business_rules.data_types.pool import data_type
from business_rules.operators import implements

__all__ = ["IntegerDataType"]


@data_type("integer")
class IntegerDataType(DataType[int]):
    def cast(self, value: str) -> int:
        return int(value)

    def __str__(self, value: int) -> str:  # type: ignore[override]
        return str(value)

    @implements("is_null")
    def is_null(self, value: int | None) -> bool:
        return value is None

    @implements("is_not_null")
    def is_not_null(self, value: int | None) -> bool:
        return value is not None

    @implements("eq")
    def eq(self, left: int, right: int) -> bool:
        return left == right

    @implements("ne")
    def ne(self, left: int, right: int) -> bool:
        return left != right

    @implements("lt")
    def lt(self, left: int, right: int) -> bool:
        return left < right

    @implements("lte")
    def lte(self, left: int, right: int) -> bool:
        return left <= right

    @implements("gt")
    def gt(self, left: int, right: int) -> bool:
        return left > right

    @implements("gte")
    def gte(self, left: int, right: int) -> bool:
        return left >= right

    @implements("is_in")
    def is_in(self, left: int, values: Collection[int]) -> bool:
        return left in values

    @implements("is_not_in")
    def is_not_in(self, left: int, values: Collection[int]) -> bool:
        return left not in values
