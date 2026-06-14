# goroba/business-rules

A Python library for declarative business rules: define conditions with typed operands, store rules in multiple formats, and run them through an engine with a pluggable context.

The typical workflow is **define → store → run**: build a `BusinessRule`, persist it with a converter if needed, register variables/functions/actions on an `Engine`, then call `engine.run(rule)`.

## Business rule

A **business rule** decides whether a situation matches a policy and what to do next. It has four parts:

### Example: premium access

The rule below grants premium access when a user is an adult with an active account, a valid email, either a premium tier or a non-suspended account, and a region on the allowed list.

```python
from business_rules.business_rule import BusinessRule
from business_rules.condition import (
    BinaryCondition,
    Conjunction,
    Disjunction,
    NegatedCondition,
    UnaryCondition,
)
from business_rules.executable import Action
from business_rules.operand import Function, Literal, Variable
from business_rules.operators import (
    EqOperator,
    GteOperator,
    IsInOperator,
    IsNotNullOperator,
)

premium_access_rule = BusinessRule(
    having=Conjunction(
        all=(
            Conjunction(
                all=(
                    BinaryCondition(
                        left=Variable("age"),
                        operator=GteOperator,
                        right=Literal("18"),
                    ),
                    BinaryCondition(
                        left=Variable("status"),
                        operator=EqOperator,
                        right=Literal("active"),
                    ),
                    UnaryCondition(
                        operand=Variable("email"),
                        operator=IsNotNullOperator,
                    ),
                )
            ),
            Disjunction(
                any=(
                    BinaryCondition(
                        left=Variable("tier"),
                        operator=EqOperator,
                        right=Literal("premium"),
                    ),
                    NegatedCondition(
                        negative=BinaryCondition(
                            left=Variable("is_suspended"),
                            operator=EqOperator,
                            right=Literal("true"),
                        )
                    ),
                )
            ),
            BinaryCondition(
                left=Variable("region"),
                operator=IsInOperator,
                right=Function(name="allowed_regions", args=("premium",)),
            ),
        )
    ),
    on_success=[Action(name="grant_access")],
    on_failure=[Action(name="reject_access")],
    on_finally=[Action(name="audit_log")],
)
```

This example uses conjunction (logical `and`), disjunction (logical `or`), negation (logical `not`), unary and binary conditions, variables, literals, functions, and defines a list of actions for any outcome.

## Business Rule Builder

The builder offers a fluent API to construct rules without nested dataclasses out of the box. Let's create the same rule with premium access:

```python
from business_rules.builder import binary, function, get_builder, variable

premium_access_rule = (
    get_builder()
    .having()
    .all()
        .all()
            .binary(variable("age"), "gte", "18")
            .binary(variable("status"), "eq", "active")
            .unary(variable("email"), "is_not_null")
        .end()
        .any()
            .binary(variable("tier"), "eq", "premium")
            .negative(binary(variable("is_suspended"), "eq", "true"))
        .end()
        .binary(
            variable("region"),
            "is_in",
            function("allowed_regions", args=("premium",)),
        )
    .end()
    .on_success()
        .action("grant_access")
    .end()
    .on_failure()
        .action("reject_access")
    .end()
    .on_finally()
        .action("audit_log")
    .end()
    .build()
)
```

Helper factories `variable()`, `literal()`, `function()`, `binary()`, and `unary()` are also available for building conditions outside the builder.

## Building blocks

At the highest level business rule consists of three lifecycle blocks: 

| Part | Role |
|---|---|
| `having` | The condition that must be evaluated (required) |
| `on_success` | Actions to run when `having` is true |
| `on_failure` | Actions to run when `having` is false |
| `on_finally` | Actions to run after success or failure |

The condition block `having` is the only required block, the others are optional, so that you can avoid any specific behaviour, just checking some custom conditions of varying degrees of complexity.

### Conditions

Conditions are combined to form the `having` expression:

