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

import pytest
from click.testing import CliRunner

from pystac_ext_generator import SchemaError, generate
from pystac_ext_generator.cli import main

from .test_generator import custom, module, schema


@pytest.mark.parametrize(
    "title,class_name",
    [
        ("View Geometry Extension", "ViewGeometryExtension"),
        (" custom-sensor data ", "CustomSensorDataExtension"),
        ("EO", "EOExtension"),
        ("STAC Storage Extension", "STACStorageExtension"),
        ("3D data", "Value3DDataExtension"),
    ],
)
def test_title_determines_class_name(title: str, class_name: str) -> None:
    document = custom({"demo:value": {"type": "string"}}, title=title)
    generated = module(document)
    extension_class = getattr(generated, class_name)
    assert extension_class.get_schema_uri() == document["$id"]


def test_missing_title_is_rejected() -> None:
    document = custom({"demo:value": {}})
    del document["title"]
    with pytest.raises(SchemaError, match="nonempty title"):
        generate(document)


@pytest.mark.parametrize("identifier", ["", "schema.json", "file:///schema.json"])
def test_noncanonical_schema_id_is_rejected(identifier: str) -> None:
    document = custom({"demo:value": {}}, **{"$id": identifier})
    with pytest.raises(SchemaError, match=r"absolute HTTP\(S\) \$id"):
        generate(document)


def test_missing_schema_id_is_rejected() -> None:
    document = custom({"demo:value": {}})
    del document["$id"]
    with pytest.raises(SchemaError, match=r"absolute HTTP\(S\) \$id"):
        generate(document)


def test_registration_uses_canonical_id_instead_of_input_filename() -> None:
    document = schema("file")
    generated = module(document)
    assert document["$id"].removesuffix("#") == generated.SCHEMA_URI
    assert document["$id"] == generated.SCHEMA["$id"]


@pytest.mark.parametrize("keyword", ["const", "enum"])
def test_schema_branches_determine_field_targets(keyword: str) -> None:
    branches = []
    for stac_type, properties in (
        ("Feature", {"properties": {"$ref": "#/$defs/item_fields"}}),
        (
            "Collection",
            {
                "demo:collection": {"type": "string"},
                "assets": {"additionalProperties": {"$ref": "#/$defs/asset_fields"}},
                "item_assets": {"additionalProperties": {"$ref": "#/$defs/asset_fields"}},
                "summaries": {"required": ["demo:item"]},
            },
        ),
        (
            "Catalog",
            {
                "demo:catalog": {"type": "string"},
                "links": {"items": {"$ref": "#/$defs/link_fields"}},
            },
        ),
    ):
        discriminator = stac_type if keyword == "const" else [stac_type]
        branches.append({"properties": {"type": {keyword: discriminator}, **properties}})
    document = custom({})
    del document["properties"]
    document["oneOf"] = branches
    document["$defs"] = {
        "item_fields": {"properties": {"demo:item": {"type": "number"}}},
        "asset_fields": {"properties": {"demo:asset": {"type": "number"}}},
        "link_fields": {"properties": {"demo:link": {"type": "number"}}},
        "unused": {"properties": {"demo:unused": {"type": "number"}}},
    }
    generated = module(document)
    assert generated.FIELD_TARGETS == {
        "demo:item": ["item", "summary"],
        "demo:asset": ["asset", "item_asset"],
        "demo:link": ["link"],
        "demo:collection": ["collection"],
        "demo:catalog": ["catalog"],
    }


def test_unused_field_definition_does_not_invent_target() -> None:
    document = custom({})
    document["$defs"] = {"fields": {"properties": {"demo:value": {"type": "string"}}}}
    with pytest.raises(SchemaError, match="No extension fields found at STAC object locations"):
        generate(document)


@pytest.mark.parametrize("option", ["--class-name", "--schema-uri", "--fields-pointer", "--target"])
def test_cli_rejects_removed_overrides(option: str) -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["-", option, "override"], input=json.dumps(schema("view")))
    assert result.exit_code != 0
    assert "No such option" in result.output
    assert option in result.output
    assert option not in runner.invoke(main, ["--help"]).output


@pytest.mark.parametrize("title", ["Properties Extension", "Summaries Extension"])
def test_title_cannot_shadow_pystac_base_classes(title: str) -> None:
    with pytest.raises(SchemaError, match="title conflicts"):
        generate(custom({"demo:value": {}}, title=title))
