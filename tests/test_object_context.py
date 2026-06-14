"""Tests for ObjectContext."""

from __future__ import annotations

import pytest

from business_rules.business_rule import BusinessRule
from business_rules.condition import BinaryCondition
from business_rules.context import ObjectContext
from business_rules.engine import Engine
from business_rules.executable import Action
from business_rules.operand import Function, Literal, Variable
from business_rules.operators import EqOperator, GteOperator


class Data:
    var1: str
    var2: int

    def __init__(self) -> None:
        self.var1 = "active"
        self.var2 = 25

    def action(self) -> bool:
        return True

    def function(self, x: int) -> int:
        return x * 2


class DataWithPrivate:
    visible: str

    def __init__(self) -> None:
        self.visible = "ok"
        self._hidden = "secret"

    def _hidden_method(self) -> str:
        return self._hidden


class DataWithCamelCase:
    userAge: int

    def __init__(self) -> None:
        self.userAge = 30


class DataWithoutHints:
    def __init__(self) -> None:
        self.unannotated = "value"


@pytest.fixture
def engine() -> Engine:
    return Engine()


def test_object_context_variable_from_attribute(engine: Engine) -> None:
    data = Data()
    object_ctx = ObjectContext(data)
    rule = BusinessRule(
        having=BinaryCondition(
            left=Variable("var1"),
            operator=EqOperator,
            right=Literal("active"),
        )
    )
    assert engine.run(rule, local_context=object_ctx) is True


def test_object_context_method_as_function_and_action(engine: Engine) -> None:
    data = Data()
    object_ctx = ObjectContext(data)
    function_rule = BusinessRule(
        having=BinaryCondition(
            left=Function("function", args=(5,)),
            operator=EqOperator,
            right=Literal("10"),
        )
    )
    assert engine.run(function_rule, local_context=object_ctx) is True

    action_calls: list[bool] = []

    class TrackingData(Data):
        def action(self) -> bool:
            action_calls.append(True)
            return True

    action_rule = BusinessRule(
        having=BinaryCondition(
            left=Variable("var2"),
            operator=GteOperator,
            right=Literal("18"),
        ),
        on_success=[Action(name="action")],
    )
    engine.run(action_rule, local_context=ObjectContext(TrackingData()))
    assert action_calls == [True]


def test_object_context_registration_is_deferred(engine: Engine) -> None:
    object_ctx = ObjectContext(Data())
    assert dict(object_ctx.variables) == {}
    assert dict(object_ctx.actions) == {}
    assert dict(object_ctx.functions) == {}

    object_ctx.get_variable("var1")
    assert "var1" in object_ctx.variables
    assert dict(object_ctx.actions) == {}
    assert dict(object_ctx.functions) == {}

    object_ctx.get_action("action")
    assert "action" in object_ctx.actions
    assert dict(object_ctx.functions) == {}

    object_ctx.get_function("function")
    assert "function" in object_ctx.functions


def test_object_context_falls_back_to_global(engine: Engine) -> None:
    @engine.variable("global_only", data_type="string")
    def global_only() -> str:
        return "global"

    data = Data()
    object_ctx = ObjectContext(data)
    rule = BusinessRule(
        having=BinaryCondition(
            left=Variable("global_only"),
            operator=EqOperator,
            right=Literal("global"),
        )
    )
    assert engine.run(rule, local_context=object_ctx) is True


def test_object_context_overrides_global(engine: Engine) -> None:
    @engine.variable("var1", data_type="string")
    def global_var1() -> str:
        return "global"

    data = Data()
    data.var1 = "local"
    object_ctx = ObjectContext(data)
    rule = BusinessRule(
        having=BinaryCondition(
            left=Variable("var1"),
            operator=EqOperator,
            right=Literal("local"),
        )
    )
    assert engine.run(rule, local_context=object_ctx) is True


def test_object_context_data_type_override(engine: Engine) -> None:
    class AmbiguousData:
        value: int

        def __init__(self) -> None:
            self.value = 1

    object_ctx = ObjectContext(AmbiguousData(), data_types={"value": "string"})
    entry = object_ctx.get_variable("value")
    assert entry.data_type == "string"


def test_object_context_missing_data_type_raises(engine: Engine) -> None:
    object_ctx = ObjectContext(DataWithoutHints())
    with pytest.raises(ValueError, match="No type annotation for 'unannotated'"):
        object_ctx.get_variable("unannotated")


def test_object_context_skips_private_members(engine: Engine) -> None:
    object_ctx = ObjectContext(DataWithPrivate())
    with pytest.raises(KeyError, match="not registered"):
        object_ctx.get_variable("_hidden")
    with pytest.raises(KeyError, match="not registered"):
        object_ctx.get_action("_hidden_method")


def test_object_context_name_normalization(engine: Engine) -> None:
    object_ctx = ObjectContext(DataWithCamelCase())
    entry = object_ctx.get_variable("user_age")
    assert entry.name == "user_age"

    rule = BusinessRule(
        having=BinaryCondition(
            left=Variable("userAge"),
            operator=EqOperator,
            right=Literal("30"),
        )
    )
    assert engine.run(rule, local_context=object_ctx) is True
