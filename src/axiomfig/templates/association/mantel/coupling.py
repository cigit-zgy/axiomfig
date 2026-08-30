"""Deterministic linkET-style source-to-matrix coupling geometry."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping

import matplotlib as mpl
import numpy as np
from matplotlib.axes import Axes
from matplotlib.patches import Circle, PathPatch
from matplotlib.path import Path

from axiomfig.style import FILL_EDGE_PT, mantel_link_width, mantel_p_style, mantel_plot_contract
from axiomfig.templates.association.mantel.data import MantelLink, MantelOptions
from axiomfig.templates.association.mantel.geometry import MantelGeometry


def nice_curvature(
    *,
    source_y: float,
    target_y: float,
    lane: float,
    link_count: int,
    matrix_type: str,
) -> tuple[float, float]:
    """Return deterministic source and target control offsets in cell units."""
    direction = -1.0 if matrix_type == "upper" else 1.0
    vertical_span = target_y - source_y
    source_offset = float(np.clip(vertical_span * 0.12 + lane * 0.10, -0.65, 0.65))
    density = min(max(link_count - 1, 0), 8) * 0.025
    target_offset = direction * (0.22 + density + abs(lane) * 0.09)
    return source_offset, target_offset


def _link_width(value: float, mode: str) -> float:
    if mode == "binned":
        return mantel_link_width(value)
    contract = mantel_plot_contract()["links"]
    assert isinstance(contract, Mapping)
    widths = tuple(float(item) for item in contract["widths_pt"])
    return widths[0] + abs(value) * (widths[-1] - widths[0])


def _link_style(link: MantelLink, nonsignificant_mode: str) -> tuple[str, float] | None:
    style = mantel_p_style(link.p_value)
    if bool(style["significant"]):
        return str(style["color"]), float(style["alpha"])
    if nonsignificant_mode == "hide":
        return None
    if nonsignificant_mode == "show":
        contract = mantel_plot_contract()["links"]
        assert isinstance(contract, Mapping)
        return str(style["color"]), float(contract["significant_alpha"])
    return str(style["color"]), float(style["alpha"])


def render_coupling(
    axis: Axes,
    links: tuple[MantelLink, ...],
    options: MantelOptions,
    geometry: MantelGeometry,
) -> tuple[PathPatch, ...]:
    """Render source nodes and stable, separated cubic Bézier routes."""
    for source, (x, y) in geometry.source_positions.items():
        node = Circle(
            (x, y),
            0.075,
            facecolor="white",
            edgecolor="black",
            linewidth=FILL_EDGE_PT,
            zorder=6,
        )
        node.set_gid("axiomfig-mantel-source-node")
        node._axiomfig_source = source
        axis.add_patch(node)
        label = axis.text(
            x - 0.12,
            y,
            source,
            ha="right",
            va="center",
            fontsize=mpl.rcParams["font.size"] * 0.82,
            clip_on=True,
            zorder=6,
        )
        label.set_gid("axiomfig-mantel-source-label")

    grouped: dict[str, list[MantelLink]] = defaultdict(list)
    for link in links:
        grouped[link.source].append(link)
    rendered: list[PathPatch] = []
    for source_index, source in enumerate(geometry.source_positions):
        source_links = sorted(
            grouped[source],
            key=lambda link: (
                -geometry.target_positions[link.target][1],
                geometry.target_positions[link.target][0],
                link.target,
            ),
        )
        for rank, link in enumerate(source_links):
            style = _link_style(link, options.nonsignificant_links)
            if style is None:
                continue
            color, alpha = style
            source_x, source_y = geometry.source_positions[source]
            target_x, target_y = geometry.target_positions[link.target]
            lane = rank - (len(source_links) - 1) / 2.0
            source_offset, target_offset = nice_curvature(
                source_y=source_y,
                target_y=target_y,
                lane=lane,
                link_count=len(source_links),
                matrix_type=options.matrix_type,
            )
            start = (source_x + 0.09, source_y)
            end = (target_x - 0.045, target_y)
            bounds = geometry.bounds
            if options.matrix_type in {"lower", "upper"}:
                gate_y = (
                    bounds.y1 + 0.16 + source_index * 0.10 + lane * 0.055
                    if options.matrix_type == "lower"
                    else bounds.y0 - 0.16 - source_index * 0.10 - lane * 0.055
                )
                gate = (
                    bounds.x0 - 0.18 - source_index * 0.12 - abs(lane) * 0.025,
                    gate_y,
                )
                first_control = (
                    start[0] + (gate[0] - start[0]) * 0.48,
                    source_y + source_offset,
                )
                second_control = (gate[0] - 0.42, gate_y)
                third_control = (gate[0] + 0.32, gate_y)
                fourth_control = (
                    max(gate[0] + 0.36, end[0] - 0.34 - abs(lane) * 0.025),
                    target_y + target_offset * (1.0 + source_index * 0.18),
                )
                vertices = (
                    start,
                    first_control,
                    second_control,
                    gate,
                    third_control,
                    fourth_control,
                    end,
                )
                codes = (
                    Path.MOVETO,
                    Path.CURVE4,
                    Path.CURVE4,
                    Path.CURVE4,
                    Path.CURVE4,
                    Path.CURVE4,
                    Path.CURVE4,
                )
            else:
                horizontal_span = max(end[0] - start[0], 0.4)
                control1 = (
                    start[0] + horizontal_span * (0.42 + 0.018 * abs(lane)),
                    source_y + source_offset,
                )
                control2 = (bounds.x0 - 0.30, target_y + lane * 0.08)
                vertices = (start, control1, control2, end)
                codes = (Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4)
            path = Path(vertices, codes)
            artist = PathPatch(
                path,
                facecolor="none",
                edgecolor=color,
                alpha=alpha,
                linewidth=_link_width(link.mantel_r, options.link_width_mode),
                capstyle="round",
                clip_on=True,
                zorder=4,
            )
            artist.set_gid("axiomfig-mantel-link")
            artist._axiomfig_source = link.source
            artist._axiomfig_target = link.target
            artist._axiomfig_source_group = link.source
            artist._axiomfig_target_label = link.target
            artist._axiomfig_mantel_r = link.mantel_r
            artist._axiomfig_p_value = link.p_value
            artist._axiomfig_label = link.label
            artist._axiomfig_metadata = dict(link.metadata)
            artist._axiomfig_route_signature = (
                link.source,
                link.target,
                *(round(value, 6) for vertex in vertices for value in vertex),
            )
            axis.add_patch(artist)
            rendered.append(artist)
    return tuple(rendered)


__all__ = ["nice_curvature", "render_coupling"]
