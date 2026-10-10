# Upstream schema fixtures

Retrieved on 2026-10-10 through the GitHub connector. These are unchanged upstream
JSON schemas, included solely as offline integration-test inputs:

- https://github.com/stac-extensions/render/blob/main/json-schema/schema.json
- https://github.com/stac-extensions/view/blob/main/json-schema/schema.json
- https://github.com/stac-extensions/file/blob/main/json-schema/schema.json
- https://github.com/stac-extensions/scientific/blob/main/json-schema/schema.json
- https://github.com/stac-extensions/projection/blob/main/json-schema/schema.json
- https://github.com/stac-extensions/storage/blob/main/json-schema/schema.json
- https://github.com/stac-extensions/storage/tree/main/json-schema/platforms

Upstream schemas remain subject to their respective repository licenses. The
fixtures are snapshots, not automatically updated dependencies.

PySTAC implementation patterns were checked against:
https://github.com/stac-utils/pystac/blob/main/extensions/view/pystac/extensions/view.py
and https://github.com/stac-utils/pystac/blob/main/core/pystac/extensions/base.py

Tests compare common View fields only: the upstream PySTAC wrapper inspected uses
View v1.0.0, while the vendored schema is v1.1.0 with additional moon fields.

Nested value classes were checked against:
https://github.com/stac-utils/pystac/blob/main/extensions/render/pystac/extensions/render.py
The Render fixture is v2.1.0; parity tests use fields shared with the inspected
handwritten v2.0.0 implementation.
