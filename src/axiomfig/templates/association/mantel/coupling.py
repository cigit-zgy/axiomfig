"""Mantel coupling layer constrained to the unused triangular matrix half-plane."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping

import numpy as np
from matplotlib.axes import Axes
from matplotlib.patches import Circle, PathPatch
from matplotlib.path import Path

from axiomfig.style import (
    FILL_EDGE_PT,
    mantel_link_width,
    mantel_p_style,
    mantel_plot_contract,
    mantel_visual_color,
)
from axiomfig.templates.association.mantel.composition import CouplingSpec
from axiomfig.templates.association.mantel.data import MantelLink
from axiomfig.templates.association.mantel.geometry import MantelGeometry, source_label_size


def nice_curvature(
    *,
    source_order: int,
    target_order: int,
    link_density: int,
    orientation: str,
    lane_index: float,
) -> float:
    """Return semantic Bézier clearance in matrix-cell units."""
    del orientation
    contract = mantel_plot_contract()["matrix"]
    assert isinstance(contract, Mapping)
    base = float(contract["route_clearance"])
    lane_spacing = float(contract["route_lane_spacing"])
    density = min(max(link_density - 1, 0), 12) * 0.018
    order_span = min(abs(target_order - source_order), 16) * 0.010
    return base + density + order_span + abs(lane_index) * lane_spacing


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


def _empty_half_plane_normal(matrix_type: str) -> np.ndarray:
    if matrix_type == "lower":
        return np.asarray((1.0, -1.0), dtype=float) / np.sqrt(2.0)
    if matrix_type == "upper":
        return np.asarray((1.0, 1.0), dtype=float) / np.sqrt(2.0)
    return np.asarray((-1.0, 0.0), dtype=float)


def _route_vertices(
    start: tuple[float, float],
    end: tuple[float, float],
    *,
    clearance: float,
    matrix_type: str,
    lane_index: float,
    y_boundary: float,
) -> tuple[tuple[float, float], ...]:
    """Create one cubic whose control polygon stays in the empty coupling half-plane.

    Bézier curves are contained by the convex hull of their control points. Both control points
    therefore remain on the same empty side of the target rail, preventing routes from entering
    visible matrix glyphs without stochastic collision search.
    """
    start_array = np.asarray(start, dtype=float)
    end_array = np.asarray(end, dtype=float)
    span = end_array - start_array
    normal = _empty_half_plane_normal(matrix_type)
    lane_scale = 1.0 + abs(lane_index) * 0.08
    outer = normal * clearance * lane_scale
    control1 = start_array + span * 0.30 + outer * 0.82
    control2 = start_array + span * 0.73 + outer
    if matrix_type == "lower":
        control1[1] = max(control1[1], y_boundary)
        control2[1] = max(control2[1], y_boundary)
    elif matrix_type == "upper":
        control1[1] = min(control1[1], y_boundary)
        control2[1] = min(control2[1], y_boundary)
    return (
        start,
        (float(control1[0]), float(control1[1])),
        (float(control2[0]), float(control2[1])),
        end,
    )


def render_coupling_layer(
    axis: Axes,
    links: tuple[MantelLink, ...],
    spec: CouplingSpec,
    geometry: MantelGeometry,
) -> tuple[PathPatch, ...]:
    """Render source nodes and deterministic matrix-attached Mantel arcs."""
    if not spec.enabled:
        return ()
    matrix_contract = mantel_plot_contract()["matrix"]
    assert isinstance(matrix_contract, Mapping)
    node_radius = float(matrix_contract["source_node_radius"])
    for source, (x, y) in geometry.source_region.positions.items():
        node = Circle(
            (x, y),
            node_radius,
            facecolor=mantel_visual_color("background"),
            edgecolor=mantel_visual_color("cell_edge"),
            linewidth=FILL_EDGE_PT,
            zorder=6,
        )
        node.set_gid("axiomfig-mantel-source-node")
        node._axiomfig_source = source
        axis.add_patch(node)
        is_upper = geometry.matrix_type == "upper"
        label = axis.text(
            x,
            y + (0.30 if is_upper else -0.30),
            source,
            ha="center",
            va="bottom" if is_upper else "top",
            fontsize=source_label_size(),
            clip_on=True,
            zorder=6,
        )
        label.set_gid("axiomfig-mantel-source-label")

    grouped: dict[str, list[MantelLink]] = defaultdict(list)
    for link in links:
        grouped[link.source].append(link)
    target_order = {label: index for index, label in enumerate(geometry.target_rail.anchors)}
    source_order = {source: index for index, source in enumerate(geometry.source_region.positions)}

    rendered: list[PathPatch] = []
    for source in geometry.source_region.positions:
        source_links = sorted(
            grouped[source],
            key=lambda link: (target_order[link.target], link.target),
        )
        for rank, link in enumerate(source_links):
            style = _link_style(link, spec.nonsignificant)
            if style is None:
                continue
            color, alpha = style
            start = geometry.source_region.positions[source]
            end = geometry.target_rail.anchors[link.target]
            lane_index = float(rank)
            clearance = nice_curvature(
                source_order=source_order[source],
                target_order=target_order[link.target],
                link_density=len(source_links),
                orientation=geometry.target_rail.orientation,
                lane_index=lane_index,
            )
            vertices = _route_vertices(
                start,
                end,
                clearance=clearance,
                matrix_type=geometry.matrix_type,
                lane_index=lane_index,
                y_boundary=(
                    geometry.bounds.y1 - 0.08
                    if geometry.matrix_type == "upper"
                    else geometry.bounds.y0 + 0.08
                ),
            )
            path = Path(vertices, (Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4))
            artist = PathPatch(
                path,
                facecolor="none",
                edgecolor=color,
                alpha=alpha,
                linewidth=_link_width(link.mantel_r, spec.width_mode),
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
            artist._axiomfig_route_model = "rail-normal-cubic"
            artist._axiomfig_route_signature = (
                link.source,
                link.target,
                *(round(value, 6) for vertex in vertices for value in vertex),
            )
            axis.add_patch(artist)
            rendered.append(artist)
    return tuple(rendered)


__all__ = ["nice_curvature", "render_coupling_layer"]
