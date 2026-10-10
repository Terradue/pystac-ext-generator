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

"""Discover fields at STAC locations, without scanning unused definitions."""

from __future__ import annotations

import keyword
import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Iterator


class SchemaError(ValueError):
    """The input cannot be represented safely by the generator."""


def identifier(value: str) -> str:
    """Convert a field name to a non-private Python identifier."""
    value = re.sub(r"\W", "_", value, flags=re.ASCII)
    if not value or value[0].isdigit():
        value = "field_" + value
    if keyword.iskeyword(value) or value.startswith("_"):
        value += "_"
    return value


@dataclass
class Field:
    """A discovered field and its internal rendering metadata."""

    key: str
    name: str
    annotation: str
    description: str
    targets: set[str] = field(default_factory=set)
    schemas: list[Any] = field(default_factory=list)
    codec: Any = None


class Schema:
    """Discover renderable fields in an already dereferenced schema graph."""

    def __init__(self, document: dict[str, Any]) -> None:
        self.document = document
        self.warnings: set[str] = set()

    def annotation(self, node: Any, seen: frozenset[int] = frozenset()) -> str:
        """Return a conservative Python annotation, recording unsupported intersections."""
        if not isinstance(node, dict):
            return "Any"
        if id(node) in seen:
            self.warnings.add("Recursive value schemas use Any at the recursion boundary.")
            return "Any"
        seen = seen | {id(node)}
        values = node.get("enum", [node["const"]] if "const" in node else None)
        if values is not None and all(
            isinstance(value, (str, int, bool)) or value is None for value in values
        ):
            return (
                "Literal[" + ", ".join(repr(value) for value in values) + "]" if values else "Any"
            )
        return self._composed_annotation(node, seen)

    def _composed_annotation(self, node: dict[str, Any], seen: frozenset[int]) -> str:
        for union in ("oneOf", "anyOf"):
            if union in node:
                annotations = list(
                    dict.fromkeys(self.annotation(part, seen) for part in node[union])
                )
                return "Any" if "Any" in annotations else " | ".join(annotations)
        if "allOf" in node and "type" not in node:
            annotations_set = {self.annotation(part, seen) for part in node["allOf"]} - {"Any"}
            if len(annotations_set) == 1:
                return annotations_set.pop()
            self.warnings.add(
                "An allOf intersection has a conservative Any annotation; validation retains its constraints."
            )
            return "Any"
        return self._type_annotation(node, seen)

    def _type_annotation(self, node: dict[str, Any], seen: frozenset[int]) -> str:
        schema_type = node.get("type")
        if isinstance(schema_type, list):
            return " | ".join(
                dict.fromkeys(
                    self.annotation({**node, "type": member}, seen) for member in schema_type
                )
            )
        if schema_type == "array":
            return self._array_annotation(node.get("items", {}), seen)
        if schema_type == "object" or "properties" in node:
            additional = node.get("additionalProperties", True)
            value = (
                self.annotation(additional, seen)
                if isinstance(additional, dict) and not node.get("properties")
                else "Any"
            )
            return f"dict[str, {value}]"
        primitives = {
            "string": "str",
            "number": "float",
            "integer": "int",
            "boolean": "bool",
            "null": "None",
        }
        return primitives.get(schema_type, "Any") if isinstance(schema_type, str) else "Any"

    def _array_annotation(self, items: Any, seen: frozenset[int]) -> str:
        if isinstance(items, list):
            annotations = list(dict.fromkeys(self.annotation(part, seen) for part in items))
            return "list[" + " | ".join(annotations or ["Any"]) + "]"
        return f"list[{self.annotation(items, seen)}]"

    def discover(self, prefix: str | None = None) -> list[Field]:
        """Discover extension fields at supported STAC locations.

        Args:
            prefix: Namespace to select, or None to infer it from discovered fields.

        Raises:
            SchemaError: If no fields are found or Python names collide.
        """
        discovery = _FieldDiscovery(self, prefix)
        for target in ("item", "collection", "catalog"):
            discovery.walk(self.document, target)
        return discovery.fields()


