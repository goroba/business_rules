"""Ordered registry for data type guessers."""

from __future__ import annotations

from typing import Any, ClassVar

from business_rules.data_types.base import DataType
from business_rules.data_types.boolean import BooleanDataType
from business_rules.data_types.date import DateDataType
from business_rules.data_types.datetime_type import DateTimeDataType
from business_rules.data_types.decimal import DecimalDataType
from business_rules.data_types.integer import IntegerDataType
from business_rules.data_types.string import StringDataType

__all__ = ["DataTypeGuesserPool"]

_DataTypeCls = type[DataType[Any]]


class DataTypeGuesserPool:
    _ordered: ClassVar[list[_DataTypeCls]] = [
        BooleanDataType,
        IntegerDataType,
        DateTimeDataType,
        DateDataType,
        DecimalDataType,
        StringDataType,
    ]

    @classmethod
    def ordered(cls) -> tuple[_DataTypeCls, ...]:
        return tuple(cls._ordered)

    @classmethod
    def top(cls, guesser: _DataTypeCls) -> None:
        if guesser in cls._ordered:
            cls._ordered.remove(guesser)
        cls._ordered.insert(0, guesser)

    @classmethod
    def bottom(cls, guesser: _DataTypeCls) -> None:
        if guesser in cls._ordered:
            cls._ordered.remove(guesser)
        cls._ordered.append(guesser)

    @classmethod
    def before(cls, guesser: _DataTypeCls, reference: _DataTypeCls) -> None:
        try:
            index = cls._ordered.index(reference)
        except ValueError as exc:
            raise ValueError(
                f"{reference.__name__} is not registered in DataTypeGuesserPool"
            ) from exc
        if guesser in cls._ordered:
            cls._ordered.remove(guesser)
            index = cls._ordered.index(reference)
        cls._ordered.insert(index, guesser)

    @classmethod
    def after(cls, guesser: _DataTypeCls, reference: _DataTypeCls) -> None:
        try:
            index = cls._ordered.index(reference)
        except ValueError as exc:
            raise ValueError(
                f"{reference.__name__} is not registered in DataTypeGuesserPool"
            ) from exc
        if guesser in cls._ordered:
            cls._ordered.remove(guesser)
            index = cls._ordered.index(reference)
        cls._ordered.insert(index + 1, guesser)

    @classmethod
    def guess(cls, value: str) -> _DataTypeCls:
        for data_type_cls in cls._ordered:
            if data_type_cls().guess(value):
                return data_type_cls
        raise RuntimeError("No data type guesser matched the value")

    @classmethod
    def guess_pair(cls, left: str, right: str, *, operator: str) -> _DataTypeCls:
        for data_type_cls in cls._ordered:
            if operator not in data_type_cls.operators:
                continue
            instance = data_type_cls()
            if instance.guess(left) and instance.guess(right):
                return data_type_cls
        raise ValueError(
            f"No common data type for {left!r} and {right!r} "
            f"supports operator {operator!r}"
        )
