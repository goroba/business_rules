import pytest

from business_rules.data_types import DataType, data_type
from business_rules.data_types.base import DataType as BaseDataType


@data_type("sample")
class SampleDataType(DataType[str]):
    def do_cast(self, value: str) -> str:
        return value

    def __str__(self, value: str) -> str:  # type: ignore[override]
        return value


class CastOnlyDataType(DataType[str]):
    def do_cast(self, value: str) -> str:
        return value


class StrOnlyDataType(DataType[str]):
    def __str__(self, value: str) -> str:  # type: ignore[override]
        return value


def test_data_type_cannot_be_instantiated() -> None:
    with pytest.raises(TypeError):
        BaseDataType()  # type: ignore[abstract]


def test_incomplete_subclass_missing_str_cannot_be_instantiated() -> None:
    with pytest.raises(TypeError):
        CastOnlyDataType()  # type: ignore[abstract]


def test_incomplete_subclass_missing_do_cast_cannot_be_instantiated() -> None:
    with pytest.raises(TypeError):
        StrOnlyDataType()  # type: ignore[abstract]


def test_sample_data_type() -> None:
    sample = SampleDataType()
    assert sample.cast("hello") == "hello"
    assert sample.__str__("hello") == "hello"
    assert sample.__bool__("hello") is True
    assert sample.__bool__("") is False
    assert sample.operators == frozenset()
    with pytest.raises(NotImplementedError):
        sample.apply("eq", "a", "b")
