from dataclasses import dataclass

import pytest

from business_rules.business_rule import BusinessRule
from business_rules.condition import Condition
from business_rules.context import Context
from business_rules.engine import Engine
from business_rules.evaluation import EvaluationContext
from business_rules.executable import Action
from business_rules.name_normalizers import (
    CamelCaseNameNormalizer,
    SnakeCaseNameNormalizer,
)
from business_rules.target import target


@pytest.fixture
def engine() -> Engine:
    return Engine()


@dataclass
class TrueCondition(Condition):
    def evaluate(self, ctx: EvaluationContext) -> bool:
        return True


@dataclass
class FalseCondition(Condition):
    def evaluate(self, ctx: EvaluationContext) -> bool:
        return False


def test_engine_defaults_to_snake_case_normalizer(engine: Engine) -> None:
    assert isinstance(engine.name_normalizer, SnakeCaseNameNormalizer)
    assert isinstance(engine.context._name_normalizer, SnakeCaseNameNormalizer)


def test_engine_custom_name_normalizer() -> None:
    normalizer = CamelCaseNameNormalizer()
    engine = Engine(name_normalizer=normalizer)
    assert engine.name_normalizer is normalizer
    assert engine.context._name_normalizer is normalizer


def test_engine_variable_registers_in_global_context(engine: Engine) -> None:
    @engine.variable("user_age", data_type="integer")
    def user_age() -> int:
        return 42

    assert "user_age" in engine.context.variables
    assert engine.context.get_variable("user_age").func is user_age


def test_resolve_variable_from_global_when_context_is_none(engine: Engine) -> None:
    @engine.variable("user_age", data_type="integer")
    def user_age() -> int:
        return 42

    entry = engine.resolve_variable("user_age", None)
    assert entry.func is user_age


def test_resolve_variable_from_local_when_present(engine: Engine) -> None:
    ctx = Context()

    @ctx.variable("tenant_id", data_type="string")
    def tenant_id() -> str:
        return "local"

    entry = engine.resolve_variable("tenant_id", ctx)
    assert entry.func is tenant_id


def test_resolve_variable_falls_back_to_global(engine: Engine) -> None:
    @engine.variable("shared_var", data_type="boolean")
    def shared_var() -> bool:
        return True

    local_ctx = Context()
    entry = engine.resolve_variable("shared_var", local_ctx)
    assert entry.func is shared_var


def test_resolve_variable_local_overrides_global(engine: Engine) -> None:
    @engine.variable("priority", data_type="integer")
    def global_priority() -> int:
        return 1

    local_ctx = Context()

    @local_ctx.variable("priority", data_type="integer")
    def local_priority() -> int:
        return 2

    assert engine.resolve_variable("priority", local_ctx).func is local_priority
    assert engine.context.get_variable("priority").func is global_priority


def test_resolve_action_falls_back_to_global(engine: Engine) -> None:
    @engine.action("global_action", data_type="boolean")
    def global_action() -> bool:
        return True

    local_ctx = Context()
    entry = engine.resolve_action("global_action", local_ctx)
    assert entry.func is global_action


def test_resolve_function_falls_back_to_global(engine: Engine) -> None:
    @engine.function("global_function", data_type="integer")
    def global_function() -> int:
        return 1

    local_ctx = Context()
    entry = engine.resolve_function("global_function", local_ctx)
    assert entry.func is global_function


def test_resolve_action_local_overrides_global(engine: Engine) -> None:
    @engine.action("notify", data_type="boolean")
    def global_notify() -> bool:
        return True

    local_ctx = Context()

    @local_ctx.action("notify", data_type="boolean")
    def local_notify() -> bool:
        return False

    assert engine.resolve_action("notify", local_ctx).func is local_notify


def test_resolve_unknown_variable_raises_key_error(engine: Engine) -> None:
    with pytest.raises(KeyError, match="not registered"):
        engine.resolve_variable("missing", None)


def test_resolve_unknown_variable_in_local_context_raises_key_error(
    engine: Engine,
) -> None:
    local_ctx = Context()
    with pytest.raises(KeyError, match="not registered"):
        engine.resolve_variable("missing", local_ctx)


def test_resolve_normalizes_names_via_context_normalizer(engine: Engine) -> None:
    @engine.variable("user_age", data_type="integer")
    def user_age() -> int:
        return 42

    entry = engine.resolve_variable("userAge", Context())
    assert entry.func is user_age


