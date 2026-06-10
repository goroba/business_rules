import importlib
import sys
from unittest.mock import patch

import pytest

from bridges import SQLAlchemyRuleBridge


def test_lazy_import_returns_bridge_class() -> None:
    assert SQLAlchemyRuleBridge.__name__ == "SQLAlchemyRuleBridge"


def test_getattr_raises_for_unknown_attribute() -> None:
    import bridges as bridges_module

    with pytest.raises(AttributeError, match="has no attribute 'unknown'"):
        _ = bridges_module.unknown


def test_submodule_lazy_import_via_getattr() -> None:
    for module_name in ("bridges.sqlalchemy2", "bridges.sqlalchemy2.bridge"):
        sys.modules.pop(module_name, None)
    bridges_module = importlib.reload(importlib.import_module("bridges"))
    bridges_module.__dict__.pop("sqlalchemy2", None)
    sqlalchemy2 = bridges_module.sqlalchemy2
    assert sqlalchemy2.__name__ == "bridges.sqlalchemy2"


def test_lazy_import_raises_helpful_error_when_sqlalchemy_missing() -> None:
    for module_name in (
        "bridges",
        "bridges.sqlalchemy2",
        "bridges.sqlalchemy2.bridge",
    ):
        sys.modules.pop(module_name, None)

    with (
        patch("importlib.util.find_spec", return_value=None),
        pytest.raises(ImportError, match="business-rules\\[sqlalchemy2\\]"),
    ):
        bridges_module = importlib.reload(importlib.import_module("bridges"))
        _ = bridges_module.SQLAlchemyRuleBridge
