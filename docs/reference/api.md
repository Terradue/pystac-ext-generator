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

# Python API

Use `pystac_ext_generator` when embedding generation in another Python tool:

```python
import json
from pathlib import Path

from pystac_ext_generator import generate

schema = json.loads(Path("quality-schema.json").read_text(encoding="utf-8"))
source, warnings = generate(schema)
Path("quality_extension.py").write_text(source, encoding="utf-8")
for warning in warnings:
    print(warning)
```

`generate()` returns source text and diagnostics. It checks the generated Python's
syntax without executing it. The only optional generation parameter is `prefix`,
which filters field namespaces while retaining the complete validation schema.

## Generation

::: pystac_ext_generator.generate
    options:
      show_root_heading: true
      show_signature_annotations: true

## External resource bundling

Call `bundle()` before `generate()` when external references are present:

```python
from pystac_ext_generator.bundle import bundle

external = json.loads(Path("common-schema.json").read_text(encoding="utf-8"))
schema = bundle(schema, documents={"https://example.org/common/schema.json": external})
source, warnings = generate(schema)
```

An optional `fetch` callback loads resources absent from the mapping. Pass
`fetch_http` to opt into network access, or provide an application-specific loader.

::: pystac_ext_generator.bundle.bundle
    options:
      show_root_heading: true
      show_signature_annotations: true

::: pystac_ext_generator.bundle.fetch_http
    options:
      show_root_heading: true
      show_signature_annotations: true

## Errors

::: pystac_ext_generator.SchemaError
    options:
      show_root_heading: true

Malformed JSON, file errors, and network errors can also arise while loading
input. The CLI presents these as command errors. See [generated classes](fields.md)
for the runtime API of the emitted module.
