from dataclasses import dataclass

import pytest

from business_rules.condition import (
    BinaryCondition,
    Condition,
    Conjunction,
    Disjunction,
    IterableCondition,
    Negation,
    UnaryCondition,
)
from business_rules.operand import Operand
from business_rules.operators import EqOperator, GtOperator, IsNullOperator, NotOperator


@dataclass
class TrueCondition(Condition):
    def verify(self) -> bool:
        return True


@dataclass
class FalseCondition(Condition):
    def verify(self) -> bool:
        return False


def test_condition() -> None:
    assert Condition() == Condition()


def test_unary_condition() -> None:
    operand = Operand("field")
    condition = UnaryCondition(operand=operand, operator=IsNullOperator)
    assert condition.operand == operand
    assert condition.operator is IsNullOperator


def test_binary_condition() -> None:
    left = Operand("age")
    right = Operand(18)
    condition = BinaryCondition(left=left, operator=GtOperator, right=right)
    assert condition.left == left
    assert condition.operator is GtOperator
    assert condition.right == right


def test_iterable_condition() -> None:
    with pytest.raises(NotImplementedError):
        iter(IterableCondition())


def test_conjunction() -> None:
    first = BinaryCondition(
        left=Operand("a"),
        operator=EqOperator,
        right=Operand(1),
    )
    second = BinaryCondition(
        left=Operand("b"),
        operator=EqOperator,
        right=Operand(2),
    )
    condition = Conjunction(all=(first, second))
    assert condition.all == (first, second)
    assert list(condition) == [first, second]


def test_disjunction() -> None:
    first = BinaryCondition(
        left=Operand("a"),
        operator=EqOperator,
        right=Operand(1),
    )
    second = BinaryCondition(
        left=Operand("b"),
        operator=EqOperator,
        right=Operand(2),
    )
    condition = Disjunction(any=(first, second))
    assert condition.any == (first, second)
    assert list(condition) == [first, second]


def test_negation() -> None:
    inner = BinaryCondition(
        left=Operand("age"),
        operator=GtOperator,
        right=Operand(18),
    )
    condition = Negation(operand=Operand(inner), operator=NotOperator)
    assert condition.operand.value == inner
    assert condition.operator is NotOperator
    assert condition.operator.name == "not"


def test_condition_verify_raises() -> None:
    with pytest.raises(NotImplementedError):
        Condition().verify()


def test_unary_condition_verify_raises() -> None:
    with pytest.raises(NotImplementedError):
        UnaryCondition(
            operand=Operand("field"),
            operator=IsNullOperator,
        ).verify()


def test_binary_condition_verify_is_stub() -> None:
    condition = BinaryCondition(
        left=Operand("age"),
        operator=GtOperator,
        right=Operand(18),
    )
    condition.verify()


def test_iterable_condition_verify_raises() -> None:
    with pytest.raises(NotImplementedError):
        IterableCondition().verify()


def test_conjunction_verify() -> None:
    assert Conjunction(all=(TrueCondition(), TrueCondition())).verify() is True
    assert Conjunction(all=(TrueCondition(), FalseCondition())).verify() is False


def test_disjunction_verify() -> None:
    assert Disjunction(any=(FalseCondition(), TrueCondition())).verify() is True
    assert Disjunction(any=(FalseCondition(), FalseCondition())).verify() is False


def test_negation_verify() -> None:
    condition = Negation(
        operand=Operand(TrueCondition()),
        operator=NotOperator,
    )
    assert condition.verify() is False
