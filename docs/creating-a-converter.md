# Creating a custom converter: XML

This guide shows how to create an **XML converter** that saves a `BusinessRule` as XML and loads it back.

You need two methods:

1. **`dump`** — convert a `BusinessRule` to your format
2. **`load`** — convert your format back to a `BusinessRule`

Use a converter when you want to persist rules to a file, database, or external system. See `DictConverter` and `JsonConverter` for the built-in dict and JSON equivalents.

## Step 1 — Pick your format

Decide how your storage format represents the rule. Here is the XML shape this guide uses:

```xml
<business-rule>
  <having type="all">
    <condition type="binary" operator="eq">
      <left type="function" name="is_adult"/>
      <right type="literal" value="true"/>
    </condition>
    ...
  </having>
  <on-success>
    <action name="grant_access">
      <arg type="target"/>
    </action>
  </on-success>
</business-rule>
```

Conventions:

- Use the same `type` names as the built-in dict format (`all`, `any`, `binary`, `unary`, `negative`, `variable`, `literal`, `function`, `action`, `target`, …).
- `target` appears only in action `args` / `kwargs` — not in condition operands.
- Omit empty lifecycle blocks (`on_success`, `on_failure`, `on_finally`).

## Step 2 — Implement the converter

Subclass `Converter[str]` and implement `dump` and `load`. This example uses the standard library `xml.etree.ElementTree` module.

