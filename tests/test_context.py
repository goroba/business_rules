import pytest

from business_rules.context import Context
from business_rules.engine import Engine
from business_rules.name_normalizers import CamelCaseNameNormalizer


@pytest.fixture
def engine() -> Engine:
    return Engine()


def test_register_variable_in_global_context(engine: Engine) -> None:
    @engine.variable("user_age", data_type="integer")
    def user_age() -> int:
        return 42

    entry = engine.context.get_variable("user_age")
    assert entry.name == "user_age"
    assert entry.data_type == "integer"
    assert entry.func is user_age
    assert engine.context.variables["user_age"] is entry


def test_register_variable_without_explicit_name(engine: Engine) -> None:
    @engine.variable(data_type="string")
    def tenant_id() -> str:
        return "t-1"

    entry = engine.context.get_variable("tenant_id")
    assert entry.name == "tenant_id"
    assert entry.func is tenant_id


def test_register_callable_class(engine: Engine) -> None:
    @engine.variable(data_type="string")
    class CurrentUser:
        def __call__(self) -> str:
            return "alice"

    entry = engine.context.get_variable("CurrentUser")
    assert entry.name == "current_user"
    assert entry.func is CurrentUser


def test_register_callable_class_rejects_missing_call(engine: Engine) -> None:
    with pytest.raises(TypeError, match="__call__"):

        @engine.variable(data_type="string")
        class NotCallable:
            pass


def test_register_in_local_context(engine: Engine) -> None:
    ctx = Context()

    @ctx.variable("tenant_id", data_type="string")
    def tenant_id() -> str:
        return "local"

    assert "tenant_id" in ctx.variables
    assert "tenant_id" not in engine.context.variables
    assert ctx.get_variable("tenant_id").func is tenant_id


def test_register_action_and_function(engine: Engine) -> None:
    @engine.action(data_type="boolean")
    def notify() -> bool:
        return True

    @engine.function("sum_values", data_type="integer")
    def sum_values(a: int, b: int) -> int:
        return a + b

    action_entry = engine.context.get_action("notify")
    assert action_entry.data_type == "boolean"
    assert action_entry.func is notify

    function_entry = engine.context.get_function("sum_values")
    assert function_entry.data_type == "integer"
    assert function_entry.func is sum_values


def test_namespace_isolation(engine: Engine) -> None:
    @engine.variable("shared_name", data_type="string")
    def as_variable() -> str:
        return "v"

    @engine.action("shared_name", data_type="boolean")
    def as_action() -> bool:
        return True

    @engine.function("shared_name", data_type="integer")
    def as_function() -> int:
        return 0

    global_ctx = engine.context
    assert global_ctx.get_variable("shared_name").func is as_variable
    assert global_ctx.get_action("shared_name").func is as_action
    assert global_ctx.get_function("shared_name").func is as_function


def test_local_contexts_are_independent() -> None:
    ctx_a = Context()
    ctx_b = Context()

    @ctx_a.variable("only_a", data_type="string")
    def only_a() -> str:
        return "a"

    @ctx_b.variable("only_b", data_type="string")
    def only_b() -> str:
        return "b"

    assert "only_a" in ctx_a.variables
    assert "only_a" not in ctx_b.variables
    assert "only_b" in ctx_b.variables
    assert "only_b" not in ctx_a.variables


def test_register_rejects_duplicate_name() -> None:
    ctx = Context()

    @ctx.variable("dup", data_type="string")
    def first() -> str:
        return "first"

    with pytest.raises(ValueError, match="already registered"):

        @ctx.variable("dup", data_type="string")
        def second() -> str:
            return "second"


def test_register_rejects_empty_name(engine: Engine) -> None:
    with pytest.raises(ValueError, match="empty"):

        @engine.variable("", data_type="string")
        def empty_name() -> str:
            return ""


def test_register_rejects_unknown_data_type(engine: Engine) -> None:
    with pytest.raises(KeyError, match="not registered"):

        @engine.variable("bad_type", data_type="unknown")
        def bad_type() -> str:
            return ""


