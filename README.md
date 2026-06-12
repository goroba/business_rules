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

This example uses conjunction (logial `and`), disjunction (logical `or`), negation(logical `not`), unary and binary conditions, variables, literals, functions, and defines a list of actions for any outcome.

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

The **engine** is the environment and the entry point for running rules. It owns it's global **context** — a registry of callable entries the rule can reference by name.

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

### Local context

A **local context** is an independant `Context` instance passed when running a rule. It overrides entries from the global context. When a name is not found locally, the engine falls back to the global context.

```python
from business_rules.context import Context

local = Context()

@local.variable("status", data_type="string")
def status_override() -> str:
    return "inactive"
```

### Lazy context

When your runtime data already lives on a plain object, `LazyContext` wraps that instance and exposes it as a local context without manual registration. Entries are resolved **lazily** on first use during rule evaluation.

```python
from business_rules.context import LazyContext

class User:
    age: int
    status: str
    email: str
    tier: str
    is_suspended: bool
    region: str

    def __init__(self) -> None:
        self.age = 25
        self.status = "active"
        self.email = "user@example.com"
        self.tier = "premium"
        self.is_suspended = False
        self.region = "US"

    def allowed_regions(self, tier: str) -> tuple[str, ...]:
        return ("US", "EU", "UK") if tier == "premium" else ("US",)

    def grant_access(self) -> bool: ...
    def reject_access(self) -> bool: ...
    def audit_log(self) -> bool: ...

user = User()
proxy_context = LazyContext(
    user,
    data_types={
        "allowed_regions": "string",
        "is_suspended": "boolean",
    },
)

passed = engine.run(premium_access_rule, local_context=proxy_context)
```

Mapping rules:

| Instance member | Context kind |
|---|---|
| Non-callable attribute or property | **variable** |
| Public method (no leading `_`) | **action** and **function** |

Member names on the wrapped object are normalized under the hood using the context's name normalizer (snake_case by default), the same way names in the business rule are. You do not need to match naming conventions between the object and the rule — for example, an attribute `userAge` on the object matches `Variable("user_age")` in the rule. Pass the same `name_normalizer` as the engine when you use a custom one.

`data_type` is inferred from Python type hints and return annotations for the rest. Use `data_types` only where needed — for example `allowed_regions`, whose return type is not a built-in rule data type, or to override a specific entry such as `is_suspended`.

Names not found on the wrapped instance still fall back to the engine's global context, same as a regular local context.

## Running a rule

Call `engine.check(rule)` to evaluate only the `having` condition.

```python
passed = engine.check(premium_access_rule)
passed = engine.check(premium_access_rule, local_context=local)
```

Call `engine.run(rule)` when you also need lifecycle actions. It evaluates the condition the same way as `check`, then runs `on_success`, `on_failure`, and `on_finally` as appropriate.

**Without local context** — all names resolve against the engine's global context:

```python
passed = engine.run(premium_access_rule)
```

**With local context** — local entries override global ones; missing names fall back to the global context:

```python
passed = engine.run(premium_access_rule, local_context=local)
```

On success, `on_success` actions run; on failure, `on_failure` actions run. `on_finally` actions always run last.

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

Having the previously created rul you can serialize it to a dict or json:

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
                        "left": {"type": "variable", "name": "age"},
                        "operator": "gte",
                        "right": {"type": "literal", "value": "18"},
                    },
                    # ...
                ],
            },
            {
                "type": "any",
                "conditions": [
                    {
                        "type": "binary",
                        "left": {"type": "variable", "name": "tier"},
                        "operator": "eq",
                        "right": {"type": "literal", "value": "premium"},
                    },
                    {
                        "type": "negative",
                        "condition": {
                            "type": "binary",
                            "left": {"type": "variable", "name": "is_suspended"},
                            "operator": "eq",
                            "right": {"type": "literal", "value": "true"},
                        },
                    },
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
    "on_success": [{"type": "action", "name": "grant_access", "args": [], "kwargs": {}}],
    "on_failure": [{"type": "action", "name": "reject_access", "args": [], "kwargs": {}}],
    "on_finally": [{"type": "action", "name": "audit_log", "args": [], "kwargs": {}}],
}
```

Load a rule back from the stored data:

```python
rule = DictConverter().load(payload)
rule = JsonConverter().load(json_text)
```

To support a custom storage format, implement your own converter. See [Creating a custom converter](docs/creating-a-converter.md).

## Documentation

- [Setup](docs/setup.md)
- [Development](docs/development.md)
- [Creating a custom data type](docs/creating-a-data-type.md)
- [Creating a custom converter](docs/creating-a-converter.md)
- [Name normalizers](docs/name-normalizers.md)
