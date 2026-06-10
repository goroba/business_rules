import importlib
import sys
from unittest.mock import patch

import pytest


def test_import_raises_helpful_error_when_sqlalchemy_missing() -> None:
    module_name = "bridges.sqlalchemy2"
    sys.modules.pop(module_name, None)

    with (
        patch("importlib.util.find_spec", return_value=None),
        pytest.raises(ImportError, match="business-rules\\[sqlalchemy2\\]"),
    ):
        importlib.import_module(module_name)
