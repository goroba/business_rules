from datetime import date, datetime
from decimal import Decimal

import pytest

from business_rules.data_types.boolean import BooleanDataType
from business_rules.data_types.date import DateDataType
from business_rules.data_types.datetime_type import DateTimeDataType
from business_rules.data_types.decimal import DecimalDataType
from business_rules.data_types.integer import IntegerDataType
from business_rules.data_types.string import StringDataType

_ORDERED_OPERATORS = frozenset(
    {
        "eq",
        "ne",
        "lt",
        "lte",
        "gt",
        "gte",
        "is_in",
        "is_not_in",
        "is_null",
        "is_not_null",
    }
)


def test_boolean_data_type() -> None:
    data_type = BooleanDataType()
    assert data_type.operators == frozenset(
        {"eq", "ne", "is_null", "is_not_null"}
    )
    assert data_type.cast("true") is True
    assert data_type.cast("FALSE") is False
    assert data_type.cast("1") is True
    assert data_type.cast("0") is False
    assert data_type.__str__(True) == "true"
    assert data_type.__bool__(True) is True
    assert data_type.__bool__(False) is False
    assert data_type.is_null(None) is True
    assert data_type.is_null(False) is False
    assert data_type.is_not_null(False) is True
    assert data_type.is_not_null(None) is False
    assert data_type.eq(True, True) is True
    assert data_type.eq(True, False) is False
    assert data_type.ne(True, False) is True
    assert data_type.ne(False, False) is False
    with pytest.raises(ValueError, match="Invalid boolean"):
        data_type.cast("maybe")
    with pytest.raises(NotImplementedError):
        data_type.apply("contains", "a", "b")
    assert data_type.apply("eq", True, True) is True


def test_string_data_type() -> None:
    data_type = StringDataType()
    assert data_type.operators == _ORDERED_OPERATORS | frozenset(
        {
            "contains",
            "not_contains",
            "starts_with",
            "ends_with",
            "matches",
        }
    )
    assert data_type.cast("hello") == "hello"
    assert data_type.__str__("hello") == "hello"
    assert data_type.__bool__("hello") is True
    assert data_type.__bool__("") is False
    assert data_type.is_null(None) is True
    assert data_type.is_not_null("x") is True
    assert data_type.eq("a", "a") is True
    assert data_type.eq("a", "b") is False
    assert data_type.ne("a", "b") is True
    assert data_type.ne("a", "a") is False
    assert data_type.lt("a", "b") is True
    assert data_type.lt("b", "a") is False
    assert data_type.lte("a", "a") is True
    assert data_type.lte("b", "a") is False
    assert data_type.gt("b", "a") is True
    assert data_type.gt("a", "b") is False
    assert data_type.gte("a", "a") is True
    assert data_type.gte("a", "b") is False
    assert data_type.contains("hello", "ell") is True
    assert data_type.contains("hello", "xyz") is False
    assert data_type.not_contains("hello", "xyz") is True
    assert data_type.not_contains("hello", "ell") is False
    assert data_type.starts_with("hello", "he") is True
    assert data_type.starts_with("hello", "lo") is False
    assert data_type.ends_with("hello", "lo") is True
    assert data_type.ends_with("hello", "he") is False
    assert data_type.matches("abc123", r"abc\d+") is True
    assert data_type.matches("abc", r"\d+") is False
    assert data_type.is_in("a", ("a", "b")) is True
    assert data_type.is_in("c", ("a", "b")) is False
    assert data_type.is_not_in("c", ("a", "b")) is True
    assert data_type.is_not_in("a", ("a", "b")) is False


def test_integer_data_type() -> None:
    data_type = IntegerDataType()
    assert data_type.operators == _ORDERED_OPERATORS
    assert data_type.cast("42") == 42
    assert data_type.__str__(42) == "42"
    assert data_type.__bool__(42) is True
    assert data_type.__bool__(0) is False
    assert data_type.is_null(None) is True
    assert data_type.is_not_null(1) is True
    assert data_type.eq(1, 1) is True
    assert data_type.eq(1, 2) is False
    assert data_type.ne(1, 2) is True
    assert data_type.ne(2, 2) is False
    assert data_type.lt(1, 2) is True
    assert data_type.lt(2, 1) is False
    assert data_type.lte(1, 1) is True
    assert data_type.lte(2, 1) is False
    assert data_type.gt(2, 1) is True
    assert data_type.gt(1, 2) is False
    assert data_type.gte(2, 2) is True
    assert data_type.gte(1, 2) is False
    assert data_type.is_in(2, (1, 2, 3)) is True
    assert data_type.is_in(4, (1, 2, 3)) is False
    assert data_type.is_not_in(4, (1, 2, 3)) is True
    assert data_type.is_not_in(2, (1, 2, 3)) is False
    with pytest.raises(NotImplementedError):
        data_type.apply("contains", 1, 2)
    assert data_type.apply("eq", 1, 1) is True


