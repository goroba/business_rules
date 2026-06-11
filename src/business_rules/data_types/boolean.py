"""Boolean data type."""

from __future__ import annotations

from business_rules.data_types.base import DataType
from business_rules.data_types.pool import data_type
from business_rules.operators import implements

__all__ = ["BooleanDataType"]

_TRUTHY = frozenset({"true", "1", "yes"})
_FALSY = frozenset({"false", "0", "no"})


@data_type("boolean")
class BooleanDataType(DataType[bool]):
    def do_cast(self, value: str) -> bool:
        normalized = value.strip().lower()
        if normalized in _TRUTHY:
            return True
        if normalized in _FALSY:
            return False
        raise ValueError(f"Invalid boolean value: {value!r}")

    def guess(self, value: str) -> bool:
        normalized = value.strip().lower()
        return normalized in ['true', 'false']

    def __str__(self, value: bool) -> str:  # type: ignore[override]
        return "true" if value else "false"

    @implements("is_null")
    def is_null(self, value: bool | None) -> bool:
        return value is None

    @implements("is_not_null")
    def is_not_null(self, value: bool | None) -> bool:
        return value is not None

    @implements("eq")
    def eq(self, left: bool, right: bool) -> bool:
        return left == right

    @implements("ne")
    def ne(self, left: bool, right: bool) -> bool:
        return left != right
