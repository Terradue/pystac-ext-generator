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
from datetime import datetime, timezone
from pathlib import Path
from types import GenericAlias, ModuleType
from typing import Any, get_type_hints
from unittest.mock import patch

import jsonschema
import pystac
import pytest
from click.testing import CliRunner

from pystac_ext_generator import SchemaError, generate
from pystac_ext_generator.bundle import bundle
from pystac_ext_generator.cli import main

FIXTURES = Path(__file__).parent / "fixtures"


def schema(name: str) -> dict[str, Any]:
    """Load an object schema fixture by name."""
    document = json.loads((FIXTURES / f"{name}.json").read_text())
    assert isinstance(document, dict)
    return document


def module(
    document: dict[str, Any], *, prefix: str | None = None, include_validation: bool = True
) -> ModuleType:
    """Compile generated source into an isolated module for behavioral tests."""
    code, _ = generate(document, prefix=prefix, include_validation=include_validation)
    mod = ModuleType("generated")
    # Dataclasses resolve postponed annotations through the normal import registry.
    with patch.dict("sys.modules", {mod.__name__: mod}):
        exec(compile(code, "generated.py", "exec"), mod.__dict__)
    return mod


def item() -> pystac.Item:
    """Create an item with a fixed acquisition time."""
    return pystac.Item("test", None, None, datetime(2026, 1, 1, tzinfo=timezone.utc), {})


def collection() -> pystac.Collection:
    """Create a collection with global spatial coverage and an open temporal extent."""
    return pystac.Collection(
        "test",
        "test",
        pystac.Extent(
            pystac.SpatialExtent([-180, -90, 180, 90]),
            pystac.TemporalExtent([[datetime(2026, 1, 1, tzinfo=timezone.utc), None]]),
        ),
    )


def custom(fields: dict[str, Any], **extra: object) -> dict[str, Any]:
    """Wrap arbitrary field schemas in an item extension schema."""
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "$id": "https://example.org/demo/v1.0.0/schema.json",
        "title": "Demo Extension",
        "type": "object",
        "properties": {"properties": {"type": "object", "properties": fields}},
        **extra,
    }


def test_view_lifecycle_and_validation() -> None:
    off_nadir = 12.5
    azimuth = 55
    m = module(schema("view"))
    obj = item()
    with pytest.raises(pystac.ExtensionNotImplemented):
        m.ViewGeometryExtension.ext(obj)
    ext = m.ViewGeometryExtension.ext(obj, add_if_missing=True)
    ext.apply(off_nadir=off_nadir, sun_elevation=30)
    ext.validate()
    assert obj.to_dict()["properties"]["view:off_nadir"] == off_nadir
    ext.apply(azimuth=azimuth)
    assert ext.off_nadir == off_nadir  # apply is a partial update
    assert m.ViewGeometryExtension.ext(pystac.Item.from_dict(obj.to_dict())).azimuth == azimuth
    ext.off_nadir = 91
    with pytest.raises(jsonschema.ValidationError):
        ext.validate()
    ext.off_nadir = None
    assert "view:off_nadir" not in obj.properties
    m.ViewGeometryExtension.add_to(obj)
    assert obj.stac_extensions.count(m.SCHEMA_URI) == 1
    m.ViewGeometryExtension.remove_from(obj)
    assert not m.ViewGeometryExtension.has_extension(obj)


def test_view_matches_pystac_wrapper() -> None:
    from pystac.extensions.view import ViewExtension

    generated = module(schema("view")).ViewGeometryExtension
    a, b = item(), item()
    expected = ViewExtension.ext(a, add_if_missing=True)
    actual = generated.ext(b, add_if_missing=True)
    for key, value in {
        "off_nadir": 4,
        "incidence_angle": 15,
        "azimuth": 80,
        "sun_azimuth": 90,
        "sun_elevation": 20,
    }.items():
        setattr(expected, key, value)
        setattr(actual, key, value)
    assert a.properties == b.properties
    assert expected.off_nadir == actual.off_nadir


def test_asset_fallback_owner_and_precedence() -> None:
    item_angle = 10
    asset_angle = 20
    m = module(schema("view"))
    obj = item()
    obj.properties["view:off_nadir"] = item_angle
    asset = pystac.Asset("s3://bucket/a.tif")
    obj.add_asset("data", asset)
    ext = m.ViewGeometryExtension.ext(asset, add_if_missing=True)
    assert ext.off_nadir == item_angle
    ext.off_nadir = asset_angle
    assert ext.off_nadir == asset_angle
    assert obj.properties["view:off_nadir"] == item_angle
    assert asset.extra_fields["view:off_nadir"] == asset_angle
    ext.validate()
    detached = pystac.Asset("a.tif")
    with pytest.raises(pystac.STACError):
        m.ViewGeometryExtension.ext(detached, add_if_missing=True)
    with pytest.raises(pystac.STACError):
        m.ViewGeometryExtension.ext(detached).validate()


