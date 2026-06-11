"""Verifiable base class for rule expressions."""

from __future__ import annotations

from abc import ABC, abstractmethod

__all__ = ["Verifiable"]


class Verifiable(ABC):
    @abstractmethod
    def verify(self) -> bool: ...
