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

"""Behavioral tests for generated nested classes using real PySTAC objects."""

from __future__ import annotations

import inspect
import json
from types import GenericAlias
from typing import get_type_hints

import jsonschema
import pystac
import pytest

from pystac_ext_generator import generate

from .test_generator import collection, custom, item, module, schema


def test_render_classes_and_round_trip() -> None:
    m = module(schema("render"))
    obj = item()
    obj.add_asset("red", pystac.Asset("red.tif"))
    ext = m.RenderingExtension.ext(obj, True)
    render = m.Render.create(assets=["red"], title="Red channel", rescale=[[0, 10000]])
    ext.renders = {"overview": render}
    assert isinstance(ext.renders["overview"], m.Render)
    assert ext.renders["overview"].assets == ["red"]
    assert obj.to_dict()["properties"]["renders"]["overview"] == render.to_dict()
    ext.validate()
    reloaded = pystac.Item.from_dict(json.loads(json.dumps(obj.to_dict())))
    again = m.RenderingExtension.ext(reloaded)
    assert again.renders["overview"] == render
    assert (
        get_type_hints(m.RenderingExtension.renders.fget, m.__dict__)["return"]
        == GenericAlias(dict, (str, m.Render)) | None
    )
    # Value changes through wrappers are live, container additions need reassignment.
    again.renders["overview"].title = "Changed"
    assert reloaded.properties["renders"]["overview"]["title"] == "Changed"
    render.title = "Independent source"
    assert obj.properties["renders"]["overview"]["title"] == "Red channel"


def test_render_matches_handwritten_pystac() -> None:
    from pystac.extensions.render import Render

    m = module(schema("render"))
    expected = Render.create(assets=["red"], title="Red", rescale=[[0, 1]])
    actual = m.Render.create(assets=["red"], title="Red", rescale=[[0, 1]])
    assert actual.to_dict() == expected.to_dict()
    actual.title = expected.title = None
    assert actual.to_dict() == expected.to_dict()
    assert "assets" in inspect.signature(m.Render.create).parameters
    assert (
        inspect.signature(m.Render.create).parameters["assets"].default is inspect.Parameter.empty
    )
    with pytest.raises(TypeError):
        m.Render.create()
    with pytest.raises(pystac.STACError, match="assets"):
        _ = m.Render({}).assets


def test_render_collection() -> None:
    m = module(schema("render"))
    obj = collection()
    obj.add_asset("red", pystac.Asset("red.tif"))
    ext = m.RenderingExtension.ext(obj, True)
    ext.renders = {"overview": m.Render.create(assets=["red"])}
    ext.validate()
    assert obj.extra_fields["renders"]["overview"]["assets"] == ["red"]


def test_nested_arrays_maps_and_deep_serialization() -> None:
    original_value = 4
    updated_value = 5
    leaf = {"type": "object", "required": ["value"], "properties": {"value": {"type": "number"}}}
    doc = custom(
        {
            "demo:config": {
                "type": "object",
                "properties": {
                    "children": {"type": "array", "items": {"$ref": "#/$defs/leaf"}},
                    "named": {"type": "object", "additionalProperties": {"$ref": "#/$defs/leaf"}},
                    "matrix": {
                        "type": "array",
                        "items": {"type": "array", "items": {"$ref": "#/$defs/leaf"}},
                    },
                },
            }
        }
    )
    doc["$defs"] = {"leaf": leaf}
    m = module(doc)
    leaf_value = m.Leaf.create(value=original_value)
    config = m.Config.create(children=[leaf_value], named={"a": leaf_value}, matrix=[[leaf_value]])
    ext = m.DemoExtension.ext(item(), True)
    ext.config = config
    assert isinstance(ext.config.children[0], m.Leaf)
    assert isinstance(ext.config.named["a"], m.Leaf)
    assert isinstance(ext.config.matrix[0][0], m.Leaf)
    ext.config.named["a"].value = updated_value
    assert ext.properties["demo:config"]["named"]["a"]["value"] == updated_value
    assert ext.config.children[0].value == original_value
    json.dumps(ext.obj.to_dict())
    ext.validate()


