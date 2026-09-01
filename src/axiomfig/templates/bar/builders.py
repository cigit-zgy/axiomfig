from __future__ import annotations

from collections.abc import Sequence

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.container import BarContainer
from matplotlib.figure import Figure

from axiomfig.ornaments import request_legend
from axiomfig.style import (
    add_bar_value_labels,
    apply_axis_contract,
    apply_bar_contract,
    apply_categorical_axis,
    apply_nice_linear_axis,
    apply_scatter_contract,
    bar_width,
)
from axiomfig.templates.bar.adapter import PROPORTION_ABSOLUTE_TOLERANCE
from axiomfig.templates.bar.geometry import error_endpoints, linear_limits


def _orientation(value: object | None, *, default: str = "vertical") -> str:
    selected = default if value is None else str(value)
    if selected not in {"vertical", "horizontal"}:
        raise ValueError("orientation must be vertical or horizontal")
    return selected


def _categorical_axes(
    axis: Axes,
    labels: Sequence[str],
    orientation: str,
    lower: float,
    upper: float,
) -> None:
    positions = np.arange(len(labels))
    apply_axis_contract(axis, surface="open")
    if orientation == "vertical":
        axis.set_xticks(positions, labels)
        apply_categorical_axis(axis, coordinate="x")
        apply_nice_linear_axis(axis, lower, upper, coordinate="y")
    else:
        axis.set_yticks(positions, labels)
        apply_categorical_axis(axis, coordinate="y")
        apply_nice_linear_axis(axis, lower, upper, coordinate="x")


def _set_axis_labels(
    axis: Axes,
    *,
    orientation: str,
    value_default: str,
    xlabel: object | None,
    ylabel: object | None,
    value_suffix: str = "",
) -> None:
    labels: dict[str, str] = {}
    if orientation == "vertical":
        if xlabel is not None:
            labels["xlabel"] = str(xlabel)
        labels["ylabel"] = (value_default if ylabel is None else str(ylabel)) + value_suffix
    else:
        labels["xlabel"] = (value_default if xlabel is None else str(xlabel)) + value_suffix
        if ylabel is not None:
            labels["ylabel"] = str(ylabel)
    axis.set(**labels)


def _finish_bars(
    axis: Axes, containers: Sequence[BarContainer], value_labels: object | None
) -> None:
    if value_labels is False:
        apply_bar_contract(containers)
    else:
        add_bar_value_labels(axis, containers)


def _bar(
    axis: Axes,
    positions: np.ndarray,
    values: np.ndarray,
    *,
    orientation: str,
    width: float,
    baseline: np.ndarray | float = 0.0,
    label: str | None = None,
    error: np.ndarray | None = None,
) -> BarContainer:
    if orientation == "vertical":
        return axis.bar(
            positions,
            values,
            width=width,
            bottom=baseline,
            label=label,
            yerr=error,
        )
    return axis.barh(
        positions,
        values,
        height=width,
        left=baseline,
        label=label,
        xerr=error,
    )


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
            raise ValueError("bar duplicate logical key for category, series")
        matrix[row, column] = selected_value
        seen[row, column] = True
    if not np.all(seen):
        raise ValueError("bar long-form data must form a complete category by series grid")
    return labels, series_labels, matrix


def _tensor(
    category: object,
    group: object,
    component: object,
    value: object,
) -> tuple[list[str], list[str], list[str], np.ndarray]:
    categories = np.asarray(category, dtype=object).astype(str)
    groups_array = np.asarray(group, dtype=object).astype(str)
    components_array = np.asarray(component, dtype=object).astype(str)
    values = np.asarray(value, dtype=float)
    labels = list(dict.fromkeys(categories))
    groups = list(dict.fromkeys(groups_array))
    components = list(dict.fromkeys(components_array))
    tensor = np.zeros((len(components), len(groups), len(labels)), dtype=float)
    seen = np.zeros_like(tensor, dtype=bool)
    for category_name, group_name, component_name, selected in zip(
        categories, groups_array, components_array, values, strict=True
    ):
        index = (
            components.index(component_name),
            groups.index(group_name),
            labels.index(category_name),
        )
        if seen[index]:
            raise ValueError("bar duplicate logical key for category, group, component")
        tensor[index] = selected
        seen[index] = True
    if not np.all(seen):
        raise ValueError("grouped-stacked data must form a complete category/group/component grid")
    return labels, groups, components, tensor


