"""Tests for nested context composition."""

from __future__ import annotations

import pytest

from business_rules.business_rule import BusinessRule
from business_rules.condition import BinaryCondition
from business_rules.context import Context, ObjectContext
from business_rules.engine import Engine
from business_rules.executable import Action
from business_rules.operand import Literal, Variable
from business_rules.operators import EqOperator


@pytest.fixture
def engine() -> Engine:
    return Engine()


def test_three_level_chain_resolution(engine: Engine) -> None:
    child = Context()
    parent = Context()
    grandparent = Context()
    parent.nests(child)
    grandparent.nests(parent)

    @child.variable("status", data_type="string")
    def child_status() -> str:
        return "child"

    @parent.action("notify", data_type="string")
    def parent_notify() -> str:
        return "parent"

    @grandparent.function("compute", data_type="integer")
    def grandparent_compute() -> int:
        return 7

    assert engine.resolve_variable("status", grandparent).func is child_status
    assert engine.resolve_action("notify", grandparent).func is parent_notify
    assert engine.resolve_function("compute", grandparent).func is grandparent_compute

    calls: list[str] = []

    @parent.action("track", data_type="boolean")
    def track() -> bool:
        calls.append("parent")
        return True

    rule = BusinessRule(
        having=BinaryCondition(
            left=Variable("status"),
            operator=EqOperator,
            right=Literal("child"),
        ),
        on_success=[Action(name="track")],
    )
    assert engine.run(rule, local_context=grandparent) is True
    assert calls == ["parent"]


def test_inner_overrides_outer(engine: Engine) -> None:
    child = Context()
    parent = Context()
    parent.nests(child)

    @child.variable("priority", data_type="integer")
    def child_priority() -> int:
        return 1

    @parent.variable("priority", data_type="integer")
    def parent_priority() -> int:
        return 2

    assert engine.resolve_variable("priority", parent).func is child_priority


def test_fallback_through_chain_to_global(engine: Engine) -> None:
    child = Context()
    parent = Context()
    parent.nests(child)

    @engine.variable("global_only", data_type="string")
    def global_only() -> str:
        return "global"

    rule = BusinessRule(
        having=BinaryCondition(
            left=Variable("global_only"),
            operator=EqOperator,
            right=Literal("global"),
        )
    )
    assert engine.run(rule, local_context=parent) is True


def test_object_context_nested_in_action_context(engine: Engine) -> None:
    class Data:
        status: str

        def __init__(self) -> None:
            self.status = "active"

    action_context = Context()
    data_context = ObjectContext(Data())
    action_context.nests(data_context)

    calls: list[str] = []

    @action_context.action("audit", data_type="boolean")
    def audit() -> bool:
        calls.append("audit")
        return True

    rule = BusinessRule(
        having=BinaryCondition(
            left=Variable("status"),
            operator=EqOperator,
            right=Literal("active"),
        ),
        on_success=[Action(name="audit")],
    )
    assert engine.run(rule, local_context=action_context) is True
    assert calls == ["audit"]


def test_nests_fluent_chaining(engine: Engine) -> None:
    child = Context()
    parent = Context()
    grandparent = Context()

    @child.variable("level", data_type="string")
    def child_level() -> str:
        return "child"

    composed = grandparent.nests(parent.nests(child))
    assert composed is grandparent
    assert engine.resolve_variable("level", grandparent).func is child_level


def test_circular_nesting_raises() -> None:
    outer = Context()
    inner = Context()
    outer.nests(inner)
    with pytest.raises(ValueError, match="Circular nested context chain"):
        inner.nests(outer)


def test_global_released_after_run(engine: Engine) -> None:
    local = Context()

    @local.variable("scoped", data_type="string")
    def local_scoped() -> str:
        return "local"

    @engine.variable("scoped", data_type="string")
    def global_scoped() -> str:
        return "global"

    rule = BusinessRule(
        having=BinaryCondition(
            left=Variable("scoped"),
            operator=EqOperator,
            right=Literal("local"),
        )
    )
    assert engine.run(rule, local_context=local) is True

    global_rule = BusinessRule(
        having=BinaryCondition(
            left=Variable("scoped"),
            operator=EqOperator,
            right=Literal("global"),
        )
    )
    assert engine.run(global_rule) is True


def test_global_released_after_check(engine: Engine) -> None:
    local = Context()

    @local.variable("scoped", data_type="string")
    def local_scoped() -> str:
        return "local"

    @engine.variable("scoped", data_type="string")
    def global_scoped() -> str:
        return "global"

    local_rule = BusinessRule(
        having=BinaryCondition(
            left=Variable("scoped"),
            operator=EqOperator,
            right=Literal("local"),
        )
    )
    assert engine.check(local_rule, local_context=local) is True

    global_rule = BusinessRule(
        having=BinaryCondition(
            left=Variable("scoped"),
            operator=EqOperator,
            right=Literal("global"),
        )
    )
    assert engine.check(global_rule) is True


def test_global_released_after_exception(engine: Engine) -> None:
    from dataclasses import dataclass

    from business_rules.condition import Condition
    from business_rules.evaluation import EvaluationContext

    local = Context()

    @local.action("boom", data_type="boolean")
    def boom() -> bool:
        raise RuntimeError("boom")

    @dataclass
    class TrueCondition(Condition):
        def evaluate(self, ctx: EvaluationContext) -> bool:
            return True

    rule = BusinessRule(
        having=TrueCondition(),
        on_success=[Action(name="boom")],
    )
    with pytest.raises(RuntimeError, match="boom"):
        engine.run(rule, local_context=local)

    @engine.variable("after_error", data_type="string")
    def after_error() -> str:
        return "ok"

    recovery_rule = BusinessRule(
        having=BinaryCondition(
            left=Variable("after_error"),
            operator=EqOperator,
            right=Literal("ok"),
        )
    )
    assert engine.run(recovery_rule) is True


def test_no_leak_between_runs(engine: Engine) -> None:
    local_one = Context()
    local_two = Context()

    @local_one.variable("tenant", data_type="string")
    def tenant_one() -> str:
        return "one"

    @local_two.variable("tenant", data_type="string")
    def tenant_two() -> str:
        return "two"

    rule = BusinessRule(
        having=BinaryCondition(
            left=Variable("tenant"),
            operator=EqOperator,
            right=Literal("one"),
        )
    )
    assert engine.run(rule, local_context=local_one) is True

    rule_two = BusinessRule(
        having=BinaryCondition(
            left=Variable("tenant"),
            operator=EqOperator,
            right=Literal("two"),
        )
    )
    assert engine.run(rule_two, local_context=local_two) is True


def test_get_methods_remain_local_only(engine: Engine) -> None:
    child = Context()
    parent = Context()
    parent.nests(child)

    @child.variable("shared", data_type="string")
    def child_shared() -> str:
        return "child"

    with pytest.raises(KeyError, match="not registered"):
        parent.get_variable("shared")

    @engine.variable("shared", data_type="string")
    def global_shared() -> str:
        return "global"

    with pytest.raises(KeyError, match="not registered"):
        parent.get_variable("shared")
