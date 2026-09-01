from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure

from axiomfig.ornaments import request_legend
from axiomfig.style import (
    apply_axis_contract,
    apply_nice_linear_axis,
    confidence_interval_kwargs,
    errorbar_kwargs,
    line_marker_kwargs,
    series_style,
)


def _open(axis: plt.Axes, xlim: tuple[float, float], ylim: tuple[float, float]) -> None:
    apply_axis_contract(axis, surface="open")
    apply_nice_linear_axis(axis, *xlim, coordinate="x")
    apply_nice_linear_axis(axis, *ylim, coordinate="y")


def _limits(x: np.ndarray, y: np.ndarray) -> tuple[tuple[float, float], tuple[float, float]]:
    x_padding = max(float(np.ptp(x)) * 0.03, 0.1)
    y_padding = max(float(np.ptp(y)) * 0.05, 0.05)
    return (
        (float(x.min()) - x_padding, float(x.max()) + x_padding),
        (float(y.min()) - y_padding, float(y.max()) + y_padding),
    )


def build_single(
    x: object | None = None,
    y: object | None = None,
    xlabel: object | None = None,
    ylabel: object | None = None,
) -> Figure:
    if x is None and y is None:
        limits = ((0.0, 12.0), (0.0, 1.0))
        values_x = np.linspace(0.0, 12.0, 81)
        values_y = 1.0 - np.exp(-values_x / 3.2)
    elif x is not None and y is not None:
        values_x = np.asarray(x, dtype=float)
        values_y = np.asarray(y, dtype=float)
        if values_x.ndim != 1 or values_x.shape != values_y.shape or values_x.size < 2:
            raise ValueError("line x and y must be equal-length one-dimensional data")
        limits = _limits(values_x, values_y)
    else:
        raise ValueError("line requires x and y together")
    figure, axis = plt.subplots()
    axis.plot(values_x, values_y)
    axis.set(
        xlabel="Time (d)" if xlabel is None else str(xlabel),
        ylabel="Normalized response (-)" if ylabel is None else str(ylabel),
    )
    _open(axis, *limits)
    return figure


def build_multi(
    x: object | None = None,
    series_values: object | None = None,
    series_labels: object | None = None,
    xlabel: object | None = None,
    ylabel: object | None = None,
) -> Figure:
    if x is None and series_values is None and series_labels is None:
        values_x = np.linspace(0.0, 12.0, 81)
        values = np.vstack(
            (
                1.0 - np.exp(-values_x / 3.0),
                0.93 * (1.0 - np.exp(-values_x / 4.1)),
                0.86 * (1.0 - np.exp(-values_x / 4.8)),
            )
        )
        labels: tuple[str, ...] = ("Hybrid model", "Mechanistic model", "Neural ODE")
        limits = ((0.0, 12.0), (0.0, 1.0))
    elif x is not None and series_values is not None and series_labels is not None:
        values_x = np.asarray(x, dtype=float)
        values = np.asarray(series_values, dtype=float)
        labels = tuple(str(item) for item in series_labels)  # type: ignore[union-attr]
        limits = _limits(values_x, values.ravel())
    else:
        raise ValueError("multi line requires x, series_values, and series_labels together")
    figure, axis = plt.subplots()
    for index, (selected, label) in enumerate(zip(values, labels, strict=True)):
        axis.plot(values_x, selected, label=label, markevery=10, **series_style(index))
    axis.set(
        xlabel="Time (d)" if xlabel is None else str(xlabel),
        ylabel="Normalized response (-)" if ylabel is None else str(ylabel),
    )
    _open(axis, *limits)
    request_legend(axis)
    return figure


def build_marker(
    x: object | None = None,
    y: object | None = None,
    xlabel: object | None = None,
    ylabel: object | None = None,
) -> Figure:
    if x is None and y is None:
        values_x = np.linspace(0.5, 9.5, 11)
        values_y = 0.18 + 0.07 * values_x
        limits = ((0.0, 10.0), (0.1, 0.95))
    elif x is not None and y is not None:
        values_x = np.asarray(x, dtype=float)
        values_y = np.asarray(y, dtype=float)
        limits = _limits(values_x, values_y)
    else:
        raise ValueError("marker line requires x and y together")
    figure, axis = plt.subplots()
    axis.plot(values_x, values_y, **line_marker_kwargs())
    axis.set(
        xlabel="Sampling day" if xlabel is None else str(xlabel),
        ylabel="Removal efficiency (-)" if ylabel is None else str(ylabel),
    )
    _open(axis, *limits)
    return figure


