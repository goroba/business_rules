"""Context registry for variables, actions, and functions."""

from business_rules.context.base import Context, RegisteredEntry
from business_rules.context.object_context import ObjectContext

__all__ = [
    "Context",
    "ObjectContext",
    "RegisteredEntry",
]
