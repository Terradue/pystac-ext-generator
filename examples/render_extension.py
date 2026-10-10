"""Generated PySTAC extension. Edit the source schema and regenerate to update."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, ClassVar, Generic, TypeVar, cast

from typing_extensions import TypedDict, Unpack

if TYPE_CHECKING:
    from collections.abc import Mapping

import pystac
from pystac.extensions.base import (
    ExtensionManagementMixin,
    PropertiesExtension,
)

SCHEMA_URI = "https://stac-extensions.github.io/render/v2.1.0/schema.json"
FIELD_TARGETS = {"renders": ["collection", "item"]}
FIELD_NAMES = {"renders": "renders"}
TARGETS = ["collection", "item"]
T = TypeVar("T", bound="pystac.Collection | pystac.Item")


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


class _Unset:
    """Distinguish omitted arguments from explicit JSON null."""


_UNSET = _Unset()


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
    """Wrap schema-declared objects while retaining live backing dictionaries."""
    if value is None or codec is None:
        return value
    kind, detail = codec
    if kind == "object":
        return _MODELS[detail].from_dict(value)
    if kind == "map":
        return _decode_map(value, detail)
    raise ValueError(f"Unknown conversion: {kind}")


def _decode_map(value: Any, codec: Any) -> dict[str, Any]:
    """Decode the values of a schema-declared object map."""
    if not isinstance(value, dict):
        raise TypeError("Expected a JSON object map")
    return {key: _decode(child, codec) for key, child in value.items()}


_O = TypeVar("_O", bound="_Object")


@dataclass
class _Object:
    """Live wrapper around JSON, following PySTAC value-object conventions."""

    _members: ClassVar[dict[str, str]] = {}
    properties: dict[str, Any]

    def __post_init__(self) -> None:
        """Require a JSON object as the live backing value."""
        if not isinstance(self.properties, dict):
            raise TypeError(f"{type(self).__name__} requires a dictionary")

    @classmethod
    def from_dict(cls: type[_O], properties: dict[str, Any], *, copy: bool = False) -> _O:
        """Wrap by reference, or request an independent copy."""
        from copy import deepcopy

        return cls(deepcopy(properties) if copy else properties)

    def to_dict(self) -> dict[str, Any]:
        """Return the live backing JSON dictionary, as PySTAC Render does."""
        return self.properties

    def _apply(self, values: Mapping[str, object]) -> None:
        """Check update names before changing the backing dictionary."""
        unknown = values.keys() - self._members.keys()
        if unknown:
            raise TypeError(f"Unknown fields: {sorted(unknown)}")
        for name, value in values.items():
            if not isinstance(value, _Unset):
                setattr(self, name, value)

    def clear(self, name: str) -> None:
        """Remove a member using its Python attribute name."""
        self.properties.pop(self._members[name], None)

    def set_null(self, name: str) -> None:
        """Store explicit JSON null using a Python member name."""
        self.properties[self._members[name]] = None

    def __repr__(self) -> str:
        return f"<{type(self).__name__} {self.properties!r}>"


class _RenderCreate(TypedDict, total=False):
    """Schema-derived keyword arguments for Render.create()."""

    asset_as_band: bool
    bidx: list[list[int | str]]
    color_formula: str
    colormap: dict[str, Any]
    colormap_name: str
    expression: str | dict[str, Any] | list[Any]
    minmax_zoom: list[float]
    nodata: float | str
    resampling: str
    rescale: list[list[float]]
    title: str


class _RenderUpdate(TypedDict, total=False):
    """Schema-derived partial updates for Render."""

    asset_as_band: bool | None
    assets: list[str] | None
    bidx: list[list[int | str]] | None
    color_formula: str | None
    colormap: dict[str, Any] | None
    colormap_name: str | None
    expression: str | dict[str, Any] | list[Any] | None
    minmax_zoom: list[float] | None
    nodata: float | str | None
    resampling: str | None
    rescale: list[list[float]] | None
    title: str | None


class Render(_Object):
    """Generated nested value object; unknown JSON members are preserved."""

    _members: ClassVar[dict[str, str]] = {
        "asset_as_band": "asset_as_band",
        "assets": "assets",
        "bidx": "bidx",
        "color_formula": "color_formula",
        "colormap": "colormap",
        "colormap_name": "colormap_name",
        "expression": "expression",
        "minmax_zoom": "minmax_zoom",
        "nodata": "nodata",
        "resampling": "resampling",
        "rescale": "rescale",
        "title": "title",
    }

    @classmethod
    def create(
        cls,
        *,
        assets: list[str],
        **_options: Unpack[_RenderCreate],
    ) -> Render:
        """Create a value from required members and typed optional keywords."""
        _values: dict[str, object] = {
            "assets": assets,
            **_options,
        }
        unknown = _values.keys() - cls._members.keys()
        if unknown:
            raise TypeError(f"Unknown fields: {sorted(unknown)}")
        return cls({cls._members[name]: _encode(value) for name, value in _values.items()})

    def apply(self, **values: Unpack[_RenderUpdate]) -> None:
        """Update supplied members; omitted values are preserved and None removes."""
        self._apply(values)

    @property
    def asset_as_band(self) -> bool | None:
        "asset_as_band"
        # Schema-derived typing at the unvalidated PySTAC JSON boundary.
        return cast("bool | None", self.properties.get("asset_as_band"))

    @asset_as_band.setter
    def asset_as_band(self, value: bool | None) -> None:
        if value is None:
            self.properties.pop("asset_as_band", None)
        else:
            self.properties["asset_as_band"] = _encode(value)

    @property
    def assets(self) -> list[str]:
        "assets"
        if "assets" not in self.properties:
            raise pystac.STACError("Missing required property: assets")
        # Schema-derived typing at the unvalidated PySTAC JSON boundary.
        return cast("list[str]", self.properties.get("assets"))

    @assets.setter
    def assets(self, value: list[str] | None) -> None:
        if value is None:
            self.properties.pop("assets", None)
        else:
            self.properties["assets"] = _encode(value)

    @property
    def bidx(self) -> list[list[int | str]] | None:
        "bidx"
        # Schema-derived typing at the unvalidated PySTAC JSON boundary.
        return cast("list[list[int | str]] | None", self.properties.get("bidx"))

    @bidx.setter
    def bidx(self, value: list[list[int | str]] | None) -> None:
        if value is None:
            self.properties.pop("bidx", None)
        else:
            self.properties["bidx"] = _encode(value)

    @property
    def color_formula(self) -> str | None:
        "color_formula"
        # Schema-derived typing at the unvalidated PySTAC JSON boundary.
        return cast("str | None", self.properties.get("color_formula"))

    @color_formula.setter
    def color_formula(self, value: str | None) -> None:
        if value is None:
            self.properties.pop("color_formula", None)
        else:
            self.properties["color_formula"] = _encode(value)

    @property
    def colormap(self) -> dict[str, Any] | None:
        "colormap"
        # Schema-derived typing at the unvalidated PySTAC JSON boundary.
        return cast("dict[str, Any] | None", self.properties.get("colormap"))

    @colormap.setter
    def colormap(self, value: dict[str, Any] | None) -> None:
        if value is None:
            self.properties.pop("colormap", None)
        else:
            self.properties["colormap"] = _encode(value)

    @property
    def colormap_name(self) -> str | None:
        "colormap_name"
        # Schema-derived typing at the unvalidated PySTAC JSON boundary.
        return cast("str | None", self.properties.get("colormap_name"))

    @colormap_name.setter
    def colormap_name(self, value: str | None) -> None:
        if value is None:
            self.properties.pop("colormap_name", None)
        else:
            self.properties["colormap_name"] = _encode(value)

    @property
    def expression(self) -> str | dict[str, Any] | list[Any] | None:
        "expression"
        # Schema-derived typing at the unvalidated PySTAC JSON boundary.
        return cast("str | dict[str, Any] | list[Any] | None", self.properties.get("expression"))

    @expression.setter
    def expression(self, value: str | dict[str, Any] | list[Any] | None) -> None:
        if value is None:
            self.properties.pop("expression", None)
        else:
            self.properties["expression"] = _encode(value)

    @property
    def minmax_zoom(self) -> list[float] | None:
        "minmax_zoom"
        # Schema-derived typing at the unvalidated PySTAC JSON boundary.
        return cast("list[float] | None", self.properties.get("minmax_zoom"))

    @minmax_zoom.setter
    def minmax_zoom(self, value: list[float] | None) -> None:
        if value is None:
            self.properties.pop("minmax_zoom", None)
        else:
            self.properties["minmax_zoom"] = _encode(value)

    @property
    def nodata(self) -> float | str | None:
        "nodata"
        # Schema-derived typing at the unvalidated PySTAC JSON boundary.
        return cast("float | str | None", self.properties.get("nodata"))

    @nodata.setter
    def nodata(self, value: float | str | None) -> None:
        if value is None:
            self.properties.pop("nodata", None)
        else:
            self.properties["nodata"] = _encode(value)

    @property
    def resampling(self) -> str | None:
        "resampling"
        # Schema-derived typing at the unvalidated PySTAC JSON boundary.
        return cast("str | None", self.properties.get("resampling"))

    @resampling.setter
    def resampling(self, value: str | None) -> None:
        if value is None:
            self.properties.pop("resampling", None)
        else:
            self.properties["resampling"] = _encode(value)

    @property
    def rescale(self) -> list[list[float]] | None:
        "rescale"
        # Schema-derived typing at the unvalidated PySTAC JSON boundary.
        return cast("list[list[float]] | None", self.properties.get("rescale"))

    @rescale.setter
    def rescale(self, value: list[list[float]] | None) -> None:
        if value is None:
            self.properties.pop("rescale", None)
        else:
            self.properties["rescale"] = _encode(value)

    @property
    def title(self) -> str | None:
        "title"
        # Schema-derived typing at the unvalidated PySTAC JSON boundary.
        return cast("str | None", self.properties.get("title"))

    @title.setter
    def title(self, value: str | None) -> None:
        if value is None:
            self.properties.pop("title", None)
        else:
            self.properties["title"] = _encode(value)


_MODELS: dict[str, type[_Object]] = {
    "Render": Render,
}


class RenderingExtension(
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

    @classmethod
    def get_schema_uri(cls) -> str:
        """The canonical schema identifier used for extension registration."""
        return SCHEMA_URI

    @classmethod
    def has_extension(cls, obj: pystac.STACObject) -> bool:
        """Check this exact schema version; migrations are not generated."""
        return SCHEMA_URI in (obj.stac_extensions or [])

    @classmethod
    def ext(cls, obj: T, add_if_missing: bool = False) -> RenderingExtension[T]:
        """Wrap a schema-supported object and optionally register its extension."""
        target = _target_for(obj)
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
    def renders(self) -> dict[str, Render] | None:
        "renders"
        self._check_field("renders")
        if "renders" in self.properties:
            return cast(
                "dict[str, Render] | None",
                _decode(self.properties["renders"], ["map", ["object", "Render"]]),
            )
        return cast(
            "dict[str, Render] | None",
            _decode(self._get_property("renders", object), ["map", ["object", "Render"]]),
        )

    @renders.setter
    def renders(self, value: dict[str, Render] | None) -> None:
        self._check_field("renders")
        self._set_property("renders", _encode(value))