```python
from __future__ import annotations

import json
import xml.etree.ElementTree as ET

from business_rules.business_rule import BusinessRule
from business_rules.condition import (
    BinaryCondition,
    Condition,
    Conjunction,
    Disjunction,
    NegatedCondition,
    UnaryCondition,
)
from business_rules.executable import Action
from business_rules.operand import (
    DataTypeAwareOperand,
    Function,
    Literal,
    Operand,
    Variable,
)
from business_rules.operators import builtin  # noqa: F401
from business_rules.operators.base import BinaryOperator, UnaryOperator
from business_rules.operators.pool import OperatorsPool
from business_rules.converters.base import Converter
from business_rules.target import Target


class XmlConverter(Converter[str]):
    def load(self, source: str) -> BusinessRule:
        root = ET.fromstring(source)
        if root.tag != "business-rule":
            raise ValueError(f"Expected <business-rule>, got <{root.tag}>")
        having = root.find("having")
        if having is None:
            raise ValueError("Missing <having> element")
        return BusinessRule(
            having=self._decode_condition(having),
            on_success=self._decode_actions(root.find("on-success")),
            on_failure=self._decode_actions(root.find("on-failure")),
            on_finally=self._decode_actions(root.find("on-finally")),
        )

    def dump(self, business_rule: BusinessRule) -> str:
        root = ET.Element("business-rule")
        root.append(self._encode_condition(business_rule.having, tag="having"))
        if business_rule.on_success is not None:
            root.append(self._encode_actions(business_rule.on_success, "on-success"))
        if business_rule.on_failure is not None:
            root.append(self._encode_actions(business_rule.on_failure, "on-failure"))
        if business_rule.on_finally is not None:
            root.append(self._encode_actions(business_rule.on_finally, "on-finally"))
        return ET.tostring(root, encoding="unicode", xml_declaration=True)

    def _encode_condition(
        self, condition: Condition, *, tag: str = "condition"
    ) -> ET.Element:
        if isinstance(condition, BinaryCondition):
            elem = ET.Element(tag, type="binary", operator=condition.operator.name)
            elem.append(self._encode_operand(condition.left, tag="left"))
            elem.append(self._encode_operand(condition.right, tag="right"))
            return elem
        if isinstance(condition, UnaryCondition):
            elem = ET.Element(tag, type="unary", operator=condition.operator.name)
            elem.append(self._encode_operand(condition.operand, tag="operand"))
            return elem
        if isinstance(condition, Conjunction):
            elem = ET.Element(tag, type="all")
            for child in condition.all:
                elem.append(self._encode_condition(child))
            return elem
        if isinstance(condition, Disjunction):
            elem = ET.Element(tag, type="any")
            for child in condition.any:
                elem.append(self._encode_condition(child))
            return elem
        if isinstance(condition, NegatedCondition):
            elem = ET.Element(tag, type="negative")
            elem.append(self._encode_condition(condition.negative))
            return elem
        raise TypeError(f"Unsupported condition type: {type(condition).__name__}")

    def _encode_operand(self, operand: Operand, *, tag: str) -> ET.Element:
        if isinstance(operand, Variable):
            return ET.Element(tag, type="variable", name=operand.name)
        if isinstance(operand, Literal):
            return ET.Element(tag, type="literal", value=operand.value)
        if isinstance(operand, Function):
            attrs: dict[str, str] = {"type": "function", "name": operand.name}
            if operand.args:
                attrs["args"] = json.dumps(list(operand.args))
            if operand.kwargs:
                attrs["kwargs"] = json.dumps(operand.kwargs)
            return ET.Element(tag, attrs)
        raise TypeError(f"Unsupported operand type: {type(operand).__name__}")

    def _encode_action_value(self, value: object, *, tag: str) -> ET.Element:
        if isinstance(value, Target):
            return ET.Element(tag, type="target")
        if isinstance(value, Operand):
            return self._encode_operand(value, tag=tag)
        raise TypeError(f"Unsupported action argument type: {type(value).__name__}")

    def _decode_action_value(self, elem: ET.Element) -> object:
        node_type = elem.get("type")
        if node_type == "target":
            return Target()
        if node_type in {"variable", "literal", "function"}:
            return self._decode_operand(elem)
        raise ValueError(f"Unknown action argument type: {node_type!r}")

    def _encode_actions(self, actions: list[Action], tag: str) -> ET.Element:
        elem = ET.Element(tag)
        for action in actions:
            action_elem = ET.Element("action", name=action.name)
            for arg in action.args:
                action_elem.append(self._encode_action_value(arg, tag="arg"))
            for key, value in action.kwargs.items():
                kwarg_elem = self._encode_action_value(value, tag="kwarg")
                kwarg_elem.set("key", key)
                action_elem.append(kwarg_elem)
            elem.append(action_elem)
        return elem

    def _decode_condition(self, elem: ET.Element) -> Condition:
        node_type = elem.get("type")
        if node_type == "binary":
            left = elem.find("left")
            right = elem.find("right")
            if left is None or right is None:
                raise ValueError("Binary condition requires <left> and <right>")
            return BinaryCondition(
                left=self._decode_operand(left),
                operator=self._resolve_binary_operator(elem.get("operator", "")),
                right=self._decode_operand(right),
            )
        if node_type == "unary":
            operand_elem = elem.find("operand")
            if operand_elem is None:
                raise ValueError("Unary condition requires <operand>")
            operand = self._decode_operand(operand_elem)
            if not isinstance(operand, DataTypeAwareOperand):
                raise TypeError("Unary operand must be a variable or function")
            return UnaryCondition(
                operand=operand,
                operator=self._resolve_unary_operator(elem.get("operator", "")),
            )
        if node_type == "all":
            return Conjunction(
                all=tuple(
                    self._decode_condition(child) for child in elem.findall("condition")
                )
            )
        if node_type == "any":
            return Disjunction(
                any=tuple(
                    self._decode_condition(child) for child in elem.findall("condition")
                )
            )
        if node_type == "negative":
            child = elem.find("condition")
            if child is None:
                raise ValueError("Negative condition requires a nested <condition>")
            return NegatedCondition(negative=self._decode_condition(child))
        raise ValueError(f"Unknown condition type: {node_type!r}")

    def _decode_operand(self, elem: ET.Element) -> Operand:
        node_type = elem.get("type")
        if node_type == "variable":
            return Variable(name=elem.get("name", ""))
        if node_type == "literal":
            return Literal(value=elem.get("value", ""))
        if node_type == "function":
            args = json.loads(elem.get("args", "[]"))
            kwargs = json.loads(elem.get("kwargs", "{}"))
            return Function(
                name=elem.get("name", ""),
                args=tuple(args),
                kwargs=kwargs,
            )
        raise ValueError(f"Unknown operand type: {node_type!r}")

    def _decode_actions(self, elem: ET.Element | None) -> list[Action] | None:
        if elem is None:
            return None
        return [self._decode_action(action) for action in elem.findall("action")]

    def _decode_action(self, elem: ET.Element) -> Action:
        return Action(
            name=elem.get("name", ""),
            args=tuple(
                self._decode_action_value(arg) for arg in elem.findall("arg")
            ),
            kwargs={
                kwarg.get("key", ""): self._decode_action_value(kwarg)
                for kwarg in elem.findall("kwarg")
            },
        )

    def _resolve_binary_operator(self, operator_name: str) -> type[BinaryOperator]:
        operator_cls = OperatorsPool.get(operator_name)
        if not issubclass(operator_cls, BinaryOperator):
            raise TypeError(f"Operator {operator_name!r} is not binary")
        return operator_cls

    def _resolve_unary_operator(self, operator_name: str) -> type[UnaryOperator]:
        operator_cls = OperatorsPool.get(operator_name)
        if not issubclass(operator_cls, UnaryOperator):
            raise TypeError(f"Operator {operator_name!r} is not unary")
        return operator_cls
```

