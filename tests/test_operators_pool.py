import pytest

from business_rules.operators import (
    BinaryOperator,
    EqOperator,
    OperatorsPool,
    UnaryOperator,
    binary,
    unary,
)


def test_operators_pool_all() -> None:
    assert EqOperator in OperatorsPool.all()


def test_operators_pool_unary_and_binary() -> None:
    unary_ops = OperatorsPool.unary()
    binary_ops = OperatorsPool.binary()
    assert all(issubclass(op, UnaryOperator) for op in unary_ops)
    assert all(issubclass(op, BinaryOperator) for op in binary_ops)
    assert EqOperator in binary_ops


class _UnaryAsBinary(UnaryOperator):
    pass


class _BinaryAsUnary(BinaryOperator):
    pass


def test_binary_rejects_wrong_base() -> None:
    with pytest.raises(TypeError, match="BinaryOperator"):
        binary("bad_binary")(_UnaryAsBinary)  # type: ignore[type-var]


def test_unary_rejects_wrong_base() -> None:
    with pytest.raises(TypeError, match="UnaryOperator"):
        unary("bad_unary")(_BinaryAsUnary)  # type: ignore[type-var]


def test_register_rejects_empty_name() -> None:
    with pytest.raises(ValueError, match="empty"):

        @binary("")
        class EmptyNameOperator(BinaryOperator):
            pass


def test_register_rejects_duplicate_name() -> None:
    with pytest.raises(ValueError, match="already registered"):

        @binary("eq")
        class DuplicateEqOperator(BinaryOperator):
            pass
