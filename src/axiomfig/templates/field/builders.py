from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
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


def build_contour() -> Figure:
    x = np.linspace(-3.0, 3.0, 81)
    y = np.linspace(-2.0, 2.0, 65)
    xx, yy = np.meshgrid(x, y)
    field = np.exp(-0.55 * (xx**2 + yy**2)) * np.cos(1.4 * xx) + 0.15 * yy
    figure = plt.figure()
    layout = create_panel_grid(figure, 1, 1, panel_labels=False)
    axis, colorbar_axis = add_panel_axes(layout, 0, colorbar=True)
    assert colorbar_axis is not None
    cmap = semantic_colormap("sequential")
    levels = np.linspace(float(field.min()), float(field.max()), 13)
    filled = axis.contourf(xx, yy, field, levels=levels, cmap=cmap)
    axis.contour(xx, yy, field, levels=levels[::2], colors="black", linewidths=MAIN_STROKE_PT)
    axis.set(xlabel="State variable x", ylabel="State variable y")
    apply_axis_contract(axis, surface="filled")
    apply_nice_linear_axis(axis, -3.0, 3.0, coordinate="x")
    apply_nice_linear_axis(axis, -2.0, 2.0, coordinate="y")
    colorbar = figure.colorbar(filled, cax=colorbar_axis, label="Field intensity (-)")
    apply_colorbar_contract(colorbar)
    return figure


def build_quiver() -> Figure:
    x = np.linspace(-2.5, 2.5, 11)
    y = np.linspace(-2.0, 2.0, 9)
    xx, yy = np.meshgrid(x, y)
    u = -yy - 0.18 * xx
    v = xx - 0.18 * yy
    magnitude = np.hypot(u, v)
    figure = plt.figure()
    layout = create_panel_grid(figure, 1, 1, panel_labels=False)
    axis, colorbar_axis = add_panel_axes(layout, 0, colorbar=True)
    assert colorbar_axis is not None
    cmap = semantic_colormap("sequential")
    arrows = axis.quiver(xx, yy, u, v, magnitude, cmap=cmap, pivot="mid")
    apply_filled_collection_contract(arrows)
    axis.set(xlabel="State variable x", ylabel="State variable y")
    apply_axis_contract(axis, surface="filled")
    apply_nice_linear_axis(axis, -2.5, 2.5, coordinate="x")
    apply_nice_linear_axis(axis, -2.0, 2.0, coordinate="y")
    colorbar = figure.colorbar(arrows, cax=colorbar_axis, label="Vector magnitude (-)")
    apply_colorbar_contract(colorbar)
    return figure


BUILDERS = {"contour": build_contour, "quiver": build_quiver}
