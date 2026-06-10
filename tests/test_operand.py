from business_rules.operand import Operand


def test_operand() -> None:
    operand = Operand("field_name")
    assert operand.value == "field_name"
