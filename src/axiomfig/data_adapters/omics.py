from __future__ import annotations

import numpy as np

from ._shared import equal_length, labels_1d, numeric_1d, optional_text, scalar


def adapt(variant: str, supplied: dict[str, object]) -> dict[str, object]:
    values = dict(supplied)
    if variant == "volcano":
        arrays = {
            "effect_size": numeric_1d(values["effect_size"], "effect_size", minimum=2),
            "adjusted_p_value": numeric_1d(
                values["adjusted_p_value"], "adjusted_p_value", minimum=2
            ),
        }
        equal_length(arrays, minimum=2)
        if np.any(arrays["adjusted_p_value"] <= 0) or np.any(arrays["adjusted_p_value"] > 1):
            raise ValueError("adjusted_p_value must lie in (0, 1]")
        values.update(arrays)
        for role in ("significance_threshold", "effect_threshold"):
            values[role] = scalar(values[role], role)
        if not 0 < values["significance_threshold"] < 1 or values["effect_threshold"] <= 0:
            raise ValueError("volcano thresholds must be scientifically valid")
        if "feature_label" in values:
            labels = labels_1d(values["feature_label"], "feature_label")
            if labels.size != arrays["effect_size"].size:
                raise ValueError("feature_label must match effect_size")
            values["feature_label"] = labels
    else:
        arrays = {
            "term": labels_1d(values["term"], "term"),
            "enrichment": numeric_1d(values["enrichment"], "enrichment"),
            "significance": numeric_1d(values["significance"], "significance"),
            "size": numeric_1d(values["size"], "size"),
        }
        equal_length(arrays)
        if np.any(arrays["significance"] <= 0) or np.any(arrays["significance"] > 1):
            raise ValueError("enrichment significance must lie in (0, 1]")
        if np.any(arrays["size"] <= 0):
            raise ValueError("enrichment size must be positive")
        values.update(arrays)
    optional_text(values, "colorbar_label", "size_label")
    return values
