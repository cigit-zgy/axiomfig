"""Mantel-specific deterministic spatial allocation in matrix cell units."""

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
class MantelGeometry:
    bounds: MatrixBounds
    source_x: float
    source_positions: dict[str, tuple[float, float]]
    target_positions: dict[str, tuple[float, float]]
    colorbar_x: float
    x_limits: tuple[float, float]
    y_limits: tuple[float, float]


def cell_center(bounds: MatrixBounds, row: int, column: int) -> tuple[float, float]:
    return bounds.x0 + column + 0.5, bounds.y0 + bounds.size - row - 0.5


def _target_position(
    bounds: MatrixBounds,
    index: int,
    *,
    matrix_type: str,
) -> tuple[float, float]:
    if matrix_type in {"full", "mixed"}:
        _, y = cell_center(bounds, index, 0)
        return bounds.x0 - 0.04, y
    x, y = cell_center(bounds, index, index)
    if matrix_type == "upper":
        return x - 0.48, y - 0.48
    return x - 0.48, y + 0.48


def solve_geometry(
    labels: tuple[str, ...],
    source_groups: tuple[str, ...],
    *,
    matrix_type: str,
) -> MantelGeometry:
    """Allocate a compact matrix, label gutter, source nodes, and legend gutter."""
    size = len(labels)
    longest_source = max((len(label) for label in source_groups), default=0)
    source_gutter = float(np.clip(1.65 + longest_source * 0.085, 2.25, 3.75))
    bounds = MatrixBounds(source_gutter + 0.45, 1.55, size)
    source_x = 0.42 + longest_source * 0.085
    if source_groups:
        top = bounds.y1 - 0.65
        bottom = bounds.y0 + 0.65
        source_y = np.linspace(top, bottom, len(source_groups))
    else:
        source_y = np.asarray(())
    source_positions = {
        source: (source_x, float(y)) for source, y in zip(source_groups, source_y, strict=True)
    }
    target_positions = {
        label: _target_position(bounds, index, matrix_type=matrix_type)
        for index, label in enumerate(labels)
    }
    longest_target = max(len(label) for label in labels)
    label_gutter = 0.0 if matrix_type not in {"full", "mixed"} else 0.65 + longest_target * 0.08
    colorbar_x = bounds.x1 + label_gutter + 0.26
    right_gutter = label_gutter + 1.35
    top_gutter = 1.10
    estimated_label_width = longest_source * 0.016 * (size + source_gutter + right_gutter)
    left_padding = max(0.0, estimated_label_width - source_x + 0.25)
    return MantelGeometry(
        bounds=bounds,
        source_x=source_x,
        source_positions=source_positions,
        target_positions=target_positions,
        colorbar_x=colorbar_x,
        x_limits=(-left_padding, bounds.x1 + right_gutter),
        y_limits=(0.0, bounds.y1 + top_gutter),
    )


__all__ = ["MantelGeometry", "MatrixBounds", "cell_center", "solve_geometry"]
