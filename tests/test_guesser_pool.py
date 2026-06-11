from collections.abc import Iterator

import pytest

from business_rules.data_types import DataType, DataTypeGuesserPool, data_type
from business_rules.data_types.boolean import BooleanDataType
from business_rules.data_types.date import DateDataType
from business_rules.data_types.datetime_type import DateTimeDataType
from business_rules.data_types.decimal import DecimalDataType
from business_rules.data_types.integer import IntegerDataType
from business_rules.data_types.string import StringDataType

_DEFAULT_ORDER = (
    BooleanDataType,
    IntegerDataType,
    DateTimeDataType,
    DateDataType,
    DecimalDataType,
    StringDataType,
)


@pytest.fixture(autouse=True)
def restore_guesser_pool_order() -> Iterator[None]:
    saved = list(DataTypeGuesserPool._ordered)
    DataTypeGuesserPool._ordered[:] = list(_DEFAULT_ORDER)
    yield
    DataTypeGuesserPool._ordered[:] = saved


def test_default_guesser_pool_order() -> None:
    assert DataTypeGuesserPool.ordered() == _DEFAULT_ORDER


def test_guesser_pool_resolves_by_priority() -> None:
    assert DataTypeGuesserPool.guess("1") is BooleanDataType
    assert DataTypeGuesserPool.guess("42") is IntegerDataType
    assert DataTypeGuesserPool.guess("3.14") is DecimalDataType
    assert DataTypeGuesserPool.guess("2024-06-11") is DateTimeDataType
    assert DataTypeGuesserPool.guess("hello") is StringDataType


def test_guesser_pool_top() -> None:
    DataTypeGuesserPool.top(DecimalDataType)
    assert DataTypeGuesserPool.ordered()[0] is DecimalDataType
    assert DataTypeGuesserPool.guess("3.14") is DecimalDataType


def test_guesser_pool_bottom() -> None:
    DataTypeGuesserPool.bottom(BooleanDataType)
    ordered = DataTypeGuesserPool.ordered()
    assert ordered[-1] is BooleanDataType
    assert DataTypeGuesserPool.guess("true") is StringDataType


def test_guesser_pool_before() -> None:
    DataTypeGuesserPool.before(DateDataType, DateTimeDataType)
    ordered = DataTypeGuesserPool.ordered()
    datetime_index = ordered.index(DateTimeDataType)
    assert ordered[datetime_index - 1] is DateDataType
    assert DataTypeGuesserPool.guess("2024-06-11") is DateDataType


def test_guesser_pool_after() -> None:
    DataTypeGuesserPool.after(IntegerDataType, BooleanDataType)
    ordered = DataTypeGuesserPool.ordered()
    boolean_index = ordered.index(BooleanDataType)
    assert ordered[boolean_index + 1] is IntegerDataType


def test_guesser_pool_before_raises_when_reference_missing() -> None:
    @data_type("not_in_pool")
    class NotInPoolDataType(DataType[str]):
        def do_cast(self, value: str) -> str:
            return value

        def guess(self, value: str) -> bool:
            return True

        def __str__(self, value: str) -> str:  # type: ignore[override]
            return value

    with pytest.raises(ValueError, match="not registered in DataTypeGuesserPool"):
        DataTypeGuesserPool.before(NotInPoolDataType, StringDataType)


def test_guesser_pool_after_raises_when_reference_missing() -> None:
    @data_type("also_not_in_pool")
    class AlsoNotInPoolDataType(DataType[str]):
        def do_cast(self, value: str) -> str:
            return value

        def guess(self, value: str) -> bool:
            return True

        def __str__(self, value: str) -> str:  # type: ignore[override]
            return value

    with pytest.raises(ValueError, match="not registered in DataTypeGuesserPool"):
        DataTypeGuesserPool.after(AlsoNotInPoolDataType, StringDataType)


def test_guesser_pool_before_custom_type_takes_priority() -> None:
    @data_type("narrow_integer", guesser_before="integer")
    class NarrowIntegerDataType(DataType[int]):
        def do_cast(self, value: str) -> int:
            return int(value)

        def guess(self, value: str) -> bool:
            try:
                parsed = int(value)
            except ValueError:
                return False
            return 0 <= parsed <= 10

        def __str__(self, value: int) -> str:  # type: ignore[override]
            return str(value)

    assert DataTypeGuesserPool.guess("5") is NarrowIntegerDataType
    assert DataTypeGuesserPool.guess("42") is IntegerDataType


def test_guesser_pool_guess_pair_string() -> None:
    assert (
        DataTypeGuesserPool.guess_pair("true", "some text", operator="eq")
        is StringDataType
    )


def test_guesser_pool_guess_pair_decimal() -> None:
    assert (
        DataTypeGuesserPool.guess_pair("1", "1.5", operator="gt") is DecimalDataType
    )


def test_guesser_pool_guess_pair_boolean() -> None:
    assert (
        DataTypeGuesserPool.guess_pair("true", "false", operator="eq")
        is BooleanDataType
    )


def test_guesser_pool_guess_pair_raises_when_no_common_type() -> None:
    from business_rules.operators import BinaryOperator, binary, implements

    @binary("pair_test_between")
    class PairTestBetweenOperator(BinaryOperator):
        pass

    @data_type("pair_test_range_integer", guesser_after="integer")
    class PairTestRangeIntegerDataType(DataType[int]):
        def do_cast(self, value: str) -> int:
            return int(value)

        def guess(self, value: str) -> bool:
            try:
                parsed = int(value)
            except ValueError:
                return False
            return 0 <= parsed <= 100

        def __str__(self, value: int) -> str:  # type: ignore[override]
            return str(value)

        @implements("pair_test_between")
        def pair_test_between(self, value: int, high: int) -> bool:
            return 1 <= value <= high

    with pytest.raises(ValueError, match="No common data type"):
        DataTypeGuesserPool.guess_pair(
            "5", "200", operator=PairTestBetweenOperator.name
        )


def test_guesser_pool_guess_pair_custom_operator() -> None:
    from business_rules.operators import BinaryOperator, binary, implements

    @binary("pair_test_between_match")
    class PairTestBetweenMatchOperator(BinaryOperator):
        pass

    @data_type("pair_test_range_integer_match", guesser_after="integer")
    class PairTestRangeIntegerMatchDataType(DataType[int]):
        def do_cast(self, value: str) -> int:
            return int(value)

        def guess(self, value: str) -> bool:
            try:
                parsed = int(value)
            except ValueError:
                return False
            return 0 <= parsed <= 100

        def __str__(self, value: int) -> str:  # type: ignore[override]
            return str(value)

        @implements("pair_test_between_match")
        def pair_test_between_match(self, value: int, high: int) -> bool:
            return 1 <= value <= high

    assert (
        DataTypeGuesserPool.guess_pair(
            "5", "10", operator=PairTestBetweenMatchOperator.name
        )
        is PairTestRangeIntegerMatchDataType
    )
