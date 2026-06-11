from business_rules.executable import Action, Executable, Function
from business_rules.operand import Value, Variable


def test_executable_hierarchy() -> None:
    assert issubclass(Action, Executable)
    assert issubclass(Function, Executable)


def test_function() -> None:
    function = Function(
        name="sum",
        args=(Variable("a"), Variable("b")),
        kwargs={"precision": Value("2")},
    )
    assert function.name == "sum"
    assert function.args == (Variable("a"), Variable("b"))
    assert function.kwargs == {"precision": Value("2")}


def test_function_defaults() -> None:
    function = Function(name="noop")
    assert function.args == ()
    assert function.kwargs == {}
