import pytest

from business_rules.context import Context
from business_rules.engine import Engine
from business_rules.evaluation import EvaluationContext
from business_rules.executable import Action
from business_rules.operand import Function, Literal, Variable
from business_rules.target import target


@pytest.fixture
def engine() -> Engine:
    return Engine()


def test_action() -> None:
    action = Action(
        name="notify",
        args=(Variable("user_id"), Literal("sent")),
        kwargs={"channel": Literal("email")},
    )
    assert action.name == "notify"
    assert action.args == (Variable("user_id"), Literal("sent"))
    assert action.kwargs == {"channel": Literal("email")}


def test_action_defaults() -> None:
    action = Action(name="noop")
    assert action.args == ()
    assert action.kwargs == {}


def test_action_execute_calls_registered_action(engine: Engine) -> None:
    @engine.action("notify", data_type="boolean")
    def notify(user_id: int, status: str) -> bool:
        return user_id == 1 and status == "sent"

    action = Action(name="notify", args=(1, "sent"))
    assert action.execute(EvaluationContext(engine)) is True


def test_action_execute_passes_kwargs(engine: Engine) -> None:
    @engine.action("scale", data_type="integer")
    def scale(value: int, *, factor: int) -> int:
        return value * factor

    action = Action(name="scale", args=(5,), kwargs={"factor": 10})
    assert action.execute(EvaluationContext(engine)) == 50


def test_action_execute_uses_local_context_override(engine: Engine) -> None:
    @engine.action("resolve", data_type="string")
    def global_resolve() -> str:
        return "global"

    local_ctx = Context()

    @local_ctx.action("resolve", data_type="string")
    def local_resolve() -> str:
        return "local"

    action = Action(name="resolve")
    ctx = EvaluationContext(engine, local_context=local_ctx)
    assert action.execute(ctx) == "local"


def test_action_execute_falls_back_to_engine_context(engine: Engine) -> None:
    @engine.action("shared", data_type="integer")
    def shared() -> int:
        return 42

    action = Action(name="shared")
    ctx = EvaluationContext(engine, local_context=Context())
    assert action.execute(ctx) == 42


def test_action_execute_unknown_raises_key_error(engine: Engine) -> None:
    action = Action(name="missing")
    with pytest.raises(KeyError, match="not registered"):
        action.execute(EvaluationContext(engine))


def test_action_execute_requires_context() -> None:
    with pytest.raises(TypeError):
        Action(name="noop").execute()  # type: ignore[call-arg]


def test_action_execute_resolves_variable_and_literal(engine: Engine) -> None:
    @engine.variable("user_id", data_type="integer")
    def user_id() -> int:
        return 1

    @engine.action("notify", data_type="boolean")
    def notify(user_id: int, status: str, *, channel: str) -> bool:
        return user_id == 1 and status == "sent" and channel == "email"

    action = Action(
        name="notify",
        args=(Variable("user_id"), Literal("sent")),
        kwargs={"channel": Literal("email")},
    )
    assert action.execute(EvaluationContext(engine)) is True


def test_action_execute_resolves_function(engine: Engine) -> None:
    @engine.function("double", data_type="integer")
    def double(value: int) -> int:
        return value * 2

    @engine.action("apply", data_type="integer")
    def apply(value: int) -> int:
        return value

    action = Action(
        name="apply",
        args=(Function(name="double", args=(5,)),),
    )
    assert action.execute(EvaluationContext(engine)) == 10


def test_action_execute_resolves_target(engine: Engine) -> None:
    user = {"id": 7}

    @engine.action("identify", data_type="integer")
    def identify(subject: dict[str, int]) -> int:
        return subject["id"]

    action = Action(name="identify", args=(target(),))
    ctx = EvaluationContext(engine, target=user)
    assert action.execute(ctx) == 7


def test_action_execute_target_without_context_target_raises(engine: Engine) -> None:
    @engine.action("identify", data_type="integer")
    def identify(subject: dict[str, int]) -> int:
        return subject["id"]

    action = Action(name="identify", args=(target(),))
    with pytest.raises(ValueError, match="target\\(\\) requires target="):
        action.execute(EvaluationContext(engine))
