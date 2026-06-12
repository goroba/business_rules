"""Dict-based converter for business rules."""

from __future__ import annotations

from typing import Any

from business_rules.business_rule import BusinessRule
from business_rules.condition import (
    BinaryCondition,
    Condition,
    Conjunction,
    Disjunction,
    NegatedCondition,
    UnaryCondition,
)
from business_rules.converters.base import Converter
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

__all__ = ["DictConverter"]


class DictConverter(Converter[dict[str, Any]]):
    def load(self, source: dict[str, Any]) -> BusinessRule:
        return BusinessRule(
            having=self._decode_condition(source["having"]),
            on_success=self._decode_actions(source.get("on_success")),
            on_failure=self._decode_actions(source.get("on_failure")),
            on_finally=self._decode_actions(source.get("on_finally")),
        )

    def dump(self, business_rule: BusinessRule) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "having": self._encode_condition(business_rule.having),
        }
        if business_rule.on_success is not None:
            payload["on_success"] = self._encode_actions(business_rule.on_success)
        if business_rule.on_failure is not None:
            payload["on_failure"] = self._encode_actions(business_rule.on_failure)
        if business_rule.on_finally is not None:
            payload["on_finally"] = self._encode_actions(business_rule.on_finally)
        return payload

    def _encode_condition(self, condition: Condition) -> dict[str, Any]:
        if isinstance(condition, BinaryCondition):
            return {
                "type": "binary",
                "left": self._encode_operand(condition.left),
                "operator": condition.operator.name,
                "right": self._encode_operand(condition.right),
            }
        if isinstance(condition, UnaryCondition):
            return {
                "type": "unary",
                "operand": self._encode_operand(condition.operand),
                "operator": condition.operator.name,
            }
        if isinstance(condition, Conjunction):
            return {
                "type": "all",
                "conditions": [
                    self._encode_condition(child) for child in condition.all
                ],
            }
        if isinstance(condition, Disjunction):
            return {
                "type": "any",
                "conditions": [
                    self._encode_condition(child) for child in condition.any
                ],
            }
        if isinstance(condition, NegatedCondition):
            return {
                "type": "negative",
                "condition": self._encode_condition(condition.negative),
            }
        raise TypeError(
            f"Unsupported condition type: {type(condition).__name__}"
        )

    def _decode_condition(self, payload: dict[str, Any]) -> Condition:
        node_type = payload.get("type")
        if node_type == "binary":
            return BinaryCondition(
                left=self._decode_operand(payload["left"]),
                operator=self._resolve_binary_operator(payload["operator"]),
                right=self._decode_operand(payload["right"]),
            )
        if node_type == "unary":
            operand = self._decode_operand(payload["operand"])
            if not isinstance(operand, DataTypeAwareOperand):
                raise TypeError("Unary operand must be a DataTypeAwareOperand")
            return UnaryCondition(
                operand=operand,
                operator=self._resolve_unary_operator(payload["operator"]),
            )
        if node_type == "all":
            return Conjunction(
                all=tuple(
                    self._decode_condition(child)
                    for child in payload["conditions"]
                )
            )
        if node_type == "any":
            return Disjunction(
                any=tuple(
                    self._decode_condition(child)
                    for child in payload["conditions"]
                )
            )
        if node_type == "negative":
            return NegatedCondition(
                negative=self._decode_condition(payload["condition"])
            )
        raise ValueError(f"Unknown condition type: {node_type!r}")

    def _encode_operand(self, operand: Operand) -> dict[str, Any]:
        if isinstance(operand, Variable):
            return {"type": "variable", "name": operand.name}
        if isinstance(operand, Literal):
            return {"type": "literal", "value": operand.value}
        if isinstance(operand, Function):
            return {
                "type": "function",
                "name": operand.name,
                "args": list(operand.args),
                "kwargs": operand.kwargs,
            }
        raise TypeError(f"Unsupported operand type: {type(operand).__name__}")

    def _decode_operand(self, payload: dict[str, Any]) -> Operand:
        node_type = payload.get("type")
        if node_type == "variable":
            return Variable(name=payload["name"])
        if node_type == "literal":
            return Literal(value=payload["value"])
        if node_type == "function":
            return Function(
                name=payload["name"],
                args=tuple(payload.get("args", [])),
                kwargs=payload.get("kwargs", {}),
            )
        raise ValueError(f"Unknown operand type: {node_type!r}")

    def _encode_actions(self, actions: list[Action]) -> list[dict[str, Any]]:
        return [self._encode_action(action) for action in actions]

    def _encode_action(self, action: Action) -> dict[str, Any]:
        return {
            "type": "action",
            "name": action.name,
            "args": list(action.args),
            "kwargs": action.kwargs,
        }

    def _decode_actions(
        self, payload: list[dict[str, Any]] | None
    ) -> list[Action] | None:
        if payload is None:
            return None
        return [self._decode_action(item) for item in payload]

    def _decode_action(self, payload: dict[str, Any]) -> Action:
        if payload.get("type") != "action":
            raise ValueError(
                f"Expected action node, got type {payload.get('type')!r}"
            )
        return Action(
            name=payload["name"],
            args=tuple(payload.get("args", [])),
            kwargs=payload.get("kwargs", {}),
        )

    def _resolve_binary_operator(self, operator_name: str) -> type[BinaryOperator]:
        operator_cls = OperatorsPool.get(operator_name)
        if not issubclass(operator_cls, BinaryOperator):
            raise TypeError(f"Operator {operator_name!r} is not binary")
        return operator_cls

    def _resolve_unary_operator(self, operator_name: str) -> type[UnaryOperator]:
        operator_cls = OperatorsPool.get(operator_name)
        if not issubclass(operator_cls, UnaryOperator):
            raise TypeError(f"Operator {operator_name!r} is not unary")
        return operator_cls
