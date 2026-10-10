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

"""Resolve schema references eagerly with jsonref before model discovery."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any
from urllib.request import urlopen

# jsonref 1.1 has no typing metadata or published type stubs.
import jsonref  # type: ignore[import-untyped]

from .schema import SchemaError, schema_children

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping


def fetch_http(uri: str) -> dict[str, Any]:
    """Fetch a JSON schema from an HTTP(S) URL with a 30-second timeout.

    Raises:
        SchemaError: If the URI is not HTTP(S) or the response is not an object.
    """
    if not uri.startswith(("https://", "http://")):
        raise SchemaError(f"Only HTTP(S) external references can be fetched: {uri}")
    # The scheme is checked above; urllib rejects file/custom-scheme redirects.
    with urlopen(uri, timeout=30) as response:  # nosec B310
        document = json.load(response)
    if not isinstance(document, dict):
        raise SchemaError(f"External schema must be an object: {uri}")
    return document


def bundle(
    document: dict[str, Any],
    *,
    documents: Mapping[str, dict[str, Any]] | None = None,
    fetch: Callable[[str], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Return an eagerly dereferenced schema graph without mutating the input.

    Args:
        document: Root schema, whose $id provides the reference base URI.
        documents: Offline resources indexed by absolute URI.
        fetch: Loader for resources absent from documents; None disables fetching.

    Raises:
        SchemaError: If a reference cannot be resolved or a resource is not an object.
    """
    if not isinstance(document, dict):
        raise SchemaError("The schema must be a JSON object")
    resources = documents or {}
    dialect = document.get("$schema", "https://json-schema.org/draft/2020-12/schema")

    def load_resource(uri: str) -> dict[str, Any]:
        if uri in resources:
            return _prepare_document(resources[uri], dialect)
        if fetch is None:
            raise SchemaError(f"Missing external schema {uri}; supply --reference URI=FILE")
        return _prepare_document(fetch(uri), dialect)

    try:
        resolved = jsonref.replace_refs(
            _prepare_document(document, dialect),
            base_uri=document.get("$id") or "",
            loader=load_resource,
            jsonschema=True,
            proxies=False,
            lazy_load=False,
        )
    except (jsonref.JsonRefError, RecursionError) as exc:
        raise SchemaError(f"Could not resolve schema references: {exc}") from exc
    if not isinstance(resolved, dict):
        raise SchemaError("The schema must be a JSON object")
    _restore_schema(resolved, set(), root=True)
    return resolved


def _prepare_document(resource: dict[str, Any], dialect: str) -> dict[str, Any]:
    """Copy one resource and adapt its dialect before jsonref traverses it."""
    if resource.get("$schema", dialect) != dialect:
        raise SchemaError("Mixed schema dialects cannot be bundled")
    prepared: dict[str, Any] = json_graph(resource)
    _prepare_schema(prepared, ref_siblings="draft-07" not in dialect)
    return prepared


@dataclass
class _Literal:
    """Shield instance-valued schema annotations from JSON Reference traversal."""

    value: Any


def _prepare_schema(node: Any, *, ref_siblings: bool) -> None:
    """Adapt JSON Schema semantics to jsonref's JSON Reference semantics."""
    if not isinstance(node, dict):
        return
    unsupported = node.keys() & {"$dynamicRef", "$recursiveRef"}
    if unsupported:
        raise SchemaError(f"{sorted(unsupported)} is not supported by jsonref")
    for child in schema_children(node):
        _prepare_schema(child, ref_siblings=ref_siblings)
    for keyword in ("default", "const", "enum", "examples"):
        if keyword in node:
            node[keyword] = _Literal(node[keyword])
    # Modern JSON Schema applies sibling constraints conjunctively, whereas
    # jsonref follows JSON Reference and would otherwise discard siblings.
    if ref_siblings and "$ref" in node and len(node) > 1:
        reference = node.pop("$ref")
        node.setdefault("allOf", []).insert(0, {"$ref": reference})


def _restore_schema(node: Any, seen: set[int], *, root: bool = False) -> None:
    """Restore literal data and remove resource scopes after eager resolution."""
    if not isinstance(node, dict) or id(node) in seen:
        return
    seen.add(id(node))
    if not root:
        # Local cycle references emitted later must resolve against the bundled
        # root, not a former external resource ID.
        node.pop("$id", None)
        node.pop("$schema", None)
    for key, child in node.items():
        if isinstance(child, _Literal):
            node[key] = child.value
    for child in schema_children(node):
        _restore_schema(child, seen)


def json_graph(value: Any, path: str = "#", ancestors: Mapping[int, str] | None = None) -> Any:
    """Make a resolved graph serializable, expressing only cycles as local references.

    This encodes Python object identities; all URI and pointer resolution belongs
    to jsonref. Repeated acyclic values are copied to retain independent constraints.
    """
    if not isinstance(value, (dict, list)):
        return value
    ancestors = ancestors or {}
    if id(value) in ancestors:
        return {"$ref": ancestors[id(value)]}
    ancestors = {**ancestors, id(value): path}
    if isinstance(value, list):
        return [
            json_graph(child, f"{path}/{index}", ancestors) for index, child in enumerate(value)
        ]
    return {
        key: json_graph(child, path + "/" + key.replace("~", "~0").replace("/", "~1"), ancestors)
        for key, child in value.items()
    }