def test_recursive_object_graph_and_reused_reference() -> None:
    doc = custom({"demo:tree": {"$ref": "#/$defs/node"}, "demo:other": {"$ref": "#/$defs/node"}})
    doc["$defs"] = {
        "node": {
            "type": "object",
            "required": ["name"],
            "properties": {
                "name": {"type": "string"},
                "children": {"type": "array", "items": {"$ref": "#/$defs/node"}},
            },
        }
    }
    m = module(doc)
    root = m.Node.create(name="root", children=[m.Node.create(name="leaf")])
    ext = m.DemoExtension.ext(item(), True)
    ext.tree = root
    assert ext.tree.children[0].name == "leaf"
    assert len(m._MODELS) == 1
    assert (
        get_type_hints(m.Node.children.fget, m.__dict__)["return"]
        == GenericAlias(list, m.Node) | None
    )
    ext.tree.children[0].name = "updated"
    assert ext.properties["demo:tree"]["children"][0]["name"] == "updated"
    ext.validate()


def test_mutually_recursive_classes() -> None:
    doc = custom({"demo:root": {"$ref": "#/$defs/a"}})
    doc["$defs"] = {
        "a": {"properties": {"label": {"type": "string"}, "child": {"$ref": "#/$defs/b"}}},
        "b": {"properties": {"count": {"type": "integer"}, "parent": {"$ref": "#/$defs/a"}}},
    }
    m = module(doc)
    value = m.A.create(label="a", child=m.B.create(count=2, parent=m.A.create(label="last")))
    assert isinstance(value.child, m.B)
    assert isinstance(value.child.parent, m.A)
    assert value.child.parent.label == "last"


def test_required_nullable_optional_and_unknown_members() -> None:
    vendor_value = 4
    doc = custom(
        {
            "demo:config": {
                "type": "object",
                "required": ["choice"],
                "properties": {
                    "choice": {"type": ["string", "null"]},
                    "text": {"type": "string"},
                    "class": {"type": "string"},
                    "result": {"type": "integer"},
                },
            }
        }
    )
    m = module(doc)
    value = m.Config.create(choice=None, class_="class", result_field=2)
    assert value.choice is None
    assert "text" not in value.to_dict()
    value.properties["vendor:extra"] = {"n": vendor_value}
    value.apply(text="hello")
    value.text = None
    assert "text" not in value.to_dict()
    assert value.properties["vendor:extra"] == {"n": vendor_value}
    value.set_null("text")
    assert value.to_dict()["text"] is None
    value.clear("text")
    assert value != {"choice": None}
    copied = m.Config.from_dict(value.to_dict(), copy=True)
    copied.properties["vendor:extra"]["n"] = 5
    assert value.properties["vendor:extra"]["n"] == vendor_value
    with pytest.raises(TypeError):
        value.apply(choice="mutated", unknown=1)
    assert value.choice is None


def test_allof_merges_record_fields_and_requirements() -> None:
    required_count = 2
    doc = custom(
        {
            "demo:thing": {
                "allOf": [
                    {"type": "object", "required": ["a"], "properties": {"a": {"type": "string"}}},
                    {"type": "object", "required": ["b"], "properties": {"b": {"type": "integer"}}},
                ]
            }
        }
    )
    m = module(doc)
    obj = m.Thing.create(a="one", b=required_count)
    assert obj.a == "one" and obj.b == required_count
    with pytest.raises(TypeError):
        m.Thing.create(a="one")


def test_discriminated_object_union_and_nullable_object() -> None:
    doc = custom(
        {
            "demo:result": {"oneOf": [{"$ref": "#/$defs/good"}, {"$ref": "#/$defs/bad"}]},
            "demo:optional": {"anyOf": [{"$ref": "#/$defs/good"}, {"type": "null"}]},
        }
    )
    doc["$defs"] = {
        "good": {
            "type": "object",
            "required": ["kind", "value"],
            "properties": {"kind": {"const": "good"}, "value": {"type": "integer"}},
        },
        "bad": {
            "type": "object",
            "required": ["kind", "reason"],
            "properties": {"kind": {"const": "bad"}, "reason": {"type": "string"}},
        },
    }
    m = module(doc)
    ext = m.DemoExtension.ext(item(), True)
    ext.result = m.Good.create(kind="good", value=3)
    assert isinstance(ext.result, m.Good)
    ext.result = m.Bad.create(kind="bad", reason="failure")
    assert isinstance(ext.result, m.Bad)
    ext.optional = m.Good.create(kind="good", value=1)
    assert isinstance(ext.optional, m.Good)
    ext.set_null("optional")
    assert ext.optional is None
    ext.validate()


