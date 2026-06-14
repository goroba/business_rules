"""Evaluation context for rule expression execution."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from business_rules.context import Context

if TYPE_CHECKING:
    from business_rules.engine import Engine

__all__ = ["EvaluationContext"]


@dataclass(frozen=True)
class EvaluationContext:
    engine: Engine
    local_context: Context | None = None
    target: Any = None
