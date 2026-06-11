import pytest

from business_rules.context import Context
from business_rules.engine import Engine
from business_rules.evaluation import EvaluationContext
from business_rules.executable import Executable
from business_rules.operand import Function, Literal, Operand, Variable


@pytest.fixture
def engine() -> Engine:
    return Engine()


def test_variable() -> None:
    operand = Variable("field_name")
    assert operand.name == "field_name"


def test_literal() -> None:
    operand = Literal("42")
    assert operand.value == "42"


def test_operand_hierarchy() -> None:
    assert issubclass(Function, Operand)
    assert issubclass(Function, Executable)
    assert issubclass(Variable, Operand)
    assert issubclass(Literal, Operand)


def test_literal_evaluate_returns_value(engine: Engine) -> None:
    assert Literal("42").evaluate(EvaluationContext(engine)) == "42"


def test_literal_evaluate_requires_context() -> None:
    with pytest.raises(TypeError):
        Literal("42").evaluate()  # type: ignore[call-arg]


def test_variable_evaluate_calls_registered_variable(engine: Engine) -> None:
    @engine.variable("user_age", data_type="integer")
    def user_age() -> int:
        return 42

    variable = Variable("user_age")
    assert variable.evaluate(EvaluationContext(engine)) == 42


def test_variable_evaluate_uses_local_context_override(engine: Engine) -> None:
    @engine.variable("tenant_id", data_type="string")
    def global_tenant_id() -> str:
        return "global"

    local_ctx = Context()

    @local_ctx.variable("tenant_id", data_type="string")
    def local_tenant_id() -> str:
        return "local"

    variable = Variable("tenant_id")
    ctx = EvaluationContext(engine, local_context=local_ctx)
    assert variable.evaluate(ctx) == "local"


def test_variable_evaluate_falls_back_to_engine_context(engine: Engine) -> None:
    @engine.variable("shared_var", data_type="boolean")
    def shared_var() -> bool:
        return True

    variable = Variable("shared_var")
    ctx = EvaluationContext(engine, local_context=Context())
    assert variable.evaluate(ctx) is True


def test_variable_evaluate_unknown_raises_key_error(engine: Engine) -> None:
    variable = Variable("missing")
    with pytest.raises(KeyError, match="not registered"):
        variable.evaluate(EvaluationContext(engine))


def test_variable_evaluate_requires_context() -> None:
    with pytest.raises(TypeError):
        Variable("field_name").evaluate()  # type: ignore[call-arg]


def test_function() -> None:
    function = Function(
        name="sum",
        args=(Variable("a"), Variable("b")),
        kwargs={"precision": Literal("2")},
    )
    assert function.name == "sum"
    assert function.args == (Variable("a"), Variable("b"))
    assert function.kwargs == {"precision": Literal("2")}


def test_function_defaults() -> None:
    function = Function(name="noop")
    assert function.args == ()
    assert function.kwargs == {}


def test_function_evaluate_calls_registered_function(engine: Engine) -> None:
    @engine.function("add", data_type="integer")
    def add(a: int, b: int) -> int:
        return a + b

    function = Function(name="add", args=(1, 2))
    assert function.evaluate(EvaluationContext(engine)) == 3


def test_function_evaluate_passes_kwargs(engine: Engine) -> None:
    @engine.function("scale", data_type="integer")
    def scale(value: int, *, factor: int) -> int:
        return value * factor

    function = Function(name="scale", args=(5,), kwargs={"factor": 10})
    assert function.evaluate(EvaluationContext(engine)) == 50


def test_function_evaluate_uses_local_context_override(engine: Engine) -> None:
    @engine.function("resolve", data_type="string")
    def global_resolve() -> str:
        return "global"

    local_ctx = Context()

    @local_ctx.function("resolve", data_type="string")
    def local_resolve() -> str:
        return "local"

    function = Function(name="resolve")
    ctx = EvaluationContext(engine, local_context=local_ctx)
    assert function.evaluate(ctx) == "local"


def test_function_evaluate_falls_back_to_engine_context(engine: Engine) -> None:
    @engine.function("shared", data_type="integer")
    def shared() -> int:
        return 42

    function = Function(name="shared")
    ctx = EvaluationContext(engine, local_context=Context())
    assert function.evaluate(ctx) == 42


def test_function_evaluate_unknown_raises_key_error(engine: Engine) -> None:
    function = Function(name="missing")
    with pytest.raises(KeyError, match="not registered"):
        function.evaluate(EvaluationContext(engine))


def test_function_evaluate_requires_context() -> None:
    with pytest.raises(TypeError):
        Function(name="noop").evaluate()  # type: ignore[call-arg]
