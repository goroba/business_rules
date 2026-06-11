import pytest

from business_rules.name_normalizers import (
    CamelCaseNameNormalizer,
    KebabCaseNameNormalizer,
    NameNormalizer,
    PascalCaseNameNormalizer,
    ScreamingSnakeCaseNameNormalizer,
    SnakeCaseNameNormalizer,
    TrainCaseNameNormalizer,
)

MULTI_WORD_INPUTS = [
    "user_age",
    "userAge",
    "UserAge",
    "user-age",
    "USER_AGE",
    "User-Age",
]


@pytest.mark.parametrize(
    ("normalizer", "expected"),
    [
        (SnakeCaseNameNormalizer(), "user_age"),
        (CamelCaseNameNormalizer(), "userAge"),
        (PascalCaseNameNormalizer(), "UserAge"),
        (KebabCaseNameNormalizer(), "user-age"),
        (ScreamingSnakeCaseNameNormalizer(), "USER_AGE"),
        (TrainCaseNameNormalizer(), "User-Age"),
    ],
)
@pytest.mark.parametrize("name", MULTI_WORD_INPUTS)
def test_normalizers_accept_mixed_input_styles(
    normalizer: NameNormalizer,
    expected: str,
    name: str,
) -> None:
    assert normalizer.normalize(name) == expected


@pytest.mark.parametrize(
    ("normalizer", "expected"),
    [
        (SnakeCaseNameNormalizer(), "user"),
        (CamelCaseNameNormalizer(), "user"),
        (PascalCaseNameNormalizer(), "User"),
        (KebabCaseNameNormalizer(), "user"),
        (ScreamingSnakeCaseNameNormalizer(), "USER"),
        (TrainCaseNameNormalizer(), "User"),
    ],
)
def test_normalizers_single_word(
    normalizer: NameNormalizer,
    expected: str,
) -> None:
    assert normalizer.normalize("user") == expected
    assert normalizer.normalize("User") == expected


def test_snake_case_normalizer_handles_numbers() -> None:
    normalizer = SnakeCaseNameNormalizer()
    assert normalizer.normalize("user2Name") == "user2_name"


@pytest.mark.parametrize(
    "normalizer",
    [
        SnakeCaseNameNormalizer(),
        CamelCaseNameNormalizer(),
        PascalCaseNameNormalizer(),
        KebabCaseNameNormalizer(),
        ScreamingSnakeCaseNameNormalizer(),
        TrainCaseNameNormalizer(),
    ],
)
def test_normalizers_reject_empty_name(normalizer: NameNormalizer) -> None:
    with pytest.raises(ValueError, match="empty"):
        normalizer.normalize("")
