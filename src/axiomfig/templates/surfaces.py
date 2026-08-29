from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from mpl_toolkits.axes_grid1.inset_locator import inset_axes

from axiomfig.config import load_contracts
from axiomfig.template_helpers import (
    apply_axis_contract,
    apply_categorical_axis,
    apply_colorbar_contract,
)


def add_panel_colorbar_axis(axis: Axes) -> Axes:
    layout = load_contracts().style["layout"]["multi_panel"]
    width = f"{100.0 * float(layout['colorbar_width_ratio']):g}%"
    gap = float(layout["colorbar_gap"])
    return inset_axes(
        axis,
        width=width,
        height="100%",
        loc="lower left",
        bbox_to_anchor=(1.0 + gap, 0.0, 1.0, 1.0),
        bbox_transform=axis.transAxes,
        borderpad=0.0,
    )


def add_heatmap(axis: Axes, *, annotate: bool = True) -> object:
    matrix = np.array(
        [
            [1.00, 0.72, 0.48, 0.36],
            [0.72, 1.00, 0.63, 0.55],
            [0.48, 0.63, 1.00, 0.81],
            [0.36, 0.55, 0.81, 1.00],
        ]
    )
    image = axis.imshow(matrix, vmin=0.0, vmax=1.0, aspect="auto", rasterized=True)
    labels = ["Oxygen", "Ammonium", "Nitrate", "Phosphate"]
    axis.set_xticks(range(4), labels, rotation=24, ha="right", rotation_mode="anchor")
    axis.set_yticks(range(4), labels)
    apply_axis_contract(axis, surface="filled")
    apply_categorical_axis(axis, coordinate="x")
    apply_categorical_axis(axis, coordinate="y")
    if annotate:
        for row in range(4):
            for column in range(4):
                axis.text(column, row, f"{matrix[row, column]:.2f}", ha="center", va="center")
    return image


def build_heatmap() -> Figure:
    figure, axis = plt.subplots()
    image = add_heatmap(axis)
    colorbar_axis = add_panel_colorbar_axis(axis)
    colorbar = figure.colorbar(image, cax=colorbar_axis, label="Correlation (-)")
    apply_colorbar_contract(colorbar)
    return figure
