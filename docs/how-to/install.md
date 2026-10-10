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

# Install and build

## Install from a checkout

Use Python 3.10 or later:

```bash
git clone https://github.com/Terradue/pystac-ext-generator.git
cd pystac-ext-generator
python -m pip install -e .
pystac-ext-generator --help
pystac-ext-generator --version
```

The distribution is `pystac-ext-generator`; its Python import package is
`pystac_ext_generator`. Installation provides the `pystac-ext-generator` command.
You can also invoke it with `python -m pystac_ext_generator`.

With uv, run `uv sync`, then `uv run pystac-ext-generator --help`.
If an editable installation predates a packaging change, repeat the installation.

## Use generated modules in another project

Copy the generated `.py` module into your application or package and install its
runtime dependencies:

```bash
python -m pip install "pystac>=1.12,<2" "jsonschema>=4.23,<5"
```

Import classes from the generated module's name. For example,
`quality_extension.py` provides `from quality_extension import QualityExtension`
when the schema title is `Quality Extension`. Generation does not install a
module into `pystac.extensions` or register a global PySTAC accessor.

## Preview the documentation

From the repository checkout, install the documentation tools:

```bash
python -m pip install "mkdocs<2" "mkdocstrings[python]" pymdown-extensions
mkdocs serve -f mkdocs.yaml
```

Build with warnings treated as errors:

```bash
mkdocs build --strict -f mkdocs.yaml
```

The configuration uses MkDocs' built-in Read the Docs theme. API pages read the
source package from `src`.

## Run repository checks

With Hatch installed, run:

```bash
hatch run dev:format-check
hatch run dev:lint-check
hatch run dev:typecheck
hatch run dev:security
hatch run test:test
```

The test matrix covers Python 3.10–3.14. Tests generate modules from local schema
fixtures and exercise them with real PySTAC objects.
