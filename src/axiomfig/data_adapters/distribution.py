from __future__ import annotations

import numpy as np

from ._shared import equal_length, labels_1d, numeric_1d, optional_text, scalar, text


def adapt(variant: str, supplied: dict[str, object]) -> dict[str, object]:
    values = dict(supplied)
    if variant == "density":
        arrays = {
            "x": numeric_1d(values["x"], "x", minimum=2),
            "density": numeric_1d(values["density"], "density", minimum=2),
        }
        equal_length(arrays, minimum=2)
        if np.any(arrays["density"] < 0):
            raise ValueError("density must be non-negative")
        values.update(arrays)
    else:
        values["value"] = numeric_1d(values["value"], "value", minimum=2)
    if "category" in values:
        category = labels_1d(values["category"], "category", minimum=2)
        if category.size != np.asarray(values["value"]).size:
            raise ValueError("value and category must be equal-length")
        values["category"] = category
    if "group" in values:
        group = labels_1d(values["group"], "group", minimum=2)
        reference = values["x"] if variant == "density" else values["value"]
        if group.size != np.asarray(reference).size:
            raise ValueError("group must be equal-length with distribution data")
        values["group"] = group
    if "bins" in values:
        raw = np.asarray(values["bins"])
        if raw.ndim == 0:
            bins = int(scalar(raw, "bins"))
            if bins < 1:
                raise ValueError("bins must be positive")
            values["bins"] = bins
        else:
            edges = numeric_1d(raw, "bins", minimum=2)
            if np.any(np.diff(edges) <= 0):
                raise ValueError("bin edges must be strictly increasing")
            values["bins"] = edges
    if "jitter" in values:
        jitter = scalar(values["jitter"], "jitter")
        if jitter < 0:
            raise ValueError("jitter must be non-negative")
        values["jitter"] = jitter
    if "summary" in values:
        values["summary"] = text(values["summary"], "summary")
    optional_text(values, "xlabel", "ylabel")
    return values
