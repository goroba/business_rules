import pytest

from business_rules.context import (
    Context,
    GlobalContext,
    action,
    function,
    get_global_context,
    variable,
)


@pytest.fixture(autouse=True)
def _clear_global_context() -> None:
    global_ctx = get_global_context()
    global_ctx._variables.clear()
    global_ctx._actions.clear()
    global_ctx._functions.clear()
    yield
    global_ctx._variables.clear()
    global_ctx._actions.clear()
    global_ctx._functions.clear()


def test_global_context_singleton() -> None:
    assert get_global_context() is get_global_context()
    assert isinstance(get_global_context(), GlobalContext)


def test_register_variable_in_global_context() -> None:
    @variable("user_age", data_type="integer")
    def user_age() -> int:
        return 42

    entry = get_global_context().get_variable("user_age")
    assert entry.name == "user_age"
    assert entry.data_type == "integer"
    assert entry.func is user_age
    assert get_global_context().variables["user_age"] is entry


def test_register_variable_without_explicit_name() -> None:
    @variable(data_type="string")
    def tenant_id() -> str:
        return "t-1"

    entry = get_global_context().get_variable("tenant_id")
    assert entry.name == "tenant_id"
    assert entry.func is tenant_id


def test_register_callable_class() -> None:
    @variable(data_type="string")
    class CurrentUser:
        def __call__(self) -> str:
            return "alice"

    entry = get_global_context().get_variable("CurrentUser")
    assert entry.name == "CurrentUser"
    assert entry.func is CurrentUser


def test_register_callable_class_rejects_missing_call() -> None:
    with pytest.raises(TypeError, match="__call__"):

        @variable(data_type="string")
        class NotCallable:
            pass


def test_register_in_local_context() -> None:
    ctx = Context()

    @variable("tenant_id", context=ctx, data_type="string")
    def tenant_id() -> str:
        return "local"

    assert "tenant_id" in ctx.variables
    assert "tenant_id" not in get_global_context().variables
    assert ctx.get_variable("tenant_id").func is tenant_id


def test_lookup_falls_back_to_global() -> None:
    @variable("shared_var", data_type="boolean")
    def shared_var() -> bool:
        return True

    local_ctx = Context()
    entry = local_ctx.get_variable("shared_var")
    assert entry.func is shared_var


def test_local_overrides_global_on_lookup() -> None:
    @variable("priority", data_type="integer")
    def global_priority() -> int:
        return 1

    local_ctx = Context()

    @variable("priority", context=local_ctx, data_type="integer")
    def local_priority() -> int:
        return 2

    assert local_ctx.get_variable("priority").func is local_priority
    assert get_global_context().get_variable("priority").func is global_priority


def test_register_action_and_function() -> None:
    @action(data_type="boolean")
    def notify() -> bool:
        return True

    @function("sum_values", data_type="integer")
    def sum_values(a: int, b: int) -> int:
        return a + b

    action_entry = get_global_context().get_action("notify")
    assert action_entry.data_type == "boolean"
    assert action_entry.func is notify

    function_entry = get_global_context().get_function("sum_values")
    assert function_entry.data_type == "integer"
    assert function_entry.func is sum_values


def test_namespace_isolation() -> None:
    @variable("shared_name", data_type="string")
    def as_variable() -> str:
        return "v"

    @action("shared_name", data_type="boolean")
    def as_action() -> bool:
        return True

    @function("shared_name", data_type="integer")
    def as_function() -> int:
        return 0

    global_ctx = get_global_context()
    assert global_ctx.get_variable("shared_name").func is as_variable
    assert global_ctx.get_action("shared_name").func is as_action
    assert global_ctx.get_function("shared_name").func is as_function


def test_local_contexts_are_independent() -> None:
    ctx_a = Context()
    ctx_b = Context()

    @variable("only_a", context=ctx_a, data_type="string")
    def only_a() -> str:
        return "a"

    @variable("only_b", context=ctx_b, data_type="string")
    def only_b() -> str:
        return "b"

    assert "only_a" in ctx_a.variables
    assert "only_a" not in ctx_b.variables
    assert "only_b" in ctx_b.variables
    assert "only_b" not in ctx_a.variables


def test_register_rejects_duplicate_name() -> None:
    ctx = Context()

    @variable("dup", context=ctx, data_type="string")
    def first() -> str:
        return "first"

    with pytest.raises(ValueError, match="already registered"):

        @variable("dup", context=ctx, data_type="string")
        def second() -> str:
            return "second"


def test_register_rejects_empty_name() -> None:
    with pytest.raises(ValueError, match="empty"):

        @variable("", data_type="string")
        def empty_name() -> str:
            return ""


def test_register_rejects_unknown_data_type() -> None:
    with pytest.raises(KeyError, match="not registered"):

        @variable("bad_type", data_type="unknown")
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


def test_global_context_get_unknown_entries_raise_key_error() -> None:
    global_ctx = get_global_context()
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


def test_lookup_action_and_function_fall_back_to_global() -> None:
    @action("global_action", data_type="boolean")
    def global_action() -> bool:
        return True

    @function("global_function", data_type="integer")
    def global_function() -> int:
        return 1

    local_ctx = Context()
    assert local_ctx.get_action("global_action").func is global_action
    assert local_ctx.get_function("global_function").func is global_function
