from __future__ import annotations

from statistics import NormalDist

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure

from axiomfig.contracts import FILL_EDGE_PT, bar_width
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


def _limits(x: np.ndarray, y: np.ndarray) -> tuple[tuple[float, float], tuple[float, float]]:
    x_padding = max(float(np.ptp(x)) * 0.05, 0.05)
    y_padding = max(float(np.ptp(y)) * 0.05, 0.05)
    return (
        (float(x.min()) - x_padding, float(x.max()) + x_padding),
        (float(y.min()) - y_padding, float(y.max()) + y_padding),
    )


def _series(
    x: np.ndarray,
    y: np.ndarray,
    group: object | None,
) -> list[tuple[np.ndarray, np.ndarray, str | None]]:
    if group is None:
        return [(x, y, None)]
    groups = np.asarray(group, dtype=object).astype(str)
    return [(x[groups == label], y[groups == label], label) for label in dict.fromkeys(groups)]


def build_residual(
    fitted: object | None = None,
    residual: object | None = None,
    trend: object | None = None,
) -> Figure:
    if fitted is None and residual is None and trend is None:
        rng = np.random.default_rng(137)
        fitted_values = np.linspace(0.8, 20.0, 54)
        residual_values = rng.normal(0.0, 0.55 + 0.035 * fitted_values, fitted_values.size)
        trend_values: np.ndarray | None = 0.13 * np.sin(fitted_values / 3.5)
        limits = ((0.0, 21.0), (-3.5, 3.5))
    elif fitted is not None and residual is not None:
        fitted_values = np.asarray(fitted, dtype=float)
        residual_values = np.asarray(residual, dtype=float)
        if (
            fitted_values.ndim != 1
            or fitted_values.shape != residual_values.shape
            or fitted_values.size < 2
        ):
            raise ValueError("fitted and residual must be equal-length one-dimensional data")
        trend_values = None if trend is None else np.asarray(trend, dtype=float)
        if trend_values is not None and trend_values.shape != fitted_values.shape:
            raise ValueError("residual trend must match fitted data")
        x_padding = max(float(np.ptp(fitted_values)) * 0.04, 0.1)
        y_padding = max(float(np.ptp(residual_values)) * 0.08, 0.1)
        limits = (
            (
                float(fitted_values.min()) - x_padding,
                float(fitted_values.max()) + x_padding,
            ),
            (
                float(residual_values.min()) - y_padding,
                float(residual_values.max()) + y_padding,
            ),
        )
    else:
        raise ValueError("residual diagnostic requires fitted and residual together")
    figure, axis = plt.subplots()
    collection = axis.scatter(fitted_values, residual_values)
    apply_scatter_contract(collection)
    if trend_values is not None:
        axis.plot(
            fitted_values,
            trend_values,
            label="Smoothed trend",
            **series_style(1, include_marker=False),
        )
    axis.axhline(0.0, **reference_line_kwargs())
    axis.set(xlabel="Fitted value", ylabel="Standardized residual")
    _open(axis, *limits)
    return figure


def build_bland_altman(
    mean: object | None = None,
    difference: object | None = None,
    agreement_type: object | None = None,
    center: object | None = None,
    limits: object | None = None,
) -> Figure:
    if mean is None and difference is None and agreement_type is None:
        rng = np.random.default_rng(127)
        mean_values = np.linspace(2.0, 20.0, 48)
        difference_values = 0.28 + rng.normal(0.0, 0.72, mean_values.size)
        agreement = "95% limits"
        axis_limits = ((0.0, 22.0), (-2.5, 3.0))
    elif mean is not None and difference is not None and agreement_type is not None:
        mean_values = np.asarray(mean, dtype=float)
        difference_values = np.asarray(difference, dtype=float)
        agreement = str(agreement_type)
        axis_limits = _limits(mean_values, difference_values)
    else:
        raise ValueError("bland_altman requires mean, difference, and agreement_type")
    selected_center = float(difference_values.mean()) if center is None else float(center)
    if limits is None:
        spread = 1.96 * float(difference_values.std(ddof=1))
        selected_limits = (selected_center - spread, selected_center + spread)
    else:
        selected_limits = tuple(float(item) for item in limits)  # type: ignore[arg-type]
    figure, axis = plt.subplots()
    collection = axis.scatter(mean_values, difference_values)
    apply_scatter_contract(collection)
    axis.axhline(selected_center, label="Mean bias", **reference_line_kwargs())
    axis.axhline(selected_limits[1], color="black", linestyle=":", label=agreement)
    axis.axhline(selected_limits[0], color="black", linestyle=":")
    axis.set(xlabel="Mean of methods", ylabel="Difference")
    _open(axis, *axis_limits)
    place_legend_above(axis)
    return figure


