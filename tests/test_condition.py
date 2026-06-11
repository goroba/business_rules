from dataclasses import dataclass

import pytest

from business_rules.condition import (
    BinaryCondition,
    Condition,
    Conjunction,
    Disjunction,
    IterableCondition,
    NegatedCondition,
    UnaryCondition,
)
from business_rules.engine import Engine
from business_rules.evaluation import EvaluationContext
from business_rules.operand import Function, Literal, Variable
from business_rules.operators import (
    EqOperator,
    GtOperator,
    IsNotNullOperator,
    IsNullOperator,
)

@dataclass
class TrueCondition(Condition):
    def evaluate(self, ctx: EvaluationContext) -> bool:
        return True


@dataclass
class FalseCondition(Condition):
    def evaluate(self, ctx: EvaluationContext) -> bool:
        return False


@pytest.fixture
def engine() -> Engine:
    return Engine()


@pytest.fixture
def ctx(engine: Engine) -> EvaluationContext:
    return EvaluationContext(engine)


def test_condition() -> None:
    assert TrueCondition() == TrueCondition()


def test_condition_is_abstract() -> None:
    with pytest.raises(TypeError):
        Condition()  # type: ignore[abstract]


def test_unary_condition() -> None:
    operand = Variable("field")
    condition = UnaryCondition(operand=operand, operator=IsNullOperator)
    assert condition.operand == operand
    assert condition.operator is IsNullOperator


def test_binary_condition() -> None:
    left = Variable("age")
    right = Literal("18")
    condition = BinaryCondition(left=left, operator=GtOperator, right=right)
    assert condition.left == left
    assert condition.operator is GtOperator
    assert condition.right == right


def test_iterable_condition() -> None:
    with pytest.raises(NotImplementedError):
        iter(IterableCondition())


def test_conjunction() -> None:
    first = BinaryCondition(
        left=Variable("a"),
        operator=EqOperator,
        right=Literal("1"),
    )
    second = BinaryCondition(
        left=Variable("b"),
        operator=EqOperator,
        right=Literal("2"),
    )
    condition = Conjunction(all=(first, second))
    assert condition.all == (first, second)
    assert list(condition) == [first, second]


def test_disjunction() -> None:
    first = BinaryCondition(
        left=Variable("a"),
        operator=EqOperator,
        right=Literal("1"),
    )
    second = BinaryCondition(
        left=Variable("b"),
        operator=EqOperator,
        right=Literal("2"),
    )
    condition = Disjunction(any=(first, second))
    assert condition.any == (first, second)
    assert list(condition) == [first, second]


def test_negated_condition() -> None:
    inner = BinaryCondition(
        left=Variable("age"),
        operator=GtOperator,
        right=Literal("18"),
    )
    condition = NegatedCondition(negative=inner)
    assert condition.negative == inner


def test_unary_condition_evaluate_literal_operand_raises(ctx: EvaluationContext) -> None:
    condition = UnaryCondition(
        operand=Literal("field"),  # type: ignore[arg-type]
        operator=IsNullOperator,
    )
    with pytest.raises(AttributeError):
        condition.evaluate(ctx)


def test_binary_condition_evaluate_variable_gt_value(
    engine: Engine, ctx: EvaluationContext
) -> None:
    @engine.variable("age", data_type="integer")
    def age() -> int:
        return 25

    condition = BinaryCondition(
        left=Variable("age"),
        operator=GtOperator,
        right=Literal("18"),
    )
    assert condition.evaluate(ctx) is True


def test_binary_condition_evaluate_value_gt_variable(
    engine: Engine, ctx: EvaluationContext
) -> None:
    @engine.variable("age", data_type="integer")
    def age() -> int:
        return 25

    condition = BinaryCondition(
        left=Literal("18"),
        operator=GtOperator,
        right=Variable("age"),
    )
    assert condition.evaluate(ctx) is False


def test_binary_condition_evaluate_two_variables_same_type(
    engine: Engine, ctx: EvaluationContext
) -> None:
    @engine.variable("a", data_type="integer")
    def a() -> int:
        return 10

    @engine.variable("b", data_type="integer")
    def b() -> int:
        return 10

    condition = BinaryCondition(
        left=Variable("a"),
        operator=EqOperator,
        right=Variable("b"),
    )
    assert condition.evaluate(ctx) is True