def test_get_unknown_entry_raises_key_error() -> None:
    ctx = Context()
    with pytest.raises(KeyError, match="not registered"):
        ctx.get_variable("missing")


def test_get_unknown_action_and_function_raise_key_error() -> None:
    ctx = Context()
    with pytest.raises(KeyError, match="Action"):
        ctx.get_action("missing")
    with pytest.raises(KeyError, match="Function"):
        ctx.get_function("missing")


def test_global_context_get_unknown_entries_raise_key_error(engine: Engine) -> None:
    global_ctx = engine.context
    with pytest.raises(KeyError, match="Variable"):
        global_ctx.get_variable("missing")
    with pytest.raises(KeyError, match="Action"):
        global_ctx.get_action("missing")
    with pytest.raises(KeyError, match="Function"):
        global_ctx.get_function("missing")


def test_actions_and_functions_properties() -> None:
    ctx = Context()

    def noop_action() -> bool:
        return True

    def noop_function() -> int:
        return 0

    ctx.register_action("noop_action", noop_action, "boolean")
    ctx.register_function("noop_function", noop_function, "integer")

    assert ctx.actions["noop_action"].func is noop_action
    assert ctx.functions["noop_function"].func is noop_function


def test_register_rejects_empty_name_via_register_method() -> None:
    ctx = Context()
    with pytest.raises(ValueError, match="empty"):
        ctx.register_variable("", lambda: "x", "string")


def test_register_rejects_non_callable() -> None:
    ctx = Context()
    with pytest.raises(TypeError, match="callable"):
        ctx.register_variable("bad", "not-callable", "string")  # type: ignore[arg-type]


def test_get_variable_with_alternate_casing(engine: Engine) -> None:
    @engine.variable("user_age", data_type="integer")
    def user_age() -> int:
        return 42

    assert engine.context.get_variable("userAge").func is user_age
    assert engine.context.get_variable("User-Age").func is user_age


def test_get_action_with_alternate_casing(engine: Engine) -> None:
    @engine.action("notify_user", data_type="boolean")
    def notify_user() -> bool:
        return True

    assert engine.context.get_action("notifyUser").func is notify_user


def test_get_function_with_alternate_casing(engine: Engine) -> None:
    @engine.function("sum_values", data_type="integer")
    def sum_values(a: int, b: int) -> int:
        return a + b

    assert engine.context.get_function("sumValues").func is sum_values


def test_register_rejects_equivalent_casing_as_duplicate() -> None:
    ctx = Context()

    @ctx.variable("user_age", data_type="string")
    def first() -> str:
        return "first"

    with pytest.raises(ValueError, match="already registered"):

        @ctx.variable("userAge", data_type="string")
        def second() -> str:
            return "second"


def test_context_with_camel_case_normalizer() -> None:
    ctx = Context(name_normalizer=CamelCaseNameNormalizer())

    @ctx.variable("user_age", data_type="string")
    def user_age() -> str:
        return "ok"

    assert "userAge" in ctx.variables
    assert ctx.get_variable("user_age").func is user_age
    assert ctx.get_variable("UserAge").func is user_age


def test_local_context_does_not_fallback_to_global(engine: Engine) -> None:
    @engine.variable("shared_var", data_type="boolean")
    def shared_var() -> bool:
        return True

    local_ctx = Context()
    with pytest.raises(KeyError, match="not registered"):
        local_ctx.get_variable("shared_var")


def test_local_context_does_not_see_global_action_or_function(
    engine: Engine,
) -> None:
    @engine.action("global_action", data_type="boolean")
    def global_action() -> bool:
        return True

    @engine.function("global_function", data_type="integer")
    def global_function() -> int:
        return 1

    local_ctx = Context()
    with pytest.raises(KeyError, match="Action"):
        local_ctx.get_action("global_action")
    with pytest.raises(KeyError, match="Function"):
        local_ctx.get_function("global_function")