def build_calibration(
    predicted_probability: object | None = None,
    observed_frequency: object | None = None,
    group: object | None = None,
) -> Figure:
    if predicted_probability is None and observed_frequency is None:
        predicted = np.tile(np.linspace(0.05, 0.95, 10), 2)
        observed = np.concatenate(
            (
                predicted[:10],
                np.clip(predicted[10:] + 0.055 * np.sin(np.pi * predicted[10:]), 0.0, 1.0),
            )
        )
        groups: object = np.repeat(["Hybrid", "Baseline"], 10)
    elif predicted_probability is not None and observed_frequency is not None:
        predicted = np.asarray(predicted_probability, dtype=float)
        observed = np.asarray(observed_frequency, dtype=float)
        groups = group
    else:
        raise ValueError("calibration requires predicted_probability and observed_frequency")
    figure, axis = plt.subplots()
    selected_series = _series(predicted, observed, groups)
    for index, (selected_x, selected_y, label) in enumerate(selected_series):
        order = np.argsort(selected_x)
        axis.plot(selected_x[order], selected_y[order], label=label, **series_style(index))
    axis.plot([0, 1], [0, 1], **reference_line_kwargs())
    axis.set(xlabel="Predicted probability", ylabel="Observed frequency")
    _open(axis, (0.0, 1.0), (0.0, 1.0))
    if any(label is not None for _, _, label in selected_series):
        place_legend_above(axis)
    return figure


def build_roc(
    false_positive_rate: object | None = None,
    true_positive_rate: object | None = None,
    group: object | None = None,
    auc: object | None = None,
) -> Figure:
    if false_positive_rate is None and true_positive_rate is None:
        false_positive = np.tile(np.linspace(0.0, 1.0, 80), 2)
        true_positive = np.concatenate((false_positive[:80] ** 0.30, false_positive[80:] ** 0.48))
        groups: object = np.repeat(["Hybrid", "Baseline"], 80)
        auc_values = np.array([0.91, 0.84])
    elif false_positive_rate is not None and true_positive_rate is not None:
        false_positive = np.asarray(false_positive_rate, dtype=float)
        true_positive = np.asarray(true_positive_rate, dtype=float)
        groups = group
        auc_values = None if auc is None else np.asarray(auc, dtype=float)
    else:
        raise ValueError("roc requires false_positive_rate and true_positive_rate")
    figure, axis = plt.subplots()
    selected_series = _series(false_positive, true_positive, groups)
    for index, (selected_x, selected_y, label) in enumerate(selected_series):
        order = np.argsort(selected_x)
        selected_label = label
        if auc_values is not None:
            auc_value = auc_values[0] if auc_values.size == 1 else auc_values[index]
            selected_label = f"{label or 'Series'} (AUC {auc_value:.2f})"
        axis.plot(
            selected_x[order],
            selected_y[order],
            label=selected_label,
            markevery=10,
            **series_style(index),
        )
    axis.plot([0, 1], [0, 1], **reference_line_kwargs())
    axis.set(xlabel="False-positive rate", ylabel="True-positive rate")
    _open(axis, (0.0, 1.0), (0.0, 1.0))
    if any(label is not None for _, _, label in selected_series) or auc_values is not None:
        place_legend_above(axis)
    return figure


def build_precision_recall(
    recall: object | None = None,
    precision: object | None = None,
    group: object | None = None,
    baseline: object | None = None,
) -> Figure:
    if recall is None and precision is None:
        recall_values = np.tile(np.linspace(0.0, 1.0, 80), 2)
        precision_values = np.concatenate(
            tuple(
                np.clip(
                    scale - 0.34 * recall_values[:80] ** 2 + 0.08 * (1.0 - recall_values[:80]),
                    0.0,
                    1.0,
                )
                for scale in (0.88, 0.78)
            )
        )
        groups: object = np.repeat(["Hybrid", "Baseline"], 80)
        selected_baseline = 0.50
    elif recall is not None and precision is not None:
        recall_values = np.asarray(recall, dtype=float)
        precision_values = np.asarray(precision, dtype=float)
        groups = group
        selected_baseline = 0.50 if baseline is None else float(baseline)
    else:
        raise ValueError("precision_recall requires recall and precision")
    figure, axis = plt.subplots()
    selected_series = _series(recall_values, precision_values, groups)
    for index, (selected_x, selected_y, label) in enumerate(selected_series):
        order = np.argsort(selected_x)
        axis.plot(
            selected_x[order], selected_y[order], label=label, markevery=10, **series_style(index)
        )
    axis.axhline(selected_baseline, **reference_line_kwargs())
    axis.set(xlabel="Recall", ylabel="Precision")
    _open(axis, (0.0, 1.0), (0.45, 1.0))
    if any(label is not None for _, _, label in selected_series):
        place_legend_above(axis)
    return figure


