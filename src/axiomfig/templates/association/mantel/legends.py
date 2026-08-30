"""Measured Mantel legends and the AxiomFig-owned Pearson colorbar."""

from __future__ import annotations

from dataclasses import dataclass

import matplotlib as mpl
from matplotlib.axes import Axes
from matplotlib.colorbar import Colorbar
from matplotlib.colors import Normalize
from matplotlib.lines import Line2D

from axiomfig.ornaments import apply_colorbar_contract
from axiomfig.style import (
    MAIN_STROKE_PT,
    axiom_colormap,
    mantel_link_width,
    mantel_p_style,
    mantel_plot_contract,
    mantel_visual_color,
)
from axiomfig.templates.association.mantel.geometry import MantelGeometry


@dataclass(frozen=True)
class LegendExtents:
    strength_width_pt: float
    strength_height_pt: float
    p_width_pt: float
    p_height_pt: float


@dataclass(frozen=True)
class OrnamentRenderResult:
    colorbar: Colorbar
    legends: tuple[object, ...]


def render_colorbar(axis: Axes, colorbar_axis: Axes) -> Colorbar:
    """Render the Pearson key through Matplotlib Colorbar and the shared tick contract."""
    matrix_contract = mantel_plot_contract()["matrix"]
    cmap = axiom_colormap(str(matrix_contract["colormap"]))
    scalar = mpl.cm.ScalarMappable(norm=Normalize(vmin=-1.0, vmax=1.0), cmap=cmap)
    scalar.set_array([])
    colorbar = axis.figure.colorbar(scalar, cax=colorbar_axis, orientation="vertical")
    colorbar.set_ticks((-1.0, -0.5, 0.0, 0.5, 1.0))
    colorbar.set_label("Pearson r")
    apply_colorbar_contract(colorbar)
    colorbar.ax.tick_params(labelsize=mpl.rcParams["xtick.labelsize"])
    colorbar_axis.set_box_aspect(7.0)
    colorbar_axis.set_anchor("C")
    return colorbar


def _legend_handles(p_value_mode: str) -> tuple[list[Line2D], list[Line2D]]:
    strength = [
        Line2D(
            [],
            [],
            color=mantel_visual_color("cell_edge"),
            linewidth=mantel_link_width(value),
            label=label,
        )
        for value, label in ((0.1, "< 0.25"), (0.35, "0.25-0.50"), (0.65, ">= 0.50"))
    ]
    bins = (
        ((0.005, "< 0.01"), (0.025, "0.01-0.05"), (0.10, ">= 0.05"))
        if p_value_mode == "canonical"
        else (
            (0.0005, "< 0.001"),
            (0.005, "0.001-0.01"),
            (0.025, "0.01-0.05"),
            (0.10, ">= 0.05"),
        )
    )
    p_values = [
        Line2D(
            [],
            [],
            color=str(mantel_p_style(value, mode=p_value_mode)["color"]),
            alpha=(
                float(mantel_p_style(value, mode=p_value_mode)["alpha"]) if value < 0.05 else 0.52
            ),
            linewidth=MAIN_STROKE_PT * 1.8,
            label=label,
        )
        for value, label in bins
    ]
    return strength, p_values


def _create_link_legends(
    axis: Axes,
    *,
    strength_anchor: tuple[float, float],
    p_anchor: tuple[float, float],
    transform: object,
    p_value_mode: str,
) -> tuple[object, object]:
    strength_handles, p_handles = _legend_handles(p_value_mode)
    common = {
        "frameon": False,
        "handlelength": 1.0,
        "borderaxespad": 0.0,
        "labelspacing": 0.20,
        "handletextpad": 0.45,
        "columnspacing": 0.75,
        "fontsize": mpl.rcParams["legend.fontsize"],
        "title_fontsize": mpl.rcParams["font.size"],
    }
    strength = axis.legend(
        handles=strength_handles,
        title="Mantel |r|",
        loc="lower left",
        bbox_to_anchor=strength_anchor,
        bbox_transform=transform,
        ncol=3,
        **common,
    )
    strength.set_gid("axiomfig-mantel-legend")
    axis.add_artist(strength)
    p_legend = axis.legend(
        handles=p_handles,
        title="P value",
        loc="lower left",
        bbox_to_anchor=p_anchor,
        bbox_transform=transform,
        ncol=3 if p_value_mode == "canonical" else 2,
        **common,
    )
    p_legend.set_gid("axiomfig-mantel-legend")
    return strength, p_legend


def measure_link_legends(axis: Axes, p_value_mode: str = "canonical") -> LegendExtents:
    """Create the final legend grammar once, measure it, then remove probe artists."""
    strength, p_legend = _create_link_legends(
        axis,
        strength_anchor=(0.0, 0.0),
        p_anchor=(0.0, 0.0),
        transform=axis.transAxes,
        p_value_mode=p_value_mode,
    )
    axis.figure.canvas.draw()
    renderer = axis.figure.canvas.get_renderer()
    strength_bbox = strength.get_window_extent(renderer)
    p_bbox = p_legend.get_window_extent(renderer)
    scale = 72.0 / axis.figure.dpi
    extents = LegendExtents(
        strength_width_pt=strength_bbox.width * scale,
        strength_height_pt=strength_bbox.height * scale,
        p_width_pt=p_bbox.width * scale,
        p_height_pt=p_bbox.height * scale,
    )
    strength.remove()
    p_legend.remove()
    return extents


def render_link_legends(
    axis: Axes,
    geometry: MantelGeometry,
    *,
    p_value_mode: str,
) -> tuple[object, object]:
    return _create_link_legends(
        axis,
        strength_anchor=geometry.strength_legend_anchor,
        p_anchor=geometry.p_legend_anchor,
        transform=axis.transData,
        p_value_mode=p_value_mode,
    )


def render_ornament_layer(
    axis: Axes,
    colorbar_axis: Axes,
    geometry: MantelGeometry,
    *,
    coupling_enabled: bool,
    colorbar: Colorbar | None = None,
    p_value_mode: str = "canonical",
) -> OrnamentRenderResult:
    colorbar = colorbar or render_colorbar(axis, colorbar_axis)
    legends = (
        render_link_legends(axis, geometry, p_value_mode=p_value_mode) if coupling_enabled else ()
    )
    return OrnamentRenderResult(colorbar, legends)


__all__ = [
    "LegendExtents",
    "OrnamentRenderResult",
    "measure_link_legends",
    "render_colorbar",
    "render_ornament_layer",
]
