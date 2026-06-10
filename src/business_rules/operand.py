"""Operands for rule expressions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

__all__ = ["Operand"]


@dataclass
class Operand:
    value: Any
