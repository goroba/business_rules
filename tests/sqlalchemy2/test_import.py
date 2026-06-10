import bridges.sqlalchemy2
from bridges import SQLAlchemyRuleBridge


def test_lazy_import_succeeds_when_sqlalchemy_installed() -> None:
    assert SQLAlchemyRuleBridge.__name__ == "SQLAlchemyRuleBridge"


def test_submodule_import_succeeds_when_sqlalchemy_installed() -> None:
    assert bridges.sqlalchemy2.__all__ == []
