"""Built-in name normalizers."""

from __future__ import annotations

from business_rules.name_normalizers._words import split_words
from business_rules.name_normalizers.base import NameNormalizer

__all__ = [
    "CamelCaseNameNormalizer",
    "KebabCaseNameNormalizer",
    "PascalCaseNameNormalizer",
    "ScreamingSnakeCaseNameNormalizer",
    "SnakeCaseNameNormalizer",
    "TrainCaseNameNormalizer",
]


class SnakeCaseNameNormalizer(NameNormalizer):
    def normalize(self, name: str) -> str:
        return "_".join(split_words(name))


class CamelCaseNameNormalizer(NameNormalizer):
    def normalize(self, name: str) -> str:
        words = split_words(name)
        return words[0] + "".join(word.capitalize() for word in words[1:])


class PascalCaseNameNormalizer(NameNormalizer):
    def normalize(self, name: str) -> str:
        words = split_words(name)
        return "".join(word.capitalize() for word in words)


class KebabCaseNameNormalizer(NameNormalizer):
    def normalize(self, name: str) -> str:
        return "-".join(split_words(name))


class ScreamingSnakeCaseNameNormalizer(NameNormalizer):
    def normalize(self, name: str) -> str:
        return "_".join(word.upper() for word in split_words(name))


class TrainCaseNameNormalizer(NameNormalizer):
    def normalize(self, name: str) -> str:
        return "-".join(word.capitalize() for word in split_words(name))
