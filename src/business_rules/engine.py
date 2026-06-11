"""Business rules engine."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar

from business_rules.business_rule import BusinessRule
from business_rules.context import Context, RegisteredEntry
from business_rules.evaluation import EvaluationContext
from business_rules.name_normalizers import NameNormalizer, SnakeCaseNameNormalizer

__all__ = ["Engine"]

_CallableT = TypeVar("_CallableT", bound=Callable[..., Any])


class Engine:
    def __init__(self, name_normalizer: NameNormalizer | None = None) -> None:
        self._name_normalizer = name_normalizer or SnakeCaseNameNormalizer()
        self.context = Context(name_normalizer=self._name_normalizer)

    @property
    def name_normalizer(self) -> NameNormalizer:
        return self._name_normalizer

    def variable(
        self, name: str | None = None, *, data_type: str
    ) -> Callable[[_CallableT], _CallableT]:
        return self.context.variable(name, data_type=data_type)

    def action(
        self, name: str | None = None, *, data_type: str
    ) -> Callable[[_CallableT], _CallableT]:
        return self.context.action(name, data_type=data_type)

    def function(
        self, name: str | None = None, *, data_type: str
    ) -> Callable[[_CallableT], _CallableT]:
        return self.context.function(name, data_type=data_type)

    def _resolve_entry(
        self,
        name: str,
        local_context: Context | None,
        local_registry: dict[str, RegisteredEntry],
        engine_registry: dict[str, RegisteredEntry],
        kind: str,
    ) -> RegisteredEntry:
        lookup_context = local_context or self.context
        normalized_name = lookup_context._normalize_entry_name(name)
        if local_context is not None:
            try:
                return local_registry[normalized_name]
            except KeyError:
                pass
        try:
            return engine_registry[normalized_name]
        except KeyError as exc:
            raise KeyError(f"{kind} {name!r} is not registered") from exc

    def resolve_variable(
        self, name: str, local_context: Context | None
    ) -> RegisteredEntry:
        return self._resolve_entry(
            name,
            local_context,
            local_context._variables if local_context is not None else {},
            self.context._variables,
            "Variable",
        )

    def resolve_action(
        self, name: str, local_context: Context | None
    ) -> RegisteredEntry:
        return self._resolve_entry(
            name,
            local_context,
            local_context._actions if local_context is not None else {},
            self.context._actions,
            "Action",
        )

    def resolve_function(
        self, name: str, local_context: Context | None
    ) -> RegisteredEntry:
        return self._resolve_entry(
            name,
            local_context,
            local_context._functions if local_context is not None else {},
            self.context._functions,
            "Function",
        )

    def run(
        self,
        business_rule: BusinessRule,
        local_context: Context | None = None,
    ) -> None:
        """Execute a business rule against the optional local context."""
        ctx = EvaluationContext(self, local_context)
        business_rule.evaluate(ctx)
