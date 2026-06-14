import pytest

from business_rules.builder import get_builder, target, variable
from business_rules.engine import Engine
from business_rules.evaluation import EvaluationContext
from business_rules.target import Target
from business_rules.target import target as target_factory


@pytest.fixture
def engine() -> Engine:
    return Engine()


def test_target_factory_returns_target() -> None:
    assert isinstance(target_factory(), Target)


def test_target_evaluate_returns_context_target(engine: Engine) -> None:
    user = {"id": 1}
    ctx = EvaluationContext(engine, target=user)
    assert target_factory().evaluate(ctx) is user


def test_target_evaluate_without_target_raises(engine: Engine) -> None:
    ctx = EvaluationContext(engine)
    with pytest.raises(ValueError, match="target\\(\\) requires target="):
        target_factory().evaluate(ctx)


def test_engine_run_passes_target_to_action(engine: Engine) -> None:
    received: list[object] = []

    @engine.action("grant_access", data_type="boolean")
    def grant_access(user: object) -> bool:
        received.append(user)
        return True

    @engine.variable("age", data_type="integer")
    def age() -> int:
        return 21

    rule = (
        get_builder()
        .having()
        .all()
        .binary(variable("age"), "gte", "18")
        .end()
        .on_success()
        .action("grant_access", args=(target(),))
        .end()
        .build()
    )

    user = {"id": 42, "name": "Ada"}
    assert engine.run(rule, target=user) is True
    assert received == [user]
