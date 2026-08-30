"""Deterministic rendered-geometry metrics for Mantel visual regression gates."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from itertools import combinations

import numpy as np
from matplotlib.transforms import Bbox


@dataclass(frozen=True)
class MantelVisualMetrics:
    matrix_occupancy_ratio: float
    visible_content_occupancy_ratio: float
    dead_space_ratio: float
    source_rail_min_distance_pt: float
    source_label_clearance_pt: float
    legend_overlap_count: int
    legend_matrix_overlap_count: int
    label_overlap_count: int
    link_matrix_intersection_count: int
    link_label_intersection_count: int
    route_midpoint_separation_pt: float


def _artists(figure: object, *gids: str) -> list[object]:
    selected = set(gids)
    return [
        artist
        for axis in figure.axes  # type: ignore[attr-defined]
        for artist in axis.get_children()
        if artist.get_gid() in selected
    ]


def _bbox(artist: object, renderer: object) -> Bbox:
    return artist.get_window_extent(renderer)  # type: ignore[attr-defined]


def _bbox_gap(first: Bbox, second: Bbox) -> float:
    horizontal = max(first.x0 - second.x1, second.x0 - first.x1, 0.0)
    vertical = max(first.y0 - second.y1, second.y0 - first.y1, 0.0)
    return float(np.hypot(horizontal, vertical))


def _union_area(boxes: list[Bbox], boundary: Bbox) -> float:
    if not boxes:
        return 0.0
    clipped = [box for box in (Bbox.intersection(item, boundary) for item in boxes) if box]
    if not clipped:
        return 0.0
    union = Bbox.union(clipped)
    return float(union.width * union.height)


def _cubic(vertices: np.ndarray, t: float) -> np.ndarray:
    one_minus = 1.0 - t
    return (
        one_minus**3 * vertices[0]
        + 3.0 * one_minus**2 * t * vertices[1]
        + 3.0 * one_minus * t**2 * vertices[2]
        + t**3 * vertices[3]
    )


def _route_samples(link: object, count: int = 49) -> np.ndarray:
    vertices = np.asarray(link.get_path().vertices, dtype=float)  # type: ignore[attr-defined]
    values = np.linspace(0.04, 0.96, count)
    data = np.asarray([_cubic(vertices, float(value)) for value in values])
    return link.get_transform().transform(data)  # type: ignore[attr-defined]


def _route_intersections(links: list[object], matrix_boxes: list[Bbox]) -> int:
    intersections = 0
    interiors = [
        Bbox.from_extents(box.x0 + 1.0, box.y0 + 1.0, box.x1 - 1.0, box.y1 - 1.0)
        for box in matrix_boxes
        if box.width > 2.0 and box.height > 2.0
    ]
    for link in links:
        samples = _route_samples(link)
        if any(any(box.contains(*point) for box in interiors) for point in samples):
            intersections += 1
    return intersections


def _route_label_intersections(links: list[object], label_boxes: list[Bbox]) -> int:
    intersections = 0
    for link in links:
        samples = _route_samples(link)
        if any(any(box.contains(*point) for box in label_boxes) for point in samples):
            intersections += 1
    return intersections


def _source_rail_distance_pt(figure: object) -> float:
    geometry = figure._axiomfig_mantel_geometry  # type: ignore[attr-defined]
    if not geometry.source_positions:
        return float("inf")
    axis = figure.axes[0]  # type: ignore[attr-defined]
    rail = axis.transData.transform(np.asarray(tuple(geometry.target_positions.values())))
    sources = axis.transData.transform(np.asarray(tuple(geometry.source_positions.values())))
    start, end = rail[0], rail[-1]
    vector = end - start
    distances = [
        abs(float(vector[0] * (point[1] - start[1]) - vector[1] * (point[0] - start[0])))
        / np.linalg.norm(vector)
        for point in sources
    ]
    return min(distances) * 72.0 / figure.dpi  # type: ignore[attr-defined]


def _route_separation_pt(figure: object, links: list[object]) -> float:
    grouped: dict[str, list[np.ndarray]] = defaultdict(list)
    for link in links:
        vertices = np.asarray(link.get_path().vertices, dtype=float)  # type: ignore[attr-defined]
        midpoint = _cubic(vertices, 0.5)
        grouped[str(link._axiomfig_source)].append(  # type: ignore[attr-defined]
            link.get_transform().transform(midpoint)  # type: ignore[attr-defined]
        )
    distances = [
        float(np.linalg.norm(first - second))
        for points in grouped.values()
        for first, second in combinations(points, 2)
    ]
    if not distances:
        return float("inf")
    return min(distances) * 72.0 / figure.dpi  # type: ignore[attr-defined]


def measure_mantel_visual_quality(figure: object) -> MantelVisualMetrics:
    """Measure visible geometry after a real renderer draw without relaxing runtime validation."""
    figure.canvas.draw()  # type: ignore[attr-defined]
    renderer = figure.canvas.get_renderer()  # type: ignore[attr-defined]
    axis = figure.axes[0]  # type: ignore[attr-defined]
    axis_box = axis.bbox
    scale = 72.0 / figure.dpi  # type: ignore[attr-defined]

    matrix = _artists(figure, "axiomfig-mantel-grid-cell")
    matrix_boxes = [_bbox(artist, renderer) for artist in matrix]
    matrix_area = sum(box.width * box.height for box in matrix_boxes)
    axis_area = axis_box.width * axis_box.height

    content_gids = (
        "axiomfig-mantel-grid-cell",
        "axiomfig-mantel-glyph",
        "axiomfig-mantel-variable-label",
        "axiomfig-mantel-column-label",
        "axiomfig-mantel-source-label",
        "axiomfig-mantel-source-node",
        "axiomfig-mantel-link",
        "axiomfig-mantel-legend",
    )
    content_boxes = [_bbox(artist, renderer) for artist in _artists(figure, *content_gids)]
    visible_ratio = _union_area(content_boxes, axis_box) / axis_area

    legends = [_bbox(artist, renderer) for artist in _artists(figure, "axiomfig-mantel-legend")]
    labels = [
        _bbox(artist, renderer)
        for artist in _artists(
            figure,
            "axiomfig-mantel-variable-label",
            "axiomfig-mantel-column-label",
            "axiomfig-mantel-source-label",
        )
    ]
    source_labels = [
        _bbox(artist, renderer) for artist in _artists(figure, "axiomfig-mantel-source-label")
    ]
    links = _artists(figure, "axiomfig-mantel-link")
    source_clearances = [
        _bbox_gap(first, second) * scale for first, second in combinations(source_labels, 2)
    ]

    return MantelVisualMetrics(
        matrix_occupancy_ratio=float(matrix_area / axis_area),
        visible_content_occupancy_ratio=float(visible_ratio),
        dead_space_ratio=float(1.0 - visible_ratio),
        source_rail_min_distance_pt=_source_rail_distance_pt(figure),
        source_label_clearance_pt=min(source_clearances, default=float("inf")),
        legend_overlap_count=sum(
            first.overlaps(second) for first, second in combinations(legends, 2)
        ),
        legend_matrix_overlap_count=sum(
            legend.overlaps(cell) for legend in legends for cell in matrix_boxes
        ),
        label_overlap_count=sum(
            first.overlaps(second) for first, second in combinations(labels, 2)
        ),
        link_matrix_intersection_count=_route_intersections(links, matrix_boxes),
        link_label_intersection_count=_route_label_intersections(links, source_labels),
        route_midpoint_separation_pt=_route_separation_pt(figure, links),
    )


__all__ = ["MantelVisualMetrics", "measure_mantel_visual_quality"]
