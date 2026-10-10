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

"""Render an independently importable extension module."""

from __future__ import annotations

import ast
import json
import re

# Fixed Ruff commands receive generated source on stdin.
import subprocess  # nosec B404
import sys
from typing import TYPE_CHECKING, Any

from jinja2 import Environment, PackageLoader, StrictUndefined
from jsonschema.exceptions import SchemaError as JSONSchemaError
from jsonschema.validators import validator_for

from .bundle import bundle, fetch_http, json_graph
from .models import ModelBuilder, pascal
from .schema import Schema, SchemaError

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from .schema import Field


def generate(
    document: dict[str, Any],
    *,
    prefix: str | None = None,
    include_validation: bool = False,
    documents: Mapping[str, dict[str, Any]] | None = None,
) -> tuple[str, list[str]]:
    """Return Python source and diagnostics. No generated code is executed.

    The schema title determines the extension class name and its canonical $id
    determines registration. Fields and applicable STAC objects are discovered
    from schema paths and references. Embedded offline validation is opt-in.

    Args:
        document: Full extension schema with a nonempty title and HTTP(S) $id.
        prefix: Optional namespace filter, without the colon.
        documents: Offline resources; missing external schemas are fetched over HTTP(S).
        include_validation: Embed the schema and a validate() method. Union
            decoding may require the schema even when this is false.

    Raises:
        SchemaError: If the schema, namespace, class name, or references cannot be supported.
    """
    document = bundle(document, documents=documents, fetch=fetch_http)
    _validate_document(json_graph(document))
    schema = Schema(document)
    fields = schema.discover(prefix)
    class_name = _class_name(document, fields, prefix)
    builder = _build_models(schema, fields, class_name)
    uri = document.get("$id")
    if isinstance(uri, str):
        uri = uri.removesuffix("#")
    if not isinstance(uri, str) or not uri.startswith(("https://", "http://")):
        raise SchemaError("The schema must declare an absolute HTTP(S) $id")
    # Python source must retain literal characters rather than HTML entities.
    env = Environment(  # nosec B701
        autoescape=False,
        loader=PackageLoader("pystac_ext_generator", "templates"),
        undefined=StrictUndefined,
        keep_trailing_newline=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["py"] = repr
    env.filters["optional"] = lambda value: _annotation_union(value, "None")
    env.filters["update_type"] = lambda value: _annotation_union(value, "_Unset", "None")
    env.filters["create_type"] = lambda value: _annotation_union(value, "_Unset")
    source = env.get_template("extension.py.j2").render(
        class_name=class_name,
        fields=fields,
        uri=uri,
        models=builder.models,
        include_validation=include_validation,
        codec_kinds=set().union(
            *(_codec_kinds(field.codec) for field in fields),
            *(_codec_kinds(member.codec) for model in builder.models for member in model.members),
        ),
        target_types=_target_types(fields),
        target_annotation=" | ".join("pystac." + name for name, _ in _target_types(fields)),
        document_json=json.dumps(json_graph(document), ensure_ascii=True, allow_nan=False),
        targets=sorted(set().union(*(f.targets for f in fields))),
        field_targets={f.key: sorted(f.targets) for f in fields},
        field_names={f.name: f.key for f in fields},
    )
    ast.parse(source)
    return _format_source(source), sorted(schema.warnings)


def _validate_document(document: dict[str, Any]) -> None:
    """Reject invalid schemas and unsupported dialects."""
    if not isinstance(document, dict):
        raise SchemaError("The schema must be a JSON object")
    try:
        validator_for(document).check_schema(document)
    except JSONSchemaError as exc:
        raise SchemaError(f"Invalid JSON Schema: {exc.message}") from exc
    declared_dialect = document.get(
        "$schema", "https://json-schema.org/draft/2020-12/schema"
    ).rstrip("#")
    supported = {
        "http://json-schema.org/draft-07/schema",
        "https://json-schema.org/draft-07/schema",
        "https://json-schema.org/draft/2019-09/schema",
        "https://json-schema.org/draft/2020-12/schema",
    }
    if declared_dialect not in supported:
        raise SchemaError(f"Unsupported JSON Schema dialect: {declared_dialect}")


def _class_name(document: dict[str, Any], fields: Sequence[Field], prefix: str | None) -> str:
    """Derive the public class name from the title after checking namespace selection."""
    prefixes = {f.key.split(":", 1)[0] for f in fields if ":" in f.key}
    if prefix is None and len(prefixes) > 1:
        raise SchemaError("Multiple namespaces discovered; select one using --prefix")
    title = document.get("title")
    if not isinstance(title, str) or not re.search(r"[A-Za-z0-9]", title):
        raise SchemaError("The schema must declare a nonempty title containing letters or digits")
    class_name = pascal(title.strip())
    if not class_name.endswith("Extension"):
        class_name += "Extension"
    if class_name in {"PropertiesExtension", "SummariesExtension"}:
        raise SchemaError("Schema title conflicts with generated module symbols")
    return class_name


def _build_models(schema: Schema, fields: Sequence[Field], class_name: str) -> ModelBuilder:
    """Attach nested conversion plans, reconciling fields found at multiple locations."""
    # Replace raw object annotations with finite class/conversion graphs.
    schema.warnings = {
        warning
        for warning in schema.warnings
        if not warning.startswith(("Recursive value", "An allOf intersection"))
    }
    builder = ModelBuilder(schema, {class_name, "Summaries" + class_name})
    for field in fields:
        candidates = [node for node in field.schemas if node] or [{}]
        # Same property can appear at different STAC locations. Use the first typed
        # representation when the other location supplies only existential constraints.
        values = [builder.build(node, field.name) for node in candidates]
        chosen = next((value for value in values if value.codec), values[0])
        if any(
            (value.annotation, value.codec) != (chosen.annotation, chosen.codec) for value in values
        ):
            chosen = builder.build({"anyOf": candidates}, field.name)
        field.annotation, field.codec = chosen.annotation, chosen.codec
    return builder


def _target_types(fields: Sequence[Field]) -> list[tuple[str, str]]:
    targets = {target for field in fields for target in field.targets}
    available = (
        ("Collection", "collection"),
        ("Catalog", "catalog"),
        ("Item", "item"),
        ("Asset", "asset"),
        ("ItemAssetDefinition", "item_asset"),
        ("Link", "link"),
    )
    return [(name, target) for name, target in available if target in targets] or [
        ("Collection", "collection")
    ]


def _codec_kinds(codec: object) -> set[str]:
    """Collect only runtime conversions needed by a generated field or member."""
    if not isinstance(codec, list) or not codec:
        return set()
    kind = codec[0]
    if not isinstance(kind, str):
        raise SchemaError("Invalid internal conversion kind")
    kinds = {kind}
    if kind in {"list", "map"}:
        kinds |= _codec_kinds(codec[1])
    elif kind == "union":
        for branch in codec[1]:
            kinds |= _codec_kinds(branch[1])
    return kinds


def _union_members(node: ast.expr) -> list[str]:
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        return [*_union_members(node.left), *_union_members(node.right)]
    return [ast.unparse(node)]


def _annotation_union(annotation: str, *additional: str) -> str:
    """Add top-level union members without changing nested nullable types."""
    members = list(
        dict.fromkeys([*_union_members(ast.parse(annotation, mode="eval").body), *additional])
    )
    if "None" in members:
        members.remove("None")
        members.append("None")
    return " | ".join(members)


def _format_source(source: str) -> str:
    """Normalize imports and format generated source without executing it."""
    commands = (
        ("check", "--select", "I,F401", "--fix"),
        ("format", "--line-length", "100"),
    )
    for command in commands:
        # Only fixed Ruff arguments are executed; schema-derived source is stdin.
        result = subprocess.run(  # nosec B603
            [
                sys.executable,
                "-m",
                "ruff",
                *command,
                "--isolated",
                "--target-version",
                "py310",
                "--stdin-filename",
                "generated.py",
                "-",
            ],
            input=source,
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode:
            raise SchemaError(f"Could not format generated Python: {result.stderr.strip()}")
        source = result.stdout
    return source
