"""Generated PySTAC extension. Edit the source schema and regenerate to update."""
from __future__ import annotations

import json
from typing import Any, Generic, Literal, TypeVar, cast

import pystac
from pystac.extensions.base import (
    ExtensionManagementMixin, PropertiesExtension, SummariesExtension,
)

SCHEMA_URI = 'https://stac-extensions.github.io/render/v2.1.0/schema.json'
SCHEMA: dict[str, Any] = json.loads('{"$schema": "http://json-schema.org/draft-07/schema#", "$id": "https://stac-extensions.github.io/render/v2.1.0/schema.json#", "title": "Rendering Extension", "description": "STAC Rendering Extension for STAC Items and STAC Collections.", "oneOf": [{"$comment": "This is the schema for STAC Items.", "allOf": [{"$ref": "#/definitions/stac_extensions"}, {"type": "object", "required": ["type", "properties", "assets"], "properties": {"type": {"const": "Feature"}, "properties": {"type": "object", "required": ["renders"], "properties": {"renders": {"type": "object", "additionalProperties": {"$ref": "#/definitions/fields"}}}}}}, {"if": {"properties": {"stac_extensions": {"contains": {"type": "string", "pattern": "https://stac-extensions\\\\.github\\\\.io/web-map-links/.*"}}}}, "then": {"properties": {"links": {"type": "array", "contains": {"type": "object", "required": ["rel", "render"], "properties": {"render": {"type": "string"}}}}}}}]}, {"$comment": "This is the schema for STAC Collections.", "type": "object", "allOf": [{"required": ["type", "renders"], "properties": {"type": {"const": "Collection"}}}, {"$ref": "#/definitions/stac_extensions"}], "anyOf": [{"$comment": "This validates the fields in Collection Assets, but does not require them.", "anyOf": [{"type": "object", "required": ["assets"]}, {"type": "object", "required": ["item_assets"]}], "properties": {"renders": {"type": "object", "not": {"additionalProperties": {"not": {"allOf": [{"$ref": "#/definitions/require_any_field"}, {"$ref": "#/definitions/fields"}]}}}}}}]}], "definitions": {"stac_extensions": {"type": "object", "required": ["stac_extensions"], "properties": {"stac_extensions": {"type": "array", "contains": {"const": "https://stac-extensions.github.io/render/v2.1.0/schema.json"}}}}, "require_any_field": {"$comment": "Please list all fields here so that we can force the existence of one of them in other parts of the schemas.", "anyOf": [{"type": "object", "required": ["assets"]}, {"type": "object", "required": ["title"]}, {"type": "object", "required": ["rescale"]}, {"type": "object", "required": ["nodata"]}, {"type": "object", "required": ["colormap_name"]}, {"type": "object", "required": ["colormap"]}, {"type": "object", "required": ["color_formula"]}, {"type": "object", "required": ["resampling"]}, {"type": "object", "required": ["expression"]}, {"type": "object", "required": ["minmax_zoom"]}, {"type": "object", "required": ["bidx"]}, {"type": "object", "required": ["asset_as_band"]}]}, "fields": {"$comment": "Add your new fields here. Don\'t require them here, do that above in the corresponding schema.", "type": "object", "required": ["assets"], "properties": {"assets": {"type": "array", "items": {"type": "string"}}, "title": {"type": "string"}, "rescale": {"type": "array", "items": {"type": "array", "items": {"type": "number"}}}, "nodata": {"type": ["number", "string"]}, "colormap_name": {"type": "string"}, "colormap": {"type": "object"}, "color_formula": {"type": "string"}, "resampling": {"type": "string"}, "expression": {"type": ["string", "object", "array"]}, "minmax_zoom": {"type": "array", "items": {"type": "number"}}, "bidx": {"type": "array", "items": {"type": "array", "items": {"oneOf": [{"type": "integer", "minimum": 1}, {"type": "string", "minLength": 1}]}}}, "asset_as_band": {"type": "boolean"}}, "additionalProperties": true}}}')
FIELD_TARGETS = {'renders': ['collection', 'item']}
FIELD_NAMES = {'renders': 'renders'}
TARGETS = ['collection', 'item']
T = TypeVar("T", pystac.Item, pystac.Collection, pystac.Catalog, pystac.Asset, pystac.ItemAssetDefinition, pystac.Link)


