from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure

from axiomfig.config import load_contracts
from axiomfig.template_helpers import (
    add_bar_value_labels,
    add_panel_labels,
    apply_axis_contract,
    apply_categorical_axis,
    apply_colorbar_contract,
    apply_nice_linear_axis,
    apply_scatter_contract,
    place_legend_above,
)


def build_multi_panel() -> Figure:
    rng = np.random.default_rng(109)
    figure = plt.figure()
    layout = load_contracts().style["layout"]["multi_panel"]
    figure.subplots_adjust(**{key: float(value) for key, value in layout["margins"].items()})
    grid = figure.add_gridspec(
        2,
        3,
        width_ratios=tuple(float(value) for value in layout["width_ratios"]),
        wspace=float(layout["wspace"]),
        hspace=float(layout["hspace"]),
    )
    axes = [
        figure.add_subplot(grid[0, 0]),
        figure.add_subplot(grid[0, 1]),
        figure.add_subplot(grid[1, 0]),
        figure.add_subplot(grid[1, 1]),
    ]
    colorbar_axis = figure.add_subplot(grid[:, 2])

    x = np.linspace(0.0, 12.0, 61)
    axes[0].plot(x, 1.0 - np.exp(-x / 3.2), label="Hybrid")
    axes[0].plot(x, 0.9 * (1.0 - np.exp(-x / 4.0)), label="Mechanistic")
    axes[0].set(xlabel="Time (d)", ylabel="Response (-)")
    apply_axis_contract(axes[0], surface="open")
    apply_nice_linear_axis(axes[0], 0.0, 12.0, coordinate="x")
    apply_nice_linear_axis(axes[0], 0.0, 1.0, coordinate="y")

    positions = np.arange(3)
    bars = axes[1].bar(positions, [0.84, 0.76, 0.71])
    axes[1].set_xticks(positions, ["COD", "TN", "TP"])
    axes[1].set(ylabel="Score (-)", ylim=(0.0, 1.0))
    apply_axis_contract(axes[1], surface="filled")
    apply_categorical_axis(axes[1], coordinate="x")
    apply_nice_linear_axis(axes[1], 0.0, 1.0, coordinate="y")
    add_bar_value_labels(axes[1], [bars])

    observed = np.linspace(2.0, 28.0, 36)
    apply_scatter_contract(
        axes[2].scatter(observed, observed + rng.normal(0.0, 1.3, observed.size))
    )
    axes[2].plot([0, 30], [0, 30], linestyle="--")
    axes[2].set(xlabel="Observed", ylabel="Predicted")
    apply_axis_contract(axes[2], surface="open")
    apply_nice_linear_axis(axes[2], 0.0, 30.0, coordinate="x")
    apply_nice_linear_axis(axes[2], 0.0, 30.0, coordinate="y")

    matrix = np.array([[1.0, 0.72, 0.48], [0.72, 1.0, 0.63], [0.48, 0.63, 1.0]])
    image = axes[3].imshow(matrix, vmin=0.0, vmax=1.0, aspect="auto", rasterized=True)
    axes[3].set_xticks(range(3), ["DO", "NH4", "NO3"])
    axes[3].set_yticks(range(3), ["DO", "NH4", "NO3"])
    apply_axis_contract(axes[3], surface="filled")
    apply_categorical_axis(axes[3], coordinate="x")
    apply_categorical_axis(axes[3], coordinate="y")
    colorbar = figure.colorbar(image, cax=colorbar_axis, label="Correlation (-)")
    apply_colorbar_contract(colorbar)

    add_panel_labels(axes)
    place_legend_above(axes[0])
    return figure