- **`all`** — conjunction: every child condition must be true
- **`any`** — disjunction: at least one child condition must be true
- **`negative`** — negation: inverts a child condition
- **`unary`** — one operand and one operator (e.g. `email` `is_not_null`)
- **`binary`** — left operand, operator, right operand (e.g. `age` `gte` `18`)

### Operands

Operands are the values that conditions compare:

- **`variable`** — a named value resolved from the engine context at runtime
- **`literal`** — a string constant embedded in the rule (e.g. `"active"`, `"18"`)
- **`function`** — a named callable resolved from the engine context, optionally with arguments

Literals live inside the rule definition. Variables and functions are registered on the engine context (see below).

## Engine and context

The **engine** is the environment and the entry point for running rules. It owns its global **context** — a registry of callable entries the rule can reference by name.

Context entries fall into three kinds:

| Kind | Purpose | Declares `data_type` |
|---|---|---|
| **variable** | Read a runtime value | Yes |
| **function** | Compute a value used in conditions | Yes |
| **action** | Perform a side effect in lifecycle blocks | Yes |

Register entries on the global context with engine decorators:

```python
from business_rules.engine import Engine

engine = Engine()

@engine.variable("age", data_type="integer")
def age() -> int:
    return 25

@engine.variable("status", data_type="string")
def status() -> str:
    return "active"

@engine.function("allowed_regions", data_type="string")
def allowed_regions(tier: str) -> tuple[str, ...]:
    return ("US", "EU", "UK") if tier == "premium" else ("US",)

@engine.action("grant_access", data_type="boolean")
def grant_access() -> bool:
    print("access granted")
    return True
```

You can also register entries programmatically via `engine.context.register_variable(...)`, `register_function(...)`, and `register_action(...)`.

Names are normalized to **snake_case** by default (`userAge` resolves as `user_age`). See [Name normalizers](docs/name-normalizers.md) for built-in options and custom normalizers.

### Running a rule

You can **run** (execute) rule or only **check** the condition.

Call `engine.check(rule)` to evaluate only the `having` condition:


```python
passed = engine.check(premium_access_rule)
```

Call `engine.run(rule)` when you also need lifecycle actions. It evaluates the condition the same way as `check`, then runs `on_success`, `on_failure`, and `on_finally` as appropriate.

```python
passed = engine.run(premium_access_rule)
```

On success, `on_success` actions run; on failure, `on_failure` actions run. `on_finally` actions always run last.

### Local context

A **local context** is an independent `Context` instance passed when running a rule. It overrides entries from the global context. When a name is not found locally, the engine falls back to the global context.

`local_context` is attached to the engine's global context only for the duration of a single `run()` or `check()` call. After execution completes, the global context no longer references it.

```python
from business_rules.context import Context

local = Context()

@local.variable("status", data_type="string")
def status_override() -> str:
    return "inactive"

passed = engine.check(premium_access_rule, local_context=local)
passed = engine.run(premium_access_rule, local_context=local)
```

### Nested contexts

Contexts can be composed with `nests(inner)`, which links an inner context into an outer one. During resolution the engine walks **innermost first**, then each outer wrapper, then the global context.

```python
from business_rules.context import Context

action_context = Context()
data_context = Context()

action_context.nests(data_context)

engine.run(rule, local_context=action_context)
```

Fluent chaining builds deeper stacks:

```python
engine.run(
    rule,
    local_context=grandparent_context.nests(
        parent_context.nests(child_context)
    ),
)
```

Each engine's `run()` / `check()` call scopes `local_context` onto its global context for that execution only. Nesting you configure on your own contexts (e.g. `action_context.nests(data_context)`) persists and can be reused across calls.

### Object context

When your runtime data already lives on a plain object, `ObjectContext` wraps that instance and exposes its attributes as context entries without manual registration. Objects could contain properties and methods that would be treated as variables and functions/actions in terms of context.

#### Recommended: split data and action contexts

The recommended approach when rules run against a domain object:

