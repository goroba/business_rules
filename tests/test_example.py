from business_rules.example import greet


def test_greet() -> None:
    assert greet("world") == "Hello, world!"
