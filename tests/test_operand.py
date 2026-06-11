import pytest

from business_rules.operand import Value, Variable


def test_variable() -> None:
    operand = Variable("field_name")
    assert operand.name == "field_name"


def test_value() -> None:
    operand = Value("42")
    assert operand.value == "42"


def test_operand_verify_raises() -> None:
    with pytest.raises(NotImplementedError):
        Variable("field_name").verify()

    with pytest.raises(NotImplementedError):
        Value("42").verify()
