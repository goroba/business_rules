"""Operands for rule expressions."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from business_rules.evaluation import EvaluationContext
from business_rules.executable import Executable

__all__ = ["DataTypeAwareOperand", "Function", "Literal", "Operand", "Variable"]


class Operand(ABC):
    @abstractmethod
    def evaluate(self, ctx: EvaluationContext) -> Any: ...


class DataTypeAwareOperand(Operand, ABC):
    @abstractmethod
    def data_type(self, ctx: EvaluationContext) -> str: ...


@dataclass
class Variable(DataTypeAwareOperand):
    name: str

    def evaluate(self, ctx: EvaluationContext) -> Any:
        entry = ctx.engine.resolve_variable(self.name, ctx.local_context)
        return entry.func()

    def data_type(self, ctx: EvaluationContext) -> str:
        return ctx.engine.resolve_variable(self.name, ctx.local_context).data_type


@dataclass
class Literal(Operand):
    value: str

    def evaluate(self, ctx: EvaluationContext) -> Any:
        return self.value


@dataclass
class Function(DataTypeAwareOperand, Executable):
    def evaluate(self, ctx: EvaluationContext) -> Any:
        entry = ctx.engine.resolve_function(self.name, ctx.local_context)
        return entry.func(*self.args, **self.kwargs)

    def data_type(self, ctx: EvaluationContext) -> str:
        return ctx.engine.resolve_function(self.name, ctx.local_context).data_type
