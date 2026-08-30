from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.colors import TwoSlopeNorm
from matplotlib.figure import Figure

from axiomfig.layout import add_panel_axes, create_panel_grid
from axiomfig.ornaments import apply_colorbar_contract
from axiomfig.style import (
    apply_axis_contract,
    apply_categorical_axis,
    semantic_colormap,
)

CORRELATION = np.array(
    [
        [1.00, 0.72, 0.48, 0.36],
        [0.72, 1.00, 0.63, 0.55],
        [0.48, 0.63, 1.00, 0.81],
        [0.36, 0.55, 0.81, 1.00],
    ]
)
CORRELATION_LABELS = ["Oxygen", "Ammonium", "Nitrate", "Phosphate"]


def _cmap(color_semantics: str) -> str:
    return semantic_colormap(color_semantics)


def add_matrix(
    axis: Axes,
    matrix: np.ndarray,
    labels: list[str] | None = None,
    *,
    row_labels: list[str] | None = None,
    column_labels: list[str] | None = None,
    annotate: bool,
    vmin: float,
    vmax: float,
    color_semantics: str,
    center: float | None = None,
    fmt: str = ".2f",
    annotation_values: np.ndarray | None = None,
) -> object:
    selected_rows = labels if row_labels is None else row_labels
    selected_columns = labels if column_labels is None else column_labels
    if selected_rows is None or selected_columns is None:
        raise ValueError("heatmap labels are required")
    norm = None
    if color_semantics == "diverging":
        if center is None:
            raise ValueError("diverging heatmap requires an explicit center")
        norm = TwoSlopeNorm(vmin=vmin, vcenter=center, vmax=vmax)
    image = axis.imshow(
        matrix,
        vmin=None if norm is not None else vmin,
        vmax=None if norm is not None else vmax,
        norm=norm,
        cmap=_cmap(color_semantics),
        aspect="auto",
        rasterized=True,
    )
    axis.set_xticks(
        range(len(selected_columns)),
        selected_columns,
        rotation=24,
        ha="right",
        rotation_mode="anchor",
    )
    axis.set_yticks(range(len(selected_rows)), selected_rows)
    apply_axis_contract(axis, surface="filled")
    apply_categorical_axis(axis, coordinate="x")
    apply_categorical_axis(axis, coordinate="y")
    if annotate:
        midpoint = (vmin + vmax) / 2.0
        for row in range(matrix.shape[0]):
            for column in range(matrix.shape[1]):
                color = "white" if matrix[row, column] < midpoint * 0.75 else "black"
                annotation = (
                    format(matrix[row, column], fmt)
                    if annotation_values is None
                    else str(annotation_values[row, column])
                )
                axis.text(
                    column,
                    row,
                    annotation,
                    ha="center",
                    va="center",
                    color=color,
                )
    return image


def add_heatmap(axis: Axes, *, annotate: bool = True) -> object:
    return add_matrix(
        axis,
        CORRELATION,
        CORRELATION_LABELS,
        annotate=annotate,
        vmin=0.0,
        vmax=1.0,
        color_semantics="sequential",
    )


def _heatmap_figure(
    matrix: np.ndarray,
    labels: list[str] | None = None,
    *,
    row_labels: list[str] | None = None,
    column_labels: list[str] | None = None,
    colorbar_label: str,
    vmin: float,
    vmax: float,
    color_semantics: str,
    center: float | None = None,
    fmt: str = ".2f",
    annotate: bool = True,
    annotation_values: np.ndarray | None = None,
) -> Figure:
    figure = plt.figure()
    layout = create_panel_grid(figure, 1, 1, panel_labels=False)
    axis, colorbar_axis = add_panel_axes(layout, 0, colorbar=True)
    assert colorbar_axis is not None
    image = add_matrix(
        axis,
        matrix,
        labels,
        row_labels=row_labels,
        column_labels=column_labels,
        annotate=annotate,
        vmin=vmin,
        vmax=vmax,
        color_semantics=color_semantics,
        center=center,
        fmt=fmt,
        annotation_values=annotation_values,
    )
    colorbar = figure.colorbar(image, cax=colorbar_axis, label=colorbar_label)
    apply_colorbar_contract(colorbar)
    return figure


