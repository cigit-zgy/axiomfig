from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from axiomfig.layout import add_panel_axes, create_panel_grid
from axiomfig.ornaments import apply_colorbar_contract, request_legend
from axiomfig.style import (
    add_bar_value_labels,
    apply_axis_contract,
    apply_categorical_axis,
    apply_nice_linear_axis,
    apply_scatter_contract,
    bar_width,
    confidence_interval_kwargs,
    reference_line_kwargs,
    series_style,
)
from axiomfig.templates.heatmap import add_heatmap


def _line_panel(axis: Axes) -> None:
    x = np.linspace(0.0, 12.0, 61)
    mean = 1.0 - np.exp(-x / 3.2)
    spread = 0.045 + 0.025 * np.exp(-x / 4.0)
    color = plt.rcParams["axes.prop_cycle"].by_key()["color"][0]
    axis.fill_between(x, mean - spread, mean + spread, **confidence_interval_kwargs(color))
    axis.plot(x, mean, label="Hybrid", **series_style(0, include_marker=False))
    axis.plot(
        x,
        0.9 * (1.0 - np.exp(-x / 4.0)),
        label="Mechanistic",
        **series_style(1, include_marker=False),
    )
    axis.set(xlabel="Time (d)", ylabel="Response (-)")
    apply_axis_contract(axis, surface="open")
    apply_nice_linear_axis(axis, 0.0, 12.0, coordinate="x")
    apply_nice_linear_axis(axis, 0.0, 1.0, coordinate="y")
    request_legend(axis)


def _bar_panel(axis: Axes) -> None:
    positions = np.arange(3)
    width = bar_width(2)
    first = axis.bar(positions - width / 2, [0.72, 0.67, 0.61], width, label="Mechanistic")
    second = axis.bar(positions + width / 2, [0.84, 0.76, 0.71], width, label="Hybrid")
    axis.set_xticks(positions, ["COD", "N", "P"])
    axis.set(ylabel="Score (-)")
    apply_axis_contract(axis, surface="open")
    apply_categorical_axis(axis, coordinate="x")
    apply_nice_linear_axis(axis, 0.0, 1.0, coordinate="y")
    add_bar_value_labels(axis, [first, second])
    request_legend(axis)


def _scatter_panel(axis: Axes, seed: int) -> None:
    rng = np.random.default_rng(seed)
    observed = np.linspace(2.0, 28.0, 36)
    collection = axis.scatter(observed, observed + rng.normal(0.0, 1.3, observed.size))
    apply_scatter_contract(collection)
    axis.plot([0, 30], [0, 30], **reference_line_kwargs())
    axis.set(xlabel="Observed", ylabel="Predicted")
    apply_axis_contract(axis, surface="open")
    apply_nice_linear_axis(axis, 0.0, 30.0, coordinate="x")
    apply_nice_linear_axis(axis, 0.0, 30.0, coordinate="y")


def _residual_panel(axis: Axes, seed: int) -> None:
    rng = np.random.default_rng(seed)
    fitted = np.linspace(1.0, 20.0, 42)
    residual = rng.normal(0.0, 1.0, fitted.size) * (0.5 + 0.03 * fitted)
    collection = axis.scatter(fitted, residual)
    apply_scatter_contract(collection)
    axis.axhline(0.0, **reference_line_kwargs())
    axis.set(xlabel="Fitted", ylabel="Residual")
    apply_axis_contract(axis, surface="open")
    apply_nice_linear_axis(axis, 0.0, 21.0, coordinate="x")
    apply_nice_linear_axis(axis, -3.0, 3.0, coordinate="y")


def _build_grid(rows: int, columns: int, *, heatmap: bool) -> Figure:
    figure = plt.figure()
    layout = create_panel_grid(figure, rows, columns)
    axes: list[Axes] = []
    colorbar_axis: Axes | None = None
    panel_count = rows * columns
    for index in range(panel_count):
        if heatmap and index == panel_count - 1:
            axis, colorbar_axis = add_panel_axes(layout, index, colorbar=True)
        else:
            axis, _ = add_panel_axes(layout, index)
        axes.append(axis)

    for index, axis in enumerate(axes):
        if heatmap and index == panel_count - 1:
            image = add_heatmap(axis, annotate=panel_count <= 4)
            assert colorbar_axis is not None
            colorbar = figure.colorbar(image, cax=colorbar_axis, label="Correlation (-)")
            apply_colorbar_contract(colorbar)
        else:
            builder_index = index % 4
            if builder_index == 2:
                _scatter_panel(axis, 109 + index)
            elif builder_index == 3:
                _residual_panel(axis, 109 + index)
            elif builder_index == 0:
                _line_panel(axis)
            else:
                _bar_panel(axis)
    return figure


def build_horizontal_2() -> Figure:
    return _build_grid(1, 2, heatmap=False)


def build_grid_2x2() -> Figure:
    return _build_grid(2, 2, heatmap=True)


def build_grid_2x3() -> Figure:
    return _build_grid(2, 3, heatmap=False)


def build_grid_3x2() -> Figure:
    return _build_grid(3, 2, heatmap=True)


BUILDERS = {
    "horizontal_2": build_horizontal_2,
    "grid_2x2": build_grid_2x2,
    "grid_2x3": build_grid_2x3,
    "grid_3x2": build_grid_3x2,
}
