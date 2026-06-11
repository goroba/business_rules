"""Executable base class and concrete call types for business rules."""

from __future__ import annotations

from abc import ABC
from dataclasses import dataclass, field

from business_rules.operand import Operand

__all__ = ["Executable", "Action", "Function"]


@dataclass
class Executable(ABC):
    name: str
    args: tuple[Operand, ...] = ()
    kwargs: dict[str, Operand] = field(default_factory=dict)


@dataclass
class Action(Executable):
    pass


@dataclass
class Function(Executable):
    pass
