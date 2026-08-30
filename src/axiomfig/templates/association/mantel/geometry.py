"""Deterministic matrix anatomy, target rail, and source-corner allocation."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

import numpy as np

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
class TargetRail:
    orientation: str
    anchors: dict[str, tuple[float, float]]


@dataclass(frozen=True)
class SourceRegion:
    corner: str
    positions: dict[str, tuple[float, float]]
    x_limits: tuple[float, float]
    y_limits: tuple[float, float]


@dataclass(frozen=True)
class MantelGeometry:
    bounds: MatrixBounds
    target_rail: TargetRail
    source_region: SourceRegion
    colorbar_x: float
    x_limits: tuple[float, float]
    y_limits: tuple[float, float]
    strength_legend_anchor: tuple[float, float]
    p_legend_anchor: tuple[float, float]

    @property
    def source_positions(self) -> dict[str, tuple[float, float]]:
        return self.source_region.positions

    @property
    def target_positions(self) -> dict[str, tuple[float, float]]:
        return self.target_rail.anchors


def cell_center(
    bounds: MatrixBounds,
    row: int,
    column: int,
    *,
    matrix_type: str,
) -> tuple[float, float]:
    """Map ordered matrix indices into one orientation-owned cell coordinate system."""
    x = bounds.x0 + column + 0.5
    y = bounds.y0 + row + 0.5 if matrix_type == "lower" else bounds.y1 - row - 0.5
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
    _, standard_y = cell_center(bounds, index, 0, matrix_type="full")
    return bounds.x0 - 0.04, standard_y


def _source_region(
    bounds: MatrixBounds,
    source_groups: tuple[str, ...],
    *,
    matrix_type: str,
) -> SourceRegion:
    count = len(source_groups)
    if not count:
        return SourceRegion("none", {}, (bounds.x0, bounds.x0), (bounds.y0, bounds.y0))
    spacing = min(0.62, 1.55 / max(count - 1, 1))
    if matrix_type == "upper":
        corner = "upper-left"
        base_x = bounds.x0 - 1.40
        base_y = bounds.y1 + 2.60
        positions = {
            source: (base_x + index * spacing, base_y - index * spacing)
            for index, source in enumerate(source_groups)
        }
    elif matrix_type == "lower":
        corner = "lower-left"
        base_x = bounds.x0 - 1.40
        base_y = bounds.y0 - 2.60
        positions = {
            source: (base_x + index * spacing, base_y + index * spacing)
            for index, source in enumerate(source_groups)
        }
    else:
        corner = "left"
        source_y = np.linspace(bounds.y1 - 0.65, bounds.y0 + 0.65, count)
        positions = {
            source: (bounds.x0 - 0.48, float(y))
            for source, y in zip(source_groups, source_y, strict=True)
        }
    xs = tuple(value[0] for value in positions.values())
    ys = tuple(value[1] for value in positions.values())
    return SourceRegion(corner, positions, (min(xs), max(xs)), (min(ys), max(ys)))


def solve_geometry(
    labels: tuple[str, ...],
    source_groups: tuple[str, ...],
    *,
    matrix_type: str,
) -> MantelGeometry:
    """Allocate matrix, mirrored target rail, compact source corner, and ornaments."""
    size = len(labels)
    longest_source = max((len(label) for label in source_groups), default=0)
    source_label_width = float(np.clip(0.78 + longest_source * 0.085, 1.35, 2.8))
    longest_variable = max((len(label) for label in labels), default=0)
    matrix_label_gutter = float(np.clip(0.78 + longest_variable * 0.085, 1.15, 2.8))
    lower_gutter = 2.25 if matrix_type == "lower" else 1.45
    upper_gutter = 2.25 if matrix_type == "upper" else matrix_label_gutter
    bounds = MatrixBounds(source_label_width + 1.45, lower_gutter, size)
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
    orientation = (
        "lower-left-to-upper-right"
        if matrix_type == "lower"
        else "upper-left-to-lower-right"
        if matrix_type == "upper"
        else "left-vertical"
    )
    rail = TargetRail(orientation, anchors)
    sources = _source_region(bounds, source_groups, matrix_type=matrix_type)
    label_gutter = 0.0 if matrix_type in {"lower", "upper"} else matrix_label_gutter
    colorbar_x = bounds.x1 + label_gutter + 0.28
    source_min_x = sources.x_limits[0] if sources.positions else bounds.x0
    source_min_y = sources.y_limits[0] if sources.positions else bounds.y0
    source_max_y = sources.y_limits[1] if sources.positions else bounds.y1
    left_padding = max(0.35, source_label_width + bounds.x0 - source_min_x - 0.45)
    x_limits = (source_min_x - left_padding, bounds.x1 + label_gutter + 1.35)
    y_limits = (
        min(0.0, source_min_y - 0.42),
        max(bounds.y1 + upper_gutter, source_max_y + 0.42),
    )
    ornament_contract = mantel_plot_contract()["ornaments"]
    assert isinstance(ornament_contract, Mapping)
    ornament_orientation = "upper" if matrix_type == "upper" else "lower"
    ornament_geometry = ornament_contract[ornament_orientation]
    assert isinstance(ornament_geometry, Mapping)
    legend_x = float(ornament_geometry["legend_anchor_x_fraction"])
    return MantelGeometry(
        bounds=bounds,
        target_rail=rail,
        source_region=sources,
        colorbar_x=colorbar_x,
        x_limits=x_limits,
        y_limits=y_limits,
        strength_legend_anchor=(
            legend_x,
            float(ornament_geometry["strength_legend_anchor_y_fraction"]),
        ),
        p_legend_anchor=(
            legend_x,
            float(ornament_geometry["p_legend_anchor_y_fraction"]),
        ),
    )


__all__ = [
    "MantelGeometry",
    "MatrixBounds",
    "SourceRegion",
    "TargetRail",
    "cell_center",
    "solve_geometry",
]
