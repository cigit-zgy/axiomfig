from __future__ import annotations

from statistics import NormalDist

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure

from axiomfig.contracts import bar_width
from axiomfig.template_helpers import (
    add_bar_value_labels,
    apply_axis_contract,
    apply_categorical_axis,
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


def build_residual() -> Figure:
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


def build_calibration() -> Figure:
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


def build_roc() -> Figure:
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


def build_precision_recall() -> Figure:
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


def build_learning_curve() -> Figure:
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


def build_qq() -> Figure:
    rng = np.random.default_rng(149)
    sample = np.sort(rng.normal(0.0, 1.0, 72) + 0.10 * rng.standard_t(5, 72))
    probability = (np.arange(sample.size) + 0.5) / sample.size
    normal = NormalDist()
    theoretical = np.array([normal.inv_cdf(float(value)) for value in probability])
    lower = min(float(theoretical.min()), float(sample.min()))
    upper = max(float(theoretical.max()), float(sample.max()))
    figure, axis = plt.subplots()
    collection = axis.scatter(theoretical, sample)
    apply_scatter_contract(collection)
    axis.plot([lower, upper], [lower, upper], **reference_line_kwargs())
    axis.set(xlabel="Theoretical normal quantile", ylabel="Sample quantile")
    _open(axis, (lower, upper), (lower, upper))
    return figure


def build_feature_importance() -> Figure:
    labels = ["Temperature", "Influent COD", "Dissolved oxygen", "Hydraulic load"]
    values = np.array([0.31, 0.27, 0.22, 0.14])
    positions = np.arange(len(labels))
    figure, axis = plt.subplots()
    bars = axis.barh(positions, values, height=bar_width())
    axis.set_yticks(positions, labels)
    axis.set(xlabel="Permutation importance (-)")
    axis.invert_yaxis()
    apply_axis_contract(axis, surface="open")
    apply_categorical_axis(axis, coordinate="y")
    apply_nice_linear_axis(axis, 0.0, 0.4, coordinate="x")
    add_bar_value_labels(axis, [bars])
    return figure


BUILDERS = {
    "residual": build_residual,
    "bland_altman": build_bland_altman,
    "calibration": build_calibration,
    "roc": build_roc,
    "precision_recall": build_precision_recall,
    "learning_curve": build_learning_curve,
    "qq": build_qq,
    "feature_importance": build_feature_importance,
}
