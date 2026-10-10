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

from __future__ import annotations

import json
from unittest.mock import patch

import jsonschema
import pytest
from click.testing import CliRunner

from pystac_ext_generator import SchemaError, generate
from pystac_ext_generator.bundle import bundle, json_graph
from pystac_ext_generator.cli import main

from .test_generator import FIXTURES, custom, item, module, schema


def test_storage_resolves_three_external_resources_before_modeling() -> None:
    document = schema("storage")
    original = json.dumps(document)
    base = document["$id"].rsplit("/", 1)[0]
    resources = {
        f"{base}/platforms/{name}.json": json.loads(
            (FIXTURES / "platforms" / f"{name}.json").read_text()
        )
        for name in ("aws-s3", "custom-s3", "ms-azure")
    }
    with patch(
        "pystac_ext_generator.generator.fetch_http", side_effect=resources.__getitem__
    ) as fetch:
        generated = module(document)
    assert [call.args[0] for call in fetch.call_args_list] == list(resources)
    assert '"$ref"' not in json.dumps(generated.SCHEMA)
    assert json.dumps(document) == original
    extension = generated.STACStorageExtension.ext(item(), True)
    extension.schemes = {"azure": {"type": "ms-azure", "platform": "invalid", "account": "example"}}
    with pytest.raises(jsonschema.ValidationError):
        extension.validate()
    extension.schemes = {
        "azure": {
            "type": "ms-azure",
            "platform": "https://{account}.blob.core.windows.net",
            "account": "example",
        }
    }
    extension.validate()


def test_cli_resolves_external_references_without_flag() -> None:
    document = custom({"demo:value": {"$ref": "value.json"}})
    with patch(
        "pystac_ext_generator.generator.fetch_http", return_value={"type": "integer"}
    ) as fetch:
        result = CliRunner().invoke(main, ["-"], input=json.dumps(document))
    assert result.exit_code == 0, result.output
    assert "def value(self) -> int | None" in result.stdout
    fetch.assert_called_once_with("https://example.org/demo/v1.0.0/value.json")


def test_nested_resource_ids_and_relative_references() -> None:
    document = custom(
        {"demo:score": {"$ref": "parts/container.json"}},
        **{"$defs": {"container": {"$id": "parts/container.json", "$ref": "number.json"}}},
    )
    resource = {"type": "integer", "minimum": 5}
    with patch("pystac_ext_generator.generator.fetch_http", return_value=resource) as fetch:
        generated = module(document)
    fetch.assert_called_once_with("https://example.org/demo/v1.0.0/parts/number.json")
    extension = generated.DemoExtension.ext(item(), True)
    extension.score = 3
    with pytest.raises(jsonschema.ValidationError):
        extension.validate()


@pytest.mark.parametrize("keyword", ["default", "const", "enum", "examples"])
def test_literal_reference_values_are_not_resolved(keyword: str) -> None:
    literal = {"$ref": "this-is-data.json", "$id": "also-data"}
    value = [literal] if keyword in {"enum", "examples"} else literal
    document = custom({"demo:value": {"type": "object", keyword: value}})
    resolved = bundle(document)
    assert resolved["properties"]["properties"]["properties"]["demo:value"][keyword] == value


def test_modern_reference_siblings_retain_both_constraints() -> None:
    document = custom(
        {"demo:value": {"$ref": "#/$defs/base", "minimum": 5}},
        **{
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$defs": {"base": {"type": "integer", "minimum": 10}},
        },
    )
    generated = module(document)
    extension = generated.DemoExtension.ext(item(), True)
    extension.value = 7
    with pytest.raises(jsonschema.ValidationError):
        extension.validate()
    extension.value = 10
    extension.validate()


def test_external_recursive_resource_remains_valid_offline() -> None:
    document = custom({"demo:tree": {"$ref": "tree.json"}})
    uri = "https://example.org/demo/v1.0.0/tree.json"
    tree = {
        "$id": uri,
        "type": "object",
        "properties": {"child": {"$ref": "#"}, "label": {"type": "integer"}},
    }
    resolved = bundle(document, documents={uri: tree})
    json.dumps(json_graph(resolved))
    generated = module(resolved)
    extension = generated.DemoExtension.ext(item(), True)
    extension.tree = {"child": {"label": "invalid"}}
    with pytest.raises(jsonschema.ValidationError):
        extension.validate()
    extension.tree = {"child": {"label": 1}}
    extension.validate()


def test_missing_local_reference_is_reported_before_modeling() -> None:
    with pytest.raises(SchemaError, match="Could not resolve schema references"):
        generate(custom({"demo:value": {"$ref": "#/$defs/missing"}}))


@pytest.mark.parametrize("include_validation", [False, True])
def test_recursive_union_branches_use_their_own_schema_root(include_validation: bool) -> None:
    document = custom(
        {"demo:tree": {"oneOf": [{"type": "null"}, {"$ref": "#/$defs/node"}]}},
        **{
            "$defs": {
                "node": {
                    "type": "object",
                    "properties": {
                        "label": {"type": "integer"},
                        "child": {"$ref": "#/$defs/node"},
                    },
                }
            }
        },
    )
    generated = module(document, include_validation=include_validation)
    extension = generated.DemoExtension.ext(item(), True)
    child_label = 2
    extension.tree = {"label": 1, "child": {"label": child_label}}
    assert extension.tree.child.label == child_label
    extension.tree = {"child": {"label": "invalid"}}
    with pytest.raises(ValueError, match="no unique representation"):
        _ = extension.tree
