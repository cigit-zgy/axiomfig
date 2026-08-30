"""Mantel-specific matrix envelope, target rail, and coupling-zone geometry.

The matrix owns one logical row/column coordinate system. Triangular presentation reserves the
complementary half of the same square envelope for Mantel coupling, following AxiomFig's
Figure/Axes/Artist separation: matrix anatomy resolves coordinates once and the coupling layer
only consumes source and target positions.
"""

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
    """Map logical matrix indices into the orientation-owned display coordinate system."""
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
        return x - rail_offset, y + rail_offset
    return bounds.x0 - 0.05, y


def _source_positions(
    bounds: MatrixBounds,
    source_groups: tuple[str, ...],
    *,
    matrix_type: str,
) -> SourceRegion:
    """Place source groups on a short rail inside the unused triangular half-plane."""
    count = len(source_groups)
    if count == 0:
        return SourceRegion("none", {})
    fractions = np.asarray((0.5,)) if count == 1 else np.linspace(0.0, 1.0, count)
    span = min(2.2, max(0.8, bounds.size * 0.16))

    if matrix_type == "lower":
        corner = "lower-left"
        base_x = bounds.x0 + 0.82
        base_y = bounds.y0 + 0.34
        positions = {
            source: (
                float(base_x + fraction * span),
                float(base_y + fraction * span * 0.38),
            )
            for source, fraction in zip(source_groups, fractions, strict=True)
        }
    elif matrix_type == "upper":
        corner = "upper-left"
        base_x = bounds.x0 + 0.34
        base_y = bounds.y1 - 0.82
        positions = {
            source: (
                float(base_x + fraction * span * 0.38),
                float(base_y - fraction * span),
            )
            for source, fraction in zip(source_groups, fractions, strict=True)
        }
    else:
        corner = "left"
        source_y = np.linspace(bounds.y1 - 0.75, bounds.y0 + 0.75, count)
        positions = {
            source: (bounds.x0 - 0.65, float(y))
            for source, y in zip(source_groups, source_y, strict=True)
        }
    return SourceRegion(corner, positions)


def _rail_orientation(matrix_type: str) -> str:
    if matrix_type == "lower":
        return "lower-left-to-upper-right"
    if matrix_type == "upper":
        return "upper-left-to-lower-right"
    return "left-vertical"


def solve_geometry(
    labels: tuple[str, ...],
    source_groups: tuple[str, ...],
    *,
    matrix_type: str,
) -> MantelGeometry:
    """Allocate matrix, coupling zone, labels, and two compact legend rows."""
    size = len(labels)
    longest_source = max((len(label) for label in source_groups), default=0)
    longest_variable = max((len(label) for label in labels), default=0)

    source_gutter = float(np.clip(0.80 + longest_source * 0.12, 1.50, 3.60))
    label_gutter = float(np.clip(1.10 + longest_variable * 0.20, 2.20, 5.00))
    if matrix_type in {"full", "mixed"}:
        left_gutter = max(source_gutter, label_gutter)
        right_gutter = label_gutter
    else:
        left_gutter = source_gutter
        right_gutter = 0.65
    bottom_gutter = 1.85
    top_gutter = label_gutter
    bounds = MatrixBounds(left_gutter, bottom_gutter, size)

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
    sources = _source_positions(bounds, source_groups, matrix_type=matrix_type)

    return MantelGeometry(
        bounds=bounds,
        matrix_type=matrix_type,
        target_rail=rail,
        source_region=sources,
        x_limits=(0.0, bounds.x1 + right_gutter),
        y_limits=(0.0, bounds.y1 + top_gutter),
        strength_legend_anchor=(0.20, 1.25),
        p_legend_anchor=(0.20, 0.15),
    )


__all__ = [
    "MantelGeometry",
    "MatrixBounds",
    "SourceRegion",
    "TargetRail",
    "cell_center",
    "solve_geometry",
]
