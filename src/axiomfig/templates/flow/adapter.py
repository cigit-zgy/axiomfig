from __future__ import annotations

import numpy as np

from axiomfig.templates._adapter import equal_length, labels_1d, numeric_1d


def adapt(variant: str, supplied: dict[str, object]) -> dict[str, object]:
    del variant
    values = dict(supplied)
    arrays: dict[str, np.ndarray] = {
        "source": labels_1d(values["source"], "source"),
        "target": labels_1d(values["target"], "target"),
        "value": numeric_1d(values["value"], "value"),
    }
    equal_length(arrays)
    if np.any(arrays["value"] <= 0):
        raise ValueError("Sankey value must be positive")
    values.update(arrays)
    if "node_labels" in values:
        values["node_labels"] = labels_1d(values["node_labels"], "node_labels")
    if "flow_labels" in values:
        labels = labels_1d(values["flow_labels"], "flow_labels")
        if labels.size != arrays["value"].size:
            raise ValueError("flow_labels must match flow records")
        values["flow_labels"] = labels
    return values
