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

# CLI reference

```text
pystac-ext-generator [OPTIONS] SCHEMA
```

`SCHEMA` is a JSON file path, HTTP(S) URL, or `-` for stdin.

| Option | Behavior |
| --- | --- |
| `-o`, `--output FILE` | Write generated Python to a file; default is stdout. |
| `--prefix PREFIX` | Select a field namespace without its colon when multiple namespaces occur. |
| `--reference URI=FILE` | Supply an offline external schema mapping; repeat as needed. |
| `--resolve-external` | Fetch missing external HTTP(S) schema resources. |
| `--strict` | Treat generation warnings as errors. |
| `--force` | Permit overwriting the output file. |
| `--version` | Print the version from the package's shared version source. |
| `-h`, `--help` | Print usage information. |

## Schema-derived settings

| Schema content | Generated result |
| --- | --- |
| `title` | PascalCase class name, with `Extension` appended if absent. |
| `$id` | Canonical HTTP(S) registration URI; a trailing empty `#` is removed. |
| Field placement and references | Accessors at the applicable STAC object locations. |
| Root `properties.type.const` or `enum` | Object-type restrictions for the schema branch. |
| Object properties, required members, and references | Nested value classes and their factory parameters. |

For example, `View Geometry Extension` produces `ViewGeometryExtension`, and
`STAC Storage Extension` produces `STACStorageExtension`. A title must contain
ASCII letters or digits. Leading digits receive the prefix `Value`. Titles that
collide with PySTAC base classes are rejected.

The removed options `--class-name`, `--schema-uri`, `--fields-pointer`, and
`--target` are not accepted. Their former Python API counterparts are also
removed. Put that information in the full extension schema and update generated
class imports when migrating from namespace-derived naming.

## Output and errors

Generated Python is deterministic for the same schema and options. Output
parent directories are created when needed. Existing files are preserved unless
`--force` is given. Generation warnings and file-output notices go to stderr.
Errors produce a nonzero exit status, including invalid schemas, missing external
resources, unsupported reference scopes, and fields that cannot be discovered.

The generator supports JSON Schema draft-07, 2019-09, and 2020-12. If `$schema`
is absent, validation uses draft 2020-12. See [limitations](../explanation/architecture.md#limitations)
for unsupported constructs.
