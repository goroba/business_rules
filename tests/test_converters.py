"""Tests for business rule converters."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import pytest

from business_rules.business_rule import BusinessRule
from business_rules.condition import BinaryCondition, Condition, UnaryCondition
from business_rules.converters import DictConverter, JsonConverter
from business_rules.operand import Literal, Operand, Variable
from business_rules.operators import EqOperator, IsNotNullOperator
from test_complex_business_rule import _build_rule

_COMPLEX_ELIGIBILITY_RULE_JSON = """
{
    "having": {
        "type": "all",
        "conditions": [
            {
                "type": "all",
                "conditions": [
                    {
                        "type": "binary",
                        "left": {
                            "type": "variable",
                            "name": "age"
                        },
                        "operator": "gte",
                        "right": {
                            "type": "literal",
                            "value": "18"
                        }
                    },
                    {
                        "type": "binary",
                        "left": {
                            "type": "variable",
                            "name": "status"
                        },
                        "operator": "eq",
                        "right": {
                            "type": "literal",
                            "value": "active"
                        }
                    },
                    {
                        "type": "unary",
                        "operand": {
                            "type": "variable",
                            "name": "email"
                        },
                        "operator": "is_not_null"
                    },
                    {
                        "type": "binary",
                        "left": {
                            "type": "variable",
                            "name": "email"
                        },
                        "operator": "contains",
                        "right": {
                            "type": "literal",
                            "value": "@"
                        }
                    },
                    {
                        "type": "unary",
                        "operand": {
                            "type": "function",
                            "name": "lookup",
                            "args": [],
                            "kwargs": {}
                        },
                        "operator": "is_not_null"
                    }
                ]
            },
            {
                "type": "any",
                "conditions": [
                    {
                        "type": "all",
                        "conditions": [
                            {
                                "type": "binary",
                                "left": {
                                    "type": "variable",
                                    "name": "tier"
                                },
                                "operator": "eq",
                                "right": {
                                    "type": "literal",
                                    "value": "premium"
                                }
                            },
                            {
                                "type": "binary",
                                "left": {
                                    "type": "variable",
                                    "name": "balance"
                                },
                                "operator": "gte",
                                "right": {
                                    "type": "literal",
                                    "value": "100.00"
                                }
                            }
                        ]
                    },
                    {
                        "type": "all",
                        "conditions": [
                            {
                                "type": "binary",
                                "left": {
                                    "type": "variable",
                                    "name": "registration_date"
                                },
                                "operator": "lt",
                                "right": {
                                    "type": "literal",
                                    "value": "2024-06-01"
                                }
                            },
                            {
                                "type": "negative",
                                "condition": {
                                    "type": "binary",
                                    "left": {
                                        "type": "variable",
                                        "name": "is_suspended"
                                    },
                                    "operator": "eq",
                                    "right": {
                                        "type": "literal",
                                        "value": "true"
                                    }
                                }
                            },
                            {
                                "type": "binary",
                                "left": {
                                    "type": "variable",
                                    "name": "last_login"
                                },
                                "operator": "gte",
                                "right": {
                                    "type": "function",
                                    "name": "login_cutoff",
                                    "args": [],
                                    "kwargs": {}
                                }
                            },
                            {
                                "type": "binary",
                                "left": {
                                    "type": "variable",
                                    "name": "age"
                                },
                                "operator": "eq",
                                "right": {
                                    "type": "variable",
                                    "name": "min_age"
                                }
                            }
                        ]
                    }
                ]
            },
            {
                "type": "negative",
                "condition": {
                    "type": "binary",
                    "left": {
                        "type": "variable",
                        "name": "user_id"
                    },
                    "operator": "is_in",
                    "right": {
                        "type": "function",
                        "name": "blocklist",
                        "args": [],
                        "kwargs": {}
                    }
                }
            },
            {
                "type": "binary",
                "left": {
                    "type": "variable",
                    "name": "region"
                },
                "operator": "is_in",
                "right": {
                    "type": "function",
                    "name": "allowed_regions",
                    "args": [
                        "premium"
                    ],
                    "kwargs": {}
                }
            }
        ]
    },
    "on_success": [
        {
            "type": "action",
            "name": "grant_access",
            "args": [],
            "kwargs": {}
        }
    ],
    "on_failure": [
        {
            "type": "action",
            "name": "reject_access",
            "args": [],
            "kwargs": {}
        }
    ],
    "on_finally": [
        {
            "type": "action",
            "name": "audit_log",
            "args": [],
            "kwargs": {}
        }
    ]
}
"""

_COMPLEX_ELIGIBILITY_RULE_DICT: dict[str, Any] = json.loads(
    _COMPLEX_ELIGIBILITY_RULE_JSON
)


@dataclass
class StubCondition(Condition):
    def evaluate(self, ctx: object) -> bool:
        return True


@dataclass
class StubOperand(Operand):
    def evaluate(self, ctx: object) -> object:
        return None


def test_dict_converter_dumps_complex_eligibility_rule() -> None:
    assert DictConverter().dump(_build_rule()) == _COMPLEX_ELIGIBILITY_RULE_DICT


def test_dict_converter_loads_complex_eligibility_rule() -> None:
    assert DictConverter().load(_COMPLEX_ELIGIBILITY_RULE_DICT) == _build_rule()


def test_json_converter_dumps_complex_eligibility_rule() -> None:
    assert (
        json.loads(JsonConverter().dump(_build_rule()))
        == _COMPLEX_ELIGIBILITY_RULE_DICT
    )


def test_json_converter_loads_complex_eligibility_rule() -> None:
    assert (
        JsonConverter().load(_COMPLEX_ELIGIBILITY_RULE_JSON)
        == _build_rule()
    )


def test_dict_converter_round_trip_minimal_rule() -> None:
    converter = DictConverter()
    rule = BusinessRule(
        having=BinaryCondition(
            left=Variable("status"),
            operator=EqOperator,
            right=Literal("active"),
        )
    )

    restored = converter.load(converter.dump(rule))

    assert restored == rule
    assert "on_success" not in converter.dump(rule)
    assert "on_failure" not in converter.dump(rule)
    assert "on_finally" not in converter.dump(rule)


def test_dict_converter_unknown_condition_type_raises() -> None:
    converter = DictConverter()

    with pytest.raises(ValueError, match="Unknown condition type"):
        converter.load({"having": {"type": "unknown"}})


def test_dict_converter_unknown_operand_type_raises() -> None:
    converter = DictConverter()

    with pytest.raises(ValueError, match="Unknown operand type"):
        converter.load(
            {
                "having": {
                    "type": "binary",
                    "left": {"type": "unknown"},
                    "operator": "eq",
                    "right": {"type": "literal", "value": "active"},
                }
            }
        )


def test_dict_converter_unknown_operator_raises() -> None:
    converter = DictConverter()

    with pytest.raises(KeyError, match="not registered"):
        converter.load(
            {
                "having": {
                    "type": "binary",
                    "left": {"type": "variable", "name": "status"},
                    "operator": "missing",
                    "right": {"type": "literal", "value": "active"},
                }
            }
        )


def test_dict_converter_binary_operator_in_unary_slot_raises() -> None:
    converter = DictConverter()

    with pytest.raises(TypeError, match="is not unary"):
        converter.load(
            {
                "having": {
                    "type": "unary",
                    "operand": {"type": "variable", "name": "email"},
                    "operator": "eq",
                }
            }
        )


def test_dict_converter_unary_operator_in_binary_slot_raises() -> None:
    converter = DictConverter()

    with pytest.raises(TypeError, match="is not binary"):
        converter.load(
            {
                "having": {
                    "type": "binary",
                    "left": {"type": "variable", "name": "status"},
                    "operator": "is_not_null",
                    "right": {"type": "literal", "value": "active"},
                }
            }
        )


def test_dict_converter_unary_literal_operand_raises() -> None:
    converter = DictConverter()

    with pytest.raises(TypeError, match="Unary operand must be a DataTypeAwareOperand"):
        converter.load(
            {
                "having": {
                    "type": "unary",
                    "operand": {"type": "literal", "value": "active"},
                    "operator": "is_not_null",
                }
            }
        )


def test_dict_converter_invalid_action_type_raises() -> None:
    converter = DictConverter()

    with pytest.raises(ValueError, match="Expected action node"):
        converter.load(
            {
                "having": {
                    "type": "binary",
                    "left": {"type": "variable", "name": "status"},
                    "operator": "eq",
                    "right": {"type": "literal", "value": "active"},
                },
                "on_success": [{"type": "function", "name": "grant_access"}],
            }
        )


def test_dict_converter_unsupported_condition_on_dump_raises() -> None:
    converter = DictConverter()

    with pytest.raises(TypeError, match="Unsupported condition type"):
        converter.dump(BusinessRule(having=StubCondition()))


def test_dict_converter_unsupported_operand_on_dump_raises() -> None:
    converter = DictConverter()

    with pytest.raises(TypeError, match="Unsupported operand type"):
        converter.dump(
            BusinessRule(
                having=BinaryCondition(
                    left=StubOperand(),
                    operator=EqOperator,
                    right=Literal("active"),
                )
            )
        )


def test_json_converter_invalid_json_raises() -> None:
    converter = JsonConverter()

    with pytest.raises(json.JSONDecodeError):
        converter.load("not json")


def test_json_converter_uses_injected_dict_converter() -> None:
    dict_converter = DictConverter()
    json_converter = JsonConverter(dict_converter=dict_converter)
    rule = BusinessRule(
        having=UnaryCondition(
            operand=Variable("email"),
            operator=IsNotNullOperator,
        )
    )

    restored = json_converter.load(json_converter.dump(rule))

    assert restored == rule
