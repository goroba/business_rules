"""Conditions for rule expressions."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass

from business_rules.data_types.pool import DataTypesPool
from business_rules.evaluation import EvaluationContext
from business_rules.operand import DataTypeAwareOperand, Operand
from business_rules.operators.base import BinaryOperator, UnaryOperator

__all__ = [
    "BinaryCondition",
    "Condition",
    "Conjunction",
    "Disjunction",
    "IterableCondition",
    "NegatedCondition",
    "UnaryCondition",
]


@dataclass
class Condition(ABC):
    @abstractmethod
    def evaluate(self, ctx: EvaluationContext) -> bool: ...


@dataclass
class UnaryCondition(Condition):
    operand: DataTypeAwareOperand
    operator: type[UnaryOperator]

    def evaluate(self, ctx: EvaluationContext) -> bool:
        value = self.operand.evaluate(ctx)
        data_type = DataTypesPool.get(self.operand.data_type(ctx))()

        return data_type.apply(self.operator.name, value)


@dataclass
class NegatedCondition(Condition):
    negative: Condition

    def evaluate(self, ctx: EvaluationContext) -> bool:
        return not self.negative.evaluate(ctx)


@dataclass
class BinaryCondition(Condition):
    left: Operand
    operator: type[BinaryOperator]
    right: Operand

    def evaluate(self, ctx: EvaluationContext) -> bool:
        left_aware = isinstance(self.left, DataTypeAwareOperand)
        right_aware = isinstance(self.right, DataTypeAwareOperand)
        if not left_aware and not right_aware:
            raise TypeError("At least one operand must be a DataTypeAwareOperand")

        if left_aware and right_aware:
            data_type_name = self.left.data_type(ctx)
            if self.right.data_type(ctx) != data_type_name:
                raise ValueError("Operands data types must match.")
        elif left_aware:
            data_type_name = self.left.data_type(ctx)
        else:
            data_type_name = self.right.data_type(ctx)

        data_type = DataTypesPool.get(data_type_name)()
        left_value = data_type.cast(self.left.evaluate(ctx))
        right_value = data_type.cast(self.right.evaluate(ctx))

        return data_type.apply(self.operator.name, left_value, right_value)


@dataclass
class IterableCondition(Condition):
    def __iter__(self) -> Iterator[Condition]:
        raise NotImplementedError

    def evaluate(self, ctx: EvaluationContext) -> bool:
        raise NotImplementedError


@dataclass
class Conjunction(IterableCondition):
    all: tuple[Condition, ...]

    def __iter__(self) -> Iterator[Condition]:
        return iter(self.all)

    def evaluate(self, ctx: EvaluationContext) -> bool:
        return all(condition.evaluate(ctx) for condition in self.all)


@dataclass
class Disjunction(IterableCondition):
    any: tuple[Condition, ...]

    def __iter__(self) -> Iterator[Condition]:
        return iter(self.any)

    def evaluate(self, ctx: EvaluationContext) -> bool:
        return any(condition.evaluate(ctx) for condition in self.any)
