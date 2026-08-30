"""Mantel ornaments using AxiomFig colorbar/tick contracts and geometry-owned legend space."""

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
class OrnamentRenderResult:
    colorbar: Colorbar
    legends: tuple[object, ...]


def render_colorbar(axis: Axes, colorbar_axis: Axes) -> Colorbar:
    """Render the Pearson key through Matplotlib Colorbar and the shared Axiom tick contract."""
    matrix_contract = mantel_plot_contract()["matrix"]
    cmap = axiom_colormap(str(matrix_contract["colormap"]))
    scalar = mpl.cm.ScalarMappable(norm=Normalize(vmin=-1.0, vmax=1.0), cmap=cmap)
    scalar.set_array([])
    colorbar = axis.figure.colorbar(scalar, cax=colorbar_axis, orientation="vertical")
    colorbar.set_ticks((-1.0, -0.5, 0.0, 0.5, 1.0))
    colorbar.set_label("Pearson r")
    apply_colorbar_contract(colorbar)
    colorbar.ax.tick_params(labelsize=mpl.rcParams["xtick.labelsize"])
    return colorbar


def render_link_legends(axis: Axes, geometry: MantelGeometry) -> tuple[object, object]:
    strength_handles = [
        Line2D(
            [],
            [],
            color=mantel_visual_color("cell_edge"),
            linewidth=mantel_link_width(value),
            label=label,
        )
        for value, label in ((0.1, "< 0.25"), (0.35, "0.25–0.50"), (0.65, "≥ 0.50"))
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
            (0.005, "0.001–0.01"),
            (0.025, "0.01–0.05"),
            (0.10, "≥ 0.05"),
        )
    ]
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
        bbox_to_anchor=geometry.strength_legend_anchor,
        bbox_transform=axis.transData,
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
        bbox_transform=axis.transData,
        ncol=len(p_handles),
        **common,
    )
    p_legend.set_gid("axiomfig-mantel-legend")
    return strength, p_legend


def render_ornament_layer(
    axis: Axes,
    colorbar_axis: Axes,
    geometry: MantelGeometry,
    *,
    coupling_enabled: bool,
) -> OrnamentRenderResult:
    colorbar = render_colorbar(axis, colorbar_axis)
    legends = render_link_legends(axis, geometry) if coupling_enabled else ()
    return OrnamentRenderResult(colorbar, legends)


__all__ = ["OrnamentRenderResult", "render_ornament_layer"]
