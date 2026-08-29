from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure

from axiomfig.config import load_contracts
from axiomfig.template_helpers import (
    apply_axis_contract,
    apply_categorical_axis,
    apply_colorbar_contract,
    apply_single_panel_layout,
)


def build_heatmap() -> Figure:
    matrix = np.array([[1.00, 0.72, 0.48], [0.72, 1.00, 0.63], [0.48, 0.63, 1.00]])
    figure = plt.figure()
    apply_single_panel_layout(figure)
    layout = load_contracts().style["layout"]["single_panel"]
    grid = figure.add_gridspec(
        1,
        2,
        width_ratios=(1.0, float(layout["colorbar_width_ratio"])),
        wspace=float(layout["colorbar_wspace"]),
    )
    axis = figure.add_subplot(grid[0, 0])
    colorbar_axis = figure.add_subplot(grid[0, 1])
    image = axis.imshow(matrix, vmin=0.0, vmax=1.0, aspect="auto", rasterized=True)
    labels = ["DO", "Ammonium", "Nitrate"]
    axis.set_xticks(range(3), labels)
    axis.set_yticks(range(3), labels)
    apply_axis_contract(axis, surface="filled")
    apply_categorical_axis(axis, coordinate="x")
    apply_categorical_axis(axis, coordinate="y")
    for row in range(3):
        for column in range(3):
            axis.text(column, row, f"{matrix[row, column]:.2f}", ha="center", va="center")
    colorbar = figure.colorbar(image, cax=colorbar_axis)
    colorbar.set_label("Correlation (-)")
    apply_colorbar_contract(colorbar)
    return figure
