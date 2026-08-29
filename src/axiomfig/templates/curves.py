from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure

from axiomfig.template_helpers import (
    apply_axis_contract,
    apply_categorical_axis,
    apply_nice_linear_axis,
    apply_scatter_contract,
    confidence_interval_kwargs,
    errorbar_kwargs,
    line_marker_kwargs,
    place_legend_above,
    reference_line_kwargs,
    series_style,
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
        **confidence_interval_kwargs(color),
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
    axis.plot(
        epochs,
        0.34 * np.exp(-epochs / 6.0) + 0.055,
        label="Training RMSE",
        markevery=3,
        **series_style(0),
    )
    axis.plot(
        epochs,
        0.38 * np.exp(-epochs / 6.8) + 0.072,
        label="Validation RMSE",
        markevery=3,
        **series_style(1),
    )
    axis.axhline(0.10, label="Target", **reference_line_kwargs())
    axis.set(xlabel="Training epoch", ylabel="RMSE (mg/L)")
    _open(axis, (1.0, 20.0), (0.0, 0.4))
    place_legend_above(axis)
    return figure


def build_forest_plot() -> Figure:
    labels = ["Hybrid ODE", "Neural ODE", "ASM baseline", "Linear model"]
    estimates = np.array([0.84, 0.73, 0.59, 0.46])
    errors = np.array([0.07, 0.09, 0.08, 0.11])
    positions = np.arange(len(labels))
    figure, axis = plt.subplots()
    axis.errorbar(estimates, positions, xerr=errors, **errorbar_kwargs())
    axis.axvline(0.5, **reference_line_kwargs())
    axis.set_yticks(positions, labels)
    axis.set(xlabel="Effect estimate (95% CI)")
    axis.invert_yaxis()
    apply_axis_contract(axis, surface="open")
    apply_categorical_axis(axis, coordinate="y")
    apply_nice_linear_axis(axis, 0.25, 1.0, coordinate="x")
    return figure


def build_point_interval() -> Figure:
    labels = ["COD", "TN", "TP"]
    values = np.array([[0.78, 0.69, 0.64], [0.87, 0.79, 0.73]])
    positions = np.arange(len(labels))
    figure, axis = plt.subplots()
    for index, label in enumerate(("Mechanistic", "Hybrid")):
        offset = (index - 0.5) * 0.16
        style = series_style(index)
        axis.errorbar(
            values[index],
            positions + offset,
            xerr=0.045 + 0.01 * index,
            label=label,
            color=style["color"],
            marker=style["marker"],
            linestyle="none",
            **{key: value for key, value in errorbar_kwargs().items() if key != "marker"},
        )
    axis.set_yticks(positions, labels)
    axis.set(xlabel="Validation score (95% CI)")
    apply_axis_contract(axis, surface="open")
    apply_categorical_axis(axis, coordinate="y")
    apply_nice_linear_axis(axis, 0.5, 1.0, coordinate="x")
    place_legend_above(axis)
    return figure


def build_bland_altman() -> Figure:
    rng = np.random.default_rng(127)
    mean = np.linspace(2.0, 20.0, 48)
    difference = 0.28 + rng.normal(0.0, 0.72, mean.size)
    center = float(difference.mean())
    limit = 1.96 * float(difference.std(ddof=1))
    figure, axis = plt.subplots()
    collection = axis.scatter(mean, difference)
    apply_scatter_contract(collection)
    axis.axhline(center, label="Mean bias", **reference_line_kwargs())
    axis.axhline(center + limit, color="black", linestyle=":", label="95% limits")
    axis.axhline(center - limit, color="black", linestyle=":")
    axis.set(xlabel="Mean of methods", ylabel="Difference")
    _open(axis, (0.0, 22.0), (-2.5, 3.0))
    place_legend_above(axis)
    return figure


def build_roc_curve() -> Figure:
    false_positive = np.linspace(0.0, 1.0, 80)
    figure, axis = plt.subplots()
    curves = ((0.30, "Hybrid (AUC 0.91)"), (0.48, "Baseline (AUC 0.84)"))
    for index, (power, label) in enumerate(curves):
        axis.plot(
            false_positive,
            false_positive**power,
            label=label,
            markevery=10,
            **series_style(index),
        )
    axis.plot([0, 1], [0, 1], **reference_line_kwargs())
    axis.set(xlabel="False-positive rate", ylabel="True-positive rate")
    _open(axis, (0.0, 1.0), (0.0, 1.0))
    place_legend_above(axis)
    return figure


def build_pr_curve() -> Figure:
    recall = np.linspace(0.0, 1.0, 80)
    figure, axis = plt.subplots()
    for index, (scale, label) in enumerate(((0.88, "Hybrid"), (0.78, "Baseline"))):
        precision = np.clip(scale - 0.34 * recall**2 + 0.08 * (1.0 - recall), 0.0, 1.0)
        axis.plot(recall, precision, label=label, markevery=10, **series_style(index))
    axis.axhline(0.50, **reference_line_kwargs())
    axis.set(xlabel="Recall", ylabel="Precision")
    _open(axis, (0.0, 1.0), (0.45, 1.0))
    place_legend_above(axis)
    return figure


def build_calibration_curve() -> Figure:
    predicted = np.linspace(0.05, 0.95, 10)
    figure, axis = plt.subplots()
    for index, (offset, label) in enumerate(((0.0, "Hybrid"), (0.055, "Baseline"))):
        observed = np.clip(predicted + offset * np.sin(np.pi * predicted), 0.0, 1.0)
        axis.plot(predicted, observed, label=label, **series_style(index))
    axis.plot([0, 1], [0, 1], **reference_line_kwargs())
    axis.set(xlabel="Predicted probability", ylabel="Observed frequency")
    _open(axis, (0.0, 1.0), (0.0, 1.0))
    place_legend_above(axis)
    return figure


def build_residual_diagnostics() -> Figure:
    rng = np.random.default_rng(137)
    fitted = np.linspace(0.8, 20.0, 54)
    residual = rng.normal(0.0, 0.55 + 0.035 * fitted, fitted.size)
    trend = 0.13 * np.sin(fitted / 3.5)
    figure, axis = plt.subplots()
    collection = axis.scatter(fitted, residual)
    apply_scatter_contract(collection)
    axis.plot(fitted, trend, label="Smoothed trend", **series_style(1, include_marker=False))
    axis.axhline(0.0, **reference_line_kwargs())
    axis.set(xlabel="Fitted value", ylabel="Standardized residual")
    _open(axis, (0.0, 21.0), (-3.5, 3.5))
    return figure
