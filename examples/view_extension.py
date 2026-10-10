"""Generated PySTAC extension. Edit the source schema and regenerate to update."""

from __future__ import annotations

from typing import Any, Generic, TypeVar, cast

import pystac
from pystac.extensions.base import (
    ExtensionManagementMixin,
    PropertiesExtension,
    SummariesExtension,
)

SCHEMA_URI = "https://stac-extensions.github.io/view/v1.1.0/schema.json"
FIELD_TARGETS = {
    "view:azimuth": ["asset", "item", "item_asset", "summary"],
    "view:incidence_angle": ["asset", "item", "item_asset", "summary"],
    "view:moon_azimuth": ["asset", "item", "item_asset", "summary"],
    "view:moon_elevation": ["asset", "item", "item_asset", "summary"],
    "view:off_nadir": ["asset", "item", "item_asset", "summary"],
    "view:sun_azimuth": ["asset", "item", "item_asset", "summary"],
    "view:sun_elevation": ["asset", "item", "item_asset", "summary"],
}
FIELD_NAMES = {
    "azimuth": "view:azimuth",
    "incidence_angle": "view:incidence_angle",
    "moon_azimuth": "view:moon_azimuth",
    "moon_elevation": "view:moon_elevation",
    "off_nadir": "view:off_nadir",
    "sun_azimuth": "view:sun_azimuth",
    "sun_elevation": "view:sun_elevation",
}
TARGETS = ["asset", "item", "item_asset", "summary"]
T = TypeVar("T", bound="pystac.Item | pystac.Asset | pystac.ItemAssetDefinition")


def _target_for(obj: object) -> str:
    """Identify supported STAC targets, checking Collection before its Catalog base."""
    target_types = (
        (pystac.Collection, "collection"),
        (pystac.Catalog, "catalog"),
        (pystac.Item, "item"),
        (pystac.Asset, "asset"),
        (pystac.ItemAssetDefinition, "item_asset"),
        (pystac.Link, "link"),
    )
    for object_type, target in target_types:
        if isinstance(obj, object_type):
            if target not in TARGETS:
                break
            return target
    raise pystac.ExtensionTypeError(f"Unsupported extension target: {type(obj).__name__}")


def _encode(value: Any) -> Any:
    """Convert generated objects at any depth into plain JSON containers."""
    if isinstance(value, dict):
        return {key: _encode(child) for key, child in value.items()}
    if isinstance(value, (list, tuple)):
        return [_encode(child) for child in value]
    return value


