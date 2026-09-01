"""Mantel links as one deterministic source-rail to target-rail curve family."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping

import numpy as np
from matplotlib.axes import Axes
from matplotlib.patches import PathPatch
from matplotlib.path import Path

from axiomfig.templates.association.mantel.composition import CouplingSpec
from axiomfig.templates.association.mantel.data import MantelLink
from axiomfig.templates.association.mantel.geometry import MantelGeometry
from axiomfig.templates.association.mantel.styling import (
    mantel_link_width,
    mantel_p_style,
    mantel_plot_contract,
)


def _link_width(value: float, mode: str) -> float:
    if mode == "binned":
        return mantel_link_width(value)
    contract = mantel_plot_contract()["links"]
    assert isinstance(contract, Mapping)
    widths = tuple(float(item) for item in contract["widths_pt"])
    return widths[0] + abs(value) * (widths[-1] - widths[0])


def _link_style(link: MantelLink, spec: CouplingSpec) -> tuple[str, float] | None:
    style = mantel_p_style(link.p_value, mode=spec.p_value_mode)
    if bool(style["significant"]):
        return str(style["color"]), float(style["alpha"])
    if spec.nonsignificant == "hide":
        return None
    if spec.nonsignificant == "show":
        contract = mantel_plot_contract()["links"]
        assert isinstance(contract, Mapping)
        return str(style["color"]), float(contract["significant_alpha"])
    return str(style["color"]), float(style["alpha"])


def curvature_sign(target_index: int, target_count: int) -> int:
    """Split ordered targets at the midpoint; an odd centre belongs to the second half."""
    if target_count < 1 or not 0 <= target_index < target_count:
        raise ValueError("target index must lie inside a non-empty target rail")
    return -1 if target_index < target_count / 2 else 1


def _coupling_basis(geometry: MantelGeometry) -> tuple[np.ndarray, np.ndarray]:
    anchors = np.asarray(tuple(geometry.target_positions.values()), dtype=float)
    tangent = anchors[-1] - anchors[0]
    tangent /= np.linalg.norm(tangent)
    normal_sign = 1.0 if geometry.matrix_type == "lower" else -1.0
    normal = normal_sign * np.asarray((1.0, 1.0), dtype=float) / np.sqrt(2.0)
    return tangent, normal


def _quadratic_vertices(
    start: tuple[float, float],
    end: tuple[float, float],
    *,
    geometry: MantelGeometry,
    curvature: float,
    sign: int,
) -> tuple[tuple[float, float], ...]:
    start_point = np.asarray(start, dtype=float)
    end_point = np.asarray(end, dtype=float)
    tangent, normal = _coupling_basis(geometry)
    chord_length = float(np.linalg.norm(end_point - start_point))
    rail_separation = max(geometry.source_rail.normal_offset, 0.5)
    midpoint = 0.5 * (start_point + end_point)
    control = (
        midpoint
        + normal * curvature * rail_separation
        + tangent * sign * curvature * min(chord_length, geometry.bounds.size * 0.5)
    )
    return start, (float(control[0]), float(control[1])), end


def render_coupling_layer(
    axis: Axes,
    links: tuple[MantelLink, ...],
    spec: CouplingSpec,
    geometry: MantelGeometry,
) -> tuple[PathPatch, ...]:
    """Render links with one quadratic primitive and one ordered curvature rule."""
    if not spec.enabled:
        return ()
    grouped: dict[str, list[MantelLink]] = defaultdict(list)
    for link in links:
        grouped[link.source].append(link)
    target_order = {label: index for index, label in enumerate(geometry.target_positions)}
    contract = mantel_plot_contract()["links"]
    assert isinstance(contract, Mapping)
    curvature = float(contract["curve_curvature"])

    rendered: list[PathPatch] = []
    for source in geometry.source_positions:
        source_links = sorted(
            grouped[source],
            key=lambda link: (target_order[link.target], link.target),
        )
        for link in source_links:
            style = _link_style(link, spec)
            if style is None:
                continue
            color, alpha = style
            start = geometry.source_positions[source]
            end = geometry.target_positions[link.target]
            sign = curvature_sign(target_order[link.target], len(target_order))
            vertices = _quadratic_vertices(
                start,
                end,
                geometry=geometry,
                curvature=curvature,
                sign=sign,
            )
            artist = PathPatch(
                Path(vertices, (Path.MOVETO, Path.CURVE3, Path.CURVE3)),
                facecolor="none",
                edgecolor=color,
                alpha=alpha,
                linewidth=_link_width(link.mantel_r, spec.width_mode),
                capstyle="round",
                clip_on=True,
                zorder=4,
            )
            artist.set_gid("axiomfig-mantel-link")
            metadata = {
                "_axiomfig_source": link.source,
                "_axiomfig_target": link.target,
                "_axiomfig_source_group": link.source,
                "_axiomfig_target_label": link.target,
                "_axiomfig_mantel_r": link.mantel_r,
                "_axiomfig_p_value": link.p_value,
                "_axiomfig_label": link.label,
                "_axiomfig_metadata": dict(link.metadata),
                "_axiomfig_route_model": "source-target-quadratic",
                "_axiomfig_curvature": curvature,
                "_axiomfig_curvature_sign": sign,
                "_axiomfig_route_signature": (
                    link.source,
                    link.target,
                    *(round(value, 6) for vertex in vertices for value in vertex),
                ),
            }
            for name, value in metadata.items():
                setattr(artist, name, value)
            axis.add_patch(artist)
            rendered.append(artist)
    return tuple(rendered)


__all__ = ["curvature_sign", "render_coupling_layer"]