class _Unset:
    pass


_UNSET = _Unset()
_VALIDATOR = None


def _encode(value: Any) -> Any:
    """Convert generated objects at any depth into plain JSON containers."""
    if isinstance(value, _Object):
        value = value.properties
    if isinstance(value, dict):
        return {key: _encode(child) for key, child in value.items()}
    if isinstance(value, (list, tuple)):
        return [_encode(child) for child in value]
    return value


def _decode(value: Any, codec: Any) -> Any:
    if value is None or codec is None:
        return value
    kind, detail = codec
    if kind == "object":
        return _MODELS[detail].from_dict(value)
    if kind == "list":
        if not isinstance(value, list):
            raise TypeError("Expected a JSON array")
        return [_decode(child, detail) for child in value]
    if kind == "map":
        if not isinstance(value, dict):
            raise TypeError("Expected a JSON object map")
        return {key: _decode(child, detail) for key, child in value.items()}
    if kind == "union":
        global _VALIDATOR
        if _VALIDATOR is None:
            from jsonschema.validators import validator_for
            _VALIDATOR = validator_for(SCHEMA)(SCHEMA)
        matches = []
        for branch_schema, branch_codec in detail:
            if _VALIDATOR.evolve(schema=branch_schema).is_valid(value) and branch_codec not in matches:
                matches.append(branch_codec)
        if len(matches) != 1:
            raise ValueError("Nested union has no unique representation; validate the JSON or access raw properties")
        return _decode(value, matches[0])
    raise ValueError(f"Unknown conversion: {kind}")


_O = TypeVar("_O", bound="_Object")


class _Object:
    """Live wrapper around JSON, following PySTAC value-object conventions."""
    _members: dict[str, str] = {}

    def __init__(self, properties: dict[str, Any]) -> None:
        if not isinstance(properties, dict):
            raise TypeError(f"{type(self).__name__} requires a dictionary")
        self.properties = properties

    @classmethod
    def from_dict(cls: type[_O], properties: dict[str, Any], *, copy: bool = False) -> _O:
        """Wrap by reference, or request an independent copy."""
        from copy import deepcopy
        return cls(deepcopy(properties) if copy else properties)

    def to_dict(self) -> dict[str, Any]:
        """Return the live backing JSON dictionary, as PySTAC Render does."""
        return self.properties

    def apply(self, **values: Any) -> None:
        """Update supplied Python member names; None removes a member."""
        unknown = values.keys() - self._members.keys()
        if unknown:
            raise TypeError(f"Unknown fields: {sorted(unknown)}")
        for name, value in values.items():
            setattr(self, name, value)

    def clear(self, name: str) -> None:
        self.properties.pop(self._members[name], None)

    def set_null(self, name: str) -> None:
        self.properties[self._members[name]] = None

    def __eq__(self, other: object) -> bool:
        if type(other) is not type(self):
            return NotImplemented
        return self.properties == other.properties

    def __repr__(self) -> str:
        return f"<{type(self).__name__} {self.properties!r}>"


