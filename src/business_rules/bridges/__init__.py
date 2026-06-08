import importlib
from typing import Any

__all__ = ["SQLAlchemyRuleBridge"]

_SUBMODULES = frozenset({"sqlalchemy2"})


def __getattr__(name: str) -> Any:
    if name == "SQLAlchemyRuleBridge":
        try:
            from .sqlalchemy2.bridge import SQLAlchemyRuleBridge

            return SQLAlchemyRuleBridge
        except ImportError as exc:
            raise ImportError(
                "SQLAlchemyRuleBridge requires the 'sqlalchemy' package. "
                "Install it with: pip install business-rules[sqlalchemy2]"
            ) from exc

    if name in _SUBMODULES:
        return importlib.import_module(f"{__name__}.{name}")

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
