# pystac-ext-generator

A Python CLI that generates an independently importable, typed **PySTAC extension
module** from a STAC Extension JSON Schema. Uses Click, Jinja2, and PySTAC;
verification uses pytest and actual PySTAC objects. Version 0.2 adds generated nested
value classes following PySTAC Render conventions.

## Install and run

Requires Python 3.10+.

```bash
python -m pip install -e '.[test]'
pystac-ext-generator tests/fixtures/view.json -o view_extension.py
# Or use a URL:
pystac-ext-generator \
  https://stac-extensions.github.io/view/v1.1.0/schema.json \
  -o view_extension.py
```

For uv: `uv sync --extra test`, then `uv run pystac-ext-generator ...`.
For Hatch: `hatch run test`.

```python
from datetime import datetime, timezone
import pystac
from view_extension import ViewGeometryExtension

item = pystac.Item(
    id="example", geometry=None, bbox=None,
    datetime=datetime(2026, 1, 1, tzinfo=timezone.utc), properties={},
)
ext = ViewGeometryExtension.ext(item, add_if_missing=True)
ext.off_nadir = 15.0
ext.apply(sun_azimuth=180.0, sun_elevation=42.0)
ext.validate()  # Full extension schema; raises jsonschema.ValidationError.
assert item.properties["view:off_nadir"] == 15.0
```

The generated module requires `pystac>=1.12,<2`. Schema validation and decoding
object unions additionally require `jsonschema>=4.23,<5`. It does not import this generator,
Click, or Jinja2. The original (or bundled) schema is embedded for offline validation.
Use `item.validate()` separately if STAC core validation is also required.

## Generated API

- `Extension.ext(obj, add_if_missing=False)` wraps applicable Items, Assets,
  ItemAssetDefinitions, Collections, Catalogs, or Links. Applicable locations are
  discovered from the schema.
- `get_schema_uri()`, `add_to()`, `remove_from()`, and `has_extension()` manage the
  exact generated schema version. No implicit migration from another version.
- Typed getters/setters write Item `properties`, Collection/Catalog/Asset/Link
  `extra_fields`, or ItemAssetDefinition `properties`, as appropriate.
- Asset reads fall back to the owning Item, as PySTAC does. Explicit asset values,
  including null, take precedence; writes affect only the asset.
- `apply(**values)` updates only supplied Python field names. Unknown/inapplicable
  names are rejected before mutation. This is intentionally a partial-update API.
- Assigning `None` removes a field. `set_null("field")` writes explicit JSON null;
  `clear("field")` removes it. Required and nullable constraints are enforced by
  validation, not setters. Defaults are annotations and are not applied automatically.
- `Extension.summaries(collection, add_if_missing=True)` is generated when summary
  fields are discovered. It accepts lists, `pystac.RangeSummary`, and JSON Schema
  dictionaries, including switching between representations.
- Owned assets/links register on their owner. Detached assets can be wrapped with
  `add_if_missing=False`; registering or validating them requires an owner.

Use `ViewGeometryExtension.ext(item)`, not `item.ext.view`, for generated extensions.
Automatic registration in PySTAC's global accessor/hook registry is not performed.

## CLI options

```text
pystac-ext-generator SCHEMA [OPTIONS]
  -o, --output FILE       Write a module (default: stdout)
  --prefix PREFIX        Select namespace, without the colon
  --reference URI=FILE   Repeat for offline external schema mappings
  --resolve-external    Fetch and bundle external HTTP(S) schemas
  --strict              Fail on generation warnings
  --force               Allow overwriting an existing output file
  --version
```

`SCHEMA` accepts a UTF-8 JSON file, HTTP(S) URL, or `-` for stdin. Warnings go to
stderr, keeping stdout usable as Python source. Generation is deterministic.
Existing output files are protected unless `--force` is specified.

The schema is the source of generation metadata:

- `title` supplies the class name in PascalCase, with `Extension` appended if it
  is not already present. For example, `View Geometry Extension` becomes
  `ViewGeometryExtension`, `Rendering Extension` becomes `RenderingExtension`,
  and `STAC Storage Extension` becomes `STACStorageExtension`. A title containing
  letters or digits is required; leading digits receive the `Value` prefix.
