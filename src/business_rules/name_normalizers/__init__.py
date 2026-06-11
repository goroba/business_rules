"""Name normalizers for business rules."""

from business_rules.name_normalizers import builtin  # noqa: F401
from business_rules.name_normalizers.base import NameNormalizer
from business_rules.name_normalizers.builtin import (
    CamelCaseNameNormalizer,
    KebabCaseNameNormalizer,
    PascalCaseNameNormalizer,
    ScreamingSnakeCaseNameNormalizer,
    SnakeCaseNameNormalizer,
    TrainCaseNameNormalizer,
)

__all__ = [
    "CamelCaseNameNormalizer",
    "KebabCaseNameNormalizer",
    "NameNormalizer",
    "PascalCaseNameNormalizer",
    "ScreamingSnakeCaseNameNormalizer",
    "SnakeCaseNameNormalizer",
    "TrainCaseNameNormalizer",
]
