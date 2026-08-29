from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure

from axiomfig.template_helpers import (
    apply_axis_contract,
    apply_categorical_axis,
    apply_nice_linear_axis,
    errorbar_kwargs,
    place_legend_above,
    reference_line_kwargs,
    series_style,
)


def build_forest(
    label: object | None = None,
    estimate: object | None = None,
    interval: object | None = None,
    uncertainty_type: object | None = None,
) -> Figure:
    if label is None and estimate is None and interval is None and uncertainty_type is None:
        labels = ["Hybrid ODE", "Neural ODE", "ASM baseline", "Linear model"]
        estimates = np.array([0.84, 0.73, 0.59, 0.46])
        errors: np.ndarray = np.array([0.07, 0.09, 0.08, 0.11])
        uncertainty_label = "95% CI"
        limits = (0.25, 1.0)
    elif label is not None and estimate is not None and interval is not None and uncertainty_type:
        labels = [str(item) for item in label]  # type: ignore[union-attr]
        estimates = np.asarray(estimate, dtype=float)
        supplied = np.asarray(interval, dtype=float)
        if estimates.ndim != 1 or estimates.size != len(labels) or estimates.size < 1:
            raise ValueError("forest labels and estimates must be equal-length data")
        if supplied.shape == estimates.shape:
            errors = supplied
            lower = estimates - errors
            upper = estimates + errors
        elif supplied.shape == (estimates.size, 2):
            lower = supplied[:, 0]
            upper = supplied[:, 1]
            if np.any(lower > estimates) or np.any(upper < estimates):
                raise ValueError("forest interval bounds must contain each estimate")
            errors = np.vstack((estimates - lower, upper - estimates))
        else:
            raise ValueError("forest interval must be half-widths or lower/upper pairs")
        uncertainty_label = str(uncertainty_type)
        padding = max(float(upper.max() - lower.min()) * 0.05, 0.05)
        limits = (float(lower.min()) - padding, float(upper.max()) + padding)
    else:
        raise ValueError("forest requires label, estimate, interval, and uncertainty_type together")
    positions = np.arange(len(labels))
    figure, axis = plt.subplots()
    axis.errorbar(estimates, positions, xerr=errors, **errorbar_kwargs())
    axis.axvline(0.5, **reference_line_kwargs())
    axis.set_yticks(positions, labels)
    axis.set(xlabel=f"Effect estimate ({uncertainty_label})")
    axis.invert_yaxis()
    apply_axis_contract(axis, surface="open")
    apply_categorical_axis(axis, coordinate="y")
    apply_nice_linear_axis(axis, *limits, coordinate="x")
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


def build_coefficient() -> Figure:
    labels = ["Intercept", "Temperature", "Loading", "Oxygen"]
    positions = np.arange(len(labels))
    estimates = np.array([[0.18, 0.42, -0.31, 0.27], [0.11, 0.36, -0.22, 0.34]])
    errors = np.array([[0.08, 0.10, 0.09, 0.08], [0.07, 0.08, 0.08, 0.09]])
    figure, axis = plt.subplots()
    for index, label in enumerate(("Mechanistic", "Hybrid")):
        offset = (index - 0.5) * 0.16
        style = series_style(index)
        axis.errorbar(
            estimates[index],
            positions + offset,
            xerr=errors[index],
            label=label,
            color=style["color"],
            marker=style["marker"],
            linestyle="none",
            **{key: value for key, value in errorbar_kwargs().items() if key != "marker"},
        )
    axis.axvline(0.0, **reference_line_kwargs())
    axis.set_yticks(positions, labels)
    axis.set(xlabel="Coefficient estimate (95% CI)")
    axis.invert_yaxis()
    apply_axis_contract(axis, surface="open")
    apply_categorical_axis(axis, coordinate="y")
    apply_nice_linear_axis(axis, -0.5, 0.6, coordinate="x")
    place_legend_above(axis)
    return figure


BUILDERS = {
    "forest": build_forest,
    "point_interval": build_point_interval,
    "coefficient": build_coefficient,
}
