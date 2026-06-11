"""Operands for rule expressions."""

from __future__ import annotations

from abc import ABC
from dataclasses import dataclass

from business_rules.verifiable import Verifiable

__all__ = ["Operand", "Value", "Variable"]


class Operand(Verifiable, ABC):
    def verify(self) -> bool:
        raise NotImplementedError


@dataclass
class Variable(Operand):
    name: str


@dataclass
class Value(Operand):
    value: str
