from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure

from axiomfig.ornaments import request_legend
from axiomfig.style import (
    apply_axis_contract,
    apply_categorical_axis,
    apply_nice_linear_axis,
    errorbar_kwargs,
    reference_line_kwargs,
    series_style,
)


def _errors(
    estimates: np.ndarray, supplied: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    if supplied.shape == estimates.shape:
        errors = supplied
        lower = estimates - errors
        upper = estimates + errors
    elif supplied.shape == (estimates.size, 2):
        lower = supplied[:, 0]
        upper = supplied[:, 1]
        if np.any(lower > estimates) or np.any(upper < estimates):
            raise ValueError("interval bounds must contain each estimate")
        errors = np.vstack((estimates - lower, upper - estimates))
    else:
        raise ValueError("interval must be half-widths or lower/upper pairs")
    return errors, lower, upper


def build_forest(
    label: object | None = None,
    estimate: object | None = None,
    interval: object | None = None,
    uncertainty_type: object | None = None,
    reference: object | None = None,
    xlabel: object | None = None,
) -> Figure:
    if label is None and estimate is None and interval is None and uncertainty_type is None:
        labels = ["Hybrid ODE", "Neural ODE", "ASM baseline", "Linear model"]
        estimates = np.array([0.84, 0.73, 0.59, 0.46])
        errors: np.ndarray = np.array([0.07, 0.09, 0.08, 0.11])
        uncertainty_label = "95% CI"
        limits = (0.25, 1.0)
        selected_reference = 0.5
    elif label is not None and estimate is not None and interval is not None and uncertainty_type:
        labels = [str(item) for item in label]  # type: ignore[union-attr]
        estimates = np.asarray(estimate, dtype=float)
        supplied = np.asarray(interval, dtype=float)
        if estimates.ndim != 1 or estimates.size != len(labels) or estimates.size < 1:
            raise ValueError("forest labels and estimates must be equal-length data")
        errors, lower, upper = _errors(estimates, supplied)
        uncertainty_label = str(uncertainty_type)
        padding = max(float(upper.max() - lower.min()) * 0.05, 0.05)
        limits = (float(lower.min()) - padding, float(upper.max()) + padding)
        selected_reference = None if reference is None else float(reference)
    else:
        raise ValueError("forest requires label, estimate, interval, and uncertainty_type together")
    positions = np.arange(len(labels))
    figure, axis = plt.subplots()
    axis.errorbar(estimates, positions, xerr=errors, **errorbar_kwargs())
    if selected_reference is not None:
        axis.axvline(selected_reference, **reference_line_kwargs())
    axis.set_yticks(positions, labels)
    axis.set(xlabel=(f"Effect estimate ({uncertainty_label})" if xlabel is None else str(xlabel)))
    axis.invert_yaxis()
    apply_axis_contract(axis, surface="open")
    apply_categorical_axis(axis, coordinate="y")
    apply_nice_linear_axis(axis, *limits, coordinate="x")
    return figure


def _grouped_interval(
    *,
    labels: np.ndarray,
    estimates: np.ndarray,
    supplied_interval: np.ndarray,
    groups: np.ndarray,
    uncertainty_type: str,
    reference: float | None,
    xlabel: str | None,
) -> Figure:
    categories = list(dict.fromkeys(labels.astype(str)))
    group_labels = list(dict.fromkeys(groups.astype(str)))
    errors, lower, upper = _errors(estimates, supplied_interval)
    limits = (float(lower.min()), float(upper.max()))
    padding = max((limits[1] - limits[0]) * 0.06, 0.05)
    positions = np.arange(len(categories))
    figure, axis = plt.subplots()
    for index, group_label in enumerate(group_labels):
        mask = groups.astype(str) == group_label
        selected_labels = labels.astype(str)[mask]
        if set(selected_labels) != set(categories) or selected_labels.size != len(categories):
            raise ValueError("each interval group must contain every category exactly once")
        order = np.asarray([list(selected_labels).index(category) for category in categories])
        selected_estimates = estimates[mask][order]
        selected_errors = errors[:, mask][:, order] if errors.ndim == 2 else errors[mask][order]
        offset = (index - (len(group_labels) - 1) / 2) * 0.16
        style = series_style(index)
        axis.errorbar(
            selected_estimates,
            positions + offset,
            xerr=selected_errors,
            label=group_label,
            color=style["color"],
            marker=style["marker"],
            linestyle="none",
            **{key: value for key, value in errorbar_kwargs().items() if key != "marker"},
        )
    if reference is not None:
        axis.axvline(reference, **reference_line_kwargs())
    axis.set_yticks(positions, categories)
    axis.set(xlabel=f"Estimate ({uncertainty_type})" if xlabel is None else xlabel)
    axis.invert_yaxis()
    apply_axis_contract(axis, surface="open")
    apply_categorical_axis(axis, coordinate="y")
    apply_nice_linear_axis(axis, limits[0] - padding, limits[1] + padding, coordinate="x")
    if len(group_labels) > 1:
        request_legend(axis)
    return figure


def build_point_interval(
    label: object | None = None,
    estimate: object | None = None,
    interval: object | None = None,
    uncertainty_type: object | None = None,
    group: object | None = None,
    xlabel: object | None = None,
) -> Figure:
    if all(item is None for item in (label, estimate, interval, uncertainty_type, group)):
        labels = np.tile(np.asarray(["COD", "TN", "TP"], dtype=object), 2)
        estimates = np.array([0.78, 0.69, 0.64, 0.87, 0.79, 0.73])
        supplied = np.array([0.045, 0.045, 0.045, 0.055, 0.055, 0.055])
        groups = np.repeat(np.asarray(["Mechanistic", "Hybrid"], dtype=object), 3)
        uncertainty = "95% CI"
    elif all(item is not None for item in (label, estimate, interval, uncertainty_type)):
        labels = np.asarray(label, dtype=object)
        estimates = np.asarray(estimate, dtype=float)
        supplied = np.asarray(interval, dtype=float)
        groups = (
            np.full(estimates.size, "Series", dtype=object)
            if group is None
            else np.asarray(group, dtype=object)
        )
        uncertainty = str(uncertainty_type)
    else:
        raise ValueError("point_interval requires label, estimate, interval, and uncertainty_type")
    return _grouped_interval(
        labels=labels,
        estimates=estimates,
        supplied_interval=supplied,
        groups=groups,
        uncertainty_type=uncertainty,
        reference=None,
        xlabel=None if xlabel is None else str(xlabel),
    )


def build_coefficient(
    term: object | None = None,
    estimate: object | None = None,
    interval: object | None = None,
    uncertainty_type: object | None = None,
    model: object | None = None,
    reference: object | None = None,
    xlabel: object | None = None,
) -> Figure:
    if all(item is None for item in (term, estimate, interval, uncertainty_type, model)):
        terms = np.tile(
            np.asarray(["Intercept", "Temperature", "Loading", "Oxygen"], dtype=object), 2
        )
        estimates = np.array([0.18, 0.42, -0.31, 0.27, 0.11, 0.36, -0.22, 0.34])
        supplied = np.array([0.08, 0.10, 0.09, 0.08, 0.07, 0.08, 0.08, 0.09])
        models = np.repeat(np.asarray(["Mechanistic", "Hybrid"], dtype=object), 4)
        uncertainty = "95% CI"
        selected_reference = 0.0
    elif all(item is not None for item in (term, estimate, interval, uncertainty_type)):
        terms = np.asarray(term, dtype=object)
        estimates = np.asarray(estimate, dtype=float)
        supplied = np.asarray(interval, dtype=float)
        models = (
            np.full(estimates.size, "Model", dtype=object)
            if model is None
            else np.asarray(model, dtype=object)
        )
        uncertainty = str(uncertainty_type)
        selected_reference = None if reference is None else float(reference)
    else:
        raise ValueError("coefficient requires term, estimate, interval, and uncertainty_type")
    return _grouped_interval(
        labels=terms,
        estimates=estimates,
        supplied_interval=supplied,
        groups=models,
        uncertainty_type=uncertainty,
        reference=selected_reference,
        xlabel=None if xlabel is None else str(xlabel),
    )


BUILDERS = {
    "forest": build_forest,
    "point_interval": build_point_interval,
    "coefficient": build_coefficient,
}
