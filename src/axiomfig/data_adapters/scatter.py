from __future__ import annotations

import numpy as np

from ._shared import equal_length, labels_1d, numeric_1d, optional_text, scalar


def adapt(variant: str, supplied: dict[str, object]) -> dict[str, object]:
    values = dict(supplied)
    if variant == "parity":
        arrays = {
            "observed": numeric_1d(values["observed"], "observed", minimum=2),
            "predicted": numeric_1d(values["predicted"], "predicted", minimum=2),
        }
    else:
        arrays = {
            "x": numeric_1d(values["x"], "x", minimum=2),
            "y": numeric_1d(values["y"], "y", minimum=2),
        }
    equal_length(arrays, minimum=2)
    values.update(arrays)
    count = next(iter(arrays.values())).size
    if variant == "grouped" or "group" in values:
        group = labels_1d(values["group"], "group")
        if group.size != count:
            raise ValueError("group must be equal-length with scatter data")
        values["group"] = group
    if variant == "regression":
        fitted = numeric_1d(values["fitted"], "fitted", minimum=2)
        if fitted.size != count:
            raise ValueError("fitted must be equal-length with x and y")
        values["fitted"] = fitted
    if variant == "bubble":
        size = numeric_1d(values["size"], "size", minimum=2)
        if size.size != count or np.any(size <= 0):
            raise ValueError("bubble size must be positive and equal-length")
        values["size"] = size
    if variant == "hexbin" and "gridsize" in values:
        gridsize = int(scalar(values["gridsize"], "gridsize"))
        if gridsize < 2:
            raise ValueError("gridsize must be at least 2")
        values["gridsize"] = gridsize
    if variant == "parity" and "identity_limits" in values:
        limits = numeric_1d(values["identity_limits"], "identity_limits")
        if limits.shape != (2,) or limits[0] >= limits[1]:
            raise ValueError("identity_limits must contain increasing lower and upper values")
        values["identity_limits"] = limits
    optional_text(values, "fit_label", "size_label", "count_label", "xlabel", "ylabel")
    return values
