from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure

from axiomfig.template_helpers import (
    add_bar_value_labels,
    add_panel_labels,
    apply_axis_contract,
    apply_categorical_axis,
    apply_colorbar_contract,
    apply_nice_linear_axis,
    apply_scatter_contract,
    confidence_interval_kwargs,
    place_legend_above,
)
from axiomfig.templates.surfaces import add_heatmap, add_panel_colorbar_axis


def build_multi_panel() -> Figure:
    rng = np.random.default_rng(109)
    figure, grid = plt.subplots(2, 2, squeeze=False)
    axes = list(grid.flat)

    x = np.linspace(0.0, 12.0, 61)
    mean = 1.0 - np.exp(-x / 3.2)
    spread = 0.045 + 0.025 * np.exp(-x / 4.0)
    color = plt.rcParams["axes.prop_cycle"].by_key()["color"][0]
    axes[0].fill_between(
        x,
        mean - spread,
        mean + spread,
        color=color,
        **confidence_interval_kwargs(),
    )
    axes[0].plot(x, mean, label="Hybrid model")
    axes[0].plot(x, 0.9 * (1.0 - np.exp(-x / 4.0)), label="Mechanistic model")
    axes[0].set(xlabel="Time (d)", ylabel="Response (-)")
    apply_axis_contract(axes[0], surface="open")
    apply_nice_linear_axis(axes[0], 0.0, 12.0, coordinate="x")
    apply_nice_linear_axis(axes[0], 0.0, 1.0, coordinate="y")

    positions = np.arange(3)
    width = 0.34
    first = axes[1].bar(
        positions - width / 2,
        [0.72, 0.67, 0.61],
        width,
        label="Mechanistic",
    )
    second = axes[1].bar(
        positions + width / 2,
        [0.84, 0.76, 0.71],
        width,
        label="Hybrid",
    )
    axes[1].set_xticks(positions, ["COD", "Nitrogen", "Phosphorus"])
    axes[1].set(ylabel="Validation score (-)")
    apply_axis_contract(axes[1], surface="open")
    apply_categorical_axis(axes[1], coordinate="x")
    apply_nice_linear_axis(axes[1], 0.0, 1.0, coordinate="y")
    add_bar_value_labels(axes[1], [first, second])

    observed = np.linspace(2.0, 28.0, 36)
    apply_scatter_contract(
        axes[2].scatter(observed, observed + rng.normal(0.0, 1.3, observed.size))
    )
    axes[2].plot([0, 30], [0, 30], linestyle="--")
    axes[2].set(xlabel="Observed concentration", ylabel="Predicted concentration")
    apply_axis_contract(axes[2], surface="open")
    apply_nice_linear_axis(axes[2], 0.0, 30.0, coordinate="x")
    apply_nice_linear_axis(axes[2], 0.0, 30.0, coordinate="y")

    image = add_heatmap(axes[3], annotate=False)
    colorbar_axis = add_panel_colorbar_axis(axes[3])
    colorbar = figure.colorbar(image, cax=colorbar_axis, label="Correlation (-)")
    apply_colorbar_contract(colorbar)

    add_panel_labels(axes)
    place_legend_above(axes[0])
    place_legend_above(axes[1])
    return figure
