"""JSON-based converter for business rules."""

from __future__ import annotations

import json

from business_rules.business_rule import BusinessRule
from business_rules.converters.base import Converter
from business_rules.converters.dict_converter import DictConverter

__all__ = ["JsonConverter"]


class JsonConverter(Converter[str]):
    def __init__(self, *, dict_converter: DictConverter | None = None) -> None:
        self._dict = dict_converter or DictConverter()

    def load(self, source: str) -> BusinessRule:
        return self._dict.load(json.loads(source))

    def dump(self, business_rule: BusinessRule) -> str:
        return json.dumps(self._dict.dump(business_rule))
