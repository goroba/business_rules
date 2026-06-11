from dataclasses import dataclass

import pytest

from business_rules.condition import (
    BinaryCondition,
    Condition,
    Conjunction,
    Disjunction,
    IterableCondition,
    UnaryCondition,
)
from business_rules.operand import Value, Variable
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
    verifiable = Variable("field")
    condition = UnaryCondition(verifiable=verifiable, operator=IsNullOperator)
    assert condition.verifiable == verifiable
    assert condition.operator is IsNullOperator


def test_binary_condition() -> None:
    left = Variable("age")
    right = Value("18")
    condition = BinaryCondition(left=left, operator=GtOperator, right=right)
    assert condition.left == left
    assert condition.operator is GtOperator
    assert condition.right == right


def test_iterable_condition() -> None:
    with pytest.raises(NotImplementedError):
        iter(IterableCondition())


def test_conjunction() -> None:
    first = BinaryCondition(
        left=Variable("a"),
        operator=EqOperator,
        right=Value("1"),
    )
    second = BinaryCondition(
        left=Variable("b"),
        operator=EqOperator,
        right=Value("2"),
    )
    condition = Conjunction(all=(first, second))
    assert condition.all == (first, second)
    assert list(condition) == [first, second]


def test_disjunction() -> None:
    first = BinaryCondition(
        left=Variable("a"),
        operator=EqOperator,
        right=Value("1"),
    )
    second = BinaryCondition(
        left=Variable("b"),
        operator=EqOperator,
        right=Value("2"),
    )
    condition = Disjunction(any=(first, second))
    assert condition.any == (first, second)
    assert list(condition) == [first, second]


def test_not_operator_condition() -> None:
    inner = BinaryCondition(
        left=Variable("age"),
        operator=GtOperator,
        right=Value("18"),
    )
    condition = UnaryCondition(verifiable=inner, operator=NotOperator)
    assert condition.verifiable == inner
    assert condition.operator is NotOperator
    assert condition.operator.name == "not"


def test_condition_verify_raises() -> None:
    with pytest.raises(NotImplementedError):
        Condition().verify()


def test_unary_condition_verify_raises() -> None:
    with pytest.raises(NotImplementedError):
        UnaryCondition(
            verifiable=Variable("field"),
            operator=IsNullOperator,
        ).verify()


def test_binary_condition_verify_is_stub() -> None:
    condition = BinaryCondition(
        left=Variable("age"),
        operator=GtOperator,
        right=Value("18"),
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


def test_not_operator_condition_verify_raises() -> None:
    with pytest.raises(NotImplementedError):
        UnaryCondition(
            verifiable=TrueCondition(),
            operator=NotOperator,
        ).verify()
