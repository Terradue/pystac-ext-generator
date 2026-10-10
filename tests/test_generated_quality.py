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
import subprocess
import sys
from pathlib import Path

import pystac
import pytest
from click.testing import CliRunner

from pystac_ext_generator import generate
from pystac_ext_generator.bundle import bundle
from pystac_ext_generator.cli import main

from .test_generator import FIXTURES, collection, custom, item, module, schema

PROJECT = Path(__file__).resolve().parents[1]


def _write_generated_fixtures(directory: Path, *, include_validation: bool) -> None:
    """Render real and synthetic schemas covering each conversion and signature shape."""
    documents = {name: schema(name) for name in ("themes", "view", "file", "render", "scientific")}
    storage = schema("storage")
    base = storage["$id"].rsplit("/", 1)[0]
    resources = {
        f"{base}/platforms/{path.name}": json.loads(path.read_text())
        for path in (FIXTURES / "platforms").glob("*.json")
    }
    documents["storage"] = bundle(storage, documents=resources)
    documents["wide_required"] = custom(
        {
            "demo:record": {
                "required": [f"field_{index}" for index in range(8)],
                "properties": {f"field_{index}": {"type": "integer"} for index in range(8)},
            }
        }
    )
    documents["recursive"] = custom(
        {"demo:node": {"$ref": "#/$defs/node"}},
        **{
            "$defs": {
                "node": {
                    "type": ["object", "null"],
                    "properties": {
                        "value": {"type": "string"},
                        "children": {"type": "array", "items": {"$ref": "#/$defs/node"}},
                    },
                },
            }
        },
    )
    documents["union"] = custom(
        {
            "demo:value": {
                "oneOf": [
                    {"properties": {"kind": {"const": "left"}}, "required": ["kind"]},
                    {"properties": {"kind": {"const": "right"}}, "required": ["kind"]},
                ]
            }
        }
    )
    documents["raw"] = custom({"demo:anything": {}, "demo:nullable": {"type": "null"}})
    for name, document in documents.items():
        source, _ = generate(document, include_validation=include_validation)
        assert not any(
            suppression in source for suppression in ("# noqa", "# type: ignore", "# nosec")
        )
        (directory / f"generated_{name}.py").write_text(source, encoding="utf-8")


@pytest.mark.parametrize("include_validation", [False, True])
def test_generated_modules_pass_quality_gates(tmp_path: Path, include_validation: bool) -> None:
    _write_generated_fixtures(tmp_path, include_validation=include_validation)
    config = str(PROJECT / "pyproject.toml")
    commands = (
        ("ruff", "format", "--check", "--config", config),
        ("ruff", "check", "--config", config),
        ("mypy", "--config-file", config),
        ("bandit", "-r"),
    )
    for command in commands:
        result = subprocess.run(
            [sys.executable, "-m", *command, str(tmp_path)],
            cwd=PROJECT,
            text=True,
            capture_output=True,
            check=False,
        )
        assert result.returncode == 0, f"{command}:\n{result.stdout}\n{result.stderr}"


@pytest.mark.parametrize("target", ["item", "collection", "catalog"])
def test_themes_serialization_and_roundtrip(target: str) -> None:
    generated = module(schema("themes"), include_validation=False)
    stac_object = {
        "item": item(),
        "collection": collection(),
        "catalog": pystac.Catalog("test", "test"),
    }[target]
    concept = generated.ThemeConcept.create(id="land-cover", title="Land cover")
    theme = generated.Theme.create(scheme="https://example.org/vocabulary", concepts=[concept])
    extension = generated.ThemesExtension.ext(stac_object, add_if_missing=True)
    extension.themes = [theme]
    expected = [
        {
            "scheme": "https://example.org/vocabulary",
            "concepts": [{"id": "land-cover", "title": "Land cover"}],
        }
    ]
    assert extension.properties["themes"] == expected
    restored = pystac.read_dict(stac_object.to_dict())
    assert generated.ThemesExtension.ext(restored).themes[0] == theme
    assert not hasattr(generated, "SCHEMA")
    assert not hasattr(extension, "validate")
    with pytest.raises(TypeError):
        hash(theme)


def test_cli_embedded_validation_is_opt_in() -> None:
    runner = CliRunner()
    document = schema("themes")
    default = runner.invoke(main, ["-"], input=json.dumps(document))
    embedded = runner.invoke(main, ["-", "--include-validation"], input=json.dumps(document))
    assert default.exit_code == embedded.exit_code == 0
    assert "jsonschema" not in default.output
    assert "SCHEMA:" not in default.output
    assert "def validate(" not in default.output
    assert "SCHEMA:" in embedded.output
    assert "def validate(" in embedded.output
    generated = module(document)
    extension = generated.ThemesExtension.ext(item(), True)
    extension.themes = [
        generated.Theme.create(
            scheme="vocabulary", concepts=[generated.ThemeConcept.create(id="concept")]
        )
    ]
    extension.validate()


def test_large_required_factory_checks_missing_and_unknown_arguments() -> None:
    fields = {f"field_{index}": {"type": "integer"} for index in range(8)}
    generated = module(
        custom({"demo:record": {"properties": fields, "required": list(fields)}}),
        include_validation=False,
    )
    values = {name: index for index, name in enumerate(fields)}
    record = generated.Record.create(**values)
    assert record.to_dict() == values
    with pytest.raises(TypeError, match="Missing required fields"):
        generated.Record.create(field_0=0)
    with pytest.raises(TypeError, match="Unknown fields"):
        generated.Record.create(**values, unknown=0)
    with pytest.raises(TypeError, match="Unknown fields"):
        record.apply(field_0=-1, unknown=0)
    assert record.field_0 == 0


def test_lean_union_still_resolves_nested_schema_branches() -> None:
    document = custom(
        {
            "demo:value": {
                "oneOf": [
                    {"properties": {"kind": {"const": "left"}}, "required": ["kind"]},
                    {"properties": {"kind": {"const": "right"}}, "required": ["kind"]},
                ]
            }
        }
    )
    generated = module(document, include_validation=False)
    extension = generated.DemoExtension.ext(item(), True)
    extension.value = {"kind": "left"}
    assert extension.value.kind == "left"
    assert hasattr(generated, "SCHEMA")
    assert not hasattr(extension, "validate")


def test_catalog_only_extension_rejects_collection_subclass() -> None:
    generated = module(
        {
            "$id": "https://example.org/catalog.json",
            "title": "Catalog Metadata",
            "properties": {"type": {"const": "Catalog"}, "demo:value": {"type": "string"}},
        },
        include_validation=False,
    )
    with pytest.raises(pystac.ExtensionTypeError):
        generated.CatalogMetadataExtension.ext(collection(), True)
