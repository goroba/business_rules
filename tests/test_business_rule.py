from dataclasses import dataclass

import pytest

from business_rules.executable import Action
from business_rules.business_rule import BusinessRule
from business_rules.condition import BinaryCondition, Condition
from business_rules.engine import Engine
from business_rules.evaluation import EvaluationContext
from business_rules.operand import Literal, Variable
from business_rules.operators import EqOperator, GtOperator


@dataclass
class TrueCondition(Condition):
    def evaluate(self, ctx: EvaluationContext) -> bool:
        return True


@dataclass
class FalseCondition(Condition):
    def evaluate(self, ctx: EvaluationContext) -> bool:
        return False


@pytest.fixture
def engine() -> Engine:
    return Engine()


@pytest.fixture
def ctx(engine: Engine) -> EvaluationContext:
    return EvaluationContext(engine)


def test_business_rule_with_having_only() -> None:
    condition = BinaryCondition(
        left=Variable("status"),
        operator=EqOperator,
        right=Literal("active"),
    )
    rule = BusinessRule(having=condition)
    assert rule.having == condition
    assert rule.on_success is None
    assert rule.on_failure is None
    assert rule.on_finally is None


def test_business_rule_with_all_fields() -> None:
    condition = BinaryCondition(
        left=Variable("age"),
        operator=GtOperator,
        right=Literal("18"),
    )
    on_success = [Action(name="on_success")]
    on_failure = [Action(name="on_failure")]
    on_finally = [Action(name="on_finally")]
    rule = BusinessRule(
        having=condition,
        on_success=on_success,
        on_failure=on_failure,
        on_finally=on_finally,
    )
    assert rule.having == condition
    assert rule.on_success == on_success
    assert rule.on_failure == on_failure
    assert rule.on_finally == on_finally


def test_business_rule_evaluate_returns_true_when_condition_passes(
    ctx: EvaluationContext,
) -> None:
    rule = BusinessRule(having=TrueCondition())
    assert rule.evaluate(ctx) is True


def test_business_rule_evaluate_returns_false_when_condition_fails(
    ctx: EvaluationContext,
) -> None:
    rule = BusinessRule(having=FalseCondition())
    assert rule.evaluate(ctx) is False
