"""Minimal validated Figure Intent boundary for LLM-facing execution."""

from __future__ import annotations

import csv
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any

from matplotlib.figure import Figure

from axiomfig.config import load_contracts
from axiomfig.structured_io import StructuredDataError, load_yaml
from axiomfig.templates import TEMPLATE_ADAPTERS, adapt_template_data, build_template
from axiomfig.templates.registry import load_family_contract, load_template_registry

FORBIDDEN_VISUAL_FIELDS = frozenset(
    {
        "font_size",
        "linewidth",
        "tick_length",
        "legend_x",
        "legend_y",
        "panel_offset",
        "bar_width",
        "colorbar_width",
        "subplot_wspace",
        "subplot_hspace",
        "figure_width",
        "figure_height",
    }
)


class FigureIntentError(ValueError):
    """Raised when an intent asks for an invalid or non-scientific decision."""


@dataclass(frozen=True)
class FigureIntent:
    template_id: str
    data: Mapping[str, str]
    geometry: str
    typography: str
    semantics: Mapping[str, Any]


def _normalize_template_id(value: object) -> str:
    if not isinstance(value, str):
        raise FigureIntentError("template must be a string")
    normalized = value.replace(".", "/")
    if normalized.count("/") != 1:
        raise FigureIntentError("template must use family.variant or family/variant")
    available = {spec.template_id for spec in load_template_registry()}
    if normalized not in available:
        raise FigureIntentError(f"unknown template: {value!r}")
    return normalized


def _mapping(value: object, name: str) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise FigureIntentError(f"{name} must be a mapping")
    if not all(isinstance(key, str) for key in value):
        raise FigureIntentError(f"{name} keys must be strings")
    return dict(value)


def parse_figure_intent(document: Mapping[str, Any]) -> FigureIntent:
    if not isinstance(document, Mapping):
        raise FigureIntentError("Figure Intent root must be a mapping")
    if not all(isinstance(key, str) for key in document):
        raise FigureIntentError("Figure Intent keys must be strings")
    forbidden = FORBIDDEN_VISUAL_FIELDS & set(document)
    if forbidden:
        rendered = ", ".join(sorted(forbidden))
        raise FigureIntentError(f"deterministic visual field is forbidden: {rendered}")
    allowed_top = {"template", "data", "geometry", "typography", "semantics"}
    unknown = set(document) - allowed_top
    if unknown:
        raise FigureIntentError(f"unknown Figure Intent fields: {sorted(unknown)}")

    template_id = _normalize_template_id(document.get("template"))
    family, variant = template_id.split("/", maxsplit=1)
    data = _mapping(document.get("data"), "data")
    if not all(isinstance(value, str) and value for value in data.values()):
        raise FigureIntentError("data values must be non-empty dataset keys or column names")
    semantics = _mapping(document.get("semantics"), "semantics")
    forbidden_semantics = FORBIDDEN_VISUAL_FIELDS & set(semantics)
    if forbidden_semantics:
        rendered = ", ".join(sorted(forbidden_semantics))
        raise FigureIntentError(f"deterministic visual field is forbidden: {rendered}")

    default_geometry = next(
        spec.geometry for spec in load_template_registry() if spec.template_id == template_id
    )
    geometry = document.get("geometry", default_geometry)
    typography = document.get("typography", "sans")
    if not isinstance(geometry, str):
        raise FigureIntentError("geometry must be a string")
    if not isinstance(typography, str):
        raise FigureIntentError("typography must be a string")
    contracts = load_contracts()
    if geometry not in contracts.style["geometry"]:
        raise FigureIntentError(f"unknown geometry: {geometry!r}")
    if typography not in contracts.fonts["modes"]:
        raise FigureIntentError(f"unknown typography: {typography!r}")

    contract = load_family_contract(family)["variants"][variant]
    permitted = set(contract["required"]) | set(contract.get("optional", ()))
    provided = set(data) | set(semantics)
    if provided:
        unknown_roles = provided - permitted
        if unknown_roles:
            raise FigureIntentError(
                f"unsupported fields for {template_id}: {sorted(unknown_roles)}"
            )
        missing = set(contract["required"]) - provided
        if missing:
            raise FigureIntentError(f"missing required fields for {template_id}: {sorted(missing)}")

    return FigureIntent(
        template_id=template_id,
        data=MappingProxyType(data),
        geometry=geometry,
        typography=typography,
        semantics=MappingProxyType(semantics),
    )