def build_basic(
    matrix: object | None = None,
    row_labels: object | None = None,
    column_labels: object | None = None,
    color_semantics: object | None = None,
    center: object | None = None,
    annotations: object | None = None,
    colorbar_label: object | None = None,
) -> Figure:
    if matrix is None and row_labels is None and column_labels is None and color_semantics is None:
        selected = CORRELATION
        rows = CORRELATION_LABELS
        columns = CORRELATION_LABELS
        semantics = "sequential"
        limits = (0.0, 1.0)
    elif all(item is not None for item in (matrix, row_labels, column_labels, color_semantics)):
        selected = np.asarray(matrix, dtype=float)
        rows = [str(item) for item in row_labels]  # type: ignore[union-attr]
        columns = [str(item) for item in column_labels]  # type: ignore[union-attr]
        semantics = str(color_semantics)
        limits = (float(selected.min()), float(selected.max()))
    else:
        raise ValueError(
            "basic heatmap requires matrix, row_labels, column_labels, and color_semantics"
        )
    return _heatmap_figure(
        selected,
        row_labels=rows,
        column_labels=columns,
        colorbar_label="Correlation (-)" if colorbar_label is None else str(colorbar_label),
        vmin=limits[0],
        vmax=limits[1],
        color_semantics=semantics,
        center=None if center is None else float(center),
        annotate=annotations is not None,
        annotation_values=None if annotations is None else np.asarray(annotations, dtype=object),
    )


def build_correlation(
    matrix: object | None = None,
    labels: object | None = None,
    center: object | None = None,
    annotations: object | None = None,
    colorbar_label: object | None = None,
) -> Figure:
    if matrix is None and labels is None and center is None:
        selected_matrix = CORRELATION * np.array(
            [[1, 1, -1, -1], [1, 1, 1, -1], [-1, 1, 1, 1], [-1, -1, 1, 1]]
        )
        selected_labels = CORRELATION_LABELS
        selected_center = 0.0
    elif matrix is not None and labels is not None and center is not None:
        selected_matrix = np.asarray(matrix, dtype=float)
        selected_labels = [str(item) for item in labels]  # type: ignore[union-attr]
        if (
            selected_matrix.ndim != 2
            or selected_matrix.shape[0] != selected_matrix.shape[1]
            or selected_matrix.shape[0] != len(selected_labels)
        ):
            raise ValueError("correlation matrix must be square and match labels")
        selected_center = float(center)
        if float(selected_matrix.min()) < -1.0 or float(selected_matrix.max()) > 1.0:
            raise ValueError("correlation values must lie between -1 and 1")
        if not float(selected_matrix.min()) < selected_center < float(selected_matrix.max()):
            raise ValueError("correlation center must lie inside the data range")
    else:
        raise ValueError("correlation heatmap requires matrix, labels, and center together")
    return _heatmap_figure(
        selected_matrix,
        selected_labels,
        colorbar_label="Pearson r" if colorbar_label is None else str(colorbar_label),
        vmin=-1.0,
        vmax=1.0,
        color_semantics="diverging",
        center=selected_center,
        annotation_values=None if annotations is None else np.asarray(annotations, dtype=object),
    )


