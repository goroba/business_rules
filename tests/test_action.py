from business_rules.executable import Action
from business_rules.operand import Value, Variable


def test_action() -> None:
    action = Action(
        name="notify",
        args=(Variable("user_id"), Value("sent")),
        kwargs={"channel": Value("email")},
    )
    assert action.name == "notify"
    assert action.args == (Variable("user_id"), Value("sent"))
    assert action.kwargs == {"channel": Value("email")}


def test_action_defaults() -> None:
    action = Action(name="noop")
    assert action.args == ()
    assert action.kwargs == {}
