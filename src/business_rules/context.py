"""Context registry for variables, actions, and functions."""

from __future__ import annotations

import inspect
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, TypeVar

from business_rules.data_types.pool import DataTypesPool

__all__ = [
    "Context",
    "GlobalContext",
    "RegisteredEntry",
    "action",
    "function",
    "get_global_context",
    "variable",
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


class Context:
    def __init__(self) -> None:
        self._variables: dict[str, RegisteredEntry] = {}
        self._actions: dict[str, RegisteredEntry] = {}
        self._functions: dict[str, RegisteredEntry] = {}

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
        if not name:
            raise ValueError("Name must not be empty")
        DataTypesPool.get(data_type)
        if name in registry:
            raise ValueError(f"{kind} {name!r} is already registered")
        registry[name] = RegisteredEntry(name=name, data_type=data_type, func=func)

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

    def _get_with_fallback(
        self,
        registry: dict[str, RegisteredEntry],
        global_registry: dict[str, RegisteredEntry],
        kind: str,
        name: str,
    ) -> RegisteredEntry:
        try:
            return registry[name]
        except KeyError as exc:
            try:
                return global_registry[name]
            except KeyError:
                raise KeyError(f"{kind} {name!r} is not registered") from exc

    def get_variable(self, name: str) -> RegisteredEntry:
        global_ctx = get_global_context()
        return self._get_with_fallback(
            self._variables, global_ctx._variables, "Variable", name
        )

    def get_action(self, name: str) -> RegisteredEntry:
        global_ctx = get_global_context()
        return self._get_with_fallback(
            self._actions, global_ctx._actions, "Action", name
        )

    def get_function(self, name: str) -> RegisteredEntry:
        global_ctx = get_global_context()
        return self._get_with_fallback(
            self._functions, global_ctx._functions, "Function", name
        )


class GlobalContext(Context):
    _instance: GlobalContext | None = None

    def __new__(cls) -> GlobalContext:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return
        super().__init__()
        self._initialized = True

    def get_variable(self, name: str) -> RegisteredEntry:
        try:
            return self._variables[name]
        except KeyError as exc:
            raise KeyError(f"Variable {name!r} is not registered") from exc

    def get_action(self, name: str) -> RegisteredEntry:
        try:
            return self._actions[name]
        except KeyError as exc:
            raise KeyError(f"Action {name!r} is not registered") from exc

    def get_function(self, name: str) -> RegisteredEntry:
        try:
            return self._functions[name]
        except KeyError as exc:
            raise KeyError(f"Function {name!r} is not registered") from exc


def get_global_context() -> GlobalContext:
    return GlobalContext()


def _make_registration_decorator(
    register: Callable[[Context, str, Callable[..., Any], str], None],
) -> Callable[..., Callable[[_CallableT], _CallableT]]:
    def decorator_factory(
        name: str | None = None,
        *,
        context: Context | None = None,
        data_type: str,
    ) -> Callable[[_CallableT], _CallableT]:
        def decorator(obj: _CallableT) -> _CallableT:
            _validate_callable_target(obj)
            resolved_name = _resolve_name(name, obj)
            target = context or get_global_context()
            register(target, resolved_name, obj, data_type)
            return obj

        return decorator

    return decorator_factory


variable = _make_registration_decorator(
    lambda ctx, name, func, data_type: ctx.register_variable(name, func, data_type)
)
action = _make_registration_decorator(
    lambda ctx, name, func, data_type: ctx.register_action(name, func, data_type)
)
function = _make_registration_decorator(
    lambda ctx, name, func, data_type: ctx.register_function(name, func, data_type)
)
