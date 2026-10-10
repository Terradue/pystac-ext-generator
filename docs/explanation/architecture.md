<!--
Copyright 2026 Terradue

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
-->

# Architecture and validation

## From schema to source

The generator reads a full STAC Extension JSON Schema and follows references from
STAC object locations. Item metadata lives under `properties`; Collection and
Catalog metadata lives at the top level. Assets, item asset definitions, Links,
and Collection summaries are discovered through their respective containers.
Root type constraints restrict applicable branches. Unused definitions are not
turned into extension fields just because they exist.

The title supplies the extension class name, and `$id` supplies the registration
URI. Field names and constraints come from the schema, with no separate class,
URI, field-pointer, or target overrides.

The package separates these responsibilities:

| Component | Responsibility |
| --- | --- |
| `cli.py` | Load inputs, handle options, report diagnostics, and write output. |
| `bundle.py` | Copy and embed explicitly supplied or fetched external resources. |
| `schema.py` | Resolve local pointers and discover fields and STAC targets. |
| `models.py` | Build internal rendering metadata for nested classes and conversion plans. |
| `generator.py` | Validate the schema, render templates, and check output syntax. |
| Jinja2 templates | Emit the standalone extension and nested value classes. |

Change the input schema and regenerate to change an extension contract. Generated
files are artifacts; manual edits will be lost during regeneration.

## Runtime integration

A generated extension wraps an existing PySTAC object and writes its normal
metadata dictionaries. PySTAC handles serialization through `to_dict()` and
`from_dict()`. Nested generated values encode as plain JSON objects and arrays.

Call the generated class's `ext()` method directly. Generation does not install
into `pystac.extensions`, register an `item.ext` accessor, or provide migration
hooks. Extension membership checks the exact canonical schema version.

Generated modules depend on PySTAC and jsonschema. They embed their schema and
conversion metadata, so the generator and its template engine are not runtime
dependencies. Bundling external references enables offline extension validation.

## Validation boundaries

Generation validates the schema itself and parses the generated Python source.
It does not execute the emitted module or validate future data values.

At runtime, property annotations describe expected values. Setters and `apply()`
do not enforce every schema constraint. `apply()` checks all field names and
targets before mutation, then assigns values; it is not a general transactional
update if serialization of a later value fails. Nested factories enforce the
presence of unconditional required arguments.

Call `extension.validate()` to check the complete wrapped object against the
embedded extension schema, including bounds, formats, and conditional constraints.
For Assets, Links, and ItemAssetDefinitions, validation uses the owning STAC
object and requires an owner. Serialization alone does not validate metadata.

STAC core validation is separate: call the PySTAC object's `validate()` when you
also need those checks. Its schema resolution and network behavior are controlled
by PySTAC, not by the generated extension's embedded validator.

## Limitations

- Conditional applicability is approximated and produces a generation warning.
  Accessor availability does not establish that every combination is schema-valid.
- Standalone field-definition fragments do not identify STAC targets. Supply the
  complete extension schema and reference fields from their intended locations.
- Unprefixed STAC core/common metadata names are reserved during field discovery.
  Declared extension fields outside that set, such as `renders`, are supported.
- Recursive records are supported. Recursive non-object values can use `Any` at
  recursion boundaries and produce warnings; complex intersections can also have
  conservative annotations without losing validation constraints.
- Ambiguous nested object unions raise an error when no unique representation
  can be selected. Inspect raw properties or fix the data before decoding again.
- Heterogeneous pattern-property maps and tuple arrays remain raw JSON values
  with warnings. Dynamic property names do not become named accessors.
- Nested `$id` scopes, named anchors, `$dynamicRef`, `$recursiveRef`, and mixed
  schema dialects in bundles are rejected.
- Domain-specific calculations, migrations, and custom semantic helpers are not
  generated. Nested Band records can be modeled, but Band-level attachment helpers
  are not generated.

Use `--strict` when generation warnings should stop your build. Keep schema
sources under version control and review regenerated modules alongside schema changes.
