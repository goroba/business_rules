"""SQLAlchemy 2.x integration for business-rules."""

from importlib.util import find_spec

if find_spec("sqlalchemy") is None:
    raise ImportError(
        "The business-rules SQLAlchemy 2.x bridge requires SQLAlchemy. "
        "Install it with: pip install business-rules[sqlalchemy2]"
    )

__all__: list[str] = []
