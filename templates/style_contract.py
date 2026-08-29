"""Four-panel acceptance sample for the deterministic visual contract."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure

from axiomfig.template_helpers import (
    add_bar_value_labels,
    add_panel_labels,
    apply_axis_contract,
    apply_scatter_contract,
    place_legend_above,
)


def build_style_contract() -> Figure:
    rng = np.random.default_rng(109)
    figure, axes_grid = plt.subplots(2, 2)
    line_axis, bar_axis, scatter_axis, heatmap_axis = axes_grid.flat

    time = np.linspace(0.0, 12.0, 61)
    line_axis.plot(time, 1.0 - np.exp(-time / 3.2), label="Open line")
    line_axis.plot(time, 0.92 * (1.0 - np.exp(-time / 4.1)), label="Reference")
    line_axis.set(xlabel="Time (d)", ylabel="Response (-)")
    apply_axis_contract(line_axis)
    place_legend_above(line_axis)

    positions = np.arange(3)
    width = 0.34
    mechanistic = bar_axis.bar(
        positions - width / 2,
        [0.72, 0.67, 0.61],
        width,
        label="Mechanistic",
    )
    hybrid = bar_axis.bar(
        positions + width / 2,
        [0.84, 0.76, 0.71],
        width,
        label="Hybrid",
    )
    bar_axis.set_xticks(positions, ["COD", "TN", "TP"])
    bar_axis.set(ylabel="$R^2$ (-)", ylim=(0.0, 1.0))
    apply_axis_contract(bar_axis, surface="filled")
    add_bar_value_labels(bar_axis, [mechanistic, hybrid])
    place_legend_above(bar_axis)

    observed = np.linspace(2.0, 28.0, 36)
    predicted = observed + rng.normal(0.0, 1.35, observed.size)
    apply_scatter_contract(scatter_axis.scatter(observed, predicted, s=18))
    scatter_axis.plot([0.0, 30.0], [0.0, 30.0], linestyle="--", label="1:1")
    scatter_axis.set(
        xlim=(0.0, 30.0),
        ylim=(0.0, 30.0),
        xlabel="Observed (mg L$^{-1}$)",
        ylabel="Predicted (mg L$^{-1}$)",
    )
    apply_axis_contract(scatter_axis)

    matrix = np.array(
        [
            [1.00, 0.72, 0.48],
            [0.72, 1.00, 0.63],
            [0.48, 0.63, 1.00],
        ]
    )
    image = heatmap_axis.imshow(
        matrix,
        vmin=0.0,
        vmax=1.0,
        aspect="equal",
        rasterized=True,
    )
    heatmap_axis.set_xticks(range(3), ["DO", "硝化效率", "硝化の効率"], rotation=18)
    heatmap_axis.set_yticks(range(3), ["DO", "硝化效率", "硝化の効率"])
    apply_axis_contract(heatmap_axis, surface="filled")
    for row in range(3):
        for column in range(3):
            color = "white" if matrix[row, column] < 0.55 else "black"
            heatmap_axis.text(
                column,
                row,
                f"{matrix[row, column]:.2f}",
                ha="center",
                va="center",
                color=color,
            )
    colorbar = figure.colorbar(image, ax=heatmap_axis, pad=0.04)
    colorbar.set_label("Correlation (-)")

    add_panel_labels(axes_grid.flat)
    return figure


if __name__ == "__main__":
    build_style_contract().show()
