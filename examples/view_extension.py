"""Generated PySTAC extension. Edit the source schema and regenerate to update."""
from __future__ import annotations

import json
from typing import Any, Generic, Literal, TypeVar, cast

import pystac
from pystac.extensions.base import (
    ExtensionManagementMixin, PropertiesExtension, SummariesExtension,
)

SCHEMA_URI = 'https://stac-extensions.github.io/view/v1.1.0/schema.json'
SCHEMA: dict[str, Any] = json.loads('{"$schema": "http://json-schema.org/draft-07/schema#", "$id": "https://stac-extensions.github.io/view/v1.1.0/schema.json", "title": "View Geometry Extension", "description": "STAC View Geometry for STAC Items and STAC Collections.", "type": "object", "required": ["stac_extensions"], "properties": {"stac_extensions": {"type": "array", "contains": {"const": "https://stac-extensions.github.io/view/v1.1.0/schema.json"}}}, "oneOf": [{"$comment": "This is the schema for STAC Items.", "type": "object", "required": ["type"], "properties": {"type": {"const": "Feature"}}, "anyOf": [{"required": ["properties"], "properties": {"properties": {"$ref": "#/definitions/requirements_and_fields"}}}, {"$ref": "#/definitions/assets"}]}, {"$comment": "This is the schema for STAC Collections.", "type": "object", "required": ["type"], "properties": {"type": {"const": "Collection"}}, "anyOf": [{"$ref": "#/definitions/assets"}, {"required": ["item_assets"], "properties": {"item_assets": {"$ref": "#/definitions/asset_contains"}}}, {"$comment": "This is the schema for the fields in Summaries. By default, only checks the existence of the properties, but not the schema of the summaries.", "required": ["summaries"], "properties": {"summaries": {"$ref": "#/definitions/require_any_field"}}}]}], "definitions": {"assets": {"required": ["assets"], "properties": {"assets": {"$ref": "#/definitions/asset_contains"}}}, "asset_contains": {"type": "object", "not": {"additionalProperties": {"not": {"$ref": "#/definitions/requirements_and_fields"}}}}, "requirements_and_fields": {"allOf": [{"$ref": "#/definitions/require_any_field"}, {"$ref": "#/definitions/fields"}]}, "require_any_field": {"$comment": "Please list all fields here so that we can force the existence of one of them in other parts of the schemas.", "anyOf": [{"required": ["view:off_nadir"]}, {"required": ["view:incidence_angle"]}, {"required": ["view:azimuth"]}, {"required": ["view:sun_azimuth"]}, {"required": ["view:sun_elevation"]}, {"required": ["view:moon_azimuth"]}, {"required": ["view:moon_elevation"]}]}, "fields": {"$comment": "Add your new fields here. Don\'t require them here, do that above in the item schema.", "type": "object", "properties": {"view:off_nadir": {"title": "Off Nadir", "type": "number", "minimum": 0, "maximum": 90}, "view:incidence_angle": {"title": "Center incidence angle", "type": "number", "minimum": 0, "maximum": 90}, "view:azimuth": {"title": "Azimuth angle", "type": "number", "minimum": 0, "maximum": 360}, "view:sun_azimuth": {"title": "Sun Azimuth", "type": "number", "minimum": 0, "maximum": 360}, "view:sun_elevation": {"title": "Sun Elevation", "type": "number", "minimum": -90, "maximum": 90}, "view:moon_azimuth": {"title": "Moon Azimuth", "type": "number", "minimum": 0, "maximum": 360}, "view:moon_elevation": {"title": "Moon Elevation", "type": "number", "minimum": 0, "maximum": 90}}, "patternProperties": {"^(?!view:)": {"$comment": "Do not allow unspecified fields prefixed with view:"}}, "additionalProperties": false}}}')
FIELD_TARGETS = {'view:azimuth': ['asset', 'item', 'item_asset', 'summary'], 'view:incidence_angle': ['asset', 'item', 'item_asset', 'summary'], 'view:moon_azimuth': ['asset', 'item', 'item_asset', 'summary'], 'view:moon_elevation': ['asset', 'item', 'item_asset', 'summary'], 'view:off_nadir': ['asset', 'item', 'item_asset', 'summary'], 'view:sun_azimuth': ['asset', 'item', 'item_asset', 'summary'], 'view:sun_elevation': ['asset', 'item', 'item_asset', 'summary']}
FIELD_NAMES = {'azimuth': 'view:azimuth', 'incidence_angle': 'view:incidence_angle', 'moon_azimuth': 'view:moon_azimuth', 'moon_elevation': 'view:moon_elevation', 'off_nadir': 'view:off_nadir', 'sun_azimuth': 'view:sun_azimuth', 'sun_elevation': 'view:sun_elevation'}
TARGETS = ['asset', 'item', 'item_asset', 'summary']
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


