"""Executable base class and concrete call types for business rules."""

from __future__ import annotations

from abc import ABC
from dataclasses import dataclass, field
from typing import Any

from business_rules.evaluation import EvaluationContext
from business_rules.target import Target

__all__ = ["Executable", "Action"]


@dataclass
class Executable(ABC):
    name: str
    args: tuple[Any, ...] = ()
    kwargs: dict[str, Any] = field(default_factory=dict)


@dataclass
class Action(Executable):
    def _resolve_action_value(self, value: Any, ctx: EvaluationContext) -> Any:
        if isinstance(value, Target):
            return value.evaluate(ctx)
        from business_rules.operand import Operand

        if isinstance(value, Operand):
            return value.evaluate(ctx)
        return value

    def execute(self, ctx: EvaluationContext) -> Any:
        entry = ctx.engine.resolve_action(self.name, ctx.local_context)
        args = tuple(self._resolve_action_value(arg, ctx) for arg in self.args)
        kwargs = {
            key: self._resolve_action_value(value, ctx)
            for key, value in self.kwargs.items()
        }
        return entry.func(*args, **kwargs)