def build_clustered(
    matrix: object | None = None,
    row_labels: object | None = None,
    column_labels: object | None = None,
    row_order: object | None = None,
    column_order: object | None = None,
    color_semantics: object | None = None,
    center: object | None = None,
    annotations: object | None = None,
    colorbar_label: object | None = None,
) -> Figure:
    if all(
        item is None
        for item in (matrix, row_labels, column_labels, row_order, column_order, color_semantics)
    ):
        rows = np.array([2, 3, 1, 0])
        columns = rows
        source = CORRELATION
        source_rows = CORRELATION_LABELS
        source_columns = CORRELATION_LABELS
        semantics = "sequential"
    elif all(
        item is not None
        for item in (matrix, row_labels, column_labels, row_order, column_order, color_semantics)
    ):
        rows = np.asarray(row_order, dtype=int)
        columns = np.asarray(column_order, dtype=int)
        source = np.asarray(matrix, dtype=float)
        source_rows = [str(item) for item in row_labels]  # type: ignore[union-attr]
        source_columns = [str(item) for item in column_labels]  # type: ignore[union-attr]
        semantics = str(color_semantics)
    else:
        raise ValueError(
            "clustered heatmap requires matrix labels, row/column order, and semantics"
        )
    selected = source[np.ix_(rows, columns)]
    selected_rows = [source_rows[index] for index in rows]
    selected_columns = [source_columns[index] for index in columns]
    selected_annotations = (
        None
        if annotations is None
        else np.asarray(annotations, dtype=object)[np.ix_(rows, columns)]
    )
    figure = _heatmap_figure(
        selected,
        row_labels=selected_rows,
        column_labels=selected_columns,
        colorbar_label=("Preordered similarity" if colorbar_label is None else str(colorbar_label)),
        vmin=float(source.min()),
        vmax=float(source.max()),
        color_semantics=semantics,
        center=None if center is None else float(center),
        annotation_values=selected_annotations,
    )
    figure.axes[0].set_title("Deterministic cluster order")
    return figure


def build_confusion_matrix(
    matrix: object | None = None,
    class_labels: object | None = None,
    annotations: object | None = None,
    colorbar_label: object | None = None,
) -> Figure:
    if matrix is None and class_labels is None:
        selected = np.array([[48, 4, 1], [5, 41, 3], [0, 6, 45]])
        labels = ["Low", "Medium", "High"]
    elif matrix is not None and class_labels is not None:
        selected = np.asarray(matrix, dtype=float)
        labels = [str(item) for item in class_labels]  # type: ignore[union-attr]
    else:
        raise ValueError("confusion_matrix requires matrix and class_labels together")
    return _heatmap_figure(
        selected,
        labels,
        colorbar_label="Count" if colorbar_label is None else str(colorbar_label),
        vmin=0.0,
        vmax=max(float(selected.max()), 1.0),
        color_semantics="sequential",
        fmt=".0f",
        annotation_values=None if annotations is None else np.asarray(annotations, dtype=object),
    )


def build_annotated(
    matrix: object | None = None,
    row_labels: object | None = None,
    column_labels: object | None = None,
    color_semantics: object | None = None,
    center: object | None = None,
    annotations: object | None = None,
    colorbar_label: object | None = None,
    annotation_format: object | None = None,
) -> Figure:
    if all(
        item is None for item in (matrix, row_labels, column_labels, color_semantics, annotations)
    ):
        selected = np.array(
            [
                [0.88, 0.64, 0.42, 0.31],
                [0.59, 0.81, 0.57, 0.46],
                [0.36, 0.53, 0.76, 0.69],
                [0.24, 0.39, 0.62, 0.91],
            ]
        )
        rows = columns = ["R1", "R2", "R3", "R4"]
        annotation_values = None
        semantics = "sequential"
    elif all(
        item is not None
        for item in (matrix, row_labels, column_labels, color_semantics, annotations)
    ):
        selected = np.asarray(matrix, dtype=float)
        rows = [str(item) for item in row_labels]  # type: ignore[union-attr]
        columns = [str(item) for item in column_labels]  # type: ignore[union-attr]
        annotation_values = np.asarray(annotations, dtype=object)
        semantics = str(color_semantics)
    else:
        raise ValueError("annotated heatmap requires matrix, labels, annotations, and semantics")
    return _heatmap_figure(
        selected,
        row_labels=rows,
        column_labels=columns,
        colorbar_label=(
            "Normalized response (-)" if colorbar_label is None else str(colorbar_label)
        ),
        vmin=float(selected.min()),
        vmax=float(selected.max()),
        color_semantics=semantics,
        center=None if center is None else float(center),
        annotate=True,
        fmt=".2f" if annotation_format is None else str(annotation_format),
        annotation_values=annotation_values,
    )


BUILDERS = {
    "basic": build_basic,
    "correlation": build_correlation,
    "clustered": build_clustered,
    "confusion_matrix": build_confusion_matrix,
    "annotated": build_annotated,
}
