from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure

from axiomfig.template_helpers import (
    apply_axis_contract,
    apply_nice_linear_axis,
    apply_scatter_contract,
    apply_single_panel_layout,
    place_legend_above,
)


def build_line() -> Figure:
    x = np.linspace(0.0, 12.0, 81)
    figure, axis = plt.subplots()
    apply_single_panel_layout(figure)
    axis.plot(x, 1.0 - np.exp(-x / 3.2), label="Hybrid model")
    axis.plot(x, 0.92 * (1.0 - np.exp(-x / 4.0)), label="Mechanistic model")
    axis.set(xlabel="Time (d)", ylabel="Normalized response (-)")
    apply_axis_contract(axis, surface="open")
    apply_nice_linear_axis(axis, float(x.min()), float(x.max()), coordinate="x")
    apply_nice_linear_axis(axis, 0.0, 1.0, coordinate="y")
    place_legend_above(axis)
    return figure


def build_scatter() -> Figure:
    rng = np.random.default_rng(23)
    observed = np.linspace(2.0, 28.0, 42)
    figure, axis = plt.subplots()
    apply_single_panel_layout(figure)
    collection = axis.scatter(observed, observed + rng.normal(0.0, 1.35, observed.size))
    apply_scatter_contract(collection)
    axis.plot([0.0, 30.0], [0.0, 30.0], linestyle="--", label="1:1 reference")
    axis.set(
        xlim=(0.0, 30.0),
        ylim=(0.0, 30.0),
        xlabel="Observed concentration (mg/L)",
        ylabel="Predicted concentration (mg/L)",
    )
    apply_axis_contract(axis, surface="open")
    apply_nice_linear_axis(axis, 0.0, 30.0, coordinate="x")
    apply_nice_linear_axis(axis, 0.0, 30.0, coordinate="y")
    return figure
