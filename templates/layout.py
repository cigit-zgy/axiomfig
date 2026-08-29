"""Two-panel and four-panel mixed-plot layout grammars."""

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


def build_two_panel() -> Figure:
    rng = np.random.default_rng(71)
    x = np.linspace(0.0, 8.0, 50)
    figure, axes = plt.subplots(1, 2)
    axes[0].plot(x, 1.0 - np.exp(-0.5 * x), label="Estimate")
    axes[0].set(xlabel="Time (d)", ylabel="Response (-)")
    observed = np.linspace(2.0, 25.0, 32)
    apply_scatter_contract(
        axes[1].scatter(observed, observed + rng.normal(0.0, 1.2, observed.size), s=16)
    )
    axes[1].plot([0, 28], [0, 28], color="0.25", linestyle="--")
    axes[1].set(xlabel="Observed", ylabel="Predicted")
    for axis in axes:
        apply_axis_contract(axis)
    place_legend_above(axes[0])
    add_panel_labels(axes)
    return figure


def build_four_panel() -> Figure:
    rng = np.random.default_rng(83)
    figure, axes_grid = plt.subplots(2, 2)
    axes = list(axes_grid.flat)

    x = np.linspace(0.0, 10.0, 61)
    mean = 1.0 - np.exp(-0.38 * x)
    line = axes[0].plot(x, mean, label="Mean")[0]
    axes[0].fill_between(
        x, mean - 0.045, mean + 0.045, color=line.get_color(), alpha=0.2, linewidth=0
    )
    axes[0].set(xlabel="Time (d)", ylabel="Response (-)")
    place_legend_above(axes[0])

    observed = np.linspace(2.0, 26.0, 34)
    predicted = observed + rng.normal(0.0, 1.35, observed.size)
    apply_scatter_contract(axes[1].scatter(observed, predicted, s=15))
    axes[1].plot([0, 28], [0, 28], color="0.25", linestyle="--")
    axes[1].set(xlim=(0, 28), ylim=(0, 28), xlabel="Observed", ylabel="Predicted")

    positions = np.arange(3)
    width = 0.35
    asm_bars = axes[2].bar(positions - width / 2, [0.72, 0.67, 0.61], width, label="ASM")
    hybrid_bars = axes[2].bar(positions + width / 2, [0.84, 0.76, 0.71], width, label="Hybrid")
    axes[2].set_xticks(positions, ["COD", "TN", "TP"])
    axes[2].set(ylabel="$R^2$ (-)", ylim=(0.0, 1.0))
    apply_axis_contract(axes[2], surface="filled")
    add_bar_value_labels(axes[2], [asm_bars, hybrid_bars])
    place_legend_above(axes[2])

    distributions = [rng.normal(value, 0.075, 70) for value in (0.62, 0.74, 0.82)]
    parts = axes[3].violinplot(distributions, showmedians=True)
    colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]
    for body, color in zip(parts["bodies"], colors, strict=False):
        body.set_facecolor(color)
        body.set_alpha(0.72)
    axes[3].set_xticks([1, 2, 3], ["ASM", "NODE", "Hybrid"])
    axes[3].set(ylabel="Score (-)")

    for axis in (axes[0], axes[1]):
        apply_axis_contract(axis)
    apply_axis_contract(axes[3], surface="filled")

    add_panel_labels(axes)
    return figure


if __name__ == "__main__":
    build_four_panel().show()
