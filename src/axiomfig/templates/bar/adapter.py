from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from axiomfig.templates._adapter import (
    equal_length,
    labels_1d,
    numeric_1d,
    optional_boolean,
    optional_text,
    text,
)
from axiomfig.templates.bar.geometry import error_limits, linear_limits

_CATEGORY_VALUE_VARIANTS = {
    "simple",
    "vertical",
    "horizontal",
    "dot",
    "grouped",
    "stacked",
    "normalized_stacked",
    "grouped_stacked",
    "diverging_stacked",
    "mirrored",
}
_ORIENTATIONS = {"vertical", "horizontal"}
PROPORTION_ABSOLUTE_TOLERANCE = 1e-8
WATERFALL_RECONCILIATION_ABSOLUTE_TOLERANCE = 1e-8


def _require_finite_derived(*arrays: np.ndarray) -> None:
    if not all(np.all(np.isfinite(array)) for array in arrays):
        raise ValueError("bar values must produce finite derived geometry")
    linear_limits(*arrays)


def _validate_error_geometry(magnitude: np.ndarray, error: np.ndarray) -> None:
    error_limits(magnitude, error)


def _validate_cumulative_geometry(
    values: dict[str, object],
    key_names: Sequence[str],
    *,
    split_sign: bool = False,
) -> None:
    components = np.asarray(values["component"], dtype=object)
    magnitude = np.asarray(values["value"], dtype=float)
    component_order = tuple(dict.fromkeys(components.tolist()))
    running: dict[tuple[object, ...], float] = {}
    endpoints: list[float] = [0.0]
    for component in component_order:
        for index in np.flatnonzero(components == component):
            key = tuple(np.asarray(values[name], dtype=object)[index] for name in key_names)
            selected = float(magnitude[index])
            if split_sign:
                key = (*key, "positive" if selected >= 0 else "negative")
            with np.errstate(over="ignore", invalid="ignore"):
                updated = running.get(key, 0.0) + selected
            if not np.isfinite(updated):
                raise ValueError("bar values must produce finite derived geometry")
            running[key] = updated
            endpoints.append(updated)
    _require_finite_derived(np.asarray(endpoints, dtype=float))


def _bar_labels(value: object, name: str) -> np.ndarray:
    array = np.asarray(value, dtype=object)
    if array.ndim == 1 and any(
        item is None
        or (isinstance(item, (float, np.floating)) and not np.isfinite(item))
        or (isinstance(item, str) and not item.strip())
        for item in array
    ):
        raise ValueError(f"{name} labels must be non-null and non-empty")
    return labels_1d(value, name)


def _unique_logical_keys(values: dict[str, object], names: Sequence[str]) -> None:
    arrays = [np.asarray(values[name], dtype=object) for name in names]
    keys = list(zip(*(array.tolist() for array in arrays), strict=True))
    if len(keys) != len(set(keys)):
        rendered = ", ".join(names)
        raise ValueError(f"bar duplicate logical key for {rendered}")


def _complete_logical_grid(values: dict[str, object], names: Sequence[str]) -> None:
    expected = 1
    for name in names:
        expected *= len(dict.fromkeys(np.asarray(values[name], dtype=object).tolist()))
    row_count = len(np.asarray(values[names[0]], dtype=object))
    if row_count != expected:
        rendered = ", ".join(names)
        raise ValueError(f"bar {rendered} rows must form a complete logical grid")


def _category_totals(values: dict[str, object]) -> np.ndarray:
    categories = np.asarray(values["category"], dtype=object)
    magnitude = np.asarray(values["value"], dtype=float)
    labels = tuple(dict.fromkeys(categories.tolist()))
    with np.errstate(over="ignore", invalid="ignore"):
        totals = np.asarray([magnitude[categories == label].sum() for label in labels], dtype=float)
    if not np.all(np.isfinite(totals)):
        raise ValueError("bar values must produce finite derived geometry")
    return totals


def _adapt_error(values: dict[str, object], magnitude: np.ndarray) -> None:
    if "error" not in values:
        if "uncertainty_type" in values:
            raise ValueError("bar uncertainty_type requires supplied error values")
        return
    try:
        error = np.asarray(values["error"], dtype=float)
    except (TypeError, ValueError) as exc:
        raise ValueError("bar error must be finite numeric data") from exc
    if (
        error.shape not in {(magnitude.size,), (magnitude.size, 2)}
        or not np.all(np.isfinite(error))
        or np.any(error < 0)
    ):
        raise ValueError("bar error must match values and be finite and non-negative")
    if "uncertainty_type" not in values:
        raise ValueError("uncertainty_type is required when bar error is supplied")
    values["error"] = error
    values["uncertainty_type"] = text(values["uncertainty_type"], "uncertainty_type")
    _validate_error_geometry(magnitude, error)


def _adapt_orientation(values: dict[str, object]) -> None:
    if "orientation" not in values:
        return
    orientation = text(values["orientation"], "orientation")
    if orientation not in _ORIENTATIONS:
        raise ValueError("orientation must be vertical or horizontal")
    values["orientation"] = orientation