def test_global_context_get_methods_normalize_search_names(engine: Engine) -> None:
    @engine.variable("user_age", data_type="integer")
    def user_age() -> int:
        return 1

    @engine.action("notify_user", data_type="boolean")
    def notify_user() -> bool:
        return True

    @engine.function("sum_values", data_type="integer")
    def sum_values() -> int:
        return 2

    global_ctx = engine.context
    assert global_ctx.get_variable("userAge").func is user_age
    assert global_ctx.get_action("notifyUser").func is notify_user
    assert global_ctx.get_function("sumValues").func is sum_values


def test_check_evaluates_condition_without_running_lifecycle(engine: Engine) -> None:
    calls: list[str] = []

    @engine.action("on_success", data_type="boolean")
    def on_success() -> bool:
        calls.append("success")
        return True

    @engine.action("on_failure", data_type="boolean")
    def on_failure() -> bool:
        calls.append("failure")
        return False

    @engine.action("on_finally", data_type="boolean")
    def on_finally() -> bool:
        calls.append("finally")
        return True

    rule = BusinessRule(
        having=TrueCondition(),
        on_success=[Action(name="on_success")],
        on_failure=[Action(name="on_failure")],
        on_finally=[Action(name="on_finally")],
    )
    assert engine.check(rule) is True
    assert calls == []

    rule = BusinessRule(
        having=FalseCondition(),
        on_success=[Action(name="on_success")],
        on_failure=[Action(name="on_failure")],
        on_finally=[Action(name="on_finally")],
    )
    assert engine.check(rule) is False
    assert calls == []


def test_check_accepts_business_rule_and_optional_context(engine: Engine) -> None:
    rule = BusinessRule(having=TrueCondition())
    assert engine.check(rule) is True
    assert engine.check(rule, local_context=Context()) is True


def test_run_accepts_business_rule_and_optional_context(engine: Engine) -> None:
    rule = BusinessRule(having=TrueCondition())
    assert engine.run(rule) is True
    assert engine.run(rule, local_context=Context()) is True


def test_run_executes_success_and_finally_lifecycle(engine: Engine) -> None:
    calls: list[str] = []

    @engine.action("on_success", data_type="boolean")
    def on_success() -> bool:
        calls.append("success")
        return True

    @engine.action("on_finally", data_type="boolean")
    def on_finally() -> bool:
        calls.append("finally")
        return True

    rule = BusinessRule(
        having=TrueCondition(),
        on_success=[Action(name="on_success")],
        on_finally=[Action(name="on_finally")],
    )
    assert engine.run(rule) is True
    assert calls == ["success", "finally"]


def test_run_executes_failure_and_finally_lifecycle(engine: Engine) -> None:
    calls: list[str] = []

    @engine.action("on_failure", data_type="boolean")
    def on_failure() -> bool:
        calls.append("failure")
        return False

    @engine.action("on_finally", data_type="boolean")
    def on_finally() -> bool:
        calls.append("finally")
        return True

    rule = BusinessRule(
        having=FalseCondition(),
        on_failure=[Action(name="on_failure")],
        on_finally=[Action(name="on_finally")],
    )
    assert engine.run(rule) is False
    assert calls == ["failure", "finally"]


def test_run_uses_local_context_for_lifecycle_actions(engine: Engine) -> None:
    calls: list[str] = []

    @engine.action("notify", data_type="string")
    def global_notify() -> str:
        calls.append("global")
        return "global"

    local_ctx = Context()

    @local_ctx.action("notify", data_type="string")
    def local_notify() -> str:
        calls.append("local")
        return "local"

    rule = BusinessRule(
        having=TrueCondition(),
        on_success=[Action(name="notify")],
    )
    engine.run(rule, local_context=local_ctx)
    assert calls == ["local"]


def test_run_passes_target_to_lifecycle_actions(engine: Engine) -> None:
    received: list[object] = []

    @engine.action("capture", data_type="boolean")
    def capture(subject: object) -> bool:
        received.append(subject)
        return True

    rule = BusinessRule(
        having=TrueCondition(),
        on_success=[Action(name="capture", args=(target(),))],
    )
    user = {"id": 99}
    engine.run(rule, target=user)
    assert received == [user]
