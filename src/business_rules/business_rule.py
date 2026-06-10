"""Business rules."""

from __future__ import annotations

from dataclasses import dataclass

from business_rules.action import Action
from business_rules.condition import Condition

__all__ = ["BusinessRule"]


@dataclass
class BusinessRule:
    condition: Condition
    on_success: list[Action] | None = None
    on_failure: list[Action] | None = None
    on_finally: list[Action] | None = None

    def __bool__(self) -> bool:
        return self.condition.verify()