def test_ambiguous_union_is_not_guessed() -> None:
    doc = custom(
        {
            "demo:value": {
                "anyOf": [
                    {"type": "object", "properties": {"a": {"type": "string"}}},
                    {"type": "object", "properties": {"b": {"type": "integer"}}},
                ]
            }
        }
    )
    m = module(doc)
    ext = m.DemoExtension.ext(item(), True)
    ext.value = {"a": "a", "b": 2}
    with pytest.raises(ValueError, match="unique representation"):
        _ = ext.value
    assert ext.properties["demo:value"]["a"] == "a"


def test_invalid_nested_constraints_detected() -> None:
    m = module(schema("render"))
    ext = m.RenderingExtension.ext(item(), True)
    ext.renders = {"bad": m.Render.create(assets="wrong")}
    with pytest.raises(jsonschema.ValidationError):
        ext.validate()


def test_class_name_collision_and_determinism() -> None:
    doc = custom(
        {
            "demo:foo-extension": {"properties": {"a": {"type": "string"}}},
            "demo:foo-bar": {"properties": {"b": {"type": "string"}}},
            "demo:foo_bar": {"properties": {"c": {"type": "integer"}}},
        }
    )
    doc["title"] = "Foo"
    code, _ = generate(doc)
    assert "class FooExtension2(_Object)" in code
    assert code == generate(doc)[0]
    m = module(doc)
    assert set(m._MODELS) == {"FooExtension2", "FooBar", "DemoFooBar"}


def test_asset_nested_fallback_view_and_map_membership() -> None:
    updated_value = 2
    new_value = 3
    doc = custom(
        {
            "demo:objects": {
                "type": "object",
                "additionalProperties": {"properties": {"value": {"type": "integer"}}},
            }
        }
    )
    doc["properties"]["assets"] = {"additionalProperties": doc["properties"]["properties"]}
    m = module(doc)
    obj = item()
    ext = m.DemoExtension.ext(obj, True)
    ext.objects = {"a": {"value": 1}}
    asset = pystac.Asset("a.tif")
    obj.add_asset("a", asset)
    asset_ext = m.DemoExtension.ext(asset)
    asset_ext.objects["a"].value = updated_value
    assert obj.properties["demo:objects"]["a"]["value"] == updated_value
    view = ext.objects
    view["b"] = type(view["a"]).create(value=new_value)
    assert "b" not in obj.properties["demo:objects"]
    ext.objects = view
    assert obj.properties["demo:objects"]["b"]["value"] == new_value


def test_nullable_record_type_array_and_recursion() -> None:
    doc = custom({"demo:node": {"$ref": "#/$defs/node"}})
    doc["$defs"] = {
        "node": {
            "type": ["object", "null"],
            "properties": {"label": {"type": "string"}, "child": {"$ref": "#/$defs/node"}},
        }
    }
    m = module(doc)
    value = m.Node.create(label="root", child=m.Node.create(label="child"))
    assert isinstance(value.child, m.Node)
    ext = m.DemoExtension.ext(item(), True)
    ext.node = value
    assert ext.node.child.label == "child"
    ext.set_null("node")
    assert ext.node is None
    ext.validate()


def test_scalar_object_union_with_shared_properties() -> None:
    doc = custom(
        {"demo:value": {"type": ["string", "object"], "properties": {"label": {"type": "string"}}}}
    )
    m = module(doc)
    ext = m.DemoExtension.ext(item(), True)
    ext.value = "plain"
    assert ext.value == "plain"
    ext.value = {"label": "object"}
    assert ext.value.label == "object"
