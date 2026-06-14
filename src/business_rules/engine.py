"""Business rules engine."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import Any, Literal, TypeVar

from business_rules.business_rule import BusinessRule
from business_rules.context import Context, RegisteredEntry
from business_rules.evaluation import EvaluationContext
from business_rules.name_normalizers import NameNormalizer, SnakeCaseNameNormalizer

__all__ = ["Engine"]

_CallableT = TypeVar("_CallableT", bound=Callable[..., Any])
_EntryKind = Literal["variable", "action", "function"]


class Engine:
    def __init__(self, name_normalizer: NameNormalizer | None = None) -> None:
        self._name_normalizer = name_normalizer or SnakeCaseNameNormalizer()
        self.context = Context(name_normalizer=self._name_normalizer)
        self._in_local_scope = False

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

    @contextmanager
    def _local_context_scope(
        self, local_context: Context | None
    ) -> Iterator[None]:
        self._in_local_scope = local_context is not None
        if local_context is not None:
            self.context.nests(local_context)
        try:
            yield
        finally:
            self.context._clear_nested()
            self._in_local_scope = False

    def _context_chain(self, local_context: Context | None) -> list[Context]:
        if self._in_local_scope:
            contexts = list(self.context._iter_nested())
            contexts.reverse()
            return contexts
        if local_context is not None:
            contexts = list(local_context._iter_nested())
            contexts.reverse()
            contexts.append(self.context)
            return contexts
        return [self.context]

    def _resolve_entry(
        self,
        name: str,
        local_context: Context | None,
        kind: _EntryKind,
        label: str,
    ) -> RegisteredEntry:
        contexts = self._context_chain(local_context)
        normalized_name = contexts[0]._normalize_entry_name(name)
        for context in contexts:
            try:
                return context._lookup_entry(kind, normalized_name)
            except KeyError:
                continue
        raise KeyError(f"{label} {name!r} is not registered")

    def resolve_variable(
        self, name: str, local_context: Context | None
    ) -> RegisteredEntry:
        return self._resolve_entry(name, local_context, "variable", "Variable")

    def resolve_action(
        self, name: str, local_context: Context | None
    ) -> RegisteredEntry:
        return self._resolve_entry(name, local_context, "action", "Action")

    def resolve_function(
        self, name: str, local_context: Context | None
    ) -> RegisteredEntry:
        return self._resolve_entry(name, local_context, "function", "Function")

    def check(
        self,
        business_rule: BusinessRule,
        local_context: Context | None = None,
    ) -> bool:
        """Evaluate whether a business rule's condition is met."""
        with self._local_context_scope(local_context):
            ctx = EvaluationContext(self, local_context)
            return business_rule.evaluate(ctx)

    def run(
        self,
        business_rule: BusinessRule,
        local_context: Context | None = None,
        target: Any = None,
    ) -> bool:
        """Evaluate a business rule and run its lifecycle actions."""
        with self._local_context_scope(local_context):
            ctx = EvaluationContext(self, local_context, target=target)
            result = business_rule.evaluate(ctx)
            if result:
                for action in business_rule.on_success or []:
                    action.execute(ctx)
            else:
                for action in business_rule.on_failure or []:
                    action.execute(ctx)
            for action in business_rule.on_finally or []:
                action.execute(ctx)

            return result
