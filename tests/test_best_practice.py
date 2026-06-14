"""Integration tests for the recommended data + action context pattern."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

import pytest

from business_rules.builder import binary, function, get_builder, target, variable
from business_rules.business_rule import BusinessRule
from business_rules.context import Context, ObjectContext
from business_rules.engine import Engine
from business_rules.target import Target


@dataclass
class User:
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

    def is_adult(self) -> bool:
        return self.age >= 18

# fmt: off


def _build_rule_via_builder_with_target() -> BusinessRule:
    return (
        get_builder()
        .having()
        .all()
            .all()
                .binary(function("is_adult"), "eq", "true")
                .binary(variable("status"), "eq", "active")
                .unary(variable("email"), "is_not_null")
                .binary(variable("email"), "contains", "@")
                .unary(function("lookup"), "is_not_null")
            .end()
            .any()
                .all()
                    .binary(variable("tier"), "eq", "premium")
                    .binary(variable("balance"), "gte", "100.00")
                .end()
                .all()
                    .binary(variable("registration_date"), "lt", "2024-06-01")
                    .negative(binary(variable("is_suspended"), "eq", "true"))
                    .binary(variable("last_login"), "gte", function("login_cutoff"))
                    .binary(variable("age"), "eq", variable("min_age"))
                .end()
            .end()
            .negative(binary(variable("user_id"), "is_in", function("blocklist")))
            .binary(
                variable("region"),
                "is_in",
                function("allowed_regions", args=("premium",)),
            )
        .end()
        .on_success()
            .action("grant_access", args=(target(),))
        .end()
        .on_failure()
            .action("reject_access", args=(target(),))
        .end()
        .on_finally()
            .action("audit_log", args=(target(),))
        .end()
        .build()
    )


# fmt: on


def _register_action_context(
    action_context: Context,
    user: User,
    calls: list[str],
) -> None:
    @action_context.function("lookup", data_type="integer")
    def lookup() -> int | None:
        return user.lookup_value

    @action_context.function("blocklist", data_type="integer")
    def blocklist() -> tuple[int, ...]:
        return (1, 2, 3)

    @action_context.function("allowed_regions", data_type="string")
    def allowed_regions(tier: str) -> tuple[str, ...]:
        if tier == "premium":
            return ("US", "EU", "UK")
        return ("US", "CA")

    @action_context.function("login_cutoff", data_type="datetime")
    def login_cutoff() -> datetime:
        return datetime(2024, 1, 1, 0, 0, 0)

    @action_context.action("grant_access", data_type="boolean")
    def grant_access(subject: User) -> bool:
        calls.append("success")
        assert subject is user
        return True

    @action_context.action("reject_access", data_type="boolean")
    def reject_access(subject: User) -> bool:
        calls.append("failure")
        assert subject is user
        return False

    @action_context.action("audit_log", data_type="boolean")
    def audit_log(subject: User) -> bool:
        calls.append("finally")
        assert subject is user
        return True


def _nested_contexts(user: User, calls: list[str]) -> Context:
    data_context = ObjectContext(user)
    action_context = Context()
    _register_action_context(action_context, user, calls)
    action_context.nests(data_context)
    return action_context


@pytest.fixture
def calls() -> list[str]:
    return []


def test_builder_rule_lifecycle_actions_use_target() -> None:
    rule = _build_rule_via_builder_with_target()
    assert rule.on_success is not None
    assert rule.on_failure is not None
    assert rule.on_finally is not None
    for actions in (rule.on_success, rule.on_failure, rule.on_finally):
        assert len(actions) == 1
        assert actions[0].args == (Target(),)


def test_complex_rule_passes_with_nested_object_context(calls: list[str]) -> None:
    user = User()
    engine = Engine()
    rule = _build_rule_via_builder_with_target()
    action_context = _nested_contexts(user, calls)

    assert engine.run(rule, local_context=action_context, target=user) is True
    assert calls == ["success", "finally"]


def test_complex_rule_fails_with_nested_object_context(calls: list[str]) -> None:
    user = User(age=16)
    engine = Engine()
    rule = _build_rule_via_builder_with_target()
    action_context = _nested_contexts(user, calls)

    assert engine.run(rule, local_context=action_context, target=user) is False
    assert calls == ["failure", "finally"]
