from __future__ import annotations

import numpy as np

from axiomfig.templates._adapter import (
    labels_1d,
    numeric_matrix,
    object_matrix,
    optional_text,
    scalar,
    text,
)


def _labels(value: object, name: str, expected: int) -> np.ndarray:
    selected = labels_1d(value, name)
    if selected.size != expected:
        raise ValueError(f"{name} must match matrix shape")
    return selected


def _order(value: object, name: str, expected: int) -> np.ndarray:
    selected = np.asarray(value, dtype=int)
    if (
        selected.ndim != 1
        or selected.size != expected
        or set(selected.tolist()) != set(range(expected))
    ):
        raise ValueError(f"{name} must be a complete zero-based permutation")
    return selected


def adapt(variant: str, supplied: dict[str, object]) -> dict[str, object]:
    values = dict(supplied)
    matrix = numeric_matrix(values["matrix"], "matrix")
    values["matrix"] = matrix
    if variant in {"correlation", "confusion_matrix"}:
        if matrix.shape[0] != matrix.shape[1]:
            raise ValueError(f"{variant} matrix must be square")
        role = "labels" if variant == "correlation" else "class_labels"
        values[role] = _labels(values[role], role, matrix.shape[0])
    else:
        values["row_labels"] = _labels(values["row_labels"], "row_labels", matrix.shape[0])
        values["column_labels"] = _labels(values["column_labels"], "column_labels", matrix.shape[1])
    if variant == "correlation":
        if np.any(matrix < -1.0) or np.any(matrix > 1.0):
            raise ValueError("correlation values must lie between -1 and 1")
        values["center"] = scalar(values["center"], "center")
    if variant == "clustered":
        values["row_order"] = _order(values["row_order"], "row_order", matrix.shape[0])
        values["column_order"] = _order(values["column_order"], "column_order", matrix.shape[1])
    if "annotations" in values:
        annotations = object_matrix(values["annotations"], "annotations")
        if annotations.shape != matrix.shape:
            raise ValueError("annotations must match matrix shape")
        values["annotations"] = annotations
    if "color_semantics" in values:
        semantics = text(values["color_semantics"], "color_semantics")
        if semantics not in {"sequential", "diverging", "qualitative", "cyclic"}:
            raise ValueError("unknown color_semantics")
        if semantics == "diverging":
            if "center" not in values:
                raise ValueError("diverging heatmap requires an explicit center")
            values["center"] = scalar(values["center"], "center")
        elif "center" in values:
            raise ValueError("center is only valid for diverging heatmap semantics")
    optional_text(values, "colorbar_label", "annotation_format")
    return values
