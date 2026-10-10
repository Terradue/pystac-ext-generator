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

"""Bundle JSON Pointer references for offline generated modules.

Remote fetching is opt-in. Nested resource IDs and mixed dialects are rejected.
"""

from __future__ import annotations

import json
from copy import deepcopy
from typing import TYPE_CHECKING, Any
from urllib.parse import urldefrag, urljoin
from urllib.request import urlopen

from .schema import SchemaError, schema_children

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping


def bundle(
    document: dict[str, Any],
    *,
    documents: Mapping[str, dict[str, Any]] | None = None,
    fetch: Callable[[str], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Return a copy with external references replaced by local JSON Pointers.

    Args:
        document: Root schema, whose $id resolves relative references.
        documents: Offline schemas indexed by their absolute resource URI.
        fetch: Optional loader for resources missing from documents.

    Raises:
        SchemaError: If a resource is missing, exceeds the resource limit, uses a
            different dialect, or contains unsupported anchors or nested IDs.
    """
    result = deepcopy(document)
    if "__bundled" in result.get("definitions", {}):
        raise SchemaError("Reserved definition __bundled already exists")
    bundler = _Bundler(document, documents or {}, fetch)
    bundler.rewrite(result, urldefrag(document.get("$id", ""))[0], root=True)
    if bundler.imports:
        result.setdefault("definitions", {})["__bundled"] = {"definitions": bundler.imports}
    return result


class _Bundler:
    """Track resource identities during one recursive bundling operation."""

    def __init__(
        self,
        document: dict[str, Any],
        documents: Mapping[str, dict[str, Any]],
        fetch: Callable[[str], dict[str, Any]] | None,
    ) -> None:
        self.resources = documents
        self.fetch = fetch
        self.locations = {urldefrag(document.get("$id", ""))[0]: "#"}
        self.imports: dict[str, Any] = {}
        self.dialect = document.get("$schema")

    def rewrite(self, node: Any, base: str, *, root: bool = False) -> None:
        """Replace references in place while preserving non-schema JSON values."""
        if not isinstance(node, dict):
            return
        if not root and "$id" in node:
            raise SchemaError("Nested $id scopes are unsupported; normalize the schema first")
        if "$ref" in node:
            node["$ref"] = self._reference(urljoin(base, node["$ref"]))
        for child in schema_children(node):
            self.rewrite(child, base)

    def _reference(self, absolute: str) -> str:
        uri, fragment = urldefrag(absolute)
        if fragment and not fragment.startswith("/"):
            raise SchemaError(f"Named anchors are unsupported: {absolute}")
        if uri not in self.locations:
            self._import_resource(uri)
        return self.locations[uri] + fragment

    def _import_resource(self, uri: str) -> None:
        """Reserve a resource before descending so cyclic imports terminate."""
        if len(self.imports) >= 100:
            raise SchemaError("External resource limit (100) exceeded")
        imported = self.resources.get(uri)
        if imported is None:
            if self.fetch is None:
                raise SchemaError(
                    f"Missing external schema {uri}; supply --reference URI=FILE or --resolve-external"
                )
            imported = self.fetch(uri)
        imported = deepcopy(imported)
        if not isinstance(imported, dict):
            raise SchemaError(f"External schema must be an object: {uri}")
        if imported.get("$schema", self.dialect) != self.dialect:
            raise SchemaError(f"Mixed schema dialects cannot be bundled: {uri}")
        name = f"resource_{len(self.imports)}"
        pointer = f"#/definitions/__bundled/definitions/{name}"
        self.locations[uri] = pointer
        canonical = urldefrag(urljoin(uri, imported.get("$id", uri)))[0]
        self.locations[canonical] = pointer
        self.imports[name] = imported
        self.rewrite(imported, canonical, root=True)
        imported.pop("$id", None)
        imported.pop("$schema", None)


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
