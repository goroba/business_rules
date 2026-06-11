from business_rules.verifiable import Verifiable


def test_verifiable_is_abstract() -> None:
    assert issubclass(Verifiable, object)