`dump` walks the `BusinessRule` and builds XML elements. `load` parses the XML and reconstructs the rule. Action arguments use child `<arg>` and `<kwarg>` elements so `target()` round-trips without JSON-encoding `Target` instances.

## Step 3 — Dump a rule to XML

Build a rule in Python, then call `dump`. This example uses the [premium access rule](../README.md#object-context) from the README (with `ObjectContext`, nested contexts, and `target()` in lifecycle actions):

```python
converter = XmlConverter()
xml_text = converter.dump(premium_access_rule)
print(xml_text)
```

Output:

```xml
<?xml version='1.0' encoding='utf-8'?>
<business-rule>
  <having type="all">
    <condition type="all">
      <condition type="binary" operator="eq">
        <left type="function" name="is_adult"/>
        <right type="literal" value="true"/>
      </condition>
      <condition type="binary" operator="eq">
        <left type="variable" name="status"/>
        <right type="literal" value="active"/>
      </condition>
      <condition type="unary" operator="is_not_null">
        <operand type="variable" name="email"/>
      </condition>
    </condition>
    <condition type="any">
      <condition type="binary" operator="eq">
        <left type="variable" name="tier"/>
        <right type="literal" value="premium"/>
      </condition>
      <condition type="negative">
        <condition type="binary" operator="eq">
          <left type="variable" name="is_suspended"/>
          <right type="literal" value="true"/>
        </condition>
      </condition>
    </condition>
    <condition type="binary" operator="is_in">
      <left type="variable" name="region"/>
      <right type="function" name="allowed_regions" args="[&quot;premium&quot;]"/>
    </condition>
  </having>
  <on-success>
    <action name="grant_access">
      <arg type="target"/>
    </action>
  </on-success>
  <on-failure>
    <action name="reject_access">
      <arg type="target"/>
    </action>
  </on-failure>
  <on-finally>
    <action name="audit_log">
      <arg type="target"/>
    </action>
  </on-finally>
</business-rule>
```

## Step 4 — Load a rule from XML

Pass the XML string to `load` to get a `BusinessRule` back:

```python
restored = converter.load(xml_text)
assert restored == premium_access_rule
```

The restored rule is ready for `engine.run(rule, local_context=action_context, target=user)`.

## Step 5 — Save and run

```python
xml_text = XmlConverter().dump(premium_access_rule)
# write xml_text to a file or database

rule = XmlConverter().load(xml_text)
engine.run(rule, local_context=action_context, target=user)
```

Set up `ObjectContext`, nest it under `action_context`, and register lifecycle handlers before running. See [Object context](../README.md#object-context) in the README.

## Notes

- `target` is serialized in the rule but bound only at run time via `engine.run(..., target=...)`.
- Put custom converters in your own project, not in the library.
- Operator names in XML must match registered operator names (`gte`, `eq`, `is_not_null`, …).
- Import `business_rules.operators.builtin` if you use built-in operators in loaded rules.
