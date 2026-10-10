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

# PySTAC extension generator

`pystac-ext-generator` is a generic Python command-line application that turns a
**STAC Extension JSON Schema** into a standalone Python module containing
**PySTAC-compatible extension classes**.

The input schema determines the class name, registration URI, fields, types, and
applicable STAC objects. Declared nested objects become additional value classes;
Collection summary helpers are generated when the schema exposes summary fields.
The generator is not tied to a particular extension or scientific domain.

```bash
pystac-ext-generator schema.json -o extension.py
```

Import the generated class from `extension.py` and use its `ext()` method to wrap
a PySTAC object. The generated module runs independently of the generator.
Embedded offline schema validation is available with `--include-validation`.

## Start here

- [Install the CLI](how-to/install.md).
- [Generate and use your first extension](tutorials/first-steps.md).
- [Work with generated fields and nested classes](how-to/use-extension.md).
- [Bundle external references](how-to/references.md).
- [Look up CLI options](reference/cli.md) or the [Python API](reference/api.md).
- [Understand schema discovery and validation](explanation/architecture.md).

Python 3.10 or later is required. Lean modules such as Themes need only PySTAC.
Embedded validation and schema-dependent union decoding additionally need jsonschema;
wide factories use typing-extensions. Generated code never requires Click, Jinja2,
Ruff, or `pystac-ext-generator`.
