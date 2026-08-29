from __future__ import annotations

import numpy as np

from ._shared import (
    equal_length,
    interval,
    labels_1d,
    numeric_1d,
    optional_text,
    scalar,
    text,
)

_PAIR_ROLES = {
    "residual": ("fitted", "residual"),
    "bland_altman": ("mean", "difference"),
    "calibration": ("predicted_probability", "observed_frequency"),
    "roc": ("false_positive_rate", "true_positive_rate"),
    "precision_recall": ("recall", "precision"),
    "qq": ("theoretical_quantile", "sample_quantile"),
}


def adapt(variant: str, supplied: dict[str, object]) -> dict[str, object]:
    values = dict(supplied)
    if variant in _PAIR_ROLES:
        names = _PAIR_ROLES[variant]
        arrays = {name: numeric_1d(values[name], name, minimum=2) for name in names}
        equal_length(arrays, minimum=2)
        values.update(arrays)
        count = next(iter(arrays.values())).size
    elif variant == "learning_curve":
        arrays = {
            "iteration": numeric_1d(values["iteration"], "iteration", minimum=2),
            "metric": numeric_1d(values["metric"], "metric", minimum=2),
            "series": labels_1d(values["series"], "series", minimum=2),
        }
        equal_length(arrays, minimum=2)
        values.update(arrays)
        count = arrays["iteration"].size
    else:
        feature = labels_1d(values["feature"], "feature")
        importance = numeric_1d(values["importance"], "importance")
        if feature.size != importance.size:
            raise ValueError("feature and importance must be equal-length")
        values.update(feature=feature, importance=importance)
        count = feature.size
    if "group" in values:
        group = labels_1d(values["group"], "group")
        if group.size != count:
            raise ValueError("group must be equal-length with diagnostic data")
        values["group"] = group
    if "trend" in values:
        trend = numeric_1d(values["trend"], "trend", minimum=2)
        if trend.size != count:
            raise ValueError("trend must be equal-length with residual data")
        values["trend"] = trend
    for role in ("center", "target", "baseline"):
        if role in values:
            values[role] = scalar(values[role], role)
    if "limits" in values:
        limits = numeric_1d(values["limits"], "limits")
        if limits.shape != (2,) or limits[0] >= limits[1]:
            raise ValueError("limits must contain increasing lower and upper values")
        values["limits"] = limits
    if "auc" in values:
        auc = numeric_1d(values["auc"], "auc")
        if auc.size not in {1, len(set(np.asarray(values.get("group", ["Series"]), dtype=str)))}:
            raise ValueError("auc must contain one value per diagnostic series")
        values["auc"] = auc
    if "envelope" in values:
        values["envelope"] = interval(values["envelope"], "envelope", count)
    if "uncertainty" in values:
        values["uncertainty"] = interval(values["uncertainty"], "uncertainty", count)
    for role in ("agreement_type", "reference_distribution", "importance_type", "metric_name"):
        if role in values:
            values[role] = text(values[role], role)
    optional_text(values, "xlabel")
    return values
