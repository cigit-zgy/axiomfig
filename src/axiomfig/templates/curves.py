from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure

from axiomfig.contracts import MAIN_STROKE_PT
from axiomfig.template_helpers import (
    apply_axis_contract,
    apply_nice_linear_axis,
    apply_scatter_contract,
    confidence_interval_kwargs,
    errorbar_kwargs,
    line_marker_kwargs,
    place_legend_above,
)


def _open(axis: plt.Axes, xlim: tuple[float, float], ylim: tuple[float, float]) -> None:
    apply_axis_contract(axis, surface="open")
    apply_nice_linear_axis(axis, *xlim, coordinate="x")
    apply_nice_linear_axis(axis, *ylim, coordinate="y")


def build_single_line() -> Figure:
    x = np.linspace(0.0, 12.0, 81)
    figure, axis = plt.subplots()
    axis.plot(x, 1.0 - np.exp(-x / 3.2))
    axis.set(xlabel="Time (d)", ylabel="Normalized response (-)")
    _open(axis, (0.0, 12.0), (0.0, 1.0))
    return figure


def build_multi_line() -> Figure:
    x = np.linspace(0.0, 12.0, 81)
    figure, axis = plt.subplots()
    axis.plot(x, 1.0 - np.exp(-x / 3.0), label="Hybrid model")
    axis.plot(x, 0.93 * (1.0 - np.exp(-x / 4.1)), label="Mechanistic model")
    axis.plot(x, 0.86 * (1.0 - np.exp(-x / 4.8)), label="Neural ODE")
    axis.set(xlabel="Time (d)", ylabel="Normalized response (-)")
    _open(axis, (0.0, 12.0), (0.0, 1.0))
    place_legend_above(axis)
    return figure


def build_line_marker() -> Figure:
    x = np.linspace(0.5, 9.5, 11)
    figure, axis = plt.subplots()
    axis.plot(x, 0.18 + 0.07 * x, **line_marker_kwargs())
    axis.set(xlabel="Sampling day", ylabel="Removal efficiency (-)")
    _open(axis, (0.0, 10.0), (0.1, 0.95))
    return figure


def build_line_ci() -> Figure:
    x = np.linspace(0.0, 12.0, 81)
    mean = 1.0 - np.exp(-x / 3.2)
    spread = 0.045 + 0.025 * np.exp(-x / 4.0)
    figure, axis = plt.subplots()
    color = plt.rcParams["axes.prop_cycle"].by_key()["color"][0]
    axis.fill_between(
        x,
        mean - spread,
        mean + spread,
        color=color,
        **confidence_interval_kwargs(),
    )
    axis.plot(x, mean)
    axis.set(xlabel="Time (d)", ylabel="Estimated response (-)")
    _open(axis, (0.0, 12.0), (0.0, 1.1))
    return figure


def build_scatter() -> Figure:
    rng = np.random.default_rng(23)
    x = np.linspace(0.0, 24.0, 48)
    figure, axis = plt.subplots()
    collection = axis.scatter(x, 0.6 * x + rng.normal(0.0, 1.4, x.size))
    apply_scatter_contract(collection)
    axis.set(xlabel="Hydraulic loading", ylabel="Observed response")
    _open(axis, (0.0, 24.0), (-2.0, 18.0))
    return figure


def build_grouped_scatter() -> Figure:
    rng = np.random.default_rng(31)
    figure, axis = plt.subplots()
    for index, label in enumerate(("Train", "Validation", "Test")):
        x = np.linspace(2.0, 28.0, 24)
        collection = axis.scatter(
            x,
            x + rng.normal(0.0, 1.0 + 0.35 * index, x.size) + (index - 1) * 0.7,
            label=label,
        )
        apply_scatter_contract(collection)
    axis.set(xlabel="Observed concentration (mg/L)", ylabel="Predicted concentration (mg/L)")
    _open(axis, (0.0, 30.0), (0.0, 30.0))
    place_legend_above(axis)
    return figure


def build_parity() -> Figure:
    rng = np.random.default_rng(43)
    observed = np.linspace(2.0, 28.0, 42)
    figure, axis = plt.subplots()
    collection = axis.scatter(observed, observed + rng.normal(0.0, 1.35, observed.size))
    apply_scatter_contract(collection)
    axis.plot([0.0, 30.0], [0.0, 30.0], linestyle="--")
    axis.set(xlabel="Observed concentration (mg/L)", ylabel="Predicted concentration (mg/L)")
    _open(axis, (0.0, 30.0), (0.0, 30.0))
    return figure


def build_regression_scatter() -> Figure:
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


def build_errorbar() -> Figure:
    x = np.linspace(1.25, 5.75, 6)
    y = np.array([0.42, 0.51, 0.63, 0.70, 0.76, 0.79])
    error = np.array([0.045, 0.052, 0.040, 0.036, 0.032, 0.030])
    figure, axis = plt.subplots()
    axis.errorbar(
        x,
        y,
        yerr=error,
        **errorbar_kwargs(),
    )
    axis.set(xlabel="Experiment", ylabel="Estimated coefficient (-)")
    _open(axis, (1.0, 6.0), (0.3, 0.9))
    return figure


def build_model_evaluation() -> Figure:
    epochs = np.arange(1.0, 21.0)
    figure, axis = plt.subplots()
    axis.plot(epochs, 0.34 * np.exp(-epochs / 6.0) + 0.055, label="Training RMSE")
    axis.plot(epochs, 0.38 * np.exp(-epochs / 6.8) + 0.072, label="Validation RMSE")
    axis.axhline(0.10, color="black", linestyle=":", linewidth=MAIN_STROKE_PT, label="Target")
    axis.set(xlabel="Training epoch", ylabel="RMSE (mg/L)")
    _open(axis, (1.0, 20.0), (0.0, 0.4))
    place_legend_above(axis)
    return figure
