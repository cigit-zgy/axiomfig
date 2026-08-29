"""Minimal validated Figure Intent boundary for LLM-facing execution."""

from __future__ import annotations

import csv
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any

import yaml
from matplotlib.figure import Figure

from axiomfig.config import load_contracts
from axiomfig.data_adapters import DATA_ADAPTERS, adapt_template_data
from axiomfig.templates import build_template
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

    geometry = document.get("geometry", "single-column")
    typography = document.get("typography", "sans")
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
        geometry=str(geometry),
        typography=str(typography),
        semantics=MappingProxyType(semantics),
    )


def load_figure_intent(path: Path) -> FigureIntent:
    path = Path(path).expanduser().resolve()
    text = path.read_text(encoding="utf-8")
    document = json.loads(text) if path.suffix.lower() == ".json" else yaml.safe_load(text)
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
        with path.open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream))
        if not rows or not rows[0]:
            raise FigureIntentError("CSV dataset must contain a header and at least one row")
        return {key: tuple(_coerce_csv_value(row[key]) for row in rows) for key in rows[0]}
    if path.suffix.lower() == ".json":
        value = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(value, Mapping):
            return dict(value)
        if isinstance(value, Sequence) and value and all(isinstance(row, Mapping) for row in value):
            keys = tuple(value[0])
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
    if intent.template_id not in DATA_ADAPTERS:
        raise FigureIntentError(f"no v1 data adapter for template {intent.template_id!r}")
    kwargs = {**_resolve_data(intent, dataset), **dict(intent.semantics)}
    try:
        adapted = adapt_template_data(intent.template_id, kwargs)
        return build_template(intent.template_id, **adapted)
    except ValueError as exc:
        raise FigureIntentError(str(exc)) from exc
