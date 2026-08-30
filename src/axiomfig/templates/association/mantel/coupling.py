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
    clearance: float,
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
    depth = min(maximum_depth * 0.62, max(0.45, clearance * 1.25))
    return diagonal + _coupling_normal(geometry.matrix_type) * depth


def _route_vertices(
    start: tuple[float, float],
    end: tuple[float, float],
    *,
    lane_anchor: np.ndarray,
) -> tuple[tuple[float, float], ...]:
    """Create two fanned cubics whose convex control polygons stay in the coupling triangle.

    Start, target, and lane anchor are all inside the complementary triangle. Convex combinations
    of those points therefore cannot enter the colored matrix triangle.
    """
    start_array = np.asarray(start, dtype=float)
    end_array = np.asarray(end, dtype=float)
    diagonal_origin = np.asarray((end_array[0], end_array[1]), dtype=float)
    normal = np.asarray((1.0, 1.0), dtype=float) / np.sqrt(2.0)
    source_depth = float(np.dot(start_array - diagonal_origin, normal))
    projection = start_array - normal * source_depth
    fan_exit = 0.15 * start_array + 0.65 * projection + 0.20 * lane_anchor
    control1 = 0.05 * start_array + 0.55 * projection + 0.40 * lane_anchor
    control2 = 0.05 * start_array + 0.80 * fan_exit + 0.15 * lane_anchor
    control3 = 0.75 * fan_exit + 0.15 * end_array + 0.10 * lane_anchor
    control4 = 0.03 * fan_exit + 0.90 * end_array + 0.07 * lane_anchor
    return (
        start,
        (float(control1[0]), float(control1[1])),
        (float(control2[0]), float(control2[1])),
        (float(fan_exit[0]), float(fan_exit[1])),
        (float(control3[0]), float(control3[1])),
        (float(control4[0]), float(control4[1])),
        end,
    )


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
    values = np.linspace(0.04, 0.96, 25)
    samples = (
        *(_cubic(array[:4], float(value)) for value in values),
        *(_cubic(array[3:7], float(value)) for value in values),
    )
    return sum(any(box.contains(*point) for box in obstacles) for point in samples)


def _lane_fractions(
    *,
    rank: int,
    link_count: int,
    target_index: int,
    target_count: int,
    source_index: int,
    source_count: int,
) -> tuple[float, ...]:
    base = (rank + 1.0) / (link_count + 1.0)
    semantic = (
        base,
        *(
            float(np.clip(base + offset, 0.06, 0.94))
            for offset in (-0.18, -0.12, -0.06, 0.06, 0.12, 0.18)
        ),
        (target_index + 0.5) / target_count,
        (source_index + 0.5) / source_count,
        0.12,
        0.88,
        0.28,
        0.72,
        0.50,
    )
    return tuple(dict.fromkeys(round(float(value), 6) for value in semantic))


def _route_samples(vertices: tuple[tuple[float, float], ...], *, count: int = 13) -> np.ndarray:
    array = np.asarray(vertices, dtype=float)
    values = np.linspace(0.04, 0.96, count)
    return np.asarray(
        [
            *(_cubic(array[:4], float(value)) for value in values),
            *(_cubic(array[3:7], float(value)) for value in values),
        ]
    )


def _segment_crosses(
    first_start: np.ndarray,
    first_end: np.ndarray,
    second_start: np.ndarray,
    second_end: np.ndarray,
) -> bool:
    def side(origin: np.ndarray, end: np.ndarray, point: np.ndarray) -> float:
        vector = end - origin
        relative = point - origin
        return float(vector[0] * relative[1] - vector[1] * relative[0])

    first_a = side(first_start, first_end, second_start)
    first_b = side(first_start, first_end, second_end)
    second_a = side(second_start, second_end, first_start)
    second_b = side(second_start, second_end, first_end)
    tolerance = 1e-9
    return first_a * first_b < -tolerance and second_a * second_b < -tolerance


def _route_interference(
    samples: np.ndarray,
    selected_routes: tuple[np.ndarray, ...],
) -> tuple[int, int]:
    crossings = 0
    proximity = 0
    for selected in selected_routes:
        crossings += sum(
            _segment_crosses(first_start, first_end, second_start, second_end)
            for first_start, first_end in zip(samples[:-1], samples[1:], strict=True)
            for second_start, second_end in zip(selected[:-1], selected[1:], strict=True)
        )
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
            candidates = []
            base_lane = (rank + 1.0) / (len(source_links) + 1.0)
            for candidate_index, lane_fraction in enumerate(
                _lane_fractions(
                    rank=rank,
                    link_count=len(source_links),
                    target_index=target_order[link.target],
                    target_count=len(target_order),
                    source_index=source_order[source],
                    source_count=len(source_order),
                )
            ):
                lane_anchor = _lane_anchor(
                    geometry,
                    lane_fraction=lane_fraction,
                    clearance=clearance,
                )
                candidate = _route_vertices(start, end, lane_anchor=lane_anchor)
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
            artist._axiomfig_route_model = "triangle-fan-double-cubic"
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
