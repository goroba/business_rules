import pytest

from business_rules.operators import EqOperator, OperatorsPool


def test_operators_pool_get() -> None:
    assert OperatorsPool.get("eq") is EqOperator
    assert EqOperator.name == "eq"


def test_operators_pool_get_unknown() -> None:
    with pytest.raises(KeyError, match="unknown"):
        OperatorsPool.get("unknown")