class ViewGeometryExtension(
    PropertiesExtension,
    ExtensionManagementMixin[pystac.Item | pystac.Collection | pystac.Catalog],
    Generic[T],
):
    """Typed property wrapper; use ext() to check/register the extension.

    Setters preserve JSON representations, including date/time strings and nested
    dictionaries. None removes a property; set_null() explicitly writes JSON null.
    Validate the owning STAC object to enforce full schema constraints.
    """

    def __init__(self, obj: T, target: str) -> None:
        """Bind a schema-supported STAC object's metadata for live updates."""
        self.obj: T = obj
        self._target = target
        self.additional_read_properties: list[dict[str, Any]] | None = None
        if isinstance(obj, (pystac.Item, pystac.ItemAssetDefinition)):
            self.properties = obj.properties
        else:
            self.properties = obj.extra_fields
        if isinstance(obj, pystac.Asset) and isinstance(obj.owner, pystac.Item):
            self.additional_read_properties = [obj.owner.properties]

    @classmethod
    def get_schema_uri(cls) -> str:
        """The canonical schema identifier used for extension registration."""
        return SCHEMA_URI

    @classmethod
    def has_extension(cls, obj: pystac.STACObject) -> bool:
        """Check this exact schema version; migrations are not generated."""
        return SCHEMA_URI in (obj.stac_extensions or [])

    @classmethod
    def ext(cls, obj: T, add_if_missing: bool = False) -> ViewGeometryExtension[T]:
        """Wrap a schema-supported object and optionally register its extension."""
        target = _target_for(obj)
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
        """Write explicit JSON null; schema validation checks whether it is permitted."""
        key = FIELD_NAMES[name]
        self._check_field(key)
        self._set_property(key, None, pop_if_none=False)

    def apply(self, **values: Any) -> None:
        """Update only supplied fields; omitted fields are preserved.

        Keys are generated Python attribute names. Unknown or inapplicable fields
        are rejected before mutation. Validate the STAC object to check values afterwards.
        """
        for name in values:
            if name not in FIELD_NAMES:
                raise TypeError(f"Unknown extension field: {name}")
            self._check_field(FIELD_NAMES[name])
        for name, value in values.items():
            setattr(self, name, value)

    @property
    def azimuth(self) -> float | None:
        "Azimuth angle"
        self._check_field("view:azimuth")
        if "view:azimuth" in self.properties:
            return cast("float | None", self.properties["view:azimuth"])
        return cast("float | None", self._get_property("view:azimuth", object))

    @azimuth.setter
    def azimuth(self, value: float | None) -> None:
        self._check_field("view:azimuth")
        self._set_property("view:azimuth", _encode(value))

    @property
    def incidence_angle(self) -> float | None:
        "Center incidence angle"
        self._check_field("view:incidence_angle")
        if "view:incidence_angle" in self.properties:
            return cast("float | None", self.properties["view:incidence_angle"])
        return cast("float | None", self._get_property("view:incidence_angle", object))

    @incidence_angle.setter
    def incidence_angle(self, value: float | None) -> None:
        self._check_field("view:incidence_angle")
        self._set_property("view:incidence_angle", _encode(value))

    @property
    def moon_azimuth(self) -> float | None:
        "Moon Azimuth"
        self._check_field("view:moon_azimuth")
        if "view:moon_azimuth" in self.properties:
            return cast("float | None", self.properties["view:moon_azimuth"])
        return cast("float | None", self._get_property("view:moon_azimuth", object))

    @moon_azimuth.setter
    def moon_azimuth(self, value: float | None) -> None:
        self._check_field("view:moon_azimuth")
        self._set_property("view:moon_azimuth", _encode(value))

    @property
    def moon_elevation(self) -> float | None:
        "Moon Elevation"
        self._check_field("view:moon_elevation")
        if "view:moon_elevation" in self.properties:
            return cast("float | None", self.properties["view:moon_elevation"])
        return cast("float | None", self._get_property("view:moon_elevation", object))

    @moon_elevation.setter
    def moon_elevation(self, value: float | None) -> None:
        self._check_field("view:moon_elevation")
        self._set_property("view:moon_elevation", _encode(value))

    @property
    def off_nadir(self) -> float | None:
        "Off Nadir"
        self._check_field("view:off_nadir")
        if "view:off_nadir" in self.properties:
            return cast("float | None", self.properties["view:off_nadir"])
        return cast("float | None", self._get_property("view:off_nadir", object))

    @off_nadir.setter
    def off_nadir(self, value: float | None) -> None:
        self._check_field("view:off_nadir")
        self._set_property("view:off_nadir", _encode(value))

    @property
    def sun_azimuth(self) -> float | None:
        "Sun Azimuth"
        self._check_field("view:sun_azimuth")
        if "view:sun_azimuth" in self.properties:
            return cast("float | None", self.properties["view:sun_azimuth"])
        return cast("float | None", self._get_property("view:sun_azimuth", object))

    @sun_azimuth.setter
    def sun_azimuth(self, value: float | None) -> None:
        self._check_field("view:sun_azimuth")
        self._set_property("view:sun_azimuth", _encode(value))

    @property
    def sun_elevation(self) -> float | None:
        "Sun Elevation"
        self._check_field("view:sun_elevation")
        if "view:sun_elevation" in self.properties:
            return cast("float | None", self.properties["view:sun_elevation"])
        return cast("float | None", self._get_property("view:sun_elevation", object))

    @sun_elevation.setter
    def sun_elevation(self, value: float | None) -> None:
        self._check_field("view:sun_elevation")
        self._set_property("view:sun_elevation", _encode(value))

    @classmethod
    def summaries(
        cls, obj: pystac.Collection, add_if_missing: bool = False
    ) -> SummariesViewGeometryExtension:
        """Wrap schema-declared Collection summaries and optionally register the extension."""
        if not isinstance(obj, pystac.Collection):
            raise pystac.ExtensionTypeError("Summaries require a Collection")
        cls.ensure_has_extension(obj, add_if_missing)
        return SummariesViewGeometryExtension(obj)