def build_simple(
    category: object | None = None,
    value: object | None = None,
    orientation: object | None = None,
    error: object | None = None,
    uncertainty_type: object | None = None,
    value_labels: object | None = None,
    xlabel: object | None = None,
    ylabel: object | None = None,
) -> Figure:
    if category is None and value is None:
        labels = ["COD", "Nitrogen", "Phosphorus"]
        values = np.array([0.84, 0.76, 0.71])
        errors = None
    elif category is not None and value is not None:
        labels = [str(item) for item in np.asarray(category, dtype=object).ravel()]
        values = np.asarray(value, dtype=float)
        if values.ndim != 1 or len(labels) != values.size or values.size < 1:
            raise ValueError("bar category and value must be equal-length one-dimensional data")
        errors = None if error is None else np.asarray(error, dtype=float)
        if errors is not None and errors.ndim == 2:
            errors = errors.T
        if errors is not None and uncertainty_type is None:
            raise ValueError("uncertainty_type is required with bar errors")
    else:
        raise ValueError("bar requires category and value together")
    if errors is None:
        bounds = linear_limits(values)
    else:
        raw_error = np.asarray(error, dtype=float)
        lower_error, upper_error = error_endpoints(values, raw_error)
        bounds = linear_limits(values, lower_error, upper_error)
    selected_orientation = _orientation(orientation)
    positions = np.arange(len(labels))
    figure, axis = plt.subplots()
    container = _bar(
        axis,
        positions,
        values,
        orientation=selected_orientation,
        width=bar_width(),
        error=errors,
    )
    suffix = "" if uncertainty_type is None else f" ({uncertainty_type})"
    _set_axis_labels(
        axis,
        orientation=selected_orientation,
        value_default="Value",
        xlabel=xlabel,
        ylabel=ylabel,
        value_suffix=suffix,
    )
    _categorical_axes(axis, labels, selected_orientation, *bounds)
    _finish_bars(axis, [container], value_labels)
    return figure


def build_vertical(**kwargs: object) -> Figure:
    return build_simple(orientation="vertical", **kwargs)


def build_horizontal(**kwargs: object) -> Figure:
    return build_simple(orientation="horizontal", **kwargs)


