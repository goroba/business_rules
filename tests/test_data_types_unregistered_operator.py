import pytest

from business_rules.data_types import DataType
from business_rules.operators import implements
from business_rules.operators.implements import IMPLEMENTS_OPERATOR_NAME


def test_data_type_rejects_unregistered_operator() -> None:
    with pytest.raises(ValueError, match="not registered"):

        class BadDataType(DataType[str]):
            def cast(self, value: str) -> str:
                return value

            def __str__(self, value: str) -> str:  # type: ignore[override]
                return value

            @implements("not_registered")
            def not_registered(self, value: str) -> bool:
                return True


def test_data_type_rejects_non_string_operator_name() -> None:
    def bad_method(self: object, value: str) -> bool:
        return True

    setattr(bad_method, IMPLEMENTS_OPERATOR_NAME, 123)

    with pytest.raises(TypeError, match="must be a string"):

        class BadNameDataType(DataType[str]):
            def cast(self, value: str) -> str:
                return value

            def __str__(self, value: str) -> str:  # type: ignore[override]
                return value

            bad = bad_method
