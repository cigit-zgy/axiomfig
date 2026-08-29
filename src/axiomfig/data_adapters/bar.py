from __future__ import annotations

import numpy as np

from ._shared import equal_length, labels_1d, numeric_1d, optional_boolean, optional_text, text


def adapt(variant: str, supplied: dict[str, object]) -> dict[str, object]:
    values = dict(supplied)
    category = labels_1d(values["category"], "category")
    magnitude = numeric_1d(values["value"], "value")
    arrays: dict[str, np.ndarray] = {"category": category, "value": magnitude}
    for role in ("group", "component"):
        if role in values:
            arrays[role] = labels_1d(values[role], role)
    equal_length(arrays)
    values.update(arrays)
    if "error" in values:
        error = np.asarray(values["error"], dtype=float)
        if error.shape not in {(magnitude.size,), (magnitude.size, 2)} or np.any(error < 0):
            raise ValueError("bar error must match values and be non-negative")
        values["error"] = error
        if "uncertainty_type" not in values:
            raise ValueError("uncertainty_type is required when bar error is supplied")
    if "uncertainty_type" in values:
        values["uncertainty_type"] = text(values["uncertainty_type"], "uncertainty_type")
    if variant == "normalized_stacked":
        mode = text(values["normalization"], "normalization")
        if mode not in {"normalize", "proportion"}:
            raise ValueError("normalization must be normalize or proportion")
    optional_boolean(values, "value_labels")
    optional_text(values, "xlabel", "ylabel")
    return values