class Render(_Object):
    """Generated nested value object; unknown JSON members are preserved."""
    _members = {
        'asset_as_band': 'asset_as_band',
        'assets': 'assets',
        'bidx': 'bidx',
        'color_formula': 'color_formula',
        'colormap': 'colormap',
        'colormap_name': 'colormap_name',
        'expression': 'expression',
        'minmax_zoom': 'minmax_zoom',
        'nodata': 'nodata',
        'resampling': 'resampling',
        'rescale': 'rescale',
        'title': 'title',
    }

    @classmethod
    def create(
        cls,
        *,
        assets: list[str],
        asset_as_band: bool | _Unset = _UNSET,
        bidx: list[list[int | str]] | _Unset = _UNSET,
        color_formula: str | _Unset = _UNSET,
        colormap: dict[str, Any] | _Unset = _UNSET,
        colormap_name: str | _Unset = _UNSET,
        expression: str | dict[str, Any] | list[Any] | _Unset = _UNSET,
        minmax_zoom: list[float] | _Unset = _UNSET,
        nodata: float | str | _Unset = _UNSET,
        resampling: str | _Unset = _UNSET,
        rescale: list[list[float]] | _Unset = _UNSET,
        title: str | _Unset = _UNSET,
    ) -> Render:
        """Create with typed members; omitted optionals are not written.

        Explicit None writes null. Validate the extension to check value constraints.
        """
        result = cls({})
        if asset_as_band is not _UNSET:
            result.properties['asset_as_band'] = _encode(asset_as_band)
        result.properties['assets'] = _encode(assets)
        if bidx is not _UNSET:
            result.properties['bidx'] = _encode(bidx)
        if color_formula is not _UNSET:
            result.properties['color_formula'] = _encode(color_formula)
        if colormap is not _UNSET:
            result.properties['colormap'] = _encode(colormap)
        if colormap_name is not _UNSET:
            result.properties['colormap_name'] = _encode(colormap_name)
        if expression is not _UNSET:
            result.properties['expression'] = _encode(expression)
        if minmax_zoom is not _UNSET:
            result.properties['minmax_zoom'] = _encode(minmax_zoom)
        if nodata is not _UNSET:
            result.properties['nodata'] = _encode(nodata)
        if resampling is not _UNSET:
            result.properties['resampling'] = _encode(resampling)
        if rescale is not _UNSET:
            result.properties['rescale'] = _encode(rescale)
        if title is not _UNSET:
            result.properties['title'] = _encode(title)
        return result

    def apply(
        self,
        *,
        asset_as_band: bool | None | _Unset = _UNSET,
        assets: list[str] | None | _Unset = _UNSET,
        bidx: list[list[int | str]] | None | _Unset = _UNSET,
        color_formula: str | None | _Unset = _UNSET,
        colormap: dict[str, Any] | None | _Unset = _UNSET,
        colormap_name: str | None | _Unset = _UNSET,
        expression: str | dict[str, Any] | list[Any] | None | _Unset = _UNSET,
        minmax_zoom: list[float] | None | _Unset = _UNSET,
        nodata: float | str | None | _Unset = _UNSET,
        resampling: str | None | _Unset = _UNSET,
        rescale: list[list[float]] | None | _Unset = _UNSET,
        title: str | None | _Unset = _UNSET,
    ) -> None:
        """Update supplied members; omitted values are preserved and None removes."""
        if asset_as_band is not _UNSET:
            self.asset_as_band = asset_as_band
        if assets is not _UNSET:
            self.assets = assets
        if bidx is not _UNSET:
            self.bidx = bidx
        if color_formula is not _UNSET:
            self.color_formula = color_formula
        if colormap is not _UNSET:
            self.colormap = colormap
        if colormap_name is not _UNSET:
            self.colormap_name = colormap_name
        if expression is not _UNSET:
            self.expression = expression
        if minmax_zoom is not _UNSET:
            self.minmax_zoom = minmax_zoom
        if nodata is not _UNSET:
            self.nodata = nodata
        if resampling is not _UNSET:
            self.resampling = resampling
        if rescale is not _UNSET:
            self.rescale = rescale
        if title is not _UNSET:
            self.title = title

    @property
    def asset_as_band(self) -> bool | None:
        'asset_as_band'
        return _decode(self.properties.get('asset_as_band'), None)

    @asset_as_band.setter
    def asset_as_band(self, value: bool | None) -> None:
        if value is None:
            self.properties.pop('asset_as_band', None)
        else:
            self.properties['asset_as_band'] = _encode(value)

    @property
    def assets(self) -> list[str]:
        'assets'
        if 'assets' not in self.properties:
            raise pystac.STACError('Missing required property: assets')
        return _decode(self.properties.get('assets'), None)

    @assets.setter
    def assets(self, value: list[str] | None) -> None:
        if value is None:
            self.properties.pop('assets', None)
        else:
            self.properties['assets'] = _encode(value)

    @property
    def bidx(self) -> list[list[int | str]] | None:
        'bidx'
        return _decode(self.properties.get('bidx'), None)

    @bidx.setter
    def bidx(self, value: list[list[int | str]] | None) -> None:
        if value is None:
            self.properties.pop('bidx', None)
        else:
            self.properties['bidx'] = _encode(value)

    @property
    def color_formula(self) -> str | None:
        'color_formula'
        return _decode(self.properties.get('color_formula'), None)

    @color_formula.setter
    def color_formula(self, value: str | None) -> None:
        if value is None:
            self.properties.pop('color_formula', None)
        else:
            self.properties['color_formula'] = _encode(value)

    @property
    def colormap(self) -> dict[str, Any] | None:
        'colormap'
        return _decode(self.properties.get('colormap'), None)

    @colormap.setter
    def colormap(self, value: dict[str, Any] | None) -> None:
        if value is None:
            self.properties.pop('colormap', None)
        else:
            self.properties['colormap'] = _encode(value)

    @property
    def colormap_name(self) -> str | None:
        'colormap_name'
        return _decode(self.properties.get('colormap_name'), None)

    @colormap_name.setter
    def colormap_name(self, value: str | None) -> None:
        if value is None:
            self.properties.pop('colormap_name', None)
        else:
            self.properties['colormap_name'] = _encode(value)

    @property
    def expression(self) -> str | dict[str, Any] | list[Any] | None:
        'expression'
        return _decode(self.properties.get('expression'), None)

    @expression.setter
    def expression(self, value: str | dict[str, Any] | list[Any] | None) -> None:
        if value is None:
            self.properties.pop('expression', None)
        else:
            self.properties['expression'] = _encode(value)

    @property
    def minmax_zoom(self) -> list[float] | None:
        'minmax_zoom'
        return _decode(self.properties.get('minmax_zoom'), None)

    @minmax_zoom.setter
    def minmax_zoom(self, value: list[float] | None) -> None:
        if value is None:
            self.properties.pop('minmax_zoom', None)
        else:
            self.properties['minmax_zoom'] = _encode(value)

    @property
    def nodata(self) -> float | str | None:
        'nodata'
        return _decode(self.properties.get('nodata'), None)

    @nodata.setter
    def nodata(self, value: float | str | None) -> None:
        if value is None:
            self.properties.pop('nodata', None)
        else:
            self.properties['nodata'] = _encode(value)

    @property
    def resampling(self) -> str | None:
        'resampling'
        return _decode(self.properties.get('resampling'), None)

    @resampling.setter
    def resampling(self, value: str | None) -> None:
        if value is None:
            self.properties.pop('resampling', None)
        else:
            self.properties['resampling'] = _encode(value)

    @property
    def rescale(self) -> list[list[float]] | None:
        'rescale'
        return _decode(self.properties.get('rescale'), None)

    @rescale.setter
    def rescale(self, value: list[list[float]] | None) -> None:
        if value is None:
            self.properties.pop('rescale', None)
        else:
            self.properties['rescale'] = _encode(value)

    @property
    def title(self) -> str | None:
        'title'
        return _decode(self.properties.get('title'), None)

    @title.setter
    def title(self, value: str | None) -> None:
        if value is None:
            self.properties.pop('title', None)
        else:
            self.properties['title'] = _encode(value)

