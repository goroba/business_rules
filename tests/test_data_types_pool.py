import pytest

from business_rules.data_types import (
    DataType,
    DataTypeGuesserPool,
    DataTypesPool,
    IntegerDataType,
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

            def guess(self, value: str) -> bool:
                return True

            def __str__(self, value: str) -> str:  # type: ignore[override]
                return value


def test_register_rejects_duplicate_name() -> None:
    with pytest.raises(ValueError, match="already registered"):

        @data_type("string")
        class DuplicateStringDataType(DataType[str]):
            def do_cast(self, value: str) -> str:
                return value

            def guess(self, value: str) -> bool:
                return True

            def __str__(self, value: str) -> str:  # type: ignore[override]
                return value


def test_data_type_rejects_multiple_guesser_placements() -> None:
    with pytest.raises(ValueError, match="Only one guesser placement"):

        @data_type("multi_placement", guesser_top=True, guesser_bottom=True)
        class MultiPlacementDataType(DataType[str]):
            def do_cast(self, value: str) -> str:
                return value

            def guess(self, value: str) -> bool:
                return True

            def __str__(self, value: str) -> str:  # type: ignore[override]
                return value


def test_data_type_rejects_unknown_guesser_anchor() -> None:
    with pytest.raises(ValueError, match="not registered"):

        @data_type("bad_anchor", guesser_before="unknown_type")
        class BadAnchorDataType(DataType[str]):
            def do_cast(self, value: str) -> str:
                return value

            def guess(self, value: str) -> bool:
                return True

            def __str__(self, value: str) -> str:  # type: ignore[override]
                return value


def test_data_type_rejects_guesser_anchor_not_in_pool() -> None:
    with pytest.raises(ValueError, match="not registered in DataTypeGuesserPool"):

        @data_type("pool_only", guesser_before="sample")
        class PoolOnlyDataType(DataType[str]):
            def do_cast(self, value: str) -> str:
                return value

            def guess(self, value: str) -> bool:
                return True

            def __str__(self, value: str) -> str:  # type: ignore[override]
                return value


def test_data_type_guesser_top_registers_in_pool() -> None:
    @data_type("guesser_top_type", guesser_top=True)
    class GuesserTopDataType(DataType[str]):
        def do_cast(self, value: str) -> str:
            return value

        def guess(self, value: str) -> bool:
            return value == "top"

        def __str__(self, value: str) -> str:  # type: ignore[override]
            return value

    assert DataTypeGuesserPool.ordered()[0] is GuesserTopDataType
    DataTypeGuesserPool._ordered.remove(GuesserTopDataType)


def test_data_type_guesser_after_registers_in_pool() -> None:
    @data_type("guesser_after_type", guesser_after="integer")
    class GuesserAfterDataType(DataType[str]):
        def do_cast(self, value: str) -> str:
            return value

        def guess(self, value: str) -> bool:
            return True

        def __str__(self, value: str) -> str:  # type: ignore[override]
            return value

    ordered = DataTypeGuesserPool.ordered()
    integer_index = ordered.index(IntegerDataType)
    assert ordered[integer_index + 1] is GuesserAfterDataType
    DataTypeGuesserPool._ordered.remove(GuesserAfterDataType)
