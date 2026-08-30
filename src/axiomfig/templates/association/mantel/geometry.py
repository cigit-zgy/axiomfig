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
class SourceRegion:
    corner: str
    positions: dict[str, tuple[float, float]]


@dataclass(frozen=True)
class MantelGeometry:
    bounds: MatrixBounds
    matrix_type: str
    target_rail: TargetRail
    source_region: SourceRegion
    x_limits: tuple[float, float]
    y_limits: tuple[float, float]
    strength_legend_anchor: tuple[float, float]
    p_legend_anchor: tuple[float, float]
    legend_arrangement: str
    cell_size_pt: float
    measurements: MantelLayoutMeasurements

    @property
    def source_positions(self) -> dict[str, tuple[float, float]]:
        return self.source_region.positions

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
    source_width, source_height = _maximum_text_extent(
        renderer,
        source_groups,
        source,
        dpi=figure.dpi,
    )
    return TextExtents(variable_width, variable_height, source_width, source_height)


def cell_center(
    bounds: MatrixBounds,
    row: int,
    column: int,
    *,
    matrix_type: str,
) -> tuple[float, float]:
    """Map logical matrix indices into the orientation-owned display coordinate system."""
    if matrix_type == "lower":
        x = bounds.x0 + column + 0.5
        y = bounds.y0 + row + 0.5
    elif matrix_type == "upper":
        # Upper presentation is the physical horizontal mirror of the lower composition.
        # Swapping row/column ownership before mirroring preserves scientific upper-mask
        # indexing while placing its visible cells opposite the mirrored source region.
        x = bounds.x0 + row + 0.5
        y = bounds.y1 - column - 0.5
    else:
        x = bounds.x0 + column + 0.5
        y = bounds.y1 - row - 0.5
    return x, y


def _target_anchor(
    bounds: MatrixBounds,
    index: int,
    *,
    matrix_type: str,
    rail_offset: float,
) -> tuple[float, float]:
    x, y = cell_center(bounds, index, index, matrix_type=matrix_type)
    if matrix_type == "lower":
        return x + rail_offset, y - rail_offset
    if matrix_type == "upper":
        return x + rail_offset, y + rail_offset
    return bounds.x0 - 0.05, y


def _source_positions(
    bounds: MatrixBounds,
    source_groups: tuple[str, ...],
    *,
    matrix_type: str,
    source_width_units: float,
    source_height_units: float,
) -> SourceRegion:
    """Place sources on a measured horizontal rail at the empty triangle's outer edge."""
    count = len(source_groups)
    if count == 0:
        return SourceRegion("none", {})
    label_half = source_width_units / 2.0
    first_x = max(0.65, label_half + 0.24)
    step = source_width_units + 0.38
    last_x = first_x + step * (count - 1)
    available_last = bounds.size - max(0.35, label_half)
    if count == 1:
        x_positions = np.asarray((min(first_x, available_last),))
    else:
        x_positions = np.linspace(first_x, min(last_x, available_last), count)
    relative_y = max(0.16, source_height_units * 0.34)
    lower_positions = {
        source: (bounds.x0 + float(x), bounds.y0 + relative_y)
        for source, x in zip(source_groups, x_positions, strict=True)
    }

    if matrix_type == "lower":
        return SourceRegion("lower-left", lower_positions)
    if matrix_type == "upper":
        mirrored = {
            source: (x, bounds.y0 + bounds.y1 - y) for source, (x, y) in lower_positions.items()
        }
        return SourceRegion("upper-left", mirrored)

    source_y = np.linspace(bounds.y1 - 0.75, bounds.y0 + 0.75, count)
    return SourceRegion(
        "left",
        {
            source: (bounds.x0 - 0.65, float(y))
            for source, y in zip(source_groups, source_y, strict=True)
        },
    )


def _rail_orientation(matrix_type: str) -> str:
    if matrix_type == "lower":
        return "lower-left-to-upper-right"
    if matrix_type == "upper":
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
    else:
        left = padding
        right = measurements.variable_width_pt + padding
        top = padding if coupling_enabled else measurements.variable_width_pt + padding * 2.0

    if not coupling_enabled:
        return left, right, padding, top, "none"
    combined_width = (
        measurements.strength_legend_width_pt
        + measurements.p_legend_width_pt
        + legend_gap
        + padding * 2.0
    )
    if combined_width <= measurements.available_width_pt:
        bottom = (
            max(
                measurements.strength_legend_height_pt,
                measurements.p_legend_height_pt,
            )
            + padding * 2.0
        )
        arrangement = "side-by-side"
    else:
        bottom = (
            measurements.strength_legend_height_pt
            + measurements.p_legend_height_pt
            + legend_gap
            + padding * 2.0
        )
        arrangement = "stacked"
    source_label_strip = measurements.source_height_pt + 6.0
    if matrix_type == "lower":
        bottom += source_label_strip
    elif matrix_type == "upper":
        top += source_label_strip
    return left, right, bottom, top, arrangement


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
    )

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
        source_region=sources,
        x_limits=(0.0, bounds.x1 + right),
        y_limits=(0.0, bounds.y1 + top),
        strength_legend_anchor=strength_anchor,
        p_legend_anchor=p_anchor,
        legend_arrangement=arrangement,
        cell_size_pt=cell_size_pt,
        measurements=measurements,
    )


__all__ = [
    "MantelGeometry",
    "MantelLayoutMeasurements",
    "MatrixBounds",
    "SourceRegion",
    "TargetRail",
    "TextExtents",
    "cell_center",
    "measure_text_extents",
    "solve_geometry",
    "source_label_size",
    "variable_label_size",
]
