"""Decorator for binding DataType methods to registered operators."""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

IMPLEMENTS_OPERATOR_NAME = "_implements_operator_name"

__all__ = ["IMPLEMENTS_OPERATOR_NAME", "implements"]

_F = TypeVar("_F", bound=Callable[..., bool])


def implements(name: str) -> Callable[[_F], _F]:
    def decorator(method: _F) -> _F:
        setattr(method, IMPLEMENTS_OPERATOR_NAME, name)
        return method

    return decorator
