"""Base data types for business rules."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any, ClassVar, Generic, TypeVar

import business_rules.operators  # noqa: F401 — register built-in operators
from business_rules.operators import OperatorsPool
from business_rules.operators.implements import IMPLEMENTS_OPERATOR_NAME

T = TypeVar("T")

__all__ = ["DataType"]


class DataType(Generic[T], ABC):
    name: ClassVar[str]
    operators: ClassVar[frozenset[str]] = frozenset()
    _implementations: ClassVar[dict[str, Callable[..., bool]]] = {}

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        implementations: dict[str, Callable[..., bool]] = {}
        operator_names: list[str] = []
        for member in cls.__dict__.values():
            if not callable(member):
                continue
            name = getattr(member, IMPLEMENTS_OPERATOR_NAME, None)
            if name is None:
                continue
            if not isinstance(name, str):
                raise TypeError("implements operator name must be a string")
            try:
                OperatorsPool.get(name)
            except KeyError as exc:
                raise ValueError(
                    f"Operator {name!r} is not registered in OperatorsPool"
                ) from exc
            implementations[name] = member
            operator_names.append(name)
        cls._implementations = implementations
        cls.operators = frozenset(operator_names)

    def cast(self, value: str | T) -> T:
        if isinstance(value, str):
            return self.do_cast(value)
        return value

    @abstractmethod
    def do_cast(self, value: str) -> T: ...

    @abstractmethod
    def __str__(self, value: T) -> str: ...  # type: ignore[override]

    def __bool__(self, value: T) -> bool:  # type: ignore[override]
        return bool(value)

    def apply(self, name: str, *args: Any) -> bool:
        try:
            implementation = self._implementations[name]
        except KeyError as exc:
            raise NotImplementedError(
                f"{type(self).__name__} does not implement operator {name!r}"
            ) from exc
        return implementation(self, *args)
