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


def build_single(x: object | None = None, y: object | None = None) -> Figure:
    if x is None and y is None:
        limits = ((0.0, 12.0), (0.0, 1.0))
        values_x = np.linspace(0.0, 12.0, 81)
        values_y = 1.0 - np.exp(-values_x / 3.2)
    elif x is not None and y is not None:
        values_x = np.asarray(x, dtype=float)
        values_y = np.asarray(y, dtype=float)
        if values_x.ndim != 1 or values_x.shape != values_y.shape or values_x.size < 2:
            raise ValueError("line x and y must be equal-length one-dimensional data")
        x_padding = max(float(np.ptp(values_x)) * 0.03, 0.1)
        y_padding = max(float(np.ptp(values_y)) * 0.05, 0.05)
        limits = (
            (float(values_x.min()) - x_padding, float(values_x.max()) + x_padding),
            (float(values_y.min()) - y_padding, float(values_y.max()) + y_padding),
        )
    else:
        raise ValueError("line requires x and y together")
    figure, axis = plt.subplots()
    axis.plot(values_x, values_y)
    axis.set(xlabel="Time (d)", ylabel="Normalized response (-)")
    _open(axis, *limits)
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


def build_step() -> Figure:
    x = np.arange(0.0, 13.0, 1.0)
    response = np.array(
        [0.08, 0.12, 0.20, 0.31, 0.39, 0.48, 0.56, 0.61, 0.69, 0.75, 0.81, 0.86, 0.89]
    )
    figure, axis = plt.subplots()
    axis.step(x, response, where="post")
    axis.set(xlabel="Sampling interval", ylabel="Cumulative response (-)")
    _open(axis, (0.0, 12.0), (0.0, 1.0))
    return figure


def build_area() -> Figure:
    x = np.linspace(0.0, 12.0, 81)
    response = 0.15 + 0.72 * (1.0 - np.exp(-x / 3.8))
    figure, axis = plt.subplots()
    color = plt.rcParams["axes.prop_cycle"].by_key()["color"][0]
    axis.fill_between(x, 0.0, response, **confidence_interval_kwargs(color))
    axis.plot(x, response)
    axis.set(xlabel="Time (d)", ylabel="Accumulated fraction (-)")
    _open(axis, (0.0, 12.0), (0.0, 1.0))
    return figure


BUILDERS = {
    "single": build_single,
    "multi": build_multi,
    "marker": build_marker,
    "confidence_band": build_confidence_band,
    "errorbar": build_errorbar,
    "step": build_step,
    "area": build_area,
}
