import pytest

from business_rules.condition import BinaryCondition
from business_rules.data_types import DataType, DataTypesPool, data_type
from business_rules.operand import Literal
from business_rules.operators import BinaryOperator, OperatorsPool, binary, implements


@binary("between")
class BetweenOperator(BinaryOperator):
    pass


@data_type("range_integer")
class RangeIntegerDataType(DataType[int]):
    def do_cast(self, value: str) -> int:
        return int(value)

    def __str__(self, value: int) -> str:  # type: ignore[override]
        return str(value)

    @implements("between")
    def between(self, left: int, low: int, high: int) -> bool:
        return low <= left <= high


def test_client_custom_operator_registered() -> None:
    assert OperatorsPool.get("between") is BetweenOperator
    assert BetweenOperator.name == "between"


def test_client_custom_data_type() -> None:
    range_integer = RangeIntegerDataType()
    assert DataTypesPool.get("range_integer") is RangeIntegerDataType
    assert RangeIntegerDataType.name == "range_integer"
    assert range_integer.operators == frozenset({"between"})
    assert range_integer.between(5, 1, 10) is True
    assert range_integer.apply("between", 5, 1, 10) is True
    assert range_integer.apply("between", 0, 1, 10) is False


def test_client_custom_operator_in_condition() -> None:
    condition = BinaryCondition(
        left=Literal("5"),
        operator=BetweenOperator,
        right=Literal("10"),
    )
    assert condition.operator is BetweenOperator


def test_client_cannot_override_builtin_operator() -> None:
    with pytest.raises(ValueError, match="already registered"):

        @binary("eq")
        class ClientEqOperator(BinaryOperator):
            pass


def test_client_cannot_override_builtin_data_type() -> None:
    with pytest.raises(ValueError, match="already registered"):

        @data_type("string")
        class ClientStringDataType(DataType[str]):
            def do_cast(self, value: str) -> str:
                return value

            def __str__(self, value: str) -> str:  # type: ignore[override]
                return value
