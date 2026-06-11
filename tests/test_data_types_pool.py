import pytest

from business_rules.data_types import (
    DataType,
    DataTypesPool,
    StringDataType,
    data_type,
)


def test_data_types_pool_all() -> None:
    assert StringDataType in DataTypesPool.all()


def test_data_types_pool_get() -> None:
    assert DataTypesPool.get("string") is StringDataType
    assert StringDataType.name == "string"


def test_data_types_pool_get_unknown() -> None:
    with pytest.raises(KeyError, match="not registered"):
        DataTypesPool.get("unknown")


class _NotDataType:
    pass


def test_data_type_rejects_wrong_base() -> None:
    with pytest.raises(TypeError, match="DataType"):
        data_type("bad")(_NotDataType)  # type: ignore[type-var]


def test_register_rejects_empty_name() -> None:
    with pytest.raises(ValueError, match="empty"):

        @data_type("")
        class EmptyNameDataType(DataType[str]):
            def do_cast(self, value: str) -> str:
                return value

            def __str__(self, value: str) -> str:  # type: ignore[override]
                return value


def test_register_rejects_duplicate_name() -> None:
    with pytest.raises(ValueError, match="already registered"):

        @data_type("string")
        class DuplicateStringDataType(DataType[str]):
            def do_cast(self, value: str) -> str:
                return value

            def __str__(self, value: str) -> str:  # type: ignore[override]
                return value
