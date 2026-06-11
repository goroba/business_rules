"""String data type."""

from __future__ import annotations

import re
from collections.abc import Collection

from business_rules.data_types.base import DataType
from business_rules.data_types.pool import data_type
from business_rules.operators import implements

__all__ = ["StringDataType"]


@data_type("string")
class StringDataType(DataType[str]):
    def do_cast(self, value: str) -> str:
        return value

    def __str__(self, value: str) -> str:  # type: ignore[override]
        return value

    @implements("is_null")
    def is_null(self, value: str | None) -> bool:
        return value is None

    @implements("is_not_null")
    def is_not_null(self, value: str | None) -> bool:
        return value is not None

    @implements("eq")
    def eq(self, left: str, right: str) -> bool:
        return left == right

    @implements("ne")
    def ne(self, left: str, right: str) -> bool:
        return left != right

    @implements("lt")
    def lt(self, left: str, right: str) -> bool:
        return left < right

    @implements("lte")
    def lte(self, left: str, right: str) -> bool:
        return left <= right

    @implements("gt")
    def gt(self, left: str, right: str) -> bool:
        return left > right

    @implements("gte")
    def gte(self, left: str, right: str) -> bool:
        return left >= right

    @implements("contains")
    def contains(self, left: str, right: str) -> bool:
        return right in left

    @implements("not_contains")
    def not_contains(self, left: str, right: str) -> bool:
        return right not in left

    @implements("starts_with")
    def starts_with(self, left: str, right: str) -> bool:
        return left.startswith(right)

    @implements("ends_with")
    def ends_with(self, left: str, right: str) -> bool:
        return left.endswith(right)

    @implements("matches")
    def matches(self, left: str, pattern: str) -> bool:
        return re.fullmatch(pattern, left) is not None

    @implements("is_in")
    def is_in(self, left: str, values: Collection[str]) -> bool:
        return left in values

    @implements("is_not_in")
    def is_not_in(self, left: str, values: Collection[str]) -> bool:
        return left not in values
