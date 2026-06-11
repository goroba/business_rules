"""Executable base class and concrete call types for business rules."""

from __future__ import annotations

from abc import ABC
from dataclasses import dataclass, field
from typing import Any

from business_rules.evaluation import EvaluationContext

__all__ = ["Executable", "Action"]


@dataclass
class Executable(ABC):
    name: str
    args: tuple[Any, ...] = ()
    kwargs: dict[str, Any] = field(default_factory=dict)


@dataclass
class Action(Executable):
    def execute(self, ctx: EvaluationContext) -> Any:
        entry = ctx.engine.resolve_action(self.name, ctx.local_context)
        return entry.func(*self.args, **self.kwargs)