def build_confidence_band(
    x: object | None = None,
    estimate: object | None = None,
    lower: object | None = None,
    upper: object | None = None,
    uncertainty_type: object | None = None,
    xlabel: object | None = None,
    ylabel: object | None = None,
) -> Figure:
    if all(item is None for item in (x, estimate, lower, upper, uncertainty_type)):
        values_x = np.linspace(0.0, 12.0, 81)
        mean = 1.0 - np.exp(-values_x / 3.2)
        spread = 0.045 + 0.025 * np.exp(-values_x / 4.0)
        lower_values = mean - spread
        upper_values = mean + spread
        uncertainty = "95% CI"
        limits = ((0.0, 12.0), (0.0, 1.1))
    elif all(item is not None for item in (x, estimate, lower, upper, uncertainty_type)):
        values_x = np.asarray(x, dtype=float)
        mean = np.asarray(estimate, dtype=float)
        lower_values = np.asarray(lower, dtype=float)
        upper_values = np.asarray(upper, dtype=float)
        uncertainty = str(uncertainty_type)
        limits = _limits(values_x, np.concatenate((lower_values, upper_values)))
    else:
        raise ValueError("confidence band requires x, estimate, lower, upper, and uncertainty_type")
    figure, axis = plt.subplots()
    color = plt.rcParams["axes.prop_cycle"].by_key()["color"][0]
    axis.fill_between(values_x, lower_values, upper_values, **confidence_interval_kwargs(color))
    axis.plot(values_x, mean)
    axis.set(
        xlabel="Time (d)" if xlabel is None else str(xlabel),
        ylabel=f"Estimated response ({uncertainty})" if ylabel is None else str(ylabel),
    )
    _open(axis, *limits)
    return figure


def build_errorbar(
    x: object | None = None,
    estimate: object | None = None,
    error: object | None = None,
    uncertainty_type: object | None = None,
    xlabel: object | None = None,
    ylabel: object | None = None,
) -> Figure:
    if all(item is None for item in (x, estimate, error, uncertainty_type)):
        values_x = np.linspace(1.25, 5.75, 6)
        values_y = np.array([0.42, 0.51, 0.63, 0.70, 0.76, 0.79])
        errors = np.array([0.045, 0.052, 0.040, 0.036, 0.032, 0.030])
        uncertainty = "SE"
        limits = ((1.0, 6.0), (0.3, 0.9))
    elif all(item is not None for item in (x, estimate, error, uncertainty_type)):
        values_x = np.asarray(x, dtype=float)
        values_y = np.asarray(estimate, dtype=float)
        supplied_error = np.asarray(error, dtype=float)
        errors = supplied_error.T if supplied_error.ndim == 2 else supplied_error
        uncertainty = str(uncertainty_type)
        maximum_error = np.max(errors, axis=0) if errors.ndim == 2 else errors
        limits = _limits(
            values_x, np.concatenate((values_y - maximum_error, values_y + maximum_error))
        )
    else:
        raise ValueError("errorbar requires x, estimate, error, and uncertainty_type together")
    figure, axis = plt.subplots()
    axis.errorbar(values_x, values_y, yerr=errors, **errorbar_kwargs())
    axis.set(
        xlabel="Experiment" if xlabel is None else str(xlabel),
        ylabel=f"Estimated coefficient ({uncertainty})" if ylabel is None else str(ylabel),
    )
    _open(axis, *limits)
    return figure


def build_step(
    x: object | None = None,
    y: object | None = None,
    where: object | None = None,
    xlabel: object | None = None,
    ylabel: object | None = None,
) -> Figure:
    if x is None and y is None:
        values_x = np.arange(0.0, 13.0, 1.0)
        response = np.array(
            [0.08, 0.12, 0.20, 0.31, 0.39, 0.48, 0.56, 0.61, 0.69, 0.75, 0.81, 0.86, 0.89]
        )
        limits = ((0.0, 12.0), (0.0, 1.0))
    elif x is not None and y is not None:
        values_x = np.asarray(x, dtype=float)
        response = np.asarray(y, dtype=float)
        limits = _limits(values_x, response)
    else:
        raise ValueError("step requires x and y together")
    figure, axis = plt.subplots()
    axis.step(values_x, response, where="post" if where is None else str(where))
    axis.set(
        xlabel="Sampling interval" if xlabel is None else str(xlabel),
        ylabel="Cumulative response (-)" if ylabel is None else str(ylabel),
    )
    _open(axis, *limits)
    return figure


def build_area(
    x: object | None = None,
    y: object | None = None,
    baseline: object | None = None,
    xlabel: object | None = None,
    ylabel: object | None = None,
) -> Figure:
    if x is None and y is None:
        values_x = np.linspace(0.0, 12.0, 81)
        response = 0.15 + 0.72 * (1.0 - np.exp(-values_x / 3.8))
        selected_baseline: object = 0.0
        limits = ((0.0, 12.0), (0.0, 1.0))
    elif x is not None and y is not None:
        values_x = np.asarray(x, dtype=float)
        response = np.asarray(y, dtype=float)
        selected_baseline = 0.0 if baseline is None else baseline
        base_values = np.broadcast_to(np.asarray(selected_baseline, dtype=float), response.shape)
        limits = _limits(values_x, np.concatenate((response, base_values)))
    else:
        raise ValueError("area requires x and y together")
    figure, axis = plt.subplots()
    color = plt.rcParams["axes.prop_cycle"].by_key()["color"][0]
    axis.fill_between(values_x, selected_baseline, response, **confidence_interval_kwargs(color))
    axis.plot(values_x, response)
    axis.set(
        xlabel="Time (d)" if xlabel is None else str(xlabel),
        ylabel="Accumulated fraction (-)" if ylabel is None else str(ylabel),
    )
    _open(axis, *limits)
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