def build_learning_curve(
    iteration: object | None = None,
    metric: object | None = None,
    series: object | None = None,
    target: object | None = None,
    metric_name: object | None = None,
) -> Figure:
    if iteration is None and metric is None and series is None:
        epochs = np.tile(np.arange(1.0, 21.0), 2)
        metrics = np.concatenate(
            (
                0.34 * np.exp(-epochs[:20] / 6.0) + 0.055,
                0.38 * np.exp(-epochs[20:] / 6.8) + 0.072,
            )
        )
        groups: object = np.repeat(["Training RMSE", "Validation RMSE"], 20)
        selected_target = 0.10
        selected_name = "RMSE (mg/L)"
    elif iteration is not None and metric is not None and series is not None:
        epochs = np.asarray(iteration, dtype=float)
        metrics = np.asarray(metric, dtype=float)
        groups = series
        selected_target = None if target is None else float(target)
        selected_name = "Metric" if metric_name is None else str(metric_name)
    else:
        raise ValueError("learning_curve requires iteration, metric, and series")
    figure, axis = plt.subplots()
    selected_series = _series(epochs, metrics, groups)
    for index, (selected_x, selected_y, label) in enumerate(selected_series):
        order = np.argsort(selected_x)
        axis.plot(
            selected_x[order], selected_y[order], label=label, markevery=3, **series_style(index)
        )
    if selected_target is not None:
        axis.axhline(selected_target, label="Target", **reference_line_kwargs())
    axis.set(xlabel="Training epoch", ylabel=selected_name)
    _open(axis, *_limits(epochs, metrics))
    place_legend_above(axis)
    return figure


def build_qq(
    theoretical_quantile: object | None = None,
    sample_quantile: object | None = None,
    reference_distribution: object | None = None,
    envelope: object | None = None,
) -> Figure:
    if theoretical_quantile is None and sample_quantile is None and reference_distribution is None:
        rng = np.random.default_rng(149)
        sample = np.sort(rng.normal(0.0, 1.0, 72) + 0.10 * rng.standard_t(5, 72))
        probability = (np.arange(sample.size) + 0.5) / sample.size
        normal = NormalDist()
        theoretical = np.array([normal.inv_cdf(float(value)) for value in probability])
        distribution_label = "normal"
    elif all(
        item is not None for item in (theoretical_quantile, sample_quantile, reference_distribution)
    ):
        theoretical = np.asarray(theoretical_quantile, dtype=float)
        sample = np.asarray(sample_quantile, dtype=float)
        distribution_label = str(reference_distribution)
    else:
        raise ValueError(
            "qq requires theoretical_quantile, sample_quantile, and reference_distribution"
        )
    lower = min(float(theoretical.min()), float(sample.min()))
    upper = max(float(theoretical.max()), float(sample.max()))
    figure, axis = plt.subplots()
    collection = axis.scatter(theoretical, sample)
    apply_scatter_contract(collection)
    if envelope is not None:
        bounds = np.asarray(envelope, dtype=float)
        axis.fill_between(
            theoretical,
            bounds[:, 0],
            bounds[:, 1],
            alpha=0.16,
            edgecolor="black",
            linewidth=FILL_EDGE_PT,
        )
    axis.plot([lower, upper], [lower, upper], **reference_line_kwargs())
    axis.set(
        xlabel=f"Theoretical {distribution_label} quantile",
        ylabel="Sample quantile",
    )
    _open(axis, (lower, upper), (lower, upper))
    return figure


def build_feature_importance(
    feature: object | None = None,
    importance: object | None = None,
    importance_type: object | None = None,
    uncertainty: object | None = None,
    xlabel: object | None = None,
) -> Figure:
    if feature is None and importance is None and importance_type is None:
        labels = ["Temperature", "Influent COD", "Dissolved oxygen", "Hydraulic load"]
        values = np.array([0.31, 0.27, 0.22, 0.14])
        selected_type = "Permutation"
        errors = None
    elif feature is not None and importance is not None and importance_type is not None:
        labels = [str(item) for item in feature]  # type: ignore[union-attr]
        values = np.asarray(importance, dtype=float)
        selected_type = str(importance_type)
        supplied = None if uncertainty is None else np.asarray(uncertainty, dtype=float)
        errors = None if supplied is None else supplied.T if supplied.ndim == 2 else supplied
    else:
        raise ValueError("feature_importance requires feature, importance, and importance_type")
    positions = np.arange(len(labels))
    figure, axis = plt.subplots()
    bars = axis.barh(positions, values, height=bar_width(), xerr=errors)
    axis.set_yticks(positions, labels)
    axis.set(xlabel=f"{selected_type} importance (-)" if xlabel is None else str(xlabel))
    axis.invert_yaxis()
    apply_axis_contract(axis, surface="open")
    apply_categorical_axis(axis, coordinate="y")
    apply_nice_linear_axis(axis, 0.0, max(float(values.max()) * 1.2, 0.1), coordinate="x")
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
