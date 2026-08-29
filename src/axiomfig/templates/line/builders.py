from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure

from axiomfig.template_helpers import (
    apply_axis_contract,
    apply_nice_linear_axis,
    confidence_interval_kwargs,
    errorbar_kwargs,
    line_marker_kwargs,
    place_legend_above,
    series_style,
)


def _open(axis: plt.Axes, xlim: tuple[float, float], ylim: tuple[float, float]) -> None:
    apply_axis_contract(axis, surface="open")
    apply_nice_linear_axis(axis, *xlim, coordinate="x")
    apply_nice_linear_axis(axis, *ylim, coordinate="y")


def build_single() -> Figure:
    x = np.linspace(0.0, 12.0, 81)
    figure, axis = plt.subplots()
    axis.plot(x, 1.0 - np.exp(-x / 3.2))
    axis.set(xlabel="Time (d)", ylabel="Normalized response (-)")
    _open(axis, (0.0, 12.0), (0.0, 1.0))
    return figure


def build_multi() -> Figure:
    x = np.linspace(0.0, 12.0, 81)
    figure, axis = plt.subplots()
    series = (
        (1.0 - np.exp(-x / 3.0), "Hybrid model"),
        (0.93 * (1.0 - np.exp(-x / 4.1)), "Mechanistic model"),
        (0.86 * (1.0 - np.exp(-x / 4.8)), "Neural ODE"),
    )
    for index, (values, label) in enumerate(series):
        axis.plot(x, values, label=label, markevery=10, **series_style(index))
    axis.set(xlabel="Time (d)", ylabel="Normalized response (-)")
    _open(axis, (0.0, 12.0), (0.0, 1.0))
    place_legend_above(axis)
    return figure


def build_marker() -> Figure:
    x = np.linspace(0.5, 9.5, 11)
    figure, axis = plt.subplots()
    axis.plot(x, 0.18 + 0.07 * x, **line_marker_kwargs())
    axis.set(xlabel="Sampling day", ylabel="Removal efficiency (-)")
    _open(axis, (0.0, 10.0), (0.1, 0.95))
    return figure


def build_confidence_band() -> Figure:
    x = np.linspace(0.0, 12.0, 81)
    mean = 1.0 - np.exp(-x / 3.2)
    spread = 0.045 + 0.025 * np.exp(-x / 4.0)
    figure, axis = plt.subplots()
    color = plt.rcParams["axes.prop_cycle"].by_key()["color"][0]
    axis.fill_between(x, mean - spread, mean + spread, **confidence_interval_kwargs(color))
    axis.plot(x, mean)
    axis.set(xlabel="Time (d)", ylabel="Estimated response (-)")
    _open(axis, (0.0, 12.0), (0.0, 1.1))
    return figure


def build_errorbar() -> Figure:
    x = np.linspace(1.25, 5.75, 6)
    y = np.array([0.42, 0.51, 0.63, 0.70, 0.76, 0.79])
    error = np.array([0.045, 0.052, 0.040, 0.036, 0.032, 0.030])
    figure, axis = plt.subplots()
    axis.errorbar(x, y, yerr=error, **errorbar_kwargs())
    axis.set(xlabel="Experiment", ylabel="Estimated coefficient (-)")
    _open(axis, (1.0, 6.0), (0.3, 0.9))
    return figure


BUILDERS = {
    "single": build_single,
    "multi": build_multi,
    "marker": build_marker,
    "confidence_band": build_confidence_band,
    "errorbar": build_errorbar,
}
