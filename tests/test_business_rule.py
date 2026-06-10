from dataclasses import dataclass

from business_rules.action import Action
from business_rules.business_rule import BusinessRule
from business_rules.condition import BinaryCondition, Condition
from business_rules.operand import Operand
from business_rules.operators import EqOperator, GtOperator


@dataclass
class TrueCondition(Condition):
    def verify(self) -> bool:
        return True


@dataclass
class FalseCondition(Condition):
    def verify(self) -> bool:
        return False


def test_business_rule_with_condition_only() -> None:
    condition = BinaryCondition(
        left=Operand("status"),
        operator=EqOperator,
        right=Operand("active"),
    )
    rule = BusinessRule(condition=condition)
    assert rule.condition == condition
    assert rule.on_success is None
    assert rule.on_failure is None
    assert rule.on_finally is None


def test_business_rule_with_all_fields() -> None:
    condition = BinaryCondition(
        left=Operand("age"),
        operator=GtOperator,
        right=Operand(18),
    )
    on_success = [Action()]
    on_failure = [Action()]
    on_finally = [Action()]
    rule = BusinessRule(
        condition=condition,
        on_success=on_success,
        on_failure=on_failure,
        on_finally=on_finally,
    )
    assert rule.condition == condition
    assert rule.on_success == on_success
    assert rule.on_failure == on_failure
    assert rule.on_finally == on_finally


def test_business_rule_bool_returns_true_when_condition_verifies() -> None:
    rule = BusinessRule(condition=TrueCondition())
    assert bool(rule) is True


def test_business_rule_bool_returns_false_when_condition_fails() -> None:
    rule = BusinessRule(condition=FalseCondition())
    assert bool(rule) is False