def test_item_asset_definition() -> None:
    off_nadir = 2
    m = module(schema("view"))
    obj = collection()
    definition = pystac.ItemAssetDefinition({"type": "image/tiff"}, owner=obj)
    ext = m.ViewGeometryExtension.ext(definition, add_if_missing=True)
    ext.off_nadir = off_nadir
    assert definition.properties["view:off_nadir"] == off_nadir
    assert m.SCHEMA_URI in obj.stac_extensions


def test_summaries_preserve_range_list_and_schema() -> None:
    m = module(schema("view"))
    obj = collection()
    ext = m.ViewGeometryExtension.summaries(obj, add_if_missing=True)
    ext.off_nadir = pystac.RangeSummary(1, 10)
    assert ext.off_nadir.minimum == 1
    assert obj.to_dict()["summaries"]["view:off_nadir"] == {"minimum": 1, "maximum": 10}
    ext.off_nadir = [1, 3]
    assert ext.off_nadir == [1, 3]
    ext.off_nadir = {"type": "number"}
    assert ext.off_nadir == {"type": "number"}
    ext.off_nadir = None
    assert ext.off_nadir is None
    with pytest.raises(pystac.ExtensionTypeError):
        m.ViewGeometryExtension.ext(obj)


def test_scientific_collection_and_nested_values() -> None:
    m = module(schema("scientific"))
    obj = collection()
    ext = m.ScientificCitationExtension.ext(obj, add_if_missing=True)
    ext.doi = "10.1234/example"
    ext.publications = [{"doi": "10.1234/paper", "citation": "A paper"}]
    ext.validate()
    assert obj.extra_fields["sci:doi"] == "10.1234/example"
    assert (
        get_type_hints(type(ext).publications.fget, m.__dict__)["return"]
        == GenericAlias(list, m.Publication) | None
    )
    assert ext.publications[0].citation == "A paper"


def test_file_asset_and_link() -> None:
    asset_size = 123
    link_size = 55
    m = module(schema("file"))
    obj = item()
    asset = pystac.Asset("a.tif")
    obj.add_asset("data", asset)
    ext = m.FileInfoExtension.ext(asset, add_if_missing=True)
    ext.apply(size=asset_size, byte_order="little-endian")
    ext.validate()
    assert asset.extra_fields["file:size"] == asset_size
    link = pystac.Link("related", "https://example.org/file")
    obj.add_link(link)
    m.FileInfoExtension.ext(link).size = link_size
    assert link.extra_fields["file:size"] == link_size
    with pytest.raises(pystac.ExtensionTypeError):
        m.FileInfoExtension.ext(obj)


def test_nullable_enum_keyword_and_safe_docstrings() -> None:
    m = module(
        custom(
            {
                "demo:class": {"enum": ["ok", "bad"]},
                "demo:property": {"type": "string"},
                "demo:apply": {"type": ["integer", "null"]},
                "demo:nothing": {"type": "null"},
                "demo:text": {"type": "string", "description": "'''\nimport os\n\"\"\""},
            }
        )
    )
    ext = m.DemoExtension.ext(item(), True)
    ext.class_ = "ok"
    ext.property_field = "works"
    ext.apply_field = 1
    ext.set_null("apply_field")
    assert "demo:apply" in ext.properties and ext.properties["demo:apply"] is None
    assert ext.nothing is None
    ext.clear("apply_field")
    assert "demo:apply" not in ext.properties
    get_type_hints(type(ext).class_.fget, m.__dict__)


def test_target_specific_fields_and_atomic_apply_names() -> None:
    doc = custom({"demo:a": {"type": "string"}})
    doc["properties"]["assets"] = {
        "additionalProperties": {"properties": {"demo:b": {"type": "integer"}}}
    }
    m = module(doc)
    ext = m.DemoExtension.ext(item(), True)
    with pytest.raises(pystac.ExtensionTypeError):
        ext.b = 2
    with pytest.raises(TypeError):
        ext.apply(a="changed", unknown="no")
    assert ext.a is None


def test_local_refs_unions_cycles_and_unused_definitions() -> None:
    doc = custom(
        {
            "demo:value": {"$ref": "#/$defs/value"},
            "demo:tree": {"type": "array", "items": {"$ref": "#/$defs/tree"}},
        }
    )
    doc["$defs"] = {
        "value": {"oneOf": [{"type": "string"}, {"type": "integer"}]},
        "tree": {"type": "array", "items": {"$ref": "#/$defs/tree"}},
        "unused": {"properties": {"alien:field": {"type": "string"}}},
    }
    code, warnings = generate(doc)
    assert "def value(self) -> str | int | None:" in code
    assert "def tree(self) -> list[list[Any]] | None:" in code
    assert "alien_field" not in code
    assert warnings


