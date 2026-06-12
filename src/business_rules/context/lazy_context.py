"""Lazy context that proxies a plain object instance."""

from __future__ import annotations

import datetime
import decimal
import types
from collections.abc import Callable, Mapping
from typing import Any, Literal, Union, get_args, get_origin, get_type_hints

from business_rules.context.base import Context, RegisteredEntry
from business_rules.data_types.pool import DataTypesPool
from business_rules.name_normalizers import NameNormalizer

__all__ = ["LazyContext"]

_EntryKind = Literal["variable", "action", "function"]

_PYTHON_TYPE_TO_DATA_TYPE: dict[type[Any], str] = {
    str: "string",
    int: "integer",
    bool: "boolean",
    decimal.Decimal: "decimal",
    datetime.date: "date",
    datetime.datetime: "datetime",
}


def _unwrap_optional(annotation: Any) -> Any:
    origin = get_origin(annotation)
    if origin is Union or isinstance(annotation, types.UnionType):
        args = [arg for arg in get_args(annotation) if arg is not type(None)]
        if len(args) == 1:
            return args[0]
    return annotation


def _python_type_to_data_type(annotation: Any) -> str:
    annotation = _unwrap_optional(annotation)
    try:
        data_type = _PYTHON_TYPE_TO_DATA_TYPE[annotation]
    except KeyError as exc:
        raise ValueError(f"Unsupported type annotation: {annotation!r}") from exc
    DataTypesPool.get(data_type)
    return data_type


class _LazyRegistry(dict[str, RegisteredEntry]):
    def __init__(self, lazy_context: LazyContext, kind: _EntryKind) -> None:
        super().__init__()
        self._lazy_context = lazy_context
        self._kind = kind

    def __missing__(self, normalized_name: str) -> RegisteredEntry:
        entry = self._lazy_context._resolve_from_target(normalized_name, self._kind)
        self[normalized_name] = entry
        return entry


class LazyContext(Context):
    def __init__(
        self,
        target: object,
        *,
        data_types: Mapping[str, str] | None = None,
        name_normalizer: NameNormalizer | None = None,
    ) -> None:
        super().__init__(name_normalizer=name_normalizer)
        self._target = target
        self._data_types = dict(data_types or {})
        self._member_index: dict[str, tuple[str, bool]] | None = None
        self._variables = _LazyRegistry(self, "variable")
        self._actions = _LazyRegistry(self, "action")
        self._functions = _LazyRegistry(self, "function")

    def _build_member_index(self) -> dict[str, tuple[str, bool]]:
        if self._member_index is not None:
            return self._member_index

        index: dict[str, tuple[str, bool]] = {}
        for name in dir(self._target):
            if name.startswith("_"):
                continue
            try:
                value = getattr(self._target, name)
            except AttributeError:
                continue
            normalized_name = self._normalize_entry_name(name)
            if normalized_name in index:
                existing_name, _ = index[normalized_name]
                raise ValueError(
                    f"Members {existing_name!r} and {name!r} normalize to "
                    f"{normalized_name!r}"
                )
            index[normalized_name] = (name, callable(value))

        self._member_index = index
        return index

    def _resolve_data_type(
        self,
        original_name: str,
        normalized_name: str,
        *,
        is_callable: bool,
    ) -> str:
        if original_name in self._data_types:
            data_type = self._data_types[original_name]
        elif normalized_name in self._data_types:
            data_type = self._data_types[normalized_name]
        elif is_callable:
            member = getattr(type(self._target), original_name, None)
            if member is None:
                raise ValueError(
                    f"Cannot resolve data type for callable {original_name!r}"
                )
            hints = get_type_hints(member)
            if "return" not in hints:
                raise ValueError(
                    f"No return type annotation for {original_name!r}; "
                    "provide one or pass data_types= to LazyContext"
                )
            data_type = _python_type_to_data_type(hints["return"])
        else:
            hints = get_type_hints(type(self._target))
            if original_name not in hints:
                raise ValueError(
                    f"No type annotation for {original_name!r}; "
                    "provide one or pass data_types= to LazyContext"
                )
            data_type = _python_type_to_data_type(hints[original_name])

        DataTypesPool.get(data_type)
        return data_type

    def _make_variable_getter(self, original_name: str) -> Callable[..., Any]:
        target = self._target

        def getter() -> Any:
            return getattr(target, original_name)

        return getter

    def _resolve_from_target(
        self, normalized_name: str, kind: _EntryKind
    ) -> RegisteredEntry:
        index = self._build_member_index()
        try:
            original_name, is_callable = index[normalized_name]
        except KeyError as exc:
            raise KeyError(normalized_name) from exc

        if kind == "variable":
            if is_callable:
                raise KeyError(normalized_name)
            func = self._make_variable_getter(original_name)
        else:
            if not is_callable:
                raise KeyError(normalized_name)
            func = getattr(self._target, original_name)

        data_type = self._resolve_data_type(
            original_name,
            normalized_name,
            is_callable=is_callable,
        )
        return RegisteredEntry(
            name=normalized_name,
            data_type=data_type,
            func=func,
        )