def build_grouped(
    category: object | None = None,
    value: object | None = None,
    group: object | None = None,
    orientation: object | None = None,
    error: object | None = None,
    uncertainty_type: object | None = None,
    value_labels: object | None = None,
    xlabel: object | None = None,
    ylabel: object | None = None,
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
    if errors is None:
        bounds = linear_limits(values)
    else:
        raw_values = np.asarray(value, dtype=float)
        raw_error = np.asarray(error, dtype=float)
        lower_error, upper_error = error_endpoints(raw_values, raw_error)
        bounds = linear_limits(raw_values, lower_error, upper_error)
    selected_orientation = _orientation(orientation)
    positions = np.arange(len(labels))
    width = bar_width(len(groups))
    figure, axis = plt.subplots()
    containers: list[BarContainer] = []
    for index, label in enumerate(groups):
        offset = (index - (len(groups) - 1) / 2) * width
        containers.append(
            _bar(
                axis,
                positions + offset,
                values[index],
                orientation=selected_orientation,
                width=width,
                label=label,
                error=None if errors is None else errors[index],
            )
        )
    suffix = "" if uncertainty_type is None else f" ({uncertainty_type})"
    _set_axis_labels(
        axis,
        orientation=selected_orientation,
        value_default="Value",
        xlabel=xlabel,
        ylabel=ylabel,
        value_suffix=suffix,
    )
    _categorical_axes(axis, labels, selected_orientation, *bounds)
    _finish_bars(axis, containers, value_labels)
    request_legend(axis)
    return figure


def _stacked(
    *,
    category: object | None,
    value: object | None,
    component: object | None,
    normalized: bool,
    normalization: object | None,
    orientation: object | None,
    value_labels: object | None,
    xlabel: object | None,
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
            if np.any(values < 0):
                raise ValueError("normalized stacks require non-negative values")
            if normalization == "normalize":
                totals = values.sum(axis=0)
                if np.any(totals <= 0):
                    raise ValueError("normalized stacks require positive category totals")
                values = values / totals
            elif not np.allclose(
                values.sum(axis=0),
                1.0,
                atol=PROPORTION_ABSOLUTE_TOLERANCE,
                rtol=0.0,
            ):
                raise ValueError("proportion stacks must sum to one for each category")
    else:
        raise ValueError("stacked bar requires category, value, and component together")
    selected_orientation = _orientation(orientation)
    positions = np.arange(len(labels))
    figure, axis = plt.subplots()
    bottom = np.zeros(len(labels), dtype=float)
    containers: list[BarContainer] = []
    for label, selected in zip(components, values, strict=True):
        containers.append(
            _bar(
                axis,
                positions,
                selected,
                orientation=selected_orientation,
                width=bar_width(),
                baseline=bottom,
                label=label,
            )
        )
        bottom += selected
    axis_label = "Proportion" if normalized else "Value"
    _set_axis_labels(
        axis,
        orientation=selected_orientation,
        value_default=axis_label,
        xlabel=xlabel,
        ylabel=ylabel,
    )
    bounds = (0.0, 1.0) if normalized else linear_limits(bottom)
    _categorical_axes(axis, labels, selected_orientation, *bounds)
    _finish_bars(axis, containers, value_labels)
    request_legend(axis)
    return figure


def build_stacked(
    category: object | None = None,
    value: object | None = None,
    component: object | None = None,
    orientation: object | None = None,
    value_labels: object | None = None,
    xlabel: object | None = None,
    ylabel: object | None = None,
) -> Figure:
    return _stacked(
        category=category,
        value=value,
        component=component,
        normalized=False,
        normalization=None,
        orientation=orientation,
        value_labels=value_labels,
        xlabel=xlabel,
        ylabel=ylabel,
    )


def build_normalized_stacked(
    category: object | None = None,
    value: object | None = None,
    component: object | None = None,
    normalization: object | None = None,
    orientation: object | None = None,
    value_labels: object | None = None,
    xlabel: object | None = None,
    ylabel: object | None = None,
) -> Figure:
    return _stacked(
        category=category,
        value=value,
        component=component,
        normalized=True,
        normalization=normalization,
        orientation=orientation,
        value_labels=value_labels,
        xlabel=xlabel,
        ylabel=ylabel,
    )


def build_grouped_stacked(
    category: object | None = None,
    value: object | None = None,
    group: object | None = None,
    component: object | None = None,
    orientation: object | None = None,
    value_labels: object | None = None,
    xlabel: object | None = None,
    ylabel: object | None = None,
) -> Figure:
    if category is None and value is None and group is None and component is None:
        labels = ["Site A", "Site B"]
        groups = ["Control", "Treatment"]
        components = ["Soluble", "Particulate"]
        values = np.array([[[2.0, 2.6], [2.5, 3.1]], [[1.0, 1.2], [1.4, 1.6]]])
    elif all(item is not None for item in (category, value, group, component)):
        labels, groups, components, values = _tensor(category, group, component, value)
    else:
        raise ValueError("grouped-stacked bar requires category, group, component, and value")
    selected_orientation = _orientation(orientation)
    positions = np.arange(len(labels))
    width = bar_width(len(groups))
    figure, axis = plt.subplots()
    bottom = np.zeros((len(groups), len(labels)), dtype=float)
    containers: list[BarContainer] = []
    for component_index, component_label in enumerate(components):
        for group_index, group_label in enumerate(groups):
            offset = (group_index - (len(groups) - 1) / 2) * width
            container = _bar(
                axis,
                positions + offset,
                values[component_index, group_index],
                orientation=selected_orientation,
                width=width,
                baseline=bottom[group_index],
                label=f"{group_label} · {component_label}",
            )
            containers.append(container)
            bottom[group_index] += values[component_index, group_index]
    _set_axis_labels(
        axis,
        orientation=selected_orientation,
        value_default="Value",
        xlabel=xlabel,
        ylabel=ylabel,
    )
    _categorical_axes(axis, labels, selected_orientation, *linear_limits(bottom))
    _finish_bars(axis, containers, value_labels)
    request_legend(axis)
    return figure


def build_diverging_stacked(
    category: object | None = None,
    value: object | None = None,
    component: object | None = None,
    orientation: object | None = None,
    value_labels: object | None = None,
    xlabel: object | None = None,
    ylabel: object | None = None,
) -> Figure:
    if category is None and value is None and component is None:
        labels = ["Site A", "Site B", "Site C"]
        components = ["Increase", "Decrease", "Recovery"]
        values = np.array([[2.0, 3.0, 2.5], [-1.0, -2.0, -1.5], [1.2, 0.8, 1.1]])
    elif category is not None and value is not None and component is not None:
        labels, components, values = _pivot(category, value, component)
    else:
        raise ValueError("diverging-stacked bar requires category, component, and value")
    selected_orientation = _orientation(orientation)
    positions = np.arange(len(labels))
    positive = np.zeros(len(labels), dtype=float)
    negative = np.zeros(len(labels), dtype=float)
    containers: list[BarContainer] = []
    figure, axis = plt.subplots()
    for label, selected in zip(components, values, strict=True):
        lower = np.where(selected >= 0, positive, negative + selected)
        height = np.abs(selected)
        containers.append(
            _bar(
                axis,
                positions,
                height,
                orientation=selected_orientation,
                width=bar_width(),
                baseline=lower,
                label=label,
            )
        )
        positive += np.maximum(selected, 0)
        negative += np.minimum(selected, 0)
    _set_axis_labels(
        axis,
        orientation=selected_orientation,
        value_default="Signed value",
        xlabel=xlabel,
        ylabel=ylabel,
    )
    _categorical_axes(axis, labels, selected_orientation, *linear_limits(negative, positive))
    _finish_bars(axis, containers, value_labels)
    request_legend(axis)
    return figure


def build_range(
    category: object | None = None,
    lower: object | None = None,
    upper: object | None = None,
    orientation: object | None = None,
    value_labels: object | None = None,
    xlabel: object | None = None,
    ylabel: object | None = None,
) -> Figure:
    if category is None and lower is None and upper is None:
        labels = ["Low flow", "Nominal", "High flow"]
        lower_values = np.array([1.2, 1.8, 2.1])
        upper_values = np.array([2.4, 3.0, 3.6])
    elif category is not None and lower is not None and upper is not None:
        labels = [str(item) for item in np.asarray(category, dtype=object).ravel()]
        lower_values = np.asarray(lower, dtype=float)
        upper_values = np.asarray(upper, dtype=float)
    else:
        raise ValueError("range bar requires category, lower, and upper")
    selected_orientation = _orientation(orientation)
    positions = np.arange(len(labels))
    figure, axis = plt.subplots()
    container = _bar(
        axis,
        positions,
        upper_values - lower_values,
        orientation=selected_orientation,
        width=bar_width(),
        baseline=lower_values,
    )
    _set_axis_labels(
        axis,
        orientation=selected_orientation,
        value_default="Range",
        xlabel=xlabel,
        ylabel=ylabel,
    )
    _categorical_axes(
        axis, labels, selected_orientation, *linear_limits(lower_values, upper_values)
    )
    _finish_bars(axis, [container], value_labels)
    return figure


def build_mirrored(
    category: object | None = None,
    value: object | None = None,
    side: object | None = None,
    mirror_side: object | None = None,
    orientation: object | None = None,
    value_labels: object | None = None,
    xlabel: object | None = None,
    ylabel: object | None = None,
) -> Figure:
    if category is None and value is None and side is None and mirror_side is None:
        category = ["0-9", "10-19", "20-29", "0-9", "10-19", "20-29"]
        side = ["Left", "Left", "Left", "Right", "Right", "Right"]
        value = [12.0, 18.0, 15.0, 11.0, 16.0, 17.0]
        mirror_side = "Left"
    elif not all(item is not None for item in (category, value, side, mirror_side)):
        raise ValueError("mirrored bar requires category, side, value, and mirror_side")
    labels, sides, values = _pivot(category, value, side)
    if len(sides) != 2 or str(mirror_side) not in sides:
        raise ValueError("mirrored bars require two sides and an explicit mirror_side")
    signed = values.copy()
    signed[sides.index(str(mirror_side))] *= -1
    selected_orientation = _orientation(orientation)
    positions = np.arange(len(labels))
    width = bar_width(len(sides))
    containers: list[BarContainer] = []
    figure, axis = plt.subplots()
    for index, label in enumerate(sides):
        offset = (index - (len(sides) - 1) / 2) * width
        containers.append(
            _bar(
                axis,
                positions + offset,
                signed[index],
                orientation=selected_orientation,
                width=width,
                label=label,
            )
        )
    _set_axis_labels(
        axis,
        orientation=selected_orientation,
        value_default="Mirrored value",
        xlabel=xlabel,
        ylabel=ylabel,
    )
    _categorical_axes(axis, labels, selected_orientation, *linear_limits(signed))
    _finish_bars(axis, containers, value_labels)
    request_legend(axis)
    return figure


def build_waterfall(
    step: object | None = None,
    delta: object | None = None,
    role: object | None = None,
    orientation: object | None = None,
    value_labels: object | None = None,
    xlabel: object | None = None,
    ylabel: object | None = None,
) -> Figure:
    if step is None and delta is None and role is None:
        labels = ["Initial", "Gain", "Loss", "Final"]
        deltas = np.array([5.0, 3.0, -2.0, 6.0])
        roles = np.array(["subtotal", "change", "change", "total"], dtype=object)
    elif step is not None and delta is not None and role is not None:
        labels = [str(item) for item in np.asarray(step, dtype=object).ravel()]
        deltas = np.asarray(delta, dtype=float)
        roles = np.asarray(role, dtype=object).astype(str)
    else:
        raise ValueError("waterfall requires step, delta, and role")
    selected_orientation = _orientation(orientation)
    starts: list[float] = []
    heights: list[float] = []
    cumulative_values: list[float] = []
    running = 0.0
    for selected, selected_role in zip(deltas, roles, strict=True):
        if selected_role == "change":
            end = running + float(selected)
            starts.append(min(running, end))
            heights.append(abs(float(selected)))
            running = end
        else:
            starts.append(min(0.0, float(selected)))
            heights.append(abs(float(selected)))
            running = float(selected)
        cumulative_values.append(running)
    positions = np.arange(len(labels))
    figure, axis = plt.subplots()
    container = _bar(
        axis,
        positions,
        np.asarray(heights),
        orientation=selected_orientation,
        width=bar_width(),
        baseline=np.asarray(starts),
    )
    cumulative_endpoints = np.asarray(starts) + np.asarray(heights)
    edge = axis.spines["bottom"]
    for index in range(len(labels) - 1):
        connector_value = cumulative_values[index]
        if selected_orientation == "vertical":
            axis.plot(
                [positions[index] + bar_width() / 2, positions[index + 1] - bar_width() / 2],
                [connector_value, connector_value],
                color=edge.get_edgecolor(),
                linewidth=edge.get_linewidth(),
            )
        else:
            axis.plot(
                [connector_value, connector_value],
                [positions[index] + bar_width() / 2, positions[index + 1] - bar_width() / 2],
                color=edge.get_edgecolor(),
                linewidth=edge.get_linewidth(),
            )
    _set_axis_labels(
        axis,
        orientation=selected_orientation,
        value_default="Cumulative value",
        xlabel=xlabel,
        ylabel=ylabel,
    )
    _categorical_axes(
        axis,
        labels,
        selected_orientation,
        *linear_limits(np.asarray(starts), cumulative_endpoints),
    )
    _finish_bars(axis, [container], value_labels)
    return figure


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
        labels = [str(item) for item in np.asarray(category, dtype=object).ravel()]
        values = np.asarray(value, dtype=float)
    else:
        raise ValueError("dot bar requires category and value together")
    positions = np.arange(len(labels))
    figure, axis = plt.subplots()
    axis.vlines(positions, 0.0, values)
    collection = axis.scatter(positions, values)
    apply_scatter_contract(collection)
    axis.set(ylabel="Value" if ylabel is None else str(ylabel))
    _categorical_axes(axis, labels, "vertical", *linear_limits(values))
    if value_labels is True:
        for position, selected in zip(positions, values, strict=True):
            axis.text(float(position), float(selected), f"{selected:.2f}", ha="center", va="bottom")
    return figure


BUILDERS = {
    "simple": build_simple,
    "grouped": build_grouped,
    "stacked": build_stacked,
    "normalized_stacked": build_normalized_stacked,
    "grouped_stacked": build_grouped_stacked,
    "diverging_stacked": build_diverging_stacked,
    "range": build_range,
    "mirrored": build_mirrored,
    "waterfall": build_waterfall,
    "vertical": build_vertical,
    "horizontal": build_horizontal,
    "dot": build_dot,
}