def load_figure_intent(path: Path) -> FigureIntent:
    path = Path(path).expanduser().resolve()
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise FigureIntentError(f"cannot read Figure Intent: {path}") from exc
    try:
        document = (
            json.loads(text)
            if path.suffix.lower() == ".json"
            else load_yaml(text, source=str(path))
        )
    except (json.JSONDecodeError, StructuredDataError) as exc:
        raise FigureIntentError(f"cannot parse Figure Intent: {exc}") from exc
    if not isinstance(document, Mapping):
        raise FigureIntentError("Figure Intent root must be a mapping")
    return parse_figure_intent(document)


def _coerce_csv_value(value: str) -> object:
    try:
        return float(value)
    except ValueError:
        return value


def load_dataset(path: Path) -> Mapping[str, object]:
    path = Path(path).expanduser().resolve()
    if path.suffix.lower() == ".csv":
        try:
            with path.open(encoding="utf-8", newline="") as stream:
                reader = csv.DictReader(stream)
                rows = list(reader)
        except (OSError, UnicodeError, csv.Error) as exc:
            raise FigureIntentError(f"cannot read dataset: {path}") from exc
        fieldnames = reader.fieldnames
        if not fieldnames or not rows:
            raise FigureIntentError("CSV dataset must contain a header and at least one row")
        if any(not isinstance(name, str) or not name for name in fieldnames):
            raise FigureIntentError("CSV column names must be non-empty strings")
        if len(fieldnames) != len(set(fieldnames)):
            raise FigureIntentError("duplicate CSV column names are not allowed")
        if any(
            None in row
            or set(row) != set(fieldnames)
            or any(value is None for value in row.values())
            for row in rows
        ):
            raise FigureIntentError("CSV rows must contain the same number of fields")
        return {key: tuple(_coerce_csv_value(row[key]) for row in rows) for key in fieldnames}
    if path.suffix.lower() == ".json":
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError) as exc:
            raise FigureIntentError(f"cannot read dataset: {path}") from exc
        except json.JSONDecodeError as exc:
            raise FigureIntentError(f"cannot parse dataset: {exc}") from exc
        if isinstance(value, Mapping):
            if not all(isinstance(key, str) for key in value):
                raise FigureIntentError("JSON dataset object keys must be strings")
            return dict(value)
        if isinstance(value, Sequence) and value and all(isinstance(row, Mapping) for row in value):
            keys = tuple(value[0])
            if not all(isinstance(key, str) for key in keys) or any(
                set(row) != set(keys) or not all(isinstance(key, str) for key in row)
                for row in value
            ):
                raise FigureIntentError("JSON object rows must have the same string keys")
            return {key: tuple(row[key] for row in value) for key in keys}
        raise FigureIntentError("JSON dataset must be an object or a non-empty array of objects")
    raise FigureIntentError("dataset must use .csv or .json")


def _resolve_data(intent: FigureIntent, dataset: Mapping[str, object]) -> dict[str, object]:
    missing = {key for key in intent.data.values() if key not in dataset}
    if missing:
        raise FigureIntentError(f"dataset keys are missing: {sorted(missing)}")
    return {role: dataset[key] for role, key in intent.data.items()}


def build_intent_figure(
    intent: FigureIntent,
    dataset: Mapping[str, object] | None = None,
) -> Figure:
    if not intent.data:
        return build_template(intent.template_id)
    if dataset is None:
        raise FigureIntentError("a dataset is required when Figure Intent declares data")
    if intent.template_id not in TEMPLATE_ADAPTERS:
        raise FigureIntentError(f"no v1 data adapter for template {intent.template_id!r}")
    kwargs = {**_resolve_data(intent, dataset), **dict(intent.semantics)}
    try:
        adapted = adapt_template_data(intent.template_id, kwargs)
    except (IndexError, KeyError, OverflowError, TypeError, ValueError) as exc:
        detail = str(exc) or f"invalid data for template {intent.template_id!r}"
        raise FigureIntentError(detail) from exc
    return build_template(intent.template_id, **adapted)
