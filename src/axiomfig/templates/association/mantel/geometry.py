"""Mantel-specific matrix envelope, target rail, and coupling-zone geometry.

The scientific matrix always uses one canonical logical row/column system.  ``upper`` and
``lower`` only change the visible structural mask plus a presentation mirror that keeps the
unused triangular half available for Mantel coupling.  This follows the Figure/Axes/Artist
separation used elsewhere in AxiomFig: matrix anatomy owns coordinates; coupling only consumes
resolved source and target positions.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


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
    """Map a logical matrix cell to one deterministic display coordinate system.

    ``upper`` is rendered in the conventional upper-right triangle. ``lower`` mirrors x so the
    complementary coupling triangle remains on the left rather than creating a detached network
    panel. ``full`` and ``mixed`` keep conventional coordinates.
    """
    y = bounds.y1 - row - 0.5
    x = bounds.x1 - column - 0.5 if matrix_type == "lower" else bounds.x0 + column + 0.5
    return x, y


def _target_anchor(
    bounds: MatrixBounds,
    index: int,
    *,
    matrix_type: str,
    rail_offset: float,
) -> tuple[float, float]:
    x, y = cell_center(bounds, index, index, matrix_type=matrix_type)
    if matrix_type == "upper":
        return x - rail_offset, y - rail_offset
    if matrix_type == "lower":
        return x - rail_offset, y + rail_offset
    return bounds.x0 - 0.05, y


def _source_positions(
    bounds: MatrixBounds,
    source_groups: tuple[str, ...],
    *,
    matrix_type: str,
) -> SourceRegion:
    """Place source groups inside the unused matrix triangle, never on a rail extension."""
    count = len(source_groups)
    if count == 0:
        return SourceRegion("none", {})

    span_x = min(2.35, max(0.0, bounds.size * 0.16))
    span_y = min(1.85, max(0.0, bounds.size * 0.12))
    fractions = np.asarray((0.5,)) if count == 1 else np.linspace(0.0, 1.0, count)

    if matrix_type == "upper":
        corner = "lower-left"
        base_x = bounds.x0 + 0.68
        base_y = bounds.y0 + 0.62
        positions = {
            source: (float(base_x + fraction * span_x), float(base_y + fraction * span_y))
            for source, fraction in zip(source_groups, fractions, strict=True)
        }
    elif matrix_type == "lower":
        corner = "upper-left"
        base_x = bounds.x0 + 0.68
        base_y = bounds.y1 - 0.62
        positions = {
            source: (float(base_x + fraction * span_x), float(base_y - fraction * span_y))
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
    if matrix_type == "upper":
        return "upper-falling-diagonal/lower-left-coupling"
    if matrix_type == "lower":
        return "lower-rising-diagonal/upper-left-coupling"
    return "left-vertical"


def solve_geometry(
    labels: tuple[str, ...],
    source_groups: tuple[str, ...],
    *,
    matrix_type: str,
) -> MantelGeometry:
    """Allocate one compact square envelope whose unused triangle owns Mantel coupling."""
    size = len(labels)
    longest_source = max((len(label) for label in source_groups), default=0)
    longest_variable = max((len(label) for label in labels), default=0)

    left_gutter = float(np.clip(0.75 + longest_source * 0.075, 1.35, 2.65))
    bottom_gutter = 1.75
    top_gutter = float(np.clip(0.65 + longest_variable * 0.075, 1.15, 2.35))
    bounds = MatrixBounds(left_gutter, bottom_gutter, size)

    rail_offset = 0.43
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

    legend_x = 0.20
    strength_anchor = (legend_x, 1.10)
    p_anchor = (legend_x, 0.42)
    right_gutter = 0.55
    return MantelGeometry(
        bounds=bounds,
        matrix_type=matrix_type,
        target_rail=rail,
        source_region=sources,
        x_limits=(0.0, bounds.x1 + right_gutter),
        y_limits=(0.0, bounds.y1 + top_gutter),
        strength_legend_anchor=strength_anchor,
        p_legend_anchor=p_anchor,
    )


__all__ = [
    "MantelGeometry",
    "MatrixBounds",
    "SourceRegion",
    "TargetRail",
    "cell_center",
    "solve_geometry",
]
