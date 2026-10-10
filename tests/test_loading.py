# Copyright 2026 Terradue
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations

import io
import json
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from pystac_ext_generator import SchemaError
from pystac_ext_generator.bundle import fetch_http
from pystac_ext_generator.cli import main

from .test_generator import custom

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.parametrize(
    "uri", ["file:///tmp/schema.json", "ftp://example.org/schema.json", "schema.json"]
)
def test_fetch_rejects_non_http_schemes_before_opening(uri: str) -> None:
    with patch("pystac_ext_generator.bundle.urlopen") as open_url:
        with pytest.raises(SchemaError, match=r"Only HTTP\(S\)"):
            fetch_http(uri)
        open_url.assert_not_called()


@pytest.mark.parametrize("payload", ["[]", "null", "true", '"schema"'])
def test_fetch_rejects_non_object_json(payload: str) -> None:
    with (
        patch("pystac_ext_generator.bundle.urlopen", return_value=io.BytesIO(payload.encode())),
        pytest.raises(SchemaError, match="External schema must be an object"),
    ):
        fetch_http("https://example.org/schema.json")


def test_fetch_returns_schema_and_closes_response() -> None:
    document = custom({"demo:value": {"type": "string"}})
    response = io.BytesIO(json.dumps(document).encode())
    uri = "https://example.org/schema.json"
    with patch("pystac_ext_generator.bundle.urlopen", return_value=response) as open_url:
        assert fetch_http(uri) == document
        open_url.assert_called_once_with(uri, timeout=30)
    assert response.closed


def test_cli_rejects_non_object_reference_file(tmp_path: Path) -> None:
    reference = tmp_path / "reference.json"
    reference.write_text("[]", encoding="utf-8")
    document = custom({"demo:value": {"$ref": "value.json"}})
    result = CliRunner().invoke(
        main,
        ["-", "--reference", f"https://example.org/demo/v1.0.0/value.json={reference}"],
        input=json.dumps(document),
    )
    assert result.exit_code == 1
    assert "External schema must be an object" in result.output
