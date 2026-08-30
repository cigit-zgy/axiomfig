from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure

from axiomfig.ornaments import request_legend
from axiomfig.style import (
    apply_axis_contract,
    apply_filled_collection_contract,
    apply_nice_linear_axis,
    apply_scatter_contract,
    reference_line_kwargs,
    semantic_colormap,
    series_style,
)


def _open(axis: plt.Axes, xlim: tuple[float, float], ylim: tuple[float, float]) -> None:
    apply_axis_contract(axis, surface="open")
    apply_nice_linear_axis(axis, *xlim, coordinate="x")
    apply_nice_linear_axis(axis, *ylim, coordinate="y")


def _limits(x: np.ndarray, y: np.ndarray) -> tuple[tuple[float, float], tuple[float, float]]:
    x_padding = max(float(np.ptp(x)) * 0.04, 0.1)
    y_padding = max(float(np.ptp(y)) * 0.04, 0.1)
    return (
        (float(x.min()) - x_padding, float(x.max()) + x_padding),
        (float(y.min()) - y_padding, float(y.max()) + y_padding),
    )


def build_simple(
    x: object | None = None,
    y: object | None = None,
    xlabel: object | None = None,
    ylabel: object | None = None,
) -> Figure:
    if x is None and y is None:
        limits = ((0.0, 24.0), (-2.0, 18.0))
        rng = np.random.default_rng(23)
        values_x = np.linspace(0.0, 24.0, 48)
        values_y = 0.6 * values_x + rng.normal(0.0, 1.4, values_x.size)
    elif x is not None and y is not None:
        values_x = np.asarray(x, dtype=float)
        values_y = np.asarray(y, dtype=float)
        if values_x.ndim != 1 or values_x.shape != values_y.shape or values_x.size < 2:
            raise ValueError("scatter x and y must be equal-length one-dimensional data")
        limits = _limits(values_x, values_y)
    else:
        raise ValueError("scatter requires x and y together")
    figure, axis = plt.subplots()
    collection = axis.scatter(values_x, values_y)
    apply_scatter_contract(collection)
    axis.set(
        xlabel="Hydraulic loading" if xlabel is None else str(xlabel),
        ylabel="Observed response" if ylabel is None else str(ylabel),
    )
    _open(axis, *limits)
    return figure


def build_grouped(
    x: object | None = None,
    y: object | None = None,
    group: object | None = None,
    xlabel: object | None = None,
    ylabel: object | None = None,
) -> Figure:
    figure, axis = plt.subplots()
    if x is None and y is None and group is None:
        rng = np.random.default_rng(31)
        limits = ((0.0, 30.0), (0.0, 30.0))
        series = []
        for index, label in enumerate(("Train", "Validation", "Test")):
            values_x = np.linspace(2.0, 28.0, 24)
            values_y = (
                values_x + rng.normal(0.0, 1.0 + 0.35 * index, values_x.size) + (index - 1) * 0.7
            )
            series.append((label, values_x, values_y))
    elif x is not None and y is not None and group is not None:
        values_x = np.asarray(x, dtype=float)
        values_y = np.asarray(y, dtype=float)
        groups = np.asarray(group, dtype=object)
        if values_x.ndim != 1 or values_x.shape != values_y.shape or values_x.shape != groups.shape:
            raise ValueError(
                "grouped scatter x, y, and group must be equal-length one-dimensional data"
            )
        labels = tuple(dict.fromkeys(str(value) for value in groups))
        series = [
            (label, values_x[groups.astype(str) == label], values_y[groups.astype(str) == label])
            for label in labels
        ]
        all_x = np.concatenate([item_x for _, item_x, _ in series])
        all_y = np.concatenate([item_y for _, _, item_y in series])
        limits = _limits(all_x, all_y)
    else:
        raise ValueError("grouped scatter requires x, y, and group together")
    for index, (label, values_x, values_y) in enumerate(series):
        style = series_style(index)
        collection = axis.scatter(
            values_x,
            values_y,
            label=label,
            color=style["color"],
            marker=style["marker"],
        )
        apply_scatter_contract(collection)
    axis.set(
        xlabel="Observed concentration (mg/L)" if xlabel is None else str(xlabel),
        ylabel="Predicted concentration (mg/L)" if ylabel is None else str(ylabel),
    )
    _open(axis, *limits)
    request_legend(axis)
    return figure


def build_regression(
    x: object | None = None,
    y: object | None = None,
    fitted: object | None = None,
    fit_label: object | None = None,
    xlabel: object | None = None,
    ylabel: object | None = None,
) -> Figure:
    if x is None and y is None and fitted is None:
        rng = np.random.default_rng(59)
        values_x = np.linspace(0.5, 19.0, 45)
        values_y = np.clip(2.1 + 0.74 * values_x + rng.normal(0.0, 1.15, values_x.size), 0.8, 19.0)
        fitted_values = np.polyval(np.polyfit(values_x, values_y, 1), values_x)
        limits = ((0.0, 20.0), (0.0, 20.0))
        annotation = r"$R^2 = 0.94$"
    elif x is not None and y is not None and fitted is not None:
        values_x = np.asarray(x, dtype=float)
        values_y = np.asarray(y, dtype=float)
        fitted_values = np.asarray(fitted, dtype=float)
        limits = _limits(values_x, np.concatenate((values_y, fitted_values)))
        annotation = None if fit_label is None else str(fit_label)
    else:
        raise ValueError("regression requires x, y, and a precomputed fitted series")
    figure, axis = plt.subplots()
    collection = axis.scatter(values_x, values_y)
    apply_scatter_contract(collection)
    axis.plot(values_x, fitted_values)
    if annotation is not None:
        axis.text(0.04, 0.92, annotation, transform=axis.transAxes)
    axis.set(
        xlabel="Influent load" if xlabel is None else str(xlabel),
        ylabel="Effluent response" if ylabel is None else str(ylabel),
    )
    _open(axis, *limits)
    return figure


