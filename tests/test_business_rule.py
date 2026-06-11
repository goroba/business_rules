from dataclasses import dataclass

from business_rules.executable import Action
from business_rules.business_rule import BusinessRule
from business_rules.condition import BinaryCondition, Condition
from business_rules.operand import Value, Variable
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
        left=Variable("status"),
        operator=EqOperator,
        right=Value("active"),
    )
    rule = BusinessRule(condition=condition)
    assert rule.condition == condition
    assert rule.on_success is None
    assert rule.on_failure is None
    assert rule.on_finally is None


def test_business_rule_with_all_fields() -> None:
    condition = BinaryCondition(
        left=Variable("age"),
        operator=GtOperator,
        right=Value("18"),
    )
    on_success = [Action(name="on_success")]
    on_failure = [Action(name="on_failure")]
    on_finally = [Action(name="on_finally")]
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
