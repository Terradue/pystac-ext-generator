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

# Generated classes and fields

Every generated module contains an extension class named from the schema title.
Nested record schemas produce value classes, and summary fields produce a
`Summaries<ClassName>` helper. No domain-specific extension classes are built in.

## Field naming and types

The namespace is removed from Python attribute names: `quality:score` becomes
`score`. JSON keys remain unchanged. Invalid identifier characters are normalized;
Python keywords and wrapper-method collisions are escaped, such as `class_` and
`apply_field`. Remaining ambiguous names can cause a generation error.

| JSON Schema shape | Python representation |
| --- | --- |
| `string`, including date/time formats | `str`; format validation happens during `validate()`. |
| `number`, `integer`, `boolean`, `null` | `float`, `int`, `bool`, `None`. |
| Scalar `enum` or `const` | `Literal[...]` where representable. |
| Array with homogeneous items | `list[...]`. |
| Object with declared members | Generated nested value class. |
| Homogeneous additional-properties map | `dict[str, ...]`, with typed values where supported. |
| Open-ended object | Raw dictionary. |
| `oneOf` / `anyOf` | Union annotations; nested codecs use schema validation to choose a representation. |

Absent extension fields return `None`. Setters preserve JSON values; annotations
do not automatically coerce dates into `datetime` or enforce numeric bounds.
The whole schema remains authoritative for validation.

## Extension operations

| Operation | Contract |
| --- | --- |
| `Extension.ext(obj, add_if_missing=False)` | Wrap a supported target and check extension membership; optionally register it. |
| `get_schema_uri()` | Return the canonical registration URI. |
| `has_extension()`, `add_to()`, `remove_from()` | Manage the exact schema version on a STAC object. |
| Typed properties | Read or write fields at the appropriate storage location. |
| `apply(**values)` | Update supplied Python field names; precheck unknown/inapplicable names. |
| `clear(name)` | Remove a field by its Python name. |
| `set_null(name)` | Store explicit JSON null; schema validation determines whether it is allowed. |
| `validate()` | Validate the wrapped STAC object, or its owner, against the embedded extension schema. |
| `summaries(collection, add_if_missing=False)` | Wrap Collection summaries when supported by the schema. |

Items store fields in `properties`; Collections, Catalogs, Assets, and Links use
`extra_fields`; ItemAssetDefinitions use `properties`. Assets fall back to Item
properties for missing values. Summary helpers preserve lists, ranges, and schema
objects. They expose field properties, rather than an extension-style `apply()`.

## Nested value classes

Nested classes provide `create()`, `from_dict(properties, copy=False)`, `to_dict()`,
typed properties, `apply()`, `clear()`, and `set_null()`. Required factory arguments
come from unconditional requirements, including merged `allOf` object fields.
`create()` preserves explicit `None`; setters and `apply()` remove fields assigned
`None`. Unknown JSON properties survive round-trips.

Class names use reference names when meaningful, otherwise field naming hints.
Collisions receive numeric suffixes, equivalent shapes may share a class, and
recursive records use forward annotations. See [mutation semantics](../how-to/use-extension.md#edit-nested-values)
for live views versus copied assignments.

## Module metadata

- `SCHEMA`: the original or bundled schema used for validation.
- `SCHEMA_URI`: canonical registration identifier.
- `FIELD_NAMES`: Python attribute names mapped to JSON keys.
- `FIELD_TARGETS`: JSON keys mapped to their discovered targets.
- `TARGETS`: the module's combined applicability.
