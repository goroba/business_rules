"""Fluent builder for business rules."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Self

from business_rules.business_rule import BusinessRule
from business_rules.condition import (
    BinaryCondition,
    Condition,
    Conjunction,
    Disjunction,
    NegatedCondition,
    UnaryCondition,
)
from business_rules.executable import Action
from business_rules.operand import (
    DataTypeAwareOperand,
    Function,
    Literal,
    Operand,
    Variable,
)
from business_rules.operators import builtin  # noqa: F401
from business_rules.operators.base import BinaryOperator, UnaryOperator
from business_rules.operators.pool import OperatorsPool

__all__ = [
    "BusinessRuleBuilder",
    "binary",
    "function",
    "get_builder",
    "literal",
    "unary",
    "variable",
]


class _Phase(Enum):
    INITIAL = auto()
    HAVING = auto()
    ON_SUCCESS = auto()
    ON_FAILURE = auto()
    ON_FINALLY = auto()
    READY = auto()


@dataclass
class _GroupFrame:
    kind: str
    children: list[Condition] = field(default_factory=list)


def _validate_name(name: str, kind: str) -> None:
    if not name:
        raise ValueError(f"{kind} name must not be empty")


def variable(name: str) -> Variable:
    _validate_name(name, "Variable")
    return Variable(name=name)


def function(
    name: str,
    *,
    args: tuple[Any, ...] = (),
    kwargs: dict[str, Any] | None = None,
) -> Function:
    _validate_name(name, "Function")
    return Function(name=name, args=args, kwargs=kwargs or {})


def literal(value: str) -> Literal:
    return Literal(value=value)


def _coerce_operand(value: Operand | str | int | float | bool) -> Operand:
    if isinstance(value, Operand):
        return value
    if isinstance(value, (str, int, float, bool)):
        return Literal(str(value))
    raise TypeError(f"Expected Operand or scalar, got {type(value).__name__}")


def _resolve_binary_operator(operator_name: str) -> type[BinaryOperator]:
    operator_cls = OperatorsPool.get(operator_name)
    if not issubclass(operator_cls, BinaryOperator):
        raise TypeError(f"Operator {operator_name!r} is not binary")
    return operator_cls


def _resolve_unary_operator(operator_name: str) -> type[UnaryOperator]:
    operator_cls = OperatorsPool.get(operator_name)
    if not issubclass(operator_cls, UnaryOperator):
        raise TypeError(f"Operator {operator_name!r} is not unary")
    return operator_cls


def binary(
    left: Operand | str | int | float | bool,
    operator_name: str,
    right: Operand | str | int | float | bool,
) -> BinaryCondition:
    operator_cls = _resolve_binary_operator(operator_name)
    return BinaryCondition(
        left=_coerce_operand(left),
        operator=operator_cls,
        right=_coerce_operand(right),
    )


def unary(
    operand: DataTypeAwareOperand,
    operator_name: str,
) -> UnaryCondition:
    if not isinstance(operand, DataTypeAwareOperand):
        raise TypeError("Unary operand must be a DataTypeAwareOperand")
    operator_cls = _resolve_unary_operator(operator_name)
    return UnaryCondition(operand=operand, operator=operator_cls)


def _wrap_group(kind: str, children: tuple[Condition, ...]) -> Condition:
    if kind == "all":
        return Conjunction(all=children)
    return Disjunction(any=children)


class BusinessRuleBuilder:
    def __init__(self) -> None:
        self._phase = _Phase.INITIAL
        self._having: Condition | None = None
        self._group_stack: list[_GroupFrame] = []
        self._on_success: list[Action] | None = None
        self._on_failure: list[Action] | None = None
        self._on_finally: list[Action] | None = None
        self._lifecycle_sections: set[_Phase] = set()
        self._open_lifecycle: _Phase | None = None
        self._lifecycle_buffer: list[Action] = []

    def having(self) -> Self:
        if self._phase is not _Phase.INITIAL:
            raise ValueError("having() can only be called once at the start")
        self._phase = _Phase.HAVING
        return self

    def all(self) -> Self:
        self._require_having_phase()
        self._group_stack.append(_GroupFrame(kind="all"))
        return self

    def any(self) -> Self:
        self._require_having_phase()
        self._group_stack.append(_GroupFrame(kind="any"))
        return self

    def binary(
        self,
        left: Operand | str | int | float | bool,
        operator_name: str,
        right: Operand | str | int | float | bool,
    ) -> Self:
        self._require_having_phase()
        self._append_condition(binary(left, operator_name, right))
        return self

    def unary(self, operand: DataTypeAwareOperand, operator_name: str) -> Self:
        self._require_having_phase()
        self._append_condition(unary(operand, operator_name))
        return self

    def negative(self, condition: Condition) -> Self:
        self._require_having_phase()
        if not isinstance(condition, Condition):
            raise TypeError("negative() requires a Condition instance")
        self._append_condition(NegatedCondition(negative=condition))
        return self

    def end(self) -> Self:
        if self._phase is _Phase.HAVING:
            return self._end_having_group()
        if self._open_lifecycle is not None:
            return self._end_lifecycle_block()
        raise ValueError("end() called with no open group or lifecycle block")

    def on_success(self) -> Self:
        return self._open_lifecycle_block(_Phase.ON_SUCCESS)

    def on_failure(self) -> Self:
        return self._open_lifecycle_block(_Phase.ON_FAILURE)

    def on_finally(self) -> Self:
        return self._open_lifecycle_block(_Phase.ON_FINALLY)

    def action(
        self,
        name: str,
        *,
        args: tuple[Any, ...] = (),
        kwargs: dict[str, Any] | None = None,
    ) -> Self:
        if self._open_lifecycle is None:
            raise ValueError("action() must be called inside a lifecycle block")
        _validate_name(name, "Action")
        self._lifecycle_buffer.append(
            Action(name=name, args=args, kwargs=kwargs or {})
        )
        return self

    def build(self) -> BusinessRule:
        if self._phase is _Phase.INITIAL:
            raise ValueError("build() requires having() to be called")
        if self._group_stack:
            raise ValueError("build() called with unclosed condition group")
        if self._open_lifecycle is not None:
            raise ValueError("build() called with unclosed lifecycle block")
        if self._having is None:
            raise ValueError("build() requires a having condition")

        return BusinessRule(
            having=self._having,
            on_success=self._on_success,
            on_failure=self._on_failure,
            on_finally=self._on_finally,
        )

    def _require_having_phase(self) -> None:
        if self._phase is not _Phase.HAVING:
            raise ValueError("Condition methods require an open having() block")

    def _append_condition(self, condition: Condition) -> None:
        if not self._group_stack:
            raise ValueError(
                "Conditions must be added inside an all() or any() group"
            )
        self._group_stack[-1].children.append(condition)

    def _end_having_group(self) -> Self:
        if not self._group_stack:
            raise ValueError("end() called with no open condition group")
        frame = self._group_stack.pop()
        if not frame.children:
            raise ValueError(f"{frame.kind}() group must not be empty")
        wrapped = _wrap_group(frame.kind, tuple(frame.children))
        if self._group_stack:
            self._group_stack[-1].children.append(wrapped)
        else:
            self._having = wrapped
            self._phase = _Phase.READY
        return self

    def _open_lifecycle_block(self, phase: _Phase) -> Self:
        if self._phase is _Phase.HAVING:
            raise ValueError("Close having() with end() before lifecycle blocks")
        if self._having is None:
            raise ValueError("having() must be completed before lifecycle blocks")
        if phase in self._lifecycle_sections:
            raise ValueError(f"{phase.name.lower()}() can only be called once")
        if self._open_lifecycle is not None:
            raise ValueError("Close the current lifecycle block with end() first")
        self._lifecycle_sections.add(phase)
        self._open_lifecycle = phase
        self._lifecycle_buffer = []
        self._phase = phase
        return self

    def _end_lifecycle_block(self) -> Self:
        actions = list(self._lifecycle_buffer)
        if self._open_lifecycle is _Phase.ON_SUCCESS:
            self._on_success = actions
        elif self._open_lifecycle is _Phase.ON_FAILURE:
            self._on_failure = actions
        elif self._open_lifecycle is _Phase.ON_FINALLY:
            self._on_finally = actions
        self._open_lifecycle = None
        self._lifecycle_buffer = []
        self._phase = _Phase.READY
        return self


def get_builder() -> BusinessRuleBuilder:
    return BusinessRuleBuilder()
