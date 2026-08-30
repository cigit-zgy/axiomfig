"""Mantel coupling layer constrained to the unused triangular matrix half-plane."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping

import numpy as np
from matplotlib.axes import Axes
from matplotlib.patches import PathPatch
from matplotlib.path import Path
from matplotlib.transforms import Bbox

from axiomfig.style import (
    mantel_link_width,
    mantel_p_style,
    mantel_plot_contract,
)
from axiomfig.templates.association.mantel.composition import CouplingSpec
from axiomfig.templates.association.mantel.data import MantelLink
from axiomfig.templates.association.mantel.geometry import MantelGeometry


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


def _coupling_normal(matrix_type: str) -> np.ndarray:
    sign = 1.0 if matrix_type == "lower" else -1.0
    return sign * np.asarray((1.0, 1.0), dtype=float) / np.sqrt(2.0)


def _lane_anchor(
    geometry: MantelGeometry,
    *,
    lane_fraction: float,
    envelope_fraction: float,
    source_depth: float,
) -> np.ndarray:
    bounds = geometry.bounds
    fraction = 0.18 + 0.64 * lane_fraction
    diagonal = np.asarray(
        (
            bounds.x0 + bounds.size * fraction,
            bounds.y1 - bounds.size * fraction,
        ),
        dtype=float,
    )
    maximum_depth = np.sqrt(2.0) * bounds.size * min(fraction, 1.0 - fraction)
    depth = min(
        maximum_depth * 0.82,
        source_depth * 0.72,
        max(maximum_depth * envelope_fraction, min(0.30, maximum_depth * 0.60)),
    )
    return diagonal + _coupling_normal(geometry.matrix_type) * depth


def _route_vertices(
    start: tuple[float, float],
    end: tuple[float, float],
    *,
    fan_point: np.ndarray,
    lane_anchor: np.ndarray,
) -> tuple[tuple[float, float], ...]:
    """Create one smooth fanned cubic using a source exit and target-side lane control.

    The local fan exit makes departures legible. The second control pulls the route toward its
    selected envelope without forcing the curve through a visible bend. De Casteljau subdivision
    retains the existing seven-vertex metadata without changing the cubic geometry.
    """
    start_array = np.asarray(start, dtype=float)
    end_array = np.asarray(end, dtype=float)
    target_control = 0.68 * end_array + 0.32 * lane_anchor
    first = 0.5 * (start_array + fan_point)
    middle = 0.5 * (fan_point + target_control)
    last = 0.5 * (target_control + end_array)
    first_middle = 0.5 * (first + middle)
    last_middle = 0.5 * (middle + last)
    split = 0.5 * (first_middle + last_middle)
    return (
        start,
        (float(first[0]), float(first[1])),
        (float(first_middle[0]), float(first_middle[1])),
        (float(split[0]), float(split[1])),
        (float(last_middle[0]), float(last_middle[1])),
        (float(last[0]), float(last[1])),
        end,
    )


def _source_fan_point(
    geometry: MantelGeometry,
    start: tuple[float, float],
    *,
    rank: int,
    link_count: int,
) -> np.ndarray:
    """Return a local fan exit that points toward the rail and away from source labels."""
    start_array = np.asarray(start, dtype=float)
    toward_rail = -_coupling_normal(geometry.matrix_type)
    tangent = np.asarray((-toward_rail[1], toward_rail[0]), dtype=float)
    if link_count <= 1:
        angle = 0.0
    else:
        span = min(np.deg2rad(64.0), np.deg2rad(12.0) * (link_count - 1))
        angle = -span / 2.0 + span * rank / (link_count - 1)
    direction = np.cos(angle) * toward_rail + np.sin(angle) * tangent
    bounds = geometry.bounds
    diagonal = bounds.x0 + bounds.y1
    depth = abs(float(start_array[0] + start_array[1] - diagonal)) / np.sqrt(2.0)
    distance = min(0.58, max(0.24, depth * 0.24))
    return start_array + direction * distance


def _source_depth(geometry: MantelGeometry, start: tuple[float, float]) -> float:
    bounds = geometry.bounds
    diagonal = bounds.x0 + bounds.y1
    point = np.asarray(start, dtype=float)
    return abs(float(point[0] + point[1] - diagonal)) / np.sqrt(2.0)


def _cubic(control: np.ndarray, value: float) -> np.ndarray:
    inverse = 1.0 - value
    return (
        inverse**3 * control[0]
        + 3.0 * inverse**2 * value * control[1]
        + 3.0 * inverse * value**2 * control[2]
        + value**3 * control[3]
    )


def _obstacle_hits(vertices: tuple[tuple[float, float], ...], obstacles: tuple[Bbox, ...]) -> int:
    if not obstacles:
        return 0
    array = np.asarray(vertices, dtype=float)
    values = np.linspace(0.02, 0.98, 49)
    padded = tuple(box.padded(0.05) for box in obstacles)
    samples = (
        *(_cubic(array[:4], float(value)) for value in values),
        *(_cubic(array[3:7], float(value)) for value in values),
    )
    return sum(any(box.contains(*point) for box in padded) for point in samples)


def _lane_fractions(
    *,
    rank: int,
    link_count: int,
    target_index: int,
    target_count: int,
    source_index: int,
    source_count: int,
) -> tuple[float, ...]:
    target_fraction = (target_index + 0.5) / target_count
    source_fraction = (source_index + 0.5) / source_count
    rank_offset = (rank - (link_count - 1) / 2.0) * 0.018
    base = float(np.clip(0.72 * target_fraction + 0.28 * source_fraction + rank_offset, 0.06, 0.94))
    semantic = (
        base,
        *(
            float(np.clip(base + offset, 0.06, 0.94))
            for offset in (-0.18, -0.12, -0.06, 0.06, 0.12, 0.18)
        ),
        target_fraction,
        source_fraction,
        0.12,
        0.88,
        0.28,
        0.72,
        0.50,
    )
    return tuple(dict.fromkeys(round(float(value), 6) for value in semantic))


def _route_samples(vertices: tuple[tuple[float, float], ...], *, count: int = 7) -> np.ndarray:
    array = np.asarray(vertices, dtype=float)
    values = np.linspace(0.04, 0.96, count)
    return np.asarray(
        [
            *(_cubic(array[:4], float(value)) for value in values),
            *(_cubic(array[3:7], float(value)) for value in values),
        ]
    )


def _cross(first: np.ndarray, second: np.ndarray) -> np.ndarray:
    return first[..., 0] * second[..., 1] - first[..., 1] * second[..., 0]


def _route_interference(
    samples: np.ndarray,
    selected_routes: tuple[np.ndarray, ...],
) -> tuple[int, int]:
    crossings = 0
    proximity = 0
    candidate_start = samples[:-1, None, :]
    candidate_end = samples[1:, None, :]
    candidate_vector = candidate_end - candidate_start
    for selected in selected_routes:
        selected_start = selected[None, :-1, :]
        selected_end = selected[None, 1:, :]
        selected_vector = selected_end - selected_start
        candidate_sides = _cross(
            candidate_vector,
            selected_start - candidate_start,
        ) * _cross(
            candidate_vector,
            selected_end - candidate_start,
        )
        selected_sides = _cross(
            selected_vector,
            candidate_start - selected_start,
        ) * _cross(
            selected_vector,
            candidate_end - selected_start,
        )
        crossings += int(np.count_nonzero((candidate_sides < -1e-9) & (selected_sides < -1e-9)))
        distances = np.linalg.norm(samples[:, None, :] - selected[None, :, :], axis=2)
        proximity += int(np.count_nonzero(distances[2:-2, 2:-2] < 0.055))
    return crossings, proximity


def render_coupling_layer(
    axis: Axes,
    links: tuple[MantelLink, ...],
    spec: CouplingSpec,
    geometry: MantelGeometry,
    *,
    label_obstacles: tuple[Bbox, ...] = (),
) -> tuple[PathPatch, ...]:
    """Render source nodes and deterministic matrix-attached Mantel arcs."""
    if not spec.enabled:
        return ()
    grouped: dict[str, list[MantelLink]] = defaultdict(list)
    for link in links:
        grouped[link.source].append(link)
    target_order = {label: index for index, label in enumerate(geometry.target_rail.anchors)}
    source_order = {source: index for index, source in enumerate(geometry.source_region.positions)}

    rendered: list[PathPatch] = []
    selected_routes: list[np.ndarray] = []
    for source in geometry.source_region.positions:
        used_lanes: list[float] = []
        source_links = sorted(
            grouped[source],
            key=lambda link: (target_order[link.target], link.target),
        )
        for rank, link in enumerate(source_links):
            style = _link_style(link, spec)
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
            envelope_fraction = float(
                np.clip(
                    0.44
                    + 0.08 * (source_order[source] % 3)
                    + 0.025 * min(len(source_links) - 1, 6)
                    + 0.04 * min(clearance, 1.0),
                    0.44,
                    0.72,
                )
            )
            candidates = []
            source_depth = _source_depth(geometry, start)
            target_fraction = (target_order[link.target] + 0.5) / len(target_order)
            source_fraction = (source_order[source] + 0.5) / len(source_order)
            base_lane = float(
                np.clip(
                    0.72 * target_fraction
                    + 0.28 * source_fraction
                    + (rank - (len(source_links) - 1) / 2.0) * 0.018,
                    0.06,
                    0.94,
                )
            )
            fan_point = _source_fan_point(
                geometry,
                start,
                rank=rank,
                link_count=len(source_links),
            )
            lane_fractions = _lane_fractions(
                rank=rank,
                link_count=len(source_links),
                target_index=target_order[link.target],
                target_count=len(target_order),
                source_index=source_order[source],
                source_count=len(source_order),
            )
            for candidate_index, lane_fraction in enumerate(lane_fractions):
                lane_anchor = _lane_anchor(
                    geometry,
                    lane_fraction=lane_fraction,
                    envelope_fraction=float(
                        np.clip(
                            envelope_fraction + 0.08 * (lane_fraction - base_lane),
                            0.38,
                            0.76,
                        )
                    ),
                    source_depth=source_depth,
                )
                candidate = _route_vertices(
                    start,
                    end,
                    fan_point=fan_point,
                    lane_anchor=lane_anchor,
                )
                samples = _route_samples(candidate)
                crossings, proximity = _route_interference(samples, tuple(selected_routes))
                length = sum(
                    np.linalg.norm(second - first)
                    for first, second in zip(
                        np.asarray(candidate[:-1]),
                        np.asarray(candidate[1:]),
                        strict=True,
                    )
                )
                candidates.append(
                    (
                        _obstacle_hits(candidate, label_obstacles),
                        crossings,
                        proximity,
                        min(
                            (abs(lane_fraction - selected) for selected in used_lanes),
                            default=1.0,
                        )
                        < 0.08,
                        abs(lane_fraction - base_lane),
                        float(length),
                        candidate_index,
                        candidate,
                        samples,
                        lane_fraction,
                    )
                )
            (
                selected_hits,
                selected_crossings,
                selected_proximity,
                _,
                _,
                _,
                _,
                vertices,
                selected_samples,
                selected_lane,
            ) = min(candidates, key=lambda item: item[:7])
            used_lanes.append(selected_lane)
            selected_routes.append(selected_samples)
            path = Path(
                vertices,
                (
                    Path.MOVETO,
                    Path.CURVE4,
                    Path.CURVE4,
                    Path.CURVE4,
                    Path.CURVE4,
                    Path.CURVE4,
                    Path.CURVE4,
                ),
            )
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
            artist._axiomfig_route_model = "triangle-fan-cubic"
            artist._axiomfig_lane_fraction = selected_lane
            artist._axiomfig_source_label_intersections = selected_hits
            artist._axiomfig_prior_route_crossings = selected_crossings
            artist._axiomfig_prior_route_proximity = selected_proximity
            artist._axiomfig_route_signature = (
                link.source,
                link.target,
                *(round(value, 6) for vertex in vertices for value in vertex),
            )
            axis.add_patch(artist)
            rendered.append(artist)
    return tuple(rendered)


__all__ = ["nice_curvature", "render_coupling_layer"]
