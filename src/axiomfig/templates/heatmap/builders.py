from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.colors import TwoSlopeNorm
from matplotlib.figure import Figure

from axiomfig.colors import semantic_colormap
from axiomfig.layout import add_panel_axes, create_panel_grid
from axiomfig.template_helpers import (
    apply_axis_contract,
    apply_categorical_axis,
    apply_colorbar_contract,
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
    labels: list[str],
    *,
    annotate: bool,
    vmin: float,
    vmax: float,
    color_semantics: str,
    center: float | None = None,
    fmt: str = ".2f",
) -> object:
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
    axis.set_xticks(range(len(labels)), labels, rotation=24, ha="right", rotation_mode="anchor")
    axis.set_yticks(range(len(labels)), labels)
    apply_axis_contract(axis, surface="filled")
    apply_categorical_axis(axis, coordinate="x")
    apply_categorical_axis(axis, coordinate="y")
    if annotate:
        midpoint = (vmin + vmax) / 2.0
        for row in range(matrix.shape[0]):
            for column in range(matrix.shape[1]):
                color = "white" if matrix[row, column] < midpoint * 0.75 else "black"
                axis.text(
                    column,
                    row,
                    format(matrix[row, column], fmt),
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
    labels: list[str],
    *,
    colorbar_label: str,
    vmin: float,
    vmax: float,
    color_semantics: str,
    center: float | None = None,
    fmt: str = ".2f",
    annotate: bool = True,
) -> Figure:
    figure = plt.figure()
    layout = create_panel_grid(figure, 1, 1, panel_labels=False)
    axis, colorbar_axis = add_panel_axes(layout, 0, colorbar=True)
    assert colorbar_axis is not None
    image = add_matrix(
        axis,
        matrix,
        labels,
        annotate=annotate,
        vmin=vmin,
        vmax=vmax,
        color_semantics=color_semantics,
        center=center,
        fmt=fmt,
    )
    colorbar = figure.colorbar(image, cax=colorbar_axis, label=colorbar_label)
    apply_colorbar_contract(colorbar)
    return figure


def build_basic() -> Figure:
    return _heatmap_figure(
        CORRELATION,
        CORRELATION_LABELS,
        colorbar_label="Correlation (-)",
        vmin=0.0,
        vmax=1.0,
        color_semantics="sequential",
        annotate=False,
    )


def build_correlation() -> Figure:
    matrix = CORRELATION * np.array([[1, 1, -1, -1], [1, 1, 1, -1], [-1, 1, 1, 1], [-1, -1, 1, 1]])
    return _heatmap_figure(
        matrix,
        CORRELATION_LABELS,
        colorbar_label="Pearson r",
        vmin=-1.0,
        vmax=1.0,
        color_semantics="diverging",
        center=0.0,
    )


def build_clustered() -> Figure:
    order = np.array([2, 3, 1, 0])
    matrix = CORRELATION[np.ix_(order, order)]
    labels = [CORRELATION_LABELS[index] for index in order]
    figure = _heatmap_figure(
        matrix,
        labels,
        colorbar_label="Preordered similarity",
        vmin=0.0,
        vmax=1.0,
        color_semantics="sequential",
    )
    figure.axes[0].set_title("Deterministic cluster order")
    return figure


def build_confusion_matrix() -> Figure:
    matrix = np.array([[48, 4, 1], [5, 41, 3], [0, 6, 45]])
    return _heatmap_figure(
        matrix,
        ["Low", "Medium", "High"],
        colorbar_label="Count",
        vmin=0.0,
        vmax=50.0,
        color_semantics="sequential",
        fmt=".0f",
    )


def build_annotated() -> Figure:
    matrix = np.array(
        [
            [0.88, 0.64, 0.42, 0.31],
            [0.59, 0.81, 0.57, 0.46],
            [0.36, 0.53, 0.76, 0.69],
            [0.24, 0.39, 0.62, 0.91],
        ]
    )
    return _heatmap_figure(
        matrix,
        ["R1", "R2", "R3", "R4"],
        colorbar_label="Normalized response (-)",
        vmin=0.0,
        vmax=1.0,
        color_semantics="sequential",
        annotate=True,
    )


BUILDERS = {
    "basic": build_basic,
    "correlation": build_correlation,
    "clustered": build_clustered,
    "confusion_matrix": build_confusion_matrix,
    "annotated": build_annotated,
}
