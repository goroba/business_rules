"""Translator base class for business rule persistence."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from business_rules.business_rule import BusinessRule

__all__ = ["Translator"]

T = TypeVar("T")


class Translator(ABC, Generic[T]):
    @abstractmethod
    def load(self, source: T) -> BusinessRule: ...

    @abstractmethod
    def dump(self, business_rule: BusinessRule) -> T: ...