def _adapt_category_values(variant: str, values: dict[str, object]) -> None:
    category = _bar_labels(values["category"], "category")
    magnitude = numeric_1d(values["value"], "value")
    arrays: dict[str, np.ndarray] = {"category": category, "value": magnitude}
    for role in ("group", "component", "side"):
        if role in values:
            arrays[role] = _bar_labels(values[role], role)
    equal_length(arrays)
    values.update(arrays)

    key_roles = {
        "simple": ("category",),
        "vertical": ("category",),
        "horizontal": ("category",),
        "dot": ("category",),
        "grouped": ("category", "group"),
        "stacked": ("category", "component"),
        "normalized_stacked": ("category", "component"),
        "grouped_stacked": ("category", "group", "component"),
        "diverging_stacked": ("category", "component"),
        "mirrored": ("category", "side"),
    }
    _unique_logical_keys(values, key_roles[variant])
    if variant in {
        "grouped",
        "stacked",
        "normalized_stacked",
        "grouped_stacked",
        "diverging_stacked",
        "mirrored",
    }:
        _complete_logical_grid(values, key_roles[variant])

    if variant in {"simple", "grouped"}:
        _adapt_error(values, magnitude)
        if "error" not in values:
            _require_finite_derived(magnitude)
    elif variant in {"vertical", "horizontal", "dot"}:
        _require_finite_derived(magnitude)
    elif variant == "stacked":
        _validate_cumulative_geometry(values, ("category",))
    elif variant == "grouped_stacked":
        _validate_cumulative_geometry(values, ("category", "group"))
    elif variant == "diverging_stacked":
        _validate_cumulative_geometry(values, ("category",), split_sign=True)
    if variant == "normalized_stacked":
        mode = text(values["normalization"], "normalization")
        if mode not in {"normalize", "proportion"}:
            raise ValueError("normalization must be normalize or proportion")
        if np.any(magnitude < 0):
            raise ValueError("normalized stacks require non-negative values")
        totals = _category_totals(values)
        if mode == "normalize" and np.any(totals <= 0):
            raise ValueError("normalized stacks require positive category totals")
        if mode == "proportion" and np.any(np.abs(totals - 1.0) > PROPORTION_ABSOLUTE_TOLERANCE):
            raise ValueError("proportion stacks must sum to one within absolute tolerance 1e-8")
        values["normalization"] = mode
    if variant == "mirrored":
        sides = list(dict.fromkeys(np.asarray(values["side"], dtype=object).astype(str)))
        if len(sides) != 2:
            raise ValueError("mirrored bars require exactly two side labels")
        if np.any(magnitude < 0):
            raise ValueError("mirrored bar input values must be non-negative")
        mirror_side = text(values["mirror_side"], "mirror_side")
        if mirror_side not in sides:
            raise ValueError("mirror_side must identify one supplied side")
        values["mirror_side"] = mirror_side
        signed = magnitude.copy()
        signed[np.asarray(values["side"], dtype=object).astype(str) == mirror_side] *= -1
        _require_finite_derived(signed)


def _adapt_range(values: dict[str, object]) -> None:
    category = _bar_labels(values["category"], "category")
    lower = numeric_1d(values["lower"], "lower")
    upper = numeric_1d(values["upper"], "upper")
    arrays = {"category": category, "lower": lower, "upper": upper}
    equal_length(arrays)
    if np.any(lower > upper):
        raise ValueError("bar range requires lower <= upper for every category")
    with np.errstate(over="ignore", invalid="ignore"):
        span = upper - lower
    _require_finite_derived(lower, upper, span)
    values.update(arrays)
    _unique_logical_keys(values, ("category",))


def _adapt_waterfall(values: dict[str, object]) -> None:
    step = _bar_labels(values["step"], "step")
    delta = numeric_1d(values["delta"], "delta")
    role = _bar_labels(values["role"], "role")
    arrays = {"step": step, "delta": delta, "role": role}
    equal_length(arrays)
    values.update(arrays)
    _unique_logical_keys(values, ("step",))
    invalid = sorted(set(role.astype(str)) - {"change", "subtotal", "total"})
    if invalid:
        raise ValueError(f"waterfall role must be change, subtotal, or total: {invalid}")
    if role[-1] != "total" or np.count_nonzero(role == "total") != 1:
        raise ValueError("waterfall requires exactly one final total row")

    running: float | None = None
    starts: list[float] = []
    endpoints: list[float] = []
    for index, (selected_delta, selected_role) in enumerate(zip(delta, role, strict=True)):
        if selected_role == "change":
            if running is None:
                raise ValueError("waterfall cannot begin with a change row without a subtotal")
            start = running
            with np.errstate(over="ignore", invalid="ignore"):
                running += float(selected_delta)
            if not np.isfinite(running):
                raise ValueError("bar values must produce finite derived geometry")
        elif selected_role == "subtotal":
            if running is not None and not np.isclose(
                selected_delta,
                running,
                atol=WATERFALL_RECONCILIATION_ABSOLUTE_TOLERANCE,
                rtol=0.0,
            ):
                raise ValueError("waterfall subtotal must equal the current cumulative value")
            start = 0.0
            running = float(selected_delta)
        elif (
            index != len(role) - 1
            or running is None
            or not np.isclose(
                selected_delta,
                running,
                atol=WATERFALL_RECONCILIATION_ABSOLUTE_TOLERANCE,
                rtol=0.0,
            )
        ):
            raise ValueError("waterfall total must be final and equal the cumulative value")
        else:
            start = 0.0
            running = float(selected_delta)
        starts.append(min(start, running))
        endpoints.append(max(start, running))
    _require_finite_derived(np.asarray(starts), np.asarray(endpoints))


def adapt(variant: str, supplied: dict[str, object]) -> dict[str, object]:
    values = dict(supplied)
    if variant in _CATEGORY_VALUE_VARIANTS:
        _adapt_category_values(variant, values)
    elif variant == "range":
        _adapt_range(values)
    elif variant == "waterfall":
        _adapt_waterfall(values)
    else:
        raise ValueError(f"unknown bar grammar: {variant}")

    _adapt_orientation(values)
    optional_boolean(values, "value_labels")
    optional_text(values, "xlabel", "ylabel")
    return values
