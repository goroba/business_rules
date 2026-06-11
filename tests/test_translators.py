"""Tests for business rule translators."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import pytest

from business_rules.business_rule import BusinessRule
from business_rules.condition import BinaryCondition, Condition, UnaryCondition
from business_rules.operand import Literal, Operand, Variable
from business_rules.operators import EqOperator, IsNotNullOperator
from business_rules.translators import DictTranslator, JsonTranslator
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


def test_dict_translator_dumps_complex_eligibility_rule() -> None:
    assert DictTranslator().dump(_build_rule()) == _COMPLEX_ELIGIBILITY_RULE_DICT


def test_dict_translator_loads_complex_eligibility_rule() -> None:
    assert DictTranslator().load(_COMPLEX_ELIGIBILITY_RULE_DICT) == _build_rule()


def test_json_translator_dumps_complex_eligibility_rule() -> None:
    assert (
        json.loads(JsonTranslator().dump(_build_rule()))
        == _COMPLEX_ELIGIBILITY_RULE_DICT
    )


def test_json_translator_loads_complex_eligibility_rule() -> None:
    assert (
        JsonTranslator().load(_COMPLEX_ELIGIBILITY_RULE_JSON)
        == _build_rule()
    )


def test_dict_translator_round_trip_minimal_rule() -> None:
    translator = DictTranslator()
    rule = BusinessRule(
        having=BinaryCondition(
            left=Variable("status"),
            operator=EqOperator,
            right=Literal("active"),
        )
    )

    restored = translator.load(translator.dump(rule))

    assert restored == rule
    assert "on_success" not in translator.dump(rule)
    assert "on_failure" not in translator.dump(rule)
    assert "on_finally" not in translator.dump(rule)


def test_dict_translator_unknown_condition_type_raises() -> None:
    translator = DictTranslator()

    with pytest.raises(ValueError, match="Unknown condition type"):
        translator.load({"having": {"type": "unknown"}})


def test_dict_translator_unknown_operand_type_raises() -> None:
    translator = DictTranslator()

    with pytest.raises(ValueError, match="Unknown operand type"):
        translator.load(
            {
                "having": {
                    "type": "binary",
                    "left": {"type": "unknown"},
                    "operator": "eq",
                    "right": {"type": "literal", "value": "active"},
                }
            }
        )


def test_dict_translator_unknown_operator_raises() -> None:
    translator = DictTranslator()

    with pytest.raises(KeyError, match="not registered"):
        translator.load(
            {
                "having": {
                    "type": "binary",
                    "left": {"type": "variable", "name": "status"},
                    "operator": "missing",
                    "right": {"type": "literal", "value": "active"},
                }
            }
        )


def test_dict_translator_binary_operator_in_unary_slot_raises() -> None:
    translator = DictTranslator()

    with pytest.raises(TypeError, match="is not unary"):
        translator.load(
            {
                "having": {
                    "type": "unary",
                    "operand": {"type": "variable", "name": "email"},
                    "operator": "eq",
                }
            }
        )


def test_dict_translator_unary_operator_in_binary_slot_raises() -> None:
    translator = DictTranslator()

    with pytest.raises(TypeError, match="is not binary"):
        translator.load(
            {
                "having": {
                    "type": "binary",
                    "left": {"type": "variable", "name": "status"},
                    "operator": "is_not_null",
                    "right": {"type": "literal", "value": "active"},
                }
            }
        )


def test_dict_translator_unary_literal_operand_raises() -> None:
    translator = DictTranslator()

    with pytest.raises(TypeError, match="Unary operand must be a DataTypeAwareOperand"):
        translator.load(
            {
                "having": {
                    "type": "unary",
                    "operand": {"type": "literal", "value": "active"},
                    "operator": "is_not_null",
                }
            }
        )


def test_dict_translator_invalid_action_type_raises() -> None:
    translator = DictTranslator()

    with pytest.raises(ValueError, match="Expected action node"):
        translator.load(
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


def test_dict_translator_unsupported_condition_on_dump_raises() -> None:
    translator = DictTranslator()

    with pytest.raises(TypeError, match="Unsupported condition type"):
        translator.dump(BusinessRule(having=StubCondition()))


def test_dict_translator_unsupported_operand_on_dump_raises() -> None:
    translator = DictTranslator()

    with pytest.raises(TypeError, match="Unsupported operand type"):
        translator.dump(
            BusinessRule(
                having=BinaryCondition(
                    left=StubOperand(),
                    operator=EqOperator,
                    right=Literal("active"),
                )
            )
        )


def test_json_translator_invalid_json_raises() -> None:
    translator = JsonTranslator()

    with pytest.raises(json.JSONDecodeError):
        translator.load("not json")


def test_json_translator_uses_injected_dict_translator() -> None:
    dict_translator = DictTranslator()
    json_translator = JsonTranslator(dict_translator=dict_translator)
    rule = BusinessRule(
        having=UnaryCondition(
            operand=Variable("email"),
            operator=IsNotNullOperator,
        )
    )

    restored = json_translator.load(json_translator.dump(rule))

    assert restored == rule