_MODELS = {
}


class ViewGeometryExtension(PropertiesExtension, ExtensionManagementMixin[pystac.Item | pystac.Collection | pystac.Catalog], Generic[T]):
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
    def ext(cls, obj: T, add_if_missing: bool = False) -> ViewGeometryExtension[T]:
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
    def azimuth(self) -> float | None:
        'Azimuth angle'
        self._check_field('view:azimuth')
        if 'view:azimuth' in self.properties:
            return cast('float | None', _decode(self.properties['view:azimuth'], None))
        return cast('float | None', _decode(self._get_property('view:azimuth', object), None))

    @azimuth.setter
    def azimuth(self, value: float | None) -> None:
        self._check_field('view:azimuth')
        self._set_property('view:azimuth', _encode(value))

    @property
    def incidence_angle(self) -> float | None:
        'Center incidence angle'
        self._check_field('view:incidence_angle')
        if 'view:incidence_angle' in self.properties:
            return cast('float | None', _decode(self.properties['view:incidence_angle'], None))
        return cast('float | None', _decode(self._get_property('view:incidence_angle', object), None))

    @incidence_angle.setter
    def incidence_angle(self, value: float | None) -> None:
        self._check_field('view:incidence_angle')
        self._set_property('view:incidence_angle', _encode(value))

    @property
    def moon_azimuth(self) -> float | None:
        'Moon Azimuth'
        self._check_field('view:moon_azimuth')
        if 'view:moon_azimuth' in self.properties:
            return cast('float | None', _decode(self.properties['view:moon_azimuth'], None))
        return cast('float | None', _decode(self._get_property('view:moon_azimuth', object), None))

    @moon_azimuth.setter
    def moon_azimuth(self, value: float | None) -> None:
        self._check_field('view:moon_azimuth')
        self._set_property('view:moon_azimuth', _encode(value))

    @property
    def moon_elevation(self) -> float | None:
        'Moon Elevation'
        self._check_field('view:moon_elevation')
        if 'view:moon_elevation' in self.properties:
            return cast('float | None', _decode(self.properties['view:moon_elevation'], None))
        return cast('float | None', _decode(self._get_property('view:moon_elevation', object), None))

    @moon_elevation.setter
    def moon_elevation(self, value: float | None) -> None:
        self._check_field('view:moon_elevation')
        self._set_property('view:moon_elevation', _encode(value))

    @property
    def off_nadir(self) -> float | None:
        'Off Nadir'
        self._check_field('view:off_nadir')
        if 'view:off_nadir' in self.properties:
            return cast('float | None', _decode(self.properties['view:off_nadir'], None))
        return cast('float | None', _decode(self._get_property('view:off_nadir', object), None))

    @off_nadir.setter
    def off_nadir(self, value: float | None) -> None:
        self._check_field('view:off_nadir')
        self._set_property('view:off_nadir', _encode(value))

    @property
    def sun_azimuth(self) -> float | None:
        'Sun Azimuth'
        self._check_field('view:sun_azimuth')
        if 'view:sun_azimuth' in self.properties:
            return cast('float | None', _decode(self.properties['view:sun_azimuth'], None))
        return cast('float | None', _decode(self._get_property('view:sun_azimuth', object), None))

    @sun_azimuth.setter
    def sun_azimuth(self, value: float | None) -> None:
        self._check_field('view:sun_azimuth')
        self._set_property('view:sun_azimuth', _encode(value))

    @property
    def sun_elevation(self) -> float | None:
        'Sun Elevation'
        self._check_field('view:sun_elevation')
        if 'view:sun_elevation' in self.properties:
            return cast('float | None', _decode(self.properties['view:sun_elevation'], None))
        return cast('float | None', _decode(self._get_property('view:sun_elevation', object), None))

    @sun_elevation.setter
    def sun_elevation(self, value: float | None) -> None:
        self._check_field('view:sun_elevation')
        self._set_property('view:sun_elevation', _encode(value))

    @classmethod
    def summaries(cls, obj: pystac.Collection, add_if_missing: bool = False) -> SummariesViewGeometryExtension:
        if not isinstance(obj, pystac.Collection):
            raise pystac.ExtensionTypeError("Summaries require a Collection")
        cls.ensure_has_extension(obj, add_if_missing)
        return SummariesViewGeometryExtension(obj)


