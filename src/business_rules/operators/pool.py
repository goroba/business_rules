"""Operators registry and registration decorators."""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

from business_rules.operators.base import BinaryOperator, Operator, UnaryOperator

__all__ = ["OperatorsPool", "binary", "unary"]

_OperatorT = TypeVar("_OperatorT", bound=Operator)
_UnaryOperatorT = TypeVar("_UnaryOperatorT", bound=UnaryOperator)
_BinaryOperatorT = TypeVar("_BinaryOperatorT", bound=BinaryOperator)


class OperatorsPool:
    _registry: dict[str, type[Operator]] = {}

    @classmethod
    def register(cls, name: str, operator_cls: type[_OperatorT]) -> type[_OperatorT]:
        if not name:
            raise ValueError("Operator name must not be empty")
        if name in cls._registry:
            raise ValueError(f"Operator {name!r} is already registered")
        cls._registry[name] = operator_cls
        return operator_cls

    @classmethod
    def get(cls, name: str) -> type[Operator]:
        try:
            return cls._registry[name]
        except KeyError as exc:
            raise KeyError(f"Operator {name!r} is not registered") from exc

    @classmethod
    def all(cls) -> frozenset[type[Operator]]:
        return frozenset(cls._registry.values())

    @classmethod
    def unary(cls) -> frozenset[type[UnaryOperator]]:
        return frozenset(
            operator_cls
            for operator_cls in cls._registry.values()
            if issubclass(operator_cls, UnaryOperator)
        )

    @classmethod
    def binary(cls) -> frozenset[type[BinaryOperator]]:
        return frozenset(
            operator_cls
            for operator_cls in cls._registry.values()
            if issubclass(operator_cls, BinaryOperator)
        )


def unary(name: str) -> Callable[[type[_UnaryOperatorT]], type[_UnaryOperatorT]]:
    def decorator(operator_cls: type[_UnaryOperatorT]) -> type[_UnaryOperatorT]:
        if not issubclass(operator_cls, UnaryOperator):
            raise TypeError(f"{operator_cls.__name__} must subclass UnaryOperator")
        operator_cls.name = name
        OperatorsPool.register(name, operator_cls)
        return operator_cls

    return decorator


def binary(name: str) -> Callable[[type[_BinaryOperatorT]], type[_BinaryOperatorT]]:
    def decorator(operator_cls: type[_BinaryOperatorT]) -> type[_BinaryOperatorT]:
        if not issubclass(operator_cls, BinaryOperator):
            raise TypeError(f"{operator_cls.__name__} must subclass BinaryOperator")
        operator_cls.name = name
        OperatorsPool.register(name, operator_cls)
        return operator_cls

    return decorator
