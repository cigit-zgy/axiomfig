from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import TwoSlopeNorm
from matplotlib.figure import Figure

from axiomfig.colors import semantic_colormap
from axiomfig.contracts import MAIN_STROKE_PT
from axiomfig.layout import add_panel_axes, create_panel_grid
from axiomfig.template_helpers import (
    apply_axis_contract,
    apply_colorbar_contract,
    apply_filled_collection_contract,
    apply_nice_linear_axis,
)


def _grid(x_values: object, y_values: object) -> tuple[np.ndarray, np.ndarray]:
    x_array = np.asarray(x_values, dtype=float)
    y_array = np.asarray(y_values, dtype=float)
    if x_array.ndim == y_array.ndim == 1:
        return np.meshgrid(x_array, y_array)
    return x_array, y_array


def build_contour(
    x_grid: object | None = None,
    y_grid: object | None = None,
    z: object | None = None,
    color_semantics: str = "sequential",
    levels: object | None = None,
    colorbar_label: str = "Field intensity (-)",
    xlabel: str = "State variable x",
    ylabel: str = "State variable y",
) -> Figure:
    if x_grid is None and y_grid is None and z is None:
        x = np.linspace(-3.0, 3.0, 81)
        y = np.linspace(-2.0, 2.0, 65)
        xx, yy = np.meshgrid(x, y)
        field = np.exp(-0.55 * (xx**2 + yy**2)) * np.cos(1.4 * xx) + 0.15 * yy
    elif x_grid is not None and y_grid is not None and z is not None:
        xx, yy = _grid(x_grid, y_grid)
        field = np.asarray(z, dtype=float)
    else:
        raise ValueError("contour requires x_grid, y_grid, and z together")
    figure = plt.figure()
    layout = create_panel_grid(figure, 1, 1, panel_labels=False)
    axis, colorbar_axis = add_panel_axes(layout, 0, colorbar=True)
    assert colorbar_axis is not None
    cmap = semantic_colormap(color_semantics)
    selected_levels = (
        np.asarray(levels, dtype=float)
        if levels is not None
        else np.linspace(float(field.min()), float(field.max()), 13)
    )
    norm = (
        TwoSlopeNorm(vmin=float(field.min()), vcenter=0.0, vmax=float(field.max()))
        if color_semantics == "diverging" and field.min() < 0 < field.max()
        else None
    )
    filled = axis.contourf(xx, yy, field, levels=selected_levels, cmap=cmap, norm=norm)
    axis.contour(
        xx,
        yy,
        field,
        levels=selected_levels[::2],
        colors="black",
        linewidths=MAIN_STROKE_PT,
    )
    axis.set(xlabel=xlabel, ylabel=ylabel)
    apply_axis_contract(axis, surface="filled")
    apply_nice_linear_axis(axis, float(xx.min()), float(xx.max()), coordinate="x")
    apply_nice_linear_axis(axis, float(yy.min()), float(yy.max()), coordinate="y")
    colorbar = figure.colorbar(filled, cax=colorbar_axis, label=colorbar_label)
    apply_colorbar_contract(colorbar)
    return figure


def build_quiver(
    x: object | None = None,
    y: object | None = None,
    u: object | None = None,
    v: object | None = None,
    color_semantics: str = "sequential",
    magnitude: object | None = None,
    colorbar_label: str = "Vector magnitude (-)",
    xlabel: str = "State variable x",
    ylabel: str = "State variable y",
) -> Figure:
    if x is None and y is None and u is None and v is None:
        x_values = np.linspace(-2.5, 2.5, 11)
        y_values = np.linspace(-2.0, 2.0, 9)
        xx, yy = np.meshgrid(x_values, y_values)
        u_values = -yy - 0.18 * xx
        v_values = xx - 0.18 * yy
    elif x is not None and y is not None and u is not None and v is not None:
        xx, yy = _grid(x, y)
        u_values = np.asarray(u, dtype=float)
        v_values = np.asarray(v, dtype=float)
    else:
        raise ValueError("quiver requires x, y, u, and v together")
    magnitude_values = (
        np.asarray(magnitude, dtype=float)
        if magnitude is not None
        else np.hypot(u_values, v_values)
    )
    figure = plt.figure()
    layout = create_panel_grid(figure, 1, 1, panel_labels=False)
    axis, colorbar_axis = add_panel_axes(layout, 0, colorbar=True)
    assert colorbar_axis is not None
    cmap = semantic_colormap(color_semantics)
    arrows = axis.quiver(
        xx,
        yy,
        u_values,
        v_values,
        magnitude_values,
        cmap=cmap,
        pivot="mid",
    )
    apply_filled_collection_contract(arrows)
    axis.set(xlabel=xlabel, ylabel=ylabel)
    apply_axis_contract(axis, surface="filled")
    apply_nice_linear_axis(axis, float(xx.min()), float(xx.max()), coordinate="x")
    apply_nice_linear_axis(axis, float(yy.min()), float(yy.max()), coordinate="y")
    colorbar = figure.colorbar(arrows, cax=colorbar_axis, label=colorbar_label)
    apply_colorbar_contract(colorbar)
    return figure


BUILDERS = {"contour": build_contour, "quiver": build_quiver}