def schema_children(node: dict[str, Any]) -> Iterator[Any]:
    """Yield schema-valued children without traversing defaults, constants, or examples."""
    for key in (
        "properties",
        "patternProperties",
        "$defs",
        "definitions",
        "dependentSchemas",
        "dependencies",
    ):
        yield from node.get(key, {}).values()
    for key in ("allOf", "anyOf", "oneOf", "prefixItems"):
        yield from node.get(key, [])
    for key in (
        "items",
        "contains",
        "additionalProperties",
        "unevaluatedProperties",
        "propertyNames",
        "additionalItems",
        "unevaluatedItems",
        "contentSchema",
        "not",
        "if",
        "then",
        "else",
    ):
        child = node.get(key)
        yield from child if isinstance(child, list) else [child]


class _FieldDiscovery:
    """Accumulate fields while preserving STAC location and graph traversal state."""

    def __init__(self, schema: Schema, prefix: str | None) -> None:
        self.schema = schema
        self.prefix = prefix
        self.found: dict[str, Field] = {}

    def _add(self, key: str, node: Any, target: str) -> None:
        if self.prefix is not None and not key.startswith(self.prefix + ":"):
            return
        core = {
            "type",
            "id",
            "stac_version",
            "stac_extensions",
            "geometry",
            "bbox",
            "properties",
            "assets",
            "item_assets",
            "links",
            "summaries",
            "extent",
            "license",
            "providers",
            "title",
            "description",
            "keywords",
            "collection",
            "datetime",
            "start_datetime",
            "end_datetime",
            "created",
            "updated",
        }
        if self.prefix is None and ":" not in key and key in core:
            return
        entry = self.found.setdefault(key, Field(key, "", "", ""))
        self._add_schema(entry, node, target)
        entry.targets.add(target)

    def _add_schema(self, entry: Field, node: Any, target: str) -> None:
        if target == "summary" and entry.schemas:
            return
        if target != "summary" and entry.targets == {"summary"}:
            entry.schemas.clear()
        if not any(node is existing for existing in entry.schemas):
            entry.schemas.append(node)

    def _declared_types(self, node: Any, seen: frozenset[int] = frozenset()) -> set[str]:
        if not isinstance(node, dict) or id(node) in seen:
            return set()
        seen = seen | {id(node)}
        type_schema = node.get("properties", {}).get("type", {})
        values = (
            type_schema.get("enum", [type_schema.get("const")])
            if isinstance(type_schema, dict)
            else []
        )
        types = {value for value in values if value in ("Feature", "Collection", "Catalog")}
        for child in node.get("allOf", []):
            types |= self._declared_types(child, seen)
        return types

    def walk(
        self,
        node: Any,
        target: str,
        location: str = "root",
        seen: frozenset[tuple[int, str]] = frozenset(),
    ) -> None:
        """Visit applicable schema branches, stopping cycles at each STAC location."""
        if not isinstance(node, dict):
            return
        if location == "root":
            declared = self._declared_types(node)
            if (
                declared
                and {"item": "Feature", "collection": "Collection", "catalog": "Catalog"}[target]
                not in declared
            ):
                return
        token = (id(node), location)
        if token in seen:
            return
        seen = seen | {token}
        self._walk_properties(node, target, location, seen)
        self._walk_branches(node, target, location, seen)
        self._walk_containers(node, target, location, seen)

    def _walk_properties(
        self, node: dict[str, Any], target: str, location: str, seen: frozenset[tuple[int, str]]
    ) -> None:
        if location == "summary":
            for key in node.get("required", []):
                self._add(key, {}, "summary")
        field_targets = {
            "fields": target,
            "asset": "asset",
            "item_asset": "item_asset",
            "summary": "summary",
            "link": "link",
        }
        for key, value in node.get("properties", {}).items():
            if location in field_targets:
                self._add(key, value, field_targets[location])
            elif location == "root":
                self._walk_root_property(key, value, target, seen)
            elif location in ("asset_map", "item_asset_map"):
                self.walk(value, target, "asset" if location == "asset_map" else "item_asset", seen)

    def _walk_root_property(
        self, key: str, value: Any, target: str, seen: frozenset[tuple[int, str]]
    ) -> None:
        destinations = {
            "assets": "asset_map",
            "item_assets": "item_asset_map",
            "links": "link_list",
        }
        if target == "item":
            destinations["properties"] = "fields"
        if target == "collection":
            destinations["summaries"] = "summary"
        if key in destinations:
            self.walk(value, target, destinations[key], seen)
        elif target in ("collection", "catalog"):
            self._add(key, value, target)

    def _walk_branches(
        self, node: dict[str, Any], target: str, location: str, seen: frozenset[tuple[int, str]]
    ) -> None:
        for key in ("allOf", "anyOf", "oneOf"):
            for child in node.get(key, []):
                self.walk(child, target, location, seen)
        for key in ("if", "then", "else"):
            if key in node:
                self.schema.warnings.add(
                    "Conditional applicability is approximated; validate the STAC object to enforce the complete schema."
                )
                self.walk(node[key], target, location, seen)

    def _walk_containers(
        self, node: dict[str, Any], target: str, location: str, seen: frozenset[tuple[int, str]]
    ) -> None:
        if location == "link_list":
            self.walk(node.get("items"), target, "link", seen)
        if location in ("asset_map", "item_asset_map"):
            slot = "asset" if location == "asset_map" else "item_asset"
            self.walk(node.get("additionalProperties"), target, slot, seen)
            for child in node.get("patternProperties", {}).values():
                self.walk(child, target, slot, seen)
            # STAC templates express 'at least one asset' with double negation.
            inner = node.get("not")
            if isinstance(inner, dict):
                inner = inner.get("additionalProperties")
                if isinstance(inner, dict):
                    self.walk(inner.get("not"), target, slot, seen)

    def fields(self) -> list[Field]:
        """Finalize field names and annotations in deterministic order."""
        if not self.found:
            raise SchemaError(
                "No extension fields found at STAC object locations. Reference field definitions from Item properties, Collection/Catalog fields, assets, item_assets, links, or summaries."
            )
        names: set[str] = set()
        result = []
        for key, entry in sorted(self.found.items()):
            entry.name = self._field_name(key, names)
            names.add(entry.name)
            annotations = list(
                dict.fromkeys(
                    self.schema.annotation(node)
                    for node in entry.schemas
                    if node or len(entry.schemas) == 1
                )
            )
            entry.annotation = "Any" if "Any" in annotations else " | ".join(annotations)
            description = next(
                (
                    node.get("description", node.get("title", ""))
                    for node in entry.schemas
                    if isinstance(node, dict)
                ),
                "",
            )
            entry.description = description or key
            result.append(entry)
        return result

    def _field_name(self, key: str, names: set[str]) -> str:
        reserved = {
            "apply",
            "ext",
            "summaries",
            "validate",
            "get_schema_uri",
            "get_schema_uris",
            "has_extension",
            "add_to",
            "remove_from",
            "ensure_has_extension",
            "ensure_owner_has_extension",
            "properties",
            "additional_read_properties",
            "name",
            "obj",
            "clear",
            "set_null",
            "property",
            "classmethod",
            "staticmethod",
            "validate_owner_has_extension",
            "validate_has_extension",
        }
        name = identifier(key.split(":", 1)[-1])
        if name in reserved:
            name += "_field"
        if name in names:
            name = identifier(key)
        if name in names or name in reserved:
            raise SchemaError(f"Python name collision for {key!r}")
        return name
