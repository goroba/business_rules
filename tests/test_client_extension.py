import pytest

from business_rules.condition import BinaryCondition
from business_rules.engine import Engine
from business_rules.evaluation import EvaluationContext
from business_rules.data_types import (
    DataType,
    DataTypeGuesserPool,
    DataTypesPool,
    IntegerDataType,
    data_type,
)
from business_rules.operand import Literal
from business_rules.operators import BinaryOperator, OperatorsPool, binary, implements


@binary("between")
class BetweenOperator(BinaryOperator):
    pass


@data_type("range_integer", guesser_after="integer")
class RangeIntegerDataType(DataType[int]):
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

    @implements("between")
    def between(self, value: int, high: int) -> bool:
        return 1 <= value <= high


def test_client_custom_operator_registered() -> None:
    assert OperatorsPool.get("between") is BetweenOperator
    assert BetweenOperator.name == "between"


def test_client_custom_data_type() -> None:
    range_integer = RangeIntegerDataType()
    assert DataTypesPool.get("range_integer") is RangeIntegerDataType
    assert RangeIntegerDataType.name == "range_integer"
    assert range_integer.operators == frozenset({"between"})
    assert range_integer.between(5, 10) is True
    assert range_integer.apply("between", 5, 10) is True
    assert range_integer.apply("between", 0, 10) is False
    assert range_integer.guess("50") is True
    assert range_integer.guess("200") is False


def test_client_custom_data_type_in_guesser_pool() -> None:
    ordered = DataTypeGuesserPool.ordered()
    integer_index = ordered.index(IntegerDataType)
    assert ordered[integer_index + 1] is RangeIntegerDataType
    assert DataTypeGuesserPool.guess("200") is IntegerDataType
    assert DataTypeGuesserPool.guess("50") is IntegerDataType


def test_client_custom_operator_in_condition() -> None:
    condition = BinaryCondition(
        left=Literal("5"),
        operator=BetweenOperator,
        right=Literal("10"),
    )
    assert condition.operator is BetweenOperator


def test_client_custom_operator_evaluate_two_literals() -> None:
    condition = BinaryCondition(
        left=Literal("5"),
        operator=BetweenOperator,
        right=Literal("10"),
    )
    ctx = EvaluationContext(Engine())
    assert condition.evaluate(ctx) is True


def test_client_custom_operator_evaluate_two_literals_no_common_type() -> None:
    condition = BinaryCondition(
        left=Literal("5"),
        operator=BetweenOperator,
        right=Literal("200"),
    )
    ctx = EvaluationContext(Engine())
    with pytest.raises(ValueError, match="No common data type"):
        condition.evaluate(ctx)


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

            def guess(self, value: str) -> bool:
                return True

            def __str__(self, value: str) -> str:  # type: ignore[override]
                return value