def build_parity(
    observed: object | None = None,
    predicted: object | None = None,
    identity_limits: object | None = None,
    xlabel: object | None = None,
    ylabel: object | None = None,
) -> Figure:
    if observed is None and predicted is None:
        rng = np.random.default_rng(43)
        observed_values = np.linspace(2.0, 28.0, 42)
        predicted_values = observed_values + rng.normal(0.0, 1.35, observed_values.size)
        limits = (0.0, 30.0)
    elif observed is not None and predicted is not None:
        observed_values = np.asarray(observed, dtype=float)
        predicted_values = np.asarray(predicted, dtype=float)
        if (
            observed_values.ndim != 1
            or observed_values.shape != predicted_values.shape
            or observed_values.size < 2
        ):
            raise ValueError(
                "parity observed and predicted must be equal-length one-dimensional data"
            )
        lower = min(float(observed_values.min()), float(predicted_values.min()))
        upper = max(float(observed_values.max()), float(predicted_values.max()))
        padding = max((upper - lower) * 0.04, 0.1)
        limits = (
            (lower - padding, upper + padding)
            if identity_limits is None
            else tuple(float(item) for item in identity_limits)
        )
    else:
        raise ValueError("parity requires observed and predicted together")
    figure, axis = plt.subplots()
    collection = axis.scatter(observed_values, predicted_values)
    apply_scatter_contract(collection)
    axis.plot(limits, limits, **reference_line_kwargs())
    axis.set(
        xlabel="Observed concentration (mg/L)" if xlabel is None else str(xlabel),
        ylabel="Predicted concentration (mg/L)" if ylabel is None else str(ylabel),
    )
    _open(axis, limits, limits)
    return figure


def build_bubble(
    x: object | None = None,
    y: object | None = None,
    size: object | None = None,
    group: object | None = None,
    size_label: object | None = None,
    xlabel: object | None = None,
    ylabel: object | None = None,
) -> Figure:
    if x is None and y is None and size is None:
        rng = np.random.default_rng(101)
        values_x = np.linspace(2.0, 28.0, 28)
        values_y = 0.72 * values_x + 3.0 + rng.normal(0.0, 1.35, values_x.size)
        magnitude = np.linspace(0.55, 1.75, values_x.size)
        groups = None
        limits = ((0.0, 30.0), (0.0, 30.0))
    elif x is not None and y is not None and size is not None:
        values_x = np.asarray(x, dtype=float)
        values_y = np.asarray(y, dtype=float)
        magnitude = np.asarray(size, dtype=float)
        groups = None if group is None else np.asarray(group, dtype=object).astype(str)
        limits = _limits(values_x, values_y)
    else:
        raise ValueError("bubble requires x, y, and size together")
    base_size = float(plt.rcParams["lines.markersize"]) ** 2
    figure, axis = plt.subplots()
    if groups is None:
        collection = axis.scatter(values_x, values_y, s=base_size * magnitude)
        apply_scatter_contract(collection)
        collection.set_sizes(base_size * magnitude)
    else:
        for index, label in enumerate(dict.fromkeys(groups)):
            mask = groups == label
            style = series_style(index)
            collection = axis.scatter(
                values_x[mask],
                values_y[mask],
                s=base_size * magnitude[mask],
                label=label,
                color=style["color"],
                marker=style["marker"],
            )
            apply_scatter_contract(collection)
            collection.set_sizes(base_size * magnitude[mask])
        request_legend(axis)
    if size_label is not None:
        axis.text(0.04, 0.92, str(size_label), transform=axis.transAxes)
    axis.set(
        xlabel="Substrate loading" if xlabel is None else str(xlabel),
        ylabel="Process response" if ylabel is None else str(ylabel),
    )
    _open(axis, *limits)
    return figure


def build_hexbin(
    x: object | None = None,
    y: object | None = None,
    gridsize: object | None = None,
    count_label: object | None = None,
    xlabel: object | None = None,
    ylabel: object | None = None,
) -> Figure:
    if x is None and y is None:
        rng = np.random.default_rng(107)
        values_x = rng.normal(12.0, 3.4, 420)
        values_y = 0.68 * values_x + rng.normal(2.5, 2.0, values_x.size)
        limits = ((2.0, 22.0), (0.0, 20.0))
    elif x is not None and y is not None:
        values_x = np.asarray(x, dtype=float)
        values_y = np.asarray(y, dtype=float)
        limits = _limits(values_x, values_y)
    else:
        raise ValueError("hexbin requires x and y together")
    figure, axis = plt.subplots()
    collection = axis.hexbin(
        values_x,
        values_y,
        gridsize=18 if gridsize is None else int(gridsize),
        mincnt=1,
        cmap=semantic_colormap("sequential"),
    )
    apply_filled_collection_contract(collection)
    axis.set(
        xlabel="Observed loading" if xlabel is None else str(xlabel),
        ylabel="Response density" if ylabel is None else str(ylabel),
    )
    if count_label is not None:
        axis.text(0.04, 0.92, str(count_label), transform=axis.transAxes)
    _open(axis, *limits)
    return figure


BUILDERS = {
    "simple": build_simple,
    "grouped": build_grouped,
    "regression": build_regression,
    "parity": build_parity,
    "bubble": build_bubble,
    "hexbin": build_hexbin,
}
