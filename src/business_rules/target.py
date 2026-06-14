"""Run-time target reference for action invocation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from business_rules.evaluation import EvaluationContext

__all__ = ["Target", "target"]


@dataclass(frozen=True)
class Target:
    def evaluate(self, ctx: EvaluationContext) -> Any:
        if ctx.target is None:
            raise ValueError(
                "target() requires target=... on engine.run()"
            )
        return ctx.target


def target() -> Target:
    return Target()
