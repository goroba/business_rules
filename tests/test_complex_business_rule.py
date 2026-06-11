"""Integration tests for complex nested business rules."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

import pytest

from business_rules.business_rule import BusinessRule
from business_rules.condition import (
    BinaryCondition,
    Conjunction,
    Disjunction,
    NegatedCondition,
    UnaryCondition,
)
from business_rules.context import Context
from business_rules.engine import Engine
from business_rules.evaluation import EvaluationContext
from business_rules.executable import Action
from business_rules.operand import Function, Literal, Variable
from business_rules.operators import (
    ContainsOperator,
    EqOperator,
    GteOperator,
    IsInOperator,
    IsNotNullOperator,
    LtOperator,
)


@dataclass
class EligibilityState:
    age: int = 25
    min_age: int = 25
    status: str = "active"
    tier: str = "premium"
    email: str = "user@example.com"
    balance: Decimal = Decimal("150.00")
    is_suspended: bool = False
    registration_date: date = date(2023, 1, 1)
    last_login: datetime = datetime(2024, 6, 1, 12, 0, 0)
    user_id: int = 99
    region: str = "US"
    lookup_value: int | None = 42


def _eligibility_condition() -> Conjunction:
    return Conjunction(
        all=(
            Conjunction(
                all=(
                    BinaryCondition(
                        left=Variable("age"),
                        operator=GteOperator,
                        right=Literal("18"),
                    ),
                    BinaryCondition(
                        left=Variable("status"),
                        operator=EqOperator,
                        right=Literal("active"),
                    ),
                    UnaryCondition(
                        operand=Variable("email"),
                        operator=IsNotNullOperator,
                    ),
                    BinaryCondition(
                        left=Variable("email"),
                        operator=ContainsOperator,
                        right=Literal("@"),
                    ),
                    UnaryCondition(
                        operand=Function(name="lookup"),
                        operator=IsNotNullOperator,
                    ),
                )
            ),
            Disjunction(
                any=(
                    Conjunction(
                        all=(
                            BinaryCondition(
                                left=Variable("tier"),
                                operator=EqOperator,
                                right=Literal("premium"),
                            ),
                            BinaryCondition(
                                left=Variable("balance"),
                                operator=GteOperator,
                                right=Literal("100.00"),
                            ),
                        )
                    ),
                    Conjunction(
                        all=(
                            BinaryCondition(
                                left=Variable("registration_date"),
                                operator=LtOperator,
                                right=Literal("2024-06-01"),
                            ),
                            NegatedCondition(
                                negative=BinaryCondition(
                                    left=Variable("is_suspended"),
                                    operator=EqOperator,
                                    right=Literal("true"),
                                )
                            ),
                            BinaryCondition(
                                left=Variable("last_login"),
                                operator=GteOperator,
                                right=Function(name="login_cutoff"),
                            ),
                            BinaryCondition(
                                left=Variable("age"),
                                operator=EqOperator,
                                right=Variable("min_age"),
                            ),
                        )
                    ),
                )
            ),
            NegatedCondition(
                negative=BinaryCondition(
                    left=Variable("user_id"),
                    operator=IsInOperator,
                    right=Function(name="blocklist"),
                )
            ),
            BinaryCondition(
                left=Variable("region"),
                operator=IsInOperator,
                right=Function(name="allowed_regions", args=("premium",)),
            ),
        )
    )


def _run_lifecycle(
    rule: BusinessRule,
    ctx: EvaluationContext,
    calls: list[str],
) -> bool:
    calls.clear()
    result = rule.evaluate(ctx)
    if result:
        for action in rule.on_success or []:
            action.execute(ctx)
    else:
        for action in rule.on_failure or []:
            action.execute(ctx)
    for action in rule.on_finally or []:
        action.execute(ctx)
    return result


def _build_rule() -> BusinessRule:
    return BusinessRule(
        having=_eligibility_condition(),
        on_success=[Action(name="grant_access")],
        on_failure=[Action(name="reject_access")],
        on_finally=[Action(name="audit_log")],
    )


def _register_eligibility(
    engine: Engine,
    state: EligibilityState,
    calls: list[str],
) -> None:
    @engine.variable("age", data_type="integer")
    def age() -> int:
        return state.age

    @engine.variable("min_age", data_type="integer")
    def min_age() -> int:
        return state.min_age

    @engine.variable("status", data_type="string")
    def status() -> str:
        return state.status

    @engine.variable("tier", data_type="string")
    def tier() -> str:
        return state.tier

    @engine.variable("email", data_type="string")
    def email() -> str:
        return state.email

    @engine.variable("balance", data_type="decimal")
    def balance() -> Decimal:
        return state.balance

    @engine.variable("is_suspended", data_type="boolean")
    def is_suspended() -> bool:
        return state.is_suspended

    @engine.variable("registration_date", data_type="date")
    def registration_date() -> date:
        return state.registration_date

    @engine.variable("last_login", data_type="datetime")
    def last_login() -> datetime:
        return state.last_login

    @engine.variable("user_id", data_type="integer")
    def user_id() -> int:
        return state.user_id

    @engine.variable("region", data_type="string")
    def region() -> str:
        return state.region

    @engine.function("lookup", data_type="integer")
    def lookup() -> int | None:
        return state.lookup_value

    @engine.function("blocklist", data_type="integer")
    def blocklist() -> tuple[int, ...]:
        return (1, 2, 3)

    @engine.function("allowed_regions", data_type="string")
    def allowed_regions(tier: str) -> tuple[str, ...]:
        if tier == "premium":
            return ("US", "EU", "UK")
        return ("US", "CA")

    @engine.function("login_cutoff", data_type="datetime")
    def login_cutoff() -> datetime:
        return datetime(2024, 1, 1, 0, 0, 0)

    @engine.action("grant_access", data_type="boolean")
    def grant_access() -> bool:
        calls.append("success")
        return True

    @engine.action("reject_access", data_type="boolean")
    def reject_access() -> bool:
        calls.append("failure")
        return False

    @engine.action("audit_log", data_type="boolean")
    def audit_log() -> bool:
        calls.append("finally")
        return True


@pytest.fixture
def calls() -> list[str]:
    return []


def test_complex_rule_passes_and_runs_success_lifecycle(
    calls: list[str],
) -> None:
    engine = Engine()
    state = EligibilityState()
    _register_eligibility(engine, state, calls)
    rule = _build_rule()
    ctx = EvaluationContext(engine)

    assert rule.evaluate(ctx) is True
    assert _run_lifecycle(rule, ctx, calls) is True
    assert calls == ["success", "finally"]


def test_complex_rule_passes_via_legacy_path(calls: list[str]) -> None:
    engine = Engine()
    state = EligibilityState(
        tier="standard",
        balance=Decimal("10.00"),
        registration_date=date(2023, 6, 1),
        is_suspended=False,
        last_login=datetime(2024, 6, 15, 8, 0, 0),
        age=30,
        min_age=30,
    )
    _register_eligibility(engine, state, calls)
    rule = _build_rule()
    ctx = EvaluationContext(engine)

    assert rule.evaluate(ctx) is True
    assert _run_lifecycle(rule, ctx, calls) is True
    assert calls == ["success", "finally"]


def test_complex_rule_fails_and_runs_failure_lifecycle(calls: list[str]) -> None:
    engine = Engine()
    state = EligibilityState(age=16)
    _register_eligibility(engine, state, calls)
    rule = _build_rule()
    ctx = EvaluationContext(engine)

    assert rule.evaluate(ctx) is False
    assert _run_lifecycle(rule, ctx, calls) is False
    assert calls == ["failure", "finally"]


def test_complex_rule_local_context_overrides_variable(calls: list[str]) -> None:
    engine = Engine()
    state = EligibilityState()
    _register_eligibility(engine, state, calls)
    rule = _build_rule()

    local_ctx = Context()

    @local_ctx.variable("status", data_type="string")
    def local_status() -> str:
        return "inactive"

    ctx = EvaluationContext(engine, local_context=local_ctx)
    assert rule.evaluate(ctx) is False
