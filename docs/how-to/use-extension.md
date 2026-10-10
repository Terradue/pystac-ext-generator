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

# Use generated extension classes

The first examples continue from the `item` and `extension` created in the
[tutorial](../tutorials/first-steps.md).

## Update or remove fields

```python
extension.apply(score=0.8)
assert extension.details.method == "manual"  # Omitted fields are preserved.
extension.details = None
assert "quality:details" not in item.properties
extension.clear("score")
assert "quality:score" not in item.properties
extension.score = 0.9
```

`apply()` uses generated Python attribute names and updates only supplied fields.
Unknown or inapplicable names are rejected before any update. Assigning `None`
or calling `clear()` removes a field. To store explicit JSON null, use
`set_null("score")`; the tutorial schema does not allow null for score, so
subsequent validation would reject it.

## Attach asset metadata

```python
asset = pystac.Asset("https://example.org/image.tif", media_type="image/tiff")
item.add_asset("image", asset)
asset_extension = QualityExtension.ext(asset)
assert asset_extension.score == 0.9  # Falls back to the owning Item.
asset_extension.score = 0.7
assert asset.extra_fields["quality:score"] == 0.7
assert extension.score == 0.9
asset_extension.validate()
```

An Asset reads missing fields from its owning Item. An explicit asset value,
including JSON null, takes precedence. Writes affect the Asset. Registration and
full-schema validation use its owner, so attach assets before those operations.
The same ownership requirement applies to Links and ItemAssetDefinitions.
Only schema-discovered targets can be wrapped.

## Edit nested values

```python
extension.details = QualityDetails.create(method="automatic", samples=24)
extension.details.method = "reviewed"
assert item.properties["quality:details"]["method"] == "reviewed"
extension.validate()
```

Nested wrappers expose `create()`, `from_dict()`, `to_dict()`, typed properties,
and partial `apply()`. `create()` requires unconditionally required members, but
full schema constraints are checked by the parent extension's `validate()`.
Required nullable members may be supplied as `None` when the schema allows it.

Nested property edits update the underlying JSON. Containers of wrappers are
fresh views: after adding or removing list/map entries, assign the container
back to its property. Assigning a nested object copies its serialized data; later
changes to the original object do not change the assigned copy.

## Use a Collection summary helper

From the repository checkout, generate the included View schema:

```bash
pystac-ext-generator tests/fixtures/view.json -o view_extension.py
```

```python
from datetime import datetime, timezone

import pystac

from view_extension import ViewGeometryExtension

collection = pystac.Collection(
    id="view-example",
    description="Images with viewing geometry",
    extent=pystac.Extent(
        pystac.SpatialExtent([-180, -90, 180, 90]),
        pystac.TemporalExtent([[datetime(2026, 1, 1, tzinfo=timezone.utc), None]]),
    ),
)
summaries = ViewGeometryExtension.summaries(collection, add_if_missing=True)
summaries.off_nadir = pystac.RangeSummary(0, 30)
assert summaries.off_nadir.maximum == 30
summaries.off_nadir = None
```

Summary helpers are generated only for fields found under Collection summaries.
They preserve lists, range summaries, and JSON Schema dictionaries, and do not
aggregate Item values automatically. Top-level Collection fields use `ext()`
when the schema declares that target; summary-only support does not imply it.
