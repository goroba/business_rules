from abc import ABC

from business_rules.executable import Action, Executable


def test_executable_is_abstract() -> None:
    assert issubclass(Executable, ABC)


def test_executable_hierarchy() -> None:
    assert issubclass(Action, Executable)
