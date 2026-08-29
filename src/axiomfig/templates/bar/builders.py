from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from axiomfig.contracts import bar_width
from axiomfig.template_helpers import (
    add_bar_value_labels,
    apply_axis_contract,
    apply_categorical_axis,
    apply_nice_linear_axis,
    place_legend_above,
)


def _vertical_axes(axis: Axes, labels: list[str], upper: float) -> None:
    axis.set_xticks(np.arange(len(labels)), labels)
    apply_axis_contract(axis, surface="open")
    apply_categorical_axis(axis, coordinate="x")
    apply_nice_linear_axis(axis, 0.0, upper, coordinate="y")


def build_vertical() -> Figure:
    labels = ["COD", "Nitrogen", "Phosphorus"]
    figure, axis = plt.subplots()
    bars = axis.bar(np.arange(3), [0.84, 0.76, 0.71], width=bar_width())
    axis.set(ylabel="Validation score (-)")
    _vertical_axes(axis, labels, 1.0)
    add_bar_value_labels(axis, [bars])
    return figure


def build_horizontal() -> Figure:
    labels = ["Mechanistic", "Neural ODE", "Hybrid ODE"]
    positions = np.arange(3)
    figure, axis = plt.subplots()
    bars = axis.barh(positions, [0.66, 0.78, 0.87], height=bar_width())
    axis.set_yticks(positions, labels)
    axis.set(xlabel="Explained variance (-)")
    apply_axis_contract(axis, surface="open")
    apply_categorical_axis(axis, coordinate="y")
    apply_nice_linear_axis(axis, 0.0, 1.0, coordinate="x")
    add_bar_value_labels(axis, [bars])
    return figure


def build_grouped() -> Figure:
    labels = ["COD", "Nitrogen", "Phosphorus"]
    positions = np.arange(3)
    width = bar_width(2)
    figure, axis = plt.subplots()
    first = axis.bar(positions - width / 2, [0.72, 0.67, 0.61], width, label="Mechanistic")
    second = axis.bar(positions + width / 2, [0.84, 0.76, 0.71], width, label="Hybrid")
    axis.set(ylabel="Validation score (-)")
    _vertical_axes(axis, labels, 1.0)
    add_bar_value_labels(axis, [first, second])
    place_legend_above(axis)
    return figure


def build_stacked() -> Figure:
    labels = ["Baseline", "Calibrated", "Hybrid"]
    positions = np.arange(3)
    first_values = np.array([0.42, 0.50, 0.57])
    second_values = np.array([0.25, 0.28, 0.31])
    figure, axis = plt.subplots()
    width = bar_width()
    first = axis.bar(positions, first_values, width=width, label="Mechanistic")
    second = axis.bar(
        positions,
        second_values,
        width=width,
        bottom=first_values,
        label="Data-driven",
    )
    axis.set(ylabel="Explained contribution (-)")
    _vertical_axes(axis, labels, 1.0)
    add_bar_value_labels(axis, [first, second])
    place_legend_above(axis)
    return figure


BUILDERS = {
    "vertical": build_vertical,
    "horizontal": build_horizontal,
    "grouped": build_grouped,
    "stacked": build_stacked,
}
