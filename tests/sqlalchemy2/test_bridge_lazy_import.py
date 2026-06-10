import importlib
import sys
from unittest.mock import patch

import pytest

from business_rules.bridges import SQLAlchemyRuleBridge


def test_lazy_import_returns_bridge_class() -> None:
    assert SQLAlchemyRuleBridge.__name__ == "SQLAlchemyRuleBridge"


def test_getattr_raises_for_unknown_attribute() -> None:
    import business_rules.bridges as bridges

    with pytest.raises(AttributeError, match="has no attribute 'unknown'"):
        _ = bridges.unknown


def test_lazy_import_raises_helpful_error_when_sqlalchemy_missing() -> None:
    for module_name in (
        "business_rules.bridges",
        "business_rules.bridges.sqlalchemy2",
        "business_rules.bridges.sqlalchemy2.bridge",
    ):
        sys.modules.pop(module_name, None)

    with (
        patch("importlib.util.find_spec", return_value=None),
        pytest.raises(ImportError, match="business-rules\\[sqlalchemy2\\]"),
    ):
        bridges = importlib.reload(importlib.import_module("business_rules.bridges"))
        _ = bridges.SQLAlchemyRuleBridge
