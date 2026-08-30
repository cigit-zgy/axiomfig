from __future__ import annotations

import numpy as np

from axiomfig.templates._adapter import (
    equal_length,
    numeric_1d,
    numeric_matrix,
    optional_text,
    scalar,
    text,
)


def adapt(variant: str, supplied: dict[str, object]) -> dict[str, object]:
    values = dict(supplied)
    x = numeric_1d(values["x"], "x", minimum=2)
    values["x"] = x
    if variant == "multi":
        series = numeric_matrix(values["series_values"], "series_values")
        labels = np.asarray(values["series_labels"], dtype=object)
        if series.shape[1] != x.size or labels.ndim != 1 or labels.size != series.shape[0]:
            raise ValueError("series_values rows and series_labels must match x")
        values["series_values"] = series
        values["series_labels"] = np.asarray([str(item) for item in labels], dtype=object)
    elif variant == "confidence_band":
        arrays = {
            name: numeric_1d(values[name], name, minimum=2)
            for name in ("estimate", "lower", "upper")
        }
        equal_length({"x": x, **arrays}, minimum=2)
        if np.any(arrays["lower"] > arrays["estimate"]) or np.any(
            arrays["upper"] < arrays["estimate"]
        ):
            raise ValueError("confidence bounds must contain each estimate")
        values.update(arrays)
        values["uncertainty_type"] = text(values["uncertainty_type"], "uncertainty_type")
    elif variant == "errorbar":
        estimate = numeric_1d(values["estimate"], "estimate", minimum=2)
        equal_length({"x": x, "estimate": estimate}, minimum=2)
        error = np.asarray(values["error"], dtype=float)
        if error.shape not in {(x.size,), (x.size, 2)} or np.any(error < 0):
            raise ValueError("error must contain non-negative half-widths or lower/upper errors")
        values.update(
            estimate=estimate,
            error=error,
            uncertainty_type=text(values["uncertainty_type"], "uncertainty_type"),
        )
    else:
        y = numeric_1d(values["y"], "y", minimum=2)
        equal_length({"x": x, "y": y}, minimum=2)
        values["y"] = y
        if variant == "step" and "where" in values:
            where = text(values["where"], "where")
            if where not in {"pre", "mid", "post"}:
                raise ValueError("where must be pre, mid, or post")
        if variant == "area" and "baseline" in values:
            baseline = np.asarray(values["baseline"], dtype=float)
            if baseline.ndim == 0:
                values["baseline"] = scalar(baseline, "baseline")
            elif baseline.shape == x.shape and np.all(np.isfinite(baseline)):
                values["baseline"] = baseline
            else:
                raise ValueError("baseline must be scalar or match x")
    optional_text(values, "xlabel", "ylabel")
    return values