class SummariesViewGeometryExtension(SummariesExtension):
    """Collection summaries; ranges, lists and JSON Schema objects are preserved."""
    @property
    def azimuth(self) -> list[Any] | pystac.RangeSummary[Any] | dict[str, Any] | None:
        value = self.summaries.to_dict().get('view:azimuth')
        if isinstance(value, dict) and "minimum" in value and "maximum" in value:
            return self.summaries.get_range('view:azimuth')
        return value

    @azimuth.setter
    def azimuth(self, value: list[Any] | pystac.RangeSummary[Any] | dict[str, Any] | None) -> None:
        self.summaries.remove('view:azimuth')
        self._set_summary('view:azimuth', value)

    @property
    def incidence_angle(self) -> list[Any] | pystac.RangeSummary[Any] | dict[str, Any] | None:
        value = self.summaries.to_dict().get('view:incidence_angle')
        if isinstance(value, dict) and "minimum" in value and "maximum" in value:
            return self.summaries.get_range('view:incidence_angle')
        return value

    @incidence_angle.setter
    def incidence_angle(self, value: list[Any] | pystac.RangeSummary[Any] | dict[str, Any] | None) -> None:
        self.summaries.remove('view:incidence_angle')
        self._set_summary('view:incidence_angle', value)

    @property
    def moon_azimuth(self) -> list[Any] | pystac.RangeSummary[Any] | dict[str, Any] | None:
        value = self.summaries.to_dict().get('view:moon_azimuth')
        if isinstance(value, dict) and "minimum" in value and "maximum" in value:
            return self.summaries.get_range('view:moon_azimuth')
        return value

    @moon_azimuth.setter
    def moon_azimuth(self, value: list[Any] | pystac.RangeSummary[Any] | dict[str, Any] | None) -> None:
        self.summaries.remove('view:moon_azimuth')
        self._set_summary('view:moon_azimuth', value)

    @property
    def moon_elevation(self) -> list[Any] | pystac.RangeSummary[Any] | dict[str, Any] | None:
        value = self.summaries.to_dict().get('view:moon_elevation')
        if isinstance(value, dict) and "minimum" in value and "maximum" in value:
            return self.summaries.get_range('view:moon_elevation')
        return value

    @moon_elevation.setter
    def moon_elevation(self, value: list[Any] | pystac.RangeSummary[Any] | dict[str, Any] | None) -> None:
        self.summaries.remove('view:moon_elevation')
        self._set_summary('view:moon_elevation', value)

    @property
    def off_nadir(self) -> list[Any] | pystac.RangeSummary[Any] | dict[str, Any] | None:
        value = self.summaries.to_dict().get('view:off_nadir')
        if isinstance(value, dict) and "minimum" in value and "maximum" in value:
            return self.summaries.get_range('view:off_nadir')
        return value

    @off_nadir.setter
    def off_nadir(self, value: list[Any] | pystac.RangeSummary[Any] | dict[str, Any] | None) -> None:
        self.summaries.remove('view:off_nadir')
        self._set_summary('view:off_nadir', value)

    @property
    def sun_azimuth(self) -> list[Any] | pystac.RangeSummary[Any] | dict[str, Any] | None:
        value = self.summaries.to_dict().get('view:sun_azimuth')
        if isinstance(value, dict) and "minimum" in value and "maximum" in value:
            return self.summaries.get_range('view:sun_azimuth')
        return value

    @sun_azimuth.setter
    def sun_azimuth(self, value: list[Any] | pystac.RangeSummary[Any] | dict[str, Any] | None) -> None:
        self.summaries.remove('view:sun_azimuth')
        self._set_summary('view:sun_azimuth', value)

    @property
    def sun_elevation(self) -> list[Any] | pystac.RangeSummary[Any] | dict[str, Any] | None:
        value = self.summaries.to_dict().get('view:sun_elevation')
        if isinstance(value, dict) and "minimum" in value and "maximum" in value:
            return self.summaries.get_range('view:sun_elevation')
        return value

    @sun_elevation.setter
    def sun_elevation(self, value: list[Any] | pystac.RangeSummary[Any] | dict[str, Any] | None) -> None:
        self.summaries.remove('view:sun_elevation')
        self._set_summary('view:sun_elevation', value)

