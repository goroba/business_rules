"""Shared word splitting for name normalizers."""

from __future__ import annotations

import re

__all__ = ["split_words"]


def split_words(name: str) -> list[str]:
    if not name:
        raise ValueError("Name must not be empty")

    normalized = re.sub(r"[-_\s]+", " ", name)
    normalized = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", normalized)
    normalized = re.sub(r"(?<=[A-Z])(?=[A-Z][a-z])", " ", normalized)

    words = [word.lower() for word in normalized.split() if word]
    if not words:
        raise ValueError("Name must not be empty")
    return words
