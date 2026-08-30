from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from axiomfig.ornaments import request_legend
from axiomfig.style import (
    add_bar_value_labels,
    apply_axis_contract,
    apply_categorical_axis,
    apply_nice_linear_axis,
    apply_scatter_contract,
    bar_width,
)


def _vertical_axes(axis: Axes, labels: list[str], upper: float) -> None:
    axis.set_xticks(np.arange(len(labels)), labels)
    apply_axis_contract(axis, surface="open")
    apply_categorical_axis(axis, coordinate="x")
    apply_nice_linear_axis(axis, 0.0, upper, coordinate="y")


def _pivot(
    category: object,
    value: object,
    series: object,
) -> tuple[list[str], list[str], np.ndarray]:
    categories = np.asarray(category, dtype=object).astype(str)
    values = np.asarray(value, dtype=float)
    groups = np.asarray(series, dtype=object).astype(str)
    labels = list(dict.fromkeys(categories))
    series_labels = list(dict.fromkeys(groups))
    matrix = np.zeros((len(series_labels), len(labels)), dtype=float)
    seen = np.zeros_like(matrix, dtype=bool)
    for category_name, selected_value, group_name in zip(categories, values, groups, strict=True):
        row = series_labels.index(group_name)
        column = labels.index(category_name)
        if seen[row, column]:
            raise ValueError("bar long-form data must contain one value per category and series")
        matrix[row, column] = selected_value
        seen[row, column] = True
    if not np.all(seen):
        raise ValueError("bar long-form data must form a complete category by series grid")
    return labels, series_labels, matrix


def build_vertical(
    category: object | None = None,
    value: object | None = None,
    value_labels: object | None = None,
    ylabel: object | None = None,
) -> Figure:
    if category is None and value is None:
        labels = ["COD", "Nitrogen", "Phosphorus"]
        values = np.array([0.84, 0.76, 0.71])
    elif category is not None and value is not None:
        labels = [str(item) for item in category]  # type: ignore[union-attr]
        values = np.asarray(value, dtype=float)
        if values.ndim != 1 or len(labels) != values.size or values.size < 1:
            raise ValueError("bar category and value must be equal-length one-dimensional data")
    else:
        raise ValueError("bar requires category and value together")
    figure, axis = plt.subplots()
    bars = axis.bar(np.arange(len(labels)), values, width=bar_width())
    axis.set(ylabel="Validation score (-)" if ylabel is None else str(ylabel))
    upper = max(float(values.max()) * 1.18, 0.1)
    _vertical_axes(axis, labels, upper)
    if value_labels is not False:
        add_bar_value_labels(axis, [bars])
    return figure


def build_horizontal(
    category: object | None = None,
    value: object | None = None,
    value_labels: object | None = None,
    xlabel: object | None = None,
) -> Figure:
    if category is None and value is None:
        labels = ["Mechanistic", "Neural ODE", "Hybrid ODE"]
        values = np.array([0.66, 0.78, 0.87])
    elif category is not None and value is not None:
        labels = [str(item) for item in category]  # type: ignore[union-attr]
        values = np.asarray(value, dtype=float)
    else:
        raise ValueError("horizontal bar requires category and value together")
    positions = np.arange(len(labels))
    figure, axis = plt.subplots()
    bars = axis.barh(positions, values, height=bar_width())
    axis.set_yticks(positions, labels)
    axis.set(xlabel="Explained variance (-)" if xlabel is None else str(xlabel))
    apply_axis_contract(axis, surface="open")
    apply_categorical_axis(axis, coordinate="y")
    apply_nice_linear_axis(axis, 0.0, max(float(values.max()) * 1.18, 0.1), coordinate="x")
    if value_labels is not False:
        add_bar_value_labels(axis, [bars])
    return figure


def build_grouped(
    category: object | None = None,
    value: object | None = None,
    group: object | None = None,
    error: object | None = None,
    uncertainty_type: object | None = None,
    value_labels: object | None = None,
) -> Figure:
    if category is None and value is None and group is None:
        labels = ["COD", "Nitrogen", "Phosphorus"]
        groups = ["Mechanistic", "Hybrid"]
        values = np.array([[0.72, 0.67, 0.61], [0.84, 0.76, 0.71]])
        errors = None
    elif category is not None and value is not None and group is not None:
        labels, groups, values = _pivot(category, value, group)
        if error is None:
            errors = None
        else:
            error_values = np.asarray(error, dtype=float)
            if error_values.ndim == 1:
                _, _, errors = _pivot(category, error_values, group)
            else:
                _, _, lower_errors = _pivot(category, error_values[:, 0], group)
                _, _, upper_errors = _pivot(category, error_values[:, 1], group)
                errors = np.stack((lower_errors, upper_errors), axis=1)
        if errors is not None and uncertainty_type is None:
            raise ValueError("uncertainty_type is required with grouped bar errors")
    else:
        raise ValueError("grouped bar requires category, value, and group together")
    positions = np.arange(len(labels))
    width = bar_width(len(groups))
    figure, axis = plt.subplots()
    containers = []
    for index, label in enumerate(groups):
        offset = (index - (len(groups) - 1) / 2) * width
        containers.append(
            axis.bar(
                positions + offset,
                values[index],
                width,
                label=label,
                yerr=None if errors is None else errors[index],
            )
        )
    suffix = "" if uncertainty_type is None else f" ({uncertainty_type})"
    axis.set(ylabel=f"Validation score{suffix}")
    _vertical_axes(axis, labels, max(float(values.max()) * 1.2, 0.1))
    if value_labels is not False:
        add_bar_value_labels(axis, containers)
    request_legend(axis)
    return figure


