from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.lines import Line2D

from axiomfig.template_helpers import (
    add_colorbar_panel_axes,
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


def _add_matrix(
    axis: Axes,
    matrix: np.ndarray,
    labels: list[str],
    *,
    annotate: bool,
    vmin: float,
    vmax: float,
    fmt: str = ".2f",
) -> object:
    image = axis.imshow(
        matrix,
        vmin=vmin,
        vmax=vmax,
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
    return _add_matrix(
        axis,
        CORRELATION,
        CORRELATION_LABELS,
        annotate=annotate,
        vmin=0.0,
        vmax=1.0,
    )


def _heatmap_figure(
    matrix: np.ndarray,
    labels: list[str],
    *,
    colorbar_label: str,
    vmin: float,
    vmax: float,
    fmt: str = ".2f",
) -> Figure:
    figure = plt.figure()
    outer = figure.add_gridspec(1, 1)[0, 0]
    axis, colorbar_axis = add_colorbar_panel_axes(figure, outer)
    image = _add_matrix(
        axis,
        matrix,
        labels,
        annotate=True,
        vmin=vmin,
        vmax=vmax,
        fmt=fmt,
    )
    colorbar = figure.colorbar(image, cax=colorbar_axis, label=colorbar_label)
    apply_colorbar_contract(colorbar)
    return figure


def build_heatmap() -> Figure:
    return _heatmap_figure(
        CORRELATION,
        CORRELATION_LABELS,
        colorbar_label="Correlation (-)",
        vmin=0.0,
        vmax=1.0,
    )


def build_correlation_heatmap() -> Figure:
    matrix = CORRELATION * np.array([[1, 1, -1, -1], [1, 1, 1, -1], [-1, 1, 1, 1], [-1, -1, 1, 1]])
    return _heatmap_figure(
        matrix,
        CORRELATION_LABELS,
        colorbar_label="Pearson r",
        vmin=-1.0,
        vmax=1.0,
    )


def build_clustered_heatmap() -> Figure:
    order = np.array([2, 3, 1, 0])
    matrix = CORRELATION[np.ix_(order, order)]
    labels = [CORRELATION_LABELS[index] for index in order]
    figure = _heatmap_figure(
        matrix,
        labels,
        colorbar_label="Preordered similarity",
        vmin=0.0,
        vmax=1.0,
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
        fmt=".0f",
    )


def build_mantel_test() -> Figure:
    figure = plt.figure()
    grid = figure.add_gridspec(1, 2, width_ratios=(1.1, 0.9), wspace=0.38)
    matrix_axis = figure.add_subplot(grid[0, 0])
    link_axis = figure.add_subplot(grid[0, 1])
    _add_matrix(
        matrix_axis,
        CORRELATION[:3, :3],
        ["COD", "TN", "TP"],
        annotate=True,
        vmin=0.0,
        vmax=1.0,
    )
    matrix_axis.set_title("Environmental correlation")

    left = [(0.12, 0.78, "COD"), (0.12, 0.50, "TN"), (0.12, 0.22, "TP")]
    right = [(0.88, 0.70, "Community"), (0.88, 0.30, "Function")]
    for x, y, label in left + right:
        link_axis.scatter([x], [y], s=42, facecolor="white", edgecolor="black", linewidth=0.6)
        link_axis.text(x, y + 0.08, label, ha="center", va="bottom")
    links = (
        (left[0], right[0], 0.61, True),
        (left[1], right[0], 0.43, False),
        (left[1], right[1], 0.68, True),
        (left[2], right[1], 0.35, False),
    )
    colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]
    for index, (source, target, correlation, significant) in enumerate(links):
        link_axis.plot(
            [source[0], target[0]],
            [source[1], target[1]],
            color=colors[index % 2],
            linewidth=0.6 + 2.0 * correlation,
            linestyle="-" if significant else ":",
        )
        midpoint = ((source[0] + target[0]) / 2, (source[1] + target[1]) / 2)
        link_axis.text(*midpoint, f"r={correlation:.2f}", ha="center", va="bottom")
    link_axis.legend(
        handles=[
            Line2D([0], [0], color=colors[0], linewidth=1.8, label="p < 0.05"),
            Line2D(
                [0],
                [0],
                color=colors[1],
                linewidth=1.4,
                linestyle=":",
                label="not significant",
            ),
        ],
        loc="lower center",
        frameon=False,
        ncol=1,
    )
    link_axis.set(xlim=(0.0, 1.0), ylim=(0.0, 1.0))
    link_axis.set_axis_off()
    return figure
