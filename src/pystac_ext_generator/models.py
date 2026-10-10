# Copyright 2026 Terradue
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Build a finite graph of typed nested value classes and conversion plans."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

from .schema import Schema, identifier


@dataclass
class ValueType:
    """Python annotation and conversion plan used by the renderer."""

    annotation: str
    codec: Any = None


@dataclass
class Member:
    """Internal rendering metadata for a nested value property."""

    key: str
    name: str
    annotation: str
    codec: Any
    required: bool
    description: str


@dataclass
class Model:
    """A generated class name and its ordered member metadata."""

    name: str
    members: list[Member] = field(default_factory=list)


def pascal(value: str) -> str:
    """Convert a naming hint into a valid PascalCase class name."""
    name = "".join(
        word[:1].upper() + word[1:] for word in re.split(r"[^a-zA-Z0-9]+", value) if word
    )
    return ("Value" + name) if not name or name[0].isdigit() else name


def singular(value: str) -> str:
    """Derive a singular naming hint for array or map members."""
    if value.endswith("ies"):
        return value[:-3] + "y"
    return value[:-1] if value.endswith("s") and not value.endswith("ss") else value


class ModelBuilder:
    """Build reusable class metadata while preserving recursive object identities."""

    def __init__(self, schema: Schema, reserved: set[str]) -> None:
        self.schema = schema
        self.models: list[Model] = []
        self.objects: dict[int, Model] = {}
        self.nodes: list[dict[str, Any]] = []
        self.active: set[int] = set()
        self.shapes: dict[str, Model] = {}
        self.names = reserved | {
            "Any",
            "ClassVar",
            "Mapping",
            "Required",
            "TypedDict",
            "Unpack",
            "Validator",
            "Literal",
            "Generic",
            "TypeVar",
            "T",
            "PropertiesExtension",
            "ExtensionManagementMixin",
            "SummariesExtension",
            "SCHEMA",
            "SCHEMA_URI",
            "FIELD_NAMES",
            "FIELD_TARGETS",
            "TARGETS",
        }

    def object_shape(
        self, node: Any, seen: frozenset[int] = frozenset()
    ) -> tuple[dict[str, Any], set[str]]:
        """Merge object properties and requirements from local references and intersections."""
        if not isinstance(node, dict) or id(node) in seen:
            return {}, set()
        seen = seen | {id(node)}
        props, required = dict(node.get("properties", {})), set(node.get("required", []))
        parts = list(node.get("allOf", []))
        if "$ref" in node:
            parts.insert(0, self.schema.pointer(node["$ref"]))
        for part in parts:
            more, req = self.object_shape(part, seen)
            required |= req
            for key, value in more.items():
                if key in props and props[key] != value:
                    props[key] = {"allOf": [props[key], value]}
                else:
                    props[key] = value
        return props, required

    def build(self, node: Any, hint: str) -> ValueType:
        """Build a conversion plan, reserving classes before following recursive fields."""
        if not isinstance(node, dict):
            return ValueType("Any")
        self.nodes.append(node)  # Keep identity-cache keys alive for synthetic schemas.
        # Reserve an object before descending to preserve recursive references.
        if id(node) in self.objects:
            name = self.objects[id(node)].name
            nullable = isinstance(node.get("type"), list) and "null" in node["type"]
            return ValueType(name + " | None" if nullable else name, ["object", name])
        if id(node) in self.active:
            self.schema.warnings.add(
                "Recursive non-object value schemas use Any at the recursion boundary."
            )
            return ValueType("Any")
        self.active.add(id(node))
        try:
            return self._build(node, hint)
        finally:
            self.active.remove(id(node))

    def _build(self, node: dict[str, Any], hint: str) -> ValueType:
        if "$ref" in node and len(set(node) - {"$ref", "description", "title", "$comment"}) == 0:
            ref = node["$ref"]
            tail = ref.rsplit("/", 1)[-1].replace("~1", "/").replace("~0", "~")
            # Generic definition names should not produce classes named Fields.
            named_hint = (
                hint
                if tail in {"fields", "items", "object", "value"} or tail.startswith("resource_")
                else tail
            )
            return self.build(self.schema.pointer(ref), named_hint)
        for keyword in ("oneOf", "anyOf"):
            if keyword in node:
                return self._union(node[keyword], hint)
        return self._build_type(node, hint)

    def _union(self, branches: list[Any], hint: str) -> ValueType:
        types = [
            self.build(part, hint + "Variant" + str(index + 1))
            for index, part in enumerate(branches)
        ]
        annotations = list(dict.fromkeys(value.annotation for value in types))
        annotation = "Any" if "Any" in annotations else " | ".join(annotations)
        if not any(value.codec is not None for value in types):
            return ValueType(annotation)
        return ValueType(
            annotation,
            ["union", [[part, value.codec] for part, value in zip(branches, types, strict=True)]],
        )

    def _build_type(self, node: dict[str, Any], hint: str) -> ValueType:
        schema_type = node.get("type")
        if isinstance(schema_type, list) and set(schema_type) == {"object", "null"}:
            narrowed = {**node, "type": "object"}
            # Keep the original identity so recursive $refs find this record class.
            value = (
                self._build(narrowed, hint)
                if not self.object_shape(node)[0]
                else self.record(node, hint)
            )
            return ValueType(value.annotation + " | None", value.codec)
        if isinstance(schema_type, list):
            branches = [{**node, "type": t} for t in schema_type]
            return self.build({"anyOf": branches}, hint)
        props, _ = self.object_shape(node)
        if props and schema_type in (None, "object"):
            return self.record(node, hint)
        if schema_type == "array":
            return self._array(node, hint)
        if schema_type == "object" or "additionalProperties" in node or "patternProperties" in node:
            return self._map(node, hint)
        return ValueType(self.schema.annotation(node))

    def _array(self, node: dict[str, Any], hint: str) -> ValueType:
        items = node.get("items", {})
        if isinstance(items, list) or node.get("prefixItems"):
            self.schema.warnings.add(
                "Tuple arrays retain raw JSON values; tuple member wrappers are not generated."
            )
            return ValueType(self.schema.annotation(node))
        value = self.build(items, singular(hint))
        return ValueType(
            f"list[{value.annotation}]", ["list", value.codec] if value.codec else None
        )

    def _map(self, node: dict[str, Any], hint: str) -> ValueType:
        value_schema = node.get("additionalProperties", {})
        patterns = list(node.get("patternProperties", {}).values())
        if patterns:
            if len(patterns) == 1 and node.get("additionalProperties") is False:
                value_schema = patterns[0]
            else:
                self.schema.warnings.add(
                    "Heterogeneous patternProperties maps remain raw dictionaries."
                )
                return ValueType("dict[str, Any]")
        if not value_schema:
            # Common STAC 'at least one matching value' double-negation idiom.
            inner = node.get("not", {})
            inner = inner.get("additionalProperties", {}) if isinstance(inner, dict) else {}
            value_schema = inner.get("not", {}) if isinstance(inner, dict) else {}
        value = self.build(value_schema, singular(hint))
        return ValueType(
            f"dict[str, {value.annotation}]", ["map", value.codec] if value.codec else None
        )

    def record(self, node: dict[str, Any], hint: str) -> ValueType:
        """Reuse an equivalent object shape or reserve and populate a new class."""
        props, required = self.object_shape(node)
        fingerprint = json.dumps([props, sorted(required)], sort_keys=True)
        if fingerprint in self.shapes:
            model = self.shapes[fingerprint]
            self.objects[id(node)] = model
            return ValueType(model.name, ["object", model.name])
        base = pascal(hint)
        name, index = base, 2
        while name in self.names:
            name, index = base + str(index), index + 1
        self.names.add(name)
        model = Model(name)
        self.objects[id(node)] = model
        self.shapes[fingerprint] = model
        self.models.append(model)
        used = {
            "properties",
            "create",
            "from_dict",
            "to_dict",
            "apply",
            "clear",
            "set_null",
            "property",
            "classmethod",
            "staticmethod",
            "self",
            "cls",
            "result",
            "_members",
        }
        for key, part in sorted(props.items()):
            member_name = identifier(key.split(":")[-1])
            if member_name in used or member_name.startswith("_"):
                member_name = member_name.lstrip("_") + "_field"
            base_name, i = member_name, 2
            while member_name in used:
                member_name, i = base_name + str(i), i + 1
            used.add(member_name)
            value_type = self.build(part, name + pascal(key.split(":")[-1]))
            description = (
                part.get("description", part.get("title", key)) if isinstance(part, dict) else key
            )
            model.members.append(
                Member(
                    key,
                    member_name,
                    value_type.annotation,
                    value_type.codec,
                    key in required,
                    description if isinstance(description, str) else key,
                )
            )
        return ValueType(name, ["object", name])