def test_decimal_data_type() -> None:
    data_type = DecimalDataType()
    assert data_type.operators == _ORDERED_OPERATORS
    assert data_type.cast("1.5") == Decimal("1.5")
    assert data_type.__str__(Decimal("1.5")) == "1.5"
    assert data_type.__bool__(Decimal("1.5")) is True
    assert data_type.__bool__(Decimal("0")) is False
    assert data_type.is_null(None) is True
    assert data_type.is_not_null(Decimal("1")) is True
    assert data_type.eq(Decimal("1.0"), Decimal("1.0")) is True
    assert data_type.eq(Decimal("1.0"), Decimal("2.0")) is False
    assert data_type.ne(Decimal("1.0"), Decimal("2.0")) is True
    assert data_type.ne(Decimal("1.0"), Decimal("1.0")) is False
    assert data_type.lt(Decimal("1"), Decimal("2")) is True
    assert data_type.lt(Decimal("2"), Decimal("1")) is False
    assert data_type.lte(Decimal("1"), Decimal("1")) is True
    assert data_type.lte(Decimal("2"), Decimal("1")) is False
    assert data_type.gt(Decimal("2"), Decimal("1")) is True
    assert data_type.gt(Decimal("1"), Decimal("2")) is False
    assert data_type.gte(Decimal("2"), Decimal("2")) is True
    assert data_type.gte(Decimal("1"), Decimal("2")) is False
    assert data_type.is_in(Decimal("2"), (Decimal("1"), Decimal("2"))) is True
    assert data_type.is_in(Decimal("3"), (Decimal("1"), Decimal("2"))) is False
    assert data_type.is_not_in(Decimal("3"), (Decimal("1"), Decimal("2"))) is True
    assert data_type.is_not_in(Decimal("2"), (Decimal("1"), Decimal("2"))) is False


def test_date_data_type() -> None:
    data_type = DateDataType()
    assert data_type.operators == _ORDERED_OPERATORS
    value = date(2024, 1, 15)
    other = date(2024, 2, 1)
    assert data_type.cast("2024-01-15") == value
    assert data_type.__str__(value) == "2024-01-15"
    assert data_type.__bool__(value) is True
    assert data_type.is_null(None) is True
    assert data_type.is_not_null(value) is True
    assert data_type.eq(value, value) is True
    assert data_type.eq(value, other) is False
    assert data_type.ne(value, other) is True
    assert data_type.ne(value, value) is False
    assert data_type.lt(value, other) is True
    assert data_type.lt(other, value) is False
    assert data_type.lte(value, value) is True
    assert data_type.lte(other, value) is False
    assert data_type.gt(other, value) is True
    assert data_type.gt(value, other) is False
    assert data_type.gte(other, other) is True
    assert data_type.gte(value, other) is False
    assert data_type.is_in(value, (value, other)) is True
    assert data_type.is_in(date(2023, 1, 1), (value, other)) is False
    assert data_type.is_not_in(date(2023, 1, 1), (value, other)) is True
    assert data_type.is_not_in(value, (value, other)) is False


def test_datetime_data_type() -> None:
    data_type = DateTimeDataType()
    assert data_type.operators == _ORDERED_OPERATORS
    value = datetime(2024, 1, 15, 10, 30, 0)
    other = datetime(2024, 1, 15, 12, 0, 0)
    assert data_type.cast("2024-01-15T10:30:00") == value
    assert data_type.__str__(value) == "2024-01-15T10:30:00"
    assert data_type.__bool__(value) is True
    assert data_type.is_null(None) is True
    assert data_type.is_not_null(value) is True
    assert data_type.eq(value, value) is True
    assert data_type.eq(value, other) is False
    assert data_type.ne(value, other) is True
    assert data_type.ne(value, value) is False
    assert data_type.lt(value, other) is True
    assert data_type.lt(other, value) is False
    assert data_type.lte(value, value) is True
    assert data_type.lte(other, value) is False
    assert data_type.gt(other, value) is True
    assert data_type.gt(value, other) is False
    assert data_type.gte(other, other) is True
    assert data_type.gte(value, other) is False
    assert data_type.is_in(value, (value, other)) is True
    assert data_type.is_in(datetime(2023, 1, 1), (value, other)) is False
    assert data_type.is_not_in(datetime(2023, 1, 1), (value, other)) is True
    assert data_type.is_not_in(value, (value, other)) is False
