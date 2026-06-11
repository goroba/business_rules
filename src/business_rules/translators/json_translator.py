"""JSON-based translator for business rules."""

from __future__ import annotations

import json

from business_rules.business_rule import BusinessRule
from business_rules.translators.base import Translator
from business_rules.translators.dict_translator import DictTranslator

__all__ = ["JsonTranslator"]


class JsonTranslator(Translator[str]):
    def __init__(self, *, dict_translator: DictTranslator | None = None) -> None:
        self._dict = dict_translator or DictTranslator()

    def load(self, source: str) -> BusinessRule:
        return self._dict.load(json.loads(source))

    def dump(self, business_rule: BusinessRule) -> str:
        return json.dumps(self._dict.dump(business_rule))