@pytest.mark.parametrize("name", ["view", "file", "scientific"])
def test_real_schemas_deterministic_and_importable(name: str) -> None:
    doc = schema(name)
    first = generate(doc)
    assert first == generate(doc)
    assert module(doc).FIELD_NAMES


@pytest.mark.parametrize("name", ["projection", "storage"])
def test_external_refs_fail_explicitly_without_bundle(name: str) -> None:
    with pytest.raises(SchemaError, match="External reference"):
        generate(schema(name))


def test_bundle_external_refs_and_offline_validation() -> None:
    doc = custom({"demo:score": {"$ref": "score.json#/definitions/score"}})
    external = {
        "$schema": doc["$schema"],
        "$id": "https://example.org/demo/v1.0.0/score.json",
        "definitions": {"score": {"type": "number", "minimum": 0}},
    }
    bundled = bundle(doc, documents={external["$id"]: external})
    m = module(bundled)
    ext = m.DemoExtension.ext(item(), True)
    ext.score = 3
    ext.validate()
    ext.score = -1
    with pytest.raises(jsonschema.ValidationError):
        ext.validate()
    assert "def score(self) -> float | None" in generate(bundled)[0]
    assert (
        doc["properties"]["properties"]["properties"]["demo:score"]["$ref"]
        == "score.json#/definitions/score"
    )


def test_bundle_cyclic_resources() -> None:
    doc = custom({"demo:tree": {"$ref": "tree.json"}})
    uri = "https://example.org/demo/v1.0.0/tree.json"
    ext = {"type": "array", "items": {"$ref": "tree.json"}}
    m = module(bundle(doc, documents={uri: ext}))
    assert m.FIELD_NAMES["tree"] == "demo:tree"


@pytest.mark.parametrize(
    "change,match",
    [
        ({"$id": None}, "Schema"),
        ({"properties": {}}, "No extension fields"),
        ({"type": 3}, "Invalid JSON Schema"),
    ],
)
def test_invalid_schemas(change: dict[str, object], match: str) -> None:
    with pytest.raises(SchemaError, match=match):
        generate({**custom({"demo:a": {"type": "integer"}}), **change})


@pytest.mark.parametrize("title", ["", "   ", "---"])
def test_invalid_schema_titles(title: str) -> None:
    with pytest.raises(SchemaError, match="nonempty title"):
        generate(custom({"demo:a": {"type": "integer"}}, title=title))


def test_referenced_unprefixed_fields_are_discovered() -> None:
    doc = {
        "$id": "https://example.org/ext/schema.json",
        "title": "Timestamps Extension",
        "properties": {
            "type": {"const": "Feature"},
            "properties": {"$ref": "#/$defs/fields"},
        },
        "$defs": {"fields": {"properties": {"expires": {"type": "string", "format": "date-time"}}}},
    }
    generated = module(doc)
    extension = generated.TimestampsExtension.ext(item(), True)
    extension.expires = "2030-01-01T00:00:00Z"
    assert extension.properties["expires"] == extension.expires
    assert generated.FIELD_TARGETS == {"expires": ["item"]}


def test_cli_stdout_file_stdin_force_and_errors(tmp_path: Path) -> None:
    runner = CliRunner()
    path = tmp_path / "view.py"
    args = [str(FIXTURES / "view.json"), "-o", str(path)]
    assert runner.invoke(main, args).exit_code == 0
    original = path.read_text()
    assert runner.invoke(main, args).exit_code != 0
    assert path.read_text() == original
    assert runner.invoke(main, [*args, "--force"]).exit_code == 0
    result = runner.invoke(main, ["-"], input=json.dumps(schema("view")))
    assert result.exit_code == 0
    assert result.stdout == original
    assert runner.invoke(main, ["-"], input="not json").exit_code != 0
    assert runner.invoke(main, ["--help"]).exit_code == 0


def test_cli_external_mapping(tmp_path: Path) -> None:
    doc = custom({"demo:a": {"$ref": "a.json"}})
    path = tmp_path / "external.json"
    path.write_text(json.dumps({"type": "integer"}))
    result = CliRunner().invoke(
        main,
        ["-", "--reference", f"https://example.org/demo/v1.0.0/a.json={path}"],
        input=json.dumps(doc),
    )
    assert result.exit_code == 0, result.output
    assert "def a(self) -> int | None" in result.stdout


def test_storage_bundled_real_platforms() -> None:
    doc = schema("storage")
    base = doc["$id"].rsplit("/", 1)[0]
    docs = {
        f"{base}/platforms/{p.name}": json.loads(p.read_text())
        for p in (FIXTURES / "platforms").glob("*.json")
    }
    m = module(bundle(doc, documents=docs))
    obj = item()
    ext = m.STACStorageExtension.ext(obj, True)
    ext.schemes = {
        "hot": {
            "type": "aws-s3",
            "bucket": "data",
            "region": "eu-west-1",
            "platform": "https://{bucket}.s3.{region}.amazonaws.com",
        }
    }
    ext.validate()
    assert obj.properties["storage:schemes"]["hot"]["type"] == "aws-s3"