_MODELS = {
    'Render': Render,
}


class RenderingExtension(PropertiesExtension, ExtensionManagementMixin[pystac.Item | pystac.Collection | pystac.Catalog], Generic[T]):
    """Typed property wrapper; use ext() to check/register the extension.

    Setters preserve JSON representations, including date/time strings and nested
    dictionaries. None removes a property; set_null() explicitly writes JSON null.
    Call validate() for full extension-schema validation, including required fields.
    """

    def __init__(self, obj: T, target: str) -> None:
        self.obj = obj
        self._target = target
        self.additional_read_properties = None
        if isinstance(obj, pystac.Item):
            self.properties = obj.properties
        elif isinstance(obj, pystac.ItemAssetDefinition):
            self.properties = obj.properties
        else:
            self.properties = obj.extra_fields
        if isinstance(obj, pystac.Asset) and isinstance(obj.owner, pystac.Item):
            self.additional_read_properties = [obj.owner.properties]

    @classmethod
    def get_schema_uri(cls) -> str:
        return SCHEMA_URI

    @classmethod
    def has_extension(cls, obj: pystac.STACObject) -> bool:
        """Check this exact schema version; migrations are not generated."""
        return SCHEMA_URI in (obj.stac_extensions or [])

    @classmethod
    def ext(cls, obj: T, add_if_missing: bool = False) -> RenderingExtension[T]:
        if isinstance(obj, pystac.Item):
            target = "item"
        elif isinstance(obj, pystac.Collection):
            target = "collection"
        elif isinstance(obj, pystac.Catalog):
            target = "catalog"
        elif isinstance(obj, pystac.Link):
            target = "link"
        elif isinstance(obj, pystac.Asset):
            target = "asset"
        elif isinstance(obj, pystac.ItemAssetDefinition):
            target = "item_asset"
        else:
            raise pystac.ExtensionTypeError(cls._ext_error_message(obj))
        if target not in TARGETS:
            raise pystac.ExtensionTypeError(cls._ext_error_message(obj))
        if isinstance(obj, (pystac.Asset, pystac.ItemAssetDefinition, pystac.Link)):
            cls.ensure_owner_has_extension(obj, add_if_missing)
        else:
            cls.ensure_has_extension(obj, add_if_missing)
        return cls(obj, target)

    def _check_field(self, key: str) -> None:
        if self._target not in FIELD_TARGETS[key]:
            raise pystac.ExtensionTypeError(f"{key} does not apply to {self._target}")

    def clear(self, name: str) -> None:
        """Remove a field using its generated Python attribute name."""
        key = FIELD_NAMES[name]
        self._check_field(key)
        self.properties.pop(key, None)

    def set_null(self, name: str) -> None:
        """Write explicit JSON null; validate() checks whether it is permitted."""
        key = FIELD_NAMES[name]
        self._check_field(key)
        self._set_property(key, None, pop_if_none=False)

    def validate(self) -> None:
        """Validate the whole Item/Collection against this extension's schema.

        Assets are validated through their owner; unowned assets cannot be checked.
        STAC core validation remains available separately through obj.validate().
        """
        from jsonschema import FormatChecker
        from jsonschema.validators import validator_for
        obj = self.obj
        if isinstance(obj, (pystac.Asset, pystac.ItemAssetDefinition, pystac.Link)):
            if obj.owner is None:
                raise pystac.STACError("Full schema validation requires an owner")
            obj = obj.owner
        validator_for(SCHEMA)(SCHEMA, format_checker=FormatChecker()).validate(obj.to_dict())

    def apply(self, **values: Any) -> None:
        """Update only supplied fields; omitted fields are preserved.

        Keys are generated Python attribute names. Unknown or inapplicable fields
        are rejected before mutation. Use validate() to check values afterwards.
        """
        for name in values:
            if name not in FIELD_NAMES:
                raise TypeError(f"Unknown extension field: {name}")
            self._check_field(FIELD_NAMES[name])
        for name, value in values.items():
            setattr(self, name, value)

    @property
    def renders(self) -> dict[str, Render] | None:
        'renders'
        self._check_field('renders')
        if 'renders' in self.properties:
            return cast('dict[str, Render] | None', _decode(self.properties['renders'], ['map', ['object', 'Render']]))
        return cast('dict[str, Render] | None', _decode(self._get_property('renders', object), ['map', ['object', 'Render']]))

    @renders.setter
    def renders(self, value: dict[str, Render] | None) -> None:
        self._check_field('renders')
        self._set_property('renders', _encode(value))

