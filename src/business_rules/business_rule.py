"""Business rules."""

from __future__ import annotations

from dataclasses import dataclass

from business_rules.executable import Action
from business_rules.condition import Condition
from business_rules.evaluation import EvaluationContext

__all__ = ["BusinessRule"]


@dataclass
class BusinessRule:
    having: Condition
    on_success: list[Action] | None = None
    on_failure: list[Action] | None = None
    on_finally: list[Action] | None = None

    def evaluate(self, ctx: EvaluationContext) -> bool:
        return self.having.evaluate(ctx)
