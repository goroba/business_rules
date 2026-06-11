"""Tests for the business rule builder."""

from __future__ import annotations

import pytest

from business_rules.builder import (
    binary,
    function,
    get_builder,
    literal,
    unary,
    variable,
)
from business_rules.business_rule import BusinessRule
from test_complex_business_rule import _build_rule

# fmt: off


def _build_rule_via_builder() -> BusinessRule:
    return (
        get_builder()
        .having()
        .all()
            .all()
                .binary(variable("age"), "gte", "18")
                .binary(variable("status"), "eq", "active")
                .unary(variable("email"), "is_not_null")
                .binary(variable("email"), "contains", "@")
                .unary(function("lookup"), "is_not_null")
            .end()
            .any()
                .all()
                    .binary(variable("tier"), "eq", "premium")
                    .binary(variable("balance"), "gte", "100.00")
                .end()
                .all()
                    .binary(variable("registration_date"), "lt", "2024-06-01")
                    .negative(binary(variable("is_suspended"), "eq", "true"))
                    .binary(variable("last_login"), "gte", function("login_cutoff"))
                    .binary(variable("age"), "eq", variable("min_age"))
                .end()
            .end()
            .negative(binary(variable("user_id"), "is_in", function("blocklist")))
            .binary(
                variable("region"),
                "is_in",
                function("allowed_regions", args=("premium",)),
            )
        .end()
        .on_success()
            .action("grant_access")
        .end()
        .on_failure()
            .action("reject_access")
        .end()
        .on_finally()
            .action("audit_log")
        .end()
        .build()
    )


def test_builder_produces_equivalent_complex_rule() -> None:
    assert _build_rule_via_builder() == _build_rule()


def test_unknown_binary_operator_raises_key_error() -> None:
    with pytest.raises(KeyError, match="not registered"):
        binary(variable("age"), "unknown_op", "18")


def test_binary_operator_with_unary_operator_raises_type_error() -> None:
    with pytest.raises(TypeError, match="is not binary"):
        binary(variable("email"), "is_not_null", "x")


def test_unknown_unary_operator_raises_key_error() -> None:
    with pytest.raises(KeyError, match="not registered"):
        unary(variable("email"), "unknown_op")


def test_unary_operator_with_binary_operator_raises_type_error() -> None:
    with pytest.raises(TypeError, match="is not unary"):
        unary(variable("email"), "eq")


def test_unary_with_literal_operand_raises_type_error() -> None:
    with pytest.raises(TypeError, match="DataTypeAwareOperand"):
        unary(literal("x"), "is_null")  # type: ignore[arg-type]


def test_binary_before_having_raises() -> None:
    with pytest.raises(ValueError, match="having"):
        (
            get_builder()
            .binary(variable("age"), "gte", "18")
        )


def test_action_outside_lifecycle_block_raises() -> None:
    builder = (
        get_builder()
        .having()
        .all()
            .binary(variable("age"), "gte", "18")
        .end()
    )
    with pytest.raises(ValueError, match="lifecycle block"):
        builder.action("grant_access")


def test_extra_end_raises() -> None:
    builder = (
        get_builder()
        .having()
        .all()
            .binary(variable("age"), "gte", "18")
        .end()
    )
    with pytest.raises(ValueError, match="no open"):
        builder.end()


def test_empty_group_on_end_raises() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        (
            get_builder()
            .having()
            .all()
            .end()
        )


def test_build_without_having_raises() -> None:
    with pytest.raises(ValueError, match="having"):
        (
            get_builder()
            .build()
        )


def test_build_with_unclosed_group_raises() -> None:
    with pytest.raises(ValueError, match="unclosed"):
        (
            get_builder()
            .having()
            .all()
                .binary(variable("age"), "gte", "18")
            .build()
        )


def test_build_with_unclosed_lifecycle_block_raises() -> None:
    with pytest.raises(ValueError, match="unclosed lifecycle"):
        (
            get_builder()
            .having()
            .all()
                .binary(variable("age"), "gte", "18")
            .end()
            .on_success()
                .action("grant_access")
            .build()
        )


def test_having_called_twice_raises() -> None:
    with pytest.raises(ValueError, match="once"):
        (
            get_builder()
            .having()
            .having()
        )


def test_negative_requires_condition() -> None:
    with pytest.raises(TypeError, match="Condition"):
        (
            get_builder()
            .having()
            .all()
                .negative(variable("age"))  # type: ignore[arg-type]
            .end()
        )


def test_condition_outside_group_raises() -> None:
    with pytest.raises(ValueError, match="all\\(\\) or any\\(\\)"):
        (
            get_builder()
            .having()
            .binary(variable("age"), "gte", "18")
        )


def test_lifecycle_block_before_having_closed_raises() -> None:
    with pytest.raises(ValueError, match="Close having"):
        (
            get_builder()
            .having()
            .all()
                .binary(variable("age"), "gte", "18")
            .on_success()
        )


def test_lifecycle_block_called_twice_raises() -> None:
    with pytest.raises(ValueError, match="once"):
        (
            get_builder()
            .having()
            .all()
                .binary(variable("age"), "gte", "18")
            .end()
            .on_success()
            .end()
            .on_success()
        )


def test_variable_empty_name_raises() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        variable("")


def test_coerce_operand_rejects_invalid_type() -> None:
    with pytest.raises(TypeError, match="Expected Operand"):
        binary(variable("age"), "gte", object())  # type: ignore[arg-type]

# fmt: on