class SummariesViewGeometryExtension(SummariesExtension):
    """Collection summaries; ranges, lists and JSON Schema objects are preserved."""

    @property
    def azimuth(self) -> list[Any] | pystac.RangeSummary[Any] | dict[str, Any] | None:
        value = self.summaries.to_dict().get("view:azimuth")
        if isinstance(value, dict) and "minimum" in value and "maximum" in value:
            return self.summaries.get_range("view:azimuth")
        return value

    @azimuth.setter
    def azimuth(self, value: list[Any] | pystac.RangeSummary[Any] | dict[str, Any] | None) -> None:
        self.summaries.remove("view:azimuth")
        self._set_summary("view:azimuth", value)

    @property
    def incidence_angle(self) -> list[Any] | pystac.RangeSummary[Any] | dict[str, Any] | None:
        value = self.summaries.to_dict().get("view:incidence_angle")
        if isinstance(value, dict) and "minimum" in value and "maximum" in value:
            return self.summaries.get_range("view:incidence_angle")
        return value

    @incidence_angle.setter
    def incidence_angle(
        self, value: list[Any] | pystac.RangeSummary[Any] | dict[str, Any] | None
    ) -> None:
        self.summaries.remove("view:incidence_angle")
        self._set_summary("view:incidence_angle", value)

    @property
    def moon_azimuth(self) -> list[Any] | pystac.RangeSummary[Any] | dict[str, Any] | None:
        value = self.summaries.to_dict().get("view:moon_azimuth")
        if isinstance(value, dict) and "minimum" in value and "maximum" in value:
            return self.summaries.get_range("view:moon_azimuth")
        return value

    @moon_azimuth.setter
    def moon_azimuth(
        self, value: list[Any] | pystac.RangeSummary[Any] | dict[str, Any] | None
    ) -> None:
        self.summaries.remove("view:moon_azimuth")
        self._set_summary("view:moon_azimuth", value)

    @property
    def moon_elevation(self) -> list[Any] | pystac.RangeSummary[Any] | dict[str, Any] | None:
        value = self.summaries.to_dict().get("view:moon_elevation")
        if isinstance(value, dict) and "minimum" in value and "maximum" in value:
            return self.summaries.get_range("view:moon_elevation")
        return value

    @moon_elevation.setter
    def moon_elevation(
        self, value: list[Any] | pystac.RangeSummary[Any] | dict[str, Any] | None
    ) -> None:
        self.summaries.remove("view:moon_elevation")
        self._set_summary("view:moon_elevation", value)

    @property
    def off_nadir(self) -> list[Any] | pystac.RangeSummary[Any] | dict[str, Any] | None:
        value = self.summaries.to_dict().get("view:off_nadir")
        if isinstance(value, dict) and "minimum" in value and "maximum" in value:
            return self.summaries.get_range("view:off_nadir")
        return value

    @off_nadir.setter
    def off_nadir(
        self, value: list[Any] | pystac.RangeSummary[Any] | dict[str, Any] | None
    ) -> None:
        self.summaries.remove("view:off_nadir")
        self._set_summary("view:off_nadir", value)

    @property
    def sun_azimuth(self) -> list[Any] | pystac.RangeSummary[Any] | dict[str, Any] | None:
        value = self.summaries.to_dict().get("view:sun_azimuth")
        if isinstance(value, dict) and "minimum" in value and "maximum" in value:
            return self.summaries.get_range("view:sun_azimuth")
        return value

    @sun_azimuth.setter
    def sun_azimuth(
        self, value: list[Any] | pystac.RangeSummary[Any] | dict[str, Any] | None
    ) -> None:
        self.summaries.remove("view:sun_azimuth")
        self._set_summary("view:sun_azimuth", value)

    @property
    def sun_elevation(self) -> list[Any] | pystac.RangeSummary[Any] | dict[str, Any] | None:
        value = self.summaries.to_dict().get("view:sun_elevation")
        if isinstance(value, dict) and "minimum" in value and "maximum" in value:
            return self.summaries.get_range("view:sun_elevation")
        return value

    @sun_elevation.setter
    def sun_elevation(
        self, value: list[Any] | pystac.RangeSummary[Any] | dict[str, Any] | None
    ) -> None:
        self.summaries.remove("view:sun_elevation")
        self._set_summary("view:sun_elevation", value)
