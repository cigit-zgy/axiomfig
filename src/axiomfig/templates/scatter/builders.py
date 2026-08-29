from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure

from axiomfig.template_helpers import (
    apply_axis_contract,
    apply_nice_linear_axis,
    apply_scatter_contract,
    place_legend_above,
    reference_line_kwargs,
    series_style,
)


def _open(axis: plt.Axes, xlim: tuple[float, float], ylim: tuple[float, float]) -> None:
    apply_axis_contract(axis, surface="open")
    apply_nice_linear_axis(axis, *xlim, coordinate="x")
    apply_nice_linear_axis(axis, *ylim, coordinate="y")


def build_simple() -> Figure:
    rng = np.random.default_rng(23)
    x = np.linspace(0.0, 24.0, 48)
    figure, axis = plt.subplots()
    collection = axis.scatter(x, 0.6 * x + rng.normal(0.0, 1.4, x.size))
    apply_scatter_contract(collection)
    axis.set(xlabel="Hydraulic loading", ylabel="Observed response")
    _open(axis, (0.0, 24.0), (-2.0, 18.0))
    return figure


def build_grouped() -> Figure:
    rng = np.random.default_rng(31)
    figure, axis = plt.subplots()
    for index, label in enumerate(("Train", "Validation", "Test")):
        x = np.linspace(2.0, 28.0, 24)
        style = series_style(index)
        collection = axis.scatter(
            x,
            x + rng.normal(0.0, 1.0 + 0.35 * index, x.size) + (index - 1) * 0.7,
            label=label,
            color=style["color"],
            marker=style["marker"],
        )
        apply_scatter_contract(collection)
    axis.set(xlabel="Observed concentration (mg/L)", ylabel="Predicted concentration (mg/L)")
    _open(axis, (0.0, 30.0), (0.0, 30.0))
    place_legend_above(axis)
    return figure


def build_regression() -> Figure:
    rng = np.random.default_rng(59)
    x = np.linspace(0.5, 19.0, 45)
    y = np.clip(2.1 + 0.74 * x + rng.normal(0.0, 1.15, x.size), 0.8, 19.0)
    fit = np.polyfit(x, y, 1)
    figure, axis = plt.subplots()
    collection = axis.scatter(x, y)
    apply_scatter_contract(collection)
    axis.plot(x, np.polyval(fit, x))
    axis.text(0.04, 0.92, r"$R^2 = 0.94$", transform=axis.transAxes)
    axis.set(xlabel="Influent load", ylabel="Effluent response")
    _open(axis, (0.0, 20.0), (0.0, 20.0))
    return figure


def build_parity() -> Figure:
    rng = np.random.default_rng(43)
    observed = np.linspace(2.0, 28.0, 42)
    figure, axis = plt.subplots()
    collection = axis.scatter(observed, observed + rng.normal(0.0, 1.35, observed.size))
    apply_scatter_contract(collection)
    axis.plot([0.0, 30.0], [0.0, 30.0], **reference_line_kwargs())
    axis.set(xlabel="Observed concentration (mg/L)", ylabel="Predicted concentration (mg/L)")
    _open(axis, (0.0, 30.0), (0.0, 30.0))
    return figure


BUILDERS = {
    "simple": build_simple,
    "grouped": build_grouped,
    "regression": build_regression,
    "parity": build_parity,
}