def _stacked(
    *,
    category: object | None,
    value: object | None,
    component: object | None,
    normalized: bool,
    normalization: object | None,
    value_labels: object | None,
    ylabel: object | None,
) -> Figure:
    if category is None and value is None and component is None:
        labels = ["Baseline", "Calibrated", "Hybrid"]
        components = ["Mechanistic", "Data-driven"]
        values = np.array([[0.42, 0.50, 0.57], [0.25, 0.28, 0.31]])
        if normalized:
            values = values / values.sum(axis=0)
    elif category is not None and value is not None and component is not None:
        labels, components, values = _pivot(category, value, component)
        if normalized:
            if normalization == "normalize":
                totals = values.sum(axis=0)
                if np.any(totals <= 0):
                    raise ValueError("normalized stacks require positive category totals")
                values = values / totals
            elif not np.allclose(values.sum(axis=0), 1.0, atol=1e-8):
                raise ValueError("proportion stacks must sum to one for each category")
    else:
        raise ValueError("stacked bar requires category, value, and component together")
    positions = np.arange(len(labels))
    figure, axis = plt.subplots()
    width = bar_width()
    bottom = np.zeros(len(labels), dtype=float)
    containers = []
    for label, selected in zip(components, values, strict=True):
        containers.append(axis.bar(positions, selected, width=width, bottom=bottom, label=label))
        bottom += selected
    default_label = "Normalized contribution (-)" if normalized else "Explained contribution (-)"
    axis.set(ylabel=default_label if ylabel is None else str(ylabel))
    _vertical_axes(axis, labels, 1.0 if normalized else max(float(bottom.max()) * 1.12, 0.1))
    if value_labels is not False:
        add_bar_value_labels(axis, containers)
    request_legend(axis)
    return figure


def build_stacked(
    category: object | None = None,
    value: object | None = None,
    component: object | None = None,
    value_labels: object | None = None,
    ylabel: object | None = None,
) -> Figure:
    return _stacked(
        category=category,
        value=value,
        component=component,
        normalized=False,
        normalization=None,
        value_labels=value_labels,
        ylabel=ylabel,
    )


def build_normalized_stacked(
    category: object | None = None,
    value: object | None = None,
    component: object | None = None,
    normalization: object | None = None,
    value_labels: object | None = None,
    ylabel: object | None = None,
) -> Figure:
    return _stacked(
        category=category,
        value=value,
        component=component,
        normalized=True,
        normalization=normalization,
        value_labels=value_labels,
        ylabel=ylabel,
    )


def build_dot(
    category: object | None = None,
    value: object | None = None,
    value_labels: object | None = None,
    ylabel: object | None = None,
) -> Figure:
    if category is None and value is None:
        labels = ["Mechanistic", "Neural ODE", "Hybrid ODE"]
        values = np.array([0.66, 0.78, 0.87])
    elif category is not None and value is not None:
        labels = [str(item) for item in category]  # type: ignore[union-attr]
        values = np.asarray(value, dtype=float)
    else:
        raise ValueError("dot bar requires category and value together")
    positions = np.arange(len(labels))
    figure, axis = plt.subplots()
    axis.vlines(positions, 0.0, values)
    collection = axis.scatter(positions, values)
    apply_scatter_contract(collection)
    axis.set_xticks(positions, labels)
    axis.set(ylabel="Explained variance (-)" if ylabel is None else str(ylabel))
    apply_axis_contract(axis, surface="open")
    apply_categorical_axis(axis, coordinate="x")
    apply_nice_linear_axis(axis, 0.0, max(float(values.max()) * 1.15, 0.1), coordinate="y")
    if value_labels is True:
        for position, selected in zip(positions, values, strict=True):
            axis.text(position, selected, f"{selected:.2f}", ha="center", va="bottom")
    return figure


BUILDERS = {
    "vertical": build_vertical,
    "horizontal": build_horizontal,
    "grouped": build_grouped,
    "stacked": build_stacked,
    "normalized_stacked": build_normalized_stacked,
    "dot": build_dot,
}
