"""Renderer-aware Mantel matrix, target-rail, source, and ornament geometry.

The matrix owns one logical row/column coordinate system. Text and legend gutters are measured
in physical points before that system is solved; every visual layer then consumes one shared
cell geometry. No glyph, overlay, or coupling primitive estimates layout from character count.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

import matplotlib as mpl
import numpy as np
from matplotlib.figure import Figure
from matplotlib.font_manager import FontProperties

from axiomfig.style import mantel_plot_contract


@dataclass(frozen=True)
class MatrixBounds:
    x0: float
    y0: float
    size: int

    @property
    def x1(self) -> float:
        return self.x0 + self.size

    @property
    def y1(self) -> float:
        return self.y0 + self.size


@dataclass(frozen=True)
class TextExtents:
    variable_width_pt: float
    variable_height_pt: float
    source_width_pt: float
    source_height_pt: float
    source_labels: tuple[str, ...]


@dataclass(frozen=True)
class MantelLayoutMeasurements:
    """Physical inputs used by the fixed-pass Mantel constraint solver."""

    available_width_pt: float
    available_height_pt: float
    variable_width_pt: float
    variable_height_pt: float
    source_width_pt: float
    source_height_pt: float
    strength_legend_width_pt: float
    strength_legend_height_pt: float
    p_legend_width_pt: float
    p_legend_height_pt: float

    @classmethod
    def for_test(
        cls,
        *,
        variable_width_pt: float = 36.0,
        variable_height_pt: float = 8.0,
        source_width_pt: float = 42.0,
        source_height_pt: float = 8.0,
        available_width_pt: float = 320.0,
        available_height_pt: float = 240.0,
    ) -> MantelLayoutMeasurements:
        return cls(
            available_width_pt=available_width_pt,
            available_height_pt=available_height_pt,
            variable_width_pt=variable_width_pt,
            variable_height_pt=variable_height_pt,
            source_width_pt=source_width_pt,
            source_height_pt=source_height_pt,
            strength_legend_width_pt=116.0,
            strength_legend_height_pt=25.0,
            p_legend_width_pt=118.0,
            p_legend_height_pt=34.0,
        )


@dataclass(frozen=True)
class TargetRail:
    orientation: str
    anchors: dict[str, tuple[float, float]]


@dataclass(frozen=True)
class SourceRail:
    corner: str
    positions: dict[str, tuple[float, float]]
    start: tuple[float, float] | None
    end: tuple[float, float] | None
    normal_offset: float


@dataclass(frozen=True)
class MantelGeometry:
    bounds: MatrixBounds
    matrix_type: str
    target_rail: TargetRail
    source_rail: SourceRail
    x_limits: tuple[float, float]
    y_limits: tuple[float, float]
    strength_legend_anchor: tuple[float, float]
    p_legend_anchor: tuple[float, float]
    legend_arrangement: str
    cell_size_pt: float
    measurements: MantelLayoutMeasurements
    matrix_region: str
    coupling_region: str
    label_edges: tuple[str, ...]

    @property
    def source_positions(self) -> dict[str, tuple[float, float]]:
        return self.source_rail.positions

    @property
    def target_positions(self) -> dict[str, tuple[float, float]]:
        return self.target_rail.anchors


def variable_label_size(count: int) -> float:
    if count >= 18:
        return float(mpl.rcParams["font.size"]) * 0.66
    if count >= 14:
        return float(mpl.rcParams["font.size"]) * 0.72
    return float(mpl.rcParams["font.size"]) * 0.80


def source_label_size() -> float:
    return float(mpl.rcParams["font.size"]) * 0.82


def _maximum_text_extent(
    renderer: object,
    values: tuple[str, ...],
    properties: FontProperties,
    *,
    dpi: float,
) -> tuple[float, float]:
    if not values:
        return 0.0, 0.0
    dimensions = [
        renderer.get_text_width_height_descent(value, properties, ismath=False)[:2]  # type: ignore[attr-defined]
        for value in values
    ]
    scale = 72.0 / dpi
    return (
        max(float(width) for width, _ in dimensions) * scale,
        max(float(height) for _, height in dimensions) * scale,
    )


def measure_text_extents(
    figure: Figure,
    renderer: object,
    labels: tuple[str, ...],
    source_groups: tuple[str, ...],
) -> TextExtents:
    """Measure selected-font extents; equal character counts need not share a gutter."""
    variable = FontProperties(size=variable_label_size(len(labels)))
    source = FontProperties(size=source_label_size())
    variable_width, variable_height = _maximum_text_extent(
        renderer,
        labels,
        variable,
        dpi=figure.dpi,
    )
    contract = mantel_plot_contract()["matrix"]
    assert isinstance(contract, Mapping)
    maximum_source_width = float(contract["source_label_max_width_pt"])
    source_labels: list[str] = []
    source_dimensions: list[tuple[float, float]] = []
    for value in source_groups:
        words = value.split()
        candidates = [value]
        if len(words) > 1:
            candidates.extend(
                " ".join(words[:index]) + "\n" + " ".join(words[index:])
                for index in range(1, len(words))
            )
        measured: list[tuple[float, float, str]] = []
        for candidate in candidates:
            lines = candidate.splitlines()
            line_dimensions = [
                _maximum_text_extent(renderer, (line,), source, dpi=figure.dpi) for line in lines
            ]
            measured.append(
                (
                    max(width for width, _ in line_dimensions),
                    sum(height for _, height in line_dimensions) * 1.12,
                    candidate,
                )
            )
        unwrapped = measured[0]
        selected = (
            min(measured[1:], key=lambda item: (item[0], item[1], item[2]))
            if unwrapped[0] > maximum_source_width and len(measured) > 1
            else unwrapped
        )
        source_dimensions.append((selected[0], selected[1]))
        source_labels.append(selected[2])
    source_width = max((width for width, _ in source_dimensions), default=0.0)
    source_height = max((height for _, height in source_dimensions), default=0.0)
    return TextExtents(
        variable_width,
        variable_height,
        source_width,
        source_height,
        tuple(source_labels),
    )


def cell_center(
    bounds: MatrixBounds,
    row: int,
    column: int,
    *,
    matrix_type: str,
) -> tuple[float, float]:
    """Map logical matrix indices into the orientation-owned display coordinate system."""
    del matrix_type
    return bounds.x0 + column + 0.5, bounds.y1 - row - 0.5


def _target_anchor(
    bounds: MatrixBounds,
    index: int,
    *,
    matrix_type: str,
    rail_offset: float,
) -> tuple[float, float]:
    x, y = cell_center(bounds, index, index, matrix_type=matrix_type)
    if matrix_type in {"lower", "upper"}:
        return x + rail_offset, y + rail_offset
    return bounds.x0 - 0.05, y


def _source_positions(
    bounds: MatrixBounds,
    source_groups: tuple[str, ...],
    *,
    matrix_type: str,
    source_width_units: float,
    source_height_units: float,
    source_label_offset_units: float,
) -> SourceRail:
    """Place sources monotonically on one rail parallel to the target diagonal."""
    count = len(source_groups)
    if count == 0:
        return SourceRail("none", {}, None, None, 0.0)
    if matrix_type in {"lower", "upper"}:
        label_margin = max(
            0.28,
            source_height_units * 1.6,
            source_width_units / np.sqrt(2.0) + np.sqrt(2.0) * source_label_offset_units,
        )
        endpoint_fraction = float(
            np.clip(0.14 + 0.015 * count + 0.02 * label_margin / bounds.size, 0.22, 0.28)
        )
        normal_sign = 1.0 if matrix_type == "lower" else -1.0
        normal = normal_sign * np.asarray((1.0, 1.0), dtype=float) / np.sqrt(2.0)
        maximum_depth = np.sqrt(2.0) * bounds.size * endpoint_fraction - label_margin
        minimum_clearance = max(0.75, bounds.size * 0.05, source_height_units * 1.6)
        preferred_depth = max(
            bounds.size * 0.18,
            minimum_clearance + min(0.25, 0.04 * max(count - 1, 0)),
        )
        depth = min(preferred_depth, max(0.35, maximum_depth))

        def rail_point(fraction: float) -> np.ndarray:
            diagonal = np.asarray(
                (
                    bounds.x0 + bounds.size * fraction,
                    bounds.y1 - bounds.size * fraction,
                ),
                dtype=float,
            )
            return diagonal + normal * depth

        start = rail_point(endpoint_fraction)
        end = rail_point(1.0 - endpoint_fraction)
        points = np.linspace(start, end, count)
        positions = {
            source: (float(point[0]), float(point[1]))
            for source, point in zip(source_groups, points, strict=True)
        }
        corner = "upper-right" if matrix_type == "lower" else "lower-left"
        return SourceRail(
            corner,
            positions,
            (float(start[0]), float(start[1])),
            (float(end[0]), float(end[1])),
            float(depth),
        )

    source_y = np.linspace(bounds.y1 - 0.75, bounds.y0 + 0.75, count)
    positions = {
        source: (bounds.x0 - 0.65, float(y))
        for source, y in zip(source_groups, source_y, strict=True)
    }
    return SourceRail(
        "left",
        positions,
        (bounds.x0 - 0.65, float(source_y[0])),
        (bounds.x0 - 0.65, float(source_y[-1])),
        0.65,
    )


def _rail_orientation(matrix_type: str) -> str:
    if matrix_type in {"lower", "upper"}:
        return "upper-left-to-lower-right"
    return "left-vertical"


def _point_gutters(
    measurements: MantelLayoutMeasurements,
    *,
    matrix_type: str,
    coupling_enabled: bool,
) -> tuple[float, float, float, float, str]:
    padding = 4.0
    legend_gap = 6.0
    if matrix_type in {"full", "mixed"}:
        projection = (measurements.variable_width_pt + measurements.variable_height_pt) / np.sqrt(
            2.0
        )
        left = measurements.variable_width_pt + padding
        right = projection + padding * 2.0
        top = projection + padding * 2.0
        bottom = padding
    elif matrix_type == "lower":
        left = measurements.variable_width_pt + padding * 2.0
        right = padding
        top = padding
        bottom = measurements.variable_width_pt + padding * 2.0
    else:
        left = padding
        right = measurements.variable_width_pt + padding * 2.0
        top = measurements.variable_width_pt + padding * 2.0
        bottom = padding

    if not coupling_enabled:
        return left, right, bottom, top, "none"
    combined_width = (
        measurements.strength_legend_width_pt
        + measurements.p_legend_width_pt
        + legend_gap
        + padding * 2.0
    )
    if combined_width <= measurements.available_width_pt:
        legend_bottom = (
            max(
                measurements.strength_legend_height_pt,
                measurements.p_legend_height_pt,
            )
            + padding * 2.0
        )
        arrangement = "side-by-side"
    else:
        legend_bottom = (
            measurements.strength_legend_height_pt
            + measurements.p_legend_height_pt
            + legend_gap
            + padding * 2.0
        )
        arrangement = "stacked"
    bottom += legend_bottom
    return left, right, bottom, top, arrangement


def _region_contract(matrix_type: str) -> tuple[str, str, tuple[str, ...]]:
    if matrix_type == "lower":
        return "lower-left", "upper-right", ("left", "bottom")
    if matrix_type == "upper":
        return "upper-right", "lower-left", ("top", "right")
    return "full", "none", ("left", "top")


def solve_geometry(
    labels: tuple[str, ...],
    source_groups: tuple[str, ...],
    *,
    matrix_type: str,
    measurements: MantelLayoutMeasurements | None = None,
) -> MantelGeometry:
    """Solve matrix, rail, source region, and ornaments from renderer-derived extents."""
    size = len(labels)
    if size < 1:
        raise ValueError("Mantel geometry requires at least one matrix label")
    measurements = measurements or MantelLayoutMeasurements.for_test()
    coupling_enabled = bool(source_groups)
    left_pt, right_pt, bottom_pt, top_pt, arrangement = _point_gutters(
        measurements,
        matrix_type=matrix_type,
        coupling_enabled=coupling_enabled,
    )
    cell_width = (measurements.available_width_pt - left_pt - right_pt) / size
    cell_height = (measurements.available_height_pt - bottom_pt - top_pt) / size
    cell_size_pt = min(cell_width, cell_height)
    if cell_size_pt <= 4.0:
        raise ValueError("measured Mantel labels and ornaments do not fit the physical panel")

    left = left_pt / cell_size_pt
    right = right_pt / cell_size_pt
    bottom = bottom_pt / cell_size_pt
    top = top_pt / cell_size_pt
    bounds = MatrixBounds(left, bottom, size)

    matrix_contract = mantel_plot_contract()["matrix"]
    assert isinstance(matrix_contract, Mapping)
    rail_offset = float(matrix_contract["target_rail_offset"])
    anchors = {
        label: _target_anchor(
            bounds,
            index,
            matrix_type=matrix_type,
            rail_offset=rail_offset,
        )
        for index, label in enumerate(labels)
    }
    rail = TargetRail(_rail_orientation(matrix_type), anchors)
    sources = _source_positions(
        bounds,
        source_groups,
        matrix_type=matrix_type,
        source_width_units=measurements.source_width_pt / cell_size_pt,
        source_height_units=measurements.source_height_pt / cell_size_pt,
        source_label_offset_units=float(matrix_contract["source_label_offset_pt"]) / cell_size_pt,
    )
    matrix_region, coupling_region, label_edges = _region_contract(matrix_type)

    padding_units = 4.0 / cell_size_pt
    legend_gap_units = 6.0 / cell_size_pt
    p_anchor = (padding_units, padding_units)
    if arrangement == "side-by-side":
        strength_anchor = (
            padding_units + measurements.p_legend_width_pt / cell_size_pt + legend_gap_units,
            padding_units,
        )
    elif arrangement == "stacked":
        strength_anchor = (
            padding_units,
            padding_units + measurements.p_legend_height_pt / cell_size_pt + legend_gap_units,
        )
    else:
        strength_anchor = p_anchor

    return MantelGeometry(
        bounds=bounds,
        matrix_type=matrix_type,
        target_rail=rail,
        source_rail=sources,
        x_limits=(0.0, bounds.x1 + right),
        y_limits=(0.0, bounds.y1 + top),
        strength_legend_anchor=strength_anchor,
        p_legend_anchor=p_anchor,
        legend_arrangement=arrangement,
        cell_size_pt=cell_size_pt,
        measurements=measurements,
        matrix_region=matrix_region,
        coupling_region=coupling_region,
        label_edges=label_edges,
    )


__all__ = [
    "MantelGeometry",
    "MantelLayoutMeasurements",
    "MatrixBounds",
    "SourceRail",
    "TargetRail",
    "TextExtents",
    "cell_center",
    "measure_text_extents",
    "solve_geometry",
    "source_label_size",
    "variable_label_size",
]