- `$id` supplies the canonical HTTP(S) registration URI. A trailing empty fragment
  (`#`) is normalized away. The input filename or URL does not override `$id`.
- Fields and targets follow the schema's STAC locations and references: Item
  `properties`, Collection/Catalog top-level fields, `assets`, `item_assets`,
  `links`, and `summaries`. Root `type.const` and `type.enum` select object types.
  Referenced `definitions` and `$defs` are followed automatically. Unused field
  definitions do not imply applicability and are not scanned as standalone fields.

These locations follow the [STAC extension conventions](https://github.com/radiantearth/stac-spec/blob/master/extensions/README.md#general-conventions).
Without `--prefix`, one namespaced extension is inferred; multiple namespaces
require selecting one. Unprefixed fields outside the reserved STAC core/common
metadata names are also discovered, including `renders`. Python keywords and
reserved method names are escaped (`demo:class` → `class_`, `demo:apply` →
`apply_field`); the JSON keys are unchanged.

The CLI options `--class-name`, `--schema-uri`, `--fields-pointer`, and `--target`
and their Python API counterparts have been removed. Supply a complete extension
schema with its title, canonical identifier, and field placement. Existing users
must update imports to the title-derived class names when regenerating modules.

### External references

Internal JSON Pointers through `definitions` or `$defs` work automatically,
including recursion. External references must be bundled; they never silently
become `Any`. Enable HTTP fetching explicitly:

```bash
pystac-ext-generator \
  https://stac-extensions.github.io/storage/v2.0.0/schema.json \
  --resolve-external -o storage_extension.py
```

For reproducible/offline operation, map each external canonical URL to a local file:

```bash
pystac-ext-generator tests/fixtures/storage.json \
  --reference 'https://stac-extensions.github.io/storage/v2.0.0/platforms/aws-s3.json=tests/fixtures/platforms/aws-s3.json' \
  --reference 'https://stac-extensions.github.io/storage/v2.0.0/platforms/custom-s3.json=tests/fixtures/platforms/custom-s3.json' \
  --reference 'https://stac-extensions.github.io/storage/v2.0.0/platforms/ms-azure.json=tests/fixtures/platforms/ms-azure.json' \
  -o storage_extension.py
```

Relative external references resolve against the schema's canonical `$id`, not the
local filename. Bundling preserves cyclic references, has a 100-document limit,
and embeds external schemas. Referenced documents must use the same dialect.
HTTP operations use a 30-second timeout. Use trusted schema sources.

## Nested value classes (0.2)

Generate the Render example directly from the included upstream schema:

```bash
pystac-ext-generator tests/fixtures/render.json -o render_extension.py
```

```python
from render_extension import Render, RenderingExtension

ext = RenderingExtension.ext(item, add_if_missing=True)
ext.renders = {
    "overview": Render.create(
        assets=["red"],
        title="Red channel",
        rescale=[[0, 10000]],
    )
}

render = ext.renders["overview"]       # Render, not dict
render.title = "Updated preview"      # Updates the backing Item properties
render.apply(colormap_name="viridis") # Typed partial update
raw = render.to_dict()                # Plain JSON dictionary
ext.validate()
```

Generation produces real Python classes with:

- Typed getters/setters, a typed keyword-only `create()`, and typed partial `apply()`.
- Required factory arguments inferred from unconditional `required` constraints,
  including object `allOf` compositions. Reading a missing required member raises
  `pystac.STACError`. Conditional required constraints remain schema-validation rules.
- `from_dict(properties, copy=False)` and `to_dict()` with PySTAC-style live dictionary
  semantics, plus equality and readable representations. Unknown fields are preserved.
- Nested arrays (`list[Publication]`) and maps (`dict[str, Render]`) with recursive
  conversion in both directions. Reused references share a class; recursive record
  schemas use forward annotations rather than degrading the record to `Any`.
- Nullable/discriminated object unions, selected by schema validation. If JSON matches
  multiple different representations, the getter raises `ValueError`; inspect
  `.properties` or fix the data instead of relying on arbitrary branch ordering.

Class names use referenced definition names when meaningful, otherwise the containing
field path. Names are deterministic and collisions receive a numeric suffix. Equivalent
record shapes can share one class. `Render`, `Publication`, and recursive `Node` are
examples, not hardcoded extension-specific implementations.

**Mutation semantics:** nested object wrappers refer to their original dictionary.
Lists/maps containing wrappers are freshly constructed views: editing an object's
property is live, but adding/removing container entries requires assigning the container
back to its parent. Setting an extension or nested property serializes/copies generated
objects to plain JSON, so later mutations of the original assigned object are independent.
Asset getters can inherit an Item's value; changing such an inherited object changes the
Item's backing JSON. Assign an asset-local value first if an independent override is needed.

`create()` omits unspecified optionals and preserves explicit `None` as JSON null.
Setters and `apply()` treat `None` as removal; use `set_null(name)` for explicit null.
Call the parent extension's `validate()` to enforce the full schema. Factories enforce
argument presence, not all type/value constraints. Raw JSON dictionaries are accepted
at runtime for interoperability; getters return generated classes where modeled.

**Migration from 0.1:** nested record getters now return classes. For example,
`ext.publications[0]["citation"]` becomes `ext.publications[0].citation`; use
`ext.publications[0].to_dict()` when a raw dictionary is needed. Open-ended JSON objects
without declared members (such as Render's colormap) remain dictionaries.

## Python API and architecture

```python
import json
from pathlib import Path
from pystac_ext_generator import generate
from pystac_ext_generator.bundle import bundle

schema = json.loads(Path("schema.json").read_text())
# Optional: schema = bundle(schema, documents={canonical_uri: external_schema})
source, warnings = generate(schema, prefix="my")
Path("my_extension.py").write_text(source)
```

`schema.py` discovers extension fields through STAC object locations and references.
It follows `allOf`/`anyOf`/`oneOf`, common STAC double-negation asset patterns, and
summary requirements. It does not turn unrelated unused definitions into fields.
`models.py` builds the nested class graph and conversion plans.
`bundle.py` makes external references local. `generator.py` builds the template
context and checks Python syntax. `templates/extension.py.j2` and `templates/models.py.j2` own generated code.

## Scope and deliberate limits

This is a generic property-wrapper generator, **not a replacement for every
handwritten semantic helper in PySTAC**.

- Supports JSON Schema draft-07, 2019-09, and 2020-12; omitted dialect means 2020-12.
- Scalar types, arrays, typed maps, nullable unions, and scalar enums/consts become
  Python annotations (`Literal` for enums). Nested records become generated classes;
  open-ended objects remain dictionaries. Dates remain strings.
- Recursive records are modeled as classes. Recursive non-object value schemas
  still use `Any` at recursion boundaries and produce a warning. Complex non-record
  intersections can also use `Any`; schema validation retains all constraints.
- Applicability through conditional schemas is approximated and produces a warning.
  Accessor availability does not imply that all branch combinations are valid;
  call `validate()` after populating the object.
- Runtime setter validation, migrations, custom semantic methods, and automatic
  global extension hooks are not generated. Nested factories do require unconditional
  required fields; constructors wrapping existing dictionaries permit incomplete data.
- Dynamic property names do not get named accessors. Homogeneous maps can wrap
  their values; heterogeneous `patternProperties` maps remain raw and produce a warning.
  Tuple arrays retain raw members with a warning. Band-level STAC attachment helpers
  are not generated, though declared nested band record fields can become value classes.
- Nested `$id` scopes, named-anchor references, `$dynamicRef`, `$recursiveRef`, and
  mixed-dialect bundles are rejected. Normalize these before generation.
- The input must be the full extension schema; `validate()` validates that document.
  Standalone field-definition fragments do not establish STAC applicability.
- Selecting a namespace generates its accessors but retains the entire validation
  schema, including any cross-extension dependencies.

## Tests and build

```bash
python -m pytest -q
python -m build
```

Tests generate and import modules, then manipulate real PySTAC instances. Coverage
includes registration, owner checks, asset inheritance, item asset definitions,
collection summaries, catalog/link fields, round trips, schema constraints, safe
names/docstrings, nullable values, references, CLI output and overwrite protection.
The View and Render tests also compare generated behavior to PySTAC's own implementations.

Vendored upstream schemas keep tests offline. View, File, Scientific, and bundled
Storage, plus Render, have integration tests; Projection explicitly tests the diagnostic for
unbundled external references. See `tests/fixtures/README.md` for provenance.

GitHub Actions covers Python 3.10–3.14; tests run locally on Python 3.12.
