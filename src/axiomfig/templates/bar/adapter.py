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


def _unique_logical_keys(values: dict[str, object], names: Sequence[str]) -> None:
    arrays = [np.asarray(values[name], dtype=object) for name in names]
    keys = list(zip(*(array.tolist() for array in arrays), strict=True))
    if len(keys) != len(set(keys)):
        rendered = ", ".join(names)
        raise ValueError(f"bar duplicate logical key for {rendered}")


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


def _adapt_orientation(values: dict[str, object]) -> None:
    if "orientation" not in values:
        return
    orientation = text(values["orientation"], "orientation")
    if orientation not in _ORIENTATIONS:
        raise ValueError("orientation must be vertical or horizontal")
    values["orientation"] = orientation


def _adapt_category_values(variant: str, values: dict[str, object]) -> None:
    category = labels_1d(values["category"], "category")
    magnitude = numeric_1d(values["value"], "value")
    arrays: dict[str, np.ndarray] = {"category": category, "value": magnitude}
    for role in ("group", "component", "side"):
        if role in values:
            arrays[role] = labels_1d(values[role], role)
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

    if variant in {"simple", "grouped"}:
        _adapt_error(values, magnitude)
    if variant == "normalized_stacked":
        mode = text(values["normalization"], "normalization")
        if mode not in {"normalize", "proportion"}:
            raise ValueError("normalization must be normalize or proportion")
        if np.any(magnitude < 0):
            raise ValueError("normalized stacks require non-negative values")
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


def _adapt_range(values: dict[str, object]) -> None:
    category = labels_1d(values["category"], "category")
    lower = numeric_1d(values["lower"], "lower")
    upper = numeric_1d(values["upper"], "upper")
    arrays = {"category": category, "lower": lower, "upper": upper}
    equal_length(arrays)
    if np.any(lower > upper):
        raise ValueError("bar range requires lower <= upper for every category")
    values.update(arrays)
    _unique_logical_keys(values, ("category",))


def _adapt_waterfall(values: dict[str, object]) -> None:
    step = labels_1d(values["step"], "step")
    delta = numeric_1d(values["delta"], "delta")
    role = labels_1d(values["role"], "role")
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
    for index, (selected_delta, selected_role) in enumerate(zip(delta, role, strict=True)):
        if selected_role == "change":
            if running is None:
                raise ValueError("waterfall cannot begin with a change row without a subtotal")
            running += float(selected_delta)
        elif selected_role == "subtotal":
            if running is not None and not np.isclose(selected_delta, running):
                raise ValueError("waterfall subtotal must equal the current cumulative value")
            running = float(selected_delta)
        elif index != len(role) - 1 or running is None or not np.isclose(selected_delta, running):
            raise ValueError("waterfall total must be final and equal the cumulative value")


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
