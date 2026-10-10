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

"""Click command line interface."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any
from urllib.error import URLError

import click

from .__about__ import __version__
from .bundle import bundle, fetch_http
from .generator import generate
from .schema import SchemaError


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("schema")
@click.option(
    "-o",
    "--output",
    type=click.Path(path_type=Path, dir_okay=False),
    help="Output module. Defaults to stdout.",
)
@click.option("--prefix", help="Extension namespace, without trailing colon.")
@click.option(
    "--reference",
    "references",
    multiple=True,
    help="Offline external schema mapping URI=FILE; repeat as needed.",
)
@click.option(
    "--resolve-external", is_flag=True, help="Fetch and bundle external HTTP(S) references."
)
@click.option(
    "--include-validation", is_flag=True, help="Embed the schema and an offline validate() method."
)
@click.option("--force", is_flag=True, help="Overwrite an existing output module.")
@click.option("--strict", is_flag=True, help="Treat generation warnings as errors.")
@click.version_option(__version__)
def main(
    schema: str,
    *,
    output: Path | None,
    prefix: str | None,
    references: tuple[str, ...],
    resolve_external: bool,
    include_validation: bool,
    force: bool,
    strict: bool,
) -> None:
    """Generate a PySTAC extension from a JSON SCHEMA file, HTTP(S) URL, or - (stdin)."""
    try:
        document = _read_schema(schema)
        if references or resolve_external:
            document = bundle(
                document,
                documents=_read_references(references),
                fetch=fetch_http if resolve_external else None,
            )
        source, warnings = generate(
            document,
            prefix=prefix,
            include_validation=include_validation,
        )
        if strict and warnings:
            raise SchemaError("; ".join(warnings))
        for warning in warnings:
            click.echo(f"Warning: {warning}", err=True)
        if output:
            output.parent.mkdir(parents=True, exist_ok=True)
            # Exclusive creation protects existing files, including empty files.
            with output.open("w" if force else "x", encoding="utf-8") as stream:
                stream.write(source)
            click.echo(f"Generated {output}", err=True)
        else:
            click.echo(source, nl=False)
    except (SchemaError, OSError, URLError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc


def _read_schema(source: str) -> dict[str, Any]:
    """Read an object schema from stdin, an HTTP(S) URL, or a UTF-8 file."""
    if source == "-":
        document = json.loads(sys.stdin.read())
    elif source.startswith(("https://", "http://")):
        return fetch_http(source)
    else:
        document = json.loads(Path(source).read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise SchemaError("The schema must be a JSON object")
    return document


def _read_references(references: tuple[str, ...]) -> dict[str, dict[str, Any]]:
    """Load offline URI=FILE mappings, rejecting malformed entries and non-object schemas."""
    documents = {}
    for reference in references:
        uri, separator, path = reference.partition("=")
        if not separator:
            raise SchemaError("--reference expects URI=FILE")
        document = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(document, dict):
            raise SchemaError(f"External schema must be an object: {uri}")
        documents[uri] = document
    return documents
