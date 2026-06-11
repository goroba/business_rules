# Creating a custom data type: Money

This guide shows how to add a **Money** data type with string values like `1.08 USD`, comparison operators, a custom `approx` operator (±5 cents), and automatic type detection.

You need three pieces:

1. A **value class** — what the data type holds (`Money`)
2. An **operator** (optional) — register new operators before using them (`approx`)
3. A **data type class** — parse strings, detect literals, and implement operators (`MoneyDataType`)

## Step 1 — Define the value class

```python
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class Currency(str, Enum):
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"


@dataclass(frozen=True, slots=True)
class Money:
    amount: Decimal
    currency: Currency
```

## Step 2 — Register a custom operator (if needed)

If you need an operator that does not exist yet, register it first:

```python
from business_rules.operators import BinaryOperator, binary

@binary("approx")
class ApproxOperator(BinaryOperator):
    pass
```

Built-in operators you can use without registering: `eq`, `ne`, `lt`, `lte`, `gt`, `gte`, `is_in`, `is_not_in`, `is_null`, `is_not_null`, and string operators (`contains`, `starts_with`, etc.).

## Step 3 — Implement the data type

Subclass `DataType[Money]`, decorate with `@data_type`, and wire up operators with `@implements`:

```python
import re
from collections.abc import Collection
from decimal import Decimal, InvalidOperation

from business_rules.data_types import DataType, data_type
from business_rules.operators import implements

_MONEY_PATTERN = re.compile(
    r"^\s*(?P<amount>-?\d+(?:\.\d+)?)\s+(?P<currency>[A-Z]{3})\s*$"
)
_TOLERANCE = Decimal("0.05")


@data_type("money", guesser_top=True)
class MoneyDataType(DataType[Money]):
    def do_cast(self, value: str) -> Money:
        match = _MONEY_PATTERN.fullmatch(value)
        if match is None:
            raise ValueError(f"Invalid money value: {value!r}")
        amount = Decimal(match.group("amount"))
        currency = Currency(match.group("currency"))
        return Money(amount=amount, currency=currency)

    def guess(self, value: str) -> bool:
        return _MONEY_PATTERN.fullmatch(value) is not None

    def __str__(self, value: Money) -> str:  # type: ignore[override]
        return f"{format(value.amount, 'f')} {value.currency.value}"

    @implements("is_null")
    def is_null(self, value: Money | None) -> bool:
        return value is None

    @implements("is_not_null")
    def is_not_null(self, value: Money | None) -> bool:
        return value is not None

    @implements("eq")
    def eq(self, left: Money, right: Money) -> bool:
        return left.currency == right.currency and left.amount == right.amount

    @implements("ne")
    def ne(self, left: Money, right: Money) -> bool:
        return not self.eq(left, right)

    @implements("lt")
    def lt(self, left: Money, right: Money) -> bool:
        return left.currency == right.currency and left.amount < right.amount

    @implements("lte")
    def lte(self, left: Money, right: Money) -> bool:
        return left.currency == right.currency and left.amount <= right.amount

    @implements("gt")
    def gt(self, left: Money, right: Money) -> bool:
        return left.currency == right.currency and left.amount > right.amount

    @implements("gte")
    def gte(self, left: Money, right: Money) -> bool:
        return left.currency == right.currency and left.amount >= right.amount

    @implements("is_in")
    def is_in(self, left: Money, values: Collection[Money]) -> bool:
        return left in values

    @implements("is_not_in")
    def is_not_in(self, left: Money, values: Collection[Money]) -> bool:
        return left not in values

    @implements("approx")
    def approx(self, left: Money, right: Money) -> bool:
        return (
            left.currency == right.currency
            and abs(left.amount - right.amount) <= _TOLERANCE
        )
```

### What each method does

| Method | Purpose |
|---|---|
| `do_cast` | Parse a string literal into a `Money` value |
| `guess` | Return `True` when a string looks like this type |
| `__str__` | Format a `Money` value back to a string |
| `@implements("…")` | Implement an operator for this type |

### Guesser placement

Use `guesser_top=True` so `1.08 USD` is detected as money, not as a decimal or string.

Other options: `guesser_bottom`, `guesser_before="integer"`, `guesser_after="integer"`. Only one can be set.

## Step 4 — Use it in conditions

When both operands are literals, `BinaryCondition` resolves a common data type by
paired guessing: it walks guessers in priority order and picks the first type
whose `guess()` accepts both values and implements the condition operator.

```python
from business_rules.condition import BinaryCondition
from business_rules.operand import Literal
from business_rules.operators import ApproxOperator, EqOperator

# within 5 cents
BinaryCondition(
    left=Literal("10.02 USD"),
    operator=ApproxOperator,
    right=Literal("10.00 USD"),
)

# exact match
BinaryCondition(
    left=Literal("1.08 USD"),
    operator=EqOperator,
    right=Literal("1.08 USD"),
)
```

## Quick test

```python
from decimal import Decimal

from business_rules.data_types import DataTypeGuesserPool

dt = MoneyDataType()

assert dt.cast("1.08 USD") == Money(Decimal("1.08"), Currency.USD)
assert dt.approx(
    Money(Decimal("1.00"), Currency.USD),
    Money(Decimal("1.04"), Currency.USD),
) is True
assert DataTypeGuesserPool.guess("1.08 USD") is MoneyDataType
```

## Notes

- Register custom operators **before** defining the data type that uses them.
- You cannot override built-in operator or data type names.
- See `tests/test_client_extension.py` for a minimal working example with a custom `between` operator.
