"""Context registry for variables, actions, and functions."""

from __future__ import annotations

import inspect
from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Literal, Self, TypeVar

_EntryKind = Literal["variable", "action", "function"]

from business_rules.data_types.pool import DataTypesPool
from business_rules.name_normalizers import NameNormalizer, SnakeCaseNameNormalizer

__all__ = [
    "Context",
    "RegisteredEntry",
]

_CallableT = TypeVar("_CallableT", bound=Callable[..., Any])


@dataclass(frozen=True)
class RegisteredEntry:
    name: str
    data_type: str
    func: Callable[..., Any]


def _validate_callable_target(obj: object) -> None:
    if not callable(obj):
        raise TypeError(f"{obj!r} must be callable")
    if inspect.isclass(obj) and "__call__" not in obj.__dict__:
        raise TypeError(f"{obj.__name__} must define __call__")


def _resolve_name(name: str | None, obj: Callable[..., Any]) -> str:
    resolved_name = name if name is not None else obj.__name__
    if not resolved_name:
        raise ValueError("Name must not be empty")
    return resolved_name


def _make_registration_decorator(
    register: Callable[[str, Callable[..., Any], str], None],
) -> Callable[..., Callable[[_CallableT], _CallableT]]:
    def decorator_factory(
        name: str | None = None,
        *,
        data_type: str,
    ) -> Callable[[_CallableT], _CallableT]:
        def decorator(obj: _CallableT) -> _CallableT:
            _validate_callable_target(obj)
            resolved_name = _resolve_name(name, obj)
            register(resolved_name, obj, data_type)
            return obj

        return decorator

    return decorator_factory


class Context:
    def __init__(self, name_normalizer: NameNormalizer | None = None) -> None:
        self._name_normalizer = name_normalizer or SnakeCaseNameNormalizer()
        self._nested: Context | None = None
        self._variables: dict[str, RegisteredEntry] = {}
        self._actions: dict[str, RegisteredEntry] = {}
        self._functions: dict[str, RegisteredEntry] = {}

    def nests(self, inner: Context) -> Self:
        self._validate_nested(inner)
        self._nested = inner
        return self

    def _clear_nested(self) -> None:
        self._nested = None

    def _iter_nested(self) -> Iterator[Context]:
        current: Context | None = self
        while current is not None:
            yield current
            current = current._nested

    def _validate_nested(self, inner: Context) -> None:
        seen = {id(self)}
        current: Context | None = inner
        while current is not None:
            if id(current) in seen:
                raise ValueError("Circular nested context chain")
            seen.add(id(current))
            current = current._nested

    def _lookup_entry(self, kind: _EntryKind, normalized_name: str) -> RegisteredEntry:
        if kind == "variable":
            registry = self._variables
        elif kind == "action":
            registry = self._actions
        else:
            registry = self._functions
        return registry[normalized_name]

    def _normalize_entry_name(self, name: str) -> str:
        return self._name_normalizer.normalize(name)

    @property
    def variables(self) -> Mapping[str, RegisteredEntry]:
        return MappingProxyType(self._variables)

    @property
    def actions(self) -> Mapping[str, RegisteredEntry]:
        return MappingProxyType(self._actions)

    @property
    def functions(self) -> Mapping[str, RegisteredEntry]:
        return MappingProxyType(self._functions)

    def _register(
        self,
        registry: dict[str, RegisteredEntry],
        kind: str,
        name: str,
        func: Callable[..., Any],
        data_type: str,
    ) -> None:
        normalized_name = self._normalize_entry_name(name)
        DataTypesPool.get(data_type)
        if normalized_name in registry:
            raise ValueError(f"{kind} {normalized_name!r} is already registered")
        registry[normalized_name] = RegisteredEntry(
            name=normalized_name, data_type=data_type, func=func
        )

    def register_variable(
        self,
        name: str,
        func: Callable[..., Any],
        data_type: str,
    ) -> None:
        _validate_callable_target(func)
        self._register(self._variables, "Variable", name, func, data_type)

    def register_action(
        self,
        name: str,
        func: Callable[..., Any],
        data_type: str,
    ) -> None:
        _validate_callable_target(func)
        self._register(self._actions, "Action", name, func, data_type)

    def register_function(
        self,
        name: str,
        func: Callable[..., Any],
        data_type: str,
    ) -> None:
        _validate_callable_target(func)
        self._register(self._functions, "Function", name, func, data_type)

    def get_variable(self, name: str) -> RegisteredEntry:
        normalized_name = self._normalize_entry_name(name)
        try:
            return self._variables[normalized_name]
        except KeyError as exc:
            raise KeyError(f"Variable {name!r} is not registered") from exc

    def get_action(self, name: str) -> RegisteredEntry:
        normalized_name = self._normalize_entry_name(name)
        try:
            return self._actions[normalized_name]
        except KeyError as exc:
            raise KeyError(f"Action {name!r} is not registered") from exc

    def get_function(self, name: str) -> RegisteredEntry:
        normalized_name = self._normalize_entry_name(name)
        try:
            return self._functions[normalized_name]
        except KeyError as exc:
            raise KeyError(f"Function {name!r} is not registered") from exc

    def variable(
        self, name: str | None = None, *, data_type: str
    ) -> Callable[[_CallableT], _CallableT]:
        return _make_registration_decorator(self.register_variable)(
            name, data_type=data_type
        )

    def action(
        self, name: str | None = None, *, data_type: str
    ) -> Callable[[_CallableT], _CallableT]:
        return _make_registration_decorator(self.register_action)(
            name, data_type=data_type
        )

    def function(
        self, name: str | None = None, *, data_type: str
    ) -> Callable[[_CallableT], _CallableT]:
        return _make_registration_decorator(self.register_function)(
            name, data_type=data_type
        )
