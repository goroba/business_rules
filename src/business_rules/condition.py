"""Conditions for rule expressions."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

from business_rules.operand import Operand
from business_rules.operators.base import BinaryOperator, UnaryOperator

__all__ = [
    "BinaryCondition",
    "Condition",
    "Conjunction",
    "Disjunction",
    "IterableCondition",
    "Negation",
    "UnaryCondition",
]


@dataclass
class Condition:
    def verify(self) -> bool:
        raise NotImplementedError


@dataclass
class UnaryCondition(Condition):
    operand: Operand
    operator: type[UnaryOperator]

    def verify(self) -> bool:
        raise NotImplementedError


@dataclass
class Negation(UnaryCondition):
    operand: Operand

    def verify(self) -> bool:
        return not self.operand.value.verify()


@dataclass
class BinaryCondition(Condition):
    left: Operand
    operator: type[BinaryOperator]
    right: Operand

    def verify(self) -> bool: ...  # type: ignore[empty-body]


@dataclass
class IterableCondition(Condition):
    def __iter__(self) -> Iterator[Condition]:
        raise NotImplementedError

    def verify(self) -> bool:
        raise NotImplementedError


@dataclass
class Conjunction(IterableCondition):
    all: tuple[Condition, ...]

    def __iter__(self) -> Iterator[Condition]:
        return iter(self.all)

    def verify(self) -> bool:
        return all(condition.verify() for condition in self.all)


@dataclass
class Disjunction(IterableCondition):
    any: tuple[Condition, ...]

    def __iter__(self) -> Iterator[Condition]:
        return iter(self.any)

    def verify(self) -> bool:
        return any(condition.verify() for condition in self.any)
