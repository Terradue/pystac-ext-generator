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

# Load schemas and bundle references

## Choose an input source

The positional `SCHEMA` argument accepts a UTF-8 JSON file, an HTTP(S) URL, or
`-` for stdin:

```bash
pystac-ext-generator schema.json -o extension.py
pystac-ext-generator https://stac-extensions.github.io/view/v1.1.0/schema.json -o view_extension.py
cat schema.json | pystac-ext-generator - > extension.py
```

The schema must have a usable `title` and an absolute HTTP(S) `$id`, regardless
of its input location. Diagnostics go to stderr and generated source goes to
stdout unless `--output` is supplied. Use trusted schema sources.

## Resolve external documents offline

Local JSON Pointers such as `#/$defs/fields` work automatically. References to
other documents need explicit resource mappings or opt-in fetching.

```bash
pystac-ext-generator schema.json \
  --reference 'https://example.org/common/schema.json=common-schema.json' \
  -o extension.py
```

Repeat `--reference URI=FILE` for every external resource needed. The URI must
match the resource's resolved absolute URL. Relative references resolve against
the root schema's canonical `$id`, not its local filename.

## Fetch external documents

```bash
pystac-ext-generator \
  https://stac-extensions.github.io/storage/v2.0.0/schema.json \
  --resolve-external -o storage_extension.py
```

`--resolve-external` permits HTTP(S) requests for missing external resources.
It can be combined with offline mappings; mapped resources are used first.
Each HTTP operation has a 30-second timeout. Bundling accepts at most 100
external documents and requires compatible schema dialects.

Bundling embeds the external documents and rewrites their references into local
JSON Pointers. Generated modules can then validate the extension without fetching
those resources. The root `$id` remains the registration identifier.

## Regenerate reproducibly

Keep the source schema and referenced files under version control, use offline
mappings, and regenerate with `--force` after reviewing schema changes. `--strict`
turns generation warnings into errors, useful when approximate conditional
applicability or conservative annotations are unacceptable for your workflow.
