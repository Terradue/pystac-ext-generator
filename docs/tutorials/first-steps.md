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

# Generate your first extension

[Install the CLI](../how-to/install.md), then work in an empty directory. This
example defines a small quality-metadata extension for Items and their Assets.

## 1. Save the extension schema

Save the following as `quality-schema.json`:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://example.org/quality/v1.0.0/schema.json",
  "title": "Quality Extension",
  "type": "object",
  "required": ["type", "stac_extensions", "properties"],
  "properties": {
    "type": {"const": "Feature"},
    "stac_extensions": {
      "type": "array",
      "contains": {"const": "https://example.org/quality/v1.0.0/schema.json"}
    },
    "properties": {"$ref": "#/$defs/fields"},
    "assets": {
      "type": "object",
      "additionalProperties": {"$ref": "#/$defs/fields"}
    }
  },
  "$defs": {
    "fields": {
      "type": "object",
      "properties": {
        "quality:score": {
          "description": "Quality score between zero and one.",
          "type": "number",
          "minimum": 0,
          "maximum": 1
        },
        "quality:details": {"$ref": "#/$defs/quality_details"}
      }
    },
    "quality_details": {
      "type": "object",
      "required": ["method"],
      "properties": {
        "method": {"type": "string"},
        "samples": {"type": "integer", "minimum": 1}
      }
    }
  }
}
```

The `example.org` identifier is illustrative. This tutorial validates against the
schema embedded in the generated module, so that URL does not need to resolve.
Use a published canonical schema URL for an extension you distribute.

## 2. Generate the Python module

```bash
pystac-ext-generator quality-schema.json --include-validation -o quality_extension.py
```

This tutorial opts into embedded validation so its illustrative schema can be
validated offline. Without `--include-validation`, use PySTAC
`item.validate()` and a published or locally configured schema resolver.

The title produces `QualityExtension`, and the referenced object definition
produces `QualityDetails`. The references under Item `properties` and `assets`
establish applicability automatically. Existing output files are protected;
pass `--force` when regenerating intentionally.

## 3. Use the generated classes

Save this as `use_quality.py` next to the generated module:

```python
import json
from datetime import datetime, timezone

import pystac

from quality_extension import QualityDetails, QualityExtension

item = pystac.Item(
    id="quality-example",
    geometry=None,
    bbox=None,
    datetime=datetime(2026, 1, 1, tzinfo=timezone.utc),
    properties={},
)
extension = QualityExtension.ext(item, add_if_missing=True)
extension.apply(
    score=0.9,
    details=QualityDetails.create(method="manual", samples=12),
)
extension.validate()

serialized = json.loads(json.dumps(item.to_dict()))
assert serialized["properties"]["quality:score"] == 0.9
assert QualityExtension.get_schema_uri() in serialized["stac_extensions"]

restored_item = pystac.Item.from_dict(serialized)
restored = QualityExtension.ext(restored_item)
assert restored.details.method == "manual"
assert restored.details.samples == 12
restored.validate()
```

Run it:

```bash
python use_quality.py
```

`add_if_missing=True` registers the schema URI on the Item. Nested value classes
serialize as ordinary JSON objects. `validate()` checks the whole Item against
the embedded extension schema; `to_dict()` alone does not validate values.

Continue with [updates, asset inheritance, and nested values](../how-to/use-extension.md).
