"""Name normalizer base class."""

from __future__ import annotations

from abc import ABC, abstractmethod

__all__ = ["NameNormalizer"]


class NameNormalizer(ABC):
    @abstractmethod
    def normalize(self, name: str) -> str: ...
