from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure

from axiomfig.config import load_contracts
from axiomfig.template_helpers import (
    add_bar_value_labels,
    apply_axis_contract,
    apply_categorical_axis,
    apply_nice_linear_axis,
    apply_single_panel_layout,
    apply_violin_contract,
    place_legend_above,
)


def build_bar() -> Figure:
    labels = ["COD", "TN", "TP"]
    positions = np.arange(len(labels))
    width = 0.34
    figure, axis = plt.subplots()
    apply_single_panel_layout(figure)
    first = axis.bar(positions - width / 2, [0.72, 0.67, 0.61], width, label="Mechanistic")
    second = axis.bar(positions + width / 2, [0.84, 0.76, 0.71], width, label="Hybrid")
    axis.set_xticks(positions, labels)
    axis.set(ylabel="Validation score (-)", ylim=(0.0, 1.0))
    apply_axis_contract(axis, surface="filled")
    apply_categorical_axis(axis, coordinate="x")
    apply_nice_linear_axis(axis, 0.0, 1.0, coordinate="y")
    add_bar_value_labels(axis, [first, second])
    place_legend_above(axis)
    return figure


def build_violin() -> Figure:
    rng = np.random.default_rng(47)
    samples = [rng.normal(mean, 0.075, 80) for mean in (0.62, 0.74, 0.82)]
    figure, axis = plt.subplots()
    apply_single_panel_layout(figure)
    parts = axis.violinplot(samples, showmedians=True, showextrema=True)
    colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]
    for body, color in zip(parts["bodies"], colors, strict=False):
        body.set_facecolor(color)
        body.set_alpha(0.72)
    apply_violin_contract(parts)
    axis.set_xticks([1, 2, 3], ["ASM", "Neural ODE", "Hybrid ODE"])
    axis.set(ylabel="Normalized score (-)")
    apply_axis_contract(axis, surface="filled")
    apply_categorical_axis(axis, coordinate="x")
    values = np.concatenate(samples)
    padding_fraction = float(load_contracts().style["plots"]["violin"]["limit_padding_fraction"])
    padding = float(np.ptp(values)) * padding_fraction
    apply_nice_linear_axis(
        axis,
        float(values.min()) - padding,
        float(values.max()) + padding,
        coordinate="y",
    )
    return figure
