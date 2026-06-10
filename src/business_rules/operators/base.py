"""Operator base classes."""

from __future__ import annotations

from abc import ABC
from typing import ClassVar

__all__ = ["BinaryOperator", "Operator", "UnaryOperator"]


class Operator(ABC):
    name: ClassVar[str]


class UnaryOperator(Operator):
    pass


class BinaryOperator(Operator):
    pass
