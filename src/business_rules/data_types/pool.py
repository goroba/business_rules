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


def _register_guesser(
    data_type_cls: type[DataType[Any]],
    *,
    guesser_top: bool,
    guesser_bottom: bool,
    guesser_before: str | None,
    guesser_after: str | None,
) -> None:
    placement_count = sum(
        (
            guesser_top,
            guesser_bottom,
            guesser_before is not None,
            guesser_after is not None,
        )
    )
    if placement_count == 0:
        return
    if placement_count > 1:
        raise ValueError("Only one guesser placement option may be set")

    from business_rules.data_types.guesser_pool import DataTypeGuesserPool

    if guesser_top:
        DataTypeGuesserPool.top(data_type_cls)
        return
    if guesser_bottom:
        DataTypeGuesserPool.bottom(data_type_cls)
        return
    if guesser_before is not None:
        try:
            reference = DataTypesPool.get(guesser_before)
        except KeyError as exc:
            raise ValueError(
                f"Data type {guesser_before!r} is not registered"
            ) from exc
        if reference not in DataTypeGuesserPool.ordered():
            raise ValueError(
                f"Data type {guesser_before!r} is not registered in DataTypeGuesserPool"
            )
        DataTypeGuesserPool.before(data_type_cls, reference)
        return
    assert guesser_after is not None
    try:
        reference = DataTypesPool.get(guesser_after)
    except KeyError as exc:
        raise ValueError(f"Data type {guesser_after!r} is not registered") from exc
    if reference not in DataTypeGuesserPool.ordered():
        raise ValueError(
            f"Data type {guesser_after!r} is not registered in DataTypeGuesserPool"
        )
    DataTypeGuesserPool.after(data_type_cls, reference)


def data_type(
    name: str,
    *,
    guesser_top: bool = False,
    guesser_bottom: bool = False,
    guesser_before: str | None = None,
    guesser_after: str | None = None,
) -> Callable[[type[_DataTypeT]], type[_DataTypeT]]:
    def decorator(data_type_cls: type[_DataTypeT]) -> type[_DataTypeT]:
        if not issubclass(data_type_cls, DataType):
            raise TypeError(f"{data_type_cls.__name__} must subclass DataType")
        data_type_cls.name = name
        DataTypesPool.register(name, data_type_cls)
        _register_guesser(
            data_type_cls,
            guesser_top=guesser_top,
            guesser_bottom=guesser_bottom,
            guesser_before=guesser_before,
            guesser_after=guesser_after,
        )
        return data_type_cls

    return decorator