- **`User`** — data attributes plus **domain helpers** on the object (e.g. `is_adult()`), exposed by `ObjectContext` as **functions**
- **`data_context`** — `ObjectContext(user)` supplies **variables** (attributes) and **object methods** used in conditions
- **`action_context`** — standalone **functions** (`allowed_regions`) and **lifecycle actions** (`grant_access`, etc.) that are not on the user object
- Lifecycle actions receive the runtime user through `target()`; nest with `action_context.nests(data_context)`

Domain helpers stay on the user; cross-cutting rule functions and lifecycle handlers stay on `action_context`. During `run()`, resolution walks **data (inner) → action (outer) → engine global** (see [Nested contexts](#nested-contexts) above).

```python
from dataclasses import dataclass

from business_rules.builder import binary, function, get_builder, target, variable
from business_rules.context import Context, ObjectContext
from business_rules.engine import Engine

@dataclass
class User:
    age: int = 25
    status: str = "active"
    email: str = "user@example.com"
    tier: str = "premium"
    is_suspended: bool = False
    region: str = "US"

    def is_adult(self) -> bool:
        return self.age >= 18

user = User()

data_context = ObjectContext(
    user,
    data_types={"is_suspended": "boolean"},
)

action_context = Context()

@action_context.function("allowed_regions", data_type="string")
def allowed_regions(tier: str) -> tuple[str, ...]:
    return ("US", "EU", "UK") if tier == "premium" else ("US",)

@action_context.action("grant_access", data_type="boolean")
def grant_access(user: User) -> bool:
    print(f"access granted for {user.email}")
    return True

@action_context.action("reject_access", data_type="boolean")
def reject_access(user: User) -> bool:
    print(f"access rejected for {user.email}")
    return False

@action_context.action("audit_log", data_type="boolean")
def audit_log(user: User) -> bool:
    print(f"audit: {user.email}")
    return True

action_context.nests(data_context)

premium_access_rule = (
    get_builder()
    .having()
    .all()
        .all()
            .binary(function("is_adult"), "eq", "true")
            .binary(variable("status"), "eq", "active")
            .unary(variable("email"), "is_not_null")
        .end()
        .any()
            .binary(variable("tier"), "eq", "premium")
            .negative(binary(variable("is_suspended"), "eq", "true"))
        .end()
        .binary(
            variable("region"),
            "is_in",
            function("allowed_regions", args=("premium",)),
        )
    .end()
    .on_success()
        .action("grant_access", args=(target(),))
    .end()
    .on_failure()
        .action("reject_access", args=(target(),))
    .end()
    .on_finally()
        .action("audit_log", args=(target(),))
    .end()
    .build()
)

engine = Engine()

passed = engine.run(
    premium_access_rule,
    local_context=action_context,
    target=user,
)
```

Lifecycle actions in the rule must pass `target()` so the handler receives the user. In the example above, `function("is_adult")` resolves from the **data** context (`user.is_adult` via `ObjectContext`), while `allowed_regions` and the lifecycle handlers come from **action** context.

#### `ObjectContext` mapping rules

| Instance member | Context kind |
|---|---|
| Non-callable attribute or property | **variable** |
| Public method (no leading `_`) | **action** and **function** |

In the recommended pattern, attributes become **variables** on `data_context`; public methods on the user (e.g. `is_adult`) are available as **functions** there. Register cross-cutting rule functions and lifecycle actions on `action_context` instead of as side-effect methods on the user.

Member names on the wrapped object are normalized under the hood using the context's name normalizer (snake_case by default), the same way names in the business rule are. You do not need to match naming conventions between the object and the rule — for example, an attribute `userAge` on the object matches `Variable("user_age")` in the rule. Pass the same `name_normalizer` as the engine when you use a custom one.

`data_type` is inferred from Python type hints on attributes. Use `data_types` only where needed — for example to override a specific entry such as `is_suspended`.

Names not found on the wrapped instance still fall back to the engine's global context, same as a regular local context.

## Data types and operators

Operands in conditions are strings at rest. **Data types** cast those strings to typed Python values and **operators** compare them at evaluation time. Each variable and function declares which data type it returns.

### Built-in data types

| Type | Name | Operators |
|---|---|---|
| String | `string` | `eq`, `ne`, `lt`, `lte`, `gt`, `gte`, `contains`, `not_contains`, `starts_with`, `ends_with`, `matches`, `is_in`, `is_not_in`, `is_null`, `is_not_null` |
| Integer | `integer` | `eq`, `ne`, `lt`, `lte`, `gt`, `gte`, `is_in`, `is_not_in`, `is_null`, `is_not_null` |
| Decimal | `decimal` | `eq`, `ne`, `lt`, `lte`, `gt`, `gte`, `is_in`, `is_not_in`, `is_null`, `is_not_null` |
| Boolean | `boolean` | `eq`, `ne`, `is_null`, `is_not_null` |
| Date | `date` | `eq`, `ne`, `lt`, `lte`, `gt`, `gte`, `is_in`, `is_not_in`, `is_null`, `is_not_null` |
| DateTime | `datetime` | `eq`, `ne`, `lt`, `lte`, `gt`, `gte`, `is_in`, `is_not_in`, `is_null`, `is_not_null` |

### Built-in operators

| Kind | Names |
|---|---|
| Unary | `is_null`, `is_not_null` |
| Binary | `eq`, `ne`, `lt`, `lte`, `gt`, `gte`, `contains`, `not_contains`, `starts_with`, `ends_with`, `matches`, `is_in`, `is_not_in` |

You can add your own data types and operators. See [Creating a custom data type](docs/creating-a-data-type.md) for a full walkthrough.

## Converters

A **converter** converts a business rule to some external representation and back. It implement `load` and `dump` methods to load business rule from some data format and dump it back.

Built-in converters:

- **`DictConverter`** — Python `dict`
- **`JsonConverter`** — JSON string (wraps `DictConverter`)

Having the eligibility rule from the [recommended ObjectContext pattern](#object-context) above (with `target()` in lifecycle actions), you can serialize it to a dict or JSON:

```python
from business_rules.converters import DictConverter, JsonConverter

payload = DictConverter().dump(premium_access_rule)
json_text = JsonConverter().dump(premium_access_rule)
```

Now you have a dumped dict of such a shape (abbreviated):

```python
{
    "having": {
        "type": "all",
        "conditions": [
            {
                "type": "all",
                "conditions": [
                    {
                        "type": "binary",
                        "left": {
                            "type": "function",
                            "name": "is_adult",
                            "args": [],
                            "kwargs": {},
                        },
                        "operator": "eq",
                        "right": {"type": "literal", "value": "true"},
                    },
                    # ...
                ],
            },
            {
                "type": "any",
                "conditions": [
                    # ...
                ],
            },
            {
                "type": "binary",
                "left": {"type": "variable", "name": "region"},
                "operator": "is_in",
                "right": {
                    "type": "function",
                    "name": "allowed_regions",
                    "args": ["premium"],
                    "kwargs": {},
                },
            },
        ],
    },
    "on_success": [
        {
            "type": "action",
            "name": "grant_access",
            "args": [{"type": "target"}],
            "kwargs": {},
        }
    ],
    "on_failure": [
        {
            "type": "action",
            "name": "reject_access",
            "args": [{"type": "target"}],
            "kwargs": {},
        }
    ],
    "on_finally": [
        {
            "type": "action",
            "name": "audit_log",
            "args": [{"type": "target"}],
            "kwargs": {},
        }
    ],
}
```

`{"type": "target"}` means the action receives the runtime object passed to `engine.run(..., target=...)`. The full serialized shape is shown in [Creating a custom converter](docs/creating-a-converter.md).

Load a rule back from the stored data:

```python
rule = DictConverter().load(payload)
rule = JsonConverter().load(json_text)

engine.run(rule, local_context=action_context, target=user)
```

To support a custom storage format, implement your own converter. See [Creating a custom converter](docs/creating-a-converter.md).

## Documentation

- [Setup](docs/setup.md)
- [Development](docs/development.md)
- [Creating a custom data type](docs/creating-a-data-type.md)
- [Creating a custom converter](docs/creating-a-converter.md)
- [Name normalizers](docs/name-normalizers.md)
