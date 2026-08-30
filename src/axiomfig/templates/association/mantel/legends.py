"""Mantel ornament layer: Pearson colorbar and coupling explanation keys."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

import matplotlib as mpl
import numpy as np
from matplotlib.axes import Axes
from matplotlib.colors import Normalize
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle

from axiomfig.style import (
    FILL_EDGE_PT,
    MAIN_STROKE_PT,
    axiom_colormap,
    mantel_link_width,
    mantel_p_style,
    mantel_plot_contract,
    mantel_visual_color,
)
from axiomfig.templates.association.mantel.geometry import MantelGeometry


@dataclass(frozen=True)
class OrnamentRenderResult:
    colorbar: object
    legends: tuple[object, ...]


def render_colorbar(axis: Axes, geometry: MantelGeometry) -> Rectangle:
    """Render a compact vector strip owned by the correlation matrix."""
    matrix_contract = mantel_plot_contract()["matrix"]
    assert isinstance(matrix_contract, Mapping)
    cmap = axiom_colormap(str(matrix_contract["colormap"]))
    norm = Normalize(vmin=-1.0, vmax=1.0)
    height = min(3.2, max(2.2, geometry.bounds.size * 0.28))
    width = 0.18
    x = geometry.colorbar_x
    y = geometry.bounds.y1 - height
    steps = 48
    for index, value in enumerate(np.linspace(-1.0, 1.0, steps, endpoint=False)):
        axis.add_patch(
            Rectangle(
                (x, y + index * height / steps),
                width,
                height / steps + 0.002,
                facecolor=cmap(norm(value)),
                edgecolor="none",
                zorder=2,
            )
        )
    border = Rectangle(
        (x, y),
        width,
        height,
        facecolor="none",
        edgecolor=mantel_visual_color("cell_edge"),
        linewidth=FILL_EDGE_PT,
        zorder=3,
    )
    border.set_gid("axiomfig-mantel-colorbar")
    axis.add_patch(border)
    for value in (-1.0, 0.0, 1.0):
        tick_y = y + (value + 1.0) * height / 2.0
        axis.plot(
            [x + width, x + width + 0.07],
            [tick_y, tick_y],
            color=mantel_visual_color("cell_edge"),
            linewidth=FILL_EDGE_PT,
            clip_on=True,
            zorder=3,
        )
        axis.text(
            x + width + 0.10,
            tick_y,
            f"{value:g}",
            ha="left",
            va="center",
            fontsize=mpl.rcParams["font.size"] * 0.68,
            clip_on=True,
        )
    axis.text(
        x - 0.14,
        y + height / 2.0,
        "Pearson r",
        ha="center",
        va="center",
        fontsize=mpl.rcParams["font.size"] * 0.72,
        rotation=90,
        clip_on=True,
    )
    return border


def render_link_legends(axis: Axes, geometry: MantelGeometry) -> tuple[object, object]:
    strength_handles = [
        Line2D(
            [],
            [],
            color=mantel_visual_color("cell_edge"),
            linewidth=mantel_link_width(value),
            label=label,
        )
        for value, label in ((0.1, "< 0.25"), (0.35, "0.25-0.50"), (0.65, ">= 0.50"))
    ]
    p_handles = [
        Line2D(
            [],
            [],
            color=str(mantel_p_style(value)["color"]),
            alpha=(float(mantel_p_style(value)["alpha"]) if value < 0.05 else 0.62),
            linewidth=MAIN_STROKE_PT * 1.8,
            label=label,
        )
        for value, label in (
            (0.0005, "< 0.001"),
            (0.005, "0.001-0.01"),
            (0.025, "0.01-0.05"),
            (0.10, ">= 0.05"),
        )
    ]
    common = {
        "frameon": False,
        "handlelength": 1.0,
        "borderaxespad": 0.0,
        "labelspacing": 0.25,
        "handletextpad": 0.45,
        "columnspacing": 0.75,
        "fontsize": mpl.rcParams["font.size"] * 0.68,
        "title_fontsize": mpl.rcParams["font.size"] * 0.70,
    }
    strength = axis.legend(
        handles=strength_handles,
        title="Mantel |r|",
        loc="lower left",
        bbox_to_anchor=geometry.strength_legend_anchor,
        bbox_transform=axis.transAxes,
        ncol=len(strength_handles),
        **common,
    )
    strength.set_gid("axiomfig-mantel-legend")
    axis.add_artist(strength)
    p_legend = axis.legend(
        handles=p_handles,
        title="P value",
        loc="lower left",
        bbox_to_anchor=geometry.p_legend_anchor,
        bbox_transform=axis.transAxes,
        ncol=len(p_handles),
        **common,
    )
    p_legend.set_gid("axiomfig-mantel-legend")
    return strength, p_legend


def render_ornament_layer(
    axis: Axes,
    geometry: MantelGeometry,
    *,
    coupling_enabled: bool,
) -> OrnamentRenderResult:
    colorbar = render_colorbar(axis, geometry)
    legends = render_link_legends(axis, geometry) if coupling_enabled else ()
    return OrnamentRenderResult(colorbar, legends)


__all__ = ["OrnamentRenderResult", "render_ornament_layer"]