def test_binary_condition_evaluate_two_variables_mismatched_types_raises(
    engine: Engine, ctx: EvaluationContext
) -> None:
    @engine.variable("count", data_type="integer")
    def count() -> int:
        return 1

    @engine.variable("label", data_type="string")
    def label() -> str:
        return "1"

    condition = BinaryCondition(
        left=Variable("count"),
        operator=EqOperator,
        right=Variable("label"),
    )
    with pytest.raises(ValueError, match="Operands data types must match"):
        condition.evaluate(ctx)


def test_binary_condition_evaluate_two_literals_raises(ctx: EvaluationContext) -> None:
    condition = BinaryCondition(
        left=Literal("5"),
        operator=EqOperator,
        right=Literal("10"),
    )
    with pytest.raises(TypeError, match="DataTypeAwareOperand"):
        condition.evaluate(ctx)


def test_iterable_condition_evaluate_raises(ctx: EvaluationContext) -> None:
    with pytest.raises(NotImplementedError):
        IterableCondition().evaluate(ctx)


def test_conjunction_evaluate(ctx: EvaluationContext) -> None:
    assert Conjunction(all=(TrueCondition(), TrueCondition())).evaluate(ctx) is True
    assert Conjunction(all=(TrueCondition(), FalseCondition())).evaluate(ctx) is False


def test_disjunction_evaluate(ctx: EvaluationContext) -> None:
    assert Disjunction(any=(FalseCondition(), TrueCondition())).evaluate(ctx) is True
    assert Disjunction(any=(FalseCondition(), FalseCondition())).evaluate(ctx) is False


def test_negated_condition_evaluate(ctx: EvaluationContext) -> None:
    assert NegatedCondition(negative=TrueCondition()).evaluate(ctx) is False
    assert NegatedCondition(negative=FalseCondition()).evaluate(ctx) is True


def test_negated_condition_evaluate_binary(
    engine: Engine, ctx: EvaluationContext
) -> None:
    @engine.variable("age", data_type="integer")
    def age() -> int:
        return 25

    passing = BinaryCondition(
        left=Variable("age"),
        operator=GtOperator,
        right=Literal("18"),
    )
    assert NegatedCondition(negative=passing).evaluate(ctx) is False

    failing = BinaryCondition(
        left=Variable("age"),
        operator=GtOperator,
        right=Literal("30"),
    )
    assert NegatedCondition(negative=failing).evaluate(ctx) is True


def test_unary_condition_evaluate_is_null_on_variable(
    engine: Engine, ctx: EvaluationContext
) -> None:
    @engine.variable("optional_field", data_type="string")
    def optional_field() -> str | None:
        return None

    condition = UnaryCondition(
        operand=Variable("optional_field"),
        operator=IsNullOperator,
    )
    assert condition.evaluate(ctx) is True


def test_unary_condition_evaluate_is_not_null_on_variable(
    engine: Engine, ctx: EvaluationContext
) -> None:
    @engine.variable("name", data_type="string")
    def name() -> str:
        return "alice"

    condition = UnaryCondition(
        operand=Variable("name"),
        operator=IsNotNullOperator,
    )
    assert condition.evaluate(ctx) is True


def test_unary_condition_evaluate_is_null_on_function(
    engine: Engine, ctx: EvaluationContext
) -> None:
    @engine.function("lookup", data_type="integer")
    def lookup() -> int | None:
        return None

    condition = UnaryCondition(
        operand=Function(name="lookup"),
        operator=IsNullOperator,
    )
    assert condition.evaluate(ctx) is True


def test_unary_condition_evaluate_uses_local_context(
    engine: Engine,
) -> None:
    from business_rules.context import Context

    @engine.variable("tenant_id", data_type="string")
    def global_tenant_id() -> str | None:
        return "global"

    local_ctx = Context()

    @local_ctx.variable("tenant_id", data_type="string")
    def local_tenant_id() -> str | None:
        return None

    condition = UnaryCondition(
        operand=Variable("tenant_id"),
        operator=IsNullOperator,
    )
    ctx = EvaluationContext(engine, local_context=local_ctx)
    assert condition.evaluate(ctx) is True
