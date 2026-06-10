"""Built-in operators registered in the global pool."""

from __future__ import annotations

from business_rules.operators.base import BinaryOperator, UnaryOperator
from business_rules.operators.pool import binary, unary

__all__ = [
    "ContainsOperator",
    "EndsWithOperator",
    "EqOperator",
    "GtOperator",
    "GteOperator",
    "IsInOperator",
    "IsNotInOperator",
    "IsNotNullOperator",
    "IsNullOperator",
    "LtOperator",
    "LteOperator",
    "MatchesOperator",
    "NeOperator",
    "NegOperator",
    "NotContainsOperator",
    "NotOperator",
    "StartsWithOperator",
]


@unary("neg")
class NegOperator(UnaryOperator):
    pass


@unary("is_null")
class IsNullOperator(UnaryOperator):
    pass


@unary("is_not_null")
class IsNotNullOperator(UnaryOperator):
    pass


@unary("not")
class NotOperator(UnaryOperator):
    pass


@binary("eq")
class EqOperator(BinaryOperator):
    pass


@binary("ne")
class NeOperator(BinaryOperator):
    pass


@binary("lt")
class LtOperator(BinaryOperator):
    pass


@binary("lte")
class LteOperator(BinaryOperator):
    pass


@binary("gt")
class GtOperator(BinaryOperator):
    pass


@binary("gte")
class GteOperator(BinaryOperator):
    pass


@binary("contains")
class ContainsOperator(BinaryOperator):
    pass


@binary("not_contains")
class NotContainsOperator(BinaryOperator):
    pass


@binary("starts_with")
class StartsWithOperator(BinaryOperator):
    pass


@binary("ends_with")
class EndsWithOperator(BinaryOperator):
    pass


@binary("matches")
class MatchesOperator(BinaryOperator):
    pass


@binary("is_in")
class IsInOperator(BinaryOperator):
    pass


@binary("is_not_in")
class IsNotInOperator(BinaryOperator):
    pass