def test_explicit_null_overrides_item_fallback() -> None:
    item_angle = 10
    m = module(schema("view"))
    obj = item()
    obj.properties["view:off_nadir"] = item_angle
    asset = pystac.Asset("a.tif")
    obj.add_asset("a", asset)
    ext = m.ViewGeometryExtension.ext(asset, True)
    ext.set_null("off_nadir")
    assert ext.off_nadir is None
    ext.clear("off_nadir")
    assert ext.off_nadir == item_angle


def test_null_only_annotations_resolve() -> None:
    m = module(custom({"demo:null": {"type": "null"}}))
    assert get_type_hints(m.DemoExtension.null.fget, m.__dict__)["return"] is type(None)


def test_catalog_fields() -> None:
    doc = {
        "$id": "https://example.org/catalog.json",
        "title": "Demo Extension",
        "properties": {"type": {"const": "Catalog"}, "demo:owner": {"type": "string"}},
    }
    m = module(doc)
    obj = pystac.Catalog("id", "description")
    ext = m.DemoExtension.ext(obj, True)
    ext.owner = "team"
    ext.validate()
    assert obj.to_dict()["demo:owner"] == "team"
    with pytest.raises(pystac.ExtensionTypeError):
        m.DemoExtension.ext(item(), True)


def test_allof_branch_discriminator_does_not_leak() -> None:
    doc = {
        "$id": "https://example.org/schema.json",
        "title": "Demo Extension",
        "oneOf": [
            {
                "allOf": [
                    {"properties": {"type": {"const": "Collection"}}},
                    {
                        "properties": {
                            "properties": {"properties": {"demo:bad": {"type": "string"}}}
                        }
                    },
                ]
            },
            {
                "properties": {
                    "type": {"const": "Feature"},
                    "properties": {"properties": {"demo:good": {"type": "string"}}},
                }
            },
        ],
    }
    m = module(doc)
    assert m.FIELD_NAMES == {"good": "demo:good"}


def test_invalid_external_mapping_and_strict_warnings() -> None:
    result = CliRunner().invoke(
        main, ["-", "--reference", "missing-equals"], input=json.dumps(custom({"demo:a": {}}))
    )
    assert result.exit_code == 1
    doc = custom({"demo:a": {}})
    doc["if"] = {"properties": {"properties": {"required": ["demo:a"]}}}
    result = CliRunner().invoke(main, ["-", "--strict"], input=json.dumps(doc))
    assert result.exit_code == 1
    assert "Conditional applicability" in result.output


def test_cli_http_schema(monkeypatch: pytest.MonkeyPatch) -> None:
    import importlib
    import io

    bundle_module = importlib.import_module("pystac_ext_generator.bundle")

    monkeypatch.setattr(
        bundle_module,
        "urlopen",
        lambda url, timeout: io.BytesIO(json.dumps(schema("view")).encode()),
    )
    result = CliRunner().invoke(main, ["https://example.org/schema.json"])
    assert result.exit_code == 0
    assert "class ViewGeometryExtension" in result.stdout


def test_json_pointer_escaping() -> None:
    doc = custom({"demo:a": {"$ref": "#/$defs/a~1b~0c"}})
    doc["$defs"] = {"a/b~c": {"type": "integer"}}
    assert "def a(self) -> int | None" in generate(doc)[0]


def test_boolean_schemas() -> None:
    doc = custom({"demo:free": True})
    doc["properties"]["type"] = True
    doc["properties"]["assets"] = {"not": False, "additionalProperties": False}
    m = module(doc)
    assert m.FIELD_NAMES == {"free": "demo:free"}


def test_namespace_selection_and_name_collision() -> None:
    doc = custom({"a:one": {}, "b:two": {}})
    with pytest.raises(SchemaError, match="Multiple namespaces"):
        generate(doc)
    assert module(doc, prefix="a").FIELD_NAMES == {"one": "a:one"}
    m = module(custom({"demo:a-b": {}, "demo:a_b": {}}))
    assert set(m.FIELD_NAMES.values()) == {"demo:a-b", "demo:a_b"}


def test_schema_defaults_do_not_mutate_instances() -> None:
    m = module(custom({"demo:tags": {"type": "array", "items": {"type": "string"}, "default": []}}))
    a, b = m.DemoExtension.ext(item(), True), m.DemoExtension.ext(item(), True)
    assert a.tags is None and b.tags is None
    a.tags = ["one"]
    assert b.tags is None
