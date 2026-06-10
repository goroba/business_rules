"""Data types registry and registration decorator."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar

from business_rules.data_types.base import DataType

__all__ = ["DataTypesPool", "data_type"]

_DataTypeT = TypeVar("_DataTypeT", bound=DataType[Any])


class DataTypesPool:
    _registry: dict[str, type[DataType[Any]]] = {}

    @classmethod
    def register(cls, name: str, data_type_cls: type[_DataTypeT]) -> type[_DataTypeT]:
        if not name:
            raise ValueError("Data type name must not be empty")
        if name in cls._registry:
            raise ValueError(f"Data type {name!r} is already registered")
        cls._registry[name] = data_type_cls
        return data_type_cls

    @classmethod
    def get(cls, name: str) -> type[DataType[Any]]:
        try:
            return cls._registry[name]
        except KeyError as exc:
            raise KeyError(f"Data type {name!r} is not registered") from exc

    @classmethod
    def all(cls) -> frozenset[type[DataType[Any]]]:
        return frozenset(cls._registry.values())


def data_type(name: str) -> Callable[[type[_DataTypeT]], type[_DataTypeT]]:
    def decorator(data_type_cls: type[_DataTypeT]) -> type[_DataTypeT]:
        if not issubclass(data_type_cls, DataType):
            raise TypeError(f"{data_type_cls.__name__} must subclass DataType")
        data_type_cls.name = name
        DataTypesPool.register(name, data_type_cls)
        return data_type_cls

    return decorator
