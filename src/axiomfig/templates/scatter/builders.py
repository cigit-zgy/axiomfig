from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure

from axiomfig.colors import semantic_colormap
from axiomfig.template_helpers import (
    apply_axis_contract,
    apply_filled_collection_contract,
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


def build_simple(x: object | None = None, y: object | None = None) -> Figure:
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
        x_padding = max(float(np.ptp(values_x)) * 0.04, 0.1)
        y_padding = max(float(np.ptp(values_y)) * 0.04, 0.1)
        limits = (
            (float(values_x.min()) - x_padding, float(values_x.max()) + x_padding),
            (float(values_y.min()) - y_padding, float(values_y.max()) + y_padding),
        )
    else:
        raise ValueError("scatter requires x and y together")
    figure, axis = plt.subplots()
    collection = axis.scatter(values_x, values_y)
    apply_scatter_contract(collection)
    axis.set(xlabel="Hydraulic loading", ylabel="Observed response")
    _open(axis, *limits)
    return figure


def build_grouped(
    x: object | None = None,
    y: object | None = None,
    group: object | None = None,
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
        x_padding = max(float(np.ptp(all_x)) * 0.04, 0.1)
        y_padding = max(float(np.ptp(all_y)) * 0.04, 0.1)
        limits = (
            (float(all_x.min()) - x_padding, float(all_x.max()) + x_padding),
            (float(all_y.min()) - y_padding, float(all_y.max()) + y_padding),
        )
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
    axis.set(xlabel="Observed concentration (mg/L)", ylabel="Predicted concentration (mg/L)")
    _open(axis, *limits)
    place_legend_above(axis)
    return figure


def build_regression() -> Figure:
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


def build_parity(observed: object | None = None, predicted: object | None = None) -> Figure:
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
        limits = (lower - padding, upper + padding)
    else:
        raise ValueError("parity requires observed and predicted together")
    figure, axis = plt.subplots()
    collection = axis.scatter(observed_values, predicted_values)
    apply_scatter_contract(collection)
    axis.plot(limits, limits, **reference_line_kwargs())
    axis.set(xlabel="Observed concentration (mg/L)", ylabel="Predicted concentration (mg/L)")
    _open(axis, limits, limits)
    return figure


def build_bubble() -> Figure:
    rng = np.random.default_rng(101)
    x = np.linspace(2.0, 28.0, 28)
    y = 0.72 * x + 3.0 + rng.normal(0.0, 1.35, x.size)
    magnitude = np.linspace(0.55, 1.75, x.size)
    base_size = float(plt.rcParams["lines.markersize"]) ** 2
    figure, axis = plt.subplots()
    collection = axis.scatter(x, y, s=base_size * magnitude)
    apply_scatter_contract(collection)
    collection.set_sizes(base_size * magnitude)
    axis.set(xlabel="Substrate loading", ylabel="Process response")
    _open(axis, (0.0, 30.0), (0.0, 30.0))
    return figure


def build_hexbin() -> Figure:
    rng = np.random.default_rng(107)
    x = rng.normal(12.0, 3.4, 420)
    y = 0.68 * x + rng.normal(2.5, 2.0, x.size)
    figure, axis = plt.subplots()
    collection = axis.hexbin(
        x,
        y,
        gridsize=18,
        mincnt=1,
        cmap=semantic_colormap("sequential"),
    )
    apply_filled_collection_contract(collection)
    axis.set(xlabel="Observed loading", ylabel="Response density")
    _open(axis, (2.0, 22.0), (0.0, 20.0))
    return figure


BUILDERS = {
    "simple": build_simple,
    "grouped": build_grouped,
    "regression": build_regression,
    "parity": build_parity,
    "bubble": build_bubble,
    "hexbin": build_hexbin,
}
