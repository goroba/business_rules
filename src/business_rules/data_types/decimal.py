"""Decimal data type."""

from __future__ import annotations

from collections.abc import Collection
from decimal import Decimal

from business_rules.data_types.base import DataType
from business_rules.data_types.pool import data_type
from business_rules.operators import implements

__all__ = ["DecimalDataType"]


@data_type("decimal")
class DecimalDataType(DataType[Decimal]):
    def cast(self, value: str) -> Decimal:
        return Decimal(value)

    def __str__(self, value: Decimal) -> str:  # type: ignore[override]
        return format(value, "f")

    @implements("is_null")
    def is_null(self, value: Decimal | None) -> bool:
        return value is None

    @implements("is_not_null")
    def is_not_null(self, value: Decimal | None) -> bool:
        return value is not None

    @implements("eq")
    def eq(self, left: Decimal, right: Decimal) -> bool:
        return left == right

    @implements("ne")
    def ne(self, left: Decimal, right: Decimal) -> bool:
        return left != right

    @implements("lt")
    def lt(self, left: Decimal, right: Decimal) -> bool:
        return left < right

    @implements("lte")
    def lte(self, left: Decimal, right: Decimal) -> bool:
        return left <= right

    @implements("gt")
    def gt(self, left: Decimal, right: Decimal) -> bool:
        return left > right

    @implements("gte")
    def gte(self, left: Decimal, right: Decimal) -> bool:
        return left >= right

    @implements("is_in")
    def is_in(self, left: Decimal, values: Collection[Decimal]) -> bool:
        return left in values

    @implements("is_not_in")
    def is_not_in(self, left: Decimal, values: Collection[Decimal]) -> bool:
        return left not in values
