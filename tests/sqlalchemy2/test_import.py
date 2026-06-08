import business_rules.bridges.sqlalchemy2
from business_rules.bridges import SQLAlchemyRuleBridge


def test_lazy_import_succeeds_when_sqlalchemy_installed() -> None:
    assert SQLAlchemyRuleBridge.__name__ == "SQLAlchemyRuleBridge"


def test_submodule_import_succeeds_when_sqlalchemy_installed() -> None:
    assert business_rules.bridges.sqlalchemy2.__all__ == []
